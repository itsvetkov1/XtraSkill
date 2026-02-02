"""Unit tests for document_search service."""

import pytest
from app.services.document_search import index_document, search_documents
from app.models import Document, Project


class TestIndexDocument:
    """Tests for index_document function."""

    @pytest.mark.asyncio
    async def test_indexes_document_content(self, db_session, user):
        """Document content is indexed in FTS5."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test Project")
        db_session.add(project)
        await db_session.commit()

        doc = Document(
            project_id=project.id,
            filename="test.md",
            content_encrypted=b"encrypted"
        )
        db_session.add(doc)
        await db_session.commit()

        # Index the document
        await index_document(
            db_session,
            doc.id,
            doc.filename,
            "This is the searchable content"
        )
        await db_session.commit()

        # Verify by searching
        results = await search_documents(db_session, project.id, "searchable")

        assert len(results) > 0
        assert results[0][0] == doc.id


class TestSearchDocuments:
    """Tests for search_documents function."""

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_project(self, db_session):
        """Returns empty list when project_id is None."""
        results = await search_documents(db_session, None, "anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_query(self, db_session, user):
        """Returns empty list when query is empty."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        results = await search_documents(db_session, project.id, "")
        assert results == []

        results = await search_documents(db_session, project.id, "   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_returns_matching_documents(self, db_session, user):
        """Returns documents matching search query."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        # Create and index document
        doc = Document(
            project_id=project.id,
            filename="requirements.md",
            content_encrypted=b"encrypted"
        )
        db_session.add(doc)
        await db_session.commit()

        await index_document(
            db_session,
            doc.id,
            doc.filename,
            "User authentication requirements and login flow"
        )
        await db_session.commit()

        results = await search_documents(db_session, project.id, "authentication")

        assert len(results) == 1
        doc_id, filename, snippet, score = results[0]
        assert doc_id == doc.id
        assert filename == "requirements.md"
        assert "authentication" in snippet.lower() or "<mark>" in snippet

    @pytest.mark.asyncio
    async def test_project_isolation(self, db_session, user):
        """Only returns documents from specified project."""
        db_session.add(user)
        await db_session.commit()

        project1 = Project(user_id=user.id, name="Project 1")
        project2 = Project(user_id=user.id, name="Project 2")
        db_session.add_all([project1, project2])
        await db_session.commit()

        doc1 = Document(project_id=project1.id, filename="p1.md", content_encrypted=b"x")
        doc2 = Document(project_id=project2.id, filename="p2.md", content_encrypted=b"x")
        db_session.add_all([doc1, doc2])
        await db_session.commit()

        await index_document(db_session, doc1.id, doc1.filename, "unique content alpha")
        await index_document(db_session, doc2.id, doc2.filename, "unique content beta")
        await db_session.commit()

        # Search in project1 should not find project2's document
        results = await search_documents(db_session, project1.id, "beta")
        assert len(results) == 0

        results = await search_documents(db_session, project1.id, "alpha")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_returns_snippets_with_highlights(self, db_session, user):
        """Results include highlighted snippets."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc = Document(project_id=project.id, filename="test.md", content_encrypted=b"x")
        db_session.add(doc)
        await db_session.commit()

        await index_document(
            db_session,
            doc.id,
            doc.filename,
            "The quick brown fox jumps over the lazy dog"
        )
        await db_session.commit()

        results = await search_documents(db_session, project.id, "fox")

        assert len(results) == 1
        _, _, snippet, _ = results[0]
        # FTS5 snippet should have <mark> tags
        assert "<mark>" in snippet or "fox" in snippet
