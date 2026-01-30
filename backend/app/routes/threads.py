"""
Thread management endpoints for conversation organization.

Provides CRUD operations for threads within projects. Threads serve as containers
for AI conversations. In MVP, threads have optional titles and empty message lists.
AI will generate summaries and populate messages in Phase 3.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Message, Project, Thread
from app.utils.jwt import get_current_user

router = APIRouter()


# Request/Response models
class ThreadCreate(BaseModel):
    """Request model for creating a thread."""
    title: Optional[str] = Field(None, max_length=255)


class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    role: str
    content: str
    created_at: str

    class Config:
        from_attributes = True


class ThreadResponse(BaseModel):
    """Response model for a thread."""
    id: str
    project_id: str
    title: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ThreadListResponse(ThreadResponse):
    """Response model for thread in list view with message count."""
    message_count: int


class ThreadDetailResponse(ThreadResponse):
    """Response model for thread details with full message history."""
    messages: List[MessageResponse]


@router.post(
    "/projects/{project_id}/threads",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(
    project_id: str,
    thread_data: ThreadCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new thread within a project.

    Args:
        project_id: ID of the project to create thread in
        thread_data: Thread creation data (optional title)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Created thread with ID, project_id, title, timestamps

    Raises:
        404: Project not found or doesn't belong to user
        400: Invalid title length
    """
    # Validate project exists and belongs to user
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user["user_id"]
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validate title length if provided
    if thread_data.title is not None and len(thread_data.title) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title must be 255 characters or less"
        )

    # Create thread
    thread = Thread(
        project_id=project_id,
        title=thread_data.title
    )

    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    return ThreadResponse(
        id=thread.id,
        project_id=thread.project_id,
        title=thread.title,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
    )


@router.get(
    "/projects/{project_id}/threads",
    response_model=List[ThreadListResponse],
)
async def list_threads(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all threads in a project ordered by creation date (newest first).

    Args:
        project_id: ID of the project
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        List of threads with message counts, ordered by created_at DESC

    Raises:
        404: Project not found or doesn't belong to user
    """
    # Validate project ownership
    stmt_project = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user["user_id"]
    )
    result_project = await db.execute(stmt_project)
    project = result_project.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Get threads with messages loaded for counting
    stmt = (
        select(Thread)
        .where(Thread.project_id == project_id)
        .options(selectinload(Thread.messages))
        .order_by(Thread.created_at.desc())
    )
    result = await db.execute(stmt)
    threads = result.scalars().all()

    return [
        ThreadListResponse(
            id=thread.id,
            project_id=thread.project_id,
            title=thread.title,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
            message_count=len(thread.messages),
        )
        for thread in threads
    ]


@router.get(
    "/threads/{thread_id}",
    response_model=ThreadDetailResponse,
)
async def get_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get thread details with full conversation history.

    Args:
        thread_id: ID of the thread
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Thread with messages ordered chronologically (oldest first)

    Raises:
        404: Thread not found or doesn't belong to user's project
    """
    # Get thread with project and messages loaded
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(
            selectinload(Thread.project),
            selectinload(Thread.messages)
        )
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Validate thread belongs to user's project
    if thread.project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Sort messages chronologically (oldest first)
    sorted_messages = sorted(thread.messages, key=lambda m: m.created_at)

    return ThreadDetailResponse(
        id=thread.id,
        project_id=thread.project_id,
        title=thread.title,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in sorted_messages
        ],
    )


@router.delete(
    "/threads/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a thread and all related data.

    Cascades to delete all messages and artifacts via database
    foreign key constraints (ON DELETE CASCADE).

    Args:
        thread_id: Thread UUID
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        404: Thread not found or doesn't belong to user's project
    """
    # Get thread with project loaded for ownership check
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

    # Validate thread belongs to user's project
    if thread.project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Delete thread (cascades to messages, artifacts)
    await db.delete(thread)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
