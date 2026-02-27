"""
Artifact endpoints for viewing generated business analysis artifacts.

Provides GET endpoints only - artifact generation happens through chat with save_artifact tool.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Artifact, Thread, Project, ArtifactType
from app.utils.jwt import get_current_user
from app.services.export_service import (
    export_markdown,
    export_pdf,
    export_docx,
    get_content_type,
    ExportFormat
)

router = APIRouter()


class ArtifactResponse(BaseModel):
    """Response model for artifact data."""
    id: str
    thread_id: str
    artifact_type: ArtifactType
    title: str
    content_markdown: str
    content_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArtifactListItem(BaseModel):
    """Lightweight response model for artifact list."""
    id: str
    thread_id: str
    artifact_type: ArtifactType
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/threads/{thread_id}/artifacts", response_model=List[ArtifactListItem])
async def list_thread_artifacts(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all artifacts for a thread.

    Returns lightweight artifact list without full content.
    Validates user owns the thread's project.

    Args:
        thread_id: ID of the thread
        current_user: Authenticated user
        db: Database session

    Returns:
        List of artifacts for the thread

    Raises:
        HTTPException 404: Thread not found or not owned by user
    """
    # Validate thread access
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Check ownership: project-less threads use user_id, project threads use project.user_id
    owner_id = thread.user_id if thread.project is None else thread.project.user_id
    if owner_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Get artifacts
    stmt = (
        select(Artifact)
        .where(Artifact.thread_id == thread_id)
        .order_by(Artifact.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single artifact with full content.

    Validates user owns the artifact's thread's project.

    Args:
        artifact_id: ID of the artifact
        current_user: Authenticated user
        db: Database session

    Returns:
        Full artifact data including content

    Raises:
        HTTPException 404: Artifact not found or not owned by user
    """
    stmt = (
        select(Artifact)
        .where(Artifact.id == artifact_id)
        .options(selectinload(Artifact.thread).selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )

    # Check ownership: project-less threads use user_id, project threads use project.user_id
    thread = artifact.thread
    owner_id = thread.user_id if thread.project is None else thread.project.user_id
    if owner_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )

    return artifact


@router.get("/artifacts/{artifact_id}/export/{format}")
async def export_artifact(
    artifact_id: str,
    format: ExportFormat,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export artifact in specified format.

    Formats:
    - md: Markdown text file
    - pdf: PDF document with styling (requires WeasyPrint/GTK)
    - docx: Microsoft Word document

    Returns file as streaming response with appropriate headers
    for browser download.

    Args:
        artifact_id: ID of the artifact to export
        format: Export format (md, pdf, docx)
        current_user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse with file content

    Raises:
        HTTPException 404: Artifact not found or not owned by user
        HTTPException 400: Unsupported format
        HTTPException 500: PDF export failed (GTK not available)
    """
    # Load artifact with thread and project for auth check
    stmt = (
        select(Artifact)
        .where(Artifact.id == artifact_id)
        .options(selectinload(Artifact.thread).selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Check ownership: project-less threads use user_id, project threads use project.user_id
    thread = artifact.thread
    owner_id = thread.user_id if thread.project is None else thread.project.user_id
    if owner_id != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Generate export based on format
    try:
        if format == "md":
            buffer = await asyncio.to_thread(export_markdown, artifact)
        elif format == "pdf":
            buffer = await asyncio.to_thread(export_pdf, artifact)
        elif format == "docx":
            buffer = await asyncio.to_thread(export_docx, artifact)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    except ImportError as e:
        # PDF export may fail without GTK/Pango system libraries
        logger.error(f"Export {format} failed (ImportError): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )
    except Exception as e:
        # Catch rendering errors (template issues, WeasyPrint crashes, etc.)
        logger.error(f"Export {format} failed for artifact {artifact_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )

    # Sanitize filename for Content-Disposition
    safe_title = "".join(c for c in artifact.title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title[:50] or "artifact"

    return StreamingResponse(
        buffer,
        media_type=get_content_type(format),
        headers={
            "Content-Disposition": f'attachment; filename="{safe_title}.{format}"'
        }
    )
