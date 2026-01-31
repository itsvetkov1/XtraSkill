---
phase: 20-database-api
plan: 02
subsystem: backend-streaming
tags: [sse, heartbeat, timeout, keepalive, streaming]
dependency-graph:
  requires: [20-01]
  provides: [SSE heartbeat during LLM thinking, connection keepalive, configurable timeout]
  affects: [Phase 21 frontend provider UI, extended thinking models like DeepSeek]
tech-stack:
  added: []
  patterns: [async queue producer-consumer, SSE comments, monotonic timing]
key-files:
  created: []
  modified:
    - backend/app/services/ai_service.py
    - backend/app/routes/conversations.py
decisions:
  - id: DEC-20-02-01
    choice: SSE comment format for heartbeat
    rationale: Comments (': heartbeat\n\n') are invisible to JavaScript EventSource clients but keep proxies alive
  - id: DEC-20-02-02
    choice: 5s initial delay, 15s interval, 10min max timeout
    rationale: Allows DeepSeek's 5+ minute thinking while preventing stale connections
metrics:
  duration: 2 minutes
  completed: 2026-01-31
---

# Phase 20 Plan 02: SSE Heartbeat Mechanism Summary

Implemented SSE heartbeat wrapper to prevent connection timeouts during extended LLM thinking periods (critical for DeepSeek reasoning).

## What Was Done

### Task 1: Create heartbeat wrapper utility in ai_service.py

Added `stream_with_heartbeat` async generator function with:

```python
async def stream_with_heartbeat(
    data_gen: AsyncGenerator[Dict[str, Any], None],
    initial_delay: float = 5.0,        # First heartbeat after 5s silence
    heartbeat_interval: float = 15.0,  # Subsequent heartbeats every 15s
    max_silence: float = 600.0         # Timeout after 10min total silence
) -> AsyncGenerator[Dict[str, Any], None]:
```

Key implementation details:
- Uses asyncio Queue with producer-consumer pattern
- data_producer task forwards events from source generator
- heartbeat_producer task monitors silence and sends heartbeats
- Uses `time.monotonic()` for accurate timing
- Resets heartbeat timer when real data arrives
- Yields `{"comment": "heartbeat"}` for SSE comment format
- Yields error event on timeout with user-friendly message
- Proper cleanup of background tasks in finally block

### Task 2: Wrap chat endpoint stream with heartbeat

Modified `backend/app/routes/conversations.py`:

```python
# Create raw stream generator
raw_stream = ai_service.stream_chat(conversation, thread.project_id, thread_id, db)

# Wrap with heartbeat for long thinking periods
heartbeat_stream = stream_with_heartbeat(raw_stream)

async for event in heartbeat_stream:
    # Heartbeat events pass through directly (no accumulation)
    if "comment" in event:
        yield event
        continue

    # Normal event processing...
```

Key changes:
- Import stream_with_heartbeat from ai_service
- Wrap raw stream with heartbeat wrapper
- Handle comment events (pass through without accumulation)
- Use `.get()` for event type checks (comment events lack "event" key)

## Commits

| Commit | Description |
|--------|-------------|
| 1b73544 | feat(20-02): add stream_with_heartbeat utility for SSE keepalive |
| d46a58c | feat(20-02): integrate heartbeat wrapper into chat endpoint |

## Verification

- [x] stream_with_heartbeat function exists with correct signature
- [x] Initial delay configurable (default 5s)
- [x] Heartbeat interval configurable (default 15s)
- [x] Max silence timeout configurable (default 600s/10min)
- [x] Heartbeat yields {"comment": "heartbeat"} format
- [x] Timeout yields error event with message
- [x] conversations.py imports and uses stream_with_heartbeat
- [x] Heartbeat events pass through event_generator correctly
- [x] Normal events still accumulated and processed correctly
- [x] Backend starts without import/syntax errors

## Deviations from Plan

None - plan executed exactly as written.

## How It Works

1. **Normal streaming:** Events flow through without heartbeats
2. **LLM thinking (silence):** After 5 seconds, first heartbeat sent
3. **Continued silence:** Heartbeats every 15 seconds
4. **Data arrives:** Timer resets, heartbeats stop until next silence
5. **Extended timeout:** After 10 minutes of silence, timeout error sent

**SSE wire format:**
```
: heartbeat

```
(Colon prefix makes it a comment - EventSource clients ignore it, proxies see activity)

## Next Phase Readiness

Phase 20-02 completes the backend preparation for multi-provider support:

**Backend Complete:**
- Thread stores provider binding (20-01)
- Chat routes to correct adapter (20-01)
- SSE survives extended thinking (20-02)

**Ready for Phase 21 (Frontend):**
- Add provider selector in new thread dialog
- Display provider in thread list
- No frontend changes needed for heartbeat (invisible by design)

---

*Summary created: 2026-01-31*
*Plan duration: 2 minutes*
