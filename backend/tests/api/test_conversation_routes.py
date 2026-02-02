"""Contract tests for Conversations API routes.

Tests verify correct status codes, response schemas, and error handling
for chat streaming and message management endpoints.

Coverage:
- POST /api/threads/{id}/chat (stream chat)
- DELETE /api/threads/{id}/messages/{msg_id} (delete message)
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models import Message, OAuthProvider, Project, Thread, User
from app.utils.jwt import create_access_token


class TestStreamChat:
    """Contract tests for POST /api/threads/{id}/chat."""

    @pytest.mark.asyncio
    async def test_200_returns_sse_stream(self, client, db_session):
        """Returns EventSource response for chat request."""
        # Create user, project, and thread
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

        token = create_access_token(user.id, user.email)

        # Mock AIService to return simple stream
        async def mock_stream(*args, **kwargs):
            yield {"event": "text_delta", "data": json.dumps({"text": "Hello"})}
            yield {"event": "message_complete", "data": json.dumps({
                "content": "Hello",
                "usage": {"input_tokens": 10, "output_tokens": 5}
            })}

        with patch('app.routes.conversations.AIService') as MockAI:
            mock_service = MockAI.return_value
            mock_service.stream_chat = mock_stream

            # Mock budget check and summarization
            with patch('app.routes.conversations.check_user_budget', return_value=True):
                with patch('app.routes.conversations.maybe_update_summary', new_callable=AsyncMock):
                    async with client.stream(
                        "POST",
                        f"/api/threads/{thread.id}/chat",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"content": "Hi"}
                    ) as response:
                        assert response.status_code == 200
                        assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        response = await client.post(
            f"/api/threads/{uuid4()}/chat",
            json={"content": "Hi"}
        )

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

        with patch('app.routes.conversations.check_user_budget', return_value=True):
            response = await client.post(
                f"/api/threads/{uuid4()}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Hi"}
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_404_thread_not_owned(self, client, db_session):
        """Returns 404 for thread owned by another user (security: don't leak existence)."""
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

        with patch('app.routes.conversations.check_user_budget', return_value=True):
            response = await client.post(
                f"/api/threads/{thread.id}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Hi"}
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_429_budget_exceeded(self, client, db_session):
        """Returns 429 when monthly budget is exceeded."""
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

        token = create_access_token(user.id, user.email)

        # Mock budget check to return False (exceeded)
        with patch('app.routes.conversations.check_user_budget', return_value=False):
            response = await client.post(
                f"/api/threads/{thread.id}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Hi"}
            )

        assert response.status_code == 429
        assert "budget exceeded" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_422_empty_content(self, client, db_session):
        """Returns 422 when content is empty."""
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

        token = create_access_token(user.id, user.email)

        response = await client.post(
            f"/api/threads/{thread.id}/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": ""}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_request_schema_requires_content(self, client, db_session):
        """Request body must have 'content' field."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Missing content field entirely
        response = await client.post(
            f"/api/threads/{uuid4()}/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestDeleteMessage:
    """Contract tests for DELETE /api/threads/{id}/messages/{msg_id}."""

    @pytest.mark.asyncio
    async def test_204_deletes_message(self, client, db_session):
        """Returns 204 on successful message deletion."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create project-less thread (user_id ownership)
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

        response = await client.delete(
            f"/api/threads/{thread.id}/messages/{msg.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication token."""
        response = await client.delete(
            f"/api/threads/{uuid4()}/messages/{uuid4()}"
        )

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

        response = await client.delete(
            f"/api/threads/{uuid4()}/messages/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_message_not_found(self, client, db_session):
        """Returns 404 for non-existent message in valid thread."""
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

        token = create_access_token(user.id, user.email)

        response = await client.delete(
            f"/api/threads/{thread.id}/messages/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_404_message_wrong_thread(self, client, db_session):
        """Returns 404 for message that exists but in different thread."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create two threads
        thread1 = Thread(
            id=str(uuid4()),
            user_id=user.id,
            title="Thread 1",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        thread2 = Thread(
            id=str(uuid4()),
            user_id=user.id,
            title="Thread 2",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add_all([thread1, thread2])
        await db_session.commit()

        # Message in thread1
        msg = Message(
            id=str(uuid4()),
            thread_id=thread1.id,
            role="user",
            content="Hello",
        )
        db_session.add(msg)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Try to delete message using thread2's endpoint
        response = await client.delete(
            f"/api/threads/{thread2.id}/messages/{msg.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_thread_not_owned(self, client, db_session):
        """Returns 404 when trying to delete from another user's thread."""
        # Create owner with thread and message
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

        msg = Message(
            id=str(uuid4()),
            thread_id=thread.id,
            role="user",
            content="Hello",
        )
        db_session.add(msg)
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
            f"/api/threads/{thread.id}/messages/{msg.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
