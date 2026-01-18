"""
Document management routes.

Handles file upload, listing, viewing, and search for project documents.
"""

from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Document, Project, User
from app.routes.auth import get_current_user
from app.services.encryption import get_encryption_service
from app.services.document_search import index_document, search_documents


router = APIRouter()

# File upload constraints
MAX_FILE_SIZE = 1024 * 1024  # 1MB
ALLOWED_CONTENT_TYPES = ["text/plain", "text/markdown"]


@router.post("/projects/{project_id}/documents", status_code=201)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to a project.

    Only text files (.txt, .md) are allowed, max 1MB.
    Content is encrypted at rest and indexed for full-text search.
    """
    # Verify project exists and belongs to current user
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user["user_id"]
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files allowed"
        )

    # Read and validate size
    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large (max 1MB)"
        )

    # Decode UTF-8 content
    try:
        plaintext = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 text"
        )

    # Encrypt content
    encrypted = get_encryption_service().encrypt_document(plaintext)

    # Create document record
    doc = Document(
        project_id=project_id,
        filename=file.filename or "untitled.txt",
        content_encrypted=encrypted
    )
    db.add(doc)
    await db.flush()  # Get doc.id

    # Index for search (in same transaction)
    await index_document(db, doc.id, doc.filename, plaintext)

    await db.commit()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "created_at": doc.created_at.isoformat()
    }


@router.get("/projects/{project_id}/documents")
async def list_documents(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents in a project.

    Returns metadata only (no content) ordered by creation date.
    """
    # Verify project ownership
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user["user_id"]
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get documents
    stmt = select(Document).where(
        Document.project_id == project_id
    ).order_by(Document.created_at.desc())

    result = await db.execute(stmt)
    documents = result.scalars().all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "created_at": doc.created_at.isoformat()
        }
        for doc in documents
    ]


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get document content.

    Verifies user owns the project containing the document.
    Content is decrypted before returning.
    """
    # Get document with project join to verify ownership
    stmt = select(Document).join(Project).where(
        Document.id == document_id,
        Project.user_id == current_user["user_id"]
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Decrypt content
    plaintext = get_encryption_service().decrypt_document(doc.content_encrypted)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "content": plaintext,
        "created_at": doc.created_at.isoformat()
    }


@router.get("/projects/{project_id}/documents/search")
async def search_project_documents(
    project_id: str,
    q: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search documents within a project using full-text search.

    Returns ranked results with snippets and BM25 relevance scores.
    """
    # Verify project ownership
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user["user_id"]
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Search documents
    results = await search_documents(db, project_id, q)

    return [
        {
            "id": doc_id,
            "filename": filename,
            "snippet": snippet,
            "score": score
        }
        for doc_id, filename, snippet, score in results
    ]
