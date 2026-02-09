"""
Log management API endpoints.

Admin endpoints for listing and downloading log files.
Authenticated user endpoint for frontend log ingestion.
"""
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.models import User
from app.services.logging_service import get_logging_service
from app.middleware.logging_middleware import get_correlation_id
from app.utils.jwt import get_admin_user, get_current_user

router = APIRouter(prefix="/api/logs", tags=["logs"])


# --- Path Validation Utility ---

def validate_log_file_path(filename: str, log_dir: Path) -> Path:
    """
    Validate that requested filename is within log directory.

    Prevents path traversal attacks like "../../../etc/passwd".

    Args:
        filename: User-provided filename (e.g., "app.log.2026-02-07")
        log_dir: Trusted base directory for logs

    Returns:
        Resolved absolute path if valid

    Raises:
        HTTPException 400: If path traversal detected
        HTTPException 404: If file not found
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

    except (RuntimeError, ValueError):
        # RuntimeError: Infinite symlink loop
        # ValueError: Path manipulation issues
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )


# --- Pydantic Models for Log Ingestion ---

class LogEntry(BaseModel):
    """Single frontend log entry."""
    timestamp: str
    level: str
    message: str
    category: str
    correlation_id: Optional[str] = None
    session_id: str
    # Additional frontend-specific fields can be added as needed

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

    @field_validator('logs')
    @classmethod
    def validate_not_empty(cls, v: List[LogEntry]) -> List[LogEntry]:
        if not v:
            raise ValueError('Log batch cannot be empty')
        return v


# --- Endpoints ---

@router.get("", response_model=List[str])
async def list_log_files(
    admin: User = Depends(get_admin_user),
):
    """
    List available log files for download.

    Returns filenames only (not absolute paths) for security.
    Files are sorted by modification time (most recent first).

    Security:
        - Requires admin authentication

    Returns:
        List of log filenames (e.g., ["app.log", "app.log.2026-02-07"])
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


@router.get("/download")
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
        - Validates path to prevent traversal attacks
        - Only serves files from configured log directory

    Raises:
        HTTPException 400: Invalid filename or path traversal attempt
        HTTPException 404: File not found
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


@router.post("/ingest")
async def ingest_frontend_logs(
    batch: LogBatch,
    user: dict = Depends(get_current_user),
):
    """
    Ingest batched logs from frontend.

    Frontend sends logs periodically (every 5 minutes or on app pause).
    Logs are written to same log file with [FRONTEND] prefix for filtering.

    Request body:
        {
          "logs": [
            {
              "timestamp": "2026-02-08T12:34:56.789Z",
              "level": "INFO",
              "message": "User navigated to Projects screen",
              "category": "navigation",
              "session_id": "uuid",
              "correlation_id": "uuid"  // optional
            }
          ]
        }

    Security:
        - Requires authentication (any user can send their own logs)
        - Batch size limited to 1000 entries (prevents memory exhaustion)
        - Logs include user_id for attribution

    Returns:
        {"status": "success", "ingested": N}
    """
    logging_service = get_logging_service()

    # Write each log entry to structured log with [FRONTEND] prefix
    for entry in batch.logs:
        logging_service.log(
            level=entry.level,
            message=f"[FRONTEND] {entry.message}",
            category=f"frontend.{entry.category}",
            user_id=user["user_id"],
            session_id=entry.session_id,
            correlation_id=entry.correlation_id or get_correlation_id(),
            # Frontend timestamp included in message for reference
            frontend_timestamp=entry.timestamp,
        )

    return {
        "status": "success",
        "ingested": len(batch.logs)
    }
