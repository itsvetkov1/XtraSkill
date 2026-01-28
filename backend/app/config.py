"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables with validation.
"""

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./ba_assistant.db"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"

    # OAuth 2.0
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""

    # AI Service
    anthropic_api_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    # Environment
    environment: str = "development"

    # Encryption (for document storage)
    fernet_key: str = ""

    # Skill configuration
    skill_path: str = ".claude/business-analyst"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def oauth_redirect_base_url(self) -> str:
        """OAuth redirect base URL varies by environment."""
        if self.environment == "production":
            # Read from BACKEND_URL env var (e.g., https://api.example.com)
            backend_url = os.getenv("BACKEND_URL", "")
            if not backend_url:
                raise ValueError("BACKEND_URL must be set in production for OAuth redirects")
            return backend_url
        return "http://localhost:8000"  # Development default

    def validate_required(self) -> None:
        """
        Validate that required configuration is present.

        Raises ValueError if critical config is missing.
        """
        if self.environment == "production":
            # Check SECRET_KEY
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed for production. "
                    "Generate a secure key with: openssl rand -hex 32"
                )

            # Check ANTHROPIC_API_KEY
            if not self.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY must be set for AI features. "
                    "Get API key from https://console.anthropic.com/"
                )

            # Check OAuth credentials
            if not self.google_client_id or not self.microsoft_client_id:
                raise ValueError(
                    "OAuth credentials required for production. "
                    "Create separate OAuth app registrations for production environment."
                )

            # Warn about SQLite in production
            if "sqlite" in self.database_url.lower():
                print(
                    "WARNING: Using SQLite in production. "
                    "Consider PostgreSQL for better concurrency and data safety."
                )


# Global settings instance
settings = Settings()
