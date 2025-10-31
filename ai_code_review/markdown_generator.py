"""마크다운 문서 생성"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ai_code_review.models import ReviewContext, ReviewIssue


class MarkdownGenerator:
    """마크다운 문서 생성기

    리뷰 결과를 아름다운 마크다운 형식으로 변환하여 저장합니다.
    두 가지 문서를 생성:
    1. 전체 리뷰 기록 - 모든 Phase의 상세 과정 포함
    2. 최종 통합 리뷰 - Phase 3 합의 결과만 포함
    """

    def save_review_files(
        self,
        context: ReviewContext,
        initial_reviews: Dict[str, List[ReviewIssue]],
        verification_history: List[Dict],
        final_review: Dict[str, Any]
    ) -> Tuple[str, str]:
        """리뷰 문서 저장

        Args:
            context: 리뷰 컨텍스트
            initial_reviews: Phase 1 초기 리뷰 결과 {ai_name: [issues]}
            verification_history: Phase 2 검증 히스토리
            final_review: Phase 3 최종 합의 결과

        Returns:
            (전체 리뷰 파일 경로, 최종 리뷰 파일 경로)
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_name = self._get_base_filename(context.target_path)

        # 1. 전체 리뷰 기록 (모든 Phase 포함)
        full_path = f"{base_name}-review-{timestamp}.md"
        with open(full_path, 'w', encoding='utf-8') as f:
            content = self._format_full_review(
                context,
                initial_reviews,
                verification_history,
                final_review,
                timestamp
            )
            f.write(content)

        # 2. 최종 통합 리뷰 (Phase 3만)
        final_path = f"{base_name}-final-review-{timestamp}.md"
        with open(final_path, 'w', encoding='utf-8') as f:
            content = self._format_final_review(
                context,
                final_review,
                timestamp
            )
            f.write(content)

        return (full_path, final_path)

    def _get_base_filename(self, target_path: str) -> str:
        """타겟 경로에서 기본 파일명 추출

        파일 존재 여부와 관계없이 경로 형식으로 판단합니다.

        Examples:
            ./src/main.py -> main
            ./src/ -> src
            /absolute/path/file.py -> file
        """
        path = Path(target_path)

        # 경로가 실제로 존재하는 경우
        if path.exists():
            if path.is_file():
                return path.stem
            elif path.is_dir():
                return path.name

        # 경로가 존재하지 않는 경우 - 패턴으로 판단
        # 확장자가 있으면 파일로 간주
        if path.suffix:
            return path.stem
        # 끝이 /로 끝나거나 확장자가 없으면 디렉토리로 간주
        elif str(target_path).endswith('/'):
            return path.name
        # 마지막 부분이 확장자 없는 이름이면 해당 이름 사용
        elif path.name:
            return path.name
        # 그 외의 경우
        else:
            return "code"

    def _format_full_review(
        self,
        context: ReviewContext,
        initial_reviews: Dict[str, List[ReviewIssue]],
        verification_history: List[Dict],
        final_review: Dict[str, Any],
        timestamp: str
    ) -> str:
        """전체 리뷰 마크다운 생성

        README.md 예시 형식을 따라 생성:
        - 메타데이터
        - AI 리뷰어 구성
        - Phase 1: 독립적 초기 리뷰
        - Phase 2: 비판적 검증
        - Phase 3: 최종 합의
        """
        sections = []

        # 헤더 및 메타데이터
        sections.append(self._format_header(context, timestamp))

        # AI 리뷰어 구성
        sections.append(self._format_ai_reviewers(initial_reviews, context))

        # Phase 1: 독립적 초기 리뷰
        sections.append(self._format_phase1(initial_reviews))

        # Phase 2: 비판적 검증
        if verification_history:
            sections.append(self._format_phase2(verification_history))

        # Phase 3: 최종 합의
        sections.append(self._format_phase3_in_full(
            initial_reviews,
            final_review
        ))

        return "\n\n".join(sections)

    def _format_final_review(
        self,
        context: ReviewContext,
        final_review: Dict[str, Any],
        timestamp: str
    ) -> str:
        """최종 통합 리뷰 마크다운 생성

        최종 합의된 이슈만 포함하는 깔끔한 문서
        """
        sections = []

        # 헤더
        sections.append("# 최종 코드 리뷰\n")
        sections.append(f"**생성 일시**: {self._format_timestamp(timestamp)}")
        sections.append(f"**리뷰 대상**: {context.target_path}")
        sections.append(f"**리뷰 모드**: {context.review_mode.title()}")
        sections.append("\n---")

        # 통합 요약
        if "summary" in final_review and final_review["summary"]:
            sections.append("## 🎯 통합 리뷰 요약\n")
            sections.append(final_review["summary"])
            sections.append("\n---")

        # 이슈별 섹션 (심각도별 분류)
        issues = final_review.get("issues", [])
        sections.append(self._format_issues_by_severity(issues))

        # 통계
        if "statistics" in final_review:
            sections.append("\n---")
            sections.append(self._format_statistics(final_review["statistics"]))

        return "\n\n".join(sections)

    def _format_header(self, context: ReviewContext, timestamp: str) -> str:
        """문서 헤더 생성"""
        lines = [
            "# 코드 리뷰 기록",
            "",
            f"**생성 일시**: {self._format_timestamp(timestamp)}",
            f"**리뷰 대상**: {context.target_path}",
            f"**리뷰 모드**: {context.review_mode.title()} Review"
        ]

        if context.files:
            lines.append(f"**파일 수**: {len(context.files)}개")

        if context.git_info:
            lines.append(f"**Git 정보**: {context.git_info.get('mode', 'N/A')}")

        return "\n".join(lines)

    def _format_timestamp(self, timestamp: str) -> str:
        """타임스탬프 포맷팅

        20240129-143022 -> 2024-01-29 14:30:22
        """
        dt = datetime.strptime(timestamp, "%Y%m%d-%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _format_ai_reviewers(
        self,
        initial_reviews: Dict[str, List[ReviewIssue]],
        context: ReviewContext
    ) -> str:
        """AI 리뷰어 구성 정보 생성"""
        lines = ["## 🤖 AI 리뷰어 구성", ""]

        # 각 AI 리뷰어별 정보
        ai_emojis = {
            "claude": "🔵",
            "gemini": "🟢",
            "grok": "🟡",
            "openai": "🔴"
        }

        for ai_name, issues in initial_reviews.items():
            emoji = ai_emojis.get(ai_name.lower(), "⚪")
            display_name = ai_name.title()

            lines.append(f"### {emoji} {display_name}")
            lines.append(f"> 발견 이슈: {len(issues)}개")

            # MCP 사용 정보
            if context.use_mcp and context.mcp_context:
                mcp_info = context.mcp_context.get(ai_name, [])
                if mcp_info:
                    lines.append(f"> MCP 활용: {', '.join(mcp_info)}")

            lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def _format_phase1(self, initial_reviews: Dict[str, List[ReviewIssue]]) -> str:
        """Phase 1 독립적 초기 리뷰 섹션 생성"""
        lines = ["## 📝 Phase 1: 독립적 초기 리뷰", ""]

        ai_emojis = {
            "claude": "🔵",
            "gemini": "🟢",
            "grok": "🟡",
            "openai": "🔴"
        }

        for ai_name, issues in initial_reviews.items():
            emoji = ai_emojis.get(ai_name.lower(), "⚪")
            lines.append(f"### {emoji} {ai_name.title()}")
            lines.append(f"#### 발견 이슈 ({len(issues)}개)")
            lines.append("")

            if not issues:
                lines.append("*이슈를 발견하지 못했습니다.*")
                lines.append("")
                continue

            # 이슈 나열
            for i, issue in enumerate(issues, 1):
                lines.extend(self._format_issue_detail(issue, i))
                lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def _format_phase2(self, verification_history: List[Dict]) -> str:
        """Phase 2 비판적 검증 섹션 생성"""
        lines = ["## 💬 Phase 2: 비판적 검증", ""]

        for round_num, round_data in enumerate(verification_history, 1):
            lines.append(f"### Round {round_num}")
            lines.append("")

            # 각 검증 내용
            verifications = round_data.get("verifications", {})
            for verifier, verification in verifications.items():
                target = verification.get("target", "Unknown")
                comments = verification.get("comments", "")

                lines.append(f"#### {verifier.title()} → {target.title()} 리뷰 검증")
                lines.append("")
                lines.append(comments)
                lines.append("")

            # 조기 종료 여부
            if round_data.get("consensus_ready", False):
                lines.append("✅ **모든 리뷰어가 합의 준비 완료**")
                lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def _format_phase3_in_full(
        self,
        initial_reviews: Dict[str, List[ReviewIssue]],
        final_review: Dict[str, Any]
    ) -> str:
        """전체 리뷰에서 Phase 3 섹션 생성"""
        lines = ["## 🎯 Phase 3: 최종 합의", ""]

        # 각 AI의 최종 리뷰
        ai_emojis = {
            "claude": "🔵",
            "gemini": "🟢",
            "grok": "🟡",
            "openai": "🔴"
        }

        for ai_name in initial_reviews.keys():
            emoji = ai_emojis.get(ai_name.lower(), "⚪")
            lines.append(f"### {emoji} {ai_name.title()} 최종 리뷰")
            lines.append("")
            lines.append("*검증을 거친 최종 이슈 목록*")
            lines.append("")

        # 통합 결과
        lines.append("### 📊 통합 결과")
        lines.append("")

        if "summary" in final_review and final_review["summary"]:
            lines.append(final_review["summary"])
            lines.append("")

        return "\n".join(lines)

    def _format_issues_by_severity(self, issues: List[ReviewIssue]) -> str:
        """심각도별로 이슈 분류 및 포맷팅"""
        sections = []

        # 심각도별 그룹핑
        severity_groups = {
            "CRITICAL": [],
            "MAJOR": [],
            "MINOR": [],
            "SUGGESTION": []
        }

        for issue in issues:
            severity_groups[issue.severity].append(issue)

        # 각 심각도별 섹션 생성
        severity_info = {
            "CRITICAL": ("🔴", "Critical Issues (즉시 수정 필요)"),
            "MAJOR": ("🟡", "Major Issues (우선 개선 권장)"),
            "MINOR": ("🟢", "Minor Issues (개선 고려)"),
            "SUGGESTION": ("💡", "Suggestions (선택적 개선)")
        }

        for severity in ["CRITICAL", "MAJOR", "MINOR", "SUGGESTION"]:
            severity_issues = severity_groups[severity]
            if not severity_issues:
                continue

            emoji, title = severity_info[severity]
            sections.append(f"## {emoji} {title}\n")

            for i, issue in enumerate(severity_issues, 1):
                sections.append(self._format_issue_in_final(issue, i))
                sections.append("")

        return "\n\n".join(sections)

    def _format_issue_detail(self, issue: ReviewIssue, num: int) -> List[str]:
        """개별 이슈 상세 포맷팅 (Phase 1용)"""
        lines = []

        # 이슈 헤더
        severity_badge = self._get_severity_badge(issue.severity)
        lines.append(f"**{num}. [{severity_badge}] {issue.title}**")
        lines.append(f"- 위치: `{issue.location}`")
        lines.append(f"- 발견자: {issue.reviewer}")
        lines.append("")

        # 설명
        lines.append("**문제**:")
        lines.append(issue.description)
        lines.append("")

        # 코드 스니펫
        if issue.code_snippet:
            lines.append("**문제 코드**:")
            lines.append("```python")
            lines.append(issue.code_snippet)
            lines.append("```")
            lines.append("")

        # 개선 제안
        if issue.suggestion:
            lines.append("**개선안**:")
            lines.append("```python")
            lines.append(issue.suggestion)
            lines.append("```")

        # 검증 정보
        if issue.verified and issue.verification_notes:
            lines.append("")
            lines.append("**검증 노트**:")
            for note in issue.verification_notes:
                lines.append(f"- {note}")

        return lines

    def _format_issue_in_final(self, issue: ReviewIssue, num: int) -> str:
        """개별 이슈 포맷팅 (최종 리뷰용)"""
        lines = []

        # 이슈 제목
        lines.append(f"### Issue {num}: {issue.title}")
        lines.append(f"**위치**: `{issue.location}`")

        # 합의 정보
        if issue.verified:
            lines.append(f"**발견자**: {issue.reviewer} (검증 완료 ✓)")
        else:
            lines.append(f"**발견자**: {issue.reviewer}")

        lines.append("")

        # 문제 설명
        lines.append("**문제**:")
        lines.append(issue.description)
        lines.append("")

        # 문제 코드
        if issue.code_snippet:
            lines.append("**문제 코드**:")
            # 파일 확장자 추론
            lang = self._infer_language(issue.location)
            lines.append(f"```{lang}")
            lines.append(issue.code_snippet)
            lines.append("```")
            lines.append("")

        # 개선안
        if issue.suggestion:
            lines.append("**개선안**:")
            lang = self._infer_language(issue.location)
            lines.append(f"```{lang}")
            lines.append(issue.suggestion)
            lines.append("```")
            lines.append("")

        # 검증 과정
        if issue.verification_notes:
            lines.append("**검증 과정**:")
            for note in issue.verification_notes:
                lines.append(f"- {note}")
            lines.append("")

        return "\n".join(lines)

    def _format_statistics(self, statistics: Dict[str, Any]) -> str:
        """통계 정보 포맷팅"""
        lines = ["## 📊 리뷰 통계", ""]

        # 기본 통계
        total = statistics.get("total", 0)
        by_severity = statistics.get("by_severity", {})

        lines.append(f"- **Total Issues**: {total}")
        lines.append(f"- **Critical**: {by_severity.get('CRITICAL', 0)}")
        lines.append(f"- **Major**: {by_severity.get('MAJOR', 0)}")
        lines.append(f"- **Minor**: {by_severity.get('MINOR', 0)}")
        lines.append(f"- **Suggestions**: {by_severity.get('SUGGESTION', 0)}")

        # 파일별 통계
        if "by_file" in statistics:
            lines.append("")
            lines.append("### 파일별 이슈 분포")
            lines.append("")
            for file_path, count in statistics["by_file"].items():
                lines.append(f"- `{file_path}`: {count}개")

        # 리뷰어별 통계
        if "by_reviewer" in statistics:
            lines.append("")
            lines.append("### 리뷰어별 기여도")
            lines.append("")
            for reviewer, count in statistics["by_reviewer"].items():
                lines.append(f"- **{reviewer}**: {count}개 이슈 발견")

        return "\n".join(lines)

    def _get_severity_badge(self, severity: str) -> str:
        """심각도 배지 텍스트 반환"""
        badges = {
            "CRITICAL": "CRITICAL",
            "MAJOR": "MAJOR",
            "MINOR": "MINOR",
            "SUGGESTION": "SUGGESTION"
        }
        return badges.get(severity, severity)

    def _infer_language(self, location: str) -> str:
        """파일 위치에서 프로그래밍 언어 추론

        Examples:
            main.py:45 -> python
            app.js:10-20 -> javascript
            server.go:5 -> go
        """
        # 파일명 추출
        file_part = location.split(":")[0] if ":" in location else location

        # 확장자 추출
        ext = Path(file_part).suffix.lower()

        # 언어 매핑
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".go": "go",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sh": "bash",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".md": "markdown"
        }

        return lang_map.get(ext, "")
