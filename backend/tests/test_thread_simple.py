"""Simple integration test for thread endpoints."""

from uuid import uuid4

import pytest
from app.models import OAuthProvider, Project, Thread, User
from app.utils.jwt import create_access_token


@pytest.mark.asyncio
async def test_create_and_list_threads(client, db_session):
    """Test creating threads and listing them."""
    # Create user
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        oauth_provider=OAuthProvider.GOOGLE,
        oauth_id="google_123",
    )
    db_session.add(user)
    await db_session.flush()  # Flush to ensure user exists before project

    # Create project
    project = Project(
        id=str(uuid4()),
        user_id=user.id,
        name="Test Project",
    )
    db_session.add(project)
    await db_session.flush()  # Flush to ensure project exists
    await db_session.commit()

    token = create_access_token(user.id, user.email)

    # Create thread with title
    response = await client.post(
        f"/api/projects/{project.id}/threads",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Thread"},
    )
    assert response.status_code == 201
    thread_data = response.json()
    assert thread_data["title"] == "Test Thread"

    # List threads
    response = await client.get(
        f"/api/projects/{project.id}/threads",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    threads = response.json()
    assert len(threads) >= 1
    assert threads[0]["message_count"] == 0
