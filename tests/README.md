# Test Suite for Code Review Response Optimization

This directory contains comprehensive tests for verifying the code review optimization implementation.

## Overview

The test suite ensures that both `review_run_code_review` and `review_audit_code_review` MCP tools meet all requirements for:

1. **Token Limits**: Responses stay under MCP limits (25,000 tokens total, 5,000 for summary)
2. **Artifact Generation**: All required files are created with correct structure
3. **Response Structure**: Both tools return identical, well-structured responses
4. **Context Usability**: Claude can effectively use responses as context
5. **Type Compliance**: All data structures follow defined schemas

## Test Files

### `test_review_response_optimization.py`
Main test suite covering all 7 test requirements:

- **Test 1**: `test_run_code_review_summary_response()` - Verify run summary < 5000 tokens
- **Test 1-2**: `test_audit_code_review_summary_response()` - Verify audit summary < 5000 tokens
- **Test 2**: `test_artifact_generation()` - Verify all artifacts created
- **Test 3**: `test_mcp_token_limit()` - Verify total response < 25000 tokens
- **Test 4**: `test_claude_can_use_context_run()` - Verify run context usability
- **Test 4-2**: `test_claude_can_use_context_audit()` - Verify audit context usability
- **Test 5**: `test_response_structure_consistency()` - Verify structure consistency

### `conftest.py`
Shared fixtures and configuration:

- `temp_dir` - Temporary directory for test artifacts
- `sample_review_content` - Sample review data
- `mock_session_data` - Mock session information
- `create_artifact_structure()` - Helper for creating artifact directories

### `pytest.ini`
Pytest configuration:

- Async test support
- Test discovery patterns
- Output formatting
- Markers for test categorization

## Running Tests

### Run All Tests
```bash
# From project root
pytest tests/test_review_response_optimization.py -v

# With coverage
pytest tests/test_review_response_optimization.py --cov=src --cov-report=html
```

### Run Specific Tests
```bash
# Run only Test 1
pytest tests/test_review_response_optimization.py::test_run_code_review_summary_response -v

# Run only audit tests
pytest tests/test_review_response_optimization.py -k "audit" -v

# Run only async tests
pytest tests/test_review_response_optimization.py -m asyncio -v
```

### Run with Output
```bash
# Show print statements
pytest tests/test_review_response_optimization.py -v -s

# Show detailed output
pytest tests/test_review_response_optimization.py -vv
```

## Test Requirements

### Dependencies
```bash
pip install pytest pytest-asyncio
```

Optional for coverage:
```bash
pip install pytest-cov
```

### Python Version
- Minimum: Python 3.8
- Recommended: Python 3.10+

## Test Coverage Goals

### Must Pass (Critical)
- ✅ All 7 main test functions
- ✅ Token limits enforced
- ✅ Artifacts generated correctly
- ✅ Response structures consistent

### Should Pass (Important)
- ✅ Error handling tests
- ✅ Token truncation tests
- ✅ Type validation tests

## Test Data Structure

### ReviewResponse Schema
```python
{
    "session_id": str,
    "status": "COMPLETED" | "IN_PROGRESS" | "FAILED",
    "consensus": {
        "result": "APPROVED" | "APPROVE_WITH_CHANGES" | "REJECTED" | "NO_CONSENSUS",
        "confidence": float (0.0-1.0),
        "participating_ais": list[str],
        "rounds_completed": int
    },
    "summary": {
        "critical_issues": int,
        "high_priority": int,
        "medium_priority": int,
        "low_priority": int,
        "suggestions": int,
        "key_findings": list[str],
        "files_reviewed": int,
        "total_changes": int
    },
    "final_review_text": str,  # < 5000 tokens
    "artifacts": {
        "summary_file": str,
        "full_transcript": str,
        "rounds_dir": str,
        "consensus_log": str
    }
}
```

### Artifact Directory Structure

#### run_code_review
```
/docs/reviews/{target}-{timestamp}/
├── summary.md                    # Final review (< 5000 tokens)
├── full-transcript.md            # Complete dialogue
├── consensus.json                # Consensus metadata
├── statistics.json               # Statistics
├── review-type.txt               # "run_code_review"
└── rounds/
    ├── round-1-claude-initial.md
    ├── round-1-gpt4-feedback.md
    ├── round-1-gemini-feedback.md
    └── ...
```

#### audit_code_review
```
/docs/reviews/{target}-{timestamp}/
├── summary.md                    # Final audit summary
├── initial-review.md             # User's original review
├── full-transcript.md            # Complete dialogue
├── consensus.json                # Consensus metadata
├── statistics.json               # Statistics
├── review-type.txt               # "audit_code_review"
└── rounds/
    ├── round-1-gpt4-feedback.md
    ├── round-1-gemini-feedback.md
    └── ...
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: pytest tests/test_review_response_optimization.py -v --cov
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

pytest tests/test_review_response_optimization.py -v
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Debugging Tests

### Common Issues

**1. Async tests not running**
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Add asyncio marker
pytest tests/ -m asyncio -v
```

**2. Fixtures not found**
```bash
# Ensure conftest.py is in tests/ directory
ls tests/conftest.py

# Run pytest with discovery
pytest tests/ -v --collect-only
```

**3. Import errors**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/ai-code-review"
pytest tests/ -v
```

## Test Maintenance

### When to Update Tests

1. **API Changes**: Update when MCP tool signatures change
2. **Structure Changes**: Update when ReviewResponse schema changes
3. **New Features**: Add tests for new functionality
4. **Bug Fixes**: Add regression tests

### Best Practices

1. **Keep Tests Independent**: Each test should work standalone
2. **Use Fixtures**: Share common setup via fixtures
3. **Mock External Dependencies**: Don't call actual AI APIs
4. **Clean Up**: Ensure temp files are removed
5. **Document Intent**: Add clear docstrings

## Success Criteria

All tests must pass before:
- ✅ Merging to main branch
- ✅ Creating release
- ✅ Deploying to production

### Expected Output
```
============================= test session starts ==============================
tests/test_review_response_optimization.py::test_run_code_review_summary_response PASSED
tests/test_review_response_optimization.py::test_audit_code_review_summary_response PASSED
tests/test_review_response_optimization.py::test_artifact_generation PASSED
tests/test_review_response_optimization.py::test_mcp_token_limit PASSED
tests/test_review_response_optimization.py::test_claude_can_use_context_run PASSED
tests/test_review_response_optimization.py::test_claude_can_use_context_audit PASSED
tests/test_review_response_optimization.py::test_response_structure_consistency PASSED

============================== 7 passed in 2.35s ===============================
```

## Contact

For questions or issues with tests:
- Review the requirements doc: `/docs/review-response-optimization-requirements.md`
- Check existing test implementation
- Create issue with test failure details
