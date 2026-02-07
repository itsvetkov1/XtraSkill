# Research Summary: v1.9.5 Pilot Logging Infrastructure

**Project:** BA Assistant - v1.9.5 Logging Milestone
**Domain:** Comprehensive application logging for AI-powered debugging
**Researched:** 2026-02-07
**Confidence:** HIGH

---

## Executive Summary

Adding comprehensive logging to the BA Assistant requires minimal new dependencies (2 Python packages, 1 Flutter package) and integrates cleanly with the existing FastAPI/Flutter architecture. The research identified a 6-phase build order that starts with backend infrastructure (testable independently) and progressively adds frontend integration.

**Key architectural decisions:**
1. **Backend as single source of truth** — Frontend logs are sent to backend for centralized storage
2. **Structured JSON format** — Required for AI-powered log analysis
3. **Correlation IDs via HTTP headers** — Links frontend actions to backend operations
4. **Async-safe logging** — Use QueueHandler pattern to avoid blocking FastAPI event loop
5. **7-day rolling retention** — Balances storage with debugging needs

**Critical pitfalls to avoid:**
- P-01: Blocking async event loop with sync file I/O (use QueueHandler)
- P-04: Exposing sensitive data in logs (implement sanitization layer)
- P-12: Uvicorn logger conflicts (configure before FastAPI app)

---

## Stack Recommendations

### Backend (Python/FastAPI)

| Library | Version | Purpose |
|---------|---------|---------|
| structlog | 25.5.0 | Structured JSON logging with processor chains |
| asgi-correlation-id | 4.3.4 | Request ID propagation middleware |
| stdlib TimedRotatingFileHandler | builtin | 7-day log rotation |

**Why structlog over loguru:** Native JSON output, better FastAPI integration via contextvars, extensible processor chains for enrichment.

### Frontend (Flutter)

| Library | Version | Purpose |
|---------|---------|---------|
| logger | ^2.6.2 | Console logging with levels |
| shared_preferences | existing | Persist toggle state |

**Architecture decision:** Web platform doesn't support file-based logging packages. Use in-memory buffer with backend-centralized storage.

---

## Feature Scope

### Table Stakes (Must Have)

| Feature | Description | Complexity |
|---------|-------------|------------|
| Structured JSON format | All logs output as parseable JSON | Low |
| Log levels (DEBUG/INFO/WARN/ERROR) | Severity classification | Low |
| Correlation ID | Links frontend request to backend response | Medium |
| Settings toggle | Enable/disable from Settings screen | Low |
| 7-day rolling retention | Auto-delete old logs | Medium |
| API download endpoint | GET /api/logs/download | Low |
| User action logging | Navigation, button clicks, form submits | Medium |
| API request/response logging | HTTP calls with status and timing | Medium |
| Error capture | Exceptions with stack traces | Medium |

### Recommended Differentiators

| Feature | Description | Value |
|---------|-------------|-------|
| Session grouping | Group logs by session ID | High |
| Log categories/tags | Filter by area (auth, api, ai) | High |
| AI conversation logging | Token counts, timing, provider | High |
| Network state logging | Connectivity changes | Medium |

### Out of Scope (Anti-Features)

| Feature | Why NOT Build |
|---------|---------------|
| Real-time log streaming | Batch download sufficient for pilot |
| Log analytics dashboard | AI analysis replaces manual dashboards |
| PII auto-redaction | Pilot is controlled; document sensitive fields |
| Cloud log aggregation | File-based sufficient for pilot scale |
| Log viewer UI | File access works for pilot |

---

## Architecture Overview

```
Frontend                           Backend
--------                           -------
LoggingService ─┐
  │             │
  └─> buffer ───┼──> POST /api/logs/ingest ──> LoggingService
                │                                    │
LoggingInterceptor                                   v
  │                                            File storage
  └─> X-Correlation-ID header ──────────────> logs/app.log
                                                     │
Settings toggle ──────────────────────────────>      v
                                              Admin API
                                              /api/logs/download
```

### Correlation ID Flow

1. Frontend generates UUID on app launch (session-level)
2. Dio interceptor attaches `X-Correlation-ID` header to all requests
3. Backend middleware extracts or generates ID
4. All backend logs include correlation ID
5. Download endpoint can filter by correlation ID

---

## Build Order (6 Phases)

### Phase 1: Backend Logging Foundation
- Create LoggingService with structlog
- Add LoggingMiddleware for request/response
- Configure async-safe file handler (QueueHandler)
- Add to config.py: LOG_DIR, LOG_LEVEL, LOG_ROTATION_DAYS

### Phase 2: Backend Admin API
- GET /api/logs (list available files)
- GET /api/logs/download (download log file)
- POST /api/logs/ingest (receive frontend logs)

### Phase 3: Frontend Logging Foundation
- Create LoggingService (singleton, in-memory buffer)
- Create LoggingProvider (toggle with SharedPreferences)
- Generate session correlation ID in main.dart

### Phase 4: Frontend HTTP Integration
- Create LoggingInterceptor for Dio
- Add X-Correlation-ID header to all requests
- Log request/response metadata

### Phase 5: Frontend Settings UI
- Add logging toggle in Settings screen
- Follow existing theme toggle pattern

### Phase 6: Frontend-to-Backend Flush
- Implement flush() to POST buffered logs
- Add lifecycle observer for app pause
- Periodic flush (every 5 min or 100 entries)

---

## Critical Pitfalls

| ID | Pitfall | Prevention |
|----|---------|------------|
| P-01 | Blocking async event loop | Use QueueHandler + QueueListener |
| P-04 | Sensitive data exposure | Implement LogSanitizer with blocklist |
| P-06 | Correlation ID not at entry point | Generate only in middleware, propagate everywhere |
| P-08 | Flutter battery drain | Batch writes every 30s, not per-entry |
| P-12 | Uvicorn logger conflicts | Configure before FastAPI app init |

---

## Log Schema

```json
{
  "timestamp": "2026-02-07T14:30:00.123Z",
  "level": "INFO",
  "category": "api",
  "source": "frontend",
  "correlationId": "abc123-def456",
  "sessionId": "session-789",
  "userId": "user-456",
  "message": "API request completed",
  "data": {
    "endpoint": "/api/projects",
    "method": "GET",
    "statusCode": 200,
    "duration_ms": 145
  }
}
```

---

## Open Questions (Resolved by User Input)

| Question | Resolution |
|----------|------------|
| Log retention | 7 days rolling |
| Toggle location | Settings screen |
| Log transport | Backend-centralized (frontend sends to backend) |
| Access method | Both API endpoint and direct file access |
| Purpose | Pilot debugging with AI analysis |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Disk full | Medium | High | Rotation from day 1 |
| Performance degradation | Low | Medium | Async logging, buffering |
| Sensitive data exposure | Medium | High | Sanitization layer |
| Frontend memory bloat | Low | Medium | Max 1000 entry buffer |

---

## Files

| Research File | Purpose |
|---------------|---------|
| STACK_LOGGING.md | Technology recommendations |
| FEATURES_LOGGING.md | Feature landscape |
| ARCHITECTURE_LOGGING.md | Integration design |
| PITFALLS_LOGGING.md | Risk mitigation |

---

*Research complete: 2026-02-07*
*Ready for requirements: yes*
