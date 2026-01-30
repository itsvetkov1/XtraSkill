"""
Project CRUD endpoints.

Provides create, read, list, and update operations for projects.
All endpoints require authentication and enforce project ownership.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Project
from app.utils.jwt import get_current_user

router = APIRouter()


# Request/Response schemas
class ProjectCreate(BaseModel):
    """Request schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Request schema for updating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Response schema for project data."""
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Response schema for project with related data."""
    documents: List[dict] = []
    threads: List[dict] = []


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project.

    Args:
        project_data: Project name and optional description
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Created project with id, timestamps

    Raises:
        401: If user not authenticated
    """
    # Create project owned by current user
    project = Project(
        user_id=current_user["user_id"],
        name=project_data.name,
        description=project_data.description,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all projects owned by the current user.

    Args:
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        List of projects ordered by updated_at DESC (most recent first)

    Raises:
        401: If user not authenticated
    """
    # Query projects owned by current user
    stmt = (
        select(Project)
        .where(Project.user_id == current_user["user_id"])
        .order_by(Project.updated_at.desc())
    )

    result = await db.execute(stmt)
    projects = result.scalars().all()

    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get project details with documents and threads.

    Args:
        project_id: Project UUID
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Project with documents and threads arrays

    Raises:
        401: If user not authenticated
        404: If project not found or not owned by user
    """
    # Query project with eager-loaded relationships
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.documents),
            selectinload(Project.threads),
        )
    )

    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    # Verify project exists and is owned by current user
    if not project or project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Serialize documents and threads
    documents = [
        {
            "id": doc.id,
            "filename": doc.filename,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in project.documents
    ]

    threads = [
        {
            "id": thread.id,
            "title": thread.title,
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
        }
        for thread in project.threads
    ]

    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        documents=documents,
        threads=threads,
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update project name and description.

    Args:
        project_id: Project UUID
        project_data: Updated name and description
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Updated project

    Raises:
        401: If user not authenticated
        404: If project not found or not owned by user
    """
    # Query project
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    # Verify project exists and is owned by current user
    if not project or project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Update fields
    project.name = project_data.name
    project.description = project_data.description
    # updated_at will be automatically updated by onupdate

    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a project and all related data.

    Cascades to delete all threads, documents, and messages via database
    foreign key constraints (ON DELETE CASCADE).

    Args:
        project_id: Project UUID
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        401: If user not authenticated
        404: If project not found or not owned by user
    """
    # Query project
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    # Verify project exists and is owned by current user
    if not project or project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Delete project (cascades to threads, documents, messages)
    await db.delete(project)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
