"""Phase 1: 독립적 초기 리뷰 모듈

각 AI가 독립적으로 코드를 분석하는 Phase 1을 담당합니다.
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

# ai_cli_tools 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_cli_tools import AIClient, AIModel


class Phase1Reviewer:
    """Phase 1 독립적 초기 리뷰 실행기"""

    def __init__(self, ai_client: AIClient, use_mcp: bool = True, verbose: bool = False):
        """초기화

        Args:
            ai_client: AI 클라이언트
            use_mcp: MCP 사용 여부
            verbose: 상세 출력 여부
        """
        self.ai_client = ai_client
        self.use_mcp = use_mcp
        self.verbose = verbose

    def execute(
        self, files: List[str], available_ais: Dict[str, AIModel]
    ) -> Dict[str, str]:
        """Phase 1 실행 (병렬)

        Args:
            files: 리뷰할 파일 목록
            available_ais: 사용 가능한 AI 모델들

        Returns:
            {ai_name: review_response} 형태의 딕셔너리
        """
        print("\n" + "=" * 70)
        print("Phase 1: 독립적 초기 리뷰")
        print("=" * 70)
        print(f"참여 AI: {len(available_ais)}개")
        print(f"리뷰 파일: {len(files)}개")
        print()

        # 파일 내용 읽기
        code_content = self._read_files(files)

        # 빈 파일 필터링
        filtered_content = {k: v for k, v in code_content.items() if v.strip()}
        skipped = len(code_content) - len(filtered_content)

        if skipped > 0:
            print(f"⚠️  {skipped}개 파일 스킵 (빈 내용 또는 읽기 실패)")

        if not filtered_content:
            raise RuntimeError("읽을 수 있는 파일이 없습니다")

        print(f"✓ {len(filtered_content)}개 파일 리뷰 준비 완료\n")

        # 프롬프트 생성
        prompt = self._generate_initial_review_prompt(filtered_content, list(filtered_content.keys()))

        # 병렬 실행
        reviews = {}
        with ThreadPoolExecutor(max_workers=len(available_ais)) as executor:
            futures = {}

            for ai_name, ai_model in available_ais.items():
                print(f"[{ai_name}] 리뷰 시작...")

                # Agent 지정
                agents = ["Explore", "Observe", "Orient", "Security", "Performance"]

                # 비동기 실행
                future = executor.submit(
                    self.ai_client.call_ai_with_retry,
                    prompt,
                    ai_model,
                    agents,
                )
                futures[future] = ai_name

            # 결과 수집
            for future in as_completed(futures):
                ai_name = futures[future]
                try:
                    response = future.result(timeout=600)
                    reviews[ai_name] = response
                    print(f"[{ai_name}] ✓ 리뷰 완료 ({len(response)} 자)")
                except Exception as e:
                    print(f"[{ai_name}] ✗ 리뷰 실패: {e}")
                    reviews[ai_name] = ""

        print(f"\nPhase 1 완료: {len([r for r in reviews.values() if r])}개 AI 성공\n")
        return reviews

    def _read_files(self, files: List[str]) -> Dict[str, str]:
        """파일들 읽기

        Args:
            files: 파일 경로 리스트

        Returns:
            {파일명: 내용} 딕셔너리
        """
        content = {}
        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content[file_path] = f.read()
            except UnicodeDecodeError:
                # 바이너리 파일은 스킵
                if self.verbose:
                    print(f"⚠️  바이너리 파일 스킵: {file_path}")
            except Exception as e:
                print(f"⚠️  파일 읽기 실패 {file_path}: {e}")
                content[file_path] = ""

        return content

    def _generate_initial_review_prompt(
        self, code_content: Dict[str, str], files: List[str]
    ) -> str:
        """Phase 1 초기 리뷰 프롬프트 생성

        Args:
            code_content: 파일 내용 딕셔너리
            files: 파일 경로 리스트

        Returns:
            프롬프트 문자열

        Raises:
            RuntimeError: 프롬프트가 너무 클 때
        """
        # 프롬프트 크기 추정 (대략적)
        total_chars = sum(len(content) for content in code_content.values())
        estimated_tokens = total_chars // 4  # 대략 4 chars = 1 token

        # 경고 출력
        if estimated_tokens > 100_000:
            print(f"⚠️  경고: 프롬프트 크기가 매우 큽니다 (~{estimated_tokens:,} 토큰)")
            print(f"    일부 AI 모델은 컨텍스트 제한으로 실패할 수 있습니다")
            print(f"    파일 수: {len(files)}개, 총 문자: {total_chars:,}개\n")

        # 프롬프트 생성
        prompt = f"""# 코드 리뷰 요청 (Phase 1: 독립적 초기 리뷰)

당신은 전문적인 코드 리뷰어입니다. 다음 코드를 다각도로 분석하고 상세한 리뷰를 제공해주세요.

## 리뷰 대상
총 {len(files)}개 파일:
{chr(10).join(f"- {f}" for f in files)}

## 코드 내용

"""

        for file_path, content in code_content.items():
            prompt += f"""
### 파일: {file_path}

```
{content}
```

"""

        prompt += """
## 리뷰 지침

다음 관점에서 철저히 분석해주세요:

1. **보안 (Security)**
   - SQL Injection, XSS, CSRF 등 취약점
   - 인증/인가 문제
   - 민감 정보 노출
   - 안전하지 않은 암호화

2. **성능 (Performance)**
   - 비효율적인 알고리즘
   - 불필요한 반복 연산
   - 메모리 누수 가능성
   - 데이터베이스 쿼리 최적화

3. **코드 품질 (Quality)**
   - 가독성 및 유지보수성
   - 중복 코드
   - 복잡도 (Cyclomatic Complexity)
   - 네이밍 규칙

4. **아키텍처 (Architecture)**
   - 설계 원칙 위반 (SOLID, DRY, KISS)
   - 의존성 관리
   - 모듈화 및 관심사 분리

5. **버그 및 오류 처리**
   - 논리적 오류
   - 예외 처리 누락
   - 엣지 케이스 처리

## 출력 형식

발견한 각 이슈마다 다음 형식으로 작성해주세요:

---
### [심각도] 이슈 제목
**위치**: `파일명:라인번호` 또는 `파일명:시작라인-종료라인`
**설명**: 문제에 대한 상세 설명
**코드**:
```
문제가 되는 코드
```
**제안**:
```
개선된 코드
```
**근거**: 왜 이것이 문제인지, 어떻게 개선되는지 설명
---

**심각도 레벨**:
- CRITICAL: 즉시 수정 필요 (보안 취약점, 심각한 버그)
- MAJOR: 중요한 문제 (성능 저하, 설계 결함)
- MINOR: 개선 권장 (가독성, 코드 스타일)
- SUGGESTION: 선택적 개선 (리팩토링 제안)

구체적이고 실행 가능한 리뷰를 작성해주세요. 모호한 제안보다는 명확한 개선 방법을 제시해주세요.
"""

        return prompt
