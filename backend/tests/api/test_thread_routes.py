"""Contract tests for Threads API routes.

Tests verify correct status codes, response schemas, and error handling
for all thread endpoints.

Coverage:
- POST /api/threads (create global thread)
- GET /api/threads (list all threads, paginated)
- POST /api/projects/{id}/threads (create project thread)
- GET /api/projects/{id}/threads (list project threads)
- GET /api/threads/{id} (get thread with messages)
- PATCH /api/threads/{id} (update thread)
- DELETE /api/threads/{id} (delete thread)
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.models import Message, OAuthProvider, Project, Thread, User
from app.utils.jwt import create_access_token


class TestCreateGlobalThread:
    """Contract tests for POST /api/threads."""

    @pytest.mark.asyncio
    async def test_201_creates_projectless_thread(self, client, db_session):
        """Creates thread without project (global thread)."""
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
            json={"title": "New Chat"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Chat"
        assert data["project_id"] is None
        assert data["model_provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_201_creates_project_thread(self, client, db_session):
        """Creates thread with project association."""
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
            json={"title": "Project Chat", "project_id": project.id},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == project.id

    @pytest.mark.asyncio
    async def test_400_invalid_provider(self, client, db_session):
        """Returns 400 for invalid model_provider."""
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
            json={"title": "Test", "model_provider": "invalid_provider"},
        )

        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        response = await client.post(
            "/api/threads",
            json={"title": "Test"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_project_not_found(self, client, db_session):
        """Returns 404 when project_id doesn't exist."""
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
            json={"title": "Test", "project_id": str(uuid4())},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_response_schema(self, client, db_session):
        """Response has required fields: id, project_id (nullable), title, model_provider."""
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
            json={"title": "Test Thread"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "project_id" in data  # can be null
        assert "title" in data
        assert "model_provider" in data
        assert "created_at" in data
        assert "updated_at" in data


class TestListAllThreads:
    """Contract tests for GET /api/threads."""

    @pytest.mark.asyncio
    async def test_200_returns_paginated(self, client, db_session):
        """Returns paginated thread list."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create a thread
        thread = Thread(
            id=str(uuid4()),
            user_id=user.id,
            title="Test Thread",
            model_provider="anthropic",
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
        assert "threads" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_more" in data
        assert len(data["threads"]) >= 1

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        response = await client.get("/api/threads")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_pagination_params(self, client, db_session):
        """Pagination parameters work correctly."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create multiple threads
        for i in range(5):
            thread = Thread(
                id=str(uuid4()),
                user_id=user.id,
                title=f"Thread {i}",
                model_provider="anthropic",
                last_activity_at=datetime.utcnow() + timedelta(seconds=i),
            )
            db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Request page 2 with page_size 2
        response = await client.get(
            "/api/threads?page=2&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert len(data["threads"]) == 2

    @pytest.mark.asyncio
    async def test_response_schema(self, client, db_session):
        """Response has required fields for paginated response."""
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
        # Verify pagination structure
        assert isinstance(data["threads"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        assert isinstance(data["has_more"], bool)


class TestCreateProjectThread:
    """Contract tests for POST /api/projects/{id}/threads."""

    @pytest.mark.asyncio
    async def test_201_creates_thread(self, client, db_session):
        """Creates thread within project."""
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
            f"/api/projects/{project.id}/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Project Discussion"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == project.id
        assert data["title"] == "Project Discussion"

    @pytest.mark.asyncio
    async def test_400_invalid_provider(self, client, db_session):
        """Returns 400 for invalid model_provider."""
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
            f"/api/projects/{project.id}/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test", "model_provider": "bad_provider"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        project_id = str(uuid4())

        response = await client.post(
            f"/api/projects/{project_id}/threads",
            json={"title": "Test"},
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

        response = await client.post(
            f"/api/projects/{str(uuid4())}/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test"},
        )

        assert response.status_code == 404


class TestListProjectThreads:
    """Contract tests for GET /api/projects/{id}/threads."""

    @pytest.mark.asyncio
    async def test_200_returns_array(self, client, db_session):
        """Returns array of threads for project."""
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
            title="Project Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/projects/{project.id}/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Project Thread"

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        project_id = str(uuid4())

        response = await client.get(f"/api/projects/{project_id}/threads")

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
            f"/api/projects/{str(uuid4())}/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_message_count_included(self, client, db_session):
        """Response items have message_count field."""
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

        # Add messages
        for _ in range(3):
            msg = Message(
                id=str(uuid4()),
                thread_id=thread.id,
                role="user",
                content="Hello",
            )
            db_session.add(msg)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/projects/{project.id}/threads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "message_count" in data[0]
        assert data[0]["message_count"] == 3


class TestGetThread:
    """Contract tests for GET /api/threads/{id}."""

    @pytest.mark.asyncio
    async def test_200_with_messages(self, client, db_session):
        """Returns thread with messages."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            user_id=user.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        msg = Message(
            id=str(uuid4()),
            thread_id=thread.id,
            role="user",
            content="Hello",
        )
        db_session.add(msg)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == thread.id
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        thread_id = str(uuid4())

        response = await client.get(f"/api/threads/{thread_id}")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, client, db_session):
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
            f"/api/threads/{str(uuid4())}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_not_owned(self, client, db_session):
        """Returns 404 for thread owned by another user."""
        # Create owner with thread
        owner = User(
            id=str(uuid4()),
            email="owner@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_owner",
        )
        db_session.add(owner)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            user_id=owner.id,
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
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_messages_ordered_chronologically(self, client, db_session):
        """Messages sorted by created_at ASC (oldest first)."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            user_id=user.id,
            title="Test Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        # Add messages with specific order
        now = datetime.utcnow()
        msg1 = Message(
            id=str(uuid4()),
            thread_id=thread.id,
            role="user",
            content="First",
            created_at=now - timedelta(minutes=2),
        )
        msg2 = Message(
            id=str(uuid4()),
            thread_id=thread.id,
            role="assistant",
            content="Second",
            created_at=now - timedelta(minutes=1),
        )
        msg3 = Message(
            id=str(uuid4()),
            thread_id=thread.id,
            role="user",
            content="Third",
            created_at=now,
        )
        db_session.add_all([msg3, msg1, msg2])  # Add in wrong order
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.get(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        messages = data["messages"]
        assert len(messages) == 3
        # Verify chronological order (oldest first)
        assert messages[0]["content"] == "First"
        assert messages[1]["content"] == "Second"
        assert messages[2]["content"] == "Third"


class TestUpdateThread:
    """Contract tests for PATCH /api/threads/{id}."""

    @pytest.mark.asyncio
    async def test_200_updates_title(self, client, db_session):
        """Updates thread title successfully."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            user_id=user.id,
            title="Original Title",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.patch(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_200_associates_project(self, client, db_session):
        """Associates project-less thread with project."""
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
            user_id=user.id,
            title="Global Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
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

    @pytest.mark.asyncio
    async def test_400_already_associated(self, client, db_session):
        """Returns 400 when trying to re-associate thread with another project."""
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
        db_session.add_all([project1, project2])
        await db_session.commit()

        # Thread already associated with project1
        thread = Thread(
            id=str(uuid4()),
            project_id=project1.id,
            title="Project Thread",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Try to re-associate with project2
        response = await client.patch(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": project2.id},
        )

        assert response.status_code == 400
        assert "already associated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        thread_id = str(uuid4())

        response = await client.patch(
            f"/api/threads/{thread_id}",
            json={"title": "New Title"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, client, db_session):
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

        response = await client.patch(
            f"/api/threads/{str(uuid4())}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "New Title"},
        )

        assert response.status_code == 404


class TestDeleteThread:
    """Contract tests for DELETE /api/threads/{id}."""

    @pytest.mark.asyncio
    async def test_204_deletes_thread(self, client, db_session):
        """Returns 204 on successful deletion."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            user_id=user.id,
            title="To Delete",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.delete(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

        # Verify thread is deleted
        get_resp = await client.get(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        thread_id = str(uuid4())

        response = await client.delete(f"/api/threads/{thread_id}")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, client, db_session):
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

        response = await client.delete(
            f"/api/threads/{str(uuid4())}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_not_owned(self, client, db_session):
        """Returns 404 for thread owned by another user."""
        # Create owner with thread
        owner = User(
            id=str(uuid4()),
            email="owner@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_owner",
        )
        db_session.add(owner)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            user_id=owner.id,
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

        response = await client.delete(
            f"/api/threads/{thread.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
