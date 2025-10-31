"""Phase 1: CLAUDE-Led Iterative Review

CLAUDE MCP 환경에서 CLAUDE가 주도적으로 REPORT를 작성하고,
다른 AI들이 검토하는 iterative refinement 방식입니다.

Architecture:
- CLAUDE: REPORT 작성자이자 통합자 (Lead Reviewer)
- 다른 AI들: REPORT 검토자 (Reviewers)
- Consensus: 자연스러운 수렴 (CLAUDE "수정 없음" + 다른 AI들 "동의")
"""

import os
import sys
import re
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ai_cli_tools 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_cli_tools import AIClient, AIModel
from src.mcp import MCPManager
from src.mcp.minimal_prompt import (
    generate_claude_initial_report_prompt,
    generate_reviewer_critique_prompt,
    generate_claude_refinement_prompt,
    generate_consensus_check_prompt
)
from src.data_curator import DataCurator


class MCPOrchestratedReviewer:
    """CLAUDE-Led Iterative Review 시스템"""

    def __init__(self, ai_client: AIClient, verbose: bool = False):
        """초기화

        Args:
            ai_client: AI 클라이언트
            verbose: 상세 출력 여부
        """
        self.ai_client = ai_client
        self.verbose = verbose
        self.mcp_manager = MCPManager()

    def execute(
        self,
        available_ais: Dict[str, AIModel],
        base_branch: str,
        target_branch: str = "HEAD",
        max_rounds: int = 5
    ) -> Dict:
        """CLAUDE-Led Iterative Review 실행

        Args:
            available_ais: 사용 가능한 AI 모델들
            base_branch: 기준 브랜치
            target_branch: 비교 대상 브랜치
            max_rounds: 최대 라운드 수

        Returns:
            최종 REPORT 결과
        """
        print("\n" + "=" * 70)
        print("CLAUDE-Led Iterative Code Review")
        print("=" * 70)

        # CLAUDE는 필수
        if "claude" not in available_ais:
            raise ValueError(
                "CLAUDE is required in MCP environment. "
                "This is a CLAUDE-Led review system."
            )

        claude_model = available_ais["claude"]
        other_ais = {k: v for k, v in available_ais.items() if k != "claude"}

        print(f"👑 Lead Reviewer: CLAUDE ({claude_model.model_id})")
        print(f"🔍 Reviewers: {len(other_ais)}개 AI")
        for ai_name, ai_model in other_ais.items():
            print(f"   • {ai_name.upper()}: {ai_model.model_id}")
        print(f"🔄 Max Rounds: {max_rounds}")
        print()

        # 1. 리뷰 세션 생성
        session_id = self.mcp_manager.call_tool(
            "review",
            "create_review_session",
            base=base_branch,
            target=target_branch
        )

        print(f"✅ 세션 생성: {session_id}")
        print()

        # 2. 데이터 큐레이션
        print("📊 Python이 변경사항을 큐레이션하는 중...")
        curator = DataCurator()
        curated_result = curator.curate(base_branch, target_branch)

        if curated_result["status"] == "error":
            raise RuntimeError(f"Curation 실패: {curated_result['error']}")

        curated_data = curated_result["formatted_output"]
        summary = curated_result["summary"]

        print(f"   ✅ {summary['curated_files']}개 파일 선택 완료")
        print(f"   → 총 변경사항: {summary['total_files']}개 파일")
        print()

        # 3. Round 1: CLAUDE 초기 REPORT 작성
        print("=" * 70)
        print("Round 1: Initial Report by CLAUDE")
        print("=" * 70)
        print()

        claude_report = self._claude_initial_report(
            session_id,
            claude_model,
            curated_data
        )

        # 4. Iterative Refinement Loop
        for round_num in range(2, max_rounds + 1):
            print("\n" + "=" * 70)
            print(f"Round {round_num}: Review and Refine")
            print("=" * 70)
            print()

            # 4a. 다른 AI들이 CLAUDE REPORT 검토 (병렬)
            reviews = self._parallel_reviews(
                session_id,
                other_ais,
                claude_report,
                curated_data,
                round_num
            )

            if not reviews:
                print("⚠️  검토자가 없습니다. CLAUDE REPORT를 최종 결과로 사용합니다.")
                break

            # 4b. CLAUDE가 검토를 읽고 판단
            decision = self._claude_refine(
                session_id,
                claude_model,
                claude_report,
                reviews,
                round_num
            )

            # 4c. CLAUDE 판단에 따라 분기
            if decision["no_changes_needed"]:
                print("\n[CLAUDE] ✓ 더 이상 수정할 내용 없음")
                print()

                # 4d. Consensus 체크
                consensus = self._check_consensus(
                    session_id,
                    other_ais,
                    claude_report
                )

                if consensus["agreed"]:
                    print("✅ 합의 완료! 모든 AI가 최종 REPORT에 동의했습니다.")
                    break
                else:
                    print("⚠️  일부 AI가 동의하지 않습니다:")
                    for ai_name in consensus["disagreed_ais"]:
                        print(f"   • {ai_name.upper()}")

                    if round_num < max_rounds:
                        print(f"\n→ Round {round_num + 1}로 진행합니다...")
                    else:
                        print("\n⚠️  Max rounds 도달. 현재 REPORT를 최종 결과로 사용합니다.")
            else:
                # 4e. REPORT 수정 후 다음 Round
                claude_report = decision["refined_report"]
                print(f"\n[CLAUDE] ✏️ REPORT 수정 완료 → Round {round_num + 1}로 진행")

        # 5. 최종 REPORT 저장
        final_result = self._save_final_report(
            session_id,
            claude_report,
            base_branch,
            target_branch
        )

        return final_result

    def _claude_initial_report(
        self,
        session_id: str,
        claude_model: AIModel,
        curated_data: str
    ) -> str:
        """CLAUDE 초기 REPORT 작성 (Round 1)"""
        print("[CLAUDE] 📝 코드 변경사항 분석 중...")

        prompt = generate_claude_initial_report_prompt(
            session_id=session_id,
            curated_data=curated_data
        )

        try:
            response = self.ai_client.call(
                model=claude_model,
                prompt=prompt,
                max_tokens=4000
            )

            # MCP에 저장
            self.mcp_manager.call_tool(
                "review",
                "submit_review",
                session_id=session_id,
                ai_name="CLAUDE",
                review=response
            )

            # 통계 추출
            stats = self._extract_stats(response)

            print(f"[CLAUDE] ✅ 초기 REPORT 작성 완료 ({len(response):,}자)")
            print(f"   → Critical: {stats['critical']}개")
            print(f"   → Major: {stats['major']}개")
            print(f"   → Minor: {stats['minor']}개")
            print()

            return response

        except Exception as e:
            print(f"[CLAUDE] ❌ 에러 발생: {e}")
            raise

    def _parallel_reviews(
        self,
        session_id: str,
        other_ais: Dict[str, AIModel],
        claude_report: str,
        curated_data: str,
        round_num: int
    ) -> list:
        """다른 AI들이 CLAUDE REPORT를 병렬로 검토"""
        if not other_ais:
            return []

        print(f"🔍 {len(other_ais)}개 AI가 CLAUDE REPORT를 검토합니다:")
        for ai_name in other_ais.keys():
            print(f"   • {ai_name.upper()}")
        print()

        reviews = []

        with ThreadPoolExecutor(max_workers=len(other_ais)) as executor:
            futures = {}

            for ai_name, ai_model in other_ais.items():
                future = executor.submit(
                    self._single_review,
                    session_id,
                    ai_name,
                    ai_model,
                    claude_report,
                    curated_data
                )
                futures[future] = ai_name

            # 병렬 실행 결과 수집
            for future in as_completed(futures):
                ai_name = futures[future]
                try:
                    review = future.result()
                    reviews.append({
                        "ai_name": ai_name,
                        "review": review
                    })
                    print(f"[{ai_name.upper()}] ✅ 검토 완료")
                except Exception as e:
                    print(f"[{ai_name.upper()}] ❌ 에러: {e}")

        print()
        return reviews

    def _single_review(
        self,
        session_id: str,
        ai_name: str,
        ai_model: AIModel,
        claude_report: str,
        curated_data: str
    ) -> str:
        """단일 AI가 CLAUDE REPORT 검토"""
        print(f"[{ai_name.upper()}] 🔍 검토 시작...")

        prompt = generate_reviewer_critique_prompt(
            session_id=session_id,
            ai_name=ai_name,
            claude_report=claude_report,
            curated_data=curated_data
        )

        response = self.ai_client.call(
            model=ai_model,
            prompt=prompt,
            max_tokens=3000
        )

        # MCP에 저장
        self.mcp_manager.call_tool(
            "review",
            "submit_review",
            session_id=session_id,
            ai_name=ai_name,
            review=response
        )

        return response

    def _claude_refine(
        self,
        session_id: str,
        claude_model: AIModel,
        current_report: str,
        reviews: list,
        round_num: int
    ) -> dict:
        """CLAUDE가 검토를 반영하여 REPORT 수정 판단"""
        print("[CLAUDE] 🤔 검토 내용 반영 판단 중...")

        prompt = generate_claude_refinement_prompt(
            session_id=session_id,
            current_report=current_report,
            reviews=reviews,
            round_num=round_num
        )

        response = self.ai_client.call(
            model=claude_model,
            prompt=prompt,
            max_tokens=5000
        )

        # MCP에 저장
        self.mcp_manager.call_tool(
            "review",
            "submit_review",
            session_id=session_id,
            ai_name="CLAUDE",
            review=response
        )

        # 판단 파싱
        if "NO_CHANGES_NEEDED" in response or "NO CHANGES NEEDED" in response:
            return {
                "no_changes_needed": True,
                "refined_report": current_report
            }
        else:
            # Refined Report 추출
            refined_report = self._extract_refined_report(response, current_report)
            return {
                "no_changes_needed": False,
                "refined_report": refined_report
            }

    def _check_consensus(
        self,
        session_id: str,
        other_ais: Dict[str, AIModel],
        claude_final_report: str
    ) -> dict:
        """다른 AI들이 CLAUDE의 최종 REPORT에 동의하는지 확인"""
        if not other_ais:
            return {"agreed": True, "disagreed_ais": []}

        print("🤝 최종 합의 확인 중...")
        print()

        agreements = []
        disagreed_ais = []

        with ThreadPoolExecutor(max_workers=len(other_ais)) as executor:
            futures = {}

            for ai_name, ai_model in other_ais.items():
                future = executor.submit(
                    self._check_single_agreement,
                    session_id,
                    ai_name,
                    ai_model,
                    claude_final_report
                )
                futures[future] = ai_name

            for future in as_completed(futures):
                ai_name = futures[future]
                try:
                    agreed = future.result()
                    agreements.append(agreed)

                    if agreed:
                        print(f"[{ai_name.upper()}] ✅ 최종 REPORT에 동의")
                    else:
                        print(f"[{ai_name.upper()}] ❌ 동의하지 않음")
                        disagreed_ais.append(ai_name)
                except Exception as e:
                    print(f"[{ai_name.upper()}] ❌ 에러: {e}")
                    disagreed_ais.append(ai_name)

        print()
        return {
            "agreed": all(agreements) if agreements else True,
            "disagreed_ais": disagreed_ais
        }

    def _check_single_agreement(
        self,
        session_id: str,
        ai_name: str,
        ai_model: AIModel,
        claude_final_report: str
    ) -> bool:
        """단일 AI가 CLAUDE REPORT에 동의하는지 확인"""
        prompt = generate_consensus_check_prompt(
            session_id=session_id,
            ai_name=ai_name,
            claude_final_report=claude_final_report
        )

        response = self.ai_client.call(
            model=ai_model,
            prompt=prompt,
            max_tokens=2000
        )

        # MCP에 저장
        self.mcp_manager.call_tool(
            "review",
            "submit_review",
            session_id=session_id,
            ai_name=ai_name,
            review=response
        )

        # YES/NO 파싱
        return "DECISION: YES" in response or "# DECISION: YES" in response

    def _extract_stats(self, report: str) -> dict:
        """리포트에서 통계 추출"""
        critical = len(re.findall(r'\[CRITICAL\]|\*\*Critical', report, re.IGNORECASE))
        major = len(re.findall(r'\[MAJOR\]|\*\*Major', report, re.IGNORECASE))
        minor = len(re.findall(r'\[MINOR\]|\*\*Minor', report, re.IGNORECASE))

        return {
            "critical": critical,
            "major": major,
            "minor": minor
        }

    def _extract_refined_report(self, decision_text: str, fallback: str) -> str:
        """CLAUDE의 refinement decision에서 refined report 추출"""
        # "## Refined Report" 섹션 찾기
        match = re.search(
            r'## Refined Report\s*\n(.*)',
            decision_text,
            re.DOTALL | re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

        # fallback: DECISION 이후 전체 텍스트
        match = re.search(
            r'REPORT_NEEDS_REFINEMENT.*?\n(.*)',
            decision_text,
            re.DOTALL
        )

        if match:
            return match.group(1).strip()

        # 최후의 fallback: 이전 report 유지
        return fallback

    def _save_final_report(
        self,
        session_id: str,
        final_report: str,
        base_branch: str,
        target_branch: str
    ) -> dict:
        """최종 REPORT를 파일로 저장"""
        import datetime
        import os

        # 저장 디렉토리 생성
        reviews_dir = "reviews"
        os.makedirs(reviews_dir, exist_ok=True)

        # 파일명 생성
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"review_{timestamp}_final.md"
        filepath = os.path.join(reviews_dir, filename)

        # REPORT 헤더 추가
        header = f"""# Code Review Report

**Session ID**: `{session_id}`
**Base Branch**: `{base_branch}`
**Target Branch**: `{target_branch}`
**Generated**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Review Type**: CLAUDE-Led Iterative Review

---

"""

        # 파일 저장
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header)
            f.write(final_report)

        # MCP에 최종화 기록
        self.mcp_manager.call_tool(
            "review",
            "finalize_review",
            session_id=session_id,
            final_review=final_report
        )

        return {
            "session_id": session_id,
            "final_review": final_report,
            "final_review_file": filepath,
            "status": "success"
        }
