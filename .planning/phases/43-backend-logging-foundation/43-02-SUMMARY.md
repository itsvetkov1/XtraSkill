---
phase: 43-backend-logging-foundation
plan: 02
subsystem: api
tags: [fastapi, middleware, correlation-id, http-logging, contextvars, structlog]

# Dependency graph
requires:
  - phase: 43-01
    provides: LoggingService with async-safe structured JSON logging
provides:
  - LoggingMiddleware ASGI middleware for HTTP request/response logging
  - Correlation ID generation and propagation via contextvars
  - X-Correlation-ID header support (request extraction, response injection)
  - Request timing and status code logging
affects: [43-03, 43-04, frontend-logging, api-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BaseHTTPMiddleware pattern for FastAPI"
    - "contextvars for async-safe request-scoped storage"
    - "time.perf_counter() for high-resolution timing"
    - "Correlation ID propagation via HTTP headers"

key-files:
  created:
    - backend/app/middleware/__init__.py
    - backend/app/middleware/logging_middleware.py
  modified:
    - backend/main.py

key-decisions:
  - "Use contextvars for correlation ID storage (async-safe, request-scoped)"
  - "Generate UUID v4 for correlation ID if not provided in request header"
  - "Add middleware after CORSMiddleware to log all requests including preflight"
  - "Vary log level by status code: INFO for 2xx/3xx, WARNING for 4xx, ERROR for 5xx"

patterns-established:
  - "Middleware pattern: Extract/generate correlation ID → store in contextvar → log request → process → log response → add to headers"
  - "Export pattern: middleware/__init__.py exports middleware classes"
  - "Timing pattern: perf_counter() start → process → calculate duration_ms"

# Metrics
duration: 2min
completed: 2026-02-07
---

# Phase 43 Plan 02: HTTP Logging Middleware Summary

**ASGI middleware logs all HTTP requests/responses with correlation IDs, timing, and structured JSON output via LoggingService**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-07T18:33:48Z
- **Completed:** 2026-02-07T18:35:37Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- LoggingMiddleware implemented as BaseHTTPMiddleware with correlation ID support
- Correlation ID generation (UUID v4) or extraction from X-Correlation-ID header
- Request-scoped storage via contextvars (async-safe, accessible throughout request lifecycle)
- HTTP request/response logging with method, path, status, duration, user ID
- X-Correlation-ID response header for frontend correlation
- Integration into main.py with proper shutdown in lifespan handler

## Task Commits

Each task was committed atomically:

1. **Task 1: Create middleware package with __init__.py** - `76d784c` (chore)
2. **Task 2: Create LoggingMiddleware with correlation ID support** - `c6d0c9a` (feat)
3. **Task 3: Integrate LoggingMiddleware into main.py** - `e4408cc` (feat)

## Files Created/Modified
- `backend/app/middleware/__init__.py` - Middleware package exports (LoggingMiddleware)
- `backend/app/middleware/logging_middleware.py` - 152-line ASGI middleware with correlation ID propagation, HTTP logging, and timing
- `backend/main.py` - Added LoggingMiddleware after CORSMiddleware, logging service shutdown in lifespan

## Decisions Made

1. **contextvars for correlation ID storage**
   - Rationale: Async-safe, request-scoped, automatically cleaned up after request
   - Alternative considered: threading.local (not async-safe)

2. **UUID v4 for generated correlation IDs**
   - Rationale: Globally unique, no collision risk, standard format
   - Pattern: str(uuid.uuid4()) → "550e8400-e29b-41d4-a716-446655440000"

3. **Middleware order: CORS → Logging → Routes**
   - Rationale: Logging should see all requests including CORS preflight
   - CORS must be first to handle OPTIONS requests

4. **Vary log level by status code**
   - INFO: 2xx/3xx (success)
   - WARNING: 4xx (client error)
   - ERROR: 5xx (server error)
   - Rationale: Enables log filtering by severity

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed standard FastAPI middleware patterns.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for 43-03 (Category-based logging enhancement)**
- LoggingMiddleware operational
- Correlation ID accessible via get_correlation_id() from any request context
- All HTTP requests producing structured JSON logs
- Foundation in place for service-level logging (ai_service, auth, database)

**Ready for future frontend logging:**
- X-Correlation-ID header in responses enables frontend to correlate logs
- Backend endpoint can receive frontend logs with matching correlation IDs

**No blockers or concerns**

## Self-Check: PASSED

All created files exist:
- backend/app/middleware/__init__.py ✓
- backend/app/middleware/logging_middleware.py ✓

All commits verified:
- 76d784c ✓
- c6d0c9a ✓
- e4408cc ✓

---
*Phase: 43-backend-logging-foundation*
*Completed: 2026-02-07*
