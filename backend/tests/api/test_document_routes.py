"""Contract tests for Documents API routes.

Tests verify correct status codes, response schemas, and error handling
for all document endpoints.

Coverage:
- POST /api/projects/{id}/documents (upload)
- GET /api/projects/{id}/documents (list)
- GET /api/documents/{id} (get with content)
- GET /api/projects/{id}/documents/search (search)
- DELETE /api/documents/{id} (delete)
"""

from io import BytesIO
from uuid import uuid4

import pytest

from app.models import Document, OAuthProvider, Project, User
from app.services.encryption import get_encryption_service
from app.utils.jwt import create_access_token


class TestUploadDocument:
    """Contract tests for POST /api/projects/{id}/documents."""

    @pytest.mark.asyncio
    async def test_201_upload_text_file(self, client, db_session):
        """Returns 201 on successful text file upload."""
        # Create user and project
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Upload file
        files = {"file": ("test.txt", BytesIO(b"Hello World"), "text/plain")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_201_upload_markdown_file(self, client, db_session):
        """Returns 201 on successful markdown file upload."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Upload markdown file
        files = {"file": ("readme.md", BytesIO(b"# Title\n\nContent"), "text/markdown")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "readme.md"

    @pytest.mark.asyncio
    async def test_400_invalid_content_type(self, client, db_session):
        """Returns 400 for non-text files."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        files = {"file": ("test.pdf", BytesIO(b"PDF content"), "application/pdf")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 400
        assert "Only .txt and .md files allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_413_file_too_large(self, client, db_session):
        """Returns 413 for files over 1MB."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Create file > 1MB
        large_content = b"x" * (1024 * 1024 + 1)
        files = {"file": ("large.txt", BytesIO(large_content), "text/plain")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_400_invalid_utf8(self, client, db_session):
        """Returns 400 for binary (non-UTF8) file content."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Invalid UTF-8 bytes
        binary_content = b"\x80\x81\x82\x83"
        files = {"file": ("binary.txt", BytesIO(binary_content), "text/plain")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 400
        assert "File must be valid UTF-8 text" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        project_id = str(uuid4())
        files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}

        response = await client.post(
            f"/api/projects/{project_id}/documents",
            files=files,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_project_not_found(self, client, db_session):
        """Returns 404 for non-existent project."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
        response = await client.post(
            f"/api/projects/{str(uuid4())}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_project_not_owned(self, client, db_session):
        """Returns 404 for project owned by another user."""
        # Create owner user
        owner = User(
            id=str(uuid4()),
            email="owner@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_owner",
        )
        db_session.add(owner)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=owner.id,
            name="Owner's Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Create different user
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        token = create_access_token(other_user.id, other_user.email)

        files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_response_schema(self, client, db_session):
        """Response has required fields: id, filename, created_at."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        # Verify all required fields
        assert "id" in data
        assert "filename" in data
        assert "created_at" in data
        # Verify types
        assert isinstance(data["id"], str)
        assert isinstance(data["filename"], str)
        assert isinstance(data["created_at"], str)


class TestListDocuments:
    """Contract tests for GET /api/projects/{id}/documents."""

    @pytest.mark.asyncio
    async def test_200_returns_array(self, client, db_session):
        """Returns 200 with array of documents."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Add a document
        encrypted = get_encryption_service().encrypt_document("Test content")
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="test.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        project_id = str(uuid4())

        response = await client.get(f"/api/projects/{project_id}/documents")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_project_not_found(self, client, db_session):
        """Returns 404 for non-existent project."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/projects/{str(uuid4())}/documents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_empty_list_for_new_project(self, client, db_session):
        """Returns empty array for project with no documents."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Empty Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestGetDocument:
    """Contract tests for GET /api/documents/{id}."""

    @pytest.mark.asyncio
    async def test_200_with_content(self, client, db_session):
        """Returns document with decrypted content."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Create document with encrypted content
        plaintext = "Test content here"
        encrypted = get_encryption_service().encrypt_document(plaintext)
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="test.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test content here"
        assert data["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        doc_id = str(uuid4())

        response = await client.get(f"/api/documents/{doc_id}")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, client, db_session):
        """Returns 404 for non-existent document."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/documents/{str(uuid4())}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_not_owned(self, client, db_session):
        """Returns 404 for document owned by another user."""
        # Create owner with project and document
        owner = User(
            id=str(uuid4()),
            email="owner@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_owner",
        )
        db_session.add(owner)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=owner.id,
            name="Owner's Project",
        )
        db_session.add(project)
        await db_session.commit()

        encrypted = get_encryption_service().encrypt_document("Secret content")
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="secret.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()

        # Create different user
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        token = create_access_token(other_user.id, other_user.email)

        response = await client.get(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_response_schema(self, client, db_session):
        """Response has required fields: id, filename, content, created_at."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        encrypted = get_encryption_service().encrypt_document("content")
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="test.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # Verify required fields
        assert "id" in data
        assert "filename" in data
        assert "content" in data
        assert "created_at" in data


class TestSearchDocuments:
    """Contract tests for GET /api/projects/{id}/documents/search."""

    @pytest.mark.asyncio
    async def test_200_with_results(self, client, db_session):
        """Returns matching documents from search."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Upload a document to create the FTS entry
        token = create_access_token(user.id, user.email)
        files = {"file": ("requirements.txt", BytesIO(b"The system must authenticate users"), "text/plain")}
        upload_resp = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )
        assert upload_resp.status_code == 201

        # Search for the content
        response = await client.get(
            f"/api/projects/{project.id}/documents/search?q=authenticate",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "id" in data[0]
        assert "filename" in data[0]

    @pytest.mark.asyncio
    async def test_200_empty_results(self, client, db_session):
        """Returns empty array when no matches found."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/projects/{project.id}/documents/search?q=nonexistentterm",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        project_id = str(uuid4())

        response = await client.get(
            f"/api/projects/{project_id}/documents/search?q=test"
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_project_not_found(self, client, db_session):
        """Returns 404 for non-existent project."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/projects/{str(uuid4())}/documents/search?q=test",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestDeleteDocument:
    """Contract tests for DELETE /api/documents/{id}."""

    @pytest.mark.asyncio
    async def test_204_deletes_document(self, client, db_session):
        """Returns 204 on successful deletion."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        encrypted = get_encryption_service().encrypt_document("to delete")
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="delete-me.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.delete(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

        # Verify document is deleted
        get_resp = await client.get(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        doc_id = str(uuid4())

        response = await client.delete(f"/api/documents/{doc_id}")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, client, db_session):
        """Returns 404 for non-existent document."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.delete(
            f"/api/documents/{str(uuid4())}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_not_owned(self, client, db_session):
        """Returns 404 for document owned by another user."""
        # Create owner with document
        owner = User(
            id=str(uuid4()),
            email="owner@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_owner",
        )
        db_session.add(owner)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=owner.id,
            name="Owner's Project",
        )
        db_session.add(project)
        await db_session.commit()

        encrypted = get_encryption_service().encrypt_document("secret")
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="secret.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()

        # Create different user
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        token = create_access_token(other_user.id, other_user.email)

        response = await client.delete(
            f"/api/documents/{doc.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
