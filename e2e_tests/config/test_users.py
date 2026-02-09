"""
Test user credentials and tokens for E2E tests.
"""
import os
from dataclasses import dataclass
from typing import Optional
import jwt
from datetime import datetime, timedelta, timezone


@dataclass
class TestUser:
    """Test user data structure."""

    id: str
    email: str
    name: str
    provider: str = "google"
    picture: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "provider": self.provider,
            "picture": self.picture or f"https://ui-avatars.com/api/?name={self.name}",
        }


class TestUsers:
    """Test user configurations."""

    # Default test user
    DEFAULT = TestUser(
        id="test-user-001",
        email="test@example.com",
        name="Test User",
        provider="google",
    )

    # Admin test user
    ADMIN = TestUser(
        id="test-admin-001",
        email="admin@example.com",
        name="Admin User",
        provider="microsoft",
    )

    # Secondary test user for multi-user scenarios
    SECONDARY = TestUser(
        id="test-user-002",
        email="secondary@example.com",
        name="Secondary User",
        provider="google",
    )

    @staticmethod
    def generate_token(
        user: TestUser,
        secret: str = "test-secret-key-for-e2e-tests",
        expires_in_hours: int = 24
    ) -> str:
        """
        Generate a JWT token for testing.

        Note: This token is for testing purposes only.
        In production, tokens come from the real OAuth flow.
        """
        payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "provider": user.provider,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def get_expired_token(user: TestUser) -> str:
        """Generate an expired token for testing auth failures."""
        payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "provider": user.provider,
            "iat": datetime.now(timezone.utc) - timedelta(hours=48),
            "exp": datetime.now(timezone.utc) - timedelta(hours=24),
        }
        return jwt.encode(payload, "test-secret-key-for-e2e-tests", algorithm="HS256")

    @staticmethod
    def get_invalid_token() -> str:
        """Get an invalid/malformed token for testing."""
        return "invalid.token.here"


# Pre-generated tokens for convenience
# These can be overridden via environment variables
DEFAULT_TOKEN = os.getenv(
    "E2E_DEFAULT_TOKEN",
    TestUsers.generate_token(TestUsers.DEFAULT)
)

ADMIN_TOKEN = os.getenv(
    "E2E_ADMIN_TOKEN",
    TestUsers.generate_token(TestUsers.ADMIN)
)
