"""Unit tests for SSE streaming helpers and stream_with_heartbeat."""

import pytest
from tests.fixtures.sse_helpers import (
    parse_sse_line,
    filter_events_by_type,
    assert_event_sequence,
    get_text_content,
    get_usage_from_events,
    has_heartbeat,
)


class TestParseSSELine:
    """Tests for parse_sse_line function."""

    def test_parse_event_line(self):
        """Event lines are parsed correctly."""
        result = parse_sse_line("event: text_delta")
        assert result == {"event": "text_delta"}

    def test_parse_event_line_with_spaces(self):
        """Event lines with extra spaces are trimmed."""
        result = parse_sse_line("event:   message_complete  ")
        assert result == {"event": "message_complete"}

    def test_parse_data_line_json(self):
        """Data lines with JSON are parsed."""
        result = parse_sse_line('data: {"text": "hello"}')
        assert result == {"data": {"text": "hello"}}

    def test_parse_data_line_complex_json(self):
        """Data lines with nested JSON are parsed."""
        result = parse_sse_line('data: {"usage": {"input_tokens": 100, "output_tokens": 50}}')
        assert result == {"data": {"usage": {"input_tokens": 100, "output_tokens": 50}}}

    def test_parse_data_line_non_json(self):
        """Data lines with non-JSON return raw string."""
        result = parse_sse_line("data: plain text here")
        assert result == {"data": "plain text here"}

    def test_parse_comment_line(self):
        """Comment lines (heartbeats) are parsed."""
        result = parse_sse_line(": heartbeat")
        assert result == {"comment": "heartbeat"}

    def test_parse_comment_line_with_space(self):
        """Comment lines with leading space are handled."""
        result = parse_sse_line(":  keep-alive  ")
        assert result == {"comment": "keep-alive"}

    def test_parse_empty_line(self):
        """Empty lines return None."""
        result = parse_sse_line("")
        assert result is None

    def test_parse_whitespace_line(self):
        """Whitespace-only lines return None."""
        result = parse_sse_line("   ")
        assert result is None


class TestFilterEventsByType:
    """Tests for filter_events_by_type function."""

    def test_filter_single_type(self):
        """Filter extracts only matching event types."""
        events = [
            {"event": "text_delta", "data": {"text": "a"}},
            {"comment": "heartbeat"},
            {"event": "text_delta", "data": {"text": "b"}},
            {"event": "message_complete", "data": {}},
        ]
        text_events = filter_events_by_type(events, "text_delta")
        assert len(text_events) == 2
        assert all(e["event"] == "text_delta" for e in text_events)

    def test_filter_no_matches(self):
        """Filter returns empty list when no matches."""
        events = [
            {"event": "text_delta", "data": {"text": "a"}},
            {"comment": "heartbeat"},
        ]
        error_events = filter_events_by_type(events, "error")
        assert error_events == []

    def test_filter_excludes_comments(self):
        """Filter excludes comment events."""
        events = [
            {"comment": "heartbeat"},
            {"event": "text_delta", "data": {"text": "x"}},
        ]
        result = filter_events_by_type(events, "text_delta")
        assert len(result) == 1


class TestAssertEventSequence:
    """Tests for assert_event_sequence function."""

    def test_sequence_found(self):
        """Sequence assertion finds expected types in order."""
        events = [
            {"event": "text_delta", "data": {}},
            {"event": "message_complete", "data": {}},
        ]
        # Should not raise
        assert_event_sequence(events, ["text_delta", "message_complete"])

    def test_sequence_with_heartbeats(self):
        """Sequence assertion ignores heartbeats."""
        events = [
            {"event": "text_delta", "data": {}},
            {"comment": "heartbeat"},
            {"event": "message_complete", "data": {}},
        ]
        # Should not raise
        assert_event_sequence(events, ["text_delta", "message_complete"])

    def test_sequence_missing_type_raises(self):
        """Sequence assertion raises when expected type missing."""
        events = [
            {"event": "text_delta", "data": {}},
        ]
        with pytest.raises(AssertionError) as exc_info:
            assert_event_sequence(events, ["message_complete"])
        assert "message_complete" in str(exc_info.value)


class TestGetTextContent:
    """Tests for get_text_content function."""

    def test_extracts_text_from_deltas(self):
        """Concatenates text from all text_delta events."""
        events = [
            {"event": "text_delta", "data": {"text": "Hello"}},
            {"event": "text_delta", "data": {"text": " world"}},
            {"event": "message_complete", "data": {}},
        ]
        text = get_text_content(events)
        assert text == "Hello world"

    def test_ignores_non_text_events(self):
        """Ignores events without text data."""
        events = [
            {"event": "text_delta", "data": {"text": "Hi"}},
            {"comment": "heartbeat"},
            {"event": "tool_executing", "data": {"status": "working"}},
        ]
        text = get_text_content(events)
        assert text == "Hi"

    def test_empty_events(self):
        """Returns empty string for no text events."""
        events = [
            {"comment": "heartbeat"},
            {"event": "message_complete", "data": {}},
        ]
        text = get_text_content(events)
        assert text == ""


class TestGetUsageFromEvents:
    """Tests for get_usage_from_events function."""

    def test_extracts_usage(self):
        """Extracts usage from message_complete event."""
        events = [
            {"event": "text_delta", "data": {"text": "Hi"}},
            {"event": "message_complete", "data": {
                "content": "Hi",
                "usage": {"input_tokens": 10, "output_tokens": 5}
            }},
        ]
        usage = get_usage_from_events(events)
        assert usage == {"input_tokens": 10, "output_tokens": 5}

    def test_no_complete_event(self):
        """Returns None if no message_complete event."""
        events = [
            {"event": "text_delta", "data": {"text": "Hi"}},
        ]
        usage = get_usage_from_events(events)
        assert usage is None


class TestHasHeartbeat:
    """Tests for has_heartbeat function."""

    def test_has_heartbeat_true(self):
        """Returns True when heartbeat present."""
        events = [
            {"event": "text_delta", "data": {}},
            {"comment": "heartbeat"},
        ]
        assert has_heartbeat(events) is True

    def test_has_heartbeat_false(self):
        """Returns False when no heartbeat."""
        events = [
            {"event": "text_delta", "data": {}},
            {"event": "message_complete", "data": {}},
        ]
        assert has_heartbeat(events) is False


class TestStreamWithHeartbeat:
    """Tests for ai_service.stream_with_heartbeat function."""

    @pytest.mark.asyncio
    async def test_yields_original_events(self):
        """Original events from source stream are yielded."""
        from app.services.ai_service import stream_with_heartbeat

        async def mock_source():
            yield {"event": "text_delta", "data": '{"text": "hello"}'}
            yield {"event": "message_complete", "data": "{}"}

        events = []
        async for event in stream_with_heartbeat(mock_source()):
            events.append(event)
            if event.get("event") == "message_complete":
                break

        # Should have received original events
        event_types = [e.get("event") for e in events if "event" in e]
        assert "text_delta" in event_types
        assert "message_complete" in event_types

    @pytest.mark.asyncio
    async def test_heartbeat_comment_format(self):
        """Heartbeat comments use correct SSE format."""
        # Test that the heartbeat is a dict with "comment" key
        # The actual SSE format (": heartbeat") is handled by sse-starlette
        from app.services.ai_service import stream_with_heartbeat

        async def slow_source():
            import asyncio
            await asyncio.sleep(0.01)  # Small delay
            yield {"event": "text_delta", "data": '{"text": "hi"}'}
            yield {"event": "message_complete", "data": "{}"}

        events = []
        async for event in stream_with_heartbeat(
            slow_source(),
            initial_delay=0.005,  # Very short for testing
            heartbeat_interval=0.005
        ):
            events.append(event)
            if event.get("event") == "message_complete":
                break

        # Check that heartbeat events have correct structure
        heartbeats = [e for e in events if "comment" in e]
        for hb in heartbeats:
            assert hb["comment"] == "heartbeat"

    @pytest.mark.asyncio
    async def test_handles_generator_completion(self):
        """Generator completes normally after source exhausted."""
        from app.services.ai_service import stream_with_heartbeat

        async def mock_source():
            yield {"event": "text_delta", "data": '{"text": "only"}'}
            yield {"event": "message_complete", "data": "{}"}

        events = []
        async for event in stream_with_heartbeat(mock_source()):
            events.append(event)

        # Should have received all events
        assert any(e.get("event") == "message_complete" for e in events)
