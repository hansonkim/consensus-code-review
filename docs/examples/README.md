# Phase 2 Examples

This directory contains example scripts demonstrating Phase 2 artifact generation features.

## Files

### `artifact_generation_example.py`

Comprehensive example showing:
- **Run review workflow** - CLAUDE-led iterative reviews
- **Audit review workflow** - Multi-AI verification of user reviews
- **Loading artifacts** - Reading previously saved reviews

## Usage

```bash
# Run all examples
python docs/examples/artifact_generation_example.py

# Or import and use in your code
from docs.examples.artifact_generation_example import example_run_review
import asyncio

asyncio.run(example_run_review())
```

## Example Output

When you run the examples, artifacts are generated in:
```
/docs/reviews/{target}-{timestamp}/
├── summary.md              # < 5000 tokens
├── full-transcript.md      # Complete conversation
├── consensus.json          # Structured data
├── review-type.txt         # "run" or "audit"
├── initial-review.md       # User review (audit only)
└── rounds/
    ├── round-1-claude-3-5-sonnet-20241022.md
    ├── round-2-gemini-2-0-flash-exp.md
    └── ...
```

## Quick Reference

### Run Review
```python
from src.mcp.utils import generate_complete_artifacts

review_data = {
    "review_type": "run",
    "rounds": [...],
    "consensus": {...}
}

paths = await generate_complete_artifacts(
    review_data=review_data,
    target="feature-branch",
    base="main"
)
```

### Audit Review
```python
review_data = {
    "review_type": "audit",
    "initial_review": "...",  # User-provided review
    "rounds": [...],
    "consensus": {...}
}

paths = await generate_complete_artifacts(
    review_data=review_data,
    target="security-fix",
    base="main"
)
```

### Load Artifacts
```python
from src.mcp.utils import load_review_artifacts

loaded = await load_review_artifacts(
    "/docs/reviews/feature-branch-20251101-103045"
)
```

## See Also

- [Phase 2 Implementation Guide](../PHASE2_IMPLEMENTATION.md)
- [Requirements Document](../review-response-optimization-requirements.md)
