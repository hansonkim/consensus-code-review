"""MCP (Model Context Protocol) 서버 모듈

Pure Task Delegation 아키텍처:
- Python: 객관적 작업 (Git 조회, 파일 선택, 토큰 관리, consensus 계산)
- AI: 주관적 작업 (데이터 분석, 리뷰 작성)

MCP Server는 Review 세션 관리만 담당하며,
AI에게는 Git 탐색 도구를 제공하지 않습니다.
"""

from .filesystem import FileSystemMCP
from .git import GitMCP
from .manager import MCPManager
from .review_orchestrator import ReviewOrchestrator
from .minimal_prompt import (
    generate_initial_review_prompt,
    generate_round2_prompt,
    generate_final_consensus_prompt_with_calculated_consensus
)
from .consensus_calculator import (
    ConsensusCalculator,
    Issue,
    calculate_consensus_from_session
)

__all__ = [
    "FileSystemMCP",
    "GitMCP",
    "MCPManager",
    "ReviewOrchestrator",
    "generate_initial_review_prompt",
    "generate_round2_prompt",
    "generate_final_consensus_prompt_with_calculated_consensus",
    "ConsensusCalculator",
    "Issue",
    "calculate_consensus_from_session"
]
