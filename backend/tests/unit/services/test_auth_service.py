"""Unit tests for auth_service OAuth2Service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.auth_service import OAuth2Service
from app.models import OAuthProvider, User


class TestGenerateState:
    """Tests for _generate_state method."""

    def test_generates_32_char_hex(self, db_session):
        """State is 32-character hex string."""
        service = OAuth2Service(db_session)
        state = service._generate_state()

        assert len(state) == 32
        assert all(c in "0123456789abcdef" for c in state)

    def test_generates_unique_states(self, db_session):
        """Each call generates unique state."""
        service = OAuth2Service(db_session)

        states = [service._generate_state() for _ in range(10)]

        assert len(set(states)) == 10  # All unique


class TestGetGoogleAuthUrl:
    """Tests for get_google_auth_url method."""

    @pytest.mark.asyncio
    async def test_returns_url_and_state(self, db_session):
        """Returns authorization URL and state parameter."""
        service = OAuth2Service(db_session)

        with patch.object(service, '_generate_state', return_value='test-state-123'):
            url, state = await service.get_google_auth_url("http://localhost/callback")

        assert state == "test-state-123"
        assert "accounts.google.com" in url
        assert "state=test-state-123" in url

    @pytest.mark.asyncio
    async def test_includes_scopes_in_url(self, db_session):
        """URL includes required OAuth scopes."""
        service = OAuth2Service(db_session)

        url, _ = await service.get_google_auth_url("http://localhost/callback")

        # URL should reference scopes (encoded)
        assert "scope=" in url


class TestGetMicrosoftAuthUrl:
    """Tests for get_microsoft_auth_url method."""

    @pytest.mark.asyncio
    async def test_returns_url_and_state(self, db_session):
        """Returns Microsoft authorization URL and state."""
        service = OAuth2Service(db_session)

        with patch.object(service, '_generate_state', return_value='ms-state-456'):
            url, state = await service.get_microsoft_auth_url("http://localhost/callback")

        assert state == "ms-state-456"
        assert "login.microsoftonline.com" in url

    @pytest.mark.asyncio
    async def test_includes_callback_in_url(self, db_session):
        """URL includes redirect_uri parameter."""
        service = OAuth2Service(db_session)

        url, _ = await service.get_microsoft_auth_url("http://localhost/callback")

        assert "redirect_uri=" in url


class TestProcessGoogleCallback:
    """Tests for process_google_callback method."""

    @pytest.mark.asyncio
    async def test_csrf_validation_fails_on_mismatch(self, db_session):
        """Raises ValueError when state doesn't match."""
        service = OAuth2Service(db_session)

        with pytest.raises(ValueError, match="CSRF"):
            await service.process_google_callback(
                code="auth-code",
                state="received-state",
                expected_state="different-state",
                redirect_uri="http://localhost/callback"
            )

    @pytest.mark.asyncio
    async def test_creates_new_user(self, db_session):
        """Creates new user when OAuth user doesn't exist."""
        service = OAuth2Service(db_session)

        # Mock the OAuth client
        mock_client = AsyncMock()
        mock_client.fetch_token = AsyncMock(return_value={"access_token": "token123"})
        mock_client.get = AsyncMock(return_value=Mock(json=lambda: {
            "id": "google-user-123",
            "email": "test@example.com",
            "name": "Test User"
        }))

        with patch('app.services.auth_service.AsyncOAuth2Client', return_value=mock_client):
            user = await service.process_google_callback(
                code="auth-code",
                state="same-state",
                expected_state="same-state",
                redirect_uri="http://localhost/callback"
            )

        assert user.email == "test@example.com"
        assert user.oauth_provider == OAuthProvider.GOOGLE
        assert user.oauth_id == "google-user-123"
        assert user.display_name == "Test User"

    @pytest.mark.asyncio
    async def test_updates_existing_user(self, db_session):
        """Updates existing user's email and display_name."""
        # Create existing user with Google OAuth
        existing_user = User(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google-existing-123",
            email="old@example.com",
            display_name="Old Name"
        )
        db_session.add(existing_user)
        await db_session.commit()
        user_id = existing_user.id

        service = OAuth2Service(db_session)

        mock_client = AsyncMock()
        mock_client.fetch_token = AsyncMock(return_value={"access_token": "token"})
        mock_client.get = AsyncMock(return_value=Mock(json=lambda: {
            "id": "google-existing-123",  # Same OAuth ID
            "email": "new@example.com",   # Updated email
            "name": "New Name"            # Updated name
        }))

        with patch('app.services.auth_service.AsyncOAuth2Client', return_value=mock_client):
            result = await service.process_google_callback(
                code="code",
                state="state",
                expected_state="state",
                redirect_uri="http://localhost/callback"
            )

        # Should be same user with updated info
        assert result.id == user_id
        assert result.email == "new@example.com"
        assert result.display_name == "New Name"

    @pytest.mark.asyncio
    async def test_handles_missing_name(self, db_session):
        """Handles missing name field in Google response."""
        service = OAuth2Service(db_session)

        mock_client = AsyncMock()
        mock_client.fetch_token = AsyncMock(return_value={"access_token": "token"})
        mock_client.get = AsyncMock(return_value=Mock(json=lambda: {
            "id": "google-no-name",
            "email": "noname@example.com"
            # No "name" field
        }))

        with patch('app.services.auth_service.AsyncOAuth2Client', return_value=mock_client):
            user = await service.process_google_callback(
                code="code",
                state="s",
                expected_state="s",
                redirect_uri="http://localhost"
            )

        assert user.email == "noname@example.com"
        assert user.display_name is None


class TestProcessMicrosoftCallback:
    """Tests for process_microsoft_callback method."""

    @pytest.mark.asyncio
    async def test_csrf_validation_fails(self, db_session):
        """Raises ValueError on state mismatch."""
        service = OAuth2Service(db_session)

        with pytest.raises(ValueError, match="CSRF"):
            await service.process_microsoft_callback(
                code="code",
                state="wrong",
                expected_state="correct",
                redirect_uri="http://localhost/callback"
            )

    @pytest.mark.asyncio
    async def test_creates_user_from_microsoft(self, db_session):
        """Creates user from Microsoft Graph API response."""
        service = OAuth2Service(db_session)

        mock_client = AsyncMock()
        mock_client.fetch_token = AsyncMock(return_value={"access_token": "ms-token"})
        mock_client.get = AsyncMock(return_value=Mock(json=lambda: {
            "id": "ms-user-456",
            "mail": "msuser@company.com",
            "displayName": "MS User"
        }))

        with patch('app.services.auth_service.AsyncOAuth2Client', return_value=mock_client):
            user = await service.process_microsoft_callback(
                code="code",
                state="state",
                expected_state="state",
                redirect_uri="http://localhost/callback"
            )

        assert user.oauth_provider == OAuthProvider.MICROSOFT
        assert user.oauth_id == "ms-user-456"
        assert user.email == "msuser@company.com"

    @pytest.mark.asyncio
    async def test_uses_upn_when_mail_missing(self, db_session):
        """Uses userPrincipalName when mail is null."""
        service = OAuth2Service(db_session)

        mock_client = AsyncMock()
        mock_client.fetch_token = AsyncMock(return_value={"access_token": "token"})
        mock_client.get = AsyncMock(return_value=Mock(json=lambda: {
            "id": "ms-user-789",
            "mail": None,
            "userPrincipalName": "user@contoso.onmicrosoft.com",
            "displayName": "User"
        }))

        with patch('app.services.auth_service.AsyncOAuth2Client', return_value=mock_client):
            user = await service.process_microsoft_callback(
                code="code",
                state="s",
                expected_state="s",
                redirect_uri="http://localhost"
            )

        assert user.email == "user@contoso.onmicrosoft.com"

    @pytest.mark.asyncio
    async def test_updates_existing_microsoft_user(self, db_session):
        """Updates existing Microsoft OAuth user."""
        # Create existing Microsoft user
        existing_user = User(
            oauth_provider=OAuthProvider.MICROSOFT,
            oauth_id="ms-existing-user",
            email="old@contoso.com",
            display_name="Old MS User"
        )
        db_session.add(existing_user)
        await db_session.commit()
        user_id = existing_user.id

        service = OAuth2Service(db_session)

        mock_client = AsyncMock()
        mock_client.fetch_token = AsyncMock(return_value={"access_token": "token"})
        mock_client.get = AsyncMock(return_value=Mock(json=lambda: {
            "id": "ms-existing-user",  # Same OAuth ID
            "mail": "updated@contoso.com",
            "displayName": "Updated MS User"
        }))

        with patch('app.services.auth_service.AsyncOAuth2Client', return_value=mock_client):
            result = await service.process_microsoft_callback(
                code="code",
                state="state",
                expected_state="state",
                redirect_uri="http://localhost"
            )

        assert result.id == user_id
        assert result.email == "updated@contoso.com"
        assert result.display_name == "Updated MS User"


class TestUpsertUser:
    """Tests for _upsert_user method."""

    @pytest.mark.asyncio
    async def test_creates_new_user(self, db_session):
        """Creates new user when not found."""
        service = OAuth2Service(db_session)

        user = await service._upsert_user(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="new-user-id",
            email="new@test.com",
            display_name="New User"
        )

        assert user.oauth_id == "new-user-id"
        assert user.email == "new@test.com"

    @pytest.mark.asyncio
    async def test_updates_existing_user(self, db_session):
        """Updates existing user's info."""
        # Create existing user
        existing = User(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="existing-id",
            email="old@test.com",
            display_name="Old"
        )
        db_session.add(existing)
        await db_session.commit()
        user_id = existing.id

        service = OAuth2Service(db_session)

        # Upsert with same OAuth ID but different info
        user = await service._upsert_user(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="existing-id",
            email="updated@test.com",
            display_name="Updated"
        )

        assert user.id == user_id  # Same user
        assert user.email == "updated@test.com"
        assert user.display_name == "Updated"

    @pytest.mark.asyncio
    async def test_multiple_users_identified_correctly(self, db_session):
        """Multiple users with different OAuth IDs are handled correctly."""
        service = OAuth2Service(db_session)

        # Create first user
        user1 = await service._upsert_user(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google-user-1",
            email="user1@test.com"
        )

        # Create second user with different OAuth ID
        user2 = await service._upsert_user(
            oauth_provider=OAuthProvider.MICROSOFT,
            oauth_id="ms-user-2",
            email="user2@test.com"
        )

        # Both users should exist with different IDs
        assert user1.id != user2.id
        assert user1.oauth_id == "google-user-1"
        assert user2.oauth_id == "ms-user-2"

        # Upsert first user again - should return same user
        user1_again = await service._upsert_user(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="google-user-1",
            email="updated1@test.com"
        )

        assert user1_again.id == user1.id
        assert user1_again.email == "updated1@test.com"

    @pytest.mark.asyncio
    async def test_handles_none_display_name(self, db_session):
        """Handles None display_name gracefully."""
        service = OAuth2Service(db_session)

        user = await service._upsert_user(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="no-name-user",
            email="noname@test.com",
            display_name=None
        )

        assert user.display_name is None

    @pytest.mark.asyncio
    async def test_user_persisted_to_database(self, db_session):
        """Created user is actually persisted to database."""
        service = OAuth2Service(db_session)

        user = await service._upsert_user(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id="persist-test",
            email="persist@test.com"
        )

        # Query again to ensure it's in DB
        from sqlalchemy import select
        stmt = select(User).where(User.oauth_id == "persist-test")
        result = await db_session.execute(stmt)
        db_user = result.scalar_one_or_none()

        assert db_user is not None
        assert db_user.id == user.id
        assert db_user.email == "persist@test.com"
