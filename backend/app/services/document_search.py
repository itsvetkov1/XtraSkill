"""
Document search service using SQLite FTS5.

Provides full-text search capabilities for project documents.
"""

from typing import List, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def index_document(
    db: AsyncSession,
    doc_id: str,
    filename: str,
    content: str
) -> None:
    """
    Index document content for full-text search.

    Args:
        db: Database session
        doc_id: Document ID (UUID)
        filename: Document filename
        content: Plaintext content to index
    """
    await db.execute(
        text("""
            INSERT INTO document_fts(document_id, filename, content)
            VALUES (:doc_id, :filename, :content)
        """),
        {"doc_id": doc_id, "filename": filename, "content": content}
    )


async def search_documents(
    db: AsyncSession,
    project_id: str,
    query: str,
    max_chunks: int = 3,  # AI-02: Token budget — limit retrieval
    thread_id: str | None = None,
) -> List[Tuple[str, str, str, float, str, str]]:
    """
    Search documents with metadata.

    Searches by project_id when available. Falls back to thread_id scope
    for assistant threads that have no project association (DOC-006).

    Args:
        db: Database session
        project_id: Project ID to search within (primary scope)
        query: Search query (FTS5 syntax)
        max_chunks: Maximum chunks to return (default 3 for token budget)
        thread_id: Thread ID to search within (fallback scope for projectless threads)

    Returns:
        List of tuples: (document_id, filename, snippet, score, content_type, metadata_json)
        Results ordered by BM25 relevance score (higher is better)
    """
    # Require at least one scope identifier and a non-empty query
    if (not project_id and not thread_id) or not query or not query.strip():
        return []

    # Sanitize query: bare '*' is invalid FTS5 syntax
    cleaned = query.strip()
    if cleaned == '*' or cleaned == '**':
        return []

    try:
        if project_id:
            # Primary: search within project scope
            result = await db.execute(
                text("""
                    SELECT d.id, d.filename,
                           snippet(document_fts, 2, '<mark>', '</mark>', '...', 20) as snippet,
                           bm25(document_fts, 10.0, 1.0) as score,
                           d.content_type,
                           d.metadata_json
                    FROM documents d
                    JOIN document_fts fts ON d.id = fts.document_id
                    WHERE d.project_id = :project_id
                      AND document_fts MATCH :query
                    ORDER BY score
                    LIMIT :max_chunks
                """),
                {"project_id": project_id, "query": cleaned, "max_chunks": max_chunks}
            )
        else:
            # Fallback: search within thread scope (DOC-006)
            result = await db.execute(
                text("""
                    SELECT d.id, d.filename,
                           snippet(document_fts, 2, '<mark>', '</mark>', '...', 20) as snippet,
                           bm25(document_fts, 10.0, 1.0) as score,
                           d.content_type,
                           d.metadata_json
                    FROM documents d
                    JOIN document_fts fts ON d.id = fts.document_id
                    WHERE d.thread_id = :thread_id
                      AND d.project_id IS NULL
                      AND document_fts MATCH :query
                    ORDER BY score
                    LIMIT :max_chunks
                """),
                {"thread_id": thread_id, "query": cleaned, "max_chunks": max_chunks}
            )
        return [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in result.fetchall()]
    except Exception:
        # Invalid FTS5 query syntax — return empty rather than crash
        return []
