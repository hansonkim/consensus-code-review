"""
Unit tests for artifact_writer module.
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from consensus_code_review.mcp.utils.artifact_writer import (
    _write_consensus_json,
    _write_initial_review,
    _write_review_type,
    _write_round_files,
    save_review_artifacts,
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
                "changes": ["Added type hints"],
            },
            {
                "ai_name": "gemini-2-0-flash-exp",
                "review": "# Code Review\n\nAgreed with previous review.",
                "timestamp": "2025-11-01T10:05:00",
                "feedback": [],
                "changes": ["Improved documentation"],
            },
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 2,
            "ais": ["claude-3-5-sonnet-20241022", "gemini-2-0-flash-exp"],
            "final_review": "Code quality is good. Minor improvements suggested.",
            "timestamp": "2025-11-01T10:10:00",
            "metadata": {"max_rounds": 5},
        },
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
                "changes": [],
            }
        ],
        "consensus": {
            "reached": False,
            "total_rounds": 1,
            "ais": ["gpt-4-turbo"],
            "final_review": "Security audit in progress.",
            "timestamp": "2025-11-01T11:05:00",
            "metadata": {},
        },
    }


@pytest.fixture
def mock_session():
    """Create a mock ReviewSession for testing private functions."""
    session = Mock()
    session.session_id = "test-session-123"
    session.base_branch = "main"
    session.target_branch = "feature-branch"
    session.current_round = 2
    session.max_rounds = 5
    session.consensus_reached = True
    session.created_at = 1730448000.0  # 2025-11-01T10:00:00
    session.reviews = {
        "CLAUDE": {
            1: {"content": "# Code Review\n\nGood structure.", "timestamp": 1730448000.0},
            2: {"content": "# Revised Review\n\nAll issues addressed.", "timestamp": 1730448300.0},
        },
        "GEMINI": {1: {"content": "# Review\n\nAgreed with CLAUDE.", "timestamp": 1730448100.0}},
        "USER": {
            1: {
                "content": "# Initial Review\n\nSecurity concerns in authentication module.",
                "timestamp": 1730447900.0,
            }
        },
    }
    session.final_review = "Code quality is good. Minor improvements suggested."
    return session


@pytest.mark.asyncio
async def test_save_review_artifacts_run_type(temp_dir, sample_run_review_data):
    """Test saving artifacts for 'run' review type."""
    review_dir_path = await save_review_artifacts(
        review_data=sample_run_review_data, target="feature-branch", base_dir=temp_dir
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
        review_data=sample_audit_review_data, target="security-fix", base_dir=temp_dir
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
async def test_write_review_type(temp_dir, mock_session):
    """Test writing review-type.txt file."""
    review_dir = Path(temp_dir) / "test-review"
    review_dir.mkdir()

    _write_review_type(mock_session, review_dir, "run")

    file_path = review_dir / "review-type.txt"
    assert file_path.exists()

    with open(file_path) as f:
        content = f.read()
        assert content.strip() == "run_code_review"


@pytest.mark.asyncio
async def test_write_initial_review(temp_dir, mock_session):
    """Test writing initial-review.md file."""
    review_dir = Path(temp_dir) / "test-review"
    review_dir.mkdir()

    _write_initial_review(mock_session, review_dir)

    file_path = review_dir / "initial-review.md"
    assert file_path.exists()

    with open(file_path) as f:
        content = f.read()
        assert "Initial User Review" in content
        assert "Security concerns in authentication module" in content


@pytest.mark.asyncio
async def test_write_round_files(temp_dir):
    """Test writing round markdown files."""
    rounds_dir = Path(temp_dir) / "rounds"
    rounds_dir.mkdir()

    # Create a custom mock session for this test
    test_session = Mock()
    test_session.current_round = 2
    test_session.reviews = {
        "claude-3-5-sonnet-20241022": {
            1: {"content": "Good code quality.", "timestamp": 1730448000.0}
        },
        "gemini-2-0-flash-exp": {1: {"content": "Agreed.", "timestamp": 1730448300.0}},
    }

    _write_round_files(test_session, rounds_dir, "run")

    # Check files created
    round_files = sorted(rounds_dir.glob("round-*.md"))
    assert len(round_files) == 2

    # Verify filenames
    assert round_files[0].name == "round-1-claude-3-5-sonnet-20241022-initial.md"
    assert round_files[1].name == "round-1-gemini-2-0-flash-exp-initial.md"

    # Verify content
    with open(round_files[0]) as f:
        content = f.read()
        assert "Round 1" in content
        assert "claude-3-5-sonnet-20241022" in content
        assert "Good code quality." in content


@pytest.mark.asyncio
async def test_write_consensus_json(temp_dir, mock_session):
    """Test writing consensus.json file."""
    review_dir = Path(temp_dir) / "test-review"
    review_dir.mkdir()

    _write_consensus_json(mock_session, review_dir, "run")

    file_path = review_dir / "consensus.json"
    assert file_path.exists()

    with open(file_path) as f:
        data = json.load(f)
        assert data["consensus"]["result"] == "APPROVED"
        assert data["consensus"]["rounds"] == 2
        assert len(data["ais"]) == 3  # CLAUDE, GEMINI, USER
        assert data["review_type"] == "run_code_review"
        assert data["branches"]["base"] == "main"
        assert data["branches"]["target"] == "feature-branch"


@pytest.mark.asyncio
async def test_invalid_review_type():
    """Test error handling for invalid review type."""
    with pytest.raises(ValueError, match="Invalid review_type"):
        await save_review_artifacts(
            review_data={"review_type": "invalid"}, target="test", base_dir="/tmp"
        )


@pytest.mark.asyncio
async def test_empty_review_data():
    """Test error handling for empty review data."""
    with pytest.raises(ValueError, match="review_data cannot be empty"):
        await save_review_artifacts(review_data={}, target="test", base_dir="/tmp")


@pytest.mark.asyncio
async def test_directory_timestamp_format(temp_dir, sample_run_review_data):
    """Test that directory uses correct timestamp format."""
    review_dir_path = await save_review_artifacts(
        review_data=sample_run_review_data, target="test-branch", base_dir=temp_dir
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
