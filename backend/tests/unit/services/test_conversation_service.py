"""Unit tests for conversation_service pure functions."""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from app.services.conversation_service import (
    estimate_tokens,
    estimate_messages_tokens,
    truncate_conversation,
    _identify_fulfilled_pairs,
    CHARS_PER_TOKEN,
    MAX_CONTEXT_TOKENS,
    ARTIFACT_CORRELATION_WINDOW,
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


class TestIdentifyFulfilledPairs:
    """Tests for _identify_fulfilled_pairs function."""

    def test_no_artifacts_returns_empty_set(self):
        """No artifacts means nothing to filter."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            SimpleNamespace(id="msg1", role="user", created_at=base_time),
            SimpleNamespace(id="msg2", role="assistant", created_at=base_time + timedelta(seconds=1)),
        ]
        artifacts = []

        result = _identify_fulfilled_pairs(messages, artifacts)

        assert result == set()

    def test_single_fulfilled_pair_detected(self):
        """User + assistant with artifact within 5s window are both filtered."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            SimpleNamespace(id="msg1", role="user", created_at=base_time),
            SimpleNamespace(id="msg2", role="assistant", created_at=base_time + timedelta(seconds=1)),
        ]
        artifacts = [
            SimpleNamespace(created_at=base_time + timedelta(seconds=3)),  # 2s after assistant
        ]

        result = _identify_fulfilled_pairs(messages, artifacts)

        assert result == {"msg1", "msg2"}

    def test_unfulfilled_request_not_filtered(self):
        """User + assistant with NO artifact remain in context."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            SimpleNamespace(id="msg1", role="user", created_at=base_time),
            SimpleNamespace(id="msg2", role="assistant", created_at=base_time + timedelta(seconds=1)),
        ]
        artifacts = []  # No artifact created

        result = _identify_fulfilled_pairs(messages, artifacts)

        assert result == set()

    def test_multiple_fulfilled_pairs(self):
        """Multiple request pairs, only fulfilled ones are filtered."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            # Pair 1 - fulfilled
            SimpleNamespace(id="msg1", role="user", created_at=base_time),
            SimpleNamespace(id="msg2", role="assistant", created_at=base_time + timedelta(seconds=1)),
            # Pair 2 - NOT fulfilled (no artifact)
            SimpleNamespace(id="msg3", role="user", created_at=base_time + timedelta(seconds=10)),
            SimpleNamespace(id="msg4", role="assistant", created_at=base_time + timedelta(seconds=11)),
            # Pair 3 - fulfilled
            SimpleNamespace(id="msg5", role="user", created_at=base_time + timedelta(seconds=20)),
            SimpleNamespace(id="msg6", role="assistant", created_at=base_time + timedelta(seconds=21)),
        ]
        artifacts = [
            SimpleNamespace(created_at=base_time + timedelta(seconds=3)),   # Matches msg2
            SimpleNamespace(created_at=base_time + timedelta(seconds=22)),  # Matches msg6
        ]

        result = _identify_fulfilled_pairs(messages, artifacts)

        # Pairs 1 and 3 fulfilled, Pair 2 NOT fulfilled
        assert result == {"msg1", "msg2", "msg5", "msg6"}

    def test_artifact_before_message_not_matched(self):
        """Artifact created BEFORE assistant message doesn't match (negative time diff)."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            SimpleNamespace(id="msg1", role="user", created_at=base_time),
            SimpleNamespace(id="msg2", role="assistant", created_at=base_time + timedelta(seconds=10)),
        ]
        artifacts = [
            SimpleNamespace(created_at=base_time + timedelta(seconds=5)),  # Before assistant msg
        ]

        result = _identify_fulfilled_pairs(messages, artifacts)

        assert result == set()

    def test_artifact_outside_window_not_matched(self):
        """Artifact created >5s after assistant message doesn't match."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            SimpleNamespace(id="msg1", role="user", created_at=base_time),
            SimpleNamespace(id="msg2", role="assistant", created_at=base_time + timedelta(seconds=1)),
        ]
        artifacts = [
            SimpleNamespace(created_at=base_time + timedelta(seconds=11)),  # 10s after assistant
        ]

        result = _identify_fulfilled_pairs(messages, artifacts)

        assert result == set()

    def test_no_preceding_user_message(self):
        """Assistant message first in list (no preceding user) only filters assistant."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            SimpleNamespace(id="msg1", role="assistant", created_at=base_time),
        ]
        artifacts = [
            SimpleNamespace(created_at=base_time + timedelta(seconds=2)),
        ]

        result = _identify_fulfilled_pairs(messages, artifacts)

        # Only assistant message filtered, no IndexError
        assert result == {"msg1"}
