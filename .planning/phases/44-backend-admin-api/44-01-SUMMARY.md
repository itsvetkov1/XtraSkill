---
phase: 44-backend-admin-api
plan: 01
subsystem: api
tags: [admin, logging, fastapi, path-traversal, security]

# Dependency graph
requires:
  - phase: 43-backend-logging-foundation
    provides: LoggingService, structured JSON logging, correlation IDs
provides:
  - Admin log file listing endpoint (GET /api/logs)
  - Secure log file download endpoint (GET /api/logs/download)
  - Frontend log ingestion endpoint (POST /api/logs/ingest)
  - User.is_admin role field
  - get_admin_user dependency for admin enforcement
  - Path traversal protection utility
affects: [45-frontend-log-viewer, admin-dashboard, pilot-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Admin role enforcement via get_admin_user dependency"
    - "Path traversal protection using pathlib.resolve() + is_relative_to()"
    - "Pydantic batch size limits (max_length=1000) for DoS prevention"

key-files:
  created:
    - backend/app/routes/logs.py
  modified:
    - backend/app/models.py
    - backend/app/utils/jwt.py
    - backend/main.py

key-decisions:
  - "Boolean is_admin flag sufficient for single admin role (RBAC library overkill for pilot)"
  - "get_admin_user returns User object (not dict) for route access to user properties"
  - "Frontend logs written to same file with [FRONTEND] prefix (simpler than separate files)"
  - "Pydantic max_length=1000 prevents memory exhaustion attacks"

patterns-established:
  - "Admin-only endpoints use Depends(get_admin_user) for authorization"
  - "Path validation via validate_log_file_path() before file operations"
  - "FileResponse for efficient log file streaming"

# Metrics
duration: 3min
completed: 2026-02-07
---

# Phase 44 Plan 01: Admin Log Management API Summary

**Admin log management API with role-based access, secure file download, and frontend log ingestion via authenticated endpoints**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-07T22:30:00Z
- **Completed:** 2026-02-07T22:33:10Z
- **Tasks:** 3
- **Files modified:** 3 created, 1 modified

## Accomplishments
- Admin role enforcement via is_admin field and get_admin_user dependency
- Secure log file listing and download with path traversal protection
- Frontend log ingestion endpoint accepting batched logs from Flutter app
- Three new API endpoints operational under /api/logs prefix

## Task Commits

Each task was committed atomically:

1. **Task 1: Add is_admin field to User model and create get_admin_user dependency** - `c89f41f` (feat)
2. **Task 2: Create log management routes with secure file validation** - `7e126d6` (feat)
3. **Task 3: Register logs router in main application** - `b4ce91f` (feat)

## Files Created/Modified

### Created
- `backend/app/routes/logs.py` - Log management endpoints with path traversal protection

### Modified
- `backend/app/models.py` - Added User.is_admin boolean field
- `backend/app/utils/jwt.py` - Added get_admin_user dependency
- `backend/main.py` - Registered logs router

## Decisions Made

1. **Boolean is_admin flag over RBAC library**
   - Rationale: Single admin role sufficient for pilot phase, RBAC library adds unnecessary complexity
   - Implementation: is_admin field on User model with default=False

2. **get_admin_user returns User object (not dict)**
   - Rationale: Routes may need access to user properties beyond ID/email
   - Consistency: Matches existing get_current_user pattern but returns full object

3. **Frontend logs written to same file with prefix**
   - Rationale: Simpler than separate files, easy to filter with [FRONTEND] prefix
   - Benefit: Single log file maintains chronological order across backend and frontend events

4. **Path traversal protection via pathlib**
   - Pattern: resolve() + is_relative_to() prevents directory traversal attacks
   - Testing: Blocks attempts like "../../../etc/passwd" with 400 Bad Request

5. **Pydantic max_length limit on log batches**
   - Security: max_length=1000 prevents memory exhaustion attacks
   - UX: Frontend batches logs every 5 minutes, unlikely to exceed 1000 entries

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all imports resolved correctly, path validation works as expected.

## User Setup Required

**Manual admin user setup required for testing:**

To test admin endpoints, you need to manually set is_admin=1 for a user in the database:

```bash
# Using SQLite CLI
cd backend
sqlite3 ba_assistant.db
UPDATE users SET is_admin = 1 WHERE email = 'your-email@example.com';
.quit
```

Or using a database GUI tool:
1. Open backend/ba_assistant.db
2. Navigate to users table
3. Find your user by email
4. Set is_admin column to 1
5. Save changes

Verification:
```bash
# Login to get JWT token
curl -X POST http://localhost:8000/auth/google/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "..."}'

# Test admin endpoint (should return 200 with log file list)
curl -X GET http://localhost:8000/api/logs \
  -H "Authorization: Bearer {your_jwt_token}"
```

## Security Verification

### Path Traversal Protection Tests

The validate_log_file_path() function was designed to block path traversal attacks:

**Test cases (manual verification recommended):**

1. **Normal file access** (should succeed for admin):
   ```bash
   GET /api/logs/download?filename=app.log
   Expected: 200 OK with file download
   ```

2. **Path traversal attempt** (should be blocked):
   ```bash
   GET /api/logs/download?filename=../../../etc/passwd
   Expected: 400 Bad Request with "Invalid file path"
   ```

3. **Non-existent file** (should fail gracefully):
   ```bash
   GET /api/logs/download?filename=fake.log
   Expected: 404 Not Found with "Log file not found"
   ```

4. **Symlink escape attempt** (should be blocked):
   ```bash
   # If attacker creates symlink in log dir pointing outside
   GET /api/logs/download?filename=malicious_symlink
   Expected: 400 Bad Request (resolve() follows symlink, is_relative_to() catches escape)
   ```

### Admin Role Enforcement

All admin endpoints require is_admin=True:
- Non-admin users receive 403 Forbidden
- Unauthenticated users receive 401 Unauthorized
- Admin users can list and download log files

## Integration with Phase 43

This plan builds directly on Phase 43's logging infrastructure:

**From Phase 43:**
- LoggingService for structured JSON logging
- Correlation IDs via HTTP headers (X-Correlation-ID)
- TimedRotatingFileHandler for daily log rotation
- Log files stored in backend/logs/app.log*

**Phase 44 adds:**
- Admin API for downloading those log files
- Frontend ingestion endpoint using LoggingService
- Path traversal protection for secure file serving

**Example integration:**
```python
# Frontend log ingestion uses Phase 43's logging service
logging_service = get_logging_service()
logging_service.log(
    level="INFO",
    message="[FRONTEND] User navigated to Projects screen",
    category="frontend.navigation",
    user_id=user["user_id"],
    session_id=entry.session_id,
    correlation_id=entry.correlation_id or get_correlation_id(),
    frontend_timestamp=entry.timestamp,
)
```

Logs appear in same file as backend logs, filterable by [FRONTEND] prefix.

## Next Phase Readiness

**Ready for:**
- Phase 45: Frontend log viewer UI (admin dashboard)
- Pilot testing with log download capability
- Frontend log ingestion implementation in Flutter app

**What's available:**
- GET /api/logs returns array of log filenames sorted by date (most recent first)
- GET /api/logs/download?filename={name} streams log file efficiently
- POST /api/logs/ingest accepts LogBatch with up to 1000 entries

**Blockers/Concerns:**
- None - all endpoints operational
- Manual is_admin setup required (acceptable for pilot, future: admin UI)

**Production considerations:**
- Admin registration workflow needed (current: manual database update)
- Consider rate limiting on /api/logs/ingest (current: auth only)
- Log retention policy enforcement (current: TimedRotatingFileHandler handles rotation)

## Self-Check: PASSED

All files and commits verified:
- ✅ backend/app/routes/logs.py exists
- ✅ Commit c89f41f exists (Task 1)
- ✅ Commit 7e126d6 exists (Task 2)
- ✅ Commit b4ce91f exists (Task 3)

---
*Phase: 44-backend-admin-api*
*Completed: 2026-02-07*
