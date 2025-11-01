"""
Artifact Manager - Orchestrates complete artifact generation workflow.

Main entry point for saving review artifacts with both artifact files
and summary/transcript generation.
"""

from pathlib import Path
from typing import Dict, Any

from .artifact_writer import save_review_artifacts
from .summary_generator import write_summary_md, write_full_transcript


async def generate_complete_artifacts(
    review_data: Dict[str, Any],
    target: str,
    base: str = "main",
    base_dir: str = "docs/reviews"
) -> Dict[str, str]:
    """
    Generate complete set of review artifacts.

    Creates:
    1. Directory structure: docs/reviews/{target}-{timestamp}/
    2. Artifact files (via artifact_writer):
       - review-type.txt
       - initial-review.md (audit only)
       - rounds/*.md
       - consensus.json
    3. Summary files (via summary_generator):
       - summary.md (< 5000 tokens)
       - full-transcript.md

    Args:
        review_data: Complete review session data containing:
            - review_type: 'run' or 'audit'
            - rounds: List of round data
            - consensus: Consensus information
            - initial_review: (audit only) User-provided initial review
        target: Target branch name
        base: Base branch name (default: 'main')
        base_dir: Base directory for reviews (default: 'docs/reviews')

    Returns:
        Dict with paths to generated files:
        {
            "review_dir": "/path/to/review/dir",
            "summary": "/path/to/summary.md",
            "transcript": "/path/to/full-transcript.md",
            "consensus": "/path/to/consensus.json",
            "review_type": "/path/to/review-type.txt",
            "rounds_dir": "/path/to/rounds",
            "initial_review": "/path/to/initial-review.md"  # audit only
        }

    Raises:
        ValueError: If review_data is invalid
        IOError: If file writing fails

    Example:
        >>> review_data = {
        ...     "review_type": "run",
        ...     "rounds": [...],
        ...     "consensus": {...}
        ... }
        >>> paths = await generate_complete_artifacts(
        ...     review_data,
        ...     target="feature-branch",
        ...     base="main"
        ... )
        >>> print(f"Review saved to: {paths['review_dir']}")
    """
    # Step 1: Save artifact files (creates directory structure)
    review_dir_path = await save_review_artifacts(
        review_data=review_data,
        target=target,
        base_dir=base_dir
    )

    review_dir = Path(review_dir_path)

    # Step 2: Generate summary.md
    await write_summary_md(
        review_dir=review_dir,
        review_data=review_data,
        target=target,
        base=base
    )

    # Step 3: Generate full-transcript.md
    await write_full_transcript(
        review_dir=review_dir,
        review_data=review_data
    )

    # Build result paths
    result = {
        "review_dir": str(review_dir),
        "summary": str(review_dir / "summary.md"),
        "transcript": str(review_dir / "full-transcript.md"),
        "consensus": str(review_dir / "consensus.json"),
        "review_type": str(review_dir / "review-type.txt"),
        "rounds_dir": str(review_dir / "rounds"),
    }

    # Audit-specific files
    if review_data.get("review_type") == "audit":
        initial_review_path = review_dir / "initial-review.md"
        if initial_review_path.exists():
            result["initial_review"] = str(initial_review_path)

    return result


async def load_review_artifacts(review_dir: str) -> Dict[str, Any]:
    """
    Load review artifacts from directory.

    Reads all artifact files and reconstructs review data structure.

    Args:
        review_dir: Path to review directory

    Returns:
        Dict containing review data

    Raises:
        FileNotFoundError: If review directory doesn't exist
        ValueError: If review directory is invalid
    """
    import json
    import aiofiles

    review_path = Path(review_dir)

    if not review_path.exists():
        raise FileNotFoundError(f"Review directory not found: {review_dir}")

    if not review_path.is_dir():
        raise ValueError(f"Path is not a directory: {review_dir}")

    result = {}

    # Read review type
    review_type_file = review_path / "review-type.txt"
    if review_type_file.exists():
        async with aiofiles.open(review_type_file, "r", encoding="utf-8") as f:
            result["review_type"] = (await f.read()).strip()

    # Read consensus
    consensus_file = review_path / "consensus.json"
    if consensus_file.exists():
        async with aiofiles.open(consensus_file, "r", encoding="utf-8") as f:
            result["consensus"] = json.loads(await f.read())

    # Read initial review (audit only)
    initial_review_file = review_path / "initial-review.md"
    if initial_review_file.exists():
        async with aiofiles.open(initial_review_file, "r", encoding="utf-8") as f:
            content = await f.read()
            # Strip header
            result["initial_review"] = content.replace("# Initial Review (User-Provided)\n\n", "")

    # Read rounds
    rounds_dir = review_path / "rounds"
    if rounds_dir.exists() and rounds_dir.is_dir():
        rounds = []
        for round_file in sorted(rounds_dir.glob("round-*.md")):
            async with aiofiles.open(round_file, "r", encoding="utf-8") as f:
                content = await f.read()
                # Parse round file (simplified)
                rounds.append({
                    "file": round_file.name,
                    "content": content
                })
        result["rounds"] = rounds

    return result
