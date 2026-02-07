# Pitfalls Research: Logging Infrastructure

**Domain:** Adding comprehensive logging to existing Flutter/FastAPI application
**Researched:** 2026-02-07
**Confidence:** HIGH (verified with official sources and community patterns)

## Summary

Adding toggleable detailed logging to an existing BA Assistant app involves pitfalls across five categories:

1. **Performance** - Blocking async operations, excessive I/O
2. **Security** - PII/secret exposure, log injection vulnerabilities
3. **Storage** - Uncontrolled growth, rotation failures
4. **Correlation** - Broken trace propagation, fragmented debugging
5. **Integration** - Disrupting existing functionality, toggle complexity

The most critical pitfalls are **blocking the FastAPI event loop with synchronous logging** (P-01) and **exposing sensitive data in verbose logs** (P-04). These can cause immediate production issues.

---

## Critical Pitfalls

These cause production failures, security incidents, or require significant rewrites.

| ID | Pitfall | Warning Signs | Prevention | Phase |
|----|---------|---------------|------------|-------|
| P-01 | **Blocking async event loop with logging** | Slow API responses under load, increased latency, timeouts | Use `QueueHandler` + `QueueListener` or `aiologger` for async-safe logging | Backend Infrastructure |
| P-02 | **Logging complete request/response bodies** | Log files growing gigabytes/day, storage alerts, slow log search | Log metadata only (IDs, sizes, status codes); full bodies only at TRACE level with explicit opt-in | Verbosity Design |
| P-03 | **No correlation ID propagation to frontend** | Cannot trace issues across Flutter/FastAPI boundary | Generate correlation ID on first request, pass via headers, include in all logs | Correlation ID Design |
| P-04 | **Exposing sensitive data in logs** | API keys, passwords, PII visible in log files | Implement log sanitization; blocklist sensitive field names; redact patterns | Security Phase |
| P-05 | **Log files filling disk, crashing app** | Disk space alerts, app crashes with "no space" errors | Implement 7-day rotation with size caps from day one; monitor disk usage | Storage & Rotation |

### P-01: Blocking Async Event Loop (CRITICAL)

**What happens:** Standard Python `logging` module with file handlers blocks the asyncio event loop. In FastAPI, this stalls ALL concurrent requests while writing log entries.

**Root cause:** Python's logging module uses synchronous I/O. Even brief disk writes block the single-threaded event loop.

**Consequences:**
- API latency increases 2-10x under load
- Request timeouts during log writes
- Cascading failures in high-throughput scenarios

**Prevention:**
```python
# Use QueueHandler to offload logging to separate thread
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

log_queue = Queue()
queue_handler = QueueHandler(log_queue)
root_logger = logging.getLogger()
root_logger.addHandler(queue_handler)

# File handler runs in background thread
file_handler = logging.handlers.RotatingFileHandler(...)
listener = QueueListener(log_queue, file_handler)
listener.start()
```

**Detection:** Use `aiodebug` package to log callbacks taking >100ms. Any logging-related slow callbacks indicate this issue.

**Source:** [Asyncio Logging Without Blocking](https://superfastpython.com/asyncio-log-blocking/)

---

### P-04: Exposing Sensitive Data in Logs (CRITICAL)

**What happens:** Verbose logging captures API keys, passwords, tokens, PII in plain text.

**OWASP classification:** CWE-532 (Insertion of Sensitive Information into Log File)

**Common sources in BA Assistant context:**
- OAuth tokens in request headers
- User email/name in request bodies
- API keys for LLM providers (Anthropic, Gemini, etc.)
- Document content (may contain confidential business data)

**Prevention:**
```python
SENSITIVE_FIELDS = {'password', 'token', 'api_key', 'secret', 'authorization'}
SENSITIVE_PATTERNS = [
    r'sk-[a-zA-Z0-9]{48}',  # Anthropic API key
    r'Bearer [a-zA-Z0-9\-_.]+',  # OAuth tokens
]

def sanitize_log_data(data: dict) -> dict:
    """Redact sensitive fields before logging."""
    return {
        k: '[REDACTED]' if k.lower() in SENSITIVE_FIELDS else v
        for k, v in data.items()
    }
```

**Source:** [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

---

## Moderate Pitfalls

These cause debugging difficulty, performance degradation, or technical debt.

| ID | Pitfall | Warning Signs | Prevention | Phase |
|----|---------|---------------|------------|-------|
| P-06 | **Correlation ID not generated at entry point** | Each service creates own ID; traces don't connect | Only generate at API gateway/first touch; propagate everywhere else | Correlation ID Design |
| P-07 | **Async context loss for correlation ID** | IDs missing in background tasks, SSE streams | Use `contextvars` instead of thread-local; explicitly pass to async callbacks | Correlation ID Design |
| P-08 | **Flutter logging drains battery (mobile)** | User complaints, app store reviews about battery | Batch log writes; reduce frequency; defer to WiFi/charging | Frontend Logging |
| P-09 | **Toggle state not synced across system** | Backend logs enabled, frontend disabled (or vice versa) | Single source of truth in settings; sync on app start | Settings Toggle |
| P-10 | **Log rotation deletes unanalyzed logs** | Important debug data lost before review | Archive rotated logs to secondary storage before deletion | Storage & Rotation |
| P-11 | **Mixing log formats (JSON vs text)** | Parse errors in log analysis tools | Standardize on structured JSON from start | Verbosity Design |
| P-12 | **Uvicorn logger conflicts** | Duplicate log entries, missing logs, format inconsistencies | Configure Uvicorn logging before FastAPI app; use single handler chain | Backend Infrastructure |

### P-06: Correlation ID Not Generated at Entry Point

**What happens:** Different services generate their own correlation IDs, making cross-service tracing impossible.

**Correct pattern:**
1. First entry point (FastAPI middleware) generates ID if not present
2. All downstream services receive and propagate the same ID
3. Flutter frontend generates ID for user actions, sends in request headers

**Implementation:**
```python
# FastAPI middleware
from contextvars import ContextVar
from uuid import uuid4

correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get('X-Correlation-ID') or str(uuid4())
    correlation_id_var.set(correlation_id)
    response = await call_next(request)
    response.headers['X-Correlation-ID'] = correlation_id
    return response
```

**Source:** [Microsoft Engineering Playbook - Correlation IDs](https://microsoft.github.io/code-with-engineering-playbook/observability/correlation-id/)

---

### P-08: Flutter Logging Drains Battery

**What happens:** Frequent file I/O and network requests for logging drain mobile battery.

**Statistics:** 70% of users uninstall apps that drain battery excessively.

**Prevention strategies:**
1. **Batch writes** - Buffer logs in memory, write every 30 seconds or 100 entries
2. **Defer network** - Only upload logs on WiFi and/or charging
3. **Reduce frequency** - Log entry/exit only, not every step
4. **User control** - Let user disable detailed logging

**Implementation guidance:**
```dart
// Use path_provider for local storage
final directory = await getApplicationDocumentsDirectory();
final logFile = File('${directory.path}/logs/app.log');

// Batch writes with timer
Timer.periodic(Duration(seconds: 30), (_) => _flushLogBuffer());
```

**Source:** [Best Practices for Reducing App Battery Drain](https://www.sidekickinteractive.com/uncategorized/best-practices-for-reducing-app-battery-drain/)

---

### P-12: Uvicorn Logger Conflicts

**What happens:** Uvicorn has its own logging configuration that conflicts with application logging, causing:
- Duplicate log entries
- Missing logs (filtered by Uvicorn)
- Format inconsistencies (Uvicorn format vs app format)

**Prevention:**
```python
# Configure before app creation
import logging

# Disable Uvicorn's default handlers
logging.getLogger("uvicorn").handlers = []
logging.getLogger("uvicorn.access").handlers = []
logging.getLogger("uvicorn.error").handlers = []

# Configure unified handler
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", ...}'
))
logging.getLogger().addHandler(handler)
```

**Source:** [Sharpening Your Code - Logging in FastAPI](https://www.pythonbynight.com/blog/sharpen-your-code)

---

## Minor Pitfalls

These cause inconvenience but are easily fixable.

| ID | Pitfall | Warning Signs | Prevention | Phase |
|----|---------|---------------|------------|-------|
| P-13 | **Using `print()` instead of proper logging** | Can't filter, no levels, no destination control | Audit for `print()` statements; replace with logger calls | Backend Infrastructure |
| P-14 | **Inconsistent timestamp formats** | Hard to correlate logs across frontend/backend | Use ISO 8601 everywhere: `2026-02-07T14:30:00.000Z` | Verbosity Design |
| P-15 | **Log files not in `.gitignore`** | Log files accidentally committed | Add `*.log`, `logs/` to `.gitignore` immediately | Backend Infrastructure |
| P-16 | **No log viewer for users** | Users can't access logs for AI analysis support | Provide export/share mechanism for log files | Frontend Logging |
| P-17 | **Hardcoded log paths** | Cross-platform failures (Windows vs Linux vs mobile) | Use `path_provider` (Flutter), `pathlib` (Python) | Both Infrastructures |
| P-18 | **Logging inside tight loops** | Performance degradation in hot paths | Log aggregated summaries, not individual iterations | Verbosity Design |

### P-13: Using print() Instead of Proper Logging

**Current state in BA Assistant:** Codebase has minimal logging; some areas use `print()` for debugging.

**Problems with print():**
- Output may be truncated
- No filtering or levels
- No structured output
- Cannot redirect to files

**Migration strategy:**
1. Search for `print(` in backend code
2. Replace with `logger.debug()` or appropriate level
3. Configure logger to show debug in dev, info+ in production

---

### P-17: Hardcoded Log Paths

**What fails:**
```python
# Bad: Won't work on Windows, mobile, or different deployments
LOG_PATH = "/var/log/ba_assistant/app.log"
```

**Correct approach:**
```python
# Python (backend)
from pathlib import Path
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_PATH = LOG_DIR / "app.log"
```

```dart
// Flutter (frontend)
import 'package:path_provider/path_provider.dart';
final directory = await getApplicationDocumentsDirectory();
final logPath = '${directory.path}/logs/app.log';
```

---

## Security Considerations

### What NOT to Log

Based on OWASP guidelines, never log:

| Category | Examples | Risk |
|----------|----------|------|
| Credentials | Passwords, API keys, secrets | Credential theft |
| PII | Email, phone, SSN, address | Privacy violation, GDPR |
| Financial | Credit card numbers, bank accounts | Financial fraud |
| Health | Medical records, conditions | HIPAA violation |
| Session data | Session IDs, tokens (if compromised) | Session hijacking |

### BA Assistant Specific Concerns

Given the application context:

1. **Document content** - May contain confidential business data
2. **LLM API keys** - Anthropic, Gemini, DeepSeek credentials
3. **OAuth tokens** - Google authentication tokens
4. **User queries** - May contain sensitive business information
5. **Generated artifacts** - BRDs may have confidential requirements

### Sanitization Implementation

```python
import re
from typing import Any, Dict

class LogSanitizer:
    REDACT_FIELDS = {
        'password', 'secret', 'token', 'api_key', 'apikey',
        'authorization', 'cookie', 'session', 'credential'
    }

    REDACT_PATTERNS = [
        (r'sk-[a-zA-Z0-9]{20,}', '[ANTHROPIC_KEY]'),
        (r'AIza[a-zA-Z0-9_-]{35}', '[GOOGLE_KEY]'),
        (r'Bearer [a-zA-Z0-9\-_\.]+', 'Bearer [REDACTED]'),
    ]

    @classmethod
    def sanitize(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in data.items():
            if key.lower() in cls.REDACT_FIELDS:
                result[key] = '[REDACTED]'
            elif isinstance(value, str):
                sanitized = value
                for pattern, replacement in cls.REDACT_PATTERNS:
                    sanitized = re.sub(pattern, replacement, sanitized)
                result[key] = sanitized
            elif isinstance(value, dict):
                result[key] = cls.sanitize(value)
            else:
                result[key] = value
        return result
```

---

## Performance Considerations

### Backend (FastAPI) Performance

| Concern | Impact | Mitigation |
|---------|--------|------------|
| Sync file I/O | Blocks event loop, 2-10x latency | Use QueueHandler pattern |
| Large log entries | Memory pressure, slow writes | Cap entry size at 10KB |
| High log volume | Disk I/O saturation | Sampling at high traffic |
| Log formatting | CPU overhead | Pre-compute format strings |

**Benchmark guidance:** With QueueHandler, logging overhead should be <1ms per request.

### Frontend (Flutter) Performance

| Concern | Impact | Mitigation |
|---------|--------|------------|
| Frequent file writes | Battery drain, I/O blocking | Batch writes (30s intervals) |
| Network uploads | Data usage, battery | WiFi-only, background sync |
| Memory buffering | OOM on low-end devices | Cap buffer at 1000 entries |
| Compute for formatting | Frame drops | Format on background isolate |

**Battery guidance:** Detailed logging enabled should increase battery drain by <5%.

### SSE Stream Logging

Special consideration for conversation streaming:

```python
# Don't log every SSE event
async def stream_response():
    event_count = 0
    for event in stream:
        event_count += 1
        yield event
    # Log summary only
    logger.info(f"Stream complete: {event_count} events")
```

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Backend Infrastructure | P-01, P-12, P-13 | Configure async logging first, before adding log statements |
| Frontend Infrastructure | P-08, P-17 | Design batching strategy upfront; use path_provider |
| Correlation IDs | P-03, P-06, P-07 | Design propagation across entire request lifecycle |
| Verbosity Design | P-02, P-11, P-14, P-18 | Define log levels and formats as specification before coding |
| Settings Toggle | P-09 | Plan sync mechanism before implementing toggle |
| Storage & Rotation | P-05, P-10 | Implement rotation from day one, not as afterthought |
| Security | P-04 | Build sanitization into logging infrastructure, not as middleware |

---

## Integration Warnings for Existing BA Assistant

### Current State Analysis

From codebase review, current logging is minimal:
- `agent_service.py`: Uses `logging.getLogger(__name__)` for errors/info
- `brd_generator.py`: Logs validation warnings
- `skill_loader.py`: Logs skill loading info
- `conversations.py`: Ad-hoc logging in exception handler

### Integration Risks

1. **Existing `logging.getLogger()` calls** - Need to ensure new configuration doesn't break existing log output
2. **Async service methods** - `agent_service.py` has async streaming; logging here must not block
3. **No current correlation** - Retrofitting correlation IDs requires touching all route handlers
4. **SSE streaming** - Conversation streaming needs special handling to avoid per-event logging

### Recommended Integration Order

1. **Configure root logger** with async-safe handler (before touching anything else)
2. **Add correlation middleware** as first middleware
3. **Update existing logging calls** to include correlation context
4. **Add new logging** to components without logging
5. **Implement toggle** after infrastructure is stable

---

## Sources

### Official Documentation
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Flutter path_provider Documentation](https://pub.dev/packages/path_provider)

### Security
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [OWASP Mobile - Inadequate Privacy Controls](https://owasp.org/www-project-mobile-top-10/2023-risks/m6-inadequate-privacy-controls)

### Performance & Best Practices
- [Asyncio Logging Best Practices](https://superfastpython.com/asyncio-logging-best-practices/)
- [FastAPI Logging with Better Stack](https://betterstack.com/community/guides/logging/logging-with-fastapi/)
- [Log Rotation Best Practices](https://edgedelta.com/company/knowledge-center/what-is-log-rotation)

### Correlation & Tracing
- [Microsoft Engineering Playbook - Correlation IDs](https://microsoft.github.io/code-with-engineering-playbook/observability/correlation-id/)
- [Distributed Tracing Logs Best Practices](https://www.groundcover.com/learn/logging/distributed-tracing-logs)

### Mobile Performance
- [Battery Consumption Best Practices](https://www.sidekickinteractive.com/uncategorized/best-practices-for-reducing-app-battery-drain/)
- [Flutter File Storage Best Practices](https://medium.com/pubdev-essentials/master-file-storage-in-flutter-with-path-provider-simplify-local-file-access-the-smart-way-fc28ff226201)
