"""
Artifact endpoints for viewing generated business analysis artifacts.

Provides GET endpoints only - artifact generation happens through chat with save_artifact tool.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Artifact, Thread, Project, ArtifactType
from app.utils.jwt import get_current_user

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

    if not thread or thread.project.user_id != current_user["user_id"]:
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

    if not artifact or artifact.thread.project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )

    return artifact
