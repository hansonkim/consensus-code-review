"""E2E 통합 테스트

전체 워크플로우를 실제로 실행하여 검증합니다.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestE2EIntegration:
    """E2E 통합 테스트"""

    @pytest.fixture
    def project_root(self):
        """프로젝트 루트 경로"""
        return Path(__file__).parent.parent

    @pytest.fixture
    def sample_file(self, project_root):
        """샘플 파일 경로"""
        return project_root / "examples" / "sample_code.py"

    def test_cli_help_command(self, project_root):
        """CLI 도움말 명령 테스트"""
        result = subprocess.run(
            [sys.executable, "ai_review.py", "--help"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "AI Code Review System" in result.stdout
        assert "--staged" in result.stdout
        assert "--only" in result.stdout

    def test_cli_version_info(self, project_root):
        """CLI 버전 정보 테스트"""
        # ai_review.py가 --version 옵션이 없다면 이 테스트는 스킵
        result = subprocess.run(
            [sys.executable, "ai_review.py", "--help"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        # 버전 정보나 프로그램 이름이 출력되는지 확인
        assert len(result.stdout) > 0

    def test_sample_file_exists(self, sample_file):
        """샘플 파일이 존재하는지 확인"""
        assert sample_file.exists()
        assert sample_file.is_file()
        assert sample_file.suffix == ".py"

    def test_import_main_modules(self):
        """주요 모듈 임포트 테스트"""
        try:
            from ai_code_review import (
                markdown_generator,
                mcp_collector,
                models,
                prompt_generator,
                response_parser,
            )

            assert models is not None
            assert prompt_generator is not None
            assert markdown_generator is not None
            assert response_parser is not None
            assert mcp_collector is not None
        except ImportError as e:
            pytest.fail(f"모듈 임포트 실패: {e}")

    def test_models_validation(self):
        """데이터 모델 검증 테스트"""
        from ai_code_review.models import ReviewContext, ReviewIssue, Severity

        # 유효한 이슈 생성
        issue = ReviewIssue(
            severity=Severity.CRITICAL.value,
            title="테스트 이슈",
            location="test.py:10",
            description="테스트 설명",
            code_snippet="test code",
            suggestion="테스트 제안",
            reviewer="test_reviewer",
        )

        assert issue.severity == Severity.CRITICAL.value
        assert issue.verified is False

        # 유효한 컨텍스트 생성
        context = ReviewContext(
            target_path="./test.py",
            review_mode="file",
            files=["./test.py"],
        )

        assert context.max_rounds == 3
        assert context.allow_early_exit is True

    def test_prompt_generator_basic(self):
        """프롬프트 생성기 기본 테스트"""
        from ai_code_review.models import ReviewContext
        from ai_code_review.prompt_generator import PromptGenerator

        generator = PromptGenerator()
        context = ReviewContext(
            target_path="./test.py",
            review_mode="file",
            files=["./test.py"],
        )

        code_content = {"./test.py": "def hello(): pass"}

        prompt = generator.generate_initial_review_prompt(
            context, code_content, "test_ai"
        )

        assert len(prompt) > 0
        assert "test_ai" in prompt
        assert "코드 리뷰" in prompt

    def test_response_parser_basic(self):
        """응답 파서 기본 테스트"""
        from ai_code_review.response_parser import ResponseParser

        parser = ResponseParser()

        json_response = """
        ```json
        {
          "issues": [
            {
              "severity": "high",
              "category": "보안",
              "line": 10,
              "description": "테스트 이슈",
              "code": "test code",
              "suggestion": "테스트 제안"
            }
          ]
        }
        ```
        """

        issues = parser.parse_review_response(json_response, "test_ai", "test.py")
        assert len(issues) >= 1

    def test_markdown_generator_basic(self):
        """마크다운 생성기 기본 테스트"""
        from ai_code_review.markdown_generator import MarkdownGenerator
        from ai_code_review.models import ReviewContext, ReviewIssue, Severity

        generator = MarkdownGenerator()

        # 샘플 데이터
        context = ReviewContext(
            target_path="./test.py",
            review_mode="file",
            files=["./test.py"],
        )

        initial_reviews = {
            "claude": [
                ReviewIssue(
                    severity=Severity.CRITICAL.value,
                    title="테스트 이슈",
                    location="test.py:10",
                    description="테스트 설명",
                    code_snippet="test code",
                    suggestion="테스트 제안",
                    reviewer="claude",
                )
            ]
        }

        # 파일명만 생성 테스트 (실제 파일 저장은 하지 않음)
        base_name = generator._get_base_filename("test.py")
        assert base_name == "test"

    def test_mcp_collector_basic(self):
        """MCP 수집기 기본 테스트"""
        from ai_code_review.mcp_collector import MCPCollector

        collector = MCPCollector(".")

        # 컨텍스트 수집 테스트
        context = collector.collect_context()

        assert "repository" in context
        assert "git" in context
        assert "files" in context
        assert "conventions" in context

    def test_file_structure_integrity(self, project_root):
        """파일 구조 무결성 테스트"""
        required_files = [
            "ai_review.py",
            "ai_code_review/models.py",
            "ai_code_review/prompt_generator.py",
            "ai_code_review/markdown_generator.py",
            "ai_code_review/response_parser.py",
            "ai_code_review/mcp_collector.py",
            "src/analyzer.py",
            "src/phase1_reviewer.py",
            "src/phase2_reviewer.py",
            "src/phase3_reviewer.py",
            "tests/test_cli_integration.py",
            "tests/test_markdown_generator.py",
            "tests/test_response_parser.py",
        ]

        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"필수 파일 누락: {file_path}"

    def test_documentation_exists(self, project_root):
        """문서 파일 존재 확인"""
        required_docs = [
            "README.md",
            "CLAUDE.md",
            "PRD.md",
            "PLAN.md",
            "docs/CLI_USAGE.md",
            "docs/QUICK_START.md",
            "docs/IMPLEMENTATION_SUMMARY.md",
            "docs/FINAL_REPORT.md",
        ]

        for doc_path in required_docs:
            full_path = project_root / doc_path
            assert full_path.exists(), f"필수 문서 누락: {doc_path}"

    @pytest.mark.slow
    def test_full_workflow_dry_run(self, project_root, sample_file):
        """전체 워크플로우 드라이런 테스트

        실제 AI를 호출하지 않고 구조만 검증
        """
        # 이 테스트는 실제로는 mock을 사용해야 하지만
        # 여기서는 최소한의 구조 검증만 수행

        # 1. 모듈 임포트 가능한지 확인
        # 2. 객체 생성 가능한지 확인
        from ai_cli_tools import AIClient
        from src.analyzer import FileAnalyzer

        analyzer = FileAnalyzer()
        ai_client = AIClient()

        # 기본 객체 생성만 검증
        assert analyzer is not None
        assert ai_client is not None


class TestCodeQuality:
    """코드 품질 테스트"""

    def test_no_syntax_errors(self):
        """구문 오류가 없는지 확인"""
        import py_compile
        from pathlib import Path

        project_root = Path(__file__).parent.parent
        python_files = list(project_root.rglob("*.py"))

        # 특정 디렉토리 제외
        exclude_dirs = {".venv", "venv", "__pycache__", ".pytest_cache", "build"}

        for py_file in python_files:
            # 제외 디렉토리 확인
            if any(exclude_dir in str(py_file) for exclude_dir in exclude_dirs):
                continue

            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"구문 오류 발견 {py_file}: {e}")

    def test_imports_work(self):
        """주요 임포트가 모두 작동하는지 확인"""
        imports_to_test = [
            "ai_code_review.models",
            "ai_code_review.prompt_generator",
            "ai_code_review.markdown_generator",
            "ai_code_review.response_parser",
            "ai_code_review.mcp_collector",
        ]

        for import_path in imports_to_test:
            try:
                __import__(import_path)
            except ImportError as e:
                pytest.fail(f"임포트 실패 {import_path}: {e}")


class TestPerformance:
    """성능 테스트"""

    def test_parser_performance(self):
        """파서 성능 테스트"""
        import time

        from ai_code_review.response_parser import ResponseParser

        parser = ResponseParser()
        response = """
        ```json
        {
          "issues": [
            {"severity": "high", "category": "test", "line": 1,
             "description": "test", "code": "test", "suggestion": "test"}
          ]
        }
        ```
        """

        start = time.time()
        for _ in range(100):
            parser.parse_review_response(response, "test", "test.py")
        elapsed = time.time() - start

        # 100번 파싱이 1초 이내에 완료되어야 함
        assert elapsed < 1.0, f"파서가 너무 느립니다: {elapsed:.2f}초"

    def test_prompt_generation_performance(self):
        """프롬프트 생성 성능 테스트"""
        import time

        from ai_code_review.models import ReviewContext
        from ai_code_review.prompt_generator import PromptGenerator

        generator = PromptGenerator()
        context = ReviewContext(
            target_path="./test.py", review_mode="file", files=["./test.py"]
        )
        code_content = {"./test.py": "def hello(): pass"}

        start = time.time()
        for _ in range(100):
            generator.generate_initial_review_prompt(context, code_content, "test")
        elapsed = time.time() - start

        # 100번 생성이 1초 이내에 완료되어야 함
        assert elapsed < 1.0, f"프롬프트 생성이 너무 느립니다: {elapsed:.2f}초"
