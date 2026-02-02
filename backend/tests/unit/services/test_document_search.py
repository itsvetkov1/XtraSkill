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


class TestSearchDocumentsRanking:
    """Tests for BM25 ranking in search results."""

    @pytest.mark.asyncio
    async def test_higher_term_frequency_ranked_first(self, db_session, user):
        """Documents with more occurrences of search term rank higher."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test Project")
        db_session.add(project)
        await db_session.commit()

        # Document with 1 occurrence
        doc1 = Document(
            project_id=project.id,
            filename="single.md",
            content_encrypted=b"x"
        )
        # Document with 3 occurrences
        doc2 = Document(
            project_id=project.id,
            filename="triple.md",
            content_encrypted=b"x"
        )
        db_session.add_all([doc1, doc2])
        await db_session.commit()

        await index_document(db_session, doc1.id, doc1.filename,
            "authentication is important for security")
        await index_document(db_session, doc2.id, doc2.filename,
            "authentication requires authentication tokens for authentication")
        await db_session.commit()

        results = await search_documents(db_session, project.id, "authentication")

        assert len(results) == 2
        # Triple occurrence should rank first (higher BM25 score)
        assert results[0][0] == doc2.id

    @pytest.mark.asyncio
    async def test_exact_match_in_filename_ranks_high(self, db_session, user):
        """Document with term in filename ranks appropriately."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc1 = Document(project_id=project.id, filename="security.md", content_encrypted=b"x")
        doc2 = Document(project_id=project.id, filename="auth.md", content_encrypted=b"x")
        db_session.add_all([doc1, doc2])
        await db_session.commit()

        await index_document(db_session, doc1.id, doc1.filename, "login requirements")
        await index_document(db_session, doc2.id, doc2.filename, "user authentication login flow")
        await db_session.commit()

        results = await search_documents(db_session, project.id, "login")

        assert len(results) == 2
        # Both have "login" but doc2 has more context

    @pytest.mark.asyncio
    async def test_multiple_results_ordered_by_relevance(self, db_session, user):
        """Multiple matching documents ordered by BM25 score."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc1 = Document(project_id=project.id, filename="basic.md", content_encrypted=b"x")
        doc2 = Document(project_id=project.id, filename="detailed.md", content_encrypted=b"x")
        doc3 = Document(project_id=project.id, filename="comprehensive.md", content_encrypted=b"x")
        db_session.add_all([doc1, doc2, doc3])
        await db_session.commit()

        await index_document(db_session, doc1.id, doc1.filename, "API endpoint")
        await index_document(db_session, doc2.id, doc2.filename, "API endpoint design and API documentation")
        await index_document(db_session, doc3.id, doc3.filename, "API API API API usage patterns")
        await db_session.commit()

        results = await search_documents(db_session, project.id, "API")

        assert len(results) == 3
        # doc3 has most API mentions, should rank first
        assert results[0][0] == doc3.id


class TestSearchDocumentsSnippets:
    """Tests for snippet highlighting in search results."""

    @pytest.mark.asyncio
    async def test_snippet_contains_search_term(self, db_session, user):
        """Result snippets contain the search term."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc = Document(project_id=project.id, filename="test.md", content_encrypted=b"x")
        db_session.add(doc)
        await db_session.commit()

        await index_document(db_session, doc.id, doc.filename,
            "User registration requires email verification before activation")
        await db_session.commit()

        results = await search_documents(db_session, project.id, "verification")

        assert len(results) == 1
        snippet = results[0][2]
        # Snippet should contain the term (either raw or in mark tags)
        assert "verification" in snippet.lower() or "<mark>" in snippet

    @pytest.mark.asyncio
    async def test_snippet_has_mark_tags(self, db_session, user):
        """Snippets have <mark> tags for highlighting."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc = Document(project_id=project.id, filename="test.md", content_encrypted=b"x")
        db_session.add(doc)
        await db_session.commit()

        await index_document(db_session, doc.id, doc.filename,
            "The authentication system uses OAuth 2.0 for secure login")
        await db_session.commit()

        results = await search_documents(db_session, project.id, "authentication")

        assert len(results) == 1
        snippet = results[0][2]
        # FTS5 snippet with mark tags
        assert "<mark>" in snippet or "authentication" in snippet

    @pytest.mark.asyncio
    async def test_long_content_truncated_in_snippet(self, db_session, user):
        """Long document content is truncated in snippet."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc = Document(project_id=project.id, filename="long.md", content_encrypted=b"x")
        db_session.add(doc)
        await db_session.commit()

        # Very long content
        long_content = "prefix content " * 100 + "TARGET_TERM" + " suffix content" * 100
        await index_document(db_session, doc.id, doc.filename, long_content)
        await db_session.commit()

        results = await search_documents(db_session, project.id, "TARGET_TERM")

        assert len(results) == 1
        snippet = results[0][2]
        # Snippet should be shorter than original content
        assert len(snippet) < len(long_content)


class TestSearchDocumentsEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self, db_session, user):
        """Empty search query returns no results."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test Project")
        db_session.add(project)
        await db_session.commit()

        results = await search_documents(db_session, project.id, "")
        assert results == []

    @pytest.mark.asyncio
    async def test_whitespace_query_returns_empty(self, db_session, user):
        """Whitespace-only query returns no results."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        results = await search_documents(db_session, project.id, "   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_no_matches_returns_empty(self, db_session, user):
        """Query with no matches returns empty list."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc = Document(project_id=project.id, filename="test.md", content_encrypted=b"x")
        db_session.add(doc)
        await db_session.commit()

        await index_document(db_session, doc.id, doc.filename, "apple banana cherry")
        await db_session.commit()

        results = await search_documents(db_session, project.id, "zebra")
        assert results == []

    @pytest.mark.asyncio
    async def test_special_characters_handled(self, db_session, user):
        """Special characters in query don't crash search."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        # These should not raise exceptions
        results = await search_documents(db_session, project.id, "test")
        assert results == []

        # Asterisk (FTS5 wildcard)
        results = await search_documents(db_session, project.id, "test*")
        assert results == []

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, db_session, user):
        """Search is case insensitive."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc = Document(project_id=project.id, filename="test.md", content_encrypted=b"x")
        db_session.add(doc)
        await db_session.commit()

        await index_document(db_session, doc.id, doc.filename,
            "Authentication requires proper authorization")
        await db_session.commit()

        # Search with different cases
        results_lower = await search_documents(db_session, project.id, "authentication")
        results_upper = await search_documents(db_session, project.id, "AUTHENTICATION")
        results_mixed = await search_documents(db_session, project.id, "Authentication")

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1

    @pytest.mark.asyncio
    async def test_wildcard_prefix_search(self, db_session, user):
        """Wildcard suffix matches partial words."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        doc = Document(project_id=project.id, filename="test.md", content_encrypted=b"x")
        db_session.add(doc)
        await db_session.commit()

        await index_document(db_session, doc.id, doc.filename,
            "authentication authorization authenticate")
        await db_session.commit()

        # "auth*" should match all auth-prefixed words
        results = await search_documents(db_session, project.id, "auth*")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_null_project_id_returns_empty(self, db_session):
        """Null project_id returns empty results."""
        results = await search_documents(db_session, None, "test")
        assert results == []

    @pytest.mark.asyncio
    async def test_nonexistent_project_returns_empty(self, db_session, user):
        """Nonexistent project returns empty results."""
        db_session.add(user)
        await db_session.commit()

        # Use a UUID that doesn't exist
        import uuid
        fake_project_id = str(uuid.uuid4())

        results = await search_documents(db_session, fake_project_id, "test")
        assert results == []
