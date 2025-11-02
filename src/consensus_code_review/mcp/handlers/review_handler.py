"""Review Response Handler

Core functions for generating ReviewResponse from ReviewSession.
This module is used by BOTH review_run_code_review and review_audit_code_review.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..review_orchestrator import ReviewSession

from ..types import ConsensusResult, ReviewResponse, ReviewSummary
from ..utils import classify_issues, save_review_artifacts, truncate_to_tokens


def extract_summary(session: "ReviewSession") -> ReviewSummary:
    """Extract summary statistics from review session

    Args:
        session: Completed review session

    Returns:
        ReviewSummary with issue counts and key findings
    """
    # Get final review text
    final_review = session.final_review or _get_latest_review_text(session)

    # Classify issues by priority
    issues = classify_issues(final_review)

    # Extract key findings (simple implementation)
    lines = final_review.split("\n")
    key_findings_list = [
        line.strip()
        for line in lines
        if line.strip().startswith(("- ", "* ", "1.", "2.", "3.", "###"))
    ][:10]  # Limit to 10 findings

    return ReviewSummary(
        critical_issues=len(issues.get("critical", [])),
        high_priority=len(issues.get("high", [])),
        medium_priority=len(issues.get("medium", [])),
        low_priority=len(issues.get("low", [])),
        suggestions=len(issues.get("suggestions", [])),
        key_findings=key_findings_list,
        files_reviewed=0,  # TODO: Extract from curated data
        total_changes=0,  # TODO: Extract from curated data
    )


def _get_latest_review_text(session: "ReviewSession") -> str:
    """Get concatenated latest reviews if no final review"""
    reviews = []
    for ai_name, rounds in session.reviews.items():
        if session.current_round in rounds:
            review_data = rounds[session.current_round]
            reviews.append(f"## {ai_name}\n\n{review_data['content']}")

    return "\n\n".join(reviews)


def extract_consensus(session: "ReviewSession") -> ConsensusResult:
    """Extract consensus result from review session

    Args:
        session: Completed review session

    Returns:
        ConsensusResult with decision and confidence
    """
    participating_ais = list(session.reviews.keys())

    # Determine consensus based on session state
    if session.consensus_reached:
        result = "APPROVED"
        confidence = 0.95
    else:
        result = "NO_CONSENSUS"
        confidence = 0.0

    return ConsensusResult(
        result=result,
        confidence=confidence,
        participating_ais=participating_ais,
        rounds_completed=session.current_round,
    )


def extract_final_review(session: "ReviewSession", max_tokens: int = 5000) -> str:
    """Extract final review text with token limit

    Args:
        session: Completed review session
        max_tokens: Maximum tokens for final review (default: 5000)

    Returns:
        Final review text truncated to max_tokens
    """
    if session.final_review:
        # Use token counting and truncation (returns tuple)
        truncated_text, was_truncated = truncate_to_tokens(session.final_review, max_tokens)
        return truncated_text

    # If no final review, concatenate latest reviews
    reviews = []
    for ai_name, rounds in session.reviews.items():
        if session.current_round in rounds:
            review_data = rounds[session.current_round]
            reviews.append(f"## {ai_name}\n\n{review_data['content']}")

    combined_review = "\n\n".join(reviews)
    truncated_text, was_truncated = truncate_to_tokens(combined_review, max_tokens)
    return truncated_text


def create_review_response(session: "ReviewSession", verbosity: str = "summary") -> ReviewResponse:
    """Create hybrid review response from session

    This function is used by BOTH review_run_code_review and
    review_audit_code_review to generate consistent responses.

    Args:
        session: Completed review session
        verbosity: Response verbosity ("summary" | "detailed" | "full")

    Returns:
        ReviewResponse with inline summary and artifact paths
    """
    # Extract summary data
    summary = extract_summary(session)
    consensus = extract_consensus(session)

    # Extract final review based on verbosity (must stay < MCP_MAX_TOKENS=25000)
    from ..utils.token_counter import VERBOSITY_LIMITS

    if verbosity == "summary":
        final_review_text = extract_final_review(session, max_tokens=VERBOSITY_LIMITS["summary"])
    elif verbosity == "detailed":
        final_review_text = extract_final_review(session, max_tokens=VERBOSITY_LIMITS["detailed"])
    else:  # full
        final_review_text = extract_final_review(session, max_tokens=VERBOSITY_LIMITS["full"])

    # Generate and save artifact files
    artifacts = save_review_artifacts(session)

    # Determine status
    status = "COMPLETED" if session.consensus_reached else "IN_PROGRESS"

    return ReviewResponse(
        session_id=session.session_id,
        status=status,
        consensus=consensus,
        summary=summary,
        final_review_text=final_review_text,
        artifacts=artifacts,
    )
