"""Phase 1: MCP-Orchestrated Multi-Round Review

AI에게 변경 내역을 전달하지 않고, 해야 할 일만 알려줍니다.
MCP Server가 AI들 간의 협업을 중재하며 합의점을 찾습니다.
"""

import os
import sys
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ai_cli_tools 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_cli_tools import AIClient, AIModel
from src.mcp import MCPManager
from src.mcp.minimal_prompt import (
    generate_initial_review_prompt,
    generate_round2_prompt,
    generate_final_consensus_prompt_with_calculated_consensus
)
from src.mcp.consensus_calculator import calculate_consensus_from_session
from src.data_curator import DataCurator


class MCPOrchestratedReviewer:
    """MCP 오케스트레이션 기반 코드 리뷰어"""

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
        max_rounds: int = 3
    ) -> Dict:
        """MCP 오케스트레이션 실행

        Args:
            available_ais: 사용 가능한 AI 모델들
            base_branch: 기준 브랜치
            target_branch: 비교 대상 브랜치
            max_rounds: 최대 라운드 수

        Returns:
            최종 합의 리뷰 결과
        """
        print("\n" + "=" * 70)
        print("MCP-Orchestrated Multi-Round Code Review")
        print("=" * 70)
        print(f"참여 AI: {len(available_ais)}개")
        print(f"Base: {base_branch} → Target: {target_branch}")
        print(f"최대 라운드: {max_rounds}")
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

        # 2. Round 1: 독립적 초기 리뷰
        print("=" * 70)
        print("Round 1: Independent Review")
        print("=" * 70)

        round1_reviews = self._execute_round1(
            session_id,
            available_ais,
            base_branch,
            target_branch
        )

        # 모든 AI가 제출했는지 확인
        consensus = self.mcp_manager.call_tool(
            "review",
            "check_consensus",
            session_id=session_id
        )

        print(f"\n✅ Round 1 완료: {consensus['submitted']}/{consensus['total_ais']} AI 제출")
        print()

        # 3. Round 2: 상호 검토 및 합의 구축
        if max_rounds >= 2:
            print("=" * 70)
            print("Round 2: Peer Review & Consensus Building")
            print("=" * 70)

            # 다음 라운드로 진행
            self.mcp_manager.call_tool(
                "review",
                "advance_round",
                session_id=session_id
            )

            round2_reviews = self._execute_round2(
                session_id,
                available_ais
            )

            consensus = self.mcp_manager.call_tool(
                "review",
                "check_consensus",
                session_id=session_id
            )

            print(f"\n✅ Round 2 완료: {consensus['submitted']}/{consensus['total_ais']} AI 제출")
            print()

        # 4. Final Round: 최종 합의 리포트
        if max_rounds >= 3:
            print("=" * 70)
            print("Final Round: Consensus Report")
            print("=" * 70)

            # 다음 라운드로 진행
            self.mcp_manager.call_tool(
                "review",
                "advance_round",
                session_id=session_id
            )

            final_review = self._execute_final_round(
                session_id,
                available_ais
            )

            # 최종 리뷰 확정
            self.mcp_manager.call_tool(
                "review",
                "finalize_review",
                session_id=session_id,
                final_review=final_review
            )

            print(f"\n✅ 최종 합의 완료")
            print()

        # 5. 세션 정보 반환
        session_info = self.mcp_manager.call_tool(
            "review",
            "get_session_info",
            session_id=session_id
        )

        return {
            "session_id": session_id,
            "session_info": session_info,
            "round1_reviews": round1_reviews,
            "round2_reviews": round2_reviews if max_rounds >= 2 else None,
            "final_review": final_review if max_rounds >= 3 else None
        }

    def _execute_round1(
        self,
        session_id: str,
        available_ais: Dict[str, AIModel],
        base_branch: str,
        target_branch: str
    ) -> Dict[str, str]:
        """Round 1 실행 - Python 큐레이션 + AI 리뷰

        Pure Task Delegation:
        - Python: Git 조회, 파일 선택, 토큰 관리
        - AI: 큐레이션된 데이터 분석 및 리뷰 작성
        """

        # 1. Python이 변경사항 큐레이션 (한 번만)
        print("\n" + "=" * 70)
        print("Step 1: Python Data Curation")
        print("=" * 70)

        curator = DataCurator(token_budget=20000)
        curated_data_dict = curator.curate_changes(base_branch, target_branch)
        curated_data_formatted = curator.format_curated_data(curated_data_dict)

        print(f"\n✅ 큐레이션 완료:")
        print(f"   - 전체 파일: {curated_data_dict['summary']['total_files']}")
        print(f"   - 선택된 파일: {curated_data_dict['summary']['curated_files']}")
        print(f"   - 토큰 사용: {curated_data_dict['summary']['token_usage']:,} / 20,000")

        # 2. AI들이 동일한 큐레이션 데이터로 병렬 리뷰
        print("\n" + "=" * 70)
        print("Step 2: AI Independent Reviews (Parallel)")
        print("=" * 70)
        print()

        reviews = {}
        review_summaries = {}

        # 참여 AI 목록 출력
        print(f"\n🚀 {len(available_ais)}개 AI를 병렬로 실행합니다:")
        for ai_name, ai_model in available_ais.items():
            print(f"   • {ai_name.upper()}: {ai_model.model_id}")
        print()

        with ThreadPoolExecutor(max_workers=len(available_ais)) as executor:
            futures = {}

            for ai_name, ai_model in available_ais.items():
                # Prompt에 큐레이션된 데이터 포함 - AI는 탐색 불필요!
                prompt = generate_initial_review_prompt(
                    session_id=session_id,
                    ai_name=ai_name,
                    curated_data=curated_data_formatted
                )

                print(f"[{ai_name.upper()}] 🔄 독립적 리뷰 시작...")
                print(f"   → 큐레이션된 {curated_data_dict['summary']['curated_files']}개 파일 분석 중")
                if self.verbose:
                    print(f"   → 프롬프트: {len(prompt):,} 문자")

                # AI 호출 (탐색 불필요, 리뷰만)
                future = executor.submit(
                    self.ai_client.call_ai_with_retry,
                    prompt,
                    ai_model,
                    []  # No agents needed - just review writing
                )
                futures[future] = ai_name

            # 결과 수집 + 실시간 progress 폴링
            import time
            last_check = time.time()
            completed_count = 0
            total_ais = len(futures)

            print()
            print("⏳ AI 리뷰 진행 중... (실시간 progress)")
            print()

            for future in as_completed(futures):
                # Progress 폴링 (2초마다)
                if time.time() - last_check > 2:
                    last_check = self._poll_and_display_progress(session_id, last_check)

                ai_name = futures[future]
                try:
                    review = future.result(timeout=600)
                    reviews[ai_name] = review

                    # 리뷰 요약 추출 (간단한 통계)
                    summary = self._extract_review_summary(review)
                    review_summaries[ai_name] = summary

                    # MCP에 리뷰 제출
                    self.mcp_manager.call_tool(
                        "review",
                        "submit_review",
                        session_id=session_id,
                        ai_name=ai_name,
                        review=review
                    )

                    completed_count += 1
                    print(f"\n[{ai_name.upper()}] ✅ 리뷰 완료 ({completed_count}/{total_ais})")
                    print(f"   → Critical: {summary['critical']}개")
                    print(f"   → Major: {summary['major']}개")
                    print(f"   → Minor: {summary['minor']}개")
                    print(f"   → 총 {len(review):,} 자")

                except Exception as e:
                    print(f"\n[{ai_name.upper()}] ❌ 리뷰 실패: {e}")
                    reviews[ai_name] = ""
                    review_summaries[ai_name] = {"critical": 0, "major": 0, "minor": 0}

            # 마지막 progress 체크
            self._poll_and_display_progress(session_id, last_check)

        # Round 1 요약 출력
        print("\n" + "=" * 70)
        print("Round 1 Summary")
        print("=" * 70)
        print()
        print("각 AI가 발견한 이슈:")
        for ai_name in available_ais.keys():
            summary = review_summaries.get(ai_name, {"critical": 0, "major": 0, "minor": 0})
            print(f"  [{ai_name.upper()}] "
                  f"Critical: {summary['critical']}개 | "
                  f"Major: {summary['major']}개 | "
                  f"Minor: {summary['minor']}개")

        total_critical = sum(s['critical'] for s in review_summaries.values())
        total_major = sum(s['major'] for s in review_summaries.values())
        total_minor = sum(s['minor'] for s in review_summaries.values())

        print()
        print(f"총 발견된 이슈 (중복 포함):")
        print(f"  Critical: {total_critical}개")
        print(f"  Major: {total_major}개")
        print(f"  Minor: {total_minor}개")
        print()
        print("→ 다음 단계: AI들이 서로의 리뷰를 검토하고 합의 구축")

        return reviews

    def _execute_round2(
        self,
        session_id: str,
        available_ais: Dict[str, AIModel]
    ) -> Dict[str, str]:
        """Round 2 실행 - 상호 검토 및 합의 구축"""

        print()
        print("각 AI가 다른 AI들의 리뷰를 비판적으로 검토합니다...")
        print()

        reviews = {}
        consensus_stats = {}

        with ThreadPoolExecutor(max_workers=len(available_ais)) as executor:
            futures = {}

            for ai_name, ai_model in available_ais.items():
                # 다른 AI들의 리뷰 가져오기
                other_reviews = self.mcp_manager.call_tool(
                    "review",
                    "get_other_reviews",
                    session_id=session_id,
                    ai_name=ai_name
                )

                # Round 2 prompt 생성
                prompt = generate_round2_prompt(
                    session_id=session_id,
                    ai_name=ai_name,
                    other_reviews=other_reviews
                )

                other_ai_names = [r['ai_name'].upper() for r in other_reviews]
                print(f"[{ai_name.upper()}] 🔍 비판적 검토 시작")
                print(f"   → 검토 대상: {', '.join(other_ai_names)}")

                future = executor.submit(
                    self.ai_client.call_ai_with_retry,
                    prompt,
                    ai_model,
                    []  # No agents needed
                )
                futures[future] = ai_name

            # 결과 수집 + 실시간 progress 폴링
            import time
            last_check = time.time()
            completed_count = 0
            total_ais = len(futures)

            print()
            print("⏳ 비판적 검토 진행 중... (실시간 progress)")
            print()

            for future in as_completed(futures):
                # Progress 폴링 (2초마다)
                if time.time() - last_check > 2:
                    last_check = self._poll_and_display_progress(session_id, last_check)

                ai_name = futures[future]
                try:
                    review = future.result(timeout=600)
                    reviews[ai_name] = review

                    # 합의 통계 추출
                    stats = self._extract_consensus_stats(review)
                    consensus_stats[ai_name] = stats

                    # MCP에 Round 2 리뷰 제출
                    self.mcp_manager.call_tool(
                        "review",
                        "submit_review",
                        session_id=session_id,
                        ai_name=ai_name,
                        review=review
                    )

                    completed_count += 1
                    print(f"\n[{ai_name.upper()}] ✅ 검토 완료 ({completed_count}/{total_ais})")
                    print(f"   → 동의: {stats['agreed']}개 이슈")
                    print(f"   → 부분 동의: {stats['partial']}개 이슈")
                    print(f"   → 반대: {stats['disagreed']}개 이슈")
                    if stats['new_issues'] > 0:
                        print(f"   → 새로 발견: {stats['new_issues']}개 이슈")

                except Exception as e:
                    print(f"\n[{ai_name.upper()}] ❌ 검토 실패: {e}")
                    reviews[ai_name] = ""
                    consensus_stats[ai_name] = {
                        "agreed": 0, "partial": 0, "disagreed": 0, "new_issues": 0
                    }

            # 마지막 progress 체크
            self._poll_and_display_progress(session_id, last_check)

        # Round 2 요약
        print("\n" + "=" * 70)
        print("Round 2 Summary: Consensus Building")
        print("=" * 70)
        print()
        print("각 AI의 동의/반대 분포:")
        for ai_name in available_ais.keys():
            stats = consensus_stats.get(ai_name, {})
            total_reviewed = stats.get('agreed', 0) + stats.get('partial', 0) + stats.get('disagreed', 0)
            if total_reviewed > 0:
                agree_pct = (stats.get('agreed', 0) / total_reviewed) * 100
                print(f"  [{ai_name.upper()}] "
                      f"동의 {agree_pct:.0f}% | "
                      f"부분동의 {stats.get('partial', 0)}개 | "
                      f"반대 {stats.get('disagreed', 0)}개")

        print()
        print("→ 다음 단계: Python이 자동으로 consensus 계산 후 최종 리포트 생성")

        return reviews

    def _execute_final_round(
        self,
        session_id: str,
        available_ais: Dict[str, AIModel]
    ) -> str:
        """Final Round 실행 - Python이 consensus 계산 후 AI가 리포트 작성"""

        # 1. 모든 라운드의 리뷰 가져오기
        session_info = self.mcp_manager.call_tool(
            "review",
            "get_session_info",
            session_id=session_id
        )

        total_ais = len(session_info.get('participating_ais', []))

        print()
        print("=" * 70)
        print(f"Step 3: Python Consensus Calculation ({total_ais} AIs)")
        print("=" * 70)
        print()
        print("📊 모든 AI 리뷰를 분석하여 합의 수준을 자동 계산 중...")
        print()

        # 2. Python이 자동으로 consensus 계산
        try:
            consensus, calculator = calculate_consensus_from_session(session_info)

            # Consensus 결과 포맷
            consensus_text = calculator.format_consensus(consensus, total_ais)

            # 통계 출력
            print("✅ Consensus 계산 완료!")
            print()
            print("합의 수준별 이슈 분류:")
            print()

            # Critical issues
            if consensus['critical']:
                print(f"  🚨 Critical Issues: {len(consensus['critical'])}개 (100% 동의 - 반드시 수정)")
                for issue in consensus['critical'][:3]:  # 상위 3개만 출력
                    print(f"     - {issue.title} ({issue.location})")
                    print(f"       동의: {', '.join(sorted(issue.agreed_by))}")
                if len(consensus['critical']) > 3:
                    print(f"     ... 외 {len(consensus['critical']) - 3}개")
                print()

            # Major issues
            if consensus['major']:
                print(f"  ⚠️  Major Issues: {len(consensus['major'])}개 (≥66% 동의 - 수정 권장)")
                for issue in consensus['major'][:3]:
                    agreement_pct = len(issue.agreed_by) / total_ais * 100
                    print(f"     - {issue.title} ({issue.location})")
                    print(f"       동의: {', '.join(sorted(issue.agreed_by))} ({agreement_pct:.0f}%)")
                if len(consensus['major']) > 3:
                    print(f"     ... 외 {len(consensus['major']) - 3}개")
                print()

            # Minor issues
            if consensus['minor']:
                print(f"  📝 Minor Issues: {len(consensus['minor'])}개 (≥33% 동의 - 검토 권장)")
                agreement_counts = {}
                for issue in consensus['minor']:
                    count = len(issue.agreed_by)
                    agreement_counts[count] = agreement_counts.get(count, 0) + 1
                for count in sorted(agreement_counts.keys(), reverse=True):
                    print(f"     - {agreement_counts[count]}개 이슈: {count}/{total_ais} AI 동의")
                print()

            # Disputed issues
            if consensus['disputed']:
                print(f"  🤔 Disputed Issues: {len(consensus['disputed'])}개 (의견 불일치 - 팀 판단 필요)")
                for issue in consensus['disputed'][:2]:
                    print(f"     - {issue.title} ({issue.location})")
                    print(f"       찬성: {', '.join(sorted(issue.agreed_by))} | "
                          f"반대: {', '.join(sorted(issue.disagreed_by))}")
                if len(consensus['disputed']) > 2:
                    print(f"     ... 외 {len(consensus['disputed']) - 2}개")
                print()

            total_issues = (len(consensus['critical']) + len(consensus['major']) +
                          len(consensus['minor']) + len(consensus['disputed']))
            print(f"총 {total_issues}개 unique 이슈 발견 (중복 제거 완료)")

        except Exception as e:
            print(f"⚠️  Consensus 계산 실패: {e}")
            print(f"ℹ️  Fallback: AI가 직접 계산하게 함")
            import traceback
            traceback.print_exc()
            # Fallback to old method if consensus calculation fails
            consensus_text = "Python consensus calculation failed. Please calculate manually."

        # 3. 첫 번째 AI가 최종 리포트 작성 (계산된 consensus 기반)
        print()
        print("=" * 70)
        print("Step 4: Final Report Writing")
        print("=" * 70)
        print()

        first_ai_name = list(available_ais.keys())[0]
        first_ai_model = available_ais[first_ai_name]

        print(f"[{first_ai_name}]를 최종 리포트 작성자로 선정")
        print()
        print("Python이 계산한 consensus를 바탕으로 전문적인 최종 리포트 작성 중...")
        print("   → Critical 이슈: 반드시 수정 필요")
        print("   → Major 이슈: 수정 권장")
        print("   → Minor 이슈: 검토 권장")
        print("   → Disputed 이슈: 팀 판단 필요")
        print()

        # Final consensus prompt (with calculated consensus)
        prompt = generate_final_consensus_prompt_with_calculated_consensus(
            session_id=session_id,
            ai_name=first_ai_name,
            consensus_text=consensus_text,
            total_ais=total_ais
        )

        print("⏳ 최종 리포트 작성 중... (실시간 progress)")
        print()

        # 병렬로 실행하면서 progress 폴링
        import time
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self.ai_client.call_ai_with_retry,
                prompt,
                first_ai_model,
                []  # No agents needed
            )

            # Progress 폴링 (2초마다)
            last_check = time.time()
            while not future.done():
                time.sleep(2)
                if time.time() - last_check > 2:
                    last_check = self._poll_and_display_progress(session_id, last_check)

            final_review = future.result()

            # 마지막 progress 체크
            self._poll_and_display_progress(session_id, last_check)

        print(f"\n✅ 최종 리포트 완료!")
        print(f"   → 길이: {len(final_review):,} 자")
        print(f"   → 작성자: {first_ai_name}")
        print(f"   → 기반: {total_ais}개 AI의 consensus")

        return final_review

    def _extract_review_summary(self, review: str) -> Dict[str, int]:
        """리뷰에서 이슈 개수 추출"""
        import re

        critical_count = len(re.findall(r'\[CRITICAL\]', review, re.IGNORECASE))
        major_count = len(re.findall(r'\[MAJOR\]', review, re.IGNORECASE))
        minor_count = len(re.findall(r'\[MINOR\]', review, re.IGNORECASE))

        return {
            "critical": critical_count,
            "major": major_count,
            "minor": minor_count
        }

    def _extract_consensus_stats(self, review: str) -> Dict[str, int]:
        """Round 2 리뷰에서 동의/반대 통계 추출"""
        import re

        # ✅, ⚠️, ❌ 마커로 동의/반대 카운트
        agreed = len(re.findall(r'✅', review))
        partial = len(re.findall(r'⚠️', review))
        disagreed = len(re.findall(r'❌', review))

        # [NEW] 마커로 새로 발견한 이슈 카운트
        new_issues = len(re.findall(r'\[NEW\]', review, re.IGNORECASE))

        return {
            "agreed": agreed,
            "partial": partial,
            "disagreed": disagreed,
            "new_issues": new_issues
        }

    def _poll_and_display_progress(self, session_id: str, last_check: float = 0) -> float:
        """실시간 진행 상황을 폴링하고 출력

        Args:
            session_id: 세션 ID
            last_check: 마지막 확인 timestamp

        Returns:
            현재 timestamp (다음 폴링에 사용)
        """
        import time

        try:
            # MCP를 통해 progress 조회
            progress_result = self.mcp_manager.call_tool(
                "review",
                "get_progress",
                session_id=session_id,
                since=last_check
            )

            # 새로운 progress 출력
            for update in progress_result.get("updates", []):
                ai_name = update["ai_name"]
                message = update["message"]
                print(f"  [{ai_name}] 📡 {message}")

        except Exception as e:
            # 에러는 조용히 무시 (progress는 선택사항)
            if self.verbose:
                print(f"  [Progress Poll Error] {e}")

        return time.time()
