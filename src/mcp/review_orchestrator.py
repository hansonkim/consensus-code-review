"""Review Orchestrator - MCP Server가 AI 간 협업을 중재

AI에게 변경 내역을 전달하지 않고, 해야 할 일만 알려주고
AI들이 MCP tools로 직접 탐색하며 서로 리뷰를 공유하며 합의점을 찾도록 합니다.
"""

import json
import time
from typing import Dict, List, Optional
from pathlib import Path
import tempfile


class ReviewSession:
    """리뷰 세션 - AI들 간의 협업 관리"""

    def __init__(self, session_id: str, base_branch: str, target_branch: str):
        self.session_id = session_id
        self.base_branch = base_branch
        self.target_branch = target_branch
        self.created_at = time.time()

        # AI 리뷰 저장소
        self.reviews: Dict[str, Dict] = {}  # {ai_name: {round: review_content}}
        self.current_round = 1
        self.max_rounds = 3

        # 합의 상태
        self.consensus_reached = False
        self.final_review = None

        # 진행 상황 저장소 (실시간 progress)
        self.progress: Dict[str, List[Dict]] = {}  # {ai_name: [{message, timestamp}, ...]}

    def submit_review(self, ai_name: str, round_num: int, review: str) -> Dict:
        """AI가 리뷰 제출"""
        if ai_name not in self.reviews:
            self.reviews[ai_name] = {}

        self.reviews[ai_name][round_num] = {
            "content": review,
            "timestamp": time.time()
        }

        return {
            "status": "accepted",
            "ai_name": ai_name,
            "round": round_num,
            "total_ais": len(self.reviews)
        }

    def get_other_reviews(self, requesting_ai: str, round_num: int) -> List[Dict]:
        """다른 AI들의 리뷰 조회"""
        other_reviews = []

        for ai_name, rounds in self.reviews.items():
            if ai_name != requesting_ai and round_num in rounds:
                other_reviews.append({
                    "ai_name": ai_name,
                    "review": rounds[round_num]["content"],
                    "timestamp": rounds[round_num]["timestamp"]
                })

        return other_reviews

    def check_consensus(self) -> Dict:
        """합의 여부 확인"""
        # 모든 AI가 현재 라운드 제출했는지
        ais_in_current_round = sum(
            1 for rounds in self.reviews.values()
            if self.current_round in rounds
        )

        return {
            "round": self.current_round,
            "submitted": ais_in_current_round,
            "total_ais": len(self.reviews),
            "all_submitted": ais_in_current_round == len(self.reviews),
            "consensus_reached": self.consensus_reached
        }

    def advance_round(self) -> Dict:
        """다음 라운드로 진행"""
        if self.current_round >= self.max_rounds:
            return {
                "status": "max_rounds_reached",
                "current_round": self.current_round
            }

        self.current_round += 1
        return {
            "status": "advanced",
            "current_round": self.current_round
        }

    def finalize(self, final_review: str) -> Dict:
        """최종 리뷰 확정"""
        self.consensus_reached = True
        self.final_review = final_review

        return {
            "status": "finalized",
            "rounds_completed": self.current_round,
            "total_reviews": sum(len(rounds) for rounds in self.reviews.values())
        }


class ReviewOrchestrator:
    """리뷰 오케스트레이터 - AI 간 협업 조정"""

    def __init__(self):
        self.sessions: Dict[str, ReviewSession] = {}
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_code_review_sessions"
        self.temp_dir.mkdir(exist_ok=True)

    def create_review_session(self, base: str, target: str = "HEAD") -> str:
        """새 리뷰 세션 생성

        Args:
            base: 기준 브랜치
            target: 비교 대상 브랜치 (기본: HEAD)

        Returns:
            session_id
        """
        session_id = f"review_{int(time.time())}_{id(self)}"
        session = ReviewSession(session_id, base, target)
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
            "created_at": session.created_at
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
        progress_entry = {
            "message": message,
            "timestamp": time.time()
        }
        session.progress[ai_name].append(progress_entry)

        # 세션 저장 (선택적)
        # self._save_session(session)  # 너무 자주 저장하면 I/O 부담

        return {
            "status": "progress_recorded",
            "ai_name": ai_name,
            "message": message
        }

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
                    updates.append({
                        "ai_name": ai_name,
                        "message": progress["message"],
                        "timestamp": progress["timestamp"]
                    })

        # 시간순 정렬
        updates.sort(key=lambda x: x["timestamp"])

        return {
            "session_id": session_id,
            "updates": updates,
            "count": len(updates)
        }

    def _save_session(self, session: ReviewSession):
        """세션을 파일에 저장 (디버깅/복구용)"""
        session_file = self.temp_dir / f"{session.session_id}.json"

        session_data = {
            "session_id": session.session_id,
            "base_branch": session.base_branch,
            "target_branch": session.target_branch,
            "current_round": session.current_round,
            "reviews": session.reviews,
            "consensus_reached": session.consensus_reached,
            "final_review": session.final_review,
            "created_at": session.created_at
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def get_available_tools(self) -> List[Dict[str, str]]:
        """사용 가능한 도구 목록"""
        return [
            {
                "name": "create_review_session",
                "description": "새 코드 리뷰 세션 시작 (AI들 간 협업을 위한 세션 생성)",
                "parameters": "base: str, target: str (기본: HEAD)",
                "example": 'create_review_session("develop", "HEAD")'
            },
            {
                "name": "submit_review",
                "description": "내 리뷰 제출 (현재 라운드에 리뷰 제출)",
                "parameters": "session_id: str, ai_name: str, review: str",
                "example": 'submit_review(session_id, "Claude", "# Review\\n...")'
            },
            {
                "name": "get_other_reviews",
                "description": "다른 AI들의 리뷰 읽기 (현재 라운드)",
                "parameters": "session_id: str, ai_name: str",
                "example": 'get_other_reviews(session_id, "Claude")'
            },
            {
                "name": "check_consensus",
                "description": "합의 상태 확인 (모든 AI가 제출했는지)",
                "parameters": "session_id: str",
                "example": "check_consensus(session_id)"
            },
            {
                "name": "advance_round",
                "description": "다음 라운드로 진행",
                "parameters": "session_id: str",
                "example": "advance_round(session_id)"
            },
            {
                "name": "finalize_review",
                "description": "최종 리뷰 확정",
                "parameters": "session_id: str, final_review: str",
                "example": 'finalize_review(session_id, "# Final Review\\n...")'
            },
            {
                "name": "get_session_info",
                "description": "세션 정보 조회",
                "parameters": "session_id: str",
                "example": "get_session_info(session_id)"
            },
            {
                "name": "report_progress",
                "description": "⭐ 실시간 진행 상황 보고 (리뷰 작성 중 사용자에게 진행 상황 알림)",
                "parameters": "session_id: str, ai_name: str, message: str",
                "example": 'report_progress(session_id, "Claude", "Analyzing security issues in auth.py...")'
            },
            {
                "name": "get_progress",
                "description": "진행 상황 조회 (특정 시간 이후의 progress 확인)",
                "parameters": "session_id: str, since: float (기본: 0)",
                "example": "get_progress(session_id, since=1730356789.0)"
            }
        ]
