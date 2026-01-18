"""Integration tests for document management endpoints."""

from io import BytesIO
from uuid import uuid4

import pytest
from sqlalchemy import select, text

from app.models import Document, OAuthProvider, Project, User
from app.services.encryption import get_encryption_service
from app.utils.jwt import create_access_token


class TestDocumentUpload:
    """Test document upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_document(self, client, db_session):
        """Test uploading a valid text document."""
        # Create test user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Create file upload
        file_content = b"User must be able to reset password via email"
        files = {
            "file": ("requirements.txt", BytesIO(file_content), "text/plain")
        }

        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "requirements.txt"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_upload_document_invalid_type(self, client, db_session):
        """Test that uploading non-text file is rejected."""
        # Create test user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Try to upload PDF file
        file_content = b"%PDF-1.4 fake pdf content"
        files = {
            "file": ("document.pdf", BytesIO(file_content), "application/pdf")
        }

        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 400
        assert "Only .txt and .md files allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_document_too_large(self, client, db_session):
        """Test that files larger than 1MB are rejected."""
        # Create test user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Create file larger than 1MB
        file_content = b"x" * (1024 * 1024 + 1)  # 1MB + 1 byte
        files = {
            "file": ("large.txt", BytesIO(file_content), "text/plain")
        }

        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]


class TestDocumentList:
    """Test document listing functionality."""

    @pytest.mark.asyncio
    async def test_list_documents(self, client, db_session):
        """Test listing documents in a project."""
        # Create test user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()

        # Add two documents
        encryption_service = get_encryption_service()
        doc1 = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="requirements.txt",
            content_encrypted=encryption_service.encrypt_document("Requirements content"),
        )
        doc2 = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="design-notes.md",
            content_encrypted=encryption_service.encrypt_document("Design notes content"),
        )
        db_session.add(doc1)
        db_session.add(doc2)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # List documents
        response = await client.get(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        filenames = [doc["filename"] for doc in data]
        assert "requirements.txt" in filenames
        assert "design-notes.md" in filenames


class TestDocumentContent:
    """Test document content retrieval."""

    @pytest.mark.asyncio
    async def test_get_document_content(self, client, db_session):
        """Test getting document content returns decrypted text."""
        # Create test user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()

        # Add document
        plaintext = "User must be able to reset password via email"
        encryption_service = get_encryption_service()
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="requirements.txt",
            content_encrypted=encryption_service.encrypt_document(plaintext),
        )
        db_session.add(doc)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Get document content
        response = await client.get(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "requirements.txt"
        assert data["content"] == plaintext

    @pytest.mark.asyncio
    async def test_document_encrypted_at_rest(self, db_session):
        """Test that document content is stored encrypted in database."""
        # Create test user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()

        # Add document with known plaintext
        plaintext = "Sensitive password reset requirements"
        encryption_service = get_encryption_service()
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="requirements.txt",
            content_encrypted=encryption_service.encrypt_document(plaintext),
        )
        db_session.add(doc)
        await db_session.commit()

        # Query database directly to verify encryption
        stmt = select(Document.content_encrypted).where(Document.id == doc.id)
        result = await db_session.execute(stmt)
        encrypted_bytes = result.scalar_one()

        # Verify it's bytes (not string)
        assert isinstance(encrypted_bytes, bytes)
        # Verify it's not plaintext (plaintext should not appear in encrypted data)
        assert plaintext.encode() not in encrypted_bytes


class TestDocumentSearch:
    """Test full-text search functionality."""

    @pytest.mark.asyncio
    async def test_search_documents(self, client, db_session):
        """Test searching documents returns relevant results with snippets."""
        # Create test user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()

        # Upload document via API to ensure FTS5 indexing
        token = create_access_token(user.id, user.email)
        file_content = b"User must be able to reset password via email"
        files = {
            "file": ("requirements.txt", BytesIO(file_content), "text/plain")
        }

        upload_response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )
        assert upload_response.status_code == 201

        # Search for "password"
        response = await client.get(
            f"/api/projects/{project.id}/documents/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": "password"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # First result should be our document
        assert data[0]["filename"] == "requirements.txt"
        # Snippet should contain the search term
        assert "password" in data[0]["snippet"].lower()
        # Should have a score
        assert "score" in data[0]


class TestDocumentIsolation:
    """Test document access isolation between projects."""

    @pytest.mark.asyncio
    async def test_document_isolation(self, client, db_session):
        """Test that users cannot access documents from other users' projects."""
        # Create two users
        user1 = User(
            id=str(uuid4()),
            email="user1@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_user1",
        )
        user2 = User(
            id=str(uuid4()),
            email="user2@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_user2",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        # Create project for user1
        project1 = Project(
            id=str(uuid4()),
            user_id=user1.id,
            name="User1 Project",
        )
        db_session.add(project1)
        await db_session.commit()

        # Add document to user1's project
        encryption_service = get_encryption_service()
        doc1 = Document(
            id=str(uuid4()),
            project_id=project1.id,
            filename="secret.txt",
            content_encrypted=encryption_service.encrypt_document("Secret content"),
        )
        db_session.add(doc1)
        await db_session.commit()

        # User2 tries to access user1's document
        token2 = create_access_token(user2.id, user2.email)
        response = await client.get(
            f"/api/documents/{doc1.id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        # Should return 404 (not found) to avoid leaking document existence
        assert response.status_code == 404
