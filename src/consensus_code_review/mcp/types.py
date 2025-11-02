"""Type definitions for Review Response structures

This module defines TypedDict structures for the hybrid review response
that combines inline summaries with file artifacts.
"""

from typing import Literal, TypedDict


class ConsensusResult(TypedDict):
    """Consensus result from multi-AI review

    Attributes:
        result: Final consensus decision
        confidence: Confidence score (0.0 to 1.0)
        participating_ais: List of AI names that participated
        rounds_completed: Number of review rounds completed
    """

    result: Literal["APPROVED", "APPROVE_WITH_CHANGES", "REJECTED", "NO_CONSENSUS"]
    confidence: float
    participating_ais: list[str]
    rounds_completed: int


class ReviewSummary(TypedDict):
    """Summary statistics of the code review

    Attributes:
        critical_issues: Count of critical priority issues
        high_priority: Count of high priority issues
        medium_priority: Count of medium priority issues
        low_priority: Count of low priority issues
        suggestions: Count of improvement suggestions
        key_findings: Top findings (max 10 items)
        files_reviewed: Number of files reviewed
        total_changes: Total number of changes
    """

    critical_issues: int
    high_priority: int
    medium_priority: int
    low_priority: int
    suggestions: int
    key_findings: list[str]
    files_reviewed: int
    total_changes: int


class ArtifactPaths(TypedDict):
    """Paths to review artifact files

    Attributes:
        summary_file: Path to summary.md file
        full_transcript: Path to full-transcript.md file
        rounds_dir: Path to rounds directory
        consensus_log: Path to consensus.json file
    """

    summary_file: str
    full_transcript: str
    rounds_dir: str
    consensus_log: str


class ReviewResponse(TypedDict):
    """Complete review response structure

    This is the main response returned by both review_run_code_review
    and review_audit_code_review MCP tools.

    Attributes:
        session_id: Unique session identifier
        status: Current status of the review
        consensus: Consensus result from all AIs
        summary: Statistical summary of findings
        final_review_text: Final review content (< 5000 tokens)
        artifacts: Paths to detailed artifact files
    """

    session_id: str
    status: Literal["COMPLETED", "IN_PROGRESS", "FAILED"]
    consensus: ConsensusResult
    summary: ReviewSummary
    final_review_text: str
    artifacts: ArtifactPaths
