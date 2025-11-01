"""
Unit tests for artifact_manager module (integration tests).
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.mcp.utils.artifact_manager import (
    generate_complete_artifacts,
    load_review_artifacts,
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
                "review": "# Review\n\nSecurity issues found.",
                "timestamp": "2025-11-01T10:00:00",
                "feedback": ["Add authentication"],
                "changes": ["Added auth middleware"]
            }
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 1,
            "ais": ["claude-3-5-sonnet-20241022"],
            "final_review": "Security improvements needed.",
            "timestamp": "2025-11-01T10:05:00"
        }
    }


@pytest.fixture
def sample_audit_review_data():
    """Sample review data for 'audit' type."""
    return {
        "review_type": "audit",
        "initial_review": "# User Review\n\nAuthentication issues.",
        "rounds": [
            {
                "ai_name": "gpt-4-turbo",
                "review": "# Audit\n\nConfirmed issues.",
                "timestamp": "2025-11-01T11:00:00"
            }
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 1,
            "ais": ["gpt-4-turbo"],
            "final_review": "Issues confirmed.",
            "timestamp": "2025-11-01T11:05:00"
        }
    }


@pytest.mark.asyncio
async def test_generate_complete_artifacts_run_type(temp_dir, sample_run_review_data):
    """Test complete artifact generation for run type."""
    paths = await generate_complete_artifacts(
        review_data=sample_run_review_data,
        target="feature-branch",
        base="main",
        base_dir=temp_dir
    )

    # Check returned paths
    assert "review_dir" in paths
    assert "summary" in paths
    assert "transcript" in paths
    assert "consensus" in paths
    assert "review_type" in paths
    assert "rounds_dir" in paths

    # No initial_review for run type
    assert "initial_review" not in paths

    # Verify all files exist
    assert Path(paths["review_dir"]).exists()
    assert Path(paths["summary"]).exists()
    assert Path(paths["transcript"]).exists()
    assert Path(paths["consensus"]).exists()
    assert Path(paths["review_type"]).exists()
    assert Path(paths["rounds_dir"]).exists()

    # Verify summary.md content
    with open(paths["summary"]) as f:
        summary = f.read()
        assert "Code Review Summary" in summary
        assert "feature-branch" in summary

    # Verify full-transcript.md content
    with open(paths["transcript"]) as f:
        transcript = f.read()
        assert "Full Review Transcript" in transcript
        assert "RUN" in transcript


@pytest.mark.asyncio
async def test_generate_complete_artifacts_audit_type(temp_dir, sample_audit_review_data):
    """Test complete artifact generation for audit type."""
    paths = await generate_complete_artifacts(
        review_data=sample_audit_review_data,
        target="security-fix",
        base="main",
        base_dir=temp_dir
    )

    # Check returned paths (should include initial_review)
    assert "initial_review" in paths

    # Verify all files exist
    assert Path(paths["review_dir"]).exists()
    assert Path(paths["summary"]).exists()
    assert Path(paths["transcript"]).exists()
    assert Path(paths["initial_review"]).exists()

    # Verify initial-review.md content
    with open(paths["initial_review"]) as f:
        initial_review = f.read()
        assert "Initial Review (User-Provided)" in initial_review
        assert "Authentication issues" in initial_review

    # Verify summary.md content
    with open(paths["summary"]) as f:
        summary = f.read()
        assert "Code Review Audit" in summary
        assert "Initial Review" in summary


@pytest.mark.asyncio
async def test_load_review_artifacts_run_type(temp_dir, sample_run_review_data):
    """Test loading review artifacts for run type."""
    # First generate artifacts
    paths = await generate_complete_artifacts(
        review_data=sample_run_review_data,
        target="feature-branch",
        base="main",
        base_dir=temp_dir
    )

    # Then load them back
    loaded_data = await load_review_artifacts(paths["review_dir"])

    # Verify loaded data
    assert loaded_data["review_type"] == "run"
    assert "consensus" in loaded_data
    assert loaded_data["consensus"]["consensus_reached"] is True
    assert "rounds" in loaded_data
    assert len(loaded_data["rounds"]) == 1


@pytest.mark.asyncio
async def test_load_review_artifacts_audit_type(temp_dir, sample_audit_review_data):
    """Test loading review artifacts for audit type."""
    # First generate artifacts
    paths = await generate_complete_artifacts(
        review_data=sample_audit_review_data,
        target="security-fix",
        base="main",
        base_dir=temp_dir
    )

    # Then load them back
    loaded_data = await load_review_artifacts(paths["review_dir"])

    # Verify loaded data
    assert loaded_data["review_type"] == "audit"
    assert "initial_review" in loaded_data
    assert "Authentication issues" in loaded_data["initial_review"]


@pytest.mark.asyncio
async def test_load_nonexistent_directory():
    """Test error handling for nonexistent directory."""
    with pytest.raises(FileNotFoundError):
        await load_review_artifacts("/nonexistent/directory")


@pytest.mark.asyncio
async def test_load_invalid_directory(temp_dir):
    """Test error handling for invalid directory (file instead)."""
    # Create a file instead of directory
    file_path = Path(temp_dir) / "test.txt"
    file_path.write_text("test")

    with pytest.raises(ValueError, match="not a directory"):
        await load_review_artifacts(str(file_path))


@pytest.mark.asyncio
async def test_complete_workflow(temp_dir, sample_run_review_data):
    """Test complete workflow: generate → load → verify."""
    # Generate
    paths = await generate_complete_artifacts(
        review_data=sample_run_review_data,
        target="test-branch",
        base="main",
        base_dir=temp_dir
    )

    # Verify directory structure
    review_dir = Path(paths["review_dir"])
    assert (review_dir / "summary.md").exists()
    assert (review_dir / "full-transcript.md").exists()
    assert (review_dir / "consensus.json").exists()
    assert (review_dir / "review-type.txt").exists()
    assert (review_dir / "rounds").is_dir()

    # Load
    loaded_data = await load_review_artifacts(paths["review_dir"])

    # Verify
    assert loaded_data["review_type"] == sample_run_review_data["review_type"]
    assert len(loaded_data["rounds"]) == len(sample_run_review_data["rounds"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
