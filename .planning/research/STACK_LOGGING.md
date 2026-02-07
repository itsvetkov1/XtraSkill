# Stack Research: Logging Infrastructure

**Project:** BA Assistant Pilot Logging
**Researched:** 2026-02-07
**Overall Confidence:** HIGH

---

## Summary

For adding comprehensive structured logging to the existing BA Assistant stack, I recommend **structlog** (backend) and **logger** package (frontend) with custom file output. These are lightweight, well-maintained options that integrate cleanly with FastAPI/Flutter without over-engineering. Both support structured JSON output, which enables future AI-powered log analysis.

Key insight: The frontend targets web primarily, where file-based logging packages like `flutter_logs` don't work. Instead, use in-memory log collection with export capability, stored via `shared_preferences` or sent to backend.

---

## Backend (Python/FastAPI)

### Recommended

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| **structlog** | 25.5.0 | Core structured logging | Industry standard for FastAPI; JSON output; processor chains for enrichment; contextvars for request correlation; works with Python's built-in logging |
| **asgi-correlation-id** | 4.3.4 | Request ID propagation | Lightweight middleware; generates/propagates correlation IDs; integrates directly with structlog contextvars |
| Python stdlib `logging.handlers.TimedRotatingFileHandler` | (builtin) | Log file rotation | 7-day rolling retention with `backupCount=7`; no extra dependency; battle-tested |

### Installation

```bash
pip install structlog==25.5.0 asgi-correlation-id==4.3.4
```

Add to `requirements.txt`:
```
structlog==25.5.0
asgi-correlation-id==4.3.4
```

### Why structlog over loguru

| Criterion | structlog | loguru |
|-----------|-----------|--------|
| JSON output | Native, first-class | Requires custom config |
| FastAPI integration | Excellent (contextvars) | Good but less mature |
| Processor chains | Yes - extensible | Limited |
| Observability tools | Direct ELK/Datadog support | Possible but manual |
| Learning curve | Moderate | Low |
| Recommendation | **Use for production structured logging** | Better for simple scripts |

For pilot debugging with potential AI analysis, structlog's native JSON and processor architecture is the better fit. Loguru's simplicity is less valuable when we need structured, queryable logs.

### Considered but Rejected

| Library | Reason |
|---------|--------|
| **loguru** | Simpler but less native JSON support; structlog's processor chains better for enrichment |
| **python-json-logger** | Only a formatter; structlog is more complete |
| **fastapi-structlog** | Adds complexity; raw structlog + asgi-correlation-id is sufficient |
| **Sentry/Datadog SDK** | Overkill for pilot phase; adds external dependency |

---

## Frontend (Flutter)

### Recommended

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| **logger** | ^2.6.2 | Console logging with levels | 1.75M downloads; simple API; customizable output; works on all platforms |
| Custom `LogStorage` service | N/A | In-memory log buffer with persistence | Web doesn't support file I/O; use shared_preferences for persistence between sessions |
| **shared_preferences** | (already installed: ^2.5.4) | Persist log settings + buffer | Already in project; cross-platform; stores toggle state and recent logs |

### Installation

Add to `pubspec.yaml`:
```yaml
dependencies:
  logger: ^2.6.2
```

### Why Not File-Based Logging

| Package | Issue |
|---------|-------|
| **flutter_logs** | Android/iOS only - **does not support web** |
| **flog** | Requires SQLite, adds complexity |
| **logd** | Good but newer, less adoption (use logger for maturity) |

Since BA Assistant targets web (and mobile), file-based logging packages won't work. Instead:
1. Log to console via `logger` package
2. Buffer logs in memory (circular buffer, ~1000 entries)
3. Persist buffer to `shared_preferences` on toggle-off or periodic flush
4. Export logs via API call to backend (backend stores/rotates files)

This approach keeps frontend simple and centralizes log storage on backend.

### Architecture Note

For detailed logging toggle:
- When enabled: Frontend buffers logs locally + sends batches to backend
- When disabled: Minimal logging (errors only)
- Export: User triggers download from backend (backend has authoritative logs)

### Considered but Rejected

| Library | Reason |
|---------|--------|
| **talker_flutter** | Feature-rich but overkill; includes UI overlays we don't need |
| **flutter_logs** | No web support - critical limitation |
| **auto_logger** | Automatic capture is too aggressive for toggleable pilot logging |
| **cr_logger** | Good but talker is more popular; neither needed for our scope |

---

## Integration Points

### Backend Integration

```
Existing Stack              +  New Logging
----------------------         ----------------------
FastAPI app                 -> CorrelationIdMiddleware (first)
                            -> Custom LoggingMiddleware (adds structlog context)
Routes/Services             -> structlog.get_logger() calls
AI streaming (SSE)          -> Correlation ID in stream events
Database (SQLAlchemy)       -> Optional: bind db queries to request context
```

**Middleware order matters:**
1. `CorrelationIdMiddleware` (generates/extracts request ID)
2. Custom `StructlogMiddleware` (binds ID + request details to context)
3. Existing middleware (auth, etc.)

### Frontend Integration

```
Existing Stack              +  New Logging
----------------------         ----------------------
Provider state             -> LogService (new provider)
Dio HTTP client            -> Interceptor adds correlation ID to requests
                           -> Interceptor logs request/response
Navigation (go_router)     -> RouteObserver logs navigation
Error handling             -> FlutterError.onError captures errors
UI actions                 -> Manual log calls in critical flows
```

### Correlation ID Flow

```
Frontend                    Backend
--------                    -------
Generate UUID           ->  X-Correlation-ID header
Log with correlation_id     Extract from header
                            Bind to structlog context
                            All logs include correlation_id
Export request          <-  Return logs filtered by correlation_id
```

---

## Configuration Decisions

### 1. Log Levels

| Level | Backend Use | Frontend Use |
|-------|-------------|--------------|
| DEBUG | Detailed flow, variable values | Never in production |
| INFO | API requests, AI calls, key actions | User actions, navigation |
| WARNING | Degraded state, retries | Rate limits, slow responses |
| ERROR | Exceptions, failures | API errors, crashes |

**Pilot mode:** DEBUG enabled
**Normal mode:** INFO and above

### 2. Log Format (JSON)

```json
{
  "timestamp": "2026-02-07T14:30:00.000Z",
  "level": "INFO",
  "correlation_id": "abc-123-def",
  "event": "ai_request_started",
  "user_id": "user_456",
  "project_id": "proj_789",
  "model": "claude-sonnet-4-20250514",
  "tokens_estimated": 1500
}
```

### 3. File Rotation (Backend)

```python
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    filename="logs/ba_assistant.log",
    when="midnight",
    interval=1,
    backupCount=7,  # Keep 7 days
    encoding="utf-8"
)
handler.suffix = "%Y-%m-%d"  # Produces: ba_assistant.log.2026-02-07
```

### 4. Storage Location

| Platform | Log Storage |
|----------|-------------|
| Backend | `./logs/` directory (gitignored) |
| Frontend Web | In-memory buffer -> backend API |
| Frontend Mobile | Application documents directory (if needed later) |

### 5. Toggle Implementation

| Component | Toggle Mechanism |
|-----------|------------------|
| Backend | Environment variable `DETAILED_LOGGING=true/false` read at startup; also runtime API endpoint for pilot users |
| Frontend | `SharedPreferences` key `detailed_logging_enabled`; Provider exposes toggle |

---

## What NOT to Add

| Technology | Why Not |
|------------|---------|
| ELK Stack / Datadog | Overkill for pilot; adds infrastructure complexity |
| Sentry | Good for errors but adds external dependency; use for v2 if needed |
| Database logging | SQLite is already busy; file-based is simpler for pilot |
| Real-time log streaming | Nice-to-have but not MVP; batch export is sufficient |
| Log aggregation service | Adds operational burden; local files are fine for pilot |

---

## Implementation Complexity

| Component | Effort | Risk |
|-----------|--------|------|
| Backend structlog setup | Low | Low - well-documented pattern |
| Correlation ID middleware | Low | Low - asgi-correlation-id handles it |
| File rotation | Low | Low - stdlib handler |
| Frontend logger setup | Low | Low - simple package |
| Frontend log buffer | Medium | Low - in-memory circular buffer |
| Log export API | Medium | Low - straightforward file read |
| Toggle UI | Low | Low - already have settings pattern |

**Total estimated effort:** 2-3 phases of focused work

---

## Sources

### Backend
- [structlog on PyPI](https://pypi.org/project/structlog/) - Version 25.5.0 (Oct 2025)
- [asgi-correlation-id on GitHub](https://github.com/snok/asgi-correlation-id) - Version 4.3.4
- [FastAPI + structlog integration guide](https://wazaari.dev/blog/fastapi-structlog-integration)
- [Python logging.handlers documentation](https://docs.python.org/3/library/logging.handlers.html)
- [structlog guide on SigNoz](https://signoz.io/guides/structlog/)

### Frontend
- [logger on pub.dev](https://pub.dev/packages/logger) - Version 2.6.2 (Oct 2025)
- [Flutter logging best practices - LogRocket](https://blog.logrocket.com/flutter-logging-best-practices/)
- [flutter_logs on pub.dev](https://pub.dev/packages/flutter_logs) - Android/iOS only, no web support

### Comparisons
- [Python logging libraries comparison - Better Stack](https://betterstack.com/community/guides/logging/best-python-logging-libraries/)
- [structlog vs loguru - piptrends](https://piptrends.com/compare/structlog-vs-loguru-vs-python-json-logger)
- [Flutter logging libraries 2025-2026 - Medium](https://medium.com/@yash22202/most-popular-flutter-logging-libraries-2025-2026-6394a0b13c29)
