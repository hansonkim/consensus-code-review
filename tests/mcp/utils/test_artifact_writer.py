"""
Unit tests for artifact_writer module.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from consensus_code_review.mcp.utils.artifact_writer import (
    _detect_review_type,
    _write_review_type,
    _write_initial_review,
    _write_full_transcript,
    _write_round_files,
    _write_consensus_json,
    _write_statistics_json,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_run_review_data():
    """Sample review data for 'run' type."""
    return {
        "review_type": "run",
        "rounds": [
            {
                "ai_name": "claude-3-5-sonnet-20241022",
                "review": "# Code Review\n\nGood structure, minor issues found.",
                "timestamp": "2025-11-01T10:00:00",
                "feedback": ["Consider adding error handling"],
                "changes": ["Added type hints"]
            },
            {
                "ai_name": "gemini-2-0-flash-exp",
                "review": "# Code Review\n\nAgreed with previous review.",
                "timestamp": "2025-11-01T10:05:00",
                "feedback": [],
                "changes": ["Improved documentation"]
            }
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 2,
            "ais": ["claude-3-5-sonnet-20241022", "gemini-2-0-flash-exp"],
            "final_review": "Code quality is good. Minor improvements suggested.",
            "timestamp": "2025-11-01T10:10:00",
            "metadata": {"max_rounds": 5}
        }
    }


@pytest.fixture
def sample_audit_review_data():
    """Sample review data for 'audit' type."""
    return {
        "review_type": "audit",
        "initial_review": "# Initial Review\n\nSecurity issues found in authentication.",
        "rounds": [
            {
                "ai_name": "gpt-4-turbo",
                "review": "# Audit Round 1\n\nVerified security issues. Additional concerns noted.",
                "timestamp": "2025-11-01T11:00:00",
                "feedback": ["Critical: SQL injection vulnerability"],
                "changes": []
            }
        ],
        "consensus": {
            "reached": False,
            "total_rounds": 1,
            "ais": ["gpt-4-turbo"],
            "final_review": "Security audit in progress.",
            "timestamp": "2025-11-01T11:05:00",
            "metadata": {}
        }
    }


@pytest.mark.asyncio
async def test_save_review_artifacts_run_type(temp_dir, sample_run_review_data):
    """Test saving artifacts for 'run' review type."""
    review_dir_path = await save_review_artifacts(
        review_data=sample_run_review_data,
        target="feature-branch",
        base_dir=temp_dir
    )

    review_dir = Path(review_dir_path)

    # Check directory created
    assert review_dir.exists()
    assert review_dir.is_dir()

    # Check files created
    assert (review_dir / "review-type.txt").exists()
    assert (review_dir / "consensus.json").exists()
    assert (review_dir / "rounds").exists()
    assert (review_dir / "rounds").is_dir()

    # Check round files
    round_files = list((review_dir / "rounds").glob("round-*.md"))
    assert len(round_files) == 2

    # Check no initial-review.md for 'run' type
    assert not (review_dir / "initial-review.md").exists()


@pytest.mark.asyncio
async def test_save_review_artifacts_audit_type(temp_dir, sample_audit_review_data):
    """Test saving artifacts for 'audit' review type."""
    review_dir_path = await save_review_artifacts(
        review_data=sample_audit_review_data,
        target="security-fix",
        base_dir=temp_dir
    )

    review_dir = Path(review_dir_path)

    # Check directory created
    assert review_dir.exists()

    # Check files created
    assert (review_dir / "review-type.txt").exists()
    assert (review_dir / "initial-review.md").exists()
    assert (review_dir / "consensus.json").exists()

    # Verify review type content
    with open(review_dir / "review-type.txt") as f:
        assert f.read().strip() == "audit"


@pytest.mark.asyncio
async def test_write_review_type(temp_dir):
    """Test writing review-type.txt file."""
    review_dir = Path(temp_dir) / "test-review"
    review_dir.mkdir()

    await write_review_type(review_dir, "run")

    file_path = review_dir / "review-type.txt"
    assert file_path.exists()

    with open(file_path) as f:
        content = f.read()
        assert content.strip() == "run"


@pytest.mark.asyncio
async def test_write_initial_review(temp_dir):
    """Test writing initial-review.md file."""
    review_dir = Path(temp_dir) / "test-review"
    review_dir.mkdir()

    initial_review = "# User Review\n\nSecurity concerns in authentication module."

    await write_initial_review(review_dir, initial_review)

    file_path = review_dir / "initial-review.md"
    assert file_path.exists()

    with open(file_path) as f:
        content = f.read()
        assert "Initial Review (User-Provided)" in content
        assert initial_review in content


@pytest.mark.asyncio
async def test_write_round_files(temp_dir):
    """Test writing round markdown files."""
    rounds_dir = Path(temp_dir) / "rounds"
    rounds_dir.mkdir()

    rounds = [
        {
            "ai_name": "claude-3-5-sonnet-20241022",
            "review": "Good code quality.",
            "timestamp": "2025-11-01T10:00:00",
            "feedback": ["Add tests"],
            "changes": ["Added docstrings"]
        },
        {
            "ai_name": "gemini-2-0-flash-exp",
            "review": "Agreed.",
            "timestamp": "2025-11-01T10:05:00"
        }
    ]

    await write_round_files(rounds_dir, rounds, "run")

    # Check files created
    round_files = sorted(rounds_dir.glob("round-*.md"))
    assert len(round_files) == 2

    # Verify filenames
    assert round_files[0].name == "round-1-claude-3-5-sonnet-20241022.md"
    assert round_files[1].name == "round-2-gemini-2-0-flash-exp.md"

    # Verify content
    with open(round_files[0]) as f:
        content = f.read()
        assert "Round 1" in content
        assert "claude-3-5-sonnet-20241022" in content
        assert "Good code quality." in content
        assert "Add tests" in content


@pytest.mark.asyncio
async def test_write_consensus_json(temp_dir):
    """Test writing consensus.json file."""
    review_dir = Path(temp_dir) / "test-review"
    review_dir.mkdir()

    consensus_data = {
        "reached": True,
        "total_rounds": 3,
        "ais": ["claude", "gemini", "gpt"],
        "final_review": "Consensus reached.",
        "timestamp": "2025-11-01T10:00:00",
        "metadata": {"confidence": 0.95}
    }

    await write_consensus_json(review_dir, consensus_data)

    file_path = review_dir / "consensus.json"
    assert file_path.exists()

    with open(file_path) as f:
        data = json.load(f)
        assert data["consensus_reached"] is True
        assert data["total_rounds"] == 3
        assert len(data["participating_ais"]) == 3
        assert data["final_review"] == "Consensus reached."


@pytest.mark.asyncio
async def test_invalid_review_type():
    """Test error handling for invalid review type."""
    with pytest.raises(ValueError, match="Invalid review_type"):
        await save_review_artifacts(
            review_data={"review_type": "invalid"},
            target="test",
            base_dir="/tmp"
        )


@pytest.mark.asyncio
async def test_empty_review_data():
    """Test error handling for empty review data."""
    with pytest.raises(ValueError, match="review_data cannot be empty"):
        await save_review_artifacts(
            review_data={},
            target="test",
            base_dir="/tmp"
        )


@pytest.mark.asyncio
async def test_directory_timestamp_format(temp_dir, sample_run_review_data):
    """Test that directory uses correct timestamp format."""
    review_dir_path = await save_review_artifacts(
        review_data=sample_run_review_data,
        target="test-branch",
        base_dir=temp_dir
    )

    # Check format: test-branch-YYYYMMDD-HHMMSS
    dir_name = Path(review_dir_path).name
    assert dir_name.startswith("test-branch-")

    # Extract timestamp part
    timestamp_part = dir_name.replace("test-branch-", "")
    # Should match: YYYYMMDD-HHMMSS
    assert len(timestamp_part) == 15  # 8 + 1 + 6
    assert timestamp_part[8] == "-"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
