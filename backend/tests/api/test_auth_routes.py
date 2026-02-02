"""Contract tests for authentication routes.

Tests verify HTTP status codes and response schemas for all auth endpoints:
- POST /auth/google/initiate
- GET /auth/google/callback
- POST /auth/microsoft/initiate
- GET /auth/microsoft/callback
- POST /auth/logout
- GET /auth/me
- GET /auth/usage
"""

import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from app.models import User, OAuthProvider


class TestGoogleOAuthInitiate:
    """Contract tests for POST /auth/google/initiate."""

    @pytest.mark.asyncio
    async def test_200_returns_auth_url(self, client, db_session):
        """Returns auth_url and state on success."""
        with patch("app.routes.auth.OAuth2Service") as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_google_auth_url = AsyncMock(
                return_value=("https://accounts.google.com/o/oauth2/auth?client_id=test", "test-state-123")
            )

            response = await client.post("/auth/google/initiate")

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert "state" in data

    @pytest.mark.asyncio
    async def test_auth_url_is_google_domain(self, client, db_session):
        """auth_url starts with Google OAuth domain."""
        with patch("app.routes.auth.OAuth2Service") as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_google_auth_url = AsyncMock(
                return_value=("https://accounts.google.com/o/oauth2/auth?client_id=test", "state-abc")
            )

            response = await client.post("/auth/google/initiate")

            assert response.status_code == 200
            data = response.json()
            assert data["auth_url"].startswith("https://accounts.google.com")


class TestGoogleOAuthCallback:
    """Contract tests for GET /auth/google/callback."""

    @pytest.mark.asyncio
    async def test_400_invalid_state(self, client, db_session):
        """Returns 400 with unknown state parameter."""
        response = await client.get(
            "/auth/google/callback",
            params={"code": "test-code", "state": "invalid-state"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "state" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_422_missing_code(self, client, db_session):
        """Returns 422 when code parameter is missing."""
        response = await client.get(
            "/auth/google/callback",
            params={"state": "some-state"}
        )

        # FastAPI validation returns 422 for missing required params
        assert response.status_code == 422


class TestMicrosoftOAuthInitiate:
    """Contract tests for POST /auth/microsoft/initiate."""

    @pytest.mark.asyncio
    async def test_200_returns_auth_url(self, client, db_session):
        """Returns auth_url and state on success."""
        with patch("app.routes.auth.OAuth2Service") as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_microsoft_auth_url = AsyncMock(
                return_value=("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=test", "test-state-456")
            )

            response = await client.post("/auth/microsoft/initiate")

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert "state" in data

    @pytest.mark.asyncio
    async def test_auth_url_is_microsoft_domain(self, client, db_session):
        """auth_url contains Microsoft login domain."""
        with patch("app.routes.auth.OAuth2Service") as MockService:
            mock_instance = MockService.return_value
            mock_instance.get_microsoft_auth_url = AsyncMock(
                return_value=("https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=test", "state-def")
            )

            response = await client.post("/auth/microsoft/initiate")

            assert response.status_code == 200
            data = response.json()
            assert "login.microsoftonline.com" in data["auth_url"]


class TestMicrosoftOAuthCallback:
    """Contract tests for GET /auth/microsoft/callback."""

    @pytest.mark.asyncio
    async def test_400_invalid_state(self, client, db_session):
        """Returns 400 with unknown state parameter."""
        response = await client.get(
            "/auth/microsoft/callback",
            params={"code": "test-code", "state": "invalid-state"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "state" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_422_missing_code(self, client, db_session):
        """Returns 422 when code parameter is missing."""
        response = await client.get(
            "/auth/microsoft/callback",
            params={"state": "some-state"}
        )

        # FastAPI validation returns 422 for missing required params
        assert response.status_code == 422


class TestLogout:
    """Contract tests for POST /auth/logout."""

    @pytest.mark.asyncio
    async def test_200_returns_message(self, client, db_session):
        """Returns logged out message on success."""
        response = await client.post("/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"


class TestGetMe:
    """Contract tests for GET /auth/me."""

    @pytest.mark.asyncio
    async def test_200_with_valid_token(self, authenticated_client):
        """Returns user info with valid JWT."""
        response = await authenticated_client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert "id" in data
        assert "oauth_provider" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_403_without_token(self, client, db_session):
        """Returns 403 without Authorization header."""
        response = await client.get("/auth/me")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_user_info_fields(self, authenticated_client):
        """Response contains required fields."""
        response = await authenticated_client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields present
        required_fields = ["id", "email", "oauth_provider", "created_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify oauth_provider is a valid value
        assert data["oauth_provider"] in ["google", "microsoft"]


class TestGetUsage:
    """Contract tests for GET /auth/usage."""

    @pytest.mark.asyncio
    async def test_200_with_valid_token(self, authenticated_client):
        """Returns usage object with valid JWT."""
        response = await authenticated_client.get("/auth/usage")

        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data
        assert "total_requests" in data

    @pytest.mark.asyncio
    async def test_403_without_token(self, client, db_session):
        """Returns 403 without Authorization header."""
        response = await client.get("/auth/usage")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_usage_fields(self, authenticated_client):
        """Response contains required usage fields."""
        response = await authenticated_client.get("/auth/usage")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields present
        required_fields = ["total_cost", "total_requests", "total_input_tokens",
                          "total_output_tokens", "month_start", "budget"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify types
        assert isinstance(data["total_cost"], (int, float))
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["budget"], (int, float))
