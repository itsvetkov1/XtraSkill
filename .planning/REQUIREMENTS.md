# Requirements: BA Assistant v1.9.5

**Defined:** 2026-02-07
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v1.9.5 Requirements

Requirements for Pilot Logging Infrastructure milestone.

### Core Infrastructure

- [x] **LOG-01**: All log entries use structured JSON format with consistent schema
- [x] **LOG-02**: Log entries include severity level (DEBUG, INFO, WARN, ERROR)
- [x] **LOG-03**: Log entries include ISO 8601 timestamps
- [x] **LOG-04**: Correlation ID links frontend requests to backend operations via X-Correlation-ID header
- [x] **LOG-05**: User can toggle detailed logging on/off from Settings screen
- [x] **LOG-06**: Logs are retained for 7 days with automatic rotation/deletion
- [x] **LOG-07**: Admin can download logs via authenticated API endpoint
- [x] **LOG-08**: Logs are stored in accessible files for direct analysis

### Frontend Logging

- [x] **FLOG-01**: User navigation events are logged (screen views, route changes)
- [x] **FLOG-02**: User actions are logged (button clicks, form submits)
- [x] **FLOG-03**: API requests/responses are logged via Dio interceptor (endpoint, method, status, duration)
- [x] **FLOG-04**: Errors are captured with exception type and stack trace
- [x] **FLOG-05**: All frontend logs include session ID for grouping
- [x] **FLOG-06**: Logs include category tags (auth, api, ai, navigation, error)
- [x] **FLOG-07**: Network state changes are logged (connectivity, timeouts)
- [x] **FLOG-08**: Frontend logs are sent to backend for centralized storage

### Backend Logging

- [x] **BLOG-01**: HTTP requests are logged via middleware (method, path, correlation ID, user ID)
- [x] **BLOG-02**: HTTP responses are logged (status code, duration)
- [x] **BLOG-03**: AI service calls are logged (provider, model, input/output tokens, duration)
- [x] **BLOG-04**: Errors are captured with exception type, stack trace, and request context
- [x] **BLOG-05**: Database operations are logged (table, operation, duration)
- [x] **BLOG-06**: SSE streaming summaries are logged (event count, total duration)
- [x] **BLOG-07**: Logging uses async-safe pattern (QueueHandler) to avoid blocking event loop
- [x] **BLOG-08**: Sensitive data is sanitized before logging (tokens, API keys, PII fields)

### Settings & Configuration

- [x] **SLOG-01**: Logging toggle state persists across app restarts
- [x] **SLOG-02**: Backend logging level is configurable via environment variable
- [x] **SLOG-03**: Log directory path is configurable via environment variable
- [x] **SLOG-04**: Frontend buffer size is configurable (default: 1000 entries)
- [x] **SLOG-05**: Frontend flush interval is configurable (default: 5 minutes)

## Future Requirements

Deferred to later milestones.

### Log Analysis (v2.0+)

- **ANAL-01**: Search/filter logs by time range, level, category via API
- **ANAL-02**: In-app log viewer UI for administrators
- **ANAL-03**: Log export in multiple formats (JSON, CSV)
- **ANAL-04**: Performance metrics dashboard

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time log streaming | Batch download sufficient for pilot debugging |
| Log analytics dashboard | AI analysis replaces manual dashboards |
| PII auto-redaction | Pilot is internal/controlled; field blocklist is sufficient |
| Cloud log aggregation | Local file storage sufficient for pilot scale |
| Log viewer UI | Direct file access works for pilot |
| Log compression | 7-day retention unlikely to exceed 10MB |
| Log encryption at rest | Pilot is development; adds key management complexity |
| Distributed tracing (OpenTelemetry) | Simple correlation ID sufficient |
| Alert rules | No automated alerting needed; human reviews with AI |

## Traceability

Which phases cover which requirements.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LOG-01 | Phase 43 | Complete |
| LOG-02 | Phase 43 | Complete |
| LOG-03 | Phase 43 | Complete |
| LOG-04 | Phase 43 | Complete |
| LOG-05 | Phase 47 | Complete |
| LOG-06 | Phase 43 | Complete |
| LOG-07 | Phase 44 | Complete |
| LOG-08 | Phase 43 | Complete |
| FLOG-01 | Phase 45 | Complete |
| FLOG-02 | Phase 45 | Complete |
| FLOG-03 | Phase 46 | Complete |
| FLOG-04 | Phase 45 | Complete |
| FLOG-05 | Phase 45 | Complete |
| FLOG-06 | Phase 45 | Complete |
| FLOG-07 | Phase 45 | Complete |
| FLOG-08 | Phase 48 | Complete |
| BLOG-01 | Phase 43 | Complete |
| BLOG-02 | Phase 43 | Complete |
| BLOG-03 | Phase 43 | Complete |
| BLOG-04 | Phase 43 | Complete |
| BLOG-05 | Phase 43 | Complete |
| BLOG-06 | Phase 43 | Complete |
| BLOG-07 | Phase 43 | Complete |
| BLOG-08 | Phase 43 | Complete |
| SLOG-01 | Phase 47 | Complete |
| SLOG-02 | Phase 43 | Complete |
| SLOG-03 | Phase 43 | Complete |
| SLOG-04 | Phase 45 | Complete |
| SLOG-05 | Phase 48 | Complete |

**Coverage:**
- v1.9.5 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0

---
*Requirements defined: 2026-02-07*
*Roadmap created: 2026-02-07*
