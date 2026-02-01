"""Unit tests for document search service."""

import pytest
from sqlalchemy import text
from uuid import uuid4

from app.models import OAuthProvider, Project, Document, User
from app.services.document_search import search_documents, index_document


class TestDocumentSearch:
    """Tests for document search functionality."""

    @pytest.mark.asyncio
    async def test_search_with_empty_query_returns_empty(self, db_session):
        """Test that empty query string returns empty results (BUG-010 fix)."""
        project_id = str(uuid4())

        result = await search_documents(db_session, project_id, "")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_with_whitespace_query_returns_empty(self, db_session):
        """Test that whitespace-only query returns empty results."""
        project_id = str(uuid4())

        result = await search_documents(db_session, project_id, "   ")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_with_none_project_id_returns_empty(self, db_session):
        """Test that None project_id returns empty results (project-less chats)."""
        result = await search_documents(db_session, None, "test query")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_with_valid_query(self, db_session):
        """Test that valid search returns matching documents."""
        # Create user
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create project
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Create document with encrypted content placeholder
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="test_doc.txt",
            content_encrypted=b"encrypted_content_placeholder",
        )
        db_session.add(doc)
        await db_session.commit()

        # Index document content (FTS5 stores plaintext separately)
        await index_document(
            db_session,
            doc.id,
            "test_doc.txt",
            "This document contains important business requirements for the login feature."
        )
        await db_session.commit()

        # Search for content
        results = await search_documents(db_session, project.id, "business requirements")

        assert len(results) > 0
        assert results[0][0] == doc.id  # First result should be our document

    @pytest.mark.asyncio
    async def test_search_isolation_between_projects(self, db_session):
        """Test that search only returns documents from specified project."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create two projects
        project1 = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Project 1",
        )
        project2 = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Project 2",
        )
        db_session.add_all([project1, project2])
        await db_session.commit()

        # Create documents in each project with encrypted content placeholder
        doc1 = Document(
            id=str(uuid4()),
            project_id=project1.id,
            filename="doc1.txt",
            content_encrypted=b"encrypted_content_placeholder",
        )
        doc2 = Document(
            id=str(uuid4()),
            project_id=project2.id,
            filename="doc2.txt",
            content_encrypted=b"encrypted_content_placeholder",
        )
        db_session.add_all([doc1, doc2])
        await db_session.commit()

        # Index both documents with similar content (FTS5 stores plaintext separately)
        await index_document(db_session, doc1.id, "doc1.txt", "authentication feature")
        await index_document(db_session, doc2.id, "doc2.txt", "authentication module")
        await db_session.commit()

        # Search in project1 only
        results = await search_documents(db_session, project1.id, "authentication")

        assert len(results) == 1
        assert results[0][0] == doc1.id  # Only doc1 from project1

    @pytest.mark.asyncio
    async def test_search_no_results_for_nonexistent_project(self, db_session):
        """Test that search with non-existent project returns empty."""
        fake_project_id = str(uuid4())

        results = await search_documents(db_session, fake_project_id, "test query")

        assert results == []
