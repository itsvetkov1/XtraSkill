"""Contract tests for project routes.

Tests verify HTTP status codes and response schemas for all project endpoints:
- POST /api/projects (create)
- GET /api/projects (list)
- GET /api/projects/{id} (get detail)
- PUT /api/projects/{id} (update)
- DELETE /api/projects/{id} (delete)
"""

import pytest
from uuid import uuid4

from app.models import Project, User, OAuthProvider
from app.utils.jwt import create_access_token


class TestCreateProject:
    """Contract tests for POST /api/projects."""

    @pytest.mark.asyncio
    async def test_201_with_valid_data(self, authenticated_client):
        """Returns 201 and project data on success."""
        response = await authenticated_client.post(
            "/api/projects",
            json={"name": "Test Project", "description": "Test description"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "Test description"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication."""
        response = await client.post(
            "/api/projects",
            json={"name": "Test"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_422_missing_name(self, authenticated_client):
        """Returns 422 when name is missing."""
        response = await authenticated_client.post(
            "/api/projects",
            json={"description": "No name provided"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_422_empty_name(self, authenticated_client):
        """Returns 422 when name is empty string."""
        response = await authenticated_client.post(
            "/api/projects",
            json={"name": "", "description": "Empty name"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_response_schema(self, authenticated_client):
        """Response has required schema fields."""
        response = await authenticated_client.post(
            "/api/projects",
            json={"name": "Schema Test Project"}
        )

        assert response.status_code == 201
        data = response.json()

        # Verify all required fields present
        required_fields = ["id", "name", "description", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


class TestListProjects:
    """Contract tests for GET /api/projects."""

    @pytest.mark.asyncio
    async def test_200_returns_array(self, authenticated_client):
        """Returns 200 with array response."""
        response = await authenticated_client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication."""
        response = await client.get("/api/projects")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_list_for_new_user(self, authenticated_client):
        """Returns empty array for user with no projects."""
        response = await authenticated_client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_returns_only_owned_projects(self, authenticated_client, db_session, create_auth_token):
        """User only sees their own projects."""
        # Create project for authenticated user
        project = Project(
            user_id=authenticated_client.test_user.id,
            name="My Project"
        )
        db_session.add(project)

        # Create another user with their own project
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        other_project = Project(
            user_id=other_user.id,
            name="Other User Project"
        )
        db_session.add(other_project)
        await db_session.commit()

        # List projects for authenticated user
        response = await authenticated_client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Project"


class TestGetProject:
    """Contract tests for GET /api/projects/{id}."""

    @pytest.mark.asyncio
    async def test_200_with_details(self, authenticated_client, db_session):
        """Returns project with documents and threads arrays."""
        project = Project(
            user_id=authenticated_client.test_user.id,
            name="Detail Test Project",
            description="Test description"
        )
        db_session.add(project)
        await db_session.commit()

        response = await authenticated_client.get(f"/api/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Test Project"
        assert data["description"] == "Test description"
        assert "documents" in data
        assert "threads" in data
        assert isinstance(data["documents"], list)
        assert isinstance(data["threads"], list)

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication."""
        response = await client.get(f"/api/projects/{uuid4()}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, authenticated_client):
        """Returns 404 for non-existent project."""
        response = await authenticated_client.get(f"/api/projects/{uuid4()}")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_404_not_owned(self, authenticated_client, db_session):
        """Returns 404 for other user's project (to avoid leaking existence)."""
        # Create another user with a project
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        other_project = Project(
            user_id=other_user.id,
            name="Other User Project"
        )
        db_session.add(other_project)
        await db_session.commit()

        # Try to access other user's project
        response = await authenticated_client.get(f"/api/projects/{other_project.id}")
        assert response.status_code == 404


class TestUpdateProject:
    """Contract tests for PUT /api/projects/{id}."""

    @pytest.mark.asyncio
    async def test_200_updates_name(self, authenticated_client, db_session):
        """Returns 200 and updates project name."""
        project = Project(
            user_id=authenticated_client.test_user.id,
            name="Original Name"
        )
        db_session.add(project)
        await db_session.commit()

        response = await authenticated_client.put(
            f"/api/projects/{project.id}",
            json={"name": "Updated Name", "description": None}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_200_updates_description(self, authenticated_client, db_session):
        """Returns 200 and updates project description."""
        project = Project(
            user_id=authenticated_client.test_user.id,
            name="Test Project",
            description="Original description"
        )
        db_session.add(project)
        await db_session.commit()

        response = await authenticated_client.put(
            f"/api/projects/{project.id}",
            json={"name": "Test Project", "description": "Updated description"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication."""
        response = await client.put(
            f"/api/projects/{uuid4()}",
            json={"name": "Test"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, authenticated_client):
        """Returns 404 for non-existent project."""
        response = await authenticated_client.put(
            f"/api/projects/{uuid4()}",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_404_not_owned(self, authenticated_client, db_session):
        """Returns 404 for other user's project."""
        # Create another user with a project
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        other_project = Project(
            user_id=other_user.id,
            name="Other User Project"
        )
        db_session.add(other_project)
        await db_session.commit()

        # Try to update other user's project
        response = await authenticated_client.put(
            f"/api/projects/{other_project.id}",
            json={"name": "Hacked Name"}
        )
        assert response.status_code == 404


class TestDeleteProject:
    """Contract tests for DELETE /api/projects/{id}."""

    @pytest.mark.asyncio
    async def test_204_deletes_project(self, authenticated_client, db_session):
        """Returns 204 on successful delete."""
        project = Project(
            user_id=authenticated_client.test_user.id,
            name="To Delete"
        )
        db_session.add(project)
        await db_session.commit()

        response = await authenticated_client.delete(f"/api/projects/{project.id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client, db_session):
        """Returns 403 without authentication."""
        response = await client.delete(f"/api/projects/{uuid4()}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_404_not_found(self, authenticated_client):
        """Returns 404 for non-existent project."""
        response = await authenticated_client.delete(f"/api/projects/{uuid4()}")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_404_not_owned(self, authenticated_client, db_session):
        """Returns 404 for other user's project."""
        # Create another user with a project
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        other_project = Project(
            user_id=other_user.id,
            name="Other User Project"
        )
        db_session.add(other_project)
        await db_session.commit()

        # Try to delete other user's project
        response = await authenticated_client.delete(f"/api/projects/{other_project.id}")
        assert response.status_code == 404
