"""Token counting and truncation utilities

Uses tiktoken for accurate token counting compatible with GPT models.
"""

import json
from typing import Any

# MCP protocol maximum token limit
MCP_MAX_TOKENS = 25000

# Verbosity mode token limits
VERBOSITY_LIMITS = {
    "summary": 5000,
    "detailed": 15000,
    "full": 25000,  # Equal to MCP_MAX_TOKENS (full response)
}


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
        except Exception:
            # Ultimate fallback
            return len(text) // 4


def truncate_to_tokens(
    text: str, max_tokens: int, model: str = "gpt-4", suffix: str = "\n\n...(truncated)"
) -> tuple[str, bool]:
    """Truncate text to maximum token count

    Args:
        text: Text to truncate
        max_tokens: Maximum allowed tokens
        model: Model name for tokenizer
        suffix: Suffix to add when truncating

    Returns:
        Tuple of (truncated_text, was_truncated)
    """
    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model)
    except Exception:
        try:
            import tiktoken

            encoding = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            # Fallback: character-based truncation
            max_chars = max_tokens * 4
            if len(text) <= max_chars:
                return (text, False)
            return (text[:max_chars] + suffix, True)

    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return (text, False)

    # Reserve tokens for suffix
    suffix_tokens = encoding.encode(suffix)
    available_tokens = max_tokens - len(suffix_tokens)

    if available_tokens <= 0:
        return (suffix, True)

    truncated_tokens = tokens[:available_tokens]
    return (encoding.decode(truncated_tokens) + suffix, True)


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


def get_token_stats(text: str, model: str = "gpt-4") -> dict:
    """Get detailed token statistics for text

    Args:
        text: Text to analyze
        model: Model name for encoding

    Returns:
        Dictionary with token count, character count, ratio, max_allowed, remaining, and percent_used
    """
    token_count = count_tokens(text, model)
    char_count = len(text)
    ratio = char_count / token_count if token_count > 0 else 0
    remaining = MCP_MAX_TOKENS - token_count
    percent_used = (token_count / MCP_MAX_TOKENS * 100) if MCP_MAX_TOKENS > 0 else 0

    return {
        "tokens": token_count,
        "characters": char_count,
        "ratio": ratio,
        "max_allowed": MCP_MAX_TOKENS,
        "remaining": remaining,
        "percent_used": percent_used,
    }


def get_verbosity_limit(verbosity: str) -> int:
    """Get token limit for verbosity mode

    Args:
        verbosity: Verbosity mode (summary/detailed/full)

    Returns:
        Token limit for the mode

    Raises:
        ValueError: If verbosity mode is invalid
    """
    if verbosity not in VERBOSITY_LIMITS:
        raise ValueError(
            f"Invalid verbosity mode: '{verbosity}'. "
            f"Must be one of: {', '.join(VERBOSITY_LIMITS.keys())}"
        )
    return VERBOSITY_LIMITS[verbosity]


def format_token_warning(token_count: int, limit: int, mode: str) -> str:
    """Format warning message about token usage

    Args:
        token_count: Current token count
        limit: Token limit
        mode: Verbosity mode (summary/detailed/full)

    Returns:
        Warning message string
    """
    percentage = (token_count / limit) * 100 if limit > 0 else 0
    remaining = limit - token_count

    if token_count > limit:
        return (
            f"⚠️  EXCEEDED limit for '{mode}' mode: {token_count:,} tokens "
            f"(limit: {limit:,}, {percentage:.1f}%) - will be truncated"
        )
    else:
        return (
            f"✅ Within '{mode}' limit: {token_count:,} tokens "
            f"({percentage:.1f}% of {limit:,}) - Remaining: {remaining:,} tokens"
        )


def estimate_tokens_by_verbosity(verbosity: str) -> int:
    """Estimate appropriate max tokens for verbosity level

    Args:
        verbosity: Verbosity level ("summary" | "detailed" | "full")

    Returns:
        Recommended max tokens for verbosity level
    """
    levels = {"summary": 5000, "detailed": 15000, "full": 50000}
    return levels.get(verbosity, 5000)
