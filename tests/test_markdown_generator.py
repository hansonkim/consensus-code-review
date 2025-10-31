"""마크다운 생성기 테스트"""

import os

import pytest

from ai_code_review.markdown_generator import MarkdownGenerator
from ai_code_review.models import ReviewContext, ReviewIssue


@pytest.fixture
def markdown_generator():
    """MarkdownGenerator 인스턴스"""
    return MarkdownGenerator()


@pytest.fixture
def sample_context():
    """샘플 리뷰 컨텍스트"""
    return ReviewContext(
        target_path="./src/authentication.py",
        review_mode="file",
        files=["./src/authentication.py"],
        git_info={"mode": "file"},
        max_rounds=3,
        allow_early_exit=True,
        use_mcp=True
    )


@pytest.fixture
def sample_issues():
    """샘플 이슈 리스트"""
    return [
        ReviewIssue(
            severity="CRITICAL",
            title="SQL Injection 취약점",
            location="authentication.py:45-47",
            description="사용자 입력을 직접 SQL 쿼리에 삽입하여 SQL Injection 공격에 취약합니다.",
            code_snippet="query = f\"SELECT * FROM users WHERE username = '{username}'\"",
            suggestion="query = \"SELECT * FROM users WHERE username = ?\"\ncursor.execute(query, (username,))",
            reviewer="claude",
            verified=True,
            verification_notes=["gemini: 동의합니다. 심각한 보안 취약점입니다."]
        ),
        ReviewIssue(
            severity="MAJOR",
            title="비밀번호 해싱 알고리즘 미흡",
            location="authentication.py:89",
            description="MD5는 더 이상 안전한 해싱 알고리즘이 아닙니다.",
            code_snippet="password_hash = hashlib.md5(password.encode()).hexdigest()",
            suggestion="import bcrypt\npassword_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
            reviewer="claude",
            verified=True
        ),
        ReviewIssue(
            severity="MINOR",
            title="예외 처리 개선 필요",
            location="authentication.py:120",
            description="일반적인 Exception 대신 구체적인 예외를 처리하는 것이 좋습니다.",
            code_snippet="except Exception as e:\n    pass",
            suggestion="except ValueError as e:\n    logger.error(f\"Invalid input: {e}\")\nexcept DatabaseError as e:\n    logger.error(f\"Database error: {e}\")",
            reviewer="gemini",
            verified=False
        ),
        ReviewIssue(
            severity="SUGGESTION",
            title="타입 힌트 추가 권장",
            location="authentication.py:10",
            description="함수 시그니처에 타입 힌트를 추가하면 코드 가독성이 향상됩니다.",
            code_snippet="def authenticate(username, password):",
            suggestion="def authenticate(username: str, password: str) -> bool:",
            reviewer="grok",
            verified=False
        )
    ]


@pytest.fixture
def sample_initial_reviews(sample_issues):
    """샘플 초기 리뷰"""
    return {
        "claude": [sample_issues[0], sample_issues[1]],
        "gemini": [sample_issues[2]],
        "grok": [sample_issues[3]]
    }


@pytest.fixture
def sample_verification_history():
    """샘플 검증 히스토리"""
    return [
        {
            "round": 1,
            "verifications": {
                "claude": {
                    "target": "gemini",
                    "comments": "Gemini의 예외 처리 지적은 타당합니다. 하지만 Minor보다는 Major로 상향 조정을 제안합니다."
                },
                "gemini": {
                    "target": "grok",
                    "comments": "타입 힌트 제안에 동의합니다."
                },
                "grok": {
                    "target": "claude",
                    "comments": "SQL Injection과 해싱 알고리즘 이슈 모두 정확합니다."
                }
            },
            "consensus_ready": False
        },
        {
            "round": 2,
            "verifications": {
                "claude": {
                    "target": "all",
                    "comments": "모든 이슈가 검증되었습니다. 합의 준비 완료."
                },
                "gemini": {
                    "target": "all",
                    "comments": "동의합니다."
                },
                "grok": {
                    "target": "all",
                    "comments": "합의 준비 완료."
                }
            },
            "consensus_ready": True
        }
    ]


@pytest.fixture
def sample_final_review(sample_issues):
    """샘플 최종 리뷰"""
    return {
        "summary": "authentication.py 파일에서 4개의 이슈가 발견되었습니다. "
                   "특히 SQL Injection과 약한 해싱 알고리즘은 즉시 수정이 필요합니다.",
        "issues": sample_issues,
        "statistics": {
            "total": 4,
            "by_severity": {
                "CRITICAL": 1,
                "MAJOR": 1,
                "MINOR": 1,
                "SUGGESTION": 1
            },
            "by_file": {
                "authentication.py": 4
            },
            "by_reviewer": {
                "claude": 2,
                "gemini": 1,
                "grok": 1
            }
        }
    }


class TestMarkdownGenerator:
    """MarkdownGenerator 테스트"""

    def test_save_review_files_creates_two_files(
        self,
        markdown_generator,
        sample_context,
        sample_initial_reviews,
        sample_verification_history,
        sample_final_review,
        tmp_path
    ):
        """두 개의 마크다운 파일이 생성되는지 확인"""
        # 임시 디렉토리로 작업 디렉토리 변경
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            full_path, final_path = markdown_generator.save_review_files(
                sample_context,
                sample_initial_reviews,
                sample_verification_history,
                sample_final_review
            )

            # 파일 존재 확인
            assert os.path.exists(full_path)
            assert os.path.exists(final_path)

            # 파일명 패턴 확인
            assert "authentication-review-" in full_path
            assert "authentication-final-review-" in final_path
            assert full_path.endswith(".md")
            assert final_path.endswith(".md")

        finally:
            os.chdir(original_cwd)

    def test_full_review_contains_all_phases(
        self,
        markdown_generator,
        sample_context,
        sample_initial_reviews,
        sample_verification_history,
        sample_final_review,
        tmp_path
    ):
        """전체 리뷰 파일이 모든 Phase를 포함하는지 확인"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            full_path, _ = markdown_generator.save_review_files(
                sample_context,
                sample_initial_reviews,
                sample_verification_history,
                sample_final_review
            )

            with open(full_path, encoding='utf-8') as f:
                content = f.read()

            # 필수 섹션 확인
            assert "# 코드 리뷰 기록" in content
            assert "## 🤖 AI 리뷰어 구성" in content
            assert "## 📝 Phase 1: 독립적 초기 리뷰" in content
            assert "## 💬 Phase 2: 비판적 검증" in content
            assert "## 🎯 Phase 3: 최종 합의" in content

            # 메타데이터 확인
            assert "**리뷰 대상**: ./src/authentication.py" in content
            assert "**리뷰 모드**: File Review" in content

        finally:
            os.chdir(original_cwd)

    def test_full_review_contains_all_reviewers(
        self,
        markdown_generator,
        sample_context,
        sample_initial_reviews,
        sample_verification_history,
        sample_final_review,
        tmp_path
    ):
        """전체 리뷰에 모든 리뷰어가 포함되는지 확인"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            full_path, _ = markdown_generator.save_review_files(
                sample_context,
                sample_initial_reviews,
                sample_verification_history,
                sample_final_review
            )

            with open(full_path, encoding='utf-8') as f:
                content = f.read()

            # 모든 리뷰어 이름 확인
            assert "Claude" in content
            assert "Gemini" in content
            assert "Grok" in content

            # 이모지 확인
            assert "🔵" in content  # Claude
            assert "🟢" in content  # Gemini
            assert "🟡" in content  # Grok

        finally:
            os.chdir(original_cwd)

    def test_final_review_contains_issues_by_severity(
        self,
        markdown_generator,
        sample_context,
        sample_initial_reviews,
        sample_verification_history,
        sample_final_review,
        tmp_path
    ):
        """최종 리뷰가 심각도별로 이슈를 분류하는지 확인"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            _, final_path = markdown_generator.save_review_files(
                sample_context,
                sample_initial_reviews,
                sample_verification_history,
                sample_final_review
            )

            with open(final_path, encoding='utf-8') as f:
                content = f.read()

            # 심각도별 섹션 확인
            assert "## 🔴 Critical Issues (즉시 수정 필요)" in content
            assert "## 🟡 Major Issues (우선 개선 권장)" in content
            assert "## 🟢 Minor Issues (개선 고려)" in content
            assert "## 💡 Suggestions (선택적 개선)" in content

            # 이슈 내용 확인
            assert "SQL Injection 취약점" in content
            assert "비밀번호 해싱 알고리즘 미흡" in content

        finally:
            os.chdir(original_cwd)

    def test_final_review_contains_statistics(
        self,
        markdown_generator,
        sample_context,
        sample_initial_reviews,
        sample_verification_history,
        sample_final_review,
        tmp_path
    ):
        """최종 리뷰가 통계를 포함하는지 확인"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            _, final_path = markdown_generator.save_review_files(
                sample_context,
                sample_initial_reviews,
                sample_verification_history,
                sample_final_review
            )

            with open(final_path, encoding='utf-8') as f:
                content = f.read()

            # 통계 섹션 확인
            assert "## 📊 리뷰 통계" in content
            assert "**Total Issues**: 4" in content
            assert "**Critical**: 1" in content
            assert "**Major**: 1" in content
            assert "**Minor**: 1" in content
            assert "**Suggestions**: 1" in content

        finally:
            os.chdir(original_cwd)

    def test_code_snippets_have_syntax_highlighting(
        self,
        markdown_generator,
        sample_context,
        sample_initial_reviews,
        sample_verification_history,
        sample_final_review,
        tmp_path
    ):
        """코드 스니펫에 문법 강조가 포함되는지 확인"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            _, final_path = markdown_generator.save_review_files(
                sample_context,
                sample_initial_reviews,
                sample_verification_history,
                sample_final_review
            )

            with open(final_path, encoding='utf-8') as f:
                content = f.read()

            # Python 문법 강조 확인
            assert "```python" in content
            assert "```" in content

        finally:
            os.chdir(original_cwd)

    def test_verification_history_in_full_review(
        self,
        markdown_generator,
        sample_context,
        sample_initial_reviews,
        sample_verification_history,
        sample_final_review,
        tmp_path
    ):
        """전체 리뷰에 검증 히스토리가 포함되는지 확인"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            full_path, _ = markdown_generator.save_review_files(
                sample_context,
                sample_initial_reviews,
                sample_verification_history,
                sample_final_review
            )

            with open(full_path, encoding='utf-8') as f:
                content = f.read()

            # 검증 라운드 확인
            assert "### Round 1" in content
            assert "### Round 2" in content

            # 검증 내용 확인
            assert "Claude → Gemini 리뷰 검증" in content or "claude → gemini 리뷰 검증" in content or "Gemini" in content

            # 합의 완료 메시지 확인
            assert "합의 준비 완료" in content

        finally:
            os.chdir(original_cwd)

    def test_get_base_filename_from_file(self, markdown_generator):
        """파일 경로에서 기본 파일명 추출"""
        assert markdown_generator._get_base_filename("./src/main.py") == "main"
        assert markdown_generator._get_base_filename("/absolute/path/auth.py") == "auth"

    def test_get_base_filename_from_directory(self, markdown_generator, tmp_path):
        """디렉토리 경로에서 기본 파일명 추출"""
        test_dir = tmp_path / "test_src"
        test_dir.mkdir()

        result = markdown_generator._get_base_filename(str(test_dir))
        assert result == "test_src"

    def test_get_base_filename_nonexistent(self, markdown_generator):
        """존재하지 않는 경로의 기본 파일명"""
        result = markdown_generator._get_base_filename("./nonexistent")
        assert result == "nonexistent"

    def test_format_timestamp(self, markdown_generator):
        """타임스탬프 포맷팅"""
        timestamp = "20240129-143022"
        formatted = markdown_generator._format_timestamp(timestamp)
        assert formatted == "2024-01-29 14:30:22"

    def test_get_severity_badge(self, markdown_generator):
        """심각도 배지 텍스트"""
        assert markdown_generator._get_severity_badge("CRITICAL") == "CRITICAL"
        assert markdown_generator._get_severity_badge("MAJOR") == "MAJOR"
        assert markdown_generator._get_severity_badge("MINOR") == "MINOR"
        assert markdown_generator._get_severity_badge("SUGGESTION") == "SUGGESTION"

    def test_infer_language_python(self, markdown_generator):
        """Python 파일 언어 추론"""
        assert markdown_generator._infer_language("main.py:10") == "python"
        assert markdown_generator._infer_language("auth.py:45-47") == "python"

    def test_infer_language_javascript(self, markdown_generator):
        """JavaScript 파일 언어 추론"""
        assert markdown_generator._infer_language("app.js:20") == "javascript"
        assert markdown_generator._infer_language("index.ts:5") == "typescript"

    def test_infer_language_other(self, markdown_generator):
        """기타 언어 추론"""
        assert markdown_generator._infer_language("main.go:10") == "go"
        assert markdown_generator._infer_language("server.java:100") == "java"
        assert markdown_generator._infer_language("config.yaml:5") == "yaml"

    def test_empty_issues_handling(
        self,
        markdown_generator,
        sample_context,
        sample_verification_history,
        tmp_path
    ):
        """이슈가 없는 경우 처리"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            empty_reviews = {
                "claude": [],
                "gemini": []
            }

            empty_final = {
                "summary": "이슈가 발견되지 않았습니다.",
                "issues": [],
                "statistics": {
                    "total": 0,
                    "by_severity": {}
                }
            }

            full_path, final_path = markdown_generator.save_review_files(
                sample_context,
                empty_reviews,
                sample_verification_history,
                empty_final
            )

            # 파일 생성 확인
            assert os.path.exists(full_path)
            assert os.path.exists(final_path)

            # 내용 확인
            with open(final_path, encoding='utf-8') as f:
                content = f.read()

            assert "이슈가 발견되지 않았습니다" in content

        finally:
            os.chdir(original_cwd)

    def test_issue_with_verification_notes(
        self,
        markdown_generator,
        sample_context,
        tmp_path
    ):
        """검증 노트가 있는 이슈 포맷팅"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            issue_with_notes = ReviewIssue(
                severity="CRITICAL",
                title="테스트 이슈",
                location="test.py:1",
                description="테스트 설명",
                code_snippet="test_code()",
                suggestion="improved_code()",
                reviewer="claude",
                verified=True,
                verification_notes=[
                    "gemini: 동의합니다.",
                    "grok: 심각도를 MAJOR로 하향 조정 제안"
                ]
            )

            reviews = {"claude": [issue_with_notes]}
            final = {
                "summary": "테스트",
                "issues": [issue_with_notes],
                "statistics": {"total": 1, "by_severity": {"CRITICAL": 1}}
            }

            _, final_path = markdown_generator.save_review_files(
                sample_context,
                reviews,
                [],
                final
            )

            with open(final_path, encoding='utf-8') as f:
                content = f.read()

            # 검증 노트 확인
            assert "검증 과정" in content
            assert "gemini: 동의합니다." in content
            assert "grok: 심각도를 MAJOR로 하향 조정 제안" in content

        finally:
            os.chdir(original_cwd)

    def test_multiple_files_in_context(self, markdown_generator, tmp_path):
        """여러 파일이 포함된 컨텍스트"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            multi_file_context = ReviewContext(
                target_path="./src/",
                review_mode="directory",
                files=["./src/main.py", "./src/auth.py", "./src/utils.py"]
            )

            reviews = {"claude": []}
            final = {
                "summary": "다중 파일 리뷰",
                "issues": [],
                "statistics": {"total": 0, "by_severity": {}}
            }

            full_path, _ = markdown_generator.save_review_files(
                multi_file_context,
                reviews,
                [],
                final
            )

            with open(full_path, encoding='utf-8') as f:
                content = f.read()

            # 파일 수 확인
            assert "**파일 수**: 3개" in content

        finally:
            os.chdir(original_cwd)


class TestMarkdownFormat:
    """마크다운 포맷 정확성 테스트"""

    def test_issue_format_has_proper_structure(self, markdown_generator):
        """이슈 포맷이 올바른 구조를 갖는지 확인"""
        issue = ReviewIssue(
            severity="CRITICAL",
            title="테스트 이슈",
            location="test.py:10",
            description="테스트 설명",
            code_snippet="bad_code()",
            suggestion="good_code()",
            reviewer="claude"
        )

        lines = markdown_generator._format_issue_detail(issue, 1)
        content = "\n".join(lines)

        # 필수 요소 확인
        assert "**1. [CRITICAL] 테스트 이슈**" in content
        assert "- 위치: `test.py:10`" in content
        assert "- 발견자: claude" in content
        assert "**문제**:" in content
        assert "**문제 코드**:" in content
        assert "**개선안**:" in content
        assert "```python" in content

    def test_statistics_format(self, markdown_generator):
        """통계 포맷 확인"""
        stats = {
            "total": 10,
            "by_severity": {
                "CRITICAL": 2,
                "MAJOR": 3,
                "MINOR": 4,
                "SUGGESTION": 1
            },
            "by_file": {
                "main.py": 5,
                "auth.py": 5
            },
            "by_reviewer": {
                "claude": 6,
                "gemini": 4
            }
        }

        formatted = markdown_generator._format_statistics(stats)

        assert "## 📊 리뷰 통계" in formatted
        assert "**Total Issues**: 10" in formatted
        assert "**Critical**: 2" in formatted
        assert "### 파일별 이슈 분포" in formatted
        assert "### 리뷰어별 기여도" in formatted
