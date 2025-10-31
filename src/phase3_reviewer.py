"""Phase 3: 최종 합의 모듈

검증된 리뷰들을 통합하여 최종 합의 문서를 생성하는 Phase 3을 담당합니다.
"""

import os
import sys
from typing import Any, Dict, List

# ai_cli_tools 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_cli_tools import AIClient, AIModel


class Phase3Reviewer:
    """Phase 3 최종 합의 생성기"""

    def __init__(self, ai_client: AIClient, verbose: bool = False):
        """초기화

        Args:
            ai_client: AI 클라이언트
            verbose: 상세 출력 여부
        """
        self.ai_client = ai_client
        self.verbose = verbose

    def execute(
        self,
        initial_reviews: Dict[str, str],
        verification_history: List[Dict[str, Any]],
        available_ais: Dict[str, AIModel],
    ) -> str:
        """Phase 3 실행

        Args:
            initial_reviews: Phase 1 리뷰 결과
            verification_history: Phase 2 검증 기록
            available_ais: 사용 가능한 AI 모델들

        Returns:
            최종 합의 리뷰 문자열
        """
        print("\n" + "=" * 70)
        print("Phase 3: 최종 합의 생성")
        print("=" * 70)
        print()

        # 대표 AI 선택 (첫 번째 AI 사용)
        representative_ai = list(available_ais.items())[0]
        ai_name, ai_model = representative_ai

        print(f"대표 AI: {ai_name}")
        print("통합 리뷰 생성 중...")

        # 합의 프롬프트 생성
        prompt = self._generate_consensus_prompt(
            initial_reviews, verification_history
        )

        # Agent 지정 (통합 작업에 적합한 Agent들)
        agents = ["Orient", "Code Review"]

        try:
            final_review = self.ai_client.call_ai_with_retry(prompt, ai_model, agents)
            print(f"✓ 최종 합의 리뷰 생성 완료 ({len(final_review)} 자)\n")
            return final_review
        except Exception as e:
            print(f"✗ 최종 합의 생성 실패: {e}\n")
            # 실패 시 초기 리뷰들을 단순 결합
            return self._fallback_merge(initial_reviews, verification_history)

    def _generate_consensus_prompt(
        self, initial_reviews: Dict[str, str], verification_history: List[Dict[str, Any]]
    ) -> str:
        """최종 합의 프롬프트 생성

        Args:
            initial_reviews: Phase 1 리뷰 결과
            verification_history: Phase 2 검증 기록

        Returns:
            프롬프트 문자열
        """
        prompt = """# 최종 합의 리뷰 생성 (Phase 3)

여러 AI 리뷰어들의 독립적 리뷰와 상호 검증 과정을 거쳐 최종 합의 리뷰를 생성해주세요.

## Phase 1: 초기 리뷰들

"""

        for ai_name, review in initial_reviews.items():
            if review:
                prompt += f"""
### {ai_name}의 리뷰

{review}

---
"""

        prompt += """
## Phase 2: 검증 과정

"""

        for round_info in verification_history:
            round_num = round_info["round"]
            verifications = round_info["verifications"]

            prompt += f"\n### Round {round_num}\n\n"

            for ai_name, verification in verifications.items():
                if verification:
                    prompt += f"""
#### {ai_name}의 검증

{verification}

---
"""

        prompt += """
## 최종 합의 리뷰 작성 지침

위의 모든 리뷰와 검증 과정을 종합하여 **합의된 이슈만** 포함한 최종 리뷰를 작성해주세요.

### 이슈 선정 기준

1. **여러 리뷰어가 동의한 이슈**: 2명 이상의 리뷰어가 지적한 이슈
2. **검증을 통과한 이슈**: Phase 2에서 다른 리뷰어들이 타당하다고 인정한 이슈
3. **반박되지 않은 이슈**: Phase 2에서 명확히 반박되지 않은 이슈

### 제외할 이슈

1. **과장된 이슈**: Phase 2에서 과장되었다고 지적된 이슈
2. **논리적 오류**: Phase 2에서 논리적 문제가 발견된 이슈
3. **단독 지적**: 한 리뷰어만 지적하고 다른 리뷰어들이 동의하지 않은 이슈

### 출력 형식

# 코드 리뷰 최종 합의 문서

## 📊 리뷰 요약

- 참여 리뷰어: [리뷰어 목록]
- 검증 라운드: [라운드 수]
- 발견된 이슈: [총 이슈 수]
  - Critical: [개수]
  - Major: [개수]
  - Minor: [개수]
  - Suggestion: [개수]

## 🔴 Critical Issues

각 이슈마다:

---
### [CRITICAL] 이슈 제목
**위치**: 파일:라인
**합의 리뷰어**: [AI1, AI2, ...]
**설명**: ...
**코드**:
```
...
```
**제안**:
```
...
```
**근거**: ...
---

## 🟡 Major Issues

(동일 형식)

## 🟢 Minor Issues

(동일 형식)

## 💡 Suggestions

(동일 형식)

## ✅ 종합 의견

전반적인 코드 품질 평가와 우선순위 개선 사항을 요약해주세요.

---

**중요**: 합의되지 않은 이슈는 포함하지 마세요. 객관적이고 검증된 이슈만 최종 리뷰에 담아주세요.
"""

        return prompt

    def _fallback_merge(
        self, initial_reviews: Dict[str, str], verification_history: List[Dict[str, Any]]
    ) -> str:
        """AI 호출 실패 시 대체 통합 방법

        Args:
            initial_reviews: Phase 1 리뷰 결과
            verification_history: Phase 2 검증 기록

        Returns:
            단순 결합된 리뷰 문자열
        """
        result = "# 코드 리뷰 최종 합의 문서 (Fallback)\n\n"
        result += "## ⚠️ 주의\n\n"
        result += "AI 통합 리뷰 생성에 실패하여 수동으로 리뷰를 결합했습니다.\n\n"

        result += "## Phase 1: 초기 리뷰들\n\n"
        for ai_name, review in initial_reviews.items():
            if review:
                result += f"### {ai_name}의 리뷰\n\n{review}\n\n---\n\n"

        result += "## Phase 2: 검증 과정\n\n"
        for round_info in verification_history:
            round_num = round_info["round"]
            verifications = round_info["verifications"]

            result += f"### Round {round_num}\n\n"

            for ai_name, verification in verifications.items():
                if verification:
                    result += f"#### {ai_name}의 검증\n\n{verification}\n\n---\n\n"

        return result
