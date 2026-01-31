# Phase 20: database-api - Research

**Researched:** 2026-01-31
**Domain:** Database migrations, SSE heartbeat/keep-alive, FastAPI streaming
**Confidence:** HIGH

## Summary

Phase 20 involves two distinct technical areas: (1) adding a `model_provider` column to the Thread database model, and (2) implementing SSE heartbeat mechanisms to prevent connection timeouts during extended LLM thinking periods (5+ minutes for DeepSeek).

The database migration is straightforward - SQLite supports simple `ALTER TABLE ADD COLUMN` directly, and the project already has Alembic configured with `render_as_batch=True` for SQLite compatibility. The existing migration pattern in `database.py` provides a model for handling this.

For SSE heartbeats, the project already uses `sse-starlette` which has built-in ping support. However, the user requirement specifies using SSE comment format (`: heartbeat\n\n`) which is invisible to JavaScript clients. The key insight is that heartbeats should only be sent during silence periods when the LLM is "thinking" - not continuously throughout streaming.

**Primary recommendation:** Use Alembic migration for the database column, and implement a custom heartbeat wrapper around the LLM adapter that tracks time since last data and sends SSE comments during silence periods.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ | ORM and database models | Already in use, async support |
| Alembic | 1.18+ | Database migrations | Already configured with batch mode |
| sse-starlette | 3.2.0 | SSE streaming | Already in use, has ping support |
| asyncio | stdlib | Async timeout/scheduling | Built-in timeout context managers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiosqlite | 0.19+ | Async SQLite driver | Already installed, handles async operations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Alembic migration | Raw SQL in `_run_migrations()` | Raw SQL is simpler for single column, but Alembic provides version tracking |
| Custom heartbeat logic | sse-starlette `ping` parameter | Built-in ping is simpler but uses different format than specified |

**Installation:**
```bash
# No new dependencies needed - all already installed
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── models.py              # Add model_provider column to Thread
├── routes/
│   ├── threads.py         # Update ThreadCreate/ThreadResponse for provider
│   └── conversations.py   # Add heartbeat wrapper to streaming
├── services/
│   └── ai_service.py      # Pass provider to factory, wrap stream with heartbeat
└── alembic/versions/      # New migration file for model_provider column
```

### Pattern 1: Database Column Addition with Default Value
**What:** Add nullable column with default value for backward compatibility
**When to use:** When adding columns to existing tables with data
**Example:**
```python
# In models.py
class Thread(Base):
    __tablename__ = "threads"
    # ... existing fields ...

    # New column with default for existing records
    model_provider: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="anthropic"  # Default for new threads
    )
```

### Pattern 2: SSE Comment Heartbeat During Silence
**What:** Track time since last data, send SSE comment if threshold exceeded
**When to use:** Long-running streaming operations that may have silent periods
**Example:**
```python
# Source: SSE specification (MDN)
async def stream_with_heartbeat(
    async_gen: AsyncGenerator,
    heartbeat_interval: float = 15.0,
    initial_delay: float = 5.0,
    max_timeout: float = 600.0  # 10 minutes
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Wrap an async generator to add heartbeat comments during silence.

    - First heartbeat after `initial_delay` seconds of silence
    - Subsequent heartbeats every `heartbeat_interval` seconds
    - Total max wait time of `max_timeout` for any single silence period
    """
    import asyncio
    import time

    last_data_time = time.monotonic()
    first_heartbeat_sent = False

    async def check_timeout_and_heartbeat():
        nonlocal last_data_time, first_heartbeat_sent
        while True:
            now = time.monotonic()
            silence_duration = now - last_data_time

            # Check for max timeout
            if silence_duration > max_timeout:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Timeout waiting for LLM response"})
                }
                return

            # Determine if heartbeat needed
            threshold = initial_delay if not first_heartbeat_sent else heartbeat_interval
            if silence_duration >= threshold:
                # SSE comment format - invisible to EventSource
                yield {"comment": "heartbeat"}
                first_heartbeat_sent = True
                last_data_time = now  # Reset timer after heartbeat

            await asyncio.sleep(1)  # Check every second

    # Run heartbeat checker and data stream concurrently
    # Actual implementation uses asyncio.TaskGroup or similar
```

### Pattern 3: Thread Creation with Provider Parameter
**What:** Accept optional provider in thread creation, store in database
**When to use:** When creating new threads with provider binding
**Example:**
```python
# In routes/threads.py
class ThreadCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    model_provider: Optional[str] = Field(None, max_length=20)

# Validation in endpoint
VALID_PROVIDERS = ["anthropic", "google", "deepseek"]

if thread_data.model_provider and thread_data.model_provider not in VALID_PROVIDERS:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid provider. Valid options: {', '.join(VALID_PROVIDERS)}"
    )
```

### Anti-Patterns to Avoid
- **Continuous heartbeats during active streaming:** Only send heartbeats during silence, not alongside data
- **Using sse-starlette's built-in ping for this:** The built-in ping uses a different format and timing than specified
- **Blocking the main stream for heartbeats:** Use concurrent tasks, not sequential waits

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE formatting | Manual string concatenation | sse-starlette ServerSentEvent | Handles edge cases, encoding |
| Database migrations | Raw `ALTER TABLE` in init | Alembic with batch mode | Version tracking, rollback support |
| Async timeout with reset | Manual timestamp tracking | asyncio.timeout with reschedule | Thread-safe, well-tested |

**Key insight:** The heartbeat logic is application-specific enough that it needs custom implementation, but the SSE message formatting and database migration tools should be reused.

## Common Pitfalls

### Pitfall 1: Breaking EventSource on Client
**What goes wrong:** Sending malformed SSE messages causes JavaScript EventSource to error
**Why it happens:** Incorrect newline handling or comment format
**How to avoid:** Use exact SSE spec format: `: comment\n\n` (colon, space, text, double newline)
**Warning signs:** JavaScript console shows EventSource errors

### Pitfall 2: Heartbeat Timer Not Resetting
**What goes wrong:** Heartbeats continue even when data is flowing
**Why it happens:** Timer reset logic not triggered on data events
**How to avoid:** Reset `last_data_time` every time a data chunk is yielded
**Warning signs:** Heartbeats appearing interleaved with normal data

### Pitfall 3: Migration Fails on Existing Database
**What goes wrong:** `NOT NULL` constraint fails on existing rows
**Why it happens:** Adding non-nullable column without default to table with data
**How to avoid:** Use `nullable=True` or provide server-side default
**Warning signs:** Alembic upgrade fails with constraint violation

### Pitfall 4: Proxy Timeout Still Occurs
**What goes wrong:** Connection drops despite heartbeats
**Why it happens:** Proxy timeout shorter than heartbeat interval, or heartbeats not reaching proxy
**How to avoid:** Ensure heartbeat interval (15s) is well under typical proxy timeouts (60s). Add `X-Accel-Buffering: no` header.
**Warning signs:** 502/504 errors from nginx/load balancer after ~60 seconds

### Pitfall 5: Thread Provider Not Passed to Chat
**What goes wrong:** Chat endpoint ignores thread's stored provider, uses default
**Why it happens:** Provider lookup not wired to AIService initialization
**How to avoid:** Load thread with provider, pass to `AIService(provider=thread.model_provider)`
**Warning signs:** All chats use anthropic regardless of thread setting

## Code Examples

Verified patterns from official sources and codebase analysis:

### Alembic Migration for model_provider Column
```python
# Source: Alembic documentation + existing project pattern
"""Add model_provider column to threads

Revision ID: [generated]
Revises: [previous]
Create Date: 2026-01-31
"""
from alembic import op
import sqlalchemy as sa

revision = '[generated]'
down_revision = '[previous]'

def upgrade() -> None:
    # batch_alter_table handles SQLite limitations
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('model_provider', sa.String(20), nullable=True, server_default='anthropic')
        )

def downgrade() -> None:
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.drop_column('model_provider')
```

### SSE Comment Format for Heartbeat
```python
# Source: MDN SSE specification
# Comments start with colon, are invisible to EventSource

async def yield_heartbeat():
    """Yield SSE comment that keeps connection alive but is invisible to client."""
    # Format: ": heartbeat\n\n"
    # Using sse-starlette's ServerSentEvent:
    from sse_starlette import ServerSentEvent
    return ServerSentEvent(comment="heartbeat")

# Or manual format for direct yield:
yield {"comment": "heartbeat"}  # sse-starlette handles formatting
```

### Thread Response with Provider
```python
# Updated response model
class ThreadResponse(BaseModel):
    id: str
    project_id: str
    title: Optional[str]
    model_provider: Optional[str] = "anthropic"  # Default for backward compat
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
```

### Concurrent Heartbeat with Data Stream
```python
# Source: asyncio documentation
import asyncio
from typing import AsyncGenerator

async def stream_with_timeout_heartbeat(
    data_gen: AsyncGenerator,
    heartbeat_interval: float = 15.0,
    initial_delay: float = 5.0,
    max_silence: float = 600.0
) -> AsyncGenerator:
    """
    Wrap async generator with heartbeat during silence and overall timeout.
    """
    import time

    queue = asyncio.Queue()
    last_data = time.monotonic()
    done = False

    async def producer():
        nonlocal done
        try:
            async for item in data_gen:
                await queue.put(("data", item))
        finally:
            done = True
            await queue.put(("done", None))

    async def heartbeat_producer():
        nonlocal last_data
        first_sent = False
        while not done:
            await asyncio.sleep(1)
            silence = time.monotonic() - last_data

            if silence > max_silence:
                await queue.put(("timeout", None))
                return

            threshold = initial_delay if not first_sent else heartbeat_interval
            if silence >= threshold:
                await queue.put(("heartbeat", None))
                first_sent = True
                last_data = time.monotonic()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer())
        tg.create_task(heartbeat_producer())

        while True:
            msg_type, data = await queue.get()

            if msg_type == "data":
                last_data = time.monotonic()
                yield data
            elif msg_type == "heartbeat":
                yield {"comment": "heartbeat"}
            elif msg_type == "timeout":
                yield {"event": "error", "data": '{"message": "Timeout"}'}
                return
            elif msg_type == "done":
                return
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| sse-starlette 1.x ping | sse-starlette 3.x with ping_message_factory | 2024 | Custom ping format support |
| asyncio.wait_for for timeout | asyncio.timeout with reschedule | Python 3.11+ | Per-chunk timeout reset |
| Raw ALTER TABLE | Alembic batch mode | Alembic 1.7+ | SQLite full ALTER support |

**Deprecated/outdated:**
- `async_timeout` library: Use stdlib `asyncio.timeout` on Python 3.11+ (project uses 3.11+)

## Open Questions

Things that couldn't be fully resolved:

1. **TaskGroup exception handling**
   - What we know: asyncio.TaskGroup propagates exceptions from any task
   - What's unclear: Best pattern for cancelling heartbeat when data stream errors
   - Recommendation: Use try/finally to ensure cleanup, catch and re-raise stream errors

2. **sse-starlette comment yielding**
   - What we know: Library supports `comment` field in ServerSentEvent
   - What's unclear: Whether yielding dict with `comment` key works directly
   - Recommendation: Test with library, may need explicit ServerSentEvent instantiation

## Sources

### Primary (HIGH confidence)
- MDN Web Docs: [Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) - SSE specification
- Alembic Documentation: [Batch Migrations for SQLite](https://alembic.sqlalchemy.org/en/latest/batch.html) - Migration patterns
- Project codebase: `backend/app/database.py`, `backend/alembic/env.py` - Existing patterns

### Secondary (MEDIUM confidence)
- sse-starlette GitHub: [README.md](https://github.com/sysid/sse-starlette/blob/main/README.md) - Library documentation
- Python Documentation: [asyncio Tasks](https://docs.python.org/3/library/asyncio-task.html) - Timeout patterns
- sse-starlette PyPI: [sse-starlette](https://pypi.org/project/sse-starlette/) - Current version info

### Tertiary (LOW confidence)
- Medium articles on SSE implementation patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing project dependencies
- Architecture: HIGH - Patterns verified against codebase and official docs
- Pitfalls: HIGH - Based on SSE spec and SQLite limitations documented officially

**Research date:** 2026-01-31
**Valid until:** 60 days (stable patterns, no fast-moving dependencies)
