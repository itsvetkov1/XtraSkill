"""Integration tests for authentication flows."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import OAuthProvider, User
from app.utils.jwt import create_access_token, verify_token


class TestJWTAuthentication:
    """Test JWT token creation and verification."""

    @pytest.mark.asyncio
    async def test_create_jwt_token(self):
        """Test JWT token creation with valid user data."""
        user_id = str(uuid4())
        email = "test@example.com"

        token = create_access_token(user_id=user_id, email=email)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are fairly long

    @pytest.mark.asyncio
    async def test_verify_jwt_token(self):
        """Test JWT token verification and payload extraction."""
        user_id = str(uuid4())
        email = "test@example.com"

        token = create_access_token(user_id=user_id, email=email)
        payload = verify_token(token)

        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self):
        """Test that invalid tokens are rejected."""
        invalid_token = "invalid.token.string"

        with pytest.raises(Exception):  # HTTPException
            verify_token(invalid_token)


class TestOAuthEndpoints:
    """Test OAuth authentication endpoints."""

    @pytest.mark.asyncio
    async def test_google_oauth_initiate(self, client):
        """Test Google OAuth initiation returns auth URL."""
        response = await client.post("/auth/google/initiate")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "accounts.google.com" in data["auth_url"]
        assert "state=" in data["auth_url"]

    @pytest.mark.asyncio
    async def test_microsoft_oauth_initiate(self, client):
        """Test Microsoft OAuth initiation returns auth URL."""
        response = await client.post("/auth/microsoft/initiate")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "login.microsoftonline.com" in data["auth_url"]
        assert "state=" in data["auth_url"]

    @pytest.mark.asyncio
    async def test_oauth_state_parameter_unique(self, client):
        """Test that each OAuth initiation generates unique state."""
        response1 = await client.post("/auth/google/initiate")
        response2 = await client.post("/auth/google/initiate")

        state1 = response1.json()["state"]
        state2 = response2.json()["state"]

        assert state1 != state2


class TestProtectedEndpoints:
    """Test protected endpoints requiring authentication."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self, client, db_session):
        """Test that /auth/me requires valid JWT token."""
        # Request without token should fail with 403 Forbidden (missing auth header)
        response = await client.get("/auth/me")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token(self, client, db_session):
        """Test that /auth/me works with valid JWT token."""
        # Create test user in database
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        # Create valid token
        token = create_access_token(user_id=user.id, email=user.email)

        # Request with valid token should succeed
        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["oauth_provider"] == "google"

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, client):
        """Test that /auth/me rejects invalid tokens."""
        response = await client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401


class TestUserCreation:
    """Test user creation during OAuth callback."""

    @pytest.mark.asyncio
    async def test_user_created_on_first_login(self, db_session):
        """Test that new user is created when logging in for first time."""
        # Verify user doesn't exist
        stmt = select(User).where(User.email == "newuser@example.com")
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        assert user is None

        # Create new user (simulating OAuth callback)
        new_user = User(
            id=str(uuid4()),
            email="newuser@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_new_123",
        )
        db_session.add(new_user)
        await db_session.commit()

        # Verify user now exists
        stmt = select(User).where(User.email == "newuser@example.com")
        result = await db_session.execute(stmt)
        created_user = result.scalar_one_or_none()

        assert created_user is not None
        assert created_user.email == "newuser@example.com"
        assert created_user.oauth_provider == OAuthProvider.GOOGLE
        assert created_user.oauth_id == "google_new_123"

    @pytest.mark.asyncio
    async def test_user_updated_on_subsequent_login(self, db_session):
        """Test that existing user is updated on subsequent logins."""
        # Create initial user
        user = User(
            id=str(uuid4()),
            email="existing@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_existing_123",
        )
        db_session.add(user)
        await db_session.commit()

        initial_updated_at = user.updated_at
        user_id = user.id

        # Update user (simulating subsequent login with email change)
        stmt = select(User).where(User.oauth_id == "google_existing_123")
        result = await db_session.execute(stmt)
        existing_user = result.scalar_one()

        existing_user.email = "updated@example.com"
        await db_session.commit()
        await db_session.refresh(existing_user)

        # Verify user was updated, not duplicated
        assert existing_user.id == user_id
        assert existing_user.email == "updated@example.com"
        assert existing_user.updated_at >= initial_updated_at

        # Verify only one user exists
        stmt = select(User).where(User.oauth_id == "google_existing_123")
        result = await db_session.execute(stmt)
        all_users = result.scalars().all()
        assert len(all_users) == 1


class TestLogout:
    """Test logout functionality."""

    @pytest.mark.asyncio
    async def test_logout_endpoint_stateless(self, client):
        """Test that logout endpoint is stateless (client-side token deletion)."""
        response = await client.post("/auth/logout")

        # Logout is stateless in JWT, so it just returns success
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
