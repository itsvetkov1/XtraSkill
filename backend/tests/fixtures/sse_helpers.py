"""
SSE (Server-Sent Events) test helpers.

Provides utilities for testing SSE streaming endpoints.
"""

import json
from typing import List, Dict, Any, Optional


def parse_sse_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single SSE line into structured dict.

    Args:
        line: SSE line string (e.g., "event: text_delta", "data: {...}")

    Returns:
        Parsed dict with one of:
        - {"event": "event_type"} for event lines
        - {"data": parsed_json} for data lines
        - {"comment": "text"} for comment lines (heartbeats)
        - None for empty lines
    """
    line = line.strip()
    if not line:
        return None

    if line.startswith(':'):
        # Comment (e.g., heartbeat)
        return {"comment": line[1:].strip()}

    if line.startswith('event:'):
        return {"event": line[6:].strip()}

    if line.startswith('data:'):
        data_str = line[5:].strip()
        try:
            return {"data": json.loads(data_str)}
        except json.JSONDecodeError:
            return {"data": data_str}

    return None


async def collect_sse_events(response) -> List[Dict[str, Any]]:
    """
    Collect all SSE events from a streaming response.

    Args:
        response: httpx streaming response with aiter_lines()

    Returns:
        List of parsed SSE event dicts. Each event may have:
        - {"event": "...", "data": {...}} for standard events
        - {"comment": "..."} for heartbeat comments
    """
    events = []
    current_event = {}

    async for line in response.aiter_lines():
        parsed = parse_sse_line(line)
        if parsed is None:
            # Empty line = end of event
            if current_event:
                events.append(current_event)
                current_event = {}
        elif "comment" in parsed:
            events.append(parsed)
        elif "event" in parsed:
            current_event["event"] = parsed["event"]
        elif "data" in parsed:
            current_event["data"] = parsed["data"]

    # Don't forget last event if no trailing newline
    if current_event:
        events.append(current_event)

    return events


def filter_events_by_type(events: List[Dict], event_type: str) -> List[Dict]:
    """
    Filter events to only those matching event_type.

    Args:
        events: List of SSE event dicts
        event_type: Event type to filter (e.g., "text_delta")

    Returns:
        List of events with matching event type
    """
    return [e for e in events if e.get("event") == event_type]


def assert_event_sequence(events: List[Dict], expected_types: List[str]) -> None:
    """
    Assert events contain expected types in order (ignoring heartbeats).

    Args:
        events: List of SSE event dicts
        expected_types: List of expected event types in order

    Raises:
        AssertionError: If expected types not found in order
    """
    actual_types = [e.get("event") for e in events if "event" in e]
    for expected in expected_types:
        assert expected in actual_types, f"Expected event type '{expected}' not found in {actual_types}"


def get_text_content(events: List[Dict]) -> str:
    """
    Extract concatenated text content from text_delta events.

    Args:
        events: List of SSE event dicts

    Returns:
        Concatenated text from all text_delta events
    """
    text_events = filter_events_by_type(events, "text_delta")
    return "".join(
        e.get("data", {}).get("text", "")
        for e in text_events
        if isinstance(e.get("data"), dict)
    )


def get_usage_from_events(events: List[Dict]) -> Optional[Dict]:
    """
    Extract usage data from message_complete event.

    Args:
        events: List of SSE event dicts

    Returns:
        Usage dict if found, None otherwise
    """
    complete_events = filter_events_by_type(events, "message_complete")
    if complete_events:
        data = complete_events[-1].get("data", {})
        if isinstance(data, dict):
            return data.get("usage")
    return None


def has_heartbeat(events: List[Dict]) -> bool:
    """
    Check if any heartbeat comments are present.

    Args:
        events: List of SSE event dicts

    Returns:
        True if heartbeat comment found
    """
    return any("comment" in e and "heartbeat" in e.get("comment", "") for e in events)
