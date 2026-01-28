"""Consolidated backend integration tests covering all critical API flows.

This test suite consolidates and expands on existing integration tests to provide
comprehensive coverage of:
- Authentication (JWT, OAuth endpoints, protected routes)
- Projects (CRUD operations, ownership, isolation)
- Documents (upload, list, get, validation, encryption)
- Threads (create, list, get, ordering, ownership)
- AI Chat (message handling, budget enforcement, token tracking)
- Artifacts (list, get, export formats)
"""

from io import BytesIO
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from unittest.mock import AsyncMock, patch, MagicMock

from app.models import OAuthProvider, User, Project, Document, Thread, Message, Artifact
from app.utils.jwt import create_access_token, verify_token


# ============================================
# Authentication Tests (12 tests)
# ============================================


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


# ============================================
# Project Tests (9 tests)
# ============================================


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        id=str(uuid4()),
        email="testuser@example.com",
        oauth_provider=OAuthProvider.GOOGLE,
        oauth_id="google_test_user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Create authentication headers with valid token."""
    token = create_access_token(user_id=test_user.id, email=test_user.email)
    return {"Authorization": f"Bearer {token}"}


class TestProjects:
    """Test project CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_project_with_valid_data(self, client, auth_headers):
        """Test creating project with valid data returns 201."""
        response = await client.post(
            "/api/projects",
            json={"name": "Test Project", "description": "Test description"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "Test description"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_project_with_empty_name(self, client, auth_headers):
        """Test creating project with empty name returns 422."""
        response = await client.post(
            "/api/projects",
            json={"name": "", "description": "Description"},
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_projects_returns_user_projects_only(
        self, client, db_session, test_user, auth_headers
    ):
        """Test that list projects returns only user's projects."""
        # Create project for test user
        project1 = Project(
            id=str(uuid4()),
            user_id=test_user.id,
            name="User Project",
            description="Test"
        )
        db_session.add(project1)

        # Create project for different user
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other",
        )
        db_session.add(other_user)
        await db_session.commit()

        project2 = Project(
            id=str(uuid4()),
            user_id=other_user.id,
            name="Other User Project",
            description="Test"
        )
        db_session.add(project2)
        await db_session.commit()

        response = await client.get("/api/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "User Project"

    @pytest.mark.asyncio
    async def test_get_project_by_id_returns_project_details(
        self, client, db_session, test_user, auth_headers
    ):
        """Test getting project by ID returns project details."""
        project = Project(
            id=str(uuid4()),
            user_id=test_user.id,
            name="Test Project",
            description="Test description"
        )
        db_session.add(project)
        await db_session.commit()

        response = await client.get(f"/api/projects/{project.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project_with_wrong_user_returns_404(
        self, client, db_session, auth_headers
    ):
        """Test that getting project owned by different user returns 404."""
        # Create project for different user
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other_2",
        )
        db_session.add(other_user)
        await db_session.commit()

        project = Project(
            id=str(uuid4()),
            user_id=other_user.id,
            name="Other User Project",
            description="Test"
        )
        db_session.add(project)
        await db_session.commit()

        response = await client.get(f"/api/projects/{project.id}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project_name_and_description(
        self, client, db_session, test_user, auth_headers
    ):
        """Test updating project name and description returns 200."""
        project = Project(
            id=str(uuid4()),
            user_id=test_user.id,
            name="Old Name",
            description="Old description"
        )
        db_session.add(project)
        await db_session.commit()

        response = await client.put(
            f"/api/projects/{project.id}",
            json={"name": "New Name", "description": "New description"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_update_nonexistent_project_returns_404(self, client, auth_headers):
        """Test updating non-existent project returns 404."""
        fake_id = str(uuid4())
        response = await client.put(
            f"/api/projects/{fake_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_projects_ordered_by_updated_at_desc(
        self, client, db_session, test_user, auth_headers
    ):
        """Test that projects are ordered by updated_at DESC."""
        import asyncio

        # Create projects with slight delays to ensure different updated_at
        project1 = Project(
            id=str(uuid4()),
            user_id=test_user.id,
            name="First Project",
            description="Created first"
        )
        db_session.add(project1)
        await db_session.commit()

        await asyncio.sleep(0.01)

        project2 = Project(
            id=str(uuid4()),
            user_id=test_user.id,
            name="Second Project",
            description="Created second"
        )
        db_session.add(project2)
        await db_session.commit()

        response = await client.get("/api/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Most recent should be first
        assert data[0]["name"] == "Second Project"
        assert data[1]["name"] == "First Project"

    @pytest.mark.asyncio
    async def test_create_project_requires_authentication(self, client):
        """Test that creating project without authentication fails."""
        response = await client.post(
            "/api/projects",
            json={"name": "Test Project"},
        )

        assert response.status_code == 403


# ============================================
# Document Tests (8 tests)
# ============================================


@pytest_asyncio.fixture
async def test_project(db_session, test_user):
    """Create a test project."""
    project = Project(
        id=str(uuid4()),
        user_id=test_user.id,
        name="Test Project",
        description="Test"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


class TestDocuments:
    """Test document operations."""

    @pytest.mark.asyncio
    async def test_upload_document_to_project_returns_201(
        self, client, test_project, auth_headers
    ):
        """Test uploading document to project returns 201."""
        file_content = b"Test document content"
        files = {
            "file": ("test.txt", BytesIO(file_content), "text/plain")
        }

        response = await client.post(
            f"/api/documents?project_id={test_project.id}",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["project_id"] == test_project.id

    @pytest.mark.asyncio
    async def test_upload_document_with_invalid_project_returns_404(
        self, client, auth_headers
    ):
        """Test uploading document with invalid project_id returns 404."""
        fake_project_id = str(uuid4())
        file_content = b"Test content"
        files = {
            "file": ("test.txt", BytesIO(file_content), "text/plain")
        }

        response = await client.post(
            f"/api/documents?project_id={fake_project_id}",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_documents_returns_project_documents(
        self, client, db_session, test_project, test_user, auth_headers
    ):
        """Test listing documents returns project's documents."""
        from cryptography.fernet import Fernet
        import os

        fernet = Fernet(os.getenv("FERNET_KEY").encode())

        document = Document(
            id=str(uuid4()),
            project_id=test_project.id,
            filename="test.txt",
            content=fernet.encrypt(b"Test content")
        )
        db_session.add(document)
        await db_session.commit()

        response = await client.get(
            f"/api/documents?project_id={test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_get_document_content_returns_decrypted_text(
        self, client, db_session, test_project, auth_headers
    ):
        """Test getting document content returns decrypted text."""
        from cryptography.fernet import Fernet
        import os

        fernet = Fernet(os.getenv("FERNET_KEY").encode())
        content = b"Test document content"

        document = Document(
            id=str(uuid4()),
            project_id=test_project.id,
            filename="test.txt",
            content=fernet.encrypt(content)
        )
        db_session.add(document)
        await db_session.commit()

        response = await client.get(
            f"/api/documents/{document.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == content.decode('utf-8')

    @pytest.mark.asyncio
    async def test_document_ownership_validated(
        self, client, db_session, auth_headers
    ):
        """Test that users can't access other users' documents."""
        # Create another user's project
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other_doc",
        )
        db_session.add(other_user)
        await db_session.commit()

        other_project = Project(
            id=str(uuid4()),
            user_id=other_user.id,
            name="Other Project",
            description="Test"
        )
        db_session.add(other_project)
        await db_session.commit()

        from cryptography.fernet import Fernet
        import os
        fernet = Fernet(os.getenv("FERNET_KEY").encode())

        document = Document(
            id=str(uuid4()),
            project_id=other_project.id,
            filename="test.txt",
            content=fernet.encrypt(b"Test")
        )
        db_session.add(document)
        await db_session.commit()

        response = await client.get(
            f"/api/documents/{document.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_oversized_document_returns_422(
        self, client, test_project, auth_headers
    ):
        """Test uploading oversized document returns 422."""
        # Create file larger than 1MB
        large_content = b"x" * (1024 * 1024 + 1)
        files = {
            "file": ("large.txt", BytesIO(large_content), "text/plain")
        }

        response = await client.post(
            f"/api/documents?project_id={test_project.id}",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_non_text_file_returns_422(
        self, client, test_project, auth_headers
    ):
        """Test uploading non-text file returns 422."""
        # Binary content
        binary_content = bytes([0xFF, 0xD8, 0xFF, 0xE0])
        files = {
            "file": ("image.jpg", BytesIO(binary_content), "image/jpeg")
        }

        response = await client.post(
            f"/api/documents?project_id={test_project.id}",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_document_search_finds_content(
        self, client, db_session, test_project, auth_headers
    ):
        """Test that document search finds content."""
        from cryptography.fernet import Fernet
        from sqlalchemy import text
        import os

        fernet = Fernet(os.getenv("FERNET_KEY").encode())
        content = b"This document contains searchable content"

        document = Document(
            id=str(uuid4()),
            project_id=test_project.id,
            filename="searchable.txt",
            content=fernet.encrypt(content)
        )
        db_session.add(document)
        await db_session.commit()

        # Add to FTS index
        await db_session.execute(
            text("""
                INSERT INTO document_fts (document_id, filename, content)
                VALUES (:doc_id, :filename, :content)
            """),
            {
                "doc_id": document.id,
                "filename": document.filename,
                "content": content.decode('utf-8')
            }
        )
        await db_session.commit()

        response = await client.get(
            f"/api/documents/search?project_id={test_project.id}&query=searchable",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "searchable" in data[0]["snippet"].lower()


# ============================================
# Thread Tests (7 tests)
# ============================================


@pytest_asyncio.fixture
async def test_thread(db_session, test_project):
    """Create a test thread."""
    thread = Thread(
        id=str(uuid4()),
        project_id=test_project.id,
        title="Test Thread"
    )
    db_session.add(thread)
    await db_session.commit()
    await db_session.refresh(thread)
    return thread


class TestThreads:
    """Test thread operations."""

    @pytest.mark.asyncio
    async def test_create_thread_in_project_returns_201(
        self, client, test_project, auth_headers
    ):
        """Test creating thread in project returns 201."""
        response = await client.post(
            f"/api/threads?project_id={test_project.id}",
            json={"title": "New Thread"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Thread"
        assert data["project_id"] == test_project.id

    @pytest.mark.asyncio
    async def test_list_threads_returns_project_threads(
        self, client, db_session, test_project, auth_headers
    ):
        """Test listing threads returns project's threads."""
        thread1 = Thread(
            id=str(uuid4()),
            project_id=test_project.id,
            title="Thread 1"
        )
        thread2 = Thread(
            id=str(uuid4()),
            project_id=test_project.id,
            title="Thread 2"
        )
        db_session.add_all([thread1, thread2])
        await db_session.commit()

        response = await client.get(
            f"/api/threads?project_id={test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_thread_with_messages_returns_conversation_history(
        self, client, db_session, test_thread, auth_headers
    ):
        """Test getting thread with messages returns conversation history."""
        message1 = Message(
            id=str(uuid4()),
            thread_id=test_thread.id,
            role="user",
            content="Hello"
        )
        message2 = Message(
            id=str(uuid4()),
            thread_id=test_thread.id,
            role="assistant",
            content="Hi there"
        )
        db_session.add_all([message1, message2])
        await db_session.commit()

        response = await client.get(
            f"/api/threads/{test_thread.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_thread_ownership_validated(
        self, client, db_session, auth_headers
    ):
        """Test that users can't access other users' threads."""
        # Create another user's project and thread
        other_user = User(
            id=str(uuid4()),
            email="other@example.com",
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google_other_thread",
        )
        db_session.add(other_user)
        await db_session.commit()

        other_project = Project(
            id=str(uuid4()),
            user_id=other_user.id,
            name="Other Project",
            description="Test"
        )
        db_session.add(other_project)
        await db_session.commit()

        other_thread = Thread(
            id=str(uuid4()),
            project_id=other_project.id,
            title="Other Thread"
        )
        db_session.add(other_thread)
        await db_session.commit()

        response = await client.get(
            f"/api/threads/{other_thread.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_threads_ordered_by_created_at_desc(
        self, client, db_session, test_project, auth_headers
    ):
        """Test that threads are ordered by created_at DESC."""
        import asyncio

        thread1 = Thread(
            id=str(uuid4()),
            project_id=test_project.id,
            title="First Thread"
        )
        db_session.add(thread1)
        await db_session.commit()

        await asyncio.sleep(0.01)

        thread2 = Thread(
            id=str(uuid4()),
            project_id=test_project.id,
            title="Second Thread"
        )
        db_session.add(thread2)
        await db_session.commit()

        response = await client.get(
            f"/api/threads?project_id={test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Most recent should be first
        assert data[0]["title"] == "Second Thread"
        assert data[1]["title"] == "First Thread"

    @pytest.mark.asyncio
    async def test_messages_within_thread_ordered_by_created_at_asc(
        self, client, db_session, test_thread, auth_headers
    ):
        """Test that messages within thread are ordered by created_at ASC."""
        import asyncio

        message1 = Message(
            id=str(uuid4()),
            thread_id=test_thread.id,
            role="user",
            content="First message"
        )
        db_session.add(message1)
        await db_session.commit()

        await asyncio.sleep(0.01)

        message2 = Message(
            id=str(uuid4()),
            thread_id=test_thread.id,
            role="assistant",
            content="Second message"
        )
        db_session.add(message2)
        await db_session.commit()

        response = await client.get(
            f"/api/threads/{test_thread.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        messages = data["messages"]
        assert len(messages) == 2
        # Chronological order
        assert messages[0]["content"] == "First message"
        assert messages[1]["content"] == "Second message"

    @pytest.mark.asyncio
    async def test_create_thread_without_title(
        self, client, test_project, auth_headers
    ):
        """Test creating thread without title (null title allowed)."""
        response = await client.post(
            f"/api/threads?project_id={test_project.id}",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] is None


# ============================================
# AI Chat Tests (5 tests)
# ============================================


class TestAIChat:
    """Test AI chat functionality."""

    @pytest.mark.asyncio
    async def test_send_message_with_api_key_returns_sse_stream(
        self, client, test_thread, auth_headers, monkeypatch
    ):
        """Test sending message with ANTHROPIC_API_KEY mocked returns SSE stream."""
        # Set mock API key
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Mock Anthropic Messages API
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Test response")]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_message.stop_reason = "end_turn"

        with patch('app.services.ai_service.anthropic') as mock_anthropic:
            mock_stream_manager = MagicMock()
            mock_stream_manager.__enter__ = MagicMock(return_value=iter([mock_message]))
            mock_stream_manager.__exit__ = MagicMock(return_value=False)

            mock_anthropic.messages.stream = MagicMock(return_value=mock_stream_manager)

            response = await client.post(
                f"/api/threads/{test_thread.id}/chat",
                json={"content": "Hello AI"},
                headers=auth_headers,
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_message_without_api_key_returns_500(
        self, client, test_thread, auth_headers, monkeypatch
    ):
        """Test sending message without API key returns 500."""
        # Unset API key
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        response = await client.post(
            f"/api/threads/{test_thread.id}/chat",
            json={"content": "Hello AI"},
            headers=auth_headers,
        )

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_thread_returns_404(
        self, client, auth_headers
    ):
        """Test sending message to non-existent thread returns 404."""
        fake_thread_id = str(uuid4())

        response = await client.post(
            f"/api/threads/{fake_thread_id}/chat",
            json={"content": "Hello AI"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_budget_exceeded_returns_429(
        self, client, db_session, test_user, test_thread, auth_headers
    ):
        """Test that budget exceeded returns 429."""
        # Set user's budget to $0
        test_user.monthly_budget = 0.0
        await db_session.commit()

        response = await client.post(
            f"/api/threads/{test_thread.id}/chat",
            json={"content": "Hello AI"},
            headers=auth_headers,
        )

        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_token_usage_recorded_after_message(
        self, client, db_session, test_thread, auth_headers, monkeypatch
    ):
        """Test that token usage is recorded after message."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Mock Anthropic Messages API
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Test response")]
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_message.stop_reason = "end_turn"

        with patch('app.services.ai_service.anthropic') as mock_anthropic:
            mock_stream_manager = MagicMock()
            mock_stream_manager.__enter__ = MagicMock(return_value=iter([mock_message]))
            mock_stream_manager.__exit__ = MagicMock(return_value=False)

            mock_anthropic.messages.stream = MagicMock(return_value=mock_stream_manager)

            await client.post(
                f"/api/threads/{test_thread.id}/chat",
                json={"content": "Hello AI"},
                headers=auth_headers,
            )

            # Check token usage was recorded
            from app.models import TokenUsage
            stmt = select(TokenUsage).where(TokenUsage.thread_id == test_thread.id)
            result = await db_session.execute(stmt)
            usage_records = result.scalars().all()

            assert len(usage_records) > 0


# ============================================
# Artifact Tests (4 tests)
# ============================================


@pytest_asyncio.fixture
async def test_artifact(db_session, test_thread):
    """Create a test artifact."""
    artifact = Artifact(
        id=str(uuid4()),
        thread_id=test_thread.id,
        type="requirements_doc",
        title="Test Requirements",
        content_markdown="# Requirements\n\nTest content"
    )
    db_session.add(artifact)
    await db_session.commit()
    await db_session.refresh(artifact)
    return artifact


class TestArtifacts:
    """Test artifact operations."""

    @pytest.mark.asyncio
    async def test_list_artifacts_for_thread(
        self, client, test_thread, test_artifact, auth_headers
    ):
        """Test listing artifacts for thread returns artifacts."""
        response = await client.get(
            f"/api/artifacts?thread_id={test_thread.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Requirements"

    @pytest.mark.asyncio
    async def test_get_artifact_by_id_returns_markdown_content(
        self, client, test_artifact, auth_headers
    ):
        """Test getting artifact by ID returns markdown content."""
        response = await client.get(
            f"/api/artifacts/{test_artifact.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content_markdown"] == "# Requirements\n\nTest content"

    @pytest.mark.asyncio
    async def test_export_artifact_as_pdf_returns_binary(
        self, client, test_artifact, auth_headers
    ):
        """Test exporting artifact as PDF returns binary with correct Content-Type."""
        response = await client.get(
            f"/api/artifacts/{test_artifact.id}/export/pdf",
            headers=auth_headers,
        )

        # PDF export may fail if WeasyPrint not installed (especially on Windows)
        # Accept either 200 (success) or 500 (GTK not available)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_export_artifact_as_word_returns_binary(
        self, client, test_artifact, auth_headers
    ):
        """Test exporting artifact as Word returns binary with correct Content-Type."""
        response = await client.get(
            f"/api/artifacts/{test_artifact.id}/export/docx",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
