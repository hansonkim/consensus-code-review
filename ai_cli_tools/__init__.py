"""
AI CLI Tools - 모듈화된 AI CLI 호출 도구

ai-discussion 프로젝트에서 추출한 AI CLI 호출 인프라를
ai-code-review 프로젝트에 맞게 조정한 모듈입니다.

주요 컴포넌트:
- AIModel: AI 모델 정보 데이터 클래스
- AIClient: AI CLI 호출 클라이언트
- ModelManager: AI 모델 감지 및 관리
- CacheManager: 가용성 캐싱
- Constants: AI 모델 정의 및 설정값
- Exceptions: 커스텀 예외 계층

사용 예시:
    from ai_cli_tools import AIClient, ModelManager, CacheManager
    from ai_cli_tools.constants import CACHE_FILE

    # 초기화
    cache_manager = CacheManager(CACHE_FILE)
    model_manager = ModelManager(cache_manager)
    model_manager.initialize_models()

    # AI 호출
    ai_client = AIClient()
    available = model_manager.get_available_models()
    claude = available['claude']

    response = ai_client.call_ai(
        "Review this code...",
        claude,
        agents=["Security", "Performance"]
    )
"""

from ai_cli_tools.cache import CacheManager
from ai_cli_tools.client import AIClient
from ai_cli_tools.exceptions import (
    AICodeReviewException,
    AIModelNotFoundError,
    AIResponseError,
    AITimeoutError,
    FileOperationError,
    InvalidInputError,
    NoAvailableModelsError,
)
from ai_cli_tools.manager import ModelManager
from ai_cli_tools.models import AIModel

__all__ = [
    # Models
    "AIModel",
    # Services
    "AIClient",
    "ModelManager",
    "CacheManager",
    # Exceptions
    "AICodeReviewException",
    "AIModelNotFoundError",
    "AIResponseError",
    "AITimeoutError",
    "NoAvailableModelsError",
    "InvalidInputError",
    "FileOperationError",
]

__version__ = "1.0.0"
__author__ = "AI Code Review Team"
__source__ = "Extracted and modularized from ai-discussion project"
