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

    def test_artifact_created_marker_detected(self):
        """Message with ARTIFACT_CREATED marker is detected regardless of timestamp."""
        base_time = datetime(2026, 2, 5, 12, 0, 0)
        messages = [
            SimpleNamespace(id="msg1", role="user", created_at=base_time),
            SimpleNamespace(
                id="msg2", 
                role="assistant", 
                created_at=base_time + timedelta(seconds=1),
                content="Here is your BRD.\n\nARTIFACT_CREATED:{\"id\":\"art-123\",\"title\":\"Test\"}|"
            ),
            SimpleNamespace(id="msg3", role="user", created_at=base_time + timedelta(seconds=10)),
            SimpleNamespace(
                id="msg4", 
                role="assistant", 
                created_at=base_time + timedelta(seconds=11),
                content="Regular response without artifact marker."
            ),
        ]
        # No artifacts needed - marker in content should trigger detection
        artifacts = []

        result = _identify_fulfilled_pairs(messages, artifacts)

        # Only msg2 should be filtered (has marker), msg4 should remain
        assert result == {"msg1", "msg2"}

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


class TestMaxContextTokensRegression:
    """TOKEN-02: Regression test ensuring 150K truncation limit is preserved."""

    def test_max_context_tokens_is_150000(self):
        """MAX_CONTEXT_TOKENS must remain 150000 — changing it breaks TOKEN-02."""
        assert MAX_CONTEXT_TOKENS == 150000, (
            f"MAX_CONTEXT_TOKENS changed to {MAX_CONTEXT_TOKENS}. "
            "This breaks TOKEN-02 requirement. If intentional, update this test."
        )

    def test_chars_per_token_is_4(self):
        """CHARS_PER_TOKEN must remain 4 — consistent estimation across codebase."""
        assert CHARS_PER_TOKEN == 4


class TestLinearTokenGrowth:
    """TOKEN-04: Verify token growth is linear across 20+ turn conversations with doc searches."""

    def _make_conversation(self, turns: int):
        """Build a realistic multi-turn conversation with document search annotations."""
        messages = []
        for i in range(turns):
            messages.append({
                "role": "user",
                "content": f"Tell me about feature {i} in the project documents."
            })
            # Realistic assistant response: some text + doc search annotation
            messages.append({
                "role": "assistant",
                "content": (
                    f"Based on the project documentation, feature {i} works as follows. "
                    f"[searched documents]\n"
                    f"This feature handles the {i}-th use case with standard behavior."
                )
            })
        return messages

    def test_token_growth_is_linear_over_20_turns(self):
        """Token counts grow linearly (not quadratically) across 20+ turns."""
        token_counts = []
        for num_turns in range(1, 22):  # 1 to 21 turns
            messages = self._make_conversation(num_turns)
            tokens = estimate_messages_tokens(messages)
            token_counts.append(tokens)

        # Linear growth: each additional turn adds approximately the same token count
        # Compute first differences (turn N+1 - turn N)
        diffs = [token_counts[i+1] - token_counts[i] for i in range(len(token_counts)-1)]

        # All first differences should be approximately equal (linear = constant first diff)
        # Allow 20% variance to handle integer truncation effects
        avg_diff = sum(diffs) / len(diffs)
        for d in diffs:
            assert abs(d - avg_diff) / avg_diff < 0.20, (
                f"Non-linear growth detected: diff={d} deviates >20% from avg={avg_diff:.1f}. "
                f"Token counts: {token_counts}"
            )

    def test_token_growth_not_quadratic(self):
        """Confirm token count at turn N is NOT proportional to N^2."""
        messages_5 = self._make_conversation(5)
        messages_10 = self._make_conversation(10)
        messages_20 = self._make_conversation(20)

        tokens_5 = estimate_messages_tokens(messages_5)
        tokens_10 = estimate_messages_tokens(messages_10)
        tokens_20 = estimate_messages_tokens(messages_20)

        # For linear growth: tokens_20 / tokens_5 should be ~4 (20/5 = 4x)
        # For quadratic growth: tokens_20 / tokens_5 would be ~16 (20^2/5^2 = 16x)
        ratio_10_vs_5 = tokens_10 / tokens_5  # Should be ~2 (linear)
        ratio_20_vs_5 = tokens_20 / tokens_5  # Should be ~4 (linear)

        assert ratio_10_vs_5 < 3.0, f"Turn 10/5 ratio {ratio_10_vs_5:.2f} suggests non-linear growth"
        assert ratio_20_vs_5 < 6.0, f"Turn 20/5 ratio {ratio_20_vs_5:.2f} suggests non-linear growth"

    def test_21_turns_token_count_reasonable(self):
        """A 21-turn conversation with doc annotations stays well under emergency limit."""
        messages = self._make_conversation(21)
        tokens = estimate_messages_tokens(messages)
        # 21 turns × ~2 messages × ~30 words ≈ ~1260 words ≈ ~1680 tokens
        # Should be well under 180K emergency limit
        assert tokens < 10000, f"21-turn conversation uses {tokens} tokens — unexpectedly high"
        assert tokens > 0, "Token count should be positive"
