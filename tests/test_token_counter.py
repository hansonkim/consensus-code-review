"""Unit tests for token counter utilities."""

import pytest
from src.mcp.utils.token_counter import (
    count_tokens,
    truncate_to_tokens,
    validate_response_size,
    get_token_stats,
    get_verbosity_limit,
    format_token_warning,
    VERBOSITY_LIMITS,
    MCP_MAX_TOKENS
)


class TestCountTokens:
    """Test token counting functionality."""

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        text = "Hello, world!"
        token_count = count_tokens(text)
        assert isinstance(token_count, int)
        assert token_count > 0

    def test_count_tokens_empty_string(self):
        """Test counting tokens in empty string."""
        assert count_tokens("") == 0

    def test_count_tokens_long_text(self):
        """Test counting tokens in long text."""
        text = "This is a test. " * 1000  # ~16000 characters
        token_count = count_tokens(text)
        assert token_count > 500  # Should be at least 500 tokens
        assert token_count < 10000  # But less than 10000 tokens


class TestTruncateToTokens:
    """Test token truncation functionality."""

    def test_truncate_no_truncation_needed(self):
        """Test when text is already within limit."""
        text = "Short text"
        truncated, was_truncated = truncate_to_tokens(text, 1000)
        assert truncated == text
        assert was_truncated is False

    def test_truncate_with_truncation(self):
        """Test truncating long text."""
        text = "This is a very long text. " * 1000
        max_tokens = 100
        truncated, was_truncated = truncate_to_tokens(text, max_tokens)

        assert was_truncated is True
        assert "(truncated" in truncated.lower()
        assert count_tokens(truncated) <= max_tokens

    def test_truncate_custom_suffix(self):
        """Test truncation with custom suffix."""
        text = "Long text " * 500
        suffix = "...END"
        truncated, was_truncated = truncate_to_tokens(
            text, 50, suffix=suffix
        )

        assert was_truncated is True
        assert truncated.endswith(suffix)


class TestValidateResponseSize:
    """Test response size validation."""

    def test_validate_within_limit(self):
        """Test validation passes for text within limit."""
        text = "Normal response text"
        # Should not raise
        validate_response_size(text)

    def test_validate_exceeds_limit(self):
        """Test validation fails for text exceeding limit."""
        # Create text that exceeds MCP limit (~25k tokens)
        # Each token is roughly 4 characters, so need ~100k+ characters
        text = "This is test text that will be repeated many times. " * 5000  # ~260k characters, ~65k tokens

        with pytest.raises(ValueError) as exc_info:
            validate_response_size(text)

        assert "exceeds MCP limit" in str(exc_info.value)

    def test_validate_custom_limit(self):
        """Test validation with custom limit."""
        text = "Test text " * 100

        with pytest.raises(ValueError):
            validate_response_size(text, max_tokens=10)


class TestGetTokenStats:
    """Test token statistics generation."""

    def test_get_token_stats_structure(self):
        """Test that stats have correct structure."""
        text = "Sample text for stats"
        stats = get_token_stats(text)

        assert "tokens" in stats
        assert "characters" in stats
        assert "ratio" in stats
        assert "max_allowed" in stats
        assert "remaining" in stats
        assert "percent_used" in stats

    def test_get_token_stats_values(self):
        """Test that stats have reasonable values."""
        text = "Hello, world!"
        stats = get_token_stats(text)

        assert stats["tokens"] > 0
        assert stats["characters"] == len(text)
        assert stats["max_allowed"] == MCP_MAX_TOKENS
        assert stats["remaining"] == MCP_MAX_TOKENS - stats["tokens"]
        assert 0 <= stats["percent_used"] <= 100

    def test_get_token_stats_ratio(self):
        """Test character-to-token ratio calculation."""
        text = "Test text"
        stats = get_token_stats(text)

        expected_ratio = stats["characters"] / stats["tokens"]
        assert abs(stats["ratio"] - expected_ratio) < 0.01


class TestVerbosityLimits:
    """Test verbosity mode limits."""

    def test_get_verbosity_limit_summary(self):
        """Test getting summary mode limit."""
        assert get_verbosity_limit("summary") == 5000

    def test_get_verbosity_limit_detailed(self):
        """Test getting detailed mode limit."""
        assert get_verbosity_limit("detailed") == 15000

    def test_get_verbosity_limit_full(self):
        """Test getting full mode limit."""
        assert get_verbosity_limit("full") == 25000

    def test_get_verbosity_limit_invalid(self):
        """Test invalid verbosity mode raises error."""
        with pytest.raises(ValueError) as exc_info:
            get_verbosity_limit("invalid")

        assert "Invalid verbosity mode" in str(exc_info.value)


class TestFormatTokenWarning:
    """Test token warning formatting."""

    def test_format_warning_basic(self):
        """Test basic warning formatting."""
        warning = format_token_warning(3000, 5000, "summary")

        assert "3,000" in warning
        assert "5,000" in warning
        assert "summary" in warning
        assert "%" in warning

    def test_format_warning_exceeded(self):
        """Test warning when limit exceeded."""
        warning = format_token_warning(6000, 5000, "summary")

        assert "EXCEEDED" in warning
        assert "truncated" in warning.lower()

    def test_format_warning_within_limit(self):
        """Test warning when within limit."""
        warning = format_token_warning(3000, 5000, "summary")

        assert "Remaining" in warning
        assert "2,000" in warning  # 5000 - 3000


class TestIntegration:
    """Integration tests for token management workflow."""

    def test_full_workflow_no_truncation(self):
        """Test complete workflow when no truncation needed."""
        text = "This is a reasonable length review."

        # Count tokens
        token_count = count_tokens(text)
        assert token_count < 100

        # Verify it fits in summary mode
        limit = get_verbosity_limit("summary")
        assert token_count < limit

        # Validate response size
        validate_response_size(text)  # Should not raise

        # No truncation needed
        truncated, was_truncated = truncate_to_tokens(text, limit)
        assert not was_truncated

    def test_full_workflow_with_truncation(self):
        """Test complete workflow with truncation."""
        # Create long text that definitely exceeds summary limit
        text = "This is a very detailed code review with lots of information. " * 1000  # ~10k tokens

        # Count tokens
        token_count = count_tokens(text)
        assert token_count > 5000  # Must exceed summary limit

        # Get summary limit
        limit = get_verbosity_limit("summary")

        # Truncate to summary mode
        truncated, was_truncated = truncate_to_tokens(text, limit)
        assert was_truncated

        # Verify truncated version fits
        truncated_count = count_tokens(truncated)
        assert truncated_count <= limit

        # Validate final response
        validate_response_size(truncated)  # Should not raise

    def test_stats_workflow(self):
        """Test token statistics workflow."""
        text = "Sample review text " * 100

        # Get stats
        stats = get_token_stats(text)

        # Verify consistency
        assert stats["tokens"] == count_tokens(text)
        assert stats["characters"] == len(text)

        # Check calculated fields
        assert stats["remaining"] + stats["tokens"] == stats["max_allowed"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_text_truncation(self):
        """Test truncating empty text."""
        truncated, was_truncated = truncate_to_tokens("", 100)
        assert truncated == ""
        assert not was_truncated

    def test_suffix_longer_than_limit(self):
        """Test when suffix is longer than token limit."""
        text = "Test text that needs truncation " * 50  # Make text long enough to need truncation
        suffix = "Very long suffix " * 20  # ~60 tokens
        truncated, was_truncated = truncate_to_tokens(
            text, 10, suffix=suffix
        )

        # Should still handle gracefully
        assert was_truncated
        assert len(truncated) > 0

    def test_unicode_text(self):
        """Test token counting with Unicode characters."""
        text = "Hello 世界! 🌍 Testing émojis and spëcial çhars"
        token_count = count_tokens(text)
        assert token_count > 0

    def test_very_large_text(self):
        """Test handling very large text."""
        text = "x" * 1000000  # 1MB of text

        # Should handle without crashing
        token_count = count_tokens(text)
        assert token_count > 0

        # Should truncate successfully
        truncated, was_truncated = truncate_to_tokens(text, 1000)
        assert was_truncated
        assert count_tokens(truncated) <= 1000
