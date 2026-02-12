"""
Document management routes.

Handles file upload, listing, viewing, and search for project documents.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Response, status, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Document, Project, User
from app.routes.auth import get_current_user
from app.services.encryption import get_encryption_service
from app.services.document_search import index_document, search_documents
from app.services.document_parser import ParserFactory
from app.services.file_validator import validate_file_security


router = APIRouter()

# File upload constraints — rich documents up to 10MB
ALLOWED_CONTENT_TYPES = ParserFactory.ALL_CONTENT_TYPES


@router.post("/projects/{project_id}/documents", status_code=201)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to a project.

    Supports .txt, .md, .xlsx, .csv, .pdf, .docx files, max 10MB.
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
            detail="Unsupported file type. Supported: .txt, .md, .xlsx, .csv, .pdf, .docx"
        )

    # Read file bytes
    content_bytes = await file.read()

    # Security validation (size, magic numbers, zip bombs)
    validate_file_security(content_bytes, file.content_type)

    # Get parser for content type
    parser = ParserFactory.get_parser(file.content_type)

    # Format-specific security validation
    parser.validate_security(content_bytes)

    # Parse document to extract text and metadata
    try:
        parsed = parser.parse(content_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse document: {str(e)}"
        )

    # Encrypt for storage
    if ParserFactory.is_rich_format(file.content_type):
        # Rich formats — store original binary
        encrypted = get_encryption_service().encrypt_binary(content_bytes)
    else:
        # Text formats — store plaintext (backward compatible)
        encrypted = get_encryption_service().encrypt_document(parsed["text"])

    # Create document record with dual-column storage
    doc = Document(
        project_id=project_id,
        filename=file.filename or "untitled",
        content_type=file.content_type,
        content_encrypted=encrypted,
        content_text=parsed["text"],
        metadata_json=json.dumps(parsed["metadata"]) if parsed["metadata"] else None,
    )
    db.add(doc)
    await db.flush()  # Get doc.id

    # Index for search (in same transaction)
    await index_document(db, doc.id, doc.filename, parsed["text"])

    await db.commit()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "metadata": parsed["metadata"],
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
            "content_type": doc.content_type or "text/plain",
            "metadata": json.loads(doc.metadata_json) if doc.metadata_json else None,
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
    Returns extracted text content for all document types.
    """
    # Get document with project join to verify ownership
    stmt = select(Document).join(Project).where(
        Document.id == document_id,
        Project.user_id == current_user["user_id"]
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get content text
    if doc.content_text is not None:
        content = doc.content_text
    else:
        # Legacy document — decrypt from content_encrypted (text format)
        content = get_encryption_service().decrypt_document(doc.content_encrypted)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "content_type": doc.content_type or "text/plain",
        "content": content,
        "metadata": json.loads(doc.metadata_json) if doc.metadata_json else None,
        "created_at": doc.created_at.isoformat()
    }


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download original document file.

    For rich documents (XLSX, CSV, PDF, DOCX): returns original binary.
    For text documents: returns plain text content.
    """
    # Get document with project join to verify ownership
    stmt = select(Document).join(Project).where(
        Document.id == document_id,
        Project.user_id == current_user["user_id"]
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    content_type = doc.content_type or "text/plain"

    if ParserFactory.is_rich_format(content_type):
        # Rich document — decrypt as binary
        file_bytes = get_encryption_service().decrypt_binary(doc.content_encrypted)
        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{doc.filename}"'
            }
        )
    else:
        # Text document — decrypt as text
        plaintext = get_encryption_service().decrypt_document(doc.content_encrypted)
        return Response(
            content=plaintext.encode('utf-8'),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{doc.filename}"'
            }
        )


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


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document.

    Verifies user owns the project containing the document.

    Args:
        document_id: Document UUID
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        404: Document not found or not owned by user
    """
    # Get document with project join to verify ownership
    stmt = select(Document).join(Project).where(
        Document.id == document_id,
        Project.user_id == current_user["user_id"]
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete document
    await db.delete(doc)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
