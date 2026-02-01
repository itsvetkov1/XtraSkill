"""Integration tests for global thread management (Phase 25/26 features)."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import OAuthProvider, Project, Thread, User
from app.utils.jwt import create_access_token


class TestGlobalThreadsAPI:
    """Tests for GET /api/threads and POST /api/threads endpoints."""

    @pytest.mark.asyncio
    async def test_list_all_threads_empty(self, client, db_session):
        """Test listing threads when user has none."""
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
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["threads"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_threads_includes_project_based(self, client, db_session):
        """Test that global list includes project-based threads."""
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

        # Create project-based thread
        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            user_id=None,  # Project-based threads don't have user_id
            title="Project Thread",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)
        response = await client.get(
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["threads"]) == 1
        assert data["threads"][0]["title"] == "Project Thread"
        assert data["threads"][0]["project_id"] == project.id
        assert data["threads"][0]["project_name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_list_threads_includes_projectless(self, client, db_session):
        """Test that global list includes project-less threads."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create project-less thread
        thread = Thread(
            id=str(uuid4()),
            project_id=None,
            user_id=user.id,
            title="Global Chat",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)
        response = await client.get(
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["threads"]) == 1
        assert data["threads"][0]["title"] == "Global Chat"
        assert data["threads"][0]["project_id"] is None
        assert data["threads"][0]["project_name"] is None

    @pytest.mark.asyncio
    async def test_list_threads_mixed_types(self, client, db_session):
        """Test listing both project-based and project-less threads."""
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
            name="My Project",
        )
        db_session.add(project)
        await db_session.commit()

        # Create project-based thread
        thread1 = Thread(
            id=str(uuid4()),
            project_id=project.id,
            user_id=None,
            title="Project Thread",
            last_activity_at=datetime.utcnow() - timedelta(hours=1),
        )
        # Create project-less thread (more recent)
        thread2 = Thread(
            id=str(uuid4()),
            project_id=None,
            user_id=user.id,
            title="Global Chat",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add_all([thread1, thread2])
        await db_session.commit()

        token = create_access_token(user.id, user.email)
        response = await client.get(
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["threads"]) == 2
        assert data["total"] == 2
        # Most recent first (ordered by last_activity_at DESC)
        assert data["threads"][0]["title"] == "Global Chat"
        assert data["threads"][0]["project_name"] is None
        assert data["threads"][1]["title"] == "Project Thread"
        assert data["threads"][1]["project_name"] == "My Project"

    @pytest.mark.asyncio
    async def test_list_threads_pagination(self, client, db_session):
        """Test thread listing pagination."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create 30 threads
        threads = []
        for i in range(30):
            thread = Thread(
                id=str(uuid4()),
                project_id=None,
                user_id=user.id,
                title=f"Thread {i}",
                last_activity_at=datetime.utcnow() - timedelta(minutes=30 - i),
            )
            threads.append(thread)
        db_session.add_all(threads)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # First page (default 25)
        response = await client.get(
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert len(data["threads"]) == 25
        assert data["total"] == 30
        assert data["has_more"] is True

        # Second page
        response = await client.get(
            "/api/threads?page=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert len(data["threads"]) == 5
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_create_projectless_thread(self, client, db_session):
        """Test creating a project-less thread via global endpoint."""
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
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "New Global Chat"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Global Chat"
        assert data["project_id"] is None

        # Verify in database
        result = await db_session.execute(
            select(Thread).where(Thread.id == data["id"])
        )
        thread = result.scalar_one()
        assert thread.user_id == user.id
        assert thread.project_id is None

    @pytest.mark.asyncio
    async def test_create_thread_with_project(self, client, db_session):
        """Test creating a thread with project via global endpoint."""
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
        response = await client.post(
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Project Thread", "project_id": project.id},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Project Thread"
        assert data["project_id"] == project.id

        # Verify in database
        result = await db_session.execute(
            select(Thread).where(Thread.id == data["id"])
        )
        thread = result.scalar_one()
        assert thread.user_id is None  # Project-based threads don't have user_id
        assert thread.project_id == project.id

    @pytest.mark.asyncio
    async def test_create_thread_with_model_provider(self, client, db_session):
        """Test creating a thread with custom model provider."""
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
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"model_provider": "google"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["model_provider"] == "google"

    @pytest.mark.asyncio
    async def test_thread_isolation_global_list(self, client, db_session):
        """Test that global list only shows user's own threads."""
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
        db_session.add_all([user1, user2])
        await db_session.commit()

        # User1 threads
        thread1 = Thread(
            id=str(uuid4()),
            project_id=None,
            user_id=user1.id,
            title="User1 Thread",
            last_activity_at=datetime.utcnow(),
        )
        # User2 threads
        thread2 = Thread(
            id=str(uuid4()),
            project_id=None,
            user_id=user2.id,
            title="User2 Thread",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add_all([thread1, thread2])
        await db_session.commit()

        # User1 should only see their thread
        token1 = create_access_token(user1.id, user1.email)
        response = await client.get(
            "/api/threads",
            headers={"Authorization": f"Bearer {token1}"},
        )
        data = response.json()
        assert len(data["threads"]) == 1
        assert data["threads"][0]["title"] == "User1 Thread"


class TestThreadProjectAssociation:
    """Tests for PATCH /api/threads/{id} with project_id (Phase 26)."""

    @pytest.mark.asyncio
    async def test_associate_thread_with_project(self, client, db_session):
        """Test associating a project-less thread with a project."""
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
        thread = Thread(
            id=str(uuid4()),
            project_id=None,
            user_id=user.id,
            title="Global Chat",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add_all([project, thread])
        await db_session.commit()

        token = create_access_token(user.id, user.email)
        response = await client.patch(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": project.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project.id

        # Verify ownership model transition
        await db_session.refresh(thread)
        assert thread.project_id == project.id
        assert thread.user_id is None  # Cleared after association

    @pytest.mark.asyncio
    async def test_cannot_reassociate_thread(self, client, db_session):
        """Test that threads already in a project cannot be re-associated."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

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
        # Thread already associated with project1
        thread = Thread(
            id=str(uuid4()),
            project_id=project1.id,
            user_id=None,
            title="Project Thread",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add_all([project1, project2, thread])
        await db_session.commit()

        token = create_access_token(user.id, user.email)
        response = await client.patch(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": project2.id},
        )

        assert response.status_code == 400
        assert "already associated" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_associate_with_nonexistent_project(self, client, db_session):
        """Test associating with a non-existent project returns 404."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        thread = Thread(
            id=str(uuid4()),
            project_id=None,
            user_id=user.id,
            title="Global Chat",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add_all([user, thread])
        await db_session.commit()

        token = create_access_token(user.id, user.email)
        response = await client.patch(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": str(uuid4())},  # Non-existent project
        )

        assert response.status_code == 404
        assert "project not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_associate_with_other_users_project(self, client, db_session):
        """Test associating with another user's project returns 404."""
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
        db_session.add_all([user1, user2])
        await db_session.commit()

        # User2's project
        project = Project(
            id=str(uuid4()),
            user_id=user2.id,
            name="User2 Project",
        )
        # User1's thread
        thread = Thread(
            id=str(uuid4()),
            project_id=None,
            user_id=user1.id,
            title="User1 Chat",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add_all([project, thread])
        await db_session.commit()

        token = create_access_token(user1.id, user1.email)
        response = await client.patch(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": project.id},
        )

        assert response.status_code == 404
        assert "project not found" in response.json()["detail"].lower()
