"""Integration tests for thread management endpoints."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import OAuthProvider, Project, Thread, User
from app.utils.jwt import create_access_token


class TestThreadEndpoints:
    """Test thread CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_thread_with_title(self, client, db_session):
        """Test creating a thread with a title."""
        # Create test user
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create test project
        project = Project(
            id=str(uuid4()),
            user_id=user.id,
            name="Test Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Generate auth token
        token = create_access_token(user.id, user.email)

        # Create thread
        response = await client.post(
            f"/api/projects/{project.id}/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Login Flow Discussion"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Login Flow Discussion"
        assert data["project_id"] == project.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_thread_without_title(self, client, db_session):
        """Test creating a thread without a title (nullable)."""
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

        # Create thread with null title
        response = await client.post(
            f"/api/projects/{project.id}/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] is None
        assert data["project_id"] == project.id

    @pytest.mark.asyncio
    async def test_create_thread_project_not_found(self, client, db_session):
        """Test creating thread for non-existent project returns 404."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.post(
            f"/api/projects/{str(uuid4())}/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_threads_ordered_by_date(self, client, db_session):
        """Test listing threads returns them ordered by created_at DESC."""
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

        # Create multiple threads
        import time
        thread1 = Thread(id=str(uuid4()), project_id=project.id, title="First Thread")
        db_session.add(thread1)
        await db_session.commit()
        time.sleep(0.01)  # Ensure distinct timestamps
        
        thread2 = Thread(id=str(uuid4()), project_id=project.id, title="Second Thread")
        db_session.add(thread2)
        await db_session.commit()
        time.sleep(0.01)  # Ensure distinct timestamps
        
        thread3 = Thread(id=str(uuid4()), project_id=project.id, title="Third Thread")
        db_session.add(thread3)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # List threads
        response = await client.get(
            f"/api/projects/{project.id}/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered newest first
        assert data[0]["title"] == "Third Thread"
        assert data[1]["title"] == "Second Thread"
        assert data[2]["title"] == "First Thread"
        # Check message_count is included
        assert data[0]["message_count"] == 0

    @pytest.mark.asyncio
    async def test_get_thread_with_messages(self, client, db_session):
        """Test getting thread details includes empty messages array in MVP."""
        # Create test user, project, and thread
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
        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test Thread",
        )
        db_session.add(user)
        await db_session.commit()
        db_session.add(project)
        await db_session.commit()
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Get thread
        response = await client.get(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == thread.id
        assert data["title"] == "Test Thread"
        assert data["messages"] == []  # Empty in MVP

    @pytest.mark.asyncio
    async def test_thread_isolation(self, client, db_session):
        """Test that users can only access threads in their own projects."""
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

        # Create thread in user1's project
        thread1 = Thread(
            id=str(uuid4()),
            project_id=project1.id,
            title="User1 Thread",
        )
        db_session.add(thread1)
        await db_session.commit()

        # User2 tries to access user1's thread
        token2 = create_access_token(user2.id, user2.email)
        response = await client.get(
            f"/api/threads/{thread1.id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 404  # Should not find thread

    @pytest.mark.asyncio
    async def test_unauthenticated_access(self, client, db_session):
        """Test that thread endpoints require authentication."""
        # Create thread without auth
        response = await client.post(
            f"/api/projects/{str(uuid4())}/threads",
            json={"title": "Test"},
        )

        assert response.status_code == 403
