"""Summary generation utilities for code review reports"""

import aiofiles
from typing import Dict, List, Any


async def write_summary_md(
    session: 'ReviewSession',
    base_dir: str
) -> str:
    """Write summary markdown file

    Args:
        session: Review session
        base_dir: Base directory for files

    Returns:
        Path to summary file
    """
    summary_path = f"{base_dir}/summary.md"

    content = f"# Code Review Summary\n\n"
    content += f"**Session**: {session.session_id}\n"
    content += f"**Branch**: {session.base_branch}...{session.target_branch}\n"
    content += f"**Type**: {session.review_type}\n\n"
    content += "## Final Review\n\n"
    content += session.final_review or "No final review yet"

    async with aiofiles.open(summary_path, "w", encoding="utf-8") as f:
        await f.write(content)

    return summary_path


async def write_full_transcript(
    session: 'ReviewSession',
    base_dir: str
) -> str:
    """Write full conversation transcript

    Args:
        session: Review session with all rounds
        base_dir: Base directory for artifacts

    Returns:
        Path to full transcript file
    """
    transcript_path = f"{base_dir}/full-transcript.md"

    content = f"# Full Review Transcript\n\n"
    content += f"**Session**: {session.session_id}\n"
    content += f"**Branch**: {session.base_branch}...{session.target_branch}\n"
    content += f"**Type**: {session.review_type}\n\n"

    # Add all rounds
    for round_num in range(1, session.current_round + 1):
        content += f"## Round {round_num}\n\n"

        for ai_name, rounds in session.reviews.items():
            if round_num in rounds:
                content += f"### {ai_name}\n\n"
                content += rounds[round_num]["content"] + "\n\n"

    async with aiofiles.open(transcript_path, "w", encoding="utf-8") as f:
        await f.write(content)

    return transcript_path


def classify_issues(review_text: str) -> Dict[str, List[str]]:
    """Classify issues by severity

    Args:
        review_text: Review content

    Returns:
        Dictionary with classified issues
    """
    return {
        "critical": [],
        "major": [],
        "minor": []
    }


def count_tokens(text: str) -> int:
    """Estimate token count

    Args:
        text: Text to count

    Returns:
        Estimated token count
    """
    return len(text) // 4


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to token limit

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens

    Returns:
        Truncated text
    """
    if count_tokens(text) <= max_tokens:
        return text

    # Simple character-based truncation
    max_chars = max_tokens * 4
    return text[:max_chars] + "\n\n...(truncated)"
