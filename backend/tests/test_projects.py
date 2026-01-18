"""Integration tests for project management endpoints."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import Document, OAuthProvider, Project, Thread, User
from app.utils.jwt import create_access_token


class TestProjectCRUD:
    """Test project create, read, list, update operations."""

    @pytest.mark.asyncio
    async def test_create_project(self, client, db_session):
        """Test creating a project with valid data."""
        # Create test user
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Create project
        response = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Client Portal Redesign",
                "description": "Modernize client-facing portal",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Client Portal Redesign"
        assert data["description"] == "Modernize client-facing portal"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_project_requires_auth(self, client):
        """Test that creating project requires authentication."""
        response = await client.post(
            "/api/projects",
            json={"name": "Test Project"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_projects(self, client, db_session):
        """Test listing projects returns all user's projects."""
        # Create test user
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
            name="Project One",
        )
        project2 = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Project Two",
            description="Second project",
        )
        db_session.add(project1)
        db_session.add(project2)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # List projects
        response = await client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be ordered by updated_at DESC (most recent first)
        project_names = [p["name"] for p in data]
        assert "Project One" in project_names
        assert "Project Two" in project_names

    @pytest.mark.asyncio
    async def test_list_projects_isolation(self, client, db_session):
        """Test that users only see their own projects."""
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

        # User2 lists projects
        token2 = create_access_token(user2.id, user2.email)
        response = await client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 200
        data = response.json()
        # User2 should see empty list (no access to user1's projects)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_project(self, client, db_session):
        """Test getting project details with documents and threads."""
        # Create test user
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
            description="Test description",
        )
        db_session.add(project)
        await db_session.commit()

        # Add document (without encryption for test simplicity)
        from app.services.encryption import get_encryption_service
        encrypted = get_encryption_service().encrypt_document("test content")
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="test.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()

        # Add thread
        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Get project
        response = await client.get(
            f"/api/projects/{project.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Test Project"
        assert data["description"] == "Test description"
        assert len(data["documents"]) == 1
        assert data["documents"][0]["filename"] == "test.txt"
        assert len(data["threads"]) == 1
        assert data["threads"][0]["title"] == "Test Thread"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client, db_session):
        """Test getting non-existent project returns 404."""
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
            f"/api/projects/{str(uuid4())}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(self, client, db_session):
        """Test updating project name and description."""
        # Create test user
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
            name="Original Name",
            description="Original description",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Update project
        response = await client.put(
            f"/api/projects/{project.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated Name",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_project_not_owned(self, client, db_session):
        """Test that users cannot update projects they don't own."""
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
        project = Project(
            id=str(uuid4()),
            user_id=user1.id,
            name="User1 Project",
        )
        db_session.add(project)
        await db_session.commit()

        # User2 tries to update user1's project
        token2 = create_access_token(user2.id, user2.email)
        response = await client.put(
            f"/api/projects/{project.id}",
            headers={"Authorization": f"Bearer {token2}"},
            json={"name": "Hacked Name"},
        )

        # Should return 404 (not found) to avoid leaking project existence
        assert response.status_code == 404


class TestCascadeDelete:
    """Test cascade delete behavior for projects."""

    @pytest.mark.asyncio
    async def test_cascade_delete_project(self, db_session):
        """Test that deleting project cascades to documents and threads."""
        # Create test user
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

        # Add document
        from app.services.encryption import get_encryption_service
        encrypted = get_encryption_service().encrypt_document("test content")
        doc = Document(
            id=str(uuid4()),
            project_id=project.id,
            filename="test.txt",
            content_encrypted=encrypted,
        )
        db_session.add(doc)
        await db_session.commit()
        doc_id = doc.id

        # Add thread
        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
        )
        db_session.add(thread)
        await db_session.commit()
        thread_id = thread.id

        # Delete project manually (MVP doesn't have DELETE endpoint yet)
        await db_session.delete(project)
        await db_session.commit()

        # Verify document was cascade deleted
        stmt = select(Document).where(Document.id == doc_id)
        result = await db_session.execute(stmt)
        deleted_doc = result.scalar_one_or_none()
        assert deleted_doc is None, "Document should be cascade deleted"

        # Verify thread was cascade deleted
        stmt = select(Thread).where(Thread.id == thread_id)
        result = await db_session.execute(stmt)
        deleted_thread = result.scalar_one_or_none()
        assert deleted_thread is None, "Thread should be cascade deleted"
