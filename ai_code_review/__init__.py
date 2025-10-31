"""AI Code Review System"""

__version__ = "1.0.0"


def main():
    """Main entry point for CLI."""
    import sys
    from pathlib import Path

    # ai_review.py를 실행하기 위해 프로젝트 루트를 sys.path에 추가
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # ai_review 모듈의 main 함수 import 및 실행
    from ai_review import main as ai_review_main
    ai_review_main()
