"""Unit tests for OpenClaw configuration."""
import pytest

import sys
sys.path.insert(0, '/home/i_tsvetkov/XtraSkill/backend')

from app.config import Settings


class TestOpenClawConfig:
    """Test OpenClaw configuration in Settings."""

    def test_openclaw_defaults(self):
        """Test OpenClaw settings have correct defaults."""
        settings = Settings()
        
        assert settings.openclaw_api_key == ""
        assert settings.openclaw_gateway_url == "http://localhost:8080"
        assert settings.openclaw_agent_id == "dev"

    def test_openclaw_can_be_set(self):
        """Test OpenClaw settings can be customized."""
        settings = Settings(
            openclaw_api_key="test-key-123",
            openclaw_gateway_url="http://custom:9999",
            openclaw_agent_id="forger",
        )
        
        assert settings.openclaw_api_key == "test-key-123"
        assert settings.openclaw_gateway_url == "http://custom:9999"
        assert settings.openclaw_agent_id == "forger"
