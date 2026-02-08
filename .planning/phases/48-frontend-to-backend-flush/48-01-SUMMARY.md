---
phase: 48-frontend-to-backend-flush
plan: 01
subsystem: logging
tags: [flutter, dio, flush, lifecycle, timer, secure-storage]

# Dependency graph
requires:
  - phase: 45-frontend-logging-foundation
    provides: LoggingService singleton with buffer, SessionService
  - phase: 46-frontend-http-integration
    provides: ApiClient singleton with Dio instance
  - phase: 47-frontend-settings-ui
    provides: LoggingProvider with isEnabled toggle
provides:
  - flush() method that POSTs buffered logs to backend
  - AppLifecycleListener for pause/detach flush triggers
  - Timer.periodic for 5-minute automatic flush
  - Logout-triggered flush via AuthProvider
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lifecycle-aware flush with AppLifecycleListener"
    - "Concurrent flush protection with _isFlushInProgress flag"
    - "Buffer copy before async POST to prevent mutation"

key-files:
  created: []
  modified:
    - frontend/lib/services/logging_service.dart
    - frontend/lib/providers/auth_provider.dart

key-decisions:
  - "LOG-027: Copy buffer before POST to prevent mutation during async operation"
  - "LOG-028: Use debugPrint for flush errors to avoid infinite logging loop"
  - "LOG-029: Skip flush if not authenticated to prevent 401 spam"

patterns-established:
  - "Lifecycle flush: AppLifecycleListener with onPause/onDetach callbacks"
  - "Periodic flush: Timer.periodic with configurable interval"
  - "Pre-logout flush: Flush logs before clearing auth token"

# Metrics
duration: 8min
completed: 2026-02-08
---

# Phase 48 Plan 01: Frontend Log Flush Summary

**Log flush mechanism with 5-minute timer, lifecycle triggers, and logout flush to POST buffered frontend logs to backend ingest endpoint**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-08T13:10:00Z
- **Completed:** 2026-02-08T13:18:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Added flush() method that POSTs buffered logs to /api/logs/ingest with Bearer token
- Implemented 5-minute periodic flush via Timer.periodic
- Added AppLifecycleListener with onPause/onDetach callbacks for lifecycle-triggered flush
- Integrated flush-before-logout in AuthProvider to capture final session logs
- Buffer preservation on flush failure for automatic retry

## Task Commits

Each task was committed atomically:

1. **Task 1: Add flush() method and lifecycle integration to LoggingService** - `15927a3` (feat)
2. **Task 2: Add flush-before-logout to AuthProvider** - `ae4da70` (feat)
3. **Task 3: Verify flush integration with manual test** - (verification only, no code changes)

## Files Created/Modified
- `frontend/lib/services/logging_service.dart` - Added flush() method, AppLifecycleListener, Timer.periodic, FlutterSecureStorage for token retrieval
- `frontend/lib/providers/auth_provider.dart` - Added LoggingService import and flush() call before logout

## Decisions Made

1. **LOG-027: Buffer copy before POST** - Copy buffer to local list before async POST to prevent mutation during transmission
2. **LOG-028: debugPrint for flush errors** - Use debugPrint instead of logError to avoid infinite loop when flush fails
3. **LOG-029: Auth check before flush** - Skip flush if not authenticated to prevent 401 errors

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 48 is the final phase of milestone v1.9.5 (Pilot Logging Infrastructure). The logging pipeline is now complete:

1. Frontend captures logs in buffer (Phase 45)
2. API calls include correlation IDs (Phase 46)
3. User can toggle logging in Settings (Phase 47)
4. Logs flush to backend periodically and on lifecycle events (Phase 48)
5. Backend stores logs with [FRONTEND] prefix for AI analysis

**Milestone v1.9.5 complete.** Ready for pilot testing.

## Self-Check: PASSED

---
*Phase: 48-frontend-to-backend-flush*
*Completed: 2026-02-08*
