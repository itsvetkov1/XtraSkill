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

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def validate_required(self) -> None:
        """
        Validate that required configuration is present.

        Raises ValueError if critical config is missing.
        """
        if self.environment == "production":
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY must be set for AI features")


# Global settings instance
settings = Settings()
