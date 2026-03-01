"""Integration tests for OpenClaw adapter."""
import pytest

import sys
sys.path.insert(0, '/home/i_tsvetkov/XtraSkill/backend')

from app.services.llm.factory import LLMFactory
from app.services.llm.base import LLMProvider


class TestLLMFactoryOpenClaw:
    """Test LLMFactory with OpenClaw provider."""

    def test_openclaw_registered_in_factory(self):
        """Test OpenClaw is registered in factory."""
        providers = LLMFactory.list_providers()
        assert "openclaw" in providers

    def test_factory_creates_openclaw_adapter(self):
        """Test factory can create OpenClaw adapter."""
        # This will fail without API key, but tests the registry
        with pytest.raises(ValueError) as exc:
            LLMFactory.create("openclaw")
        
        assert "OPENCLAW_API_KEY" in str(exc.value)


class TestOpenClawIntegration:
    """Integration tests for OpenClaw components."""

    def test_all_components_importable(self):
        """Test all OpenClaw components can be imported."""
        from app.services.llm.openclaw_adapter import OpenClawAdapter
        from app.services.openclaw_tools import OpenClawToolMapper, OpenClawSubAgent
        
        assert OpenClawAdapter is not None
        assert OpenClawToolMapper is not None
        assert OpenClawSubAgent is not None

    def test_tool_mapper_integration(self):
        """Test tool mapper integrates with adapter."""
        from app.services.openclaw_tools import OpenClawToolMapper
        
        mapper = OpenClawToolMapper()
        tools = mapper.get_tools()
        
        assert len(tools) > 0
        assert all("name" in t for t in tools)
        assert all("description" in t for t in tools)

    def test_subagent_valid_agents(self):
        """Test subagent has valid agent types."""
        from app.services.openclaw_tools import OpenClawSubAgent
        
        # Test via the class attribute
        assert hasattr(OpenClawSubAgent, 'VALID_AGENTS')
        assert "dev" in OpenClawSubAgent.VALID_AGENTS

    def test_full_tool_flow(self):
        """Test full flow: factory -> adapter -> tools."""
        from app.services.llm.openclaw_adapter import OpenClawAdapter
        from app.services.openclaw_tools import OpenClawToolMapper
        
        # Create adapter (will need API key to actually work)
        adapter = OpenClawAdapter(
            api_key="test-key",
            gateway_url="http://localhost:8080",
            agent_id="dev",
        )
        
        # Get tools
        mapper = OpenClawToolMapper()
        tools = mapper.get_tools()
        
        # Verify integration points
        assert adapter.provider.value == "openclaw"
        assert len(tools) == 7
