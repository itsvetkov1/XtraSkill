"""API test fixtures."""

import pytest
import pytest_asyncio
from uuid import uuid4
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.models import User, OAuthProvider
from app.utils.jwt import create_access_token
from main import app


@pytest_asyncio.fixture
async def authenticated_client(db_session):
    """Create test client with authenticated user.

    Provides an AsyncClient pre-configured with valid JWT authentication
    and a test user. The test user is accessible via `client.test_user`.
    """
    # Create test user
    user = User(
        id=str(uuid4()),
        email="testuser@example.com",
        oauth_provider=OAuthProvider.GOOGLE,
        oauth_id=f"google_{uuid4().hex[:8]}",
    )
    db_session.add(user)
    await db_session.commit()

    # Create JWT token
    token = create_access_token(user.id, user.email)

    # Override db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        # Attach user for test access
        ac.test_user = user
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def create_auth_token():
    """Factory to create JWT tokens for specific users."""
    def _create(user: User) -> str:
        return create_access_token(user.id, user.email)
    return _create
