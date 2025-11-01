"""Token counting and truncation utilities

Uses tiktoken for accurate token counting compatible with GPT models.
"""

import json
from typing import Any


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken

    Args:
        text: Text to count tokens for
        model: Model name for tokenizer (default: gpt-4)

    Returns:
        Number of tokens in text
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4
    except Exception:
        # If model not found, use cl100k_base (GPT-4 default)
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except:
            # Ultimate fallback
            return len(text) // 4


def truncate_to_tokens(
    text: str,
    max_tokens: int,
    model: str = "gpt-4",
    suffix: str = "\n\n...(truncated)"
) -> str:
    """Truncate text to maximum token count

    Args:
        text: Text to truncate
        max_tokens: Maximum allowed tokens
        model: Model name for tokenizer
        suffix: Suffix to add when truncating

    Returns:
        Truncated text with suffix if needed
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
    except:
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            # Fallback: character-based truncation
            max_chars = max_tokens * 4
            if len(text) <= max_chars:
                return text
            return text[:max_chars] + suffix

    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text

    # Reserve tokens for suffix
    suffix_tokens = encoding.encode(suffix)
    available_tokens = max_tokens - len(suffix_tokens)

    if available_tokens <= 0:
        return suffix

    truncated_tokens = tokens[:available_tokens]
    return encoding.decode(truncated_tokens) + suffix


def validate_response_size(response: dict[str, Any], max_tokens: int = 25000) -> None:
    """Validate that response size doesn't exceed MCP limit

    Args:
        response: Response dictionary to validate
        max_tokens: Maximum allowed tokens (default: 25000 for MCP)

    Raises:
        ValueError: If response exceeds token limit
    """
    response_json = json.dumps(response, ensure_ascii=False)
    token_count = count_tokens(response_json)

    if token_count > max_tokens:
        raise ValueError(
            f"Response size ({token_count} tokens) exceeds MCP limit ({max_tokens}). "
            f"Consider using verbosity='summary' or reducing content."
        )


def estimate_tokens_by_verbosity(verbosity: str) -> int:
    """Estimate appropriate max tokens for verbosity level

    Args:
        verbosity: Verbosity level ("summary" | "detailed" | "full")

    Returns:
        Recommended max tokens for verbosity level
    """
    levels = {
        "summary": 5000,
        "detailed": 15000,
        "full": 50000
    }
    return levels.get(verbosity, 5000)
