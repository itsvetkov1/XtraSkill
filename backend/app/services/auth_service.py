"""
OAuth 2.0 authentication service.

Handles OAuth flows for Google and Microsoft providers, including:
- Authorization URL generation with CSRF protection
- OAuth callback processing and token exchange
- User profile retrieval from provider APIs
- User creation/update in database
"""

import secrets
from typing import Optional

from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import OAuthProvider, User


class OAuth2Service:
    """Service for OAuth 2.0 authentication flows."""

    # Google OAuth configuration
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_SCOPES = ["openid", "email", "profile"]

    # Microsoft OAuth configuration
    MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"
    MICROSOFT_SCOPES = ["openid", "email", "profile", "User.Read"]

    def __init__(self, db: AsyncSession):
        """
        Initialize OAuth service.

        Args:
            db: Database session for user operations
        """
        self.db = db

    def _generate_state(self) -> str:
        """
        Generate random state parameter for CSRF protection.

        Returns:
            Random 32-character hex string
        """
        return secrets.token_hex(16)

    async def get_google_auth_url(self, redirect_uri: str) -> tuple[str, str]:
        """
        Generate Google OAuth authorization URL.

        Args:
            redirect_uri: Callback URL after OAuth approval

        Returns:
            Tuple of (authorization_url, state_parameter)
        """
        state = self._generate_state()

        client = AsyncOAuth2Client(
            client_id=settings.google_client_id,
            redirect_uri=redirect_uri,
        )

        authorization_url, _ = client.create_authorization_url(
            self.GOOGLE_AUTH_URL,
            scope=self.GOOGLE_SCOPES,
            state=state,
        )

        return authorization_url, state

    async def process_google_callback(
        self,
        code: str,
        state: str,
        expected_state: str,
        redirect_uri: str,
    ) -> User:
        """
        Process Google OAuth callback and create/update user.

        Args:
            code: Authorization code from Google
            state: State parameter from callback
            expected_state: Expected state value (CSRF check)
            redirect_uri: Redirect URI used in initial request

        Returns:
            User object (created or updated)

        Raises:
            ValueError: If state parameter doesn't match (CSRF attack)
            Exception: If OAuth exchange or user fetch fails
        """
        # CSRF protection
        if state != expected_state:
            raise ValueError("State parameter mismatch - possible CSRF attack")

        # Exchange authorization code for access token
        client = AsyncOAuth2Client(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=redirect_uri,
        )

        token = await client.fetch_token(
            self.GOOGLE_TOKEN_URL,
            code=code,
        )

        # Fetch user profile from Google
        client.token = token
        response = await client.get(self.GOOGLE_USERINFO_URL)
        user_info = response.json()

        # Extract user data
        oauth_id = user_info["id"]
        email = user_info["email"]
        display_name = user_info.get("name")

        # Create or update user in database
        user = await self._upsert_user(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_id=oauth_id,
            email=email,
            display_name=display_name,
        )

        return user

    async def get_microsoft_auth_url(self, redirect_uri: str) -> tuple[str, str]:
        """
        Generate Microsoft OAuth authorization URL.

        Args:
            redirect_uri: Callback URL after OAuth approval

        Returns:
            Tuple of (authorization_url, state_parameter)
        """
        state = self._generate_state()

        client = AsyncOAuth2Client(
            client_id=settings.microsoft_client_id,
            redirect_uri=redirect_uri,
        )

        authorization_url, _ = client.create_authorization_url(
            self.MICROSOFT_AUTH_URL,
            scope=self.MICROSOFT_SCOPES,
            state=state,
        )

        return authorization_url, state

    async def process_microsoft_callback(
        self,
        code: str,
        state: str,
        expected_state: str,
        redirect_uri: str,
    ) -> User:
        """
        Process Microsoft OAuth callback and create/update user.

        Args:
            code: Authorization code from Microsoft
            state: State parameter from callback
            expected_state: Expected state value (CSRF check)
            redirect_uri: Redirect URI used in initial request

        Returns:
            User object (created or updated)

        Raises:
            ValueError: If state parameter doesn't match (CSRF attack)
            Exception: If OAuth exchange or user fetch fails
        """
        # CSRF protection
        if state != expected_state:
            raise ValueError("State parameter mismatch - possible CSRF attack")

        # Exchange authorization code for access token
        client = AsyncOAuth2Client(
            client_id=settings.microsoft_client_id,
            client_secret=settings.microsoft_client_secret,
            redirect_uri=redirect_uri,
        )

        token = await client.fetch_token(
            self.MICROSOFT_TOKEN_URL,
            code=code,
        )

        # Fetch user profile from Microsoft Graph API
        client.token = token
        response = await client.get(self.MICROSOFT_USERINFO_URL)
        user_info = response.json()

        # Extract user data
        oauth_id = user_info["id"]
        email = user_info["mail"] or user_info.get("userPrincipalName")
        display_name = user_info.get("displayName")

        # Create or update user in database
        user = await self._upsert_user(
            oauth_provider=OAuthProvider.MICROSOFT,
            oauth_id=oauth_id,
            email=email,
            display_name=display_name,
        )

        return user

    async def _upsert_user(
        self,
        oauth_provider: OAuthProvider,
        oauth_id: str,
        email: str,
        display_name: Optional[str] = None,
    ) -> User:
        """
        Create new user or update existing user by oauth_provider + oauth_id.

        Args:
            oauth_provider: OAuth provider (Google or Microsoft)
            oauth_id: Provider-specific user ID
            email: User's email address
            display_name: User's display name from OAuth provider

        Returns:
            User object (created or existing)
        """
        # Check if user exists
        stmt = select(User).where(
            User.oauth_provider == oauth_provider,
            User.oauth_id == oauth_id,
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update existing user (in case email or display name changed)
            user.email = email
            user.display_name = display_name
        else:
            # Create new user
            user = User(
                oauth_provider=oauth_provider,
                oauth_id=oauth_id,
                email=email,
                display_name=display_name,
            )
            self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)

        return user
