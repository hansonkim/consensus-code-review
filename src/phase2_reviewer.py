"""Phase 2: 비판적 검증 모듈

각 AI가 다른 AI의 리뷰를 검증하는 Phase 2를 담당합니다.
"""

import os
import sys
from typing import Dict, List

# ai_cli_tools 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_cli_tools import AIClient, AIModel


class Phase2Reviewer:
    """Phase 2 비판적 검증 실행기"""

    def __init__(
        self,
        ai_client: AIClient,
        max_rounds: int = 3,
        allow_early_exit: bool = True,
        verbose: bool = False,
    ):
        """초기화

        Args:
            ai_client: AI 클라이언트
            max_rounds: 최대 검증 라운드 수
            allow_early_exit: 조기 종료 허용 여부
            verbose: 상세 출력 여부
        """
        self.ai_client = ai_client
        self.max_rounds = max_rounds
        self.allow_early_exit = allow_early_exit
        self.verbose = verbose

    def execute(
        self, initial_reviews: Dict[str, str], available_ais: Dict[str, AIModel]
    ) -> List[Dict[str, str]]:
        """Phase 2 실행 (순차 라운드)

        Args:
            initial_reviews: Phase 1 리뷰 결과
            available_ais: 사용 가능한 AI 모델들

        Returns:
            라운드별 검증 결과 리스트
        """
        print("\n" + "=" * 70)
        print("Phase 2: 비판적 검증")
        print("=" * 70)
        print(f"최대 라운드: {self.max_rounds}")
        print(f"조기 종료: {'허용' if self.allow_early_exit else '비활성'}")
        print()

        verification_history = []

        for round_num in range(1, self.max_rounds + 1):
            print(f"\n--- Round {round_num}/{self.max_rounds} ---")

            round_verifications = {}

            for ai_name, ai_model in available_ais.items():
                # 자신을 제외한 다른 AI들의 리뷰
                other_reviews = {
                    name: review
                    for name, review in initial_reviews.items()
                    if name != ai_name and review
                }

                if not other_reviews:
                    continue

                print(f"[{ai_name}] 검증 시작...")

                # 검증 프롬프트 생성
                prompt = self._generate_verification_prompt(
                    ai_name=ai_name,
                    own_review=initial_reviews.get(ai_name, ""),
                    other_reviews=other_reviews,
                    round_num=round_num,
                )

                # Agent 지정
                agents = ["Explore", "Observe", "Orient"]

                # AI 호출
                try:
                    response = self.ai_client.call_ai_with_retry(
                        prompt, ai_model, agents
                    )
                    round_verifications[ai_name] = response
                    print(f"[{ai_name}] ✓ 검증 완료")
                except Exception as e:
                    print(f"[{ai_name}] ✗ 검증 실패: {e}")
                    round_verifications[ai_name] = ""

            verification_history.append(
                {"round": round_num, "verifications": round_verifications}
            )

            # 조기 종료 체크 (2라운드 이후)
            if round_num >= 2 and self.allow_early_exit:
                if self._check_consensus_ready(round_verifications):
                    print(f"\n✓ 모든 리뷰어가 합의 준비 완료 (Round {round_num})")
                    break

        print(f"\nPhase 2 완료: {len(verification_history)}개 라운드 실행\n")
        return verification_history

    def _generate_verification_prompt(
        self,
        ai_name: str,
        own_review: str,
        other_reviews: Dict[str, str],
        round_num: int,
    ) -> str:
        """검증 프롬프트 생성

        Args:
            ai_name: 현재 AI 이름
            own_review: 자신의 리뷰
            other_reviews: 다른 AI들의 리뷰
            round_num: 현재 라운드 번호

        Returns:
            프롬프트 문자열
        """
        prompt = f"""# 코드 리뷰 검증 요청 (Phase 2: Round {round_num})

당신({ai_name})은 다른 AI 리뷰어들의 리뷰를 비판적으로 검증하는 역할을 맡았습니다.

## 당신의 초기 리뷰

{own_review}

## 다른 리뷰어들의 리뷰

"""

        for reviewer_name, review in other_reviews.items():
            prompt += f"""
### {reviewer_name}의 리뷰

{review}

---
"""

        prompt += """
## 검증 지침

다른 리뷰어들의 지적사항을 철저히 검증하고 다음을 확인해주세요:

1. **논리적 타당성**
   - 지적 내용이 논리적으로 타당한가?
   - 근거가 명확하고 구체적인가?

2. **정확성**
   - 코드에 대한 이해가 정확한가?
   - 잘못된 가정이나 오해는 없는가?

3. **과장 여부**
   - 문제의 심각도가 적절하게 평가되었는가?
   - 과도하게 부풀려진 이슈는 없는가?

4. **실행 가능성**
   - 제안한 해결책이 실제로 작동하는가?
   - 부작용이나 다른 문제를 야기하지 않는가?

5. **중복 또는 누락**
   - 여러 리뷰어가 같은 이슈를 중복해서 지적했는가?
   - 중요한 이슈가 누락되었는가?

## 출력 형식

### 동의하는 이슈
다른 리뷰어의 지적 중 타당하다고 판단되는 것들을 나열:
- [리뷰어명] 이슈 제목: 동의 이유

### 반대하는 이슈
다른 리뷰어의 지적 중 부정확하거나 과장되었다고 판단되는 것들:
- [리뷰어명] 이슈 제목: 반대 이유 및 근거

### 심각도 조정 제안
심각도가 부적절하다고 판단되는 이슈:
- [리뷰어명] 이슈 제목: 현재 심각도 → 제안 심각도 (이유)

### 추가 발견 사항
다른 리뷰어들이 놓친 중요한 이슈가 있다면 추가:

객관적이고 건설적인 검증을 수행해주세요. 감정적이거나 주관적인 판단은 지양하고,
코드와 기술적 근거에 기반한 검증을 제공해주세요.
"""

        return prompt

    def _check_consensus_ready(self, verifications: Dict[str, str]) -> bool:
        """합의 준비 여부 확인

        Args:
            verifications: 현재 라운드 검증 결과

        Returns:
            모든 AI가 합의 준비되었는지 여부
        """
        # 간단한 휴리스틱: 모든 AI가 검증을 완료했으면 합의 준비된 것으로 간주
        # 실제로는 더 정교한 로직이 필요할 수 있음 (예: "반대하는 이슈"가 없는 경우)
        if not verifications:
            return False

        # 모든 AI가 응답했는지 확인
        return all(response for response in verifications.values())
