"""마크다운 문서 생성 모듈

리뷰 결과를 마크다운 형식으로 저장합니다.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class MarkdownGenerator:
    """마크다운 문서 생성기"""

    def save_review_files(
        self,
        target_path: str,
        review_mode: str,
        files: List[str],
        initial_reviews: Dict[str, str],
        verification_history: List[Dict[str, Any]],
        final_review: str,
    ) -> tuple:
        """리뷰 문서를 2개의 마크다운 파일로 저장

        Args:
            target_path: 리뷰 대상 경로
            review_mode: 리뷰 모드
            files: 리뷰된 파일 목록
            initial_reviews: Phase 1 결과
            verification_history: Phase 2 검증 기록
            final_review: Phase 3 최종 리뷰

        Returns:
            (전체_리뷰_경로, 최종_리뷰_경로) 튜플
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_name = self._get_base_filename(target_path)

        # 1. 전체 리뷰 기록 (Phase 1-3 전체)
        full_path = f"{base_name}-review-{timestamp}.md"
        with open(full_path, "w", encoding="utf-8") as f:
            content = self._format_full_review(
                target_path,
                review_mode,
                files,
                initial_reviews,
                verification_history,
                final_review,
                timestamp,
            )
            f.write(content)

        # 2. 최종 통합 리뷰 (Phase 3만)
        final_path = f"{base_name}-final-review-{timestamp}.md"
        with open(final_path, "w", encoding="utf-8") as f:
            content = self._format_final_review(
                target_path, review_mode, files, final_review, timestamp
            )
            f.write(content)

        return (full_path, final_path)

    def _get_base_filename(self, target_path: str) -> str:
        """대상 경로로부터 기본 파일명 생성

        Args:
            target_path: 대상 경로

        Returns:
            기본 파일명
        """
        path = Path(target_path)

        if path.is_file():
            return path.stem
        elif path.is_dir():
            return path.name
        else:
            return "code"

    def _format_full_review(
        self,
        target_path: str,
        review_mode: str,
        files: List[str],
        initial_reviews: Dict[str, str],
        verification_history: List[Dict[str, Any]],
        final_review: str,
        timestamp: str,
    ) -> str:
        """전체 리뷰 마크다운 생성 (Phase 1-3 전체)

        Args:
            target_path: 리뷰 대상 경로
            review_mode: 리뷰 모드
            files: 리뷰된 파일 목록
            initial_reviews: Phase 1 결과
            verification_history: Phase 2 검증 기록
            final_review: Phase 3 최종 리뷰
            timestamp: 타임스탬프

        Returns:
            마크다운 문자열
        """
        content = f"""# 코드 리뷰 전체 기록

**생성 일시**: {timestamp}
**리뷰 대상**: `{target_path}`
**리뷰 모드**: {review_mode}
**리뷰 파일 수**: {len(files)}개

---

## 📋 리뷰 대상 파일

"""
        for file in files:
            content += f"- `{file}`\n"

        content += """

---

## Phase 1: 독립적 초기 리뷰

각 AI 리뷰어가 독립적으로 코드를 분석한 결과입니다.

"""

        for ai_name, review in initial_reviews.items():
            content += f"""
### {ai_name}의 초기 리뷰

"""
            if review:
                content += f"{review}\n\n"
            else:
                content += "*리뷰 실패*\n\n"

            content += "---\n\n"

        content += """
## Phase 2: 비판적 검증

각 AI가 다른 AI의 리뷰를 검증한 과정입니다.

"""

        for round_info in verification_history:
            round_num = round_info["round"]
            verifications = round_info["verifications"]

            content += f"""
### Round {round_num}

"""

            for ai_name, verification in verifications.items():
                content += f"""
#### {ai_name}의 검증

"""
                if verification:
                    content += f"{verification}\n\n"
                else:
                    content += "*검증 실패*\n\n"

                content += "---\n\n"

        content += f"""
## Phase 3: 최종 합의

모든 리뷰와 검증 과정을 거쳐 합의된 최종 리뷰입니다.

{final_review}

---

## 📌 사용 방법

1. **최종 리뷰 확인**: `*-final-review-*.md` 파일을 먼저 확인하세요.
2. **상세 내용 확인**: 각 이슈의 논의 과정이 궁금하면 이 문서를 참조하세요.
3. **우선순위**: Critical > Major > Minor > Suggestion 순으로 처리하세요.

**생성 도구**: AI Code Review System
**문의**: https://github.com/yourusername/ai-code-review
"""

        return content

    def _format_final_review(
        self,
        target_path: str,
        review_mode: str,
        files: List[str],
        final_review: str,
        timestamp: str,
    ) -> str:
        """최종 리뷰 마크다운 생성 (Phase 3만)

        Args:
            target_path: 리뷰 대상 경로
            review_mode: 리뷰 모드
            files: 리뷰된 파일 목록
            final_review: Phase 3 최종 리뷰
            timestamp: 타임스탬프

        Returns:
            마크다운 문자열
        """
        content = f"""# 코드 리뷰 최종 합의 문서

**생성 일시**: {timestamp}
**리뷰 대상**: `{target_path}`
**리뷰 모드**: {review_mode}
**리뷰 파일 수**: {len(files)}개

---

## 📋 리뷰 대상 파일

"""
        for file in files:
            content += f"- `{file}`\n"

        content += f"""

---

{final_review}

---

## 📝 다음 단계

1. **Critical 이슈**: 즉시 수정하세요.
2. **Major 이슈**: 다음 릴리스 전에 수정하세요.
3. **Minor 이슈**: 시간이 있을 때 개선하세요.
4. **Suggestion**: 선택적으로 적용하세요.

## 📚 참고 자료

- **전체 리뷰 기록**: `*-review-*.md` 파일 참조
- **리뷰 프로세스**: Phase 1(독립 리뷰) → Phase 2(검증) → Phase 3(합의)

**생성 도구**: AI Code Review System
**문의**: https://github.com/yourusername/ai-code-review
"""

        return content
