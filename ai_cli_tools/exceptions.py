"""커스텀 예외 정의"""


class AICodeReviewException(Exception):
    """AI 코드 리뷰 시스템 기본 예외"""
    pass


class AIModelNotFoundError(AICodeReviewException):
    """AI 모델 CLI를 찾을 수 없음"""
    pass


class AIResponseError(AICodeReviewException):
    """AI 응답 오류"""
    pass


class AITimeoutError(AIResponseError):
    """AI 응답 타임아웃"""
    pass


class NoAvailableModelsError(AICodeReviewException):
    """사용 가능한 AI 모델이 없음"""
    pass


class InvalidInputError(AICodeReviewException):
    """유효하지 않은 입력"""
    pass


class FileOperationError(AICodeReviewException):
    """파일 작업 오류"""
    pass
