"""설정 상수 및 기본값"""

from pathlib import Path
from typing import Dict

from ai_cli_tools.models import AIModel

# 지원하는 AI 모델 정의
ALL_AI_MODELS: Dict[str, AIModel] = {
    "claude": AIModel(
        name="Claude",
        command=["claude", "-p"],
        display_name="Claude (Anthropic)",
        test_command=["claude", "--version"],
    ),
    "openai": AIModel(
        name="OpenAI",
        command=["codex", "exec", "--skip-git-repo-check"],
        display_name="OpenAI GPT (Codex)",
        test_command=["codex", "--version"],
    ),
    "gemini": AIModel(
        name="Gemini",
        command=["gemini"],  # -p flag removed (deprecated, use stdin instead)
        display_name="Gemini (Google)",
        test_command=["gemini", "--version"],
    ),
    "grok": AIModel(
        name="Grok",
        command=["grok", "-p"],
        display_name="Grok (xAI)",
        test_command=["grok", "--version"],
    ),
}

# 캐시 파일 경로
CACHE_FILE = Path(".ai_code_review_cache.json")

# 타임아웃 설정 (초)
AI_CALL_TIMEOUT = 600  # 10분 (코드 리뷰는 더 오래 걸릴 수 있음)
MODEL_CHECK_TIMEOUT = 1.0  # 1초

# 코드 리뷰 기본 설정
DEFAULT_MAX_ROUNDS = 3  # 기본 검증 라운드 수
MIN_REVIEWERS = 2  # 최소 리뷰어 수
