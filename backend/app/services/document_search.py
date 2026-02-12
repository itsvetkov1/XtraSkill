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
    query: str
) -> List[Tuple[str, str, str, float]]:
    """
    Search documents within a project using FTS5.

    Args:
        db: Database session
        project_id: Project ID to search within
        query: Search query (FTS5 syntax)

    Returns:
        List of tuples: (document_id, filename, snippet, score)
        Results ordered by BM25 relevance score (higher is better)
    """
    # Skip search for project-less chats or empty queries
    if not project_id or not query or not query.strip():
        return []

    # Sanitize query: bare '*' is invalid FTS5 syntax
    cleaned = query.strip()
    if cleaned == '*' or cleaned == '**':
        return []

    try:
        result = await db.execute(
        text("""
            SELECT d.id, d.filename,
                   snippet(document_fts, 2, '<mark>', '</mark>', '...', 20) as snippet,
                   bm25(document_fts, 10.0, 1.0) as score
            FROM documents d
            JOIN document_fts fts ON d.id = fts.document_id
            WHERE d.project_id = :project_id
              AND document_fts MATCH :query
            ORDER BY score
            LIMIT 20
        """),
            {"project_id": project_id, "query": cleaned}
        )
        return [(row[0], row[1], row[2], row[3]) for row in result.fetchall()]
    except Exception:
        # Invalid FTS5 query syntax — return empty rather than crash
        return []
