"""
Environment configuration for E2E tests.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class Settings:
    """Test environment settings."""

    # URLs
    BASE_URL: str = os.getenv("E2E_BASE_URL", "http://localhost:8001")
    FRONTEND_URL: str = os.getenv("E2E_FRONTEND_URL", "http://localhost:8080")

    # Timeouts (in milliseconds for Playwright)
    TIMEOUT_DEFAULT: int = int(os.getenv("E2E_TIMEOUT_DEFAULT", "10000"))
    TIMEOUT_LONG: int = int(os.getenv("E2E_TIMEOUT_LONG", "30000"))
    TIMEOUT_SHORT: int = int(os.getenv("E2E_TIMEOUT_SHORT", "5000"))

    # Browser settings
    HEADLESS: bool = os.getenv("E2E_HEADLESS", "true").lower() == "true"
    SLOW_MO: int = int(os.getenv("E2E_SLOW_MO", "0"))  # Slow down actions by ms

    # Viewport
    VIEWPORT_WIDTH: int = int(os.getenv("E2E_VIEWPORT_WIDTH", "1280"))
    VIEWPORT_HEIGHT: int = int(os.getenv("E2E_VIEWPORT_HEIGHT", "720"))

    # Test data paths
    TEST_FILES_DIR: str = os.path.join(os.path.dirname(__file__), "..", "test_files")

    # Screenshot and video settings
    SCREENSHOT_DIR: str = os.path.join(os.path.dirname(__file__), "..", "screenshots")
    VIDEO_DIR: str = os.path.join(os.path.dirname(__file__), "..", "videos")

    # Retry settings
    MAX_RETRIES: int = int(os.getenv("E2E_MAX_RETRIES", "3"))

    @classmethod
    def get_frontend_url(cls, path: str = "") -> str:
        """Get full frontend URL with optional path."""
        base = cls.FRONTEND_URL.rstrip("/")
        path = path.lstrip("/") if path else ""
        return f"{base}/{path}" if path else base

    @classmethod
    def get_api_url(cls, endpoint: str = "") -> str:
        """Get full API URL with optional endpoint."""
        base = cls.BASE_URL.rstrip("/")
        endpoint = endpoint.lstrip("/") if endpoint else ""
        return f"{base}/{endpoint}" if endpoint else base


# Singleton instance
settings = Settings()
