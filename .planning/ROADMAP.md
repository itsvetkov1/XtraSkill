# Roadmap: BA Assistant v1.9.5

## Overview

This milestone adds comprehensive logging infrastructure for AI-powered debugging during pilot testing. The 6-phase build order starts with backend logging foundation (testable independently), adds admin API endpoints, then progressively integrates frontend logging with HTTP correlation, settings UI, and centralized flush to backend storage.

## Milestones

- **v1.9.5 Pilot Logging Infrastructure** - Phases 43-48 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (43, 44, 45...): Planned milestone work
- Decimal phases (43.1, 43.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 43: Backend Logging Foundation** - Core LoggingService with structlog, middleware, file rotation, config ✓
- [ ] **Phase 44: Backend Admin API** - Log listing, download, and ingest endpoints
- [ ] **Phase 45: Frontend Logging Foundation** - LoggingService, LoggingProvider, categories, buffering
- [ ] **Phase 46: Frontend HTTP Integration** - Dio interceptor with correlation ID header
- [ ] **Phase 47: Frontend Settings UI** - Logging toggle in Settings screen with persistence
- [ ] **Phase 48: Frontend-to-Backend Flush** - Send buffered logs to backend, lifecycle handling

## Phase Details

### Phase 43: Backend Logging Foundation
**Goal**: All backend operations produce structured, async-safe logs stored in rotating files
**Depends on**: Nothing (first phase)
**Requirements**: LOG-01, LOG-02, LOG-03, LOG-04, LOG-06, LOG-08, BLOG-01, BLOG-02, BLOG-03, BLOG-04, BLOG-05, BLOG-06, BLOG-07, BLOG-08, SLOG-02, SLOG-03
**Success Criteria** (what must be TRUE):
  1. Backend HTTP requests/responses are logged with method, path, status, duration, and correlation ID
  2. AI service calls are logged with provider, model, token counts, and timing
  3. Database operations are logged with table, operation type, and duration
  4. All log entries are structured JSON with consistent schema (timestamp, level, category, correlationId)
  5. Logs rotate automatically and retain for 7 days
**Plans**: 3 plans in 3 waves

Plans:
- [x] 43-01-PLAN.md — Configuration & LoggingService core (structlog, QueueHandler, file rotation) ✓
- [x] 43-02-PLAN.md — Correlation ID & LoggingMiddleware (HTTP request/response logging) ✓
- [x] 43-03-PLAN.md — Service integration & sanitization (AI, DB logging, sensitive data redaction) ✓

### Phase 44: Backend Admin API
**Goal**: Administrators can access logs via authenticated API endpoints
**Depends on**: Phase 43
**Requirements**: LOG-07
**Success Criteria** (what must be TRUE):
  1. Admin can list available log files via GET /api/logs
  2. Admin can download log files via GET /api/logs/download
  3. Backend can receive frontend logs via POST /api/logs/ingest
**Plans**: TBD

Plans:
- [ ] 44-01: TBD

### Phase 45: Frontend Logging Foundation
**Goal**: Frontend captures user actions, navigation, and errors with session grouping
**Depends on**: Phase 44 (needs ingest endpoint)
**Requirements**: FLOG-01, FLOG-02, FLOG-04, FLOG-05, FLOG-06, FLOG-07, SLOG-04
**Success Criteria** (what must be TRUE):
  1. User navigation events (screen views, route changes) are logged
  2. User actions (button clicks, form submits) are logged
  3. Errors are captured with exception type and stack trace
  4. All frontend logs include session ID and category tags
  5. Network state changes (connectivity, timeouts) are logged
**Plans**: TBD

Plans:
- [ ] 45-01: TBD

### Phase 46: Frontend HTTP Integration
**Goal**: All HTTP requests include correlation ID and are logged with response metadata
**Depends on**: Phase 45
**Requirements**: FLOG-03
**Success Criteria** (what must be TRUE):
  1. Dio interceptor attaches X-Correlation-ID header to all requests
  2. API requests/responses are logged with endpoint, method, status, and duration
  3. Correlation ID links frontend requests to backend logs
**Plans**: TBD

Plans:
- [ ] 46-01: TBD

### Phase 47: Frontend Settings UI
**Goal**: Users can toggle detailed logging from Settings screen
**Depends on**: Phase 46
**Requirements**: LOG-05, SLOG-01
**Success Criteria** (what must be TRUE):
  1. Logging toggle appears in Settings screen
  2. Toggle state persists across app restarts via SharedPreferences
  3. Disabling logging stops all log capture (no privacy leakage)
**Plans**: TBD

Plans:
- [ ] 47-01: TBD

### Phase 48: Frontend-to-Backend Flush
**Goal**: Buffered frontend logs are sent to backend for centralized storage
**Depends on**: Phase 47
**Requirements**: FLOG-08, SLOG-05
**Success Criteria** (what must be TRUE):
  1. Frontend logs are sent to backend via POST /api/logs/ingest
  2. Logs flush on configurable interval (default: 5 minutes)
  3. Logs flush on app lifecycle events (pause, terminate)
  4. Buffered logs persist until successfully delivered
**Plans**: TBD

Plans:
- [ ] 48-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 43 -> 44 -> 45 -> 46 -> 47 -> 48

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 43. Backend Logging Foundation | 3/3 | ✓ Complete | 2026-02-07 |
| 44. Backend Admin API | 0/TBD | Not started | - |
| 45. Frontend Logging Foundation | 0/TBD | Not started | - |
| 46. Frontend HTTP Integration | 0/TBD | Not started | - |
| 47. Frontend Settings UI | 0/TBD | Not started | - |
| 48. Frontend-to-Backend Flush | 0/TBD | Not started | - |

---

*Roadmap created: 2026-02-07*
*Milestone: v1.9.5 Pilot Logging Infrastructure*
*Requirements: 29 mapped across 6 phases*
