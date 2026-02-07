---
phase: 43-backend-logging-foundation
plan: 01
subsystem: backend-logging
tags: [logging, structlog, async-safety, configuration]
requires: [config-infrastructure]
provides: [logging-service, structured-json-logs, async-safe-logging]
affects: [phase-44-correlation-tracking, phase-45-api-integration]
tech-stack:
  added: [structlog-25.5.0, asgi-correlation-id-4.3.0]
  patterns: [queue-handler-pattern, singleton-service, timed-rotation]
key-files:
  created:
    - backend/app/services/logging_service.py
  modified:
    - backend/app/config.py
    - backend/requirements.txt
decisions:
  - id: LOG-001
    decision: Use QueueHandler + QueueListener pattern for async-safe logging
    rationale: Prevents blocking FastAPI event loop during file I/O (P-01 prevention)
    alternatives: [direct-file-write, async-file-handlers]
  - id: LOG-002
    decision: Use structlog for structured JSON logging
    rationale: Native JSON output, processor chains, compatible with AI analysis tools
    alternatives: [python-json-logger, custom-formatter]
  - id: LOG-003
    decision: TimedRotatingFileHandler with daily rotation
    rationale: Simple, reliable, configurable retention via log_rotation_days setting
    alternatives: [size-based-rotation, external-logrotate]
metrics:
  duration: 2min 39sec
  completed: 2026-02-07
---

# Phase 43 Plan 01: Backend Logging Foundation Summary

**One-liner:** Async-safe structured JSON logging with QueueHandler pattern, configurable via env vars

## What Was Built

Core logging infrastructure for v1.9.5 milestone:

1. **LoggingService singleton** (169 lines)
   - QueueHandler + QueueListener pattern for async-safe file writes
   - structlog with JSON renderer for structured output
   - TimedRotatingFileHandler for daily log rotation
   - Support for log categories (api, ai, db, auth)
   - Custom field support (correlation_id, user_id, etc.)

2. **Configuration settings** in Settings class
   - `log_dir`: Directory for log files (default: "logs")
   - `log_level`: Configurable log level (default: "INFO")
   - `log_rotation_days`: Retention period (default: 7 days)
   - `log_dir_path` property: Path resolution relative to backend/

3. **Dependencies added**
   - structlog>=25.0.0 (structured logging with processors)
   - asgi-correlation-id>=4.3.0 (for Phase 44 request ID propagation)

## Architecture Decisions

### Decision: QueueHandler Pattern (P-01 Prevention)

**Problem:** Direct file writes in async request handlers block the event loop.

**Solution:** Queue-based logging architecture:
```
Application code → structlog → Python logging → QueueHandler (non-blocking)
                                                      ↓
                                        Background thread: QueueListener
                                                      ↓
                                          File write (isolated from event loop)
```

**Benefits:**
- Log calls return immediately (no I/O blocking)
- File writes happen in background thread
- Graceful shutdown with queue flush

### Decision: Structured JSON Format

**Example log entry:**
```json
{
  "category": "api",
  "correlation_id": "abc-123",
  "endpoint": "/chat",
  "event": "Request received",
  "timestamp": "2026-02-07T18:30:23.104231Z",
  "level": "info",
  "logger": "ba_assistant"
}
```

**Why JSON:**
- Machine-parseable for AI analysis (milestone goal)
- Structured fields enable filtering/aggregation
- Standard format for log analysis tools

### Decision: Environment-Configurable Settings

All logging behavior controllable via environment variables:
- `LOG_DIR`: Change log location (e.g., /var/log for production)
- `LOG_LEVEL`: DEBUG|INFO|WARNING|ERROR|CRITICAL
- `LOG_ROTATION_DAYS`: Retention policy (compliance/storage management)

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add logging configuration to Settings | bab0633 | backend/app/config.py |
| 2 | Add structlog and asgi-correlation-id dependencies | b40c4d0 | backend/requirements.txt |
| 3 | Create LoggingService with async-safe file handlers | 37e5fb2 | backend/app/services/logging_service.py |

## Verification Results

✅ **Config settings accessible:**
```bash
$ python -c "from app.config import settings; print(settings.log_level, settings.log_dir, settings.log_rotation_days)"
INFO logs 7
```

✅ **JSON log format valid:**
```json
{
  "category": "api",
  "correlation_id": "test-123",
  "endpoint": "/test",
  "event": "Verification test",
  "timestamp": "2026-02-07T18:30:23.104231Z",
  "level": "info",
  "logger": "ba_assistant"
}
```

✅ **Dependencies installed:**
- structlog 25.5.0 installed without conflicts
- asgi-correlation-id 4.3.4 installed successfully

✅ **Async-safe operation:**
- QueueHandler captures log calls (non-blocking)
- QueueListener writes to file in background thread
- Graceful shutdown with `shutdown()` method

## Integration Points

### For Phase 44 (Correlation ID Middleware):
```python
from app.services.logging_service import get_logging_service

ls = get_logging_service()
ls.log('INFO', 'Request received', 'api',
       correlation_id=request.headers.get('X-Correlation-ID'),
       endpoint=request.url.path)
```

### For Phase 45 (API Route Integration):
```python
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    ls = get_logging_service()
    ls.log('INFO', 'Chat request started', 'api',
           user_id=current_user.id,
           project_id=request.project_id,
           correlation_id=get_correlation_id())
    # ... endpoint logic ...
```

### For Phase 46 (AI Service Integration):
```python
async def call_llm(prompt: str):
    ls = get_logging_service()
    ls.log('DEBUG', 'LLM request started', 'ai',
           provider='anthropic',
           model='claude-sonnet-4.5',
           prompt_length=len(prompt))
    # ... AI call ...
```

## Deviations from Plan

None - plan executed exactly as written.

## Testing Notes

**Manual verification completed:**
1. Config settings accessible via `settings.log_level`, etc.
2. Log file created at `backend/logs/app.log`
3. JSON format validated with all required fields
4. Queue-based logging operational (verified via time.sleep test)
5. Graceful shutdown flushes queue successfully

**No unit tests in this plan** - testing deferred to dedicated phase per milestone roadmap.

## Next Phase Readiness

**Ready for Phase 44:** Correlation ID middleware can now:
- Import `get_logging_service()`
- Log with correlation_id field
- Rely on async-safe operation

**Blockers:** None

**Concerns:** None - core infrastructure solid and verified

## Files Changed

### Created (1 file, 181 lines):
- `backend/app/services/logging_service.py` (+181 lines)
  - LoggingService class with singleton pattern
  - Queue-based async-safe logging
  - structlog configuration with JSON renderer
  - get_logging_service() factory function

### Modified (2 files, 15 lines):
- `backend/app/config.py` (+13 lines)
  - Added Path import
  - Added log_dir, log_level, log_rotation_days fields
  - Added log_dir_path property

- `backend/requirements.txt` (+2 lines)
  - structlog>=25.0.0
  - asgi-correlation-id>=4.3.0

## Self-Check: PASSED

**Files verified:**
```bash
$ ls backend/app/services/logging_service.py
FOUND: backend/app/services/logging_service.py
```

**Commits verified:**
```bash
$ git log --oneline | grep -E "bab0633|b40c4d0|37e5fb2"
FOUND: bab0633
FOUND: b40c4d0
FOUND: 37e5fb2
```

All claimed files exist and all commits are in git history. ✅
