# Features Research: Logging Infrastructure

**Domain:** Pilot Application Logging with AI Analysis
**Researched:** 2026-02-07
**Overall Confidence:** HIGH

---

## Summary

This research identifies features for comprehensive application logging in BA Assistant, designed for pilot debugging with AI-powered analysis capability. The feature set is scoped for a pilot/MVP context - focused on debugging and operational insight rather than enterprise compliance or massive scale.

**Key Recommendations:**
1. Structured JSON logging is essential for AI analysis
2. Correlation IDs must span frontend-to-backend for request tracing
3. 7-day rolling retention balances storage with debugging needs
4. Toggle in Settings enables user control over log verbosity
5. Log schema should be AI-friendly with consistent fields

---

## Table Stakes

Features users expect for a functional logging system. Missing = logging infrastructure feels incomplete.

| Feature | Description | Complexity | Notes |
|---------|-------------|------------|-------|
| **Structured JSON Format** | All logs output as JSON with consistent schema | Low | Essential for AI parsing per [SigNoz best practices](https://signoz.io/blog/structured-logs/) |
| **Log Levels** | INFO, WARN, ERROR, DEBUG severity classification | Low | Standard pattern; filter by level for analysis |
| **Timestamps** | ISO 8601 timestamps on all entries | Low | Required for timeline reconstruction |
| **Correlation ID** | Unique ID linking frontend request to backend response | Medium | Per [W3C Trace Context](https://www.w3.org/TR/trace-context/), use `X-Correlation-ID` header |
| **Settings Toggle** | Enable/disable detailed logging from Settings screen | Low | User control; integrates with existing settings pattern |
| **7-Day Rolling Retention** | Auto-delete logs older than 7 days | Medium | Prevents unbounded growth; common for pilot/standard tier |
| **API Download Endpoint** | `GET /api/logs/download` returns logs as JSON file | Low | Enables analysis by external tools or AI |
| **Direct File Access** | Logs stored in accessible SQLite DB | Low | Allows direct file copy for offline analysis |
| **User Action Logging** | Log user interactions (navigation, button clicks, form submits) | Medium | Essential for reproducing issues |
| **API Request/Response Logging** | Log all HTTP requests with status codes and timing | Medium | Backend: use FastAPI middleware |
| **Error Capture** | Automatic capture of exceptions with stack traces | Medium | Frontend: Flutter error handlers; Backend: exception middleware |

### Rationale for Table Stakes

These features are table stakes because:
- **Structured JSON**: AI models cannot reliably parse unstructured text logs
- **Correlation IDs**: Without these, cannot connect "user clicked X" to "backend threw error Y"
- **Settings Toggle**: User should control whether their actions are logged in detail
- **7-Day Retention**: Per [LogicMonitor retention guide](https://www.logicmonitor.com/blog/what-is-log-retention), 7 days is standard for troubleshooting tier
- **Download/Access**: User requirement - AI needs access to logs for analysis

---

## Differentiators

Features that add value beyond baseline functionality. Nice to have, not blocking for pilot.

| Feature | Description | Complexity | Value Proposition |
|---------|-------------|------------|-------------------|
| **Session Grouping** | Group logs by user session with session ID | Low | Easier to isolate single user's journey |
| **AI Conversation Logging** | Detailed logging of AI prompts, tokens, timing | Medium | Debug AI behavior, token optimization |
| **Performance Metrics** | Response times, render durations, memory usage | Medium | Identify performance bottlenecks |
| **Log Categories/Tags** | Categorize logs (auth, navigation, api, ai, error) | Low | Filter by area for focused analysis |
| **Log Viewer UI** | In-app screen to view recent logs | High | Convenient but not essential - file access works |
| **Search/Filter API** | Query logs by time range, level, category | Medium | Useful for large log volumes |
| **Automatic Error Context** | Capture surrounding logs when error occurs | Medium | Reduces manual context gathering |
| **Network State Logging** | Log connectivity changes, timeouts | Low | Diagnose network-related issues |
| **State Snapshot on Error** | Capture provider state when errors occur | Medium | Faster debugging without reproduction |

### Recommended Differentiators for Pilot

Prioritize these differentiators (low effort, high value):
1. **Session Grouping** - Nearly free to implement, high debugging value
2. **Log Categories/Tags** - Simple field addition, major filtering benefit
3. **AI Conversation Logging** - High value for debugging the core feature
4. **Network State Logging** - Low effort, catches common issues

Defer these (high effort or low pilot value):
- **Log Viewer UI** - File access is sufficient for pilot
- **Search/Filter API** - Download and analyze externally for now

---

## Anti-Features (Out of Scope)

Features to deliberately NOT build for pilot. Common mistakes or over-engineering.

| Anti-Feature | Why NOT Build |
|--------------|---------------|
| **Real-time Log Streaming** | Adds WebSocket complexity; batch download is sufficient for pilot debugging |
| **Log Analytics Dashboard** | Enterprise feature; AI analysis replaces manual dashboards |
| **PII Auto-Redaction** | Pilot is internal/controlled; adds complexity. Document sensitive fields instead |
| **Multi-User Log Separation** | Single-user pilot; logs are per-device already |
| **Cloud Log Aggregation** | External service (Datadog, ELK) overkill for pilot; SQLite file is sufficient |
| **Log Compression** | 7-day retention on JSON logs unlikely to exceed 10MB; premature optimization |
| **Log Encryption at Rest** | Pilot is local development; adds key management complexity |
| **Compliance Formatting** | No SOC2/HIPAA requirements for internal pilot |
| **Alert Rules** | No need for automated alerting; human reviews logs with AI assistance |
| **Distributed Tracing (full)** | OpenTelemetry/Jaeger overkill; simple correlation ID sufficient |
| **Log Level Hot-Reloading** | Restart acceptable for pilot; adds complexity |

### Pilot Philosophy

The logging system is for **debugging with AI assistance**, not enterprise observability. Build the minimum that enables:
1. User reports issue
2. Developer gets logs from that session
3. AI analyzes logs and identifies root cause
4. Developer fixes issue

---

## Log Event Categories

What to log in frontend (Flutter) and backend (FastAPI).

### Frontend Events

| Category | Events to Log | Example Fields |
|----------|---------------|----------------|
| **Navigation** | Screen views, route changes, back navigation | `route`, `previousRoute`, `params` |
| **User Actions** | Button clicks, form submits, gestures | `action`, `target`, `value` |
| **Auth** | Login attempts, logout, token refresh | `provider`, `success`, `error` |
| **API Calls** | Request sent, response received | `endpoint`, `method`, `statusCode`, `duration_ms` |
| **State Changes** | Provider state transitions | `provider`, `oldState`, `newState` |
| **Errors** | Unhandled exceptions, caught errors | `error`, `stackTrace`, `context` |
| **AI Interactions** | Message sent, streaming started/ended | `threadId`, `messageLength`, `responseTime` |
| **Document Operations** | Upload, view, delete | `documentId`, `action`, `size` |

### Backend Events

| Category | Events to Log | Example Fields |
|----------|---------------|----------------|
| **HTTP Request** | All incoming requests | `method`, `path`, `correlationId`, `userId` |
| **HTTP Response** | All outgoing responses | `statusCode`, `duration_ms`, `correlationId` |
| **Auth** | Token validation, OAuth callbacks | `userId`, `provider`, `success` |
| **Database** | CRUD operations, query timing | `table`, `operation`, `duration_ms` |
| **AI Service** | Provider calls, token counts | `provider`, `model`, `inputTokens`, `outputTokens`, `duration_ms` |
| **Document** | Upload processing, parsing | `documentId`, `size`, `type`, `parseTime_ms` |
| **Errors** | Exceptions, validation failures | `error`, `stackTrace`, `requestData` |
| **SSE Streaming** | Stream start/end, chunks sent | `streamId`, `chunkCount`, `totalDuration_ms` |

---

## Log Schema

Recommended JSON structure for AI analysis. Consistent schema enables pattern recognition.

### Base Log Entry

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

### Required Fields (All Entries)

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO 8601 string | When event occurred |
| `level` | enum | DEBUG, INFO, WARN, ERROR |
| `category` | string | Event category (navigation, api, auth, ai, error) |
| `source` | enum | "frontend" or "backend" |
| `correlationId` | UUID string | Links frontend/backend for same request |
| `message` | string | Human-readable description |

### Optional Fields (When Available)

| Field | Type | Description |
|-------|------|-------------|
| `sessionId` | string | Groups logs by user session |
| `userId` | string | User identifier (if authenticated) |
| `data` | object | Event-specific structured data |
| `error` | object | Error details if level=ERROR |
| `stackTrace` | string | Stack trace for errors |
| `duration_ms` | number | Timing for operations |

### Error Entry Schema

```json
{
  "timestamp": "2026-02-07T14:30:00.123Z",
  "level": "ERROR",
  "category": "api",
  "source": "frontend",
  "correlationId": "abc123-def456",
  "sessionId": "session-789",
  "userId": "user-456",
  "message": "API request failed",
  "data": {
    "endpoint": "/api/projects",
    "method": "POST",
    "requestBody": {"name": "Test Project"}
  },
  "error": {
    "type": "DioException",
    "message": "Connection timeout",
    "code": "TIMEOUT"
  },
  "stackTrace": "at ApiService.post (api_service.dart:45)\n..."
}
```

### AI Conversation Entry Schema

```json
{
  "timestamp": "2026-02-07T14:30:00.123Z",
  "level": "INFO",
  "category": "ai",
  "source": "backend",
  "correlationId": "abc123-def456",
  "sessionId": "session-789",
  "userId": "user-456",
  "message": "AI response generated",
  "data": {
    "threadId": "thread-123",
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "inputTokens": 1250,
    "outputTokens": 890,
    "duration_ms": 3450,
    "streaming": true,
    "artifactGenerated": true
  }
}
```

---

## Feature Dependencies

How features depend on existing app capabilities and each other.

```
Settings Toggle
    |-- Requires: Existing Settings screen (DONE - settings_screen.dart)
    |-- Requires: Logging service (NEW)
    +-- Requires: Shared preferences for persistence (DONE - theme uses this)

Correlation ID
    |-- Frontend: Dio interceptor to add header (integrates with existing Dio usage)
    +-- Backend: FastAPI middleware to extract/generate (integrates with existing middleware stack)

Log Storage (Backend)
    |-- Requires: SQLite table for logs (new table in existing DB)
    +-- Requires: Retention cleanup job (new background task)

Log Storage (Frontend)
    |-- Option A: Local SQLite (requires sqflite package)
    +-- Option B: Send to backend (simpler, uses existing API pattern) <-- RECOMMENDED

API Download
    |-- Requires: Log storage backend
    +-- Requires: Auth middleware (DONE)

AI Conversation Logging
    |-- Requires: Integration with existing ai_service.py
    +-- Requires: Log storage backend
```

### Recommended Approach

**Frontend logs sent to backend** (not stored locally):
- Simpler architecture - one log store
- Backend already has SQLite
- Download endpoint serves all logs
- Correlation IDs already link everything

**Backend is single source of truth for logs:**
- 7-day retention implemented once
- Single download endpoint
- AI analyzes unified log stream

---

## Integration Points with Existing Code

Based on codebase analysis, here are the key integration points:

### Frontend (Flutter)

| File | Integration |
|------|-------------|
| `settings_screen.dart` | Add logging toggle in new "Diagnostics" section |
| `auth_service.dart` | Uses Dio - add interceptor for correlation ID |
| `project_service.dart` | Uses Dio - logging interceptor applies |
| All providers | Add state change logging calls |

### Backend (FastAPI)

| File | Integration |
|------|-------------|
| `main.py` | Add logging middleware after CORS middleware |
| `auth.py` route | Log authentication events |
| `conversations.py` route | Log AI interactions |
| `ai_service.py` | Log token usage, provider calls |
| New: `logging_service.py` | Logging business logic |
| New: `logging_routes.py` | Download endpoint |

---

## MVP Feature Recommendation

For the pilot logging milestone, prioritize in this order:

### Phase 1: Core Infrastructure
1. Structured JSON log format (both ends)
2. Backend log storage (SQLite table)
3. Correlation ID middleware (FastAPI)
4. Correlation ID interceptor (Dio)
5. 7-day retention cleanup

### Phase 2: Frontend Integration
6. Settings toggle for detailed logging
7. Frontend logging service
8. User action logging
9. API request/response logging
10. Error capture

### Phase 3: Backend Logging
11. HTTP request/response middleware
12. AI service logging
13. Error middleware

### Phase 4: Access and Retrieval
14. Download endpoint
15. Direct file access documentation

### Defer to Post-Pilot
- Log viewer UI
- Search/filter API
- Performance metrics
- State snapshots

---

## Sources

### Structured Logging Best Practices
- [SigNoz - Structured Logging Guide](https://signoz.io/blog/structured-logs/) - HIGH confidence
- [Better Stack - Logging Best Practices](https://betterstack.com/community/guides/logging/logging-best-practices/) - HIGH confidence
- [Honeycomb - Engineer's Checklist](https://www.honeycomb.io/blog/engineers-checklist-logging-best-practices) - MEDIUM confidence

### Flutter Logging
- [LogRocket - Flutter Logging Best Practices](https://blog.logrocket.com/flutter-logging-best-practices/) - MEDIUM confidence
- [Flutter DevTools - Logging View](https://docs.flutter.dev/tools/devtools/logging) - HIGH confidence

### FastAPI Logging
- [asgi-correlation-id GitHub](https://github.com/snok/asgi-correlation-id) - HIGH confidence
- [Structlog Integration Guide](https://ouassim.tech/notes/setting-up-structured-logging-in-fastapi-with-structlog/) - MEDIUM confidence

### Correlation IDs
- [W3C Trace Context Spec](https://www.w3.org/TR/trace-context/) - HIGH confidence
- [OpenTelemetry Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/) - HIGH confidence

### Log Retention
- [LogicMonitor - Log Retention Overview](https://www.logicmonitor.com/blog/what-is-log-retention) - MEDIUM confidence
- [Groundcover - Log Retention Policies](https://www.groundcover.com/learn/logging/log-retention-policies) - MEDIUM confidence

### AI Log Analysis
- [IBM - AI for Log Analysis](https://www.ibm.com/think/topics/ai-for-log-analysis) - MEDIUM confidence
- [Salesforce LogAI](https://github.com/salesforce/logai) - MEDIUM confidence

---

*Research completed 2026-02-07. Ready for requirements definition.*
