"""Review Orchestrator - MCP Server가 AI 간 협업을 중재

AI에게 변경 내역을 전달하지 않고, 해야 할 일만 알려주고
AI들이 MCP tools로 직접 탐색하며 서로 리뷰를 공유하며 합의점을 찾도록 합니다.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Literal, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Type alias for verbosity modes
VerbosityMode = Literal["summary", "detailed", "full"]


class ReviewSession:
    """리뷰 세션 - AI들 간의 협업 관리"""

    def __init__(
        self,
        session_id: str,
        base_branch: str,
        target_branch: str,
        curated_data: Optional[str] = None,
        max_rounds: int = 3,
        target_ais: Optional[List[str]] = None,
        verbosity: VerbosityMode = "summary",
    ):
        self.session_id = session_id
        self.base_branch = base_branch
        self.target_branch = target_branch
        self.created_at = time.time()

        # AI 리뷰 저장소
        self.reviews: Dict[str, Dict] = {}  # {ai_name: {round: review_content}}
        self.current_round = 1
        self.max_rounds = max_rounds

        # 합의 상태
        self.consensus_reached = False
        self.final_review = None

        # 진행 상황 저장소 (실시간 progress)
        self.progress: Dict[str, List[Dict]] = {}  # {ai_name: [{message, timestamp}, ...]}

        # 자동화를 위한 메타데이터
        self.curated_data = curated_data
        self.target_ais = target_ais
        self.verbosity = verbosity
        self.auto_peer_review_triggered = False  # 중복 트리거 방지

    def submit_review(self, ai_name: str, round_num: int, review: str) -> Dict:
        """AI가 리뷰 제출"""
        if ai_name not in self.reviews:
            self.reviews[ai_name] = {}

        self.reviews[ai_name][round_num] = {"content": review, "timestamp": time.time()}

        return {
            "status": "accepted",
            "ai_name": ai_name,
            "round": round_num,
            "total_ais": len(self.reviews),
        }

    def get_other_reviews(self, requesting_ai: str, round_num: int) -> List[Dict]:
        """다른 AI들의 리뷰 조회"""
        other_reviews = []

        for ai_name, rounds in self.reviews.items():
            if ai_name != requesting_ai and round_num in rounds:
                other_reviews.append(
                    {
                        "ai_name": ai_name,
                        "review": rounds[round_num]["content"],
                        "timestamp": rounds[round_num]["timestamp"],
                    }
                )

        return other_reviews

    def check_consensus(self) -> Dict:
        """합의 여부 확인"""
        # 모든 AI가 현재 라운드 제출했는지
        ais_in_current_round = sum(
            1 for rounds in self.reviews.values() if self.current_round in rounds
        )

        return {
            "round": self.current_round,
            "submitted": ais_in_current_round,
            "total_ais": len(self.reviews),
            "all_submitted": ais_in_current_round == len(self.reviews),
            "consensus_reached": self.consensus_reached,
        }

    def advance_round(self) -> Dict:
        """다음 라운드로 진행"""
        if self.current_round >= self.max_rounds:
            return {"status": "max_rounds_reached", "current_round": self.current_round}

        self.current_round += 1
        return {"status": "advanced", "current_round": self.current_round}

    def finalize(self, final_review: str) -> Dict:
        """최종 리뷰 확정"""
        self.consensus_reached = True
        self.final_review = final_review

        return {
            "status": "finalized",
            "rounds_completed": self.current_round,
            "total_reviews": sum(len(rounds) for rounds in self.reviews.values()),
        }


class ReviewOrchestrator:
    """리뷰 오케스트레이터 - AI 간 협업 조정"""

    def __init__(self):
        self.sessions: Dict[str, ReviewSession] = {}
        # MCP 서버 호출한 디렉토리에 reviews 폴더 생성
        self.reviews_dir = Path.cwd() / "reviews"
        self.reviews_dir.mkdir(exist_ok=True)

    def create_review_session(
        self,
        base: str,
        target: str = "HEAD",
        curated_data: Optional[str] = None,
        max_rounds: int = 3,
        target_ais: Optional[List[str]] = None,
        verbosity: VerbosityMode = "summary",
    ) -> str:
        """새 리뷰 세션 생성

        Args:
            base: 기준 브랜치
            target: 비교 대상 브랜치 (기본: HEAD)
            curated_data: 큐레이션된 변경 내역 (자동 트리거용)
            max_rounds: 최대 라운드 수
            target_ais: 타겟 AI 목록 (None이면 자동 감지)
            verbosity: 응답 상세도

        Returns:
            session_id
        """
        session_id = f"review_{int(time.time())}_{id(self)}"
        session = ReviewSession(
            session_id,
            base,
            target,
            curated_data=curated_data,
            max_rounds=max_rounds,
            target_ais=target_ais,
            verbosity=verbosity,
        )
        self.sessions[session_id] = session

        # 세션 저장 (디버깅용)
        self._save_session(session)

        return session_id

    def get_session(self, session_id: str) -> Optional[ReviewSession]:
        """세션 조회"""
        return self.sessions.get(session_id)

    def submit_review(self, session_id: str, ai_name: str, review: str) -> Dict:
        """AI가 리뷰 제출

        Args:
            session_id: 세션 ID
            ai_name: AI 이름 (예: "Claude", "GPT-4", "Gemini")
            review: 리뷰 내용

        Returns:
            제출 결과
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        result = session.submit_review(ai_name, session.current_round, review)
        self._save_session(session)

        # 🚀 자동 트리거: CLAUDE 리뷰 제출 감지
        if ai_name.upper() == "CLAUDE" and session.curated_data:
            if session.current_round == 1 and not session.auto_peer_review_triggered:
                # 라운드 1: 첫 리뷰 → 다른 AI 피드백 수집
                logger.info("[Round 1] CLAUDE's first review. Triggering peer reviews...")
                peer_results = self._trigger_peer_reviews(session)
                result["peer_reviews_triggered"] = True
                result["peer_reviews"] = peer_results

            elif session.current_round >= 2:
                # 라운드 2+: 개선 리뷰 → 합의 확인 → 피드백 or 완료
                logger.info(
                    f"[Round {session.current_round}] CLAUDE's improved review. Checking consensus..."
                )

                # 합의 확인
                consensus_result = self._check_round_consensus(session)

                if consensus_result["consensus_reached"]:
                    # 합의 도달! 최종 리포트 생성
                    session.consensus_reached = True
                    session.final_review = review
                    self._save_session(session)

                    # 최종 리포트 생성
                    from .handlers.review_handler import create_review_response

                    response = create_review_response(session, verbosity=session.verbosity)

                    result["status"] = "consensus_reached"
                    result["final_report"] = {
                        "summary_file": response.artifacts.summary_file,
                        "full_transcript": response.artifacts.full_transcript,
                        "consensus_details": consensus_result,
                    }
                    result["message"] = (
                        f"🎉 Consensus reached! Full report: {response.artifacts.summary_file}"
                    )

                elif session.current_round >= session.max_rounds:
                    # max_rounds 도달, 강제 종료
                    session.consensus_reached = False
                    session.final_review = review
                    self._save_session(session)

                    # 최종 리포트 생성 (합의 없이)
                    from .handlers.review_handler import create_review_response

                    response = create_review_response(session, verbosity=session.verbosity)

                    result["status"] = "max_rounds_reached"
                    result["final_report"] = {
                        "summary_file": response.artifacts.summary_file,
                        "full_transcript": response.artifacts.full_transcript,
                    }
                    result["message"] = (
                        f"⚠️ Max rounds ({session.max_rounds}) reached. Final report: {response.artifacts.summary_file}"
                    )

                else:
                    # 합의 안됨 → 다음 라운드 진행
                    # 다른 AI 피드백 수집
                    logger.info(
                        f"[Round {session.current_round}] No consensus. Triggering next round..."
                    )
                    peer_results = self._trigger_peer_reviews(session)

                    # 라운드 증가
                    session.current_round += 1
                    self._save_session(session)

                    # 다른 AI 피드백 조회
                    peer_feedbacks = session.get_other_reviews("CLAUDE", session.current_round - 1)

                    # 개선 프롬프트 생성
                    improvement_prompt = self._generate_improvement_prompt(
                        session, review, peer_feedbacks
                    )

                    result["status"] = "awaiting_improvement"
                    result["current_round"] = session.current_round
                    result["peer_feedbacks_count"] = len(peer_feedbacks)
                    result["improvement_prompt_preview"] = improvement_prompt[:500] + "..."
                    result["instruction"] = (
                        f"라운드 {session.current_round}: 피드백을 검토하고 개선된 리뷰를 작성하세요"
                    )
                    result["next_tool"] = "submit_review"

        return result

    def get_other_reviews(self, session_id: str, ai_name: str) -> List[Dict]:
        """다른 AI들의 리뷰 읽기

        Args:
            session_id: 세션 ID
            ai_name: 요청하는 AI 이름

        Returns:
            다른 AI들의 리뷰 목록
        """
        session = self.get_session(session_id)
        if not session:
            return []

        return session.get_other_reviews(ai_name, session.current_round)

    def check_consensus(self, session_id: str) -> Dict:
        """합의 상태 확인

        Args:
            session_id: 세션 ID

        Returns:
            합의 상태
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        return session.check_consensus()

    def advance_round(self, session_id: str) -> Dict:
        """다음 라운드로 진행

        Args:
            session_id: 세션 ID

        Returns:
            라운드 진행 결과
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        result = session.advance_round()
        self._save_session(session)

        return result

    def finalize_review(self, session_id: str, final_review: str) -> Dict:
        """최종 리뷰 확정

        Args:
            session_id: 세션 ID
            final_review: 최종 합의된 리뷰

        Returns:
            확정 결과
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        result = session.finalize(final_review)
        self._save_session(session)

        return result

    def get_session_info(self, session_id: str) -> Dict:
        """세션 정보 조회"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session.session_id,
            "base_branch": session.base_branch,
            "target_branch": session.target_branch,
            "current_round": session.current_round,
            "max_rounds": session.max_rounds,
            "participating_ais": list(session.reviews.keys()),
            "consensus_reached": session.consensus_reached,
            "created_at": session.created_at,
        }

    def report_progress(self, session_id: str, ai_name: str, message: str) -> Dict:
        """AI가 작업 중 진행 상황 보고

        AI가 리뷰 작성 중 실시간으로 자신의 진행 상황을 보고할 수 있습니다.

        Args:
            session_id: 세션 ID
            ai_name: AI 이름
            message: 진행 상황 메시지 (예: "Analyzing security issues in auth.py...")

        Returns:
            보고 결과
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # AI별 progress 리스트 초기화
        if ai_name not in session.progress:
            session.progress[ai_name] = []

        # 진행 상황 추가
        progress_entry = {"message": message, "timestamp": time.time()}
        session.progress[ai_name].append(progress_entry)

        # 세션 저장 (선택적)
        # self._save_session(session)  # 너무 자주 저장하면 I/O 부담

        return {"status": "progress_recorded", "ai_name": ai_name, "message": message}

    def get_progress(self, session_id: str, since: float = 0) -> Dict:
        """진행 상황 조회

        특정 시간 이후의 모든 AI 진행 상황을 조회합니다.

        Args:
            session_id: 세션 ID
            since: 이 timestamp 이후의 progress만 반환 (기본: 0 = 전체)

        Returns:
            진행 상황 목록
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # 모든 AI의 progress를 수집
        updates = []
        for ai_name, progress_list in session.progress.items():
            for progress in progress_list:
                if progress["timestamp"] > since:
                    updates.append(
                        {
                            "ai_name": ai_name,
                            "message": progress["message"],
                            "timestamp": progress["timestamp"],
                        }
                    )

        # 시간순 정렬
        updates.sort(key=lambda x: x["timestamp"])

        return {"session_id": session_id, "updates": updates, "count": len(updates)}

    def _check_round_consensus(self, session: ReviewSession) -> Dict:
        """현재 라운드에서 합의 도달 여부 확인

        Args:
            session: 리뷰 세션

        Returns:
            {
                "consensus_reached": bool,
                "confidence": float,
                "reason": str
            }
        """
        # 현재 라운드의 다른 AI 피드백 조회
        peer_feedbacks = session.get_other_reviews("CLAUDE", session.current_round)

        if not peer_feedbacks:
            return {
                "consensus_reached": False,
                "confidence": 0.0,
                "reason": "No peer feedbacks available",
            }

        # 간단한 휴리스틱: 긍정/부정 키워드 분석
        positive_keywords = [
            "approve",
            "approved",
            "accept",
            "accepted",
            "good",
            "agree",
            "agreed",
            "looks good",
            "lgtm",
            "excellent",
            "well done",
            "comprehensive",
            "thorough",
            "accurate",
            "correct",
            "합의",
            "동의",
            "좋습니다",
        ]

        negative_keywords = [
            "critical",
            "must fix",
            "serious issue",
            "concern",
            "problem",
            "incorrect",
            "missing",
            "overlooked",
            "disagree",
            "reject",
            "not enough",
            "insufficient",
            "incomplete",
            "부족",
            "문제",
            "개선 필요",
        ]

        positive_count = 0
        negative_count = 0
        total_feedbacks = len(peer_feedbacks)

        for fb in peer_feedbacks:
            review_text = fb["review"].lower()

            # 긍정 키워드 카운트
            for keyword in positive_keywords:
                if keyword.lower() in review_text:
                    positive_count += 1
                    break  # 각 피드백당 1번만 카운트

            # 부정 키워드 카운트
            for keyword in negative_keywords:
                if keyword.lower() in review_text:
                    negative_count += 1
                    break

        # 합의 판단: 긍정이 부정보다 많고, 과반수 이상 긍정
        consensus_reached = (
            positive_count > negative_count and positive_count >= total_feedbacks * 0.5
        )

        confidence = positive_count / total_feedbacks if total_feedbacks > 0 else 0.0

        reason = f"{positive_count}/{total_feedbacks} AI들이 긍정적 평가, {negative_count} 부정적"

        return {
            "consensus_reached": consensus_reached,
            "confidence": confidence,
            "reason": reason,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total_feedbacks": total_feedbacks,
        }

    def _generate_improvement_prompt(
        self, session: ReviewSession, current_review: str, peer_feedbacks: List[Dict]
    ) -> str:
        """CLAUDE에게 개선 프롬프트 생성

        Args:
            session: 리뷰 세션
            current_review: CLAUDE의 현재 리뷰
            peer_feedbacks: 다른 AI들의 피드백

        Returns:
            개선 프롬프트
        """
        prompt = f"""# 코드 리뷰 개선 요청 - 라운드 {session.current_round}

## 📝 당신의 현재 리뷰

{current_review}

## 💬 다른 AI들의 피드백

"""
        for fb in peer_feedbacks:
            prompt += f"""### {fb["ai_name"]}의 피드백

{fb["review"]}

---

"""

        prompt += """## 🎯 개선 과제

다른 AI들의 피드백을 검토하고:

1. **수용할 피드백**: 타당한 지적을 리뷰에 반영하세요
2. **거부할 피드백**: 근거 없거나 부적절한 지적은 무시하세요
3. **추가 발견**: 피드백을 보고 새로 발견한 이슈가 있다면 추가하세요

**개선 원칙**:
- 모든 피드백을 맹목적으로 수용하지 마세요
- 각 피드백의 타당성을 비판적으로 평가하세요
- 리뷰의 품질을 높이는 방향으로만 수정하세요

개선된 리뷰를 작성한 후 `submit_review` 도구를 호출하세요.
"""
        return prompt

    def _trigger_peer_reviews(self, session: ReviewSession) -> List[Dict]:
        """CLAUDE의 첫 리뷰 제출 시 자동으로 다른 AI들 호출

        Args:
            session: 리뷰 세션 (CLAUDE의 첫 리뷰가 제출된 상태)

        Returns:
            다른 AI들의 리뷰 결과 목록
        """
        from ai_cli_tools import AIClient, CacheManager, ModelManager
        from ai_cli_tools.constants import CACHE_FILE

        # 중복 트리거 방지
        if session.auto_peer_review_triggered:
            return []

        session.auto_peer_review_triggered = True

        # 1. AI 감지 (CLAUDE 제외)
        cache_manager = CacheManager(CACHE_FILE)
        model_manager = ModelManager(cache_manager)
        model_manager.initialize_models()

        available_ais = model_manager.get_available_models()

        # CLAUDE 제외 + target_ais 필터링
        if session.target_ais:
            # 사용자가 특정 AI 지정한 경우
            reviewer_ais = {
                k: v
                for k, v in available_ais.items()
                if k.upper() in session.target_ais and k != "claude"
            }
        else:
            # 모든 AI 사용 (CLAUDE 제외)
            reviewer_ais = {k: v for k, v in available_ais.items() if k != "claude"}

        if not reviewer_ais:
            logger.warning("No peer AIs available for review")
            return []

        # 2. CLAUDE의 리뷰 가져오기
        claude_review = session.reviews.get("CLAUDE", {}).get(1, {}).get("content", "")

        if not claude_review:
            logger.error("CLAUDE's review not found in session")
            return []

        # 3. 각 AI에게 검토 요청
        ai_client = AIClient()
        peer_results = []

        for ai_name, ai_model in reviewer_ais.items():
            try:
                prompt = f"""다음 코드 리뷰를 검토하고 피드백을 제공해주세요:

=== CODE CHANGES ===
{session.curated_data}

=== CLAUDE's REVIEW ===
{claude_review}

=== YOUR TASK ===
위 리뷰를 비판적으로 검토하고:
1. 놓친 이슈가 있는지
2. 잘못된 분석이 있는지
3. 개선할 점이 있는지
평가해주세요."""

                logger.info(f"[Auto-trigger] Requesting review from {ai_name}...")
                response = ai_client.call_ai(prompt, ai_model)

                # 세션에 저장
                session.submit_review(ai_name.upper(), 1, response)
                logger.info(f"[Auto-trigger] {ai_name} review completed")

                peer_results.append(
                    {"ai": ai_name, "status": "success", "review_length": len(response)}
                )

            except Exception as e:
                logger.error(f"[Auto-trigger] Failed to get review from {ai_name}: {e}")
                peer_results.append({"ai": ai_name, "status": "error", "error": str(e)})

        # 세션 저장
        self._save_session(session)

        return peer_results

    def _save_session(self, session: ReviewSession):
        """세션을 파일에 저장 (디버깅/복구용)"""
        session_file = self.reviews_dir / f"{session.session_id}.json"

        session_data = {
            "session_id": session.session_id,
            "base_branch": session.base_branch,
            "target_branch": session.target_branch,
            "current_round": session.current_round,
            "reviews": session.reviews,
            "consensus_reached": session.consensus_reached,
            "final_review": session.final_review,
            "created_at": session.created_at,
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def review_iterative_consensus(
        self,
        base: str,
        target: str = "HEAD",
        initial_review_file: str = "",
        max_rounds: int = 5,
        verbosity: VerbosityMode = "summary",
    ) -> Dict:
        """🔄 반복적 합의 프로세스 (외부 파일 시작)

        외부 파일에서 CLAUDE의 초기 리뷰를 읽어서,
        다른 AI들의 피드백을 받고 CLAUDE가 개선하는 과정을 반복합니다.

        워크플로우:
        1. 외부 파일에서 CLAUDE의 초기 리뷰 읽기
        2. 세션 생성 및 CLAUDE 리뷰 등록
        3. 다른 AI들(GPT-4, Gemini) 자동 호출하여 피드백 수집
        4. CLAUDE에게 피드백 보여주고 개선 프롬프트 반환
        5. CLAUDE가 submit_review로 개선된 리뷰 제출
        6. 라운드 2+: 합의 확인 → 다시 피드백 → 개선 반복
        7. 합의 도달 또는 max_rounds까지 반복

        Args:
            base: 기준 브랜치
            target: 비교 대상 브랜치 (기본: HEAD)
            initial_review_file: CLAUDE가 작성한 초기 리뷰 파일 경로 (필수)
            max_rounds: 최대 라운드 수 (기본: 5)
            verbosity: 응답 상세도 (summary | detailed | full)

        Returns:
            {
                "status": "awaiting_improvement",
                "session_id": "...",
                "current_round": 1,
                "peer_feedbacks": [...],
                "improvement_prompt": "...",
                "next_tool": "submit_review"
            }
        """
        from pathlib import Path

        from ..data_curator import DataCurator

        # 1. 파일 경로 검증
        if not initial_review_file or not initial_review_file.strip():
            return {"status": "error", "error": "initial_review_file is required"}

        review_path = Path(initial_review_file)
        if not review_path.exists():
            return {"status": "error", "error": f"Review file not found: {initial_review_file}"}

        # 2. 외부 파일에서 CLAUDE 리뷰 읽기
        try:
            initial_review = review_path.read_text(encoding="utf-8")
        except Exception as e:
            return {"status": "error", "error": f"Failed to read review file: {e}"}

        if not initial_review.strip():
            return {"status": "error", "error": "Review file is empty"}

        # 3. 데이터 큐레이션
        curator = DataCurator()
        curated_result = curator.curate_changes(base, target)
        curated_data = curator.format_curated_data(curated_result)

        # 4. 세션 생성 (메타데이터 포함, ais 파라미터 없이 자동 감지)
        session_id = self.create_review_session(
            base,
            target,
            curated_data=curated_data,
            max_rounds=max_rounds,
            target_ais=None,  # 모든 사용 가능한 AI 자동 감지
            verbosity=verbosity,
        )

        # 5. CLAUDE의 초기 리뷰를 세션에 등록 (submit_review 호출)
        #    → 자동으로 _trigger_peer_reviews 실행됨!
        submit_result = self.submit_review(session_id, "CLAUDE", initial_review)

        # 6. 피어 리뷰 결과 확인
        if not submit_result.get("peer_reviews_triggered"):
            return {
                "status": "error",
                "error": "Failed to trigger peer reviews",
                "details": submit_result,
            }

        # 7. 다른 AI들의 피드백 조회
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "error": "Session not found"}

        peer_feedbacks = session.get_other_reviews("CLAUDE", 1)

        # 8. CLAUDE에게 개선 프롬프트 생성
        improvement_prompt = self._generate_improvement_prompt(
            session, initial_review, peer_feedbacks
        )

        return {
            "status": "awaiting_improvement",
            "session_id": session_id,
            "current_round": 1,
            "max_rounds": max_rounds,
            "peer_feedbacks": [
                {"ai": fb["ai_name"], "feedback_preview": fb["review"][:300] + "..."}
                for fb in peer_feedbacks
            ],
            "improvement_prompt_preview": improvement_prompt[:500] + "...",
            "instruction": "다른 AI들의 피드백을 검토하고 개선된 리뷰를 작성하세요. 완료 후 submit_review를 호출하세요.",
            "next_tool": "submit_review",
            "next_args": {"session_id": session_id, "ai_name": "CLAUDE", "review": "<개선된 리뷰>"},
        }

    def get_available_tools(self) -> List[Dict[str, str]]:
        """사용 가능한 도구 목록"""
        return [
            {
                "name": "review_iterative_consensus",
                "description": "🔄 반복적 합의 프로세스 시작 | 외부 파일에서 CLAUDE의 초기 리뷰를 읽고, 다른 AI 피드백 → CLAUDE 개선을 반복하여 합의에 도달합니다. MCP가 사용 가능한 모든 AI를 자동 감지합니다.",
                "parameters": "base: str, target: str = 'HEAD', initial_review_file: str, max_rounds: int = 5, verbosity: str = 'summary'",
                "example": 'review_iterative_consensus(base="develop", initial_review_file="./review.md", max_rounds=5, verbosity="summary")',
            },
            {
                "name": "create_review_session",
                "description": "🆕 새 리뷰 세션을 생성하고 초기 메타데이터를 설정합니다.",
                "parameters": "base: str, target: str = 'HEAD', curated_data: str | None = None, max_rounds: int = 3, target_ais: list[str] | None = None, verbosity: str = 'summary'",
                "example": 'create_review_session(base="develop", target="HEAD")',
            },
            {
                "name": "submit_review",
                "description": "🔁 리뷰 제출 및 라운드 진행 | CLAUDE가 개선된 리뷰를 제출합니다. 자동으로 합의 확인 → 피드백 수집 → 다음 라운드 진행 또는 최종 리포트 생성을 수행합니다.",
                "parameters": "session_id: str, ai_name: str = 'CLAUDE', review: str",
                "example": 'submit_review(session_id="review_xxx", ai_name="CLAUDE", review="# Improved Review\\n...")',
            },
            {
                "name": "get_other_reviews",
                "description": "👥 동일 라운드에서 다른 AI가 제출한 리뷰를 조회합니다.",
                "parameters": "session_id: str, ai_name: str",
                "example": 'get_other_reviews(session_id="review_xxx", ai_name="Claude")',
            },
            {
                "name": "check_consensus",
                "description": "✅ 현재 라운드에서 합의 여부를 확인합니다.",
                "parameters": "session_id: str",
                "example": 'check_consensus(session_id="review_xxx")',
            },
            {
                "name": "advance_round",
                "description": "⏭️ 강제로 다음 라운드로 이동시킵니다 (max_rounds까지).",
                "parameters": "session_id: str",
                "example": 'advance_round(session_id="review_xxx")',
            },
            {
                "name": "get_session_info",
                "description": "ℹ️ 세션 메타데이터와 상태를 조회합니다.",
                "parameters": "session_id: str",
                "example": 'get_session_info(session_id="review_xxx")',
            },
            {
                "name": "report_progress",
                "description": "📝 AI 작업 진행 상황을 기록합니다.",
                "parameters": "session_id: str, ai_name: str, message: str",
                "example": 'report_progress(session_id="review_xxx", ai_name="Claude", message="Analyzing diffs...")',
            },
            {
                "name": "get_progress",
                "description": "📈 기록된 진행 상황 로그를 조회합니다.",
                "parameters": "session_id: str, since: float = 0",
                "example": 'get_progress(session_id="review_xxx")',
            },
        ]
