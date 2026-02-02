"""Contract tests for Artifacts API routes.

Tests verify correct status codes, response schemas, and error handling
for artifact endpoints.

Coverage:
- GET /api/threads/{id}/artifacts (list artifacts for thread)
- GET /api/artifacts/{id} (get artifact with content)
- GET /api/artifacts/{id}/export/{format} (export artifact)
"""

import sys
from datetime import datetime
from uuid import uuid4

import pytest

from app.models import (
    Artifact,
    ArtifactType,
    OAuthProvider,
    Project,
    Thread,
    User,
)
from app.utils.jwt import create_access_token


class TestListThreadArtifacts:
    """Contract tests for GET /api/threads/{id}/artifacts."""

    @pytest.mark.asyncio
    async def test_200_returns_array(self, client, db_session):
        """Returns array of artifacts for thread."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="Test BRD",
            content_markdown="# Test\n\nContent",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/threads/{thread.id}/artifacts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Test BRD"

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        response = await client.get(f"/api/threads/{uuid4()}/artifacts")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_thread_not_found(self, client, db_session):
        """Returns 404 for non-existent thread."""
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
            f"/api/threads/{uuid4()}/artifacts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_thread_not_owned(self, client, db_session):
        """Returns 404 for thread owned by another user."""
        # Create owner with project and thread
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Owner's Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
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
            f"/api/threads/{thread.id}/artifacts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_empty_list_no_artifacts(self, client, db_session):
        """Returns empty array when thread has no artifacts."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Empty Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/threads/{thread.id}/artifacts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_response_schema(self, client, db_session):
        """Response items have correct schema fields."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.USER_STORIES,
            title="User Stories",
            content_markdown="# Stories",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/threads/{thread.id}/artifacts",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        item = data[0]
        # Lightweight list items don't include content
        assert "id" in item
        assert "thread_id" in item
        assert "artifact_type" in item
        assert "title" in item
        assert "created_at" in item


class TestGetArtifact:
    """Contract tests for GET /api/artifacts/{id}."""

    @pytest.mark.asyncio
    async def test_200_with_content(self, client, db_session):
        """Returns artifact with full content."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="Test BRD",
            content_markdown="# Business Requirements\n\n## Overview\n\nTest content",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/artifacts/{artifact.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test BRD"
        assert "# Business Requirements" in data["content_markdown"]
        assert data["artifact_type"] == "brd"

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        response = await client.get(f"/api/artifacts/{uuid4()}")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, client, db_session):
        """Returns 404 for non-existent artifact."""
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
            f"/api/artifacts/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_404_not_owned(self, client, db_session):
        """Returns 404 for artifact owned by another user."""
        # Create owner with full hierarchy
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Owner's Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="Secret BRD",
            content_markdown="Confidential",
        )
        db_session.add(artifact)
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
            f"/api/artifacts/{artifact.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_response_schema(self, client, db_session):
        """Response has required schema fields."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="Schema Test",
            content_markdown="Content here",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/artifacts/{artifact.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # Full artifact response includes content
        assert "id" in data
        assert "thread_id" in data
        assert "artifact_type" in data
        assert "title" in data
        assert "content_markdown" in data
        assert "created_at" in data


class TestExportArtifact:
    """Contract tests for GET /api/artifacts/{id}/export/{format}."""

    @pytest.mark.asyncio
    async def test_200_export_markdown(self, client, db_session):
        """Returns markdown file with Content-Disposition header."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="Export Test",
            content_markdown="# Test Export\n\nContent here",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/artifacts/{artifact.id}/export/md",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".md" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_200_export_docx(self, client, db_session):
        """Returns docx file with proper content type."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="DOCX Export",
            content_markdown="# Word Doc\n\nContent",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/artifacts/{artifact.id}/export/docx",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "Content-Disposition" in response.headers
        assert ".docx" in response.headers["Content-Disposition"]
        # Check content type for Word documents
        content_type = response.headers.get("content-type", "")
        assert "application/vnd.openxmlformats" in content_type or "docx" in content_type.lower()

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="PDF export requires GTK which is not available on Windows"
    )
    async def test_200_export_pdf(self, client, db_session):
        """Returns PDF file with proper content type (Linux/Mac only)."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="PDF Export",
            content_markdown="# PDF\n\nContent",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/artifacts/{artifact.id}/export/pdf",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert ".pdf" in response.headers["Content-Disposition"]

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        response = await client.get(f"/api/artifacts/{uuid4()}/export/md")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, client, db_session):
        """Returns 404 for non-existent artifact."""
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
            f"/api/artifacts/{uuid4()}/export/md",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_content_disposition_header(self, client, db_session):
        """Response has Content-Disposition with sanitized filename."""
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        # Artifact with special characters in title
        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="Test Artifact (v1.0)",
            content_markdown="Content",
        )
        db_session.add(artifact)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/artifacts/{artifact.id}/export/md",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in disposition
        # Filename is sanitized (no special chars like parentheses)
        assert "filename=" in disposition

    @pytest.mark.asyncio
    async def test_404_not_owned(self, client, db_session):
        """Returns 404 when exporting artifact owned by another user."""
        # Create owner with full hierarchy
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

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Owner's Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        artifact = Artifact(
            id=str(uuid4()),
            thread_id=thread.id,
            artifact_type=ArtifactType.BRD,
            title="Secret Artifact",
            content_markdown="Confidential",
        )
        db_session.add(artifact)
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
            f"/api/artifacts/{artifact.id}/export/md",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
