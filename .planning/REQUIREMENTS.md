# Requirements: BA Assistant v1.9.5

**Defined:** 2026-02-07
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v1.9.5 Requirements

Requirements for Pilot Logging Infrastructure milestone.

### Core Infrastructure

- [ ] **LOG-01**: All log entries use structured JSON format with consistent schema
- [ ] **LOG-02**: Log entries include severity level (DEBUG, INFO, WARN, ERROR)
- [ ] **LOG-03**: Log entries include ISO 8601 timestamps
- [ ] **LOG-04**: Correlation ID links frontend requests to backend operations via X-Correlation-ID header
- [ ] **LOG-05**: User can toggle detailed logging on/off from Settings screen
- [ ] **LOG-06**: Logs are retained for 7 days with automatic rotation/deletion
- [ ] **LOG-07**: Admin can download logs via authenticated API endpoint
- [ ] **LOG-08**: Logs are stored in accessible files for direct analysis

### Frontend Logging

- [ ] **FLOG-01**: User navigation events are logged (screen views, route changes)
- [ ] **FLOG-02**: User actions are logged (button clicks, form submits)
- [x] **FLOG-03**: API requests/responses are logged via Dio interceptor (endpoint, method, status, duration)
- [ ] **FLOG-04**: Errors are captured with exception type and stack trace
- [ ] **FLOG-05**: All frontend logs include session ID for grouping
- [ ] **FLOG-06**: Logs include category tags (auth, api, ai, navigation, error)
- [ ] **FLOG-07**: Network state changes are logged (connectivity, timeouts)
- [ ] **FLOG-08**: Frontend logs are sent to backend for centralized storage

### Backend Logging

- [ ] **BLOG-01**: HTTP requests are logged via middleware (method, path, correlation ID, user ID)
- [ ] **BLOG-02**: HTTP responses are logged (status code, duration)
- [ ] **BLOG-03**: AI service calls are logged (provider, model, input/output tokens, duration)
- [ ] **BLOG-04**: Errors are captured with exception type, stack trace, and request context
- [ ] **BLOG-05**: Database operations are logged (table, operation, duration)
- [ ] **BLOG-06**: SSE streaming summaries are logged (event count, total duration)
- [ ] **BLOG-07**: Logging uses async-safe pattern (QueueHandler) to avoid blocking event loop
- [ ] **BLOG-08**: Sensitive data is sanitized before logging (tokens, API keys, PII fields)

### Settings & Configuration

- [ ] **SLOG-01**: Logging toggle state persists across app restarts
- [ ] **SLOG-02**: Backend logging level is configurable via environment variable
- [ ] **SLOG-03**: Log directory path is configurable via environment variable
- [ ] **SLOG-04**: Frontend buffer size is configurable (default: 1000 entries)
- [ ] **SLOG-05**: Frontend flush interval is configurable (default: 5 minutes)

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
| LOG-05 | Phase 47 | Pending |
| LOG-06 | Phase 43 | Complete |
| LOG-07 | Phase 44 | Complete |
| LOG-08 | Phase 43 | Complete |
| FLOG-01 | Phase 45 | Pending |
| FLOG-02 | Phase 45 | Pending |
| FLOG-03 | Phase 46 | Complete |
| FLOG-04 | Phase 45 | Pending |
| FLOG-05 | Phase 45 | Pending |
| FLOG-06 | Phase 45 | Pending |
| FLOG-07 | Phase 45 | Pending |
| FLOG-08 | Phase 48 | Pending |
| BLOG-01 | Phase 43 | Complete |
| BLOG-02 | Phase 43 | Complete |
| BLOG-03 | Phase 43 | Complete |
| BLOG-04 | Phase 43 | Complete |
| BLOG-05 | Phase 43 | Complete |
| BLOG-06 | Phase 43 | Complete |
| BLOG-07 | Phase 43 | Complete |
| BLOG-08 | Phase 43 | Complete |
| SLOG-01 | Phase 47 | Pending |
| SLOG-02 | Phase 43 | Complete |
| SLOG-03 | Phase 43 | Complete |
| SLOG-04 | Phase 45 | Pending |
| SLOG-05 | Phase 48 | Pending |

**Coverage:**
- v1.9.5 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0

---
*Requirements defined: 2026-02-07*
*Roadmap created: 2026-02-07*
