"""
Thread management endpoints for conversation organization.

Provides CRUD operations for threads within projects and global thread management.
Threads serve as containers for AI conversations. In MVP, threads have optional
titles and empty message lists. AI will generate summaries and populate messages
in Phase 3.

Supports two ownership models:
- Project-based: thread belongs to a project (legacy and current)
- Project-less: thread directly owned by user (global chats)
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Message, Project, Thread
from app.utils.jwt import get_current_user

router = APIRouter()

# Valid LLM providers for thread binding
VALID_PROVIDERS = ["anthropic", "google", "deepseek"]

# Valid conversation modes for threads
# Per PITFALL-07: Mode is a thread property, not global preference
VALID_MODES = ["meeting", "document_refinement"]


# Request/Response models
class ThreadCreate(BaseModel):
    """Request model for creating a thread within a project."""
    title: Optional[str] = Field(None, max_length=255)
    model_provider: Optional[str] = Field(None, max_length=20)
    conversation_mode: Optional[str] = Field(None, max_length=50)


class GlobalThreadCreate(BaseModel):
    """Request model for creating a thread (project optional)."""
    title: Optional[str] = Field(None, max_length=255)
    project_id: Optional[str] = None  # Null = project-less thread
    model_provider: Optional[str] = Field(None, max_length=20)
    conversation_mode: Optional[str] = Field(None, max_length=50)


class ThreadUpdate(BaseModel):
    """Request model for updating a thread (title and/or project association)."""
    title: Optional[str] = Field(None, max_length=255)
    project_id: Optional[str] = None  # For associating project-less chats with projects
    conversation_mode: Optional[str] = Field(None, max_length=50)


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
    project_id: Optional[str]  # Nullable for project-less threads
    title: Optional[str]
    model_provider: Optional[str] = "anthropic"  # Default for backward compatibility
    conversation_mode: Optional[str] = None
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


class GlobalThreadListResponse(BaseModel):
    """Response model for thread in global list."""
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str
    last_activity_at: str
    project_id: Optional[str]
    project_name: Optional[str]
    message_count: int
    model_provider: str
    conversation_mode: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedThreadsResponse(BaseModel):
    """Paginated threads response."""
    threads: List[GlobalThreadListResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# Global Thread Endpoints (all user threads across projects)
# ============================================================================

@router.get("/threads", response_model=PaginatedThreadsResponse)
async def list_all_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all threads for current user across all projects.

    Includes project-less threads. Sorted by last_activity_at DESC.

    Args:
        page: Page number (1-indexed)
        page_size: Number of threads per page (max 50)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Paginated list of threads with project info
    """
    user_id = current_user["user_id"]

    # Query: threads owned directly (user_id) OR via project (project.user_id)
    base_query = (
        select(Thread)
        .outerjoin(Project, Thread.project_id == Project.id)
        .where(
            (Thread.user_id == user_id) |
            (Project.user_id == user_id)
        )
        .options(selectinload(Thread.project), selectinload(Thread.messages))
        .order_by(Thread.last_activity_at.desc())
    )

    # Count total matching threads
    count_subquery = (
        select(Thread.id)
        .outerjoin(Project, Thread.project_id == Project.id)
        .where((Thread.user_id == user_id) | (Project.user_id == user_id))
    ).subquery()
    count_stmt = select(func.count()).select_from(count_subquery)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * page_size
    paginated = base_query.offset(offset).limit(page_size)
    result = await db.execute(paginated)
    threads = result.scalars().unique().all()

    return PaginatedThreadsResponse(
        threads=[
            GlobalThreadListResponse(
                id=t.id,
                title=t.title,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
                last_activity_at=t.last_activity_at.isoformat() if t.last_activity_at else t.updated_at.isoformat(),
                project_id=t.project_id,
                project_name=t.project.name if t.project else None,
                message_count=len(t.messages),
                model_provider=t.model_provider or "anthropic",
                conversation_mode=t.conversation_mode,
            )
            for t in threads
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(threads)) < total,
    )


@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_global_thread(
    thread_data: GlobalThreadCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create thread, optionally within a project.

    If project_id is null, creates a project-less thread owned directly by user.

    Args:
        thread_data: Thread creation data (optional title, optional project_id)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Created thread with ID, project_id (or None), title, timestamps

    Raises:
        404: Project not found or doesn't belong to user
        400: Invalid provider
    """
    user_id = current_user["user_id"]

    # Validate project if provided
    if thread_data.project_id:
        stmt = select(Project).where(
            Project.id == thread_data.project_id,
            Project.user_id == user_id
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Project not found")

    # Validate provider
    if thread_data.model_provider and thread_data.model_provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Valid options: {', '.join(VALID_PROVIDERS)}"
        )

    # Validate conversation mode if provided
    if thread_data.conversation_mode and thread_data.conversation_mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Valid options: {', '.join(VALID_MODES)}"
        )

    # Create thread
    # If project_id is None, set user_id for direct ownership
    # If project_id is set, user_id stays None (owned via project)
    thread = Thread(
        project_id=thread_data.project_id,
        user_id=user_id if thread_data.project_id is None else None,
        title=thread_data.title or "New Chat",
        model_provider=thread_data.model_provider or "anthropic",
        conversation_mode=thread_data.conversation_mode,
        last_activity_at=datetime.utcnow()
    )

    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    return ThreadResponse(
        id=thread.id,
        project_id=thread.project_id,
        title=thread.title,
        model_provider=thread.model_provider or "anthropic",
        conversation_mode=thread.conversation_mode,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
    )


# ============================================================================
# Project-scoped Thread Endpoints (legacy, within specific project)
# ============================================================================

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

    # Validate provider if provided
    if thread_data.model_provider and thread_data.model_provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Valid options: {', '.join(VALID_PROVIDERS)}"
        )

    # Validate conversation mode if provided
    if thread_data.conversation_mode and thread_data.conversation_mode not in VALID_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode. Valid options: {', '.join(VALID_MODES)}"
        )

    # Create thread
    thread = Thread(
        project_id=project_id,
        title=thread_data.title,
        model_provider=thread_data.model_provider or "anthropic",
        conversation_mode=thread_data.conversation_mode,
        last_activity_at=datetime.utcnow()
    )

    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    return ThreadResponse(
        id=thread.id,
        project_id=thread.project_id,
        title=thread.title,
        model_provider=thread.model_provider or "anthropic",
        conversation_mode=thread.conversation_mode,
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
            model_provider=thread.model_provider or "anthropic",
            conversation_mode=thread.conversation_mode,
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
        404: Thread not found or doesn't belong to user
    """
    user_id = current_user["user_id"]

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

    # Validate ownership: project-less threads check user_id, project threads check project.user_id
    if thread.project_id is None:
        if thread.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
    else:
        if thread.project.user_id != user_id:
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
        model_provider=thread.model_provider or "anthropic",
        conversation_mode=thread.conversation_mode,
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


@router.patch(
    "/threads/{thread_id}",
    response_model=ThreadResponse,
)
async def update_thread(
    thread_id: str,
    update_data: ThreadUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update thread title and/or associate with project.

    Args:
        thread_id: ID of the thread to update
        update_data: Thread update data (title and/or project_id)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Updated thread with new title/project_id and timestamps

    Raises:
        404: Thread not found or doesn't belong to user
        400: Thread already associated with a project (re-association not allowed)
        400: Title exceeds 255 characters (handled by Pydantic)
    """
    user_id = current_user["user_id"]

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

    # Validate ownership: project-less threads check user_id, project threads check project.user_id
    if thread.project_id is None:
        if thread.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
    else:
        if thread.project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )

    # Handle project association
    if update_data.project_id is not None:
        # Prevent re-association (permanent, one-way)
        if thread.project_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thread already associated with a project"
            )

        # Validate project ownership
        stmt = select(Project).where(
            Project.id == update_data.project_id,
            Project.user_id == user_id
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Transition ownership model
        thread.project_id = update_data.project_id
        thread.user_id = None  # Clear direct ownership

    # Handle title update (existing logic)
    if update_data.title is not None:
        thread.title = update_data.title

    # Handle conversation mode update
    if update_data.conversation_mode is not None:
        if update_data.conversation_mode not in VALID_MODES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode. Valid options: {', '.join(VALID_MODES)}"
            )
        thread.conversation_mode = update_data.conversation_mode

    await db.commit()
    await db.refresh(thread)

    return ThreadResponse(
        id=thread.id,
        project_id=thread.project_id,
        title=thread.title,
        model_provider=thread.model_provider or "anthropic",
        conversation_mode=thread.conversation_mode,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
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
        404: Thread not found or doesn't belong to user
    """
    user_id = current_user["user_id"]

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

    # Validate ownership: project-less threads check user_id, project threads check project.user_id
    if thread.project_id is None:
        if thread.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
    else:
        if thread.project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )

    # Delete thread (cascades to messages, artifacts)
    await db.delete(thread)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
