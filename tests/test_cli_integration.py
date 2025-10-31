"""CLI 통합 테스트

전체 시스템의 End-to-End 테스트를 수행합니다.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 모듈 임포트
from ai_cli_tools import AIModel
from ai_review import (
    analyze_target_files,
    determine_review_mode,
    initialize_ai_models,
    parse_arguments,
    save_review_documents,
)


@pytest.fixture
def temp_test_file(tmp_path):
    """테스트용 임시 파일 생성"""
    test_file = tmp_path / "test.py"
    test_file.write_text(
        """
def hello_world():
    user_id = input("Enter user ID: ")
    query = f"SELECT * FROM users WHERE id={user_id}"
    return query
"""
    )
    return str(test_file)


@pytest.fixture
def mock_available_ais():
    """Mock AI 모델 딕셔너리"""
    return {
        "claude": AIModel(
            name="Claude",
            command=["claude", "-p"],
            display_name="Claude (Anthropic)",
            test_command=["claude", "--version"],
        ),
        "gemini": AIModel(
            name="Gemini",
            command=["gemini", "-p"],
            display_name="Gemini (Google)",
            test_command=["gemini", "--version"],
        ),
    }


@pytest.fixture
def mock_ai_responses():
    """Mock AI 응답 데이터"""
    return {
        "phase1": "### [CRITICAL] SQL Injection 취약점",
        "phase2": "### 동의하는 이슈",
        "phase3": "# 최종 합의 문서",
    }


class TestCLIArguments:
    """CLI 인자 파싱 테스트"""

    def test_parse_file_mode(self):
        """파일 모드 인자 파싱"""
        with patch("sys.argv", ["ai_review.py", "./test.py"]):
            args = parse_arguments()
            assert args.target == "./test.py"

    def test_parse_staged_mode(self):
        """Staged 모드 인자 파싱"""
        with patch("sys.argv", ["ai_review.py", "--staged"]):
            args = parse_arguments()
            assert args.staged is True


class TestReviewModeDetection:
    """리뷰 모드 감지 테스트"""

    def test_file_mode_detection(self, temp_test_file):
        """파일 모드 감지"""
        args = Mock()
        args.target = temp_test_file
        args.staged = False
        args.commits = None
        args.branch = False

        review_mode, target_path = determine_review_mode(args)

        assert review_mode == "file"
        assert target_path == temp_test_file


class TestFileAnalysis:
    """파일 분석 테스트"""

    def test_analyze_single_file(self, temp_test_file):
        """단일 파일 분석"""
        files = analyze_target_files("file", temp_test_file, None)

        assert len(files) == 1
        assert files[0] == temp_test_file

    def test_analyze_directory(self, tmp_path):
        """디렉토리 분석"""
        # 테스트 파일 생성
        (tmp_path / "file1.py").write_text("# test")
        (tmp_path / "file2.py").write_text("# test")

        files = analyze_target_files("directory", str(tmp_path), [".py"])

        assert len(files) == 2


class TestAIInitialization:
    """AI 초기화 테스트"""

    @patch("ai_review.ModelManager")
    @patch("ai_review.CacheManager")
    def test_initialize_success(
        self, mock_cache_manager, mock_model_manager, mock_available_ais
    ):
        """AI 모델 초기화 성공"""
        # Mock 설정
        mock_manager_instance = Mock()
        mock_manager_instance.get_available_models.return_value = mock_available_ais
        mock_model_manager.return_value = mock_manager_instance

        # 실행
        available_ais = initialize_ai_models(
            force_refresh=False, only_ais=None, verbose=False
        )

        # 검증
        assert len(available_ais) == 2


class TestDocumentGeneration:
    """문서 생성 테스트"""

    def test_save_review_documents(
        self, temp_test_file, mock_ai_responses, tmp_path
    ):
        """리뷰 문서 저장"""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            initial_reviews = {"claude": mock_ai_responses["phase1"]}
            verification_history = [{"round": 1, "verifications": {}}]
            final_review = mock_ai_responses["phase3"]

            # 실행
            full_path, final_path = save_review_documents(
                review_mode="file",
                target_path=temp_test_file,
                files=[temp_test_file],
                initial_reviews=initial_reviews,
                verification_history=verification_history,
                final_review=final_review,
            )

            # 검증
            assert Path(full_path).exists()
            assert Path(final_path).exists()

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
