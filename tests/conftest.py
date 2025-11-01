"""
Pytest configuration and shared fixtures for code review tests

This file provides common fixtures and configuration for all tests.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp(prefix="test_reviews_"))
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_review_content() -> dict:
    """Sample review content for testing"""
    return {
        "summary": """# Code Review Summary

## Critical Issues (2)
- SQL Injection vulnerability
- Type safety issues

## High Priority (5)
- Performance optimization needed
- Missing error handling

## Recommendations
1. Fix SQL injection
2. Add type annotations
3. Implement error handling
""",
        "full_review": """# Full Code Review

## Files Changed
- src/auth.py (45 lines)
- src/models/user.py (23 lines)
- src/api/endpoints.py (78 lines)

## Detailed Analysis

### src/auth.py
Line 45: SQL Injection vulnerability found
User input is directly concatenated into SQL query.

**Recommendation**: Use parameterized queries

### src/models/user.py
Line 23: Missing type annotations
Function lacks proper type hints

**Recommendation**: Add comprehensive type annotations

### src/api/endpoints.py
Line 78: Missing input validation
API endpoint accepts unvalidated user input

**Recommendation**: Implement validation middleware
"""
    }


@pytest.fixture
def mock_session_data() -> dict:
    """Mock review session data"""
    return {
        "session_id": "test_session_12345",
        "base_branch": "develop",
        "target_branch": "feature/test",
        "current_round": 3,
        "max_rounds": 3,
        "participating_ais": ["claude-sonnet-4", "gpt-4", "gemini-pro"],
        "reviews": {
            "CLAUDE": {
                1: {"content": "Initial review...", "timestamp": 1000.0},
                2: {"content": "Revised review...", "timestamp": 2000.0},
                3: {"content": "Final review...", "timestamp": 3000.0}
            },
            "GPT4": {
                1: {"content": "GPT-4 feedback...", "timestamp": 1100.0},
                2: {"content": "GPT-4 revised...", "timestamp": 2100.0},
                3: {"content": "GPT-4 final...", "timestamp": 3100.0}
            },
            "GEMINI": {
                1: {"content": "Gemini feedback...", "timestamp": 1200.0},
                2: {"content": "Gemini revised...", "timestamp": 2200.0},
                3: {"content": "Gemini final...", "timestamp": 3200.0}
            }
        }
    }


# Helper functions for tests
def create_artifact_structure(base_dir: Path, review_type: str = "run") -> dict:
    """
    Create a complete artifact directory structure

    Args:
        base_dir: Base directory for artifacts
        review_type: "run" or "audit"

    Returns:
        Dictionary of artifact paths
    """
    # Create directories
    (base_dir / "rounds").mkdir(parents=True, exist_ok=True)

    # Create artifact files
    artifacts = {
        "summary_file": base_dir / "summary.md",
        "full_transcript": base_dir / "full-transcript.md",
        "consensus_log": base_dir / "consensus.json",
        "statistics": base_dir / "statistics.json",
        "review_type": base_dir / "review-type.txt",
        "rounds_dir": base_dir / "rounds"
    }

    # Write basic content
    artifacts["summary_file"].write_text("# Summary\n\nTest summary")
    artifacts["full_transcript"].write_text("# Full Transcript\n\nTest content")
    artifacts["consensus_log"].write_text('{"result": "APPROVED"}')
    artifacts["statistics"].write_text('{"files": 10, "changes": 100}')
    artifacts["review_type"].write_text(f"{review_type}_code_review")

    # Create round files
    for round_num in range(1, 4):
        ais = ["claude", "gpt4", "gemini"] if review_type == "run" else ["gpt4", "gemini"]
        for ai in ais:
            round_file = artifacts["rounds_dir"] / f"round-{round_num}-{ai}-feedback.md"
            round_file.write_text(f"Round {round_num} {ai} feedback")

    # For audit, create initial-review.md
    if review_type == "audit":
        initial_review = base_dir / "initial-review.md"
        initial_review.write_text("# User's Initial Review\n\nTest review content")
        artifacts["initial_review"] = initial_review

    return {k: str(v) for k, v in artifacts.items()}
