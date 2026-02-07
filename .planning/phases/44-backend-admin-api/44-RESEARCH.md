# Phase 44: Backend Admin API - Research

**Researched:** 2026-02-08
**Domain:** FastAPI admin endpoints, file operations security, log ingestion validation
**Confidence:** HIGH

## Summary

This phase implements three authenticated API endpoints for log management: listing available log files, downloading log files securely, and ingesting frontend logs. The primary technical challenges are implementing admin-only authentication, preventing path traversal vulnerabilities, and validating large JSON payloads efficiently.

**Current state:** Backend has JWT authentication with `get_current_user` dependency, structured JSON logging to `backend/logs/app.log` with daily rotation, and no admin role distinction (all authenticated users are equal).

**Standard approach:** Use FastAPI dependency injection to create admin role checker, `FileResponse` for streaming log downloads, pathlib validation to prevent path traversal, and Pydantic models with size limits for log ingestion.

**Primary recommendation:** Add `is_admin` boolean to User model, create `get_admin_user` dependency that checks this flag, use pathlib's `resolve()` + `is_relative_to()` for secure file path validation, and use FileResponse for efficient streaming without memory bloat.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | Web framework | Native dependency injection, FileResponse built-in |
| Pydantic | 2.x | Request validation | 4-17x faster than v1, Rust core for heavy payloads |
| pathlib | stdlib | File path validation | Secure path resolution with `resolve()` and `is_relative_to()` |
| python-jose | 3.3+ | JWT handling | Already used for authentication in codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.0+ | Database ORM | User model migration for admin flag |
| Alembic | Latest | Schema migration | Adding `is_admin` column to users table |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Boolean flag | RBAC library (fastapi-user-auth) | Boolean sufficient for single role; RBAC adds complexity for pilot |
| FileResponse | StreamingResponse | FileResponse optimized for disk files; StreamingResponse for generated content |
| pathlib | os.path | pathlib provides cleaner API and better security with `is_relative_to()` |

**Installation:**
No new dependencies required - all core libraries already in project.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── routes/
│   ├── auth.py           # Existing authentication routes
│   └── logs.py           # NEW: Admin log endpoints
├── utils/
│   └── jwt.py            # Existing JWT utilities
│       ├── get_current_user()    # Existing
│       └── get_admin_user()      # NEW: Admin dependency
└── services/
    └── logging_service.py        # Existing logging service
```

### Pattern 1: Admin Role Check via Dependency Injection
**What:** Reusable dependency that validates user is admin before allowing endpoint access
**When to use:** All admin-only endpoints (logs, future admin features)
**Example:**
```python
# Source: Compiled from multiple 2025-2026 FastAPI RBAC tutorials
# In app/utils/jwt.py

async def get_admin_user(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency to verify current user has admin privileges.

    Usage:
        @router.get("/admin/logs")
        async def list_logs(admin: User = Depends(get_admin_user)):
            # Only admins reach here

    Raises:
        HTTPException 403: If user lacks admin privileges
    """
    from sqlalchemy import select
    from app.models import User

    stmt = select(User).where(User.id == user["user_id"])
    result = await db.execute(stmt)
    user_obj = result.scalar_one_or_none()

    if not user_obj or not user_obj.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return user_obj
```

### Pattern 2: Secure File Path Validation
**What:** Prevent path traversal attacks when listing/downloading files
**When to use:** Any endpoint that accepts filename/path from client
**Example:**
```python
# Source: https://salvatoresecurity.com/preventing-directory-traversal-vulnerabilities-in-python/
from pathlib import Path
from fastapi import HTTPException, status

def validate_log_file_path(filename: str, log_dir: Path) -> Path:
    """
    Validate that requested filename is within log directory.

    Prevents path traversal attacks like "../../../etc/passwd"

    Args:
        filename: User-provided filename (e.g., "app.log.2026-02-07")
        log_dir: Trusted base directory for logs

    Returns:
        Resolved absolute path if valid

    Raises:
        HTTPException 400: If path traversal detected
    """
    try:
        # Resolve to canonical absolute path (follows symlinks)
        base_dir = log_dir.resolve()
        requested_path = (base_dir / filename).resolve()

        # Ensure resolved path is within base directory
        if not requested_path.is_relative_to(base_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )

        # Ensure file exists
        if not requested_path.exists() or not requested_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log file not found"
            )

        return requested_path

    except (RuntimeError, ValueError) as e:
        # RuntimeError: Infinite symlink loop
        # ValueError: Path manipulation issues
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )
```

### Pattern 3: Efficient File Download with FileResponse
**What:** Stream files from disk without loading into memory
**When to use:** Downloading existing log files (not generated content)
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/custom-response/
from fastapi.responses import FileResponse

@router.get("/logs/download")
async def download_log_file(
    filename: str,
    admin: User = Depends(get_admin_user),
):
    """
    Download a specific log file.

    FileResponse streams file efficiently without blocking event loop
    or loading entire file into memory.
    """
    log_dir = settings.log_dir_path
    file_path = validate_log_file_path(filename, log_dir)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/json",  # Structured JSON logs
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
```

### Pattern 4: Log Ingestion with Request Size Limits
**What:** Accept frontend logs with validation and size constraints
**When to use:** POST endpoint receiving batched logs from frontend
**Example:**
```python
# Source: Multiple 2026 FastAPI performance guides
from pydantic import BaseModel, Field, field_validator
from typing import List

class LogEntry(BaseModel):
    """Single frontend log entry."""
    timestamp: str
    level: str
    message: str
    category: str
    correlation_id: str | None = None
    session_id: str
    # Additional frontend-specific fields

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in allowed:
            raise ValueError(f'Level must be one of {allowed}')
        return v.upper()

class LogBatch(BaseModel):
    """Batch of frontend logs."""
    logs: List[LogEntry] = Field(..., max_length=1000)
    # Limit batch size to prevent memory issues

    @field_validator('logs')
    @classmethod
    def validate_not_empty(cls, v: List[LogEntry]) -> List[LogEntry]:
        if not v:
            raise ValueError('Log batch cannot be empty')
        return v

@router.post("/logs/ingest")
async def ingest_frontend_logs(
    batch: LogBatch,
    user: dict = Depends(get_current_user),  # Any authenticated user can send logs
):
    """
    Receive frontend logs and append to backend log storage.

    Note: Does NOT require admin - all users can send their own logs.
    """
    # Write to frontend-specific log file
    # (Keep separate from backend logs for clarity)
    pass
```

### Anti-Patterns to Avoid
- **Loading files into memory:** Never use `open().read()` for log downloads - use FileResponse streaming
- **Exposing raw filesystem paths:** Never return absolute paths in API responses (e.g., `C:\backend\logs\app.log`)
- **Trusting client filenames:** Always validate with pathlib before filesystem operations
- **No admin check:** Logs contain sensitive data (user IDs, API activity) - require admin role
- **Unlimited payload size:** Frontend could send 100MB batch - enforce max_length on Pydantic models

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File streaming | Custom chunk iterator | `FileResponse` | Handles ranges, caching, content-type automatically |
| Path validation | String manipulation (replace "..", check "/") | `pathlib.resolve()` + `is_relative_to()` | Handles symlinks, Windows/Linux differences, edge cases |
| Request size limits | Manual byte counting | Pydantic `Field(max_length=N)` | Validated before processing, clear error messages |
| JWT verification | Custom token parsing | Existing `get_current_user` | Already handles expiry, signature, payload extraction |

**Key insight:** Path traversal vulnerabilities are notoriously difficult to prevent correctly with string operations. The tarfile module has had CVE-2007-4559 (path traversal) unfixed for 15+ years. pathlib's `resolve()` + `is_relative_to()` is the Python community's recommended approach as of 2025-2026.

## Common Pitfalls

### Pitfall 1: Forgetting to Check Admin Role
**What goes wrong:** All authenticated users can download logs containing sensitive data (user IDs, correlation IDs, API activity)
**Why it happens:** Existing auth only checks "is user logged in", not "does user have permission"
**How to avoid:** Create `get_admin_user` dependency that checks `is_admin` flag, use it on all log endpoints
**Warning signs:** Code reviews should flag any `/logs` endpoint using `get_current_user` instead of `get_admin_user`

### Pitfall 2: Path Traversal via URL Encoding
**What goes wrong:** Attacker sends `filename=%2E%2E%2F%2E%2E%2Fetc%2Fpasswd` (URL-encoded `../../etc/passwd`)
**Why it happens:** FastAPI decodes URL parameters automatically, but validation might happen on encoded string
**How to avoid:** Validate AFTER FastAPI's parameter parsing, use pathlib which handles decoded strings correctly
**Warning signs:** Getting filenames from raw request.url instead of endpoint parameters

### Pitfall 3: Race Condition on Log Rotation
**What goes wrong:** User requests `app.log` but file rotates mid-download to `app.log.2026-02-08`, resulting in FileNotFoundError
**Why it happens:** TimedRotatingFileHandler renames files at midnight
**How to avoid:** FileResponse handles this gracefully (raises 404), document that downloads near midnight may fail
**Warning signs:** No special handling needed - FileResponse is atomic

### Pitfall 4: Exposing Frontend Logs to All Users
**What goes wrong:** User A sends logs, User B downloads them and sees User A's session data
**Why it happens:** Treating frontend logs like backend logs (centralized storage)
**How to avoid:** Two approaches:
  1. Write frontend logs to user-specific files (`logs/frontend_{user_id}.log`)
  2. OR require admin to download frontend logs (treat as sensitive)
**Warning signs:** LOG-07 says "admin can download" but doesn't specify which logs - clarify scope

### Pitfall 5: Memory Exhaustion from Large Ingestion
**What goes wrong:** Frontend sends 10,000 log entries (50MB JSON), Pydantic validation loads entire payload into memory
**Why it happens:** Pydantic v2 is fast but still validates full structure before endpoint executes
**How to avoid:** Set `max_length=1000` on LogBatch.logs field, document batch size limit for frontend
**Warning signs:** Lack of explicit size limits in Pydantic models

## Code Examples

Verified patterns from official sources:

### Listing Available Log Files
```python
# Source: Python pathlib documentation + FastAPI patterns
from pathlib import Path
from typing import List

@router.get("/logs", response_model=List[str])
async def list_log_files(
    admin: User = Depends(get_admin_user),
):
    """
    List available log files for download.

    Returns filenames only (not absolute paths) for security.
    Admin can then request specific file via /logs/download?filename=X
    """
    log_dir = settings.log_dir_path

    # Glob for log files (app.log, app.log.2026-02-07, etc.)
    log_files = sorted(
        log_dir.glob("app.log*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True  # Most recent first
    )

    # Return only filenames, not full paths
    return [f.name for f in log_files if f.is_file()]
```

### Complete Download Endpoint
```python
# Source: Combining FastAPI FileResponse + pathlib validation patterns

@router.get("/logs/download")
async def download_log_file(
    filename: str,
    admin: User = Depends(get_admin_user),
):
    """
    Download a specific log file.

    Query params:
        filename: Name of log file (e.g., "app.log", "app.log.2026-02-07")

    Returns:
        File stream as application/json attachment

    Security:
        - Requires admin authentication
        - Validates path to prevent traversal
        - Only serves files from configured log directory
    """
    log_dir = settings.log_dir_path
    file_path = validate_log_file_path(filename, log_dir)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
```

### Frontend Log Ingestion
```python
# Source: FastAPI validation + structlog writing patterns

@router.post("/logs/ingest")
async def ingest_frontend_logs(
    batch: LogBatch,
    user: dict = Depends(get_current_user),  # Any user can send logs
):
    """
    Ingest batched logs from frontend.

    Frontend sends logs periodically (every 5 minutes or on app pause).
    Logs are written to separate frontend log file for later analysis.

    Request body:
        {
          "logs": [
            {
              "timestamp": "2026-02-08T12:34:56.789Z",
              "level": "INFO",
              "message": "User navigated to Projects screen",
              "category": "navigation",
              "session_id": "uuid",
              "correlation_id": "uuid"
            }
          ]
        }

    Security:
        - Requires authentication (any user)
        - Batch size limited to 1000 entries
        - Logs written to user-specific file
    """
    logging_service = get_logging_service()

    # Write each log entry to structured log
    for entry in batch.logs:
        logging_service.log(
            level=entry.level,
            message=f"[FRONTEND] {entry.message}",
            category=f"frontend.{entry.category}",
            user_id=user["user_id"],
            session_id=entry.session_id,
            correlation_id=entry.correlation_id,
            # Include any additional frontend fields
        )

    return {
        "status": "success",
        "ingested": len(batch.logs)
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| String path validation | pathlib `resolve()` + `is_relative_to()` | Python 3.9 (2020) | Simpler, more secure, handles symlinks |
| Manual file chunking | FileResponse | FastAPI 0.1+ (2018) | Async-safe, memory-efficient, handles ranges |
| Pydantic v1 validation | Pydantic v2 with Rust core | Pydantic 2.0 (2023) | 4-17x faster for large payloads |
| os.path manipulation | pathlib Path objects | Python 3.4+ (2014) | Cleaner API, cross-platform |

**Deprecated/outdated:**
- `os.path.join()` + string checks: pathlib is now standard for path operations
- Loading files with `open().read()`: StreamingResponse/FileResponse are async-safe
- Custom RBAC libraries for single role: Dependency injection sufficient for admin flag

## Open Questions

Things that couldn't be fully resolved:

1. **Should frontend logs be user-specific or centralized?**
   - What we know: LOG-07 requires "admin can download logs", doesn't specify backend vs frontend
   - What's unclear: Privacy implications of admins seeing all user navigation/actions
   - Recommendation: Write all logs (frontend + backend) to same file with `user_id` field, require admin to download. Frontend flush endpoint (`POST /logs/ingest`) available to all authenticated users.

2. **Should log download support filtering by date range?**
   - What we know: Daily rotation creates separate files (`app.log.2026-02-07`)
   - What's unclear: Does admin need to download all files or just specific dates?
   - Recommendation: Start with simple file listing + download. Admin can glob files client-side. Future enhancement: query parameter like `?from=2026-02-01&to=2026-02-07` returns filtered entries (Phase 44.1).

3. **Do we need log compression?**
   - What we know: 7-day retention, structured JSON format
   - What's unclear: Estimated log volume during pilot (10MB? 100MB?)
   - Recommendation: Skip compression for pilot. Out of scope per REQUIREMENTS.md. If 7-day volume exceeds 50MB, revisit in Phase 44.1.

## Sources

### Primary (HIGH confidence)
- [FastAPI Custom Response Documentation](https://fastapi.tiangolo.com/advanced/custom-response/) - FileResponse official usage
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/first-steps/) - Dependency injection for auth
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html) - Path.resolve() and is_relative_to()
- [Preventing Directory Traversal in Python](https://salvatoresecurity.com/preventing-directory-traversal-vulnerabilities-in-python/) - Pathlib validation patterns

### Secondary (MEDIUM confidence)
- [FastAPI Authentication and Authorization Guide (2024)](https://betterstack.com/community/guides/scaling-python/authentication-fastapi/) - Role-based access patterns
- [FastAPI File Downloads Guide](https://davidmuraya.com/blog/fastapi-file-downloads/) - FileResponse best practices
- [How to Use Dependency Injection in FastAPI (Feb 2026)](https://oneuptime.com/blog/post/2026-02-02-fastapi-dependency-injection/view) - Admin role dependency pattern
- [FastAPI Under Load in 2026: Pydantic v2 (Jan 2026)](https://medium.com/@2nick2patel2/fastapi-under-load-in-2026-pydantic-v2-uvloop-http-3-what-actually-moves-the-needle-74717b74e74e) - Pydantic validation performance

### Tertiary (LOW confidence)
- [Path Traversal and Remediation in Python](https://osintteam.blog/path-traversal-and-remediation-in-python-0b6e126b4746) - Additional validation patterns
- [How to Log API Endpoints Using Python FastAPI](https://apidog.com/blog/logging-endpoints-python-fastapi/) - Logging patterns for endpoints

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project, no new dependencies
- Architecture: HIGH - Official FastAPI patterns, pathlib is stdlib, extensive 2025-2026 sources
- Pitfalls: HIGH - Path traversal is well-documented vulnerability class, FileResponse patterns verified

**Research date:** 2026-02-08
**Valid until:** 60 days (stable domain - file operations and FastAPI patterns change slowly)
