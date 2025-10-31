#!/usr/bin/env python3
"""AI Code Review System - 메인 CLI 진입점

다중 AI 리뷰어가 독립적으로 코드를 분석하고 서로 검증하여
최종 합의된 리뷰 문서를 생성하는 자동화 시스템입니다.
"""

import argparse
import sys
from pathlib import Path

# 로컬 모듈 임포트
from ai_cli_tools import AIClient, ModelManager, CacheManager
from ai_cli_tools.constants import CACHE_FILE
from src.analyzer import FileAnalyzer
from src.phase1_reviewer import Phase1Reviewer
from src.phase2_reviewer import Phase2Reviewer
from src.phase3_reviewer import Phase3Reviewer
from src.markdown_generator import MarkdownGenerator


def print_banner() -> None:
    """시작 배너 출력"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              AI Code Review System v1.0                      ║
║                                                              ║
║     다중 AI 리뷰어의 독립 분석 및 비판적 검증 시스템          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_success(
    full_review_path: str, final_review_path: str, files_count: int
) -> None:
    """성공 메시지 출력

    Args:
        full_review_path: 전체 리뷰 파일 경로
        final_review_path: 최종 리뷰 파일 경로
        files_count: 리뷰된 파일 수
    """
    success = f"""
╔══════════════════════════════════════════════════════════════╗
║                    리뷰 완료!                                ║
╚══════════════════════════════════════════════════════════════╝

📊 리뷰 통계:
  - 리뷰된 파일: {files_count}개

📄 생성된 문서:
  1. 전체 리뷰 기록 (Phase 1-3 전체)
     → {full_review_path}

  2. 최종 합의 리뷰 (Phase 3만)
     → {final_review_path}

💡 권장사항:
  1. {final_review_path} 파일을 먼저 확인하세요.
  2. Critical 이슈부터 우선 처리하세요.
  3. 상세 논의 과정은 {full_review_path}를 참조하세요.

감사합니다! 🎉
"""
    print(success)


def parse_arguments() -> argparse.Namespace:
    """명령줄 인자 파싱

    Returns:
        파싱된 인자
    """
    parser = argparse.ArgumentParser(
        description="AI Code Review System - 다중 AI 코드 리뷰 및 검증",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 파일 리뷰
  python ai_code_review.py ./src/main.py

  # 디렉토리 리뷰
  python ai_code_review.py ./src/

  # Staged 변경사항 리뷰
  python ai_code_review.py --staged

  # 특정 커밋 범위 리뷰
  python ai_code_review.py --commits HEAD~3..HEAD

  # 브랜치 리뷰
  python ai_code_review.py --branch

  # Python 파일만 리뷰
  python ai_code_review.py ./src/ --extensions .py

  # 특정 AI만 사용
  python ai_code_review.py ./src/main.py --only claude,gemini

  # 검증 라운드 조정
  python ai_code_review.py ./src/main.py --max-rounds 5
""",
    )

    # 리뷰 대상
    parser.add_argument(
        "target",
        nargs="?",
        help="리뷰할 파일 또는 디렉토리 경로",
    )

    # 리뷰 모드 (상호 배타적)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--staged",
        action="store_true",
        help="Git staged 변경사항 리뷰",
    )
    mode_group.add_argument(
        "--commits",
        metavar="RANGE",
        help="특정 커밋 범위 리뷰 (예: HEAD~3..HEAD)",
    )
    mode_group.add_argument(
        "--branch",
        nargs="?",
        const="auto",
        metavar="BASE_BRANCH",
        help="현재 브랜치의 변경사항 리뷰 (기본: 자동 감지 - main/master/develop)",
    )

    # 리뷰 옵션
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=3,
        metavar="N",
        help="최대 검증 라운드 수 (기본값: 3)",
    )
    parser.add_argument(
        "--only",
        metavar="AI_LIST",
        help="사용할 AI 리스트 (쉼표로 구분, 예: claude,gemini)",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="MCP 서버 사용 안 함",
    )
    parser.add_argument(
        "--extensions",
        metavar="EXT_LIST",
        help="리뷰할 파일 확장자 필터 (쉼표로 구분, 예: .py,.js)",
    )
    parser.add_argument(
        "--no-early-exit",
        action="store_true",
        help="조기 종료 비활성화 (모든 라운드 실행)",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="AI CLI 캐시 무시하고 재감지",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="상세 출력 모드",
    )

    return parser.parse_args()


def determine_review_mode(args: argparse.Namespace) -> tuple:
    """리뷰 모드 결정

    Args:
        args: 파싱된 인자

    Returns:
        (review_mode, target_path) 튜플

    Raises:
        ValueError: 리뷰 모드가 명확하지 않을 때
    """
    if args.staged:
        return ("staged", None)
    elif args.commits:
        return ("commits", args.commits)
    elif args.branch:
        # args.branch가 True이면 "auto", 문자열이면 그 값 사용
        base_branch = args.branch if isinstance(args.branch, str) else "auto"
        return ("branch", base_branch)
    elif args.target:
        path = Path(args.target)
        if path.is_file():
            return ("file", args.target)
        elif path.is_dir():
            return ("directory", args.target)
        else:
            raise ValueError(f"대상을 찾을 수 없습니다: {args.target}")
    else:
        raise ValueError(
            "리뷰 대상을 지정해주세요. 사용법: python ai_code_review.py <파일|디렉토리> 또는 --staged, --commits, --branch"
        )


def analyze_target_files(
    review_mode: str, target_path: str, extensions: list
) -> list:
    """대상 파일 분석 및 수집

    Args:
        review_mode: 리뷰 모드
        target_path: 대상 경로 (모드에 따라 None일 수 있음)
        extensions: 확장자 필터

    Returns:
        파일 경로 리스트

    Raises:
        RuntimeError: 파일 분석 실패 시
    """
    analyzer = FileAnalyzer()

    try:
        if review_mode == "file":
            files = analyzer.analyze_file_mode(target_path, extensions)
        elif review_mode == "directory":
            files = analyzer.analyze_directory_mode(target_path, extensions)
        elif review_mode == "staged":
            files = analyzer.analyze_staged_mode(extensions)
        elif review_mode == "commits":
            files = analyzer.analyze_commits_mode(target_path, extensions)
        elif review_mode == "branch":
            # target_path에 base_branch가 전달됨
            base_branch = target_path if target_path else "auto"
            files = analyzer.analyze_branch_mode(base_branch, extensions)
        else:
            raise ValueError(f"알 수 없는 리뷰 모드: {review_mode}")

        if not files:
            raise RuntimeError("리뷰할 파일이 없습니다.")

        return files

    except Exception as e:
        raise RuntimeError(f"파일 분석 중 오류 발생: {e}")


def initialize_ai_models(
    force_refresh: bool, only_ais: list, verbose: bool
) -> dict:
    """AI 모델 초기화 및 감지

    Args:
        force_refresh: 캐시 무시 여부
        only_ais: 사용할 AI 리스트 (None이면 모두 사용)
        verbose: 상세 출력 여부

    Returns:
        사용 가능한 AI 모델 딕셔너리

    Raises:
        RuntimeError: AI 초기화 실패 시
    """
    print("\n" + "=" * 70)
    print("AI CLI 감지 및 초기화")
    print("=" * 70)

    try:
        cache_manager = CacheManager(CACHE_FILE)
        model_manager = ModelManager(cache_manager)
        model_manager.initialize_models(force_refresh=force_refresh)

        available_ais = model_manager.get_available_models()

        if not available_ais:
            raise RuntimeError(
                "사용 가능한 AI CLI가 없습니다. 최소 2개 이상의 AI CLI를 설치해주세요.\n"
                "설치 방법: https://github.com/yourusername/ai-code-review#requirements"
            )

        # --only 옵션 처리
        if only_ais:
            specified = set(only_ais)
            available_ais = {
                k: v for k, v in available_ais.items() if k in specified
            }

            if not available_ais:
                raise RuntimeError(
                    f"지정된 AI를 찾을 수 없습니다: {', '.join(only_ais)}"
                )

        # 최소 2개 AI 필요
        if len(available_ais) < 2:
            raise RuntimeError(
                f"최소 2개 이상의 AI CLI가 필요합니다. 현재: {len(available_ais)}개"
            )

        print(f"\n사용 가능한 AI: {len(available_ais)}개")
        for ai_name in available_ais.keys():
            print(f"  ✓ {ai_name}")
        print()

        return available_ais

    except Exception as e:
        raise RuntimeError(f"AI 초기화 실패: {e}")


def execute_review_process(
    files: list,
    available_ais: dict,
    max_rounds: int,
    allow_early_exit: bool,
    use_mcp: bool,
    verbose: bool,
) -> tuple:
    """리뷰 프로세스 실행 (Phase 1-3)

    Args:
        files: 리뷰할 파일 목록
        available_ais: 사용 가능한 AI 모델들
        max_rounds: 최대 검증 라운드
        allow_early_exit: 조기 종료 허용 여부
        use_mcp: MCP 사용 여부
        verbose: 상세 출력 여부

    Returns:
        (initial_reviews, verification_history, final_review) 튜플
    """
    ai_client = AIClient()

    # Phase 1: 독립적 초기 리뷰
    phase1 = Phase1Reviewer(ai_client, use_mcp=use_mcp, verbose=verbose)
    initial_reviews = phase1.execute(files, available_ais)

    # Phase 2: 비판적 검증
    phase2 = Phase2Reviewer(
        ai_client,
        max_rounds=max_rounds,
        allow_early_exit=allow_early_exit,
        verbose=verbose,
    )
    verification_history = phase2.execute(initial_reviews, available_ais)

    # Phase 3: 최종 합의
    phase3 = Phase3Reviewer(ai_client, verbose=verbose)
    final_review = phase3.execute(initial_reviews, verification_history, available_ais)

    return (initial_reviews, verification_history, final_review)


def save_review_documents(
    review_mode: str,
    target_path: str,
    files: list,
    initial_reviews: dict,
    verification_history: list,
    final_review: str,
) -> tuple:
    """리뷰 문서 저장

    Args:
        review_mode: 리뷰 모드
        target_path: 대상 경로
        files: 리뷰된 파일 목록
        initial_reviews: Phase 1 결과
        verification_history: Phase 2 검증 기록
        final_review: Phase 3 최종 리뷰

    Returns:
        (full_review_path, final_review_path) 튜플
    """
    print("\n" + "=" * 70)
    print("문서 생성 및 저장")
    print("=" * 70)

    markdown_gen = MarkdownGenerator()

    # 대상 경로가 None이면 현재 디렉토리 이름 사용
    if target_path is None:
        target_path = Path.cwd().name

    full_path, final_path = markdown_gen.save_review_files(
        target_path=target_path,
        review_mode=review_mode,
        files=files,
        initial_reviews=initial_reviews,
        verification_history=verification_history,
        final_review=final_review,
    )

    print(f"✓ 전체 리뷰 기록: {full_path}")
    print(f"✓ 최종 합의 리뷰: {final_path}")
    print()

    return (full_path, final_path)


def main() -> None:
    """메인 함수"""
    try:
        # 1. 인자 파싱
        args = parse_arguments()

        # 배너 출력
        print_banner()

        # 2. 리뷰 모드 결정
        review_mode, target_path = determine_review_mode(args)

        # 3. 확장자 필터 파싱
        extensions = None
        if args.extensions:
            extensions = [ext.strip() for ext in args.extensions.split(",")]
            if not all(ext.startswith(".") for ext in extensions):
                extensions = ["." + ext if not ext.startswith(".") else ext for ext in extensions]

        # 4. AI 모델 초기화
        only_ais = None
        if args.only:
            only_ais = [ai.strip() for ai in args.only.split(",")]

        available_ais = initialize_ai_models(
            force_refresh=args.force_refresh,
            only_ais=only_ais,
            verbose=args.verbose,
        )

        # 5. 파일 분석
        files = analyze_target_files(review_mode, target_path, extensions)

        print("=" * 70)
        print(f"리뷰 대상: {len(files)}개 파일")
        print("=" * 70)
        for file in files[:10]:  # 최대 10개만 출력
            print(f"  - {file}")
        if len(files) > 10:
            print(f"  ... 외 {len(files) - 10}개")
        print()

        # 6. 리뷰 프로세스 실행 (Phase 1-3)
        initial_reviews, verification_history, final_review = execute_review_process(
            files=files,
            available_ais=available_ais,
            max_rounds=args.max_rounds,
            allow_early_exit=not args.no_early_exit,
            use_mcp=not args.no_mcp,
            verbose=args.verbose,
        )

        # 7. 문서 저장
        full_path, final_path = save_review_documents(
            review_mode=review_mode,
            target_path=target_path,
            files=files,
            initial_reviews=initial_reviews,
            verification_history=verification_history,
            final_review=final_review,
        )

        # 8. 성공 메시지
        print_success(full_path, final_path, len(files))

    except KeyboardInterrupt:
        print("\n\n⚠️  리뷰가 사용자에 의해 중단되었습니다.")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
