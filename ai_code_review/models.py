"""리뷰 시스템 데이터 모델"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(Enum):
    """이슈 심각도"""
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    SUGGESTION = "SUGGESTION"


class ReviewMode(Enum):
    """리뷰 모드"""
    FILE = "file"
    DIRECTORY = "directory"
    STAGED = "staged"
    COMMITS = "commits"
    BRANCH = "branch"


@dataclass
class ReviewIssue:
    """코드 리뷰 이슈

    Attributes:
        severity: 심각도 (CRITICAL/MAJOR/MINOR/SUGGESTION)
        title: 이슈 제목
        location: 파일:라인 형식 (예: "main.py:45-47")
        description: 상세 설명
        code_snippet: 문제가 되는 코드
        suggestion: 개선 제안 (코드 포함)
        reviewer: 발견한 리뷰어 이름 (AI 이름)
        verified: 다른 리뷰어들이 검증했는지 여부
        verification_notes: 검증 과정 기록
    """
    severity: str
    title: str
    location: str
    description: str
    code_snippet: str
    suggestion: str
    reviewer: str
    verified: bool = False
    verification_notes: List[str] = field(default_factory=list)

    def __post_init__(self):
        """데이터 검증"""
        valid_severities = [s.value for s in Severity]
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity: {self.severity}. Must be one of {valid_severities}"
            )


@dataclass
class ReviewContext:
    """리뷰 실행 컨텍스트

    Attributes:
        target_path: 리뷰 대상 경로
        review_mode: 리뷰 모드 (file/directory/staged/commits/branch)
        files: 리뷰할 파일 목록
        mcp_context: MCP로부터 수집한 정보
        git_info: Git 관련 정보
        max_rounds: 최대 검증 라운드
        allow_early_exit: 조기 종료 허용 여부
        use_mcp: MCP 사용 여부
        file_extensions: 필터링할 확장자
    """
    target_path: str
    review_mode: str
    files: List[str]
    mcp_context: Dict[str, Any] = field(default_factory=dict)
    git_info: Dict[str, Any] = field(default_factory=dict)
    max_rounds: int = 3
    allow_early_exit: bool = True
    use_mcp: bool = True
    file_extensions: Optional[List[str]] = None

    def __post_init__(self):
        """데이터 검증"""
        valid_modes = [m.value for m in ReviewMode]
        if self.review_mode not in valid_modes:
            raise ValueError(
                f"Invalid review_mode: {self.review_mode}. Must be one of {valid_modes}"
            )

        if self.max_rounds < 1:
            raise ValueError("max_rounds must be at least 1")
