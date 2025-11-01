"""Artifact file writer for review sessions

Generates and saves review artifacts to disk:
- summary.md: Final consolidated review
- full-transcript.md: Complete conversation history
- rounds/*.md: Individual round reviews
- consensus.json: Metadata and statistics
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..review_orchestrator import ReviewSession

from ..types import ArtifactPaths


async def save_review_artifacts(session: "ReviewSession") -> ArtifactPaths:
    """Save review session results to files

    Creates directory structure:
    /docs/reviews/{target}-{timestamp}/
        ├── summary.md
        ├── full-transcript.md
        ├── consensus.json
        ├── statistics.json
        ├── review-type.txt
        ├── initial-review.md (audit_code_review only)
        └── rounds/
            ├── round-1-claude-initial.md
            ├── round-1-gpt4-feedback.md
            └── ...

    Args:
        session: Completed review session

    Returns:
        ArtifactPaths with file locations
    """
    # Create base directory
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    project_root = Path(__file__).parent.parent.parent.parent
    base_dir = project_root / "docs" / "reviews" / f"{session.target_branch}-{timestamp}"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create rounds directory
    rounds_dir = base_dir / "rounds"
    rounds_dir.mkdir(exist_ok=True)

    # Detect review type
    review_type = _detect_review_type(session)

    # Write review type marker
    await _write_review_type(session, base_dir, review_type)

    # Write initial review if audit type
    if review_type == "audit":
        await _write_initial_review(session, base_dir)

    # Write summary
    from .summary_generator import write_summary_md
    summary_path = await write_summary_md(session, str(base_dir), review_type)

    # Write full transcript
    transcript_path = await _write_full_transcript(session, base_dir)

    # Write round files
    await _write_round_files(session, rounds_dir, review_type)

    # Write consensus JSON
    consensus_path = await _write_consensus_json(session, base_dir, review_type)

    # Write statistics
    await _write_statistics_json(session, base_dir)

    return ArtifactPaths(
        summary_file=summary_path,
        full_transcript=str(transcript_path),
        rounds_dir=str(rounds_dir),
        consensus_log=str(consensus_path)
    )


def _detect_review_type(session: "ReviewSession") -> str:
    """Detect if this is run or audit review"""
    if "USER" in session.reviews:
        return "audit"
    if "CLAUDE" in session.reviews:
        return "run"
    return "run"


async def _write_review_type(session: "ReviewSession", base_dir: Path, review_type: str) -> None:
    """Write review type marker file"""
    type_file = base_dir / "review-type.txt"
    type_file.write_text(f"{review_type}_code_review\n")


async def _write_initial_review(session: "ReviewSession", base_dir: Path) -> None:
    """Write initial user review for audit type"""
    if "USER" in session.reviews and 1 in session.reviews["USER"]:
        initial_review = session.reviews["USER"][1]["content"]
        review_file = base_dir / "initial-review.md"
        timestamp = datetime.fromtimestamp(session.reviews["USER"][1]["timestamp"]).isoformat()
        review_file.write_text(f"""# Initial User Review

**Submitted**: {timestamp}

---

{initial_review}
""")


async def _write_full_transcript(session: "ReviewSession", base_dir: Path) -> Path:
    """Write complete conversation transcript"""
    transcript_file = base_dir / "full-transcript.md"

    lines = [
        f"# Full Review Transcript: {session.target_branch}",
        "",
        f"**Branch**: `{session.base_branch}...{session.target_branch}`",
        f"**Session ID**: {session.session_id}",
        f"**Created**: {datetime.fromtimestamp(session.created_at).isoformat()}",
        f"**Rounds**: {session.current_round}",
        "",
        "---",
        ""
    ]

    for round_num in range(1, session.current_round + 1):
        lines.append(f"## Round {round_num}")
        lines.append("")

        for ai_name, rounds in sorted(session.reviews.items()):
            if round_num in rounds:
                review_data = rounds[round_num]
                timestamp = datetime.fromtimestamp(review_data["timestamp"]).isoformat()
                lines.append(f"### {ai_name} ({timestamp})")
                lines.append("")
                lines.append(review_data["content"])
                lines.append("")
                lines.append("---")
                lines.append("")

    transcript_file.write_text("\n".join(lines))
    return transcript_file


async def _write_round_files(session: "ReviewSession", rounds_dir: Path, review_type: str) -> None:
    """Write individual round review files"""
    for ai_name, rounds in session.reviews.items():
        for round_num, review_data in rounds.items():
            ai_lower = ai_name.lower()
            
            if review_type == "run":
                stage = "initial" if round_num == 1 else "revised" if round_num < session.current_round else "final"
            else:
                stage = "feedback" if ai_name != "USER" else "revised"

            filename = f"round-{round_num}-{ai_lower}-{stage}.md"
            file_path = rounds_dir / filename

            timestamp = datetime.fromtimestamp(review_data["timestamp"]).isoformat()
            content = f"""# {ai_name} - Round {round_num}

**Timestamp**: {timestamp}
**Stage**: {stage}

---

{review_data["content"]}
"""
            file_path.write_text(content)


async def _write_consensus_json(session: "ReviewSession", base_dir: Path, review_type: str) -> Path:
    """Write consensus metadata as JSON"""
    consensus_file = base_dir / "consensus.json"

    issues = {"critical": 0, "high": 0, "medium": 0, "low": 0, "suggestions": 0}

    ais_info = []
    for ai_name in session.reviews.keys():
        role = "primary_reviewer" if ai_name == "CLAUDE" else "validator" if ai_name != "USER" else "author"
        ais_info.append({
            "name": ai_name,
            "role": role,
            "rounds_participated": len(session.reviews[ai_name])
        })

    consensus_data = {
        "session_id": session.session_id,
        "timestamp": datetime.now().isoformat(),
        "review_type": f"{review_type}_code_review",
        "branches": {"base": session.base_branch, "target": session.target_branch},
        "consensus": {
            "result": "APPROVED" if session.consensus_reached else "IN_PROGRESS",
            "confidence": 0.95 if session.consensus_reached else 0.0,
            "rounds": session.current_round
        },
        "ais": ais_info,
        "issues": issues,
        "files_changed": 0,
        "total_changes": 0
    }

    consensus_file.write_text(json.dumps(consensus_data, indent=2))
    return consensus_file


async def _write_statistics_json(session: "ReviewSession", base_dir: Path) -> None:
    """Write review statistics"""
    stats_file = base_dir / "statistics.json"

    stats = {
        "session_id": session.session_id,
        "duration_seconds": 0,
        "rounds_completed": session.current_round,
        "max_rounds": session.max_rounds,
        "participating_ais": len(session.reviews),
        "total_reviews_submitted": sum(len(rounds) for rounds in session.reviews.values()),
        "consensus_reached": session.consensus_reached
    }

    stats_file.write_text(json.dumps(stats, indent=2))
