"""프롬프트 생성 시스템

각 Phase별로 AI에게 전달할 프롬프트를 생성합니다.
"""

from typing import Dict, List

from ai_code_review.models import ReviewContext, ReviewIssue


class PromptGenerator:
    """AI 프롬프트 생성기"""

    def generate_initial_review_prompt(
        self,
        context: ReviewContext,
        code_content: Dict[str, str],
        ai_name: str
    ) -> str:
        """Phase 1 초기 리뷰 프롬프트 생성

        Args:
            context: 리뷰 컨텍스트
            code_content: {파일경로: 코드내용} 딕셔너리
            ai_name: AI 이름

        Returns:
            생성된 프롬프트
        """
        prompt_parts = [
            f"# 코드 리뷰 요청 - {ai_name}",
            "",
            "당신은 전문 코드 리뷰어입니다. 다음 코드를 철저히 분석하세요.",
            "",
            "## 리뷰 대상",
            f"- 모드: {context.review_mode}",
            f"- 파일 수: {len(code_content)}개",
            "",
        ]

        # 파일별 코드 추가
        for file_path, code in code_content.items():
            prompt_parts.extend([
                f"### 파일: {file_path}",
                "```python",
                code[:2000],  # 최대 2000자
                "```",
                "",
            ])

        prompt_parts.extend([
            "## 검토 항목",
            "1. 코드 품질 및 가독성",
            "2. 보안 취약점",
            "3. 성능 최적화 기회",
            "4. 버그 및 에지 케이스",
            "5. 모범 사례 준수",
            "",
            "## 출력 형식",
            "각 이슈를 다음 형식으로 작성하세요:",
            "",
            "```json",
            "{",
            '  "issues": [',
            "    {",
            '      "severity": "high|medium|low",',
            '      "category": "카테고리",',
            '      "line": 라인번호,',
            '      "description": "문제 설명",',
            '      "code": "문제 코드",',
            '      "suggestion": "개선 제안"',
            "    }",
            "  ]",
            "}",
            "```",
            "",
            "**중요**: 심각한 이슈부터 우선적으로 보고하세요.",
        ])

        return "\n".join(prompt_parts)

    def generate_verification_prompt(
        self,
        ai_name: str,
        own_reviews: List[ReviewIssue],
        other_reviews: Dict[str, List[ReviewIssue]],
        round_num: int
    ) -> str:
        """Phase 2 검증 프롬프트 생성

        Args:
            ai_name: 현재 AI 이름
            own_reviews: 자신의 리뷰 결과
            other_reviews: 다른 AI들의 리뷰 결과
            round_num: 현재 라운드 번호

        Returns:
            생성된 프롬프트
        """
        prompt_parts = [
            f"# 코드 리뷰 검증 - Round {round_num}",
            "",
            f"당신({ai_name})은 다른 리뷰어들의 분석을 검증하는 역할입니다.",
            "",
            "## 당신의 리뷰",
            f"발견한 이슈: {len(own_reviews)}개",
            "",
        ]

        # 자신의 주요 이슈 표시
        for issue in own_reviews[:3]:
            prompt_parts.append(
                f"- [{issue.severity}] {issue.title} ({issue.location})"
            )

        prompt_parts.extend([
            "",
            "## 다른 리뷰어들의 발견",
            "",
        ])

        # 다른 리뷰어들의 이슈
        for reviewer_name, issues in other_reviews.items():
            prompt_parts.append(f"### {reviewer_name}")
            for issue in issues[:5]:
                prompt_parts.append(
                    f"- [{issue.severity}] {issue.title} ({issue.location})"
                )
            prompt_parts.append("")

        prompt_parts.extend([
            "## 검증 작업",
            "1. 다른 리뷰어들이 발견한 이슈의 유효성 확인",
            "2. 당신이 놓친 이슈가 있는지 재검토",
            "3. 과장되거나 잘못된 지적이 있는지 확인",
            "",
            "## 출력",
            "- AGREE: 동의하는 이슈 ID",
            "- DISAGREE: 동의하지 않는 이슈와 이유",
            "- NEW: 새로 발견한 이슈",
            "- READY: 합의 준비 완료 여부 (YES/NO)",
        ])

        return "\n".join(prompt_parts)

    def generate_consensus_prompt(
        self,
        all_reviews: Dict[str, List[ReviewIssue]],
        verification_history: List[Dict]
    ) -> str:
        """Phase 3 최종 합의 프롬프트 생성

        Args:
            all_reviews: 모든 AI의 리뷰 결과
            verification_history: 검증 기록

        Returns:
            생성된 프롬프트
        """
        # 모든 이슈 수집
        all_issues = []
        for issues in all_reviews.values():
            all_issues.extend(issues)

        prompt_parts = [
            "# 최종 합의 리뷰 생성",
            "",
            "여러 AI 리뷰어의 분석을 종합하여 최종 리뷰를 작성하세요.",
            "",
            "## 통계",
            f"- 참여 리뷰어: {len(all_reviews)}명",
            f"- 총 발견 이슈: {len(all_issues)}개",
            f"- 검증 라운드: {len(verification_history)}회",
            "",
            "## 발견된 주요 이슈",
            "",
        ]

        # 심각도별로 이슈 그룹화
        critical = [i for i in all_issues if i.severity == "CRITICAL"]
        major = [i for i in all_issues if i.severity == "MAJOR"]
        minor = [i for i in all_issues if i.severity == "MINOR"]

        if critical:
            prompt_parts.append(f"### CRITICAL ({len(critical)}개)")
            for issue in critical[:5]:
                prompt_parts.append(f"- {issue.title} by {issue.reviewer}")
            prompt_parts.append("")

        if major:
            prompt_parts.append(f"### MAJOR ({len(major)}개)")
            for issue in major[:5]:
                prompt_parts.append(f"- {issue.title} by {issue.reviewer}")
            prompt_parts.append("")

        prompt_parts.extend([
            "## 작업",
            "1. 중복 이슈 통합",
            "2. 검증된 이슈만 선택",
            "3. 우선순위 결정",
            "4. 실행 가능한 권장사항 작성",
            "",
            "## 출력 형식",
            "```json",
            "{",
            '  "summary": "전체 요약",',
            '  "critical_issues": [...],',
            '  "action_items": [...]',
            "}",
            "```",
        ])

        return "\n".join(prompt_parts)
