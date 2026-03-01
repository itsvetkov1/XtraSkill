"""Unit tests for OpenClaw sub-agent spawner."""
import pytest

import sys
sys.path.insert(0, '/home/i_tsvetkov/XtraSkill/backend')

from app.services.openclaw_tools.subagent import OpenClawSubAgent, default_subagent


class TestOpenClawSubAgent:
    """Test cases for OpenClawSubAgent."""

    def test_valid_agents(self):
        """Test valid agent types."""
        assert "dev" in OpenClawSubAgent.VALID_AGENTS
        assert "debugger" in OpenClawSubAgent.VALID_AGENTS
        assert "code-reviewer" in OpenClawSubAgent.VALID_AGENTS
        assert "architect" in OpenClawSubAgent.VALID_AGENTS

    def test_default_instance_exists(self):
        """Test default_subagent exists."""
        assert default_subagent is not None

    @pytest.mark.asyncio
    async def test_spawn_invalid_agent_type(self):
        """Test spawn rejects invalid agent type."""
        subagent = OpenClawSubAgent()
        with pytest.raises(ValueError) as exc_info:
            await subagent.spawn(agent_type="invalid", task="do something")
        assert "Invalid agent type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test close works without client."""
        subagent = OpenClawSubAgent()
        assert subagent._client is None
        await subagent.close()
        assert subagent._client is None


class TestSubAgentConfig:
    """Test subagent configuration."""

    def test_default_config(self):
        """Test default configuration."""
        subagent = OpenClawSubAgent()
        assert subagent._gateway_url == "http://localhost:8080"

    def test_custom_config(self):
        """Test custom configuration."""
        subagent = OpenClawSubAgent(
            gateway_url="http://custom:9999",
            api_key="custom-key",
        )
        assert subagent._gateway_url == "http://custom:9999"
        assert subagent._api_key == "custom-key"
