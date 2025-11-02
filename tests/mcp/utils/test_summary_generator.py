"""
Unit tests for summary_generator module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from consensus_code_review.mcp.utils.summary_generator import (
    count_tokens,
    truncate_to_tokens,
    classify_issues,
    write_summary_md,
    write_full_transcript,
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
                "review": "Security vulnerability in authentication module.",
                "timestamp": "2025-11-01T10:00:00",
                "feedback": ["Critical: SQL injection found"],
                "changes": ["Added input validation"]
            },
            {
                "ai_name": "gemini-2-0-flash-exp",
                "review": "Minor style issues in formatting.",
                "timestamp": "2025-11-01T10:05:00",
                "feedback": [],
                "changes": []
            }
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 2,
            "ais": ["claude-3-5-sonnet-20241022", "gemini-2-0-flash-exp"],
            "final_review": "Security vulnerability found. Minor style issues noted.",
            "timestamp": "2025-11-01T10:10:00"
        }
    }


@pytest.fixture
def sample_audit_review_data():
    """Sample review data for 'audit' type."""
    return {
        "review_type": "audit",
        "initial_review": "# Initial Review\n\nAuthentication issues found.",
        "rounds": [
            {
                "ai_name": "gpt-4-turbo",
                "review": "Verified authentication issues. Security concerns confirmed.",
                "timestamp": "2025-11-01T11:00:00"
            }
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 1,
            "ais": ["gpt-4-turbo"],
            "final_review": "Authentication security issues confirmed.",
            "timestamp": "2025-11-01T11:05:00"
        }
    }


def test_count_tokens():
    """Test token counting approximation."""
    # Rough estimate: 1 token ≈ 4 characters
    text = "a" * 400
    tokens = count_tokens(text)
    assert tokens == 100

    text = "Hello, world!"
    tokens = count_tokens(text)
    assert tokens == 3  # 13 chars / 4 ≈ 3


def test_truncate_to_tokens():
    """Test truncation to max tokens."""
    # Short text - no truncation
    short_text = "a" * 100
    result = truncate_to_tokens(short_text, max_tokens=50)
    assert result == short_text

    # Long text - truncation needed
    long_text = "a" * 30000  # ~7500 tokens
    result = truncate_to_tokens(long_text, max_tokens=5000)
    assert len(result) < len(long_text)
    assert "[Content truncated to stay under 5000 tokens]" in result


def test_classify_issues():
    """Test issue classification into critical, major, minor."""
    review_text = """
    - Security vulnerability in authentication
    - Bug: null pointer exception in handler
    - Style: inconsistent naming conventions
    - Critical: SQL injection possible
    - Minor improvement: add more comments
    """

    critical, major, minor = classify_issues(review_text)

    # Check critical issues
    assert len(critical) > 0
    assert any("security" in issue.lower() for issue in critical)

    # Check major issues
    assert len(major) > 0
    assert any("bug" in issue.lower() for issue in major)

    # Check minor issues
    assert len(minor) > 0
    assert any("style" in issue.lower() for issue in minor)


def test_generate_run_summary_markdown(sample_run_review_data):
    """Test run summary markdown generation."""
    summary = generate_run_summary_markdown(
        review_data=sample_run_review_data,
        target="feature-branch",
        base="main"
    )

    # Check structure
    assert "# Code Review Summary: feature-branch" in summary
    assert "## Metadata" in summary
    assert "**Target Branch**: `feature-branch`" in summary
    assert "**Base Branch**: `main`" in summary
    assert "**Review Type**: Run" in summary

    # Check participating AIs
    assert "claude-3-5-sonnet-20241022" in summary
    assert "gemini-2-0-flash-exp" in summary

    # Check classification
    assert "Critical Issues" in summary or "Major Issues" in summary or "Minor Issues" in summary

    # Check footer
    assert "rounds/" in summary
    assert "full-transcript.md" in summary


def test_generate_audit_summary_markdown(sample_audit_review_data):
    """Test audit summary markdown generation."""
    summary = generate_audit_summary_markdown(
        review_data=sample_audit_review_data,
        target="security-fix",
        base="main"
    )

    # Check structure
    assert "# Code Review Audit: security-fix" in summary
    assert "## Metadata" in summary
    assert "**Review Type**: Audit" in summary

    # Check initial review section
    assert "## Initial Review (User-Provided)" in summary
    assert "initial-review.md" in summary

    # Check audit-specific content
    assert "Audit" in summary


@pytest.mark.asyncio
async def test_write_summary_md_run_type(temp_dir, sample_run_review_data):
    """Test writing summary.md for run type."""
    review_dir = Path(temp_dir)

    await write_summary_md(
        review_dir=review_dir,
        review_data=sample_run_review_data,
        target="feature-branch",
        base="main"
    )

    summary_file = review_dir / "summary.md"
    assert summary_file.exists()

    with open(summary_file) as f:
        content = f.read()
        assert "Code Review Summary" in content
        assert "feature-branch" in content

        # Check token limit
        tokens = count_tokens(content)
        assert tokens <= 5000


@pytest.mark.asyncio
async def test_write_summary_md_audit_type(temp_dir, sample_audit_review_data):
    """Test writing summary.md for audit type."""
    review_dir = Path(temp_dir)

    await write_summary_md(
        review_dir=review_dir,
        review_data=sample_audit_review_data,
        target="security-fix",
        base="main"
    )

    summary_file = review_dir / "summary.md"
    assert summary_file.exists()

    with open(summary_file) as f:
        content = f.read()
        assert "Code Review Audit" in content
        assert "Initial Review" in content


@pytest.mark.asyncio
async def test_write_full_transcript_run_type(temp_dir, sample_run_review_data):
    """Test writing full-transcript.md for run type."""
    review_dir = Path(temp_dir)

    await write_full_transcript(
        review_dir=review_dir,
        review_data=sample_run_review_data
    )

    transcript_file = review_dir / "full-transcript.md"
    assert transcript_file.exists()

    with open(transcript_file) as f:
        content = f.read()
        assert "Full Review Transcript" in content
        assert "**Review Type**: RUN" in content

        # Check all rounds included
        assert "Round 1" in content
        assert "Round 2" in content
        assert "claude-3-5-sonnet-20241022" in content
        assert "gemini-2-0-flash-exp" in content

        # Check final consensus
        assert "Final Consensus" in content


@pytest.mark.asyncio
async def test_write_full_transcript_audit_type(temp_dir, sample_audit_review_data):
    """Test writing full-transcript.md for audit type."""
    review_dir = Path(temp_dir)

    await write_full_transcript(
        review_dir=review_dir,
        review_data=sample_audit_review_data
    )

    transcript_file = review_dir / "full-transcript.md"
    assert transcript_file.exists()

    with open(transcript_file) as f:
        content = f.read()
        assert "**Review Type**: AUDIT" in content
        assert "Initial Review (User-Provided)" in content
        assert "Authentication issues found" in content


def test_truncate_to_tokens_paragraph_boundary():
    """Test truncation at paragraph boundaries."""
    # Create text with paragraphs
    paragraphs = []
    for i in range(50):
        paragraphs.append(f"Paragraph {i} with some content.\n\n")

    long_text = "".join(paragraphs)

    result = truncate_to_tokens(long_text, max_tokens=100)

    # Should truncate at paragraph boundary
    assert "\n\n" in result[:-100]  # Has paragraph breaks
    assert "[Content truncated" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
