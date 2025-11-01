# Phase 2: Quick Start Guide

## Installation

```bash
# Install required dependency
pip install aiofiles>=24.0.0
```

## Basic Usage

### 1. Generate Complete Artifacts (Recommended)

```python
from src.mcp.utils import generate_complete_artifacts

# Your review data (from Phase 1)
review_data = {
    "review_type": "run",  # or "audit"
    "rounds": [
        {
            "ai_name": "claude-3-5-sonnet-20241022",
            "review": "Security issues found...",
            "timestamp": "2025-11-01T10:00:00",
            "feedback": ["Add input validation"],
            "changes": ["Added middleware"]
        }
    ],
    "consensus": {
        "reached": True,
        "total_rounds": 1,
        "ais": ["claude-3-5-sonnet-20241022"],
        "final_review": "Code improvements needed.",
        "timestamp": "2025-11-01T10:05:00"
    }
}

# Generate all artifacts
paths = await generate_complete_artifacts(
    review_data=review_data,
    target="feature-branch",
    base="main"
)

print(f"✅ Review saved to: {paths['review_dir']}")
```

### 2. What Gets Created

```
/docs/reviews/feature-branch-20251101-103045/
├── summary.md              # Human-readable summary (< 5000 tokens)
├── full-transcript.md      # Complete conversation history
├── consensus.json          # Structured review data
├── review-type.txt         # "run" or "audit"
└── rounds/
    └── round-1-claude-3-5-sonnet-20241022.md
```

### 3. Load Artifacts Later

```python
from src.mcp.utils import load_review_artifacts

# Load previously saved review
loaded = await load_review_artifacts(
    "/docs/reviews/feature-branch-20251101-103045"
)

print(f"Review type: {loaded['review_type']}")
print(f"Consensus: {loaded['consensus']}")
```

## Review Types

### Run Review (CLAUDE-led)

```python
review_data = {
    "review_type": "run",
    "rounds": [...],
    "consensus": {...}
}
# No initial_review field
```

### Audit Review (Multi-AI verification)

```python
review_data = {
    "review_type": "audit",
    "initial_review": "# User's review text...",  # Required
    "rounds": [...],
    "consensus": {...}
}
```

## File Formats

### summary.md
- Human-readable overview
- Automatically classified issues (Critical/Major/Minor)
- Limited to < 5000 tokens
- Different templates for run vs audit

### full-transcript.md
- Complete chronological conversation
- All rounds, feedback, and AI interactions
- No token limit

### consensus.json
```json
{
  "consensus_reached": true,
  "total_rounds": 2,
  "participating_ais": ["claude-3-5-sonnet-20241022", "gemini-2-0-flash-exp"],
  "final_review": "...",
  "timestamp": "2025-11-01T10:10:00",
  "metadata": {}
}
```

### Round Files
- One file per AI per round
- Naming: `round-{N}-{ai-name}.md`
- Includes metadata, review content, feedback, changes

## Advanced Usage

### Custom Base Directory

```python
paths = await generate_complete_artifacts(
    review_data=review_data,
    target="feature-branch",
    base="main",
    base_dir="/custom/path/reviews"  # Default: "docs/reviews"
)
```

### Issue Classification

Issues are automatically classified by keywords:

- **🔴 Critical**: security, vulnerability, authentication, SQL injection
- **🟡 Major**: bug, error, performance, memory leak
- **🟢 Minor**: style, formatting, documentation, naming

### Token Truncation

Summaries are automatically truncated at paragraph boundaries if they exceed 5000 tokens.

## Integration with Phase 1

```python
# In your MCP tool (after review completes)
from src.mcp.utils import generate_complete_artifacts

async def review_run_code_review(target: str, base: str, ais: str, max_rounds: int):
    # ... Phase 1: Conduct review ...

    # Phase 2: Save artifacts
    review_data = {
        "review_type": "run",
        "rounds": session.rounds,
        "consensus": {
            "reached": session.consensus_reached,
            "total_rounds": session.current_round,
            "ais": list(session.participating_ais),
            "final_review": session.final_review,
            "timestamp": datetime.now().isoformat()
        }
    }

    paths = await generate_complete_artifacts(
        review_data=review_data,
        target=target,
        base=base
    )

    return {
        "success": True,
        "review_dir": paths["review_dir"],
        "summary": paths["summary"]
    }
```

## Testing

```bash
# Run all tests
pytest tests/mcp/utils/ -v

# Run specific module tests
pytest tests/mcp/utils/test_artifact_writer.py -v
pytest tests/mcp/utils/test_summary_generator.py -v
pytest tests/mcp/utils/test_artifact_manager.py -v

# With coverage
pytest tests/mcp/utils/ --cov=src/mcp/utils --cov-report=html
```

## Examples

See complete examples in:
- `/docs/examples/artifact_generation_example.py`
- `/docs/examples/README.md`

Run examples:
```bash
python docs/examples/artifact_generation_example.py
```

## Common Patterns

### Error Handling

```python
try:
    paths = await generate_complete_artifacts(
        review_data=review_data,
        target=target,
        base=base
    )
except ValueError as e:
    print(f"Invalid review data: {e}")
except IOError as e:
    print(f"File system error: {e}")
```

### Parallel Generation

```python
import asyncio

# Generate multiple reviews concurrently
reviews = [review_data_1, review_data_2, review_data_3]
tasks = [
    generate_complete_artifacts(data, f"feature-{i}", "main")
    for i, data in enumerate(reviews)
]
results = await asyncio.gather(*tasks)
```

## Troubleshooting

**Q: Directory already exists?**
A: Directories use timestamps (YYYYMMDD-HHMMSS), conflicts are rare. If needed, wait 1 second.

**Q: Summary exceeds 5000 tokens?**
A: Automatic truncation at paragraph boundaries with ellipsis notification.

**Q: Unicode encoding errors?**
A: All files use UTF-8. Check input data encoding.

**Q: Missing audit initial_review?**
A: For audit type, initial_review is required in review_data.

## Performance

- **Async I/O**: All file operations are non-blocking
- **Memory efficient**: Streaming writes, no large buffers
- **Concurrent safe**: Multiple reviews can be generated in parallel
- **Fast**: Typical generation time < 100ms per review

## Next Steps

- [Phase 2 Full Implementation](./PHASE2_IMPLEMENTATION.md)
- [Phase 3: LLM Response Generation](./review-response-optimization-requirements.md#phase-3)
- [API Documentation](../src/mcp/utils/)

## Support

- GitHub Issues: [Report bugs](https://github.com/...)
- Documentation: [Full docs](./PHASE2_IMPLEMENTATION.md)
- Examples: [Example scripts](./examples/)
