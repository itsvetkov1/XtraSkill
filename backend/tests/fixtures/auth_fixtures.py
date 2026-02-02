"""Authentication fixtures for testing."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from main import app


@pytest_asyncio.fixture
async def client(db_session):
    """Create test HTTP client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Factory for creating auth headers with a given user ID."""
    def _create_headers(user_id: str) -> dict:
        # In tests, we typically override auth dependency
        # This fixture provides consistent header format
        return {"Authorization": f"Bearer test-token-{user_id}"}
    return _create_headers
