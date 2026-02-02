"""Unit tests for conversation_service pure functions."""

import pytest
from app.services.conversation_service import (
    estimate_tokens,
    estimate_messages_tokens,
    truncate_conversation,
    CHARS_PER_TOKEN,
    MAX_CONTEXT_TOKENS,
)


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_short_text_estimation(self):
        # CHARS_PER_TOKEN = 4, so 11 chars = 2 tokens (11 // 4 = 2)
        text = "Hello world"  # 11 characters
        assert estimate_tokens(text) == 2

    def test_exact_multiple_of_chars_per_token(self):
        text = "a" * 400  # 400 chars = 100 tokens exactly
        assert estimate_tokens(text) == 100

    def test_rounds_down(self):
        text = "a" * 7  # 7 chars = 1 token (rounds down from 1.75)
        assert estimate_tokens(text) == 1


class TestEstimateMessagesTokens:
    """Tests for estimate_messages_tokens function."""

    def test_empty_list_returns_zero(self):
        assert estimate_messages_tokens([]) == 0

    def test_single_message(self):
        messages = [{"role": "user", "content": "a" * 400}]
        assert estimate_messages_tokens(messages) == 100

    def test_multiple_messages(self):
        messages = [
            {"role": "user", "content": "a" * 400},
            {"role": "assistant", "content": "b" * 200},
        ]
        # 400/4 + 200/4 = 100 + 50 = 150
        assert estimate_messages_tokens(messages) == 150

    def test_message_with_missing_content(self):
        messages = [{"role": "user"}]  # No content key
        assert estimate_messages_tokens(messages) == 0

    def test_message_with_list_content(self):
        # Multi-part content (tool results)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "content": "a" * 40},
                {"type": "tool_result", "content": "b" * 40},
            ]
        }]
        # 40/4 + 40/4 = 10 + 10 = 20
        assert estimate_messages_tokens(messages) == 20


class TestTruncateConversation:
    """Tests for truncate_conversation function."""

    def test_no_truncation_when_under_limit(self):
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        result = truncate_conversation(messages, 10000)
        assert result == messages

    def test_truncation_keeps_recent_messages(self):
        # Create messages that exceed budget
        messages = [
            {"role": "user", "content": "a" * 4000},      # 1000 tokens
            {"role": "assistant", "content": "b" * 4000}, # 1000 tokens
            {"role": "user", "content": "recent"},        # ~1 token
        ]
        # Budget = 100 * 0.8 = 80 tokens
        result = truncate_conversation(messages, 100)

        # Should have summary + recent message
        assert len(result) == 2
        assert "[System note:" in result[0]["content"]
        assert result[1]["content"] == "recent"

    def test_truncation_adds_summary_with_correct_count(self):
        messages = [
            {"role": "user", "content": "a" * 4000},
            {"role": "assistant", "content": "b" * 4000},
            {"role": "user", "content": "c" * 4000},
            {"role": "user", "content": "recent"},
        ]
        result = truncate_conversation(messages, 100)

        # Summary should mention truncated count
        assert "3 earlier messages" in result[0]["content"]

    def test_no_summary_when_nothing_truncated(self):
        messages = [{"role": "user", "content": "short"}]
        result = truncate_conversation(messages, 10000)

        # No summary message added
        assert len(result) == 1
        assert "[System note:" not in result[0]["content"]

    def test_truncation_uses_80_percent_budget(self):
        # 80% of 1000 = 800 tokens budget
        # Message with 700 tokens should fit, 900 should not
        messages = [
            {"role": "user", "content": "a" * 3600},  # 900 tokens
            {"role": "user", "content": "b" * 2800},  # 700 tokens
        ]
        result = truncate_conversation(messages, 1000)

        # Only the 700-token message should remain (fits in 800 budget)
        # Plus summary
        assert len(result) == 2
        assert result[1]["content"] == "b" * 2800
