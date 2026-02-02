"""Error consistency verification tests.

Verifies all API routes return errors in consistent format.
BAPI-07: All error responses follow {"detail": "message"} format.

Coverage:
- Auth errors (401, 403)
- Validation errors (422)
- Not found errors (404)
- Bad request errors (400)
- Rate limit errors (429)
- Error message consistency
"""

from datetime import datetime
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models import (
    OAuthProvider,
    Project,
    Thread,
    User,
)
from app.utils.jwt import create_access_token


class TestErrorResponseFormat:
    """Verify all error responses use consistent format."""

    @pytest.mark.asyncio
    async def test_auth_403_format(self, client, db_session):
        """403 errors have {"detail": str} format."""
        response = await client.get("/auth/me")

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_projects_404_format(self, client, db_session):
        """Project 404 errors have {"detail": str} format."""
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
            f"/api/projects/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_projects_422_format(self, client, db_session):
        """Project 422 validation errors have proper format."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Missing required 'name' field
        response = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "Missing name field"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # FastAPI validation errors return list of issues
        assert isinstance(data["detail"], list)

    @pytest.mark.asyncio
    async def test_documents_400_format(self, client, db_session):
        """Document 400 errors have {"detail": str} format."""
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
            name="Test",
        )
        db_session.add(project)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Upload unsupported file type
        files = {"file": ("test.pdf", BytesIO(b"fake pdf"), "application/pdf")}
        response = await client.post(
            f"/api/projects/{project.id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_threads_400_format(self, client, db_session):
        """Thread 400 errors have {"detail": str} format."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Invalid provider
        response = await client.post(
            "/api/threads",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test", "model_provider": "invalid_provider"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_threads_404_format(self, client, db_session):
        """Thread 404 errors have {"detail": str} format."""
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
            f"/api/threads/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_conversations_429_format(self, client, db_session):
        """Conversation 429 budget error has {"detail": str} format."""
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
            name="Test",
        )
        db_session.add(project)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        with patch('app.routes.conversations.check_user_budget', return_value=False):
            response = await client.post(
                f"/api/threads/{thread.id}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Hi"},
            )

        assert response.status_code == 429
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_artifacts_404_format(self, client, db_session):
        """Artifact 404 errors have {"detail": str} format."""
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
            f"/api/artifacts/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_documents_404_format(self, client, db_session):
        """Document 404 errors have {"detail": str} format."""
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
            f"/api/documents/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestErrorMessageClarity:
    """Verify error messages are clear and consistent."""

    @pytest.mark.asyncio
    async def test_not_found_uses_consistent_phrasing(self, client, db_session):
        """All 404 errors use 'not found' phrasing."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        endpoints = [
            f"/api/projects/{uuid4()}",
            f"/api/threads/{uuid4()}",
            f"/api/documents/{uuid4()}",
            f"/api/artifacts/{uuid4()}",
        ]

        for endpoint in endpoints:
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 404:
                data = response.json()
                assert "not found" in data["detail"].lower(), \
                    f"Endpoint {endpoint} doesn't use 'not found' phrasing"

    @pytest.mark.asyncio
    async def test_auth_error_is_descriptive(self, client, db_session):
        """Auth errors provide clear guidance."""
        # No token at all
        response = await client.get("/api/projects")

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        # Should mention authentication requirement
        detail_lower = data["detail"].lower()
        assert "authenticat" in detail_lower or "credential" in detail_lower or "bearer" in detail_lower

    @pytest.mark.asyncio
    async def test_validation_provides_field_info(self, client, db_session):
        """422 errors include field name in details."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Missing 'name' field for project creation
        response = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        # Should include field info
        found_name_field = False
        for error in data["detail"]:
            if "name" in str(error).lower():
                found_name_field = True
                break
        assert found_name_field, "Validation error should mention 'name' field"

    @pytest.mark.asyncio
    async def test_budget_error_is_user_friendly(self, client, db_session):
        """429 budget error is clear about the issue."""
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
            name="Test",
        )
        db_session.add(project)
        await db_session.commit()

        thread = Thread(
            id=str(uuid4()),
            project_id=project.id,
            title="Test",
            model_provider="anthropic",
            last_activity_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        with patch('app.routes.conversations.check_user_budget', return_value=False):
            response = await client.post(
                f"/api/threads/{thread.id}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Hi"},
            )

        assert response.status_code == 429
        data = response.json()
        detail_lower = data["detail"].lower()
        # Should mention budget or tokens
        assert "budget" in detail_lower or "token" in detail_lower


class TestCrossRouterConsistency:
    """Verify error handling is consistent across all routers."""

    @pytest.mark.asyncio
    async def test_all_routers_require_auth(self, client, db_session):
        """All protected endpoints return 403 without auth."""
        protected_endpoints = [
            ("GET", "/api/projects"),
            ("POST", "/api/projects"),
            ("GET", "/api/threads"),
            ("POST", "/api/threads"),
            ("GET", "/auth/me"),
        ]

        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            else:
                response = await client.post(endpoint, json={})

            assert response.status_code == 403, \
                f"{method} {endpoint} should return 403 without auth"
            data = response.json()
            assert "detail" in data, \
                f"{method} {endpoint} should have 'detail' in response"

    @pytest.mark.asyncio
    async def test_all_routers_return_404_for_nonexistent(self, client, db_session):
        """All GET endpoints return 404 for non-existent resources."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        fake_uuid = str(uuid4())
        endpoints = [
            f"/api/projects/{fake_uuid}",
            f"/api/threads/{fake_uuid}",
            f"/api/documents/{fake_uuid}",
            f"/api/artifacts/{fake_uuid}",
        ]

        for endpoint in endpoints:
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 404, \
                f"{endpoint} should return 404 for non-existent resource"
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_error_detail_never_leaks_internal_info(self, client, db_session):
        """Error messages don't expose internal implementation details."""
        user = User(
            id=str(uuid4()),
            email="test@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_123",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Check various error responses don't leak internal info
        endpoints_to_check = [
            f"/api/projects/{uuid4()}",
            f"/api/threads/{uuid4()}",
            f"/api/documents/{uuid4()}",
        ]

        sensitive_patterns = [
            "sql",
            "database",
            "traceback",
            "exception",
            "stack",
            "file",
            "path",
            "/app/",
            "\\app\\",
        ]

        for endpoint in endpoints_to_check:
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                data = response.json()
                detail = str(data.get("detail", "")).lower()
                for pattern in sensitive_patterns:
                    assert pattern not in detail, \
                        f"Error at {endpoint} may leak internal info: '{pattern}' found"
