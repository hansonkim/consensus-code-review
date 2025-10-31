#!/usr/bin/env python3
"""AI Code Review CLI - Pure Task Delegation Architecture

여러 AI CLI(Claude, GPT-4, Gemini)를 자동 감지하여
병렬로 코드 리뷰를 수행하는 메인 스크립트입니다.
"""

import argparse
import sys
import os

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(__file__))

from ai_cli_tools import AIClient
from src.phase1_reviewer_mcp_orchestrated import MCPOrchestratedReviewer


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="AI Code Review System - Pure Task Delegation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # develop 브랜치와 비교하여 리뷰
  python review.py --base develop

  # 특정 브랜치와 비교
  python review.py --base main --target feature/new-feature

  # 특정 AI만 사용
  python review.py --base develop --ais claude,gpt4

  # 상세 출력
  python review.py --base develop --verbose
"""
    )

    parser.add_argument(
        "--base",
        required=True,
        help="기준 브랜치 (예: develop, main)"
    )

    parser.add_argument(
        "--target",
        default="HEAD",
        help="비교 대상 브랜치 (기본: HEAD)"
    )

    parser.add_argument(
        "--ais",
        help="사용할 AI 지정 (쉼표로 구분, 예: claude,gpt4,gemini). 미지정 시 자동 감지"
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=3,
        help="최대 리뷰 라운드 수 (기본: 3)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 출력 모드"
    )

    args = parser.parse_args()

    # AI Client 초기화
    print("\n" + "=" * 70)
    print("🤖 AI Code Review System - Pure Task Delegation")
    print("=" * 70)
    print()

    ai_client = AIClient(verbose=args.verbose)

    # 사용 가능한 AI 감지
    print("🔍 AI CLI 자동 감지 중...")
    print()

    if args.ais:
        # 사용자가 지정한 AI만 사용
        requested_ais = [ai.strip().lower() for ai in args.ais.split(",")]
        available_ais = {}

        for ai_name in requested_ais:
            try:
                ai_model = ai_client.get_model_by_name(ai_name)
                available_ais[ai_name] = ai_model
                print(f"  ✅ {ai_name.upper()}: {ai_model.model_id}")
            except Exception as e:
                print(f"  ❌ {ai_name.upper()}: 사용 불가 ({e})")
    else:
        # 모든 사용 가능한 AI 자동 감지
        available_ais = ai_client.get_available_models()

        if not available_ais:
            print("  ❌ 사용 가능한 AI CLI를 찾을 수 없습니다!")
            print()
            print("다음 AI CLI 중 최소 2개를 설치해주세요:")
            print("  - Claude CLI: https://claude.ai/cli")
            print("  - OpenAI CLI: pip install openai")
            print("  - Google AI CLI: pip install google-generativeai")
            sys.exit(1)

        # 감지된 AI 출력
        for ai_name, ai_model in available_ais.items():
            print(f"  ✅ {ai_name.upper()}: {ai_model.model_id}")

    print()
    print(f"📊 총 {len(available_ais)}개 AI가 리뷰에 참여합니다")
    print()

    if len(available_ais) < 2:
        print("⚠️  경고: 최소 2개의 AI가 필요합니다 (더 많을수록 좋습니다)")
        print()

    # 리뷰 실행
    reviewer = MCPOrchestratedReviewer(ai_client, verbose=args.verbose)

    try:
        result = reviewer.execute(
            available_ais=available_ais,
            base_branch=args.base,
            target_branch=args.target,
            max_rounds=args.max_rounds
        )

        print("\n" + "=" * 70)
        print("✅ 리뷰 완료!")
        print("=" * 70)
        print()

        if "final_review_file" in result:
            print(f"📄 최종 리포트: {result['final_review_file']}")

        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 에러 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
