"""Unit tests for OpenClaw tool mapper."""
import pytest

import sys
sys.path.insert(0, '/home/i_tsvetkov/XtraSkill/backend')

from app.services.openclaw_tools.tool_mapper import OpenClawToolMapper, default_tool_mapper


class TestOpenClawToolMapper:
    """Test cases for OpenClawToolMapper."""

    def test_default_tools_count(self):
        """Test default tool count."""
        assert len(OpenClawToolMapper.TOOL_DEFINITIONS) == 7

    def test_default_tools_include_core(self):
        """Test core XtraSkill tools are included."""
        tool_names = [t["name"] for t in OpenClawToolMapper.TOOL_DEFINITIONS]
        assert "search_documents" in tool_names
        assert "save_artifact" in tool_names

    def test_default_tools_include_skill_tools(self):
        """Test OpenClaw skill tools are included."""
        tool_names = [t["name"] for t in OpenClawToolMapper.TOOL_DEFINITIONS]
        assert "send_email" in tool_names
        assert "check_calendar" in tool_names
        assert "post_twitter" in tool_names

    def test_default_tools_include_subagent(self):
        """Test spawn_subagent tool is included."""
        tool_names = [t["name"] for t in OpenClawToolMapper.TOOL_DEFINITIONS]
        assert "spawn_subagent" in tool_names

    def test_get_tools_returns_all_by_default(self):
        """Test get_tools returns all tools when no filter."""
        mapper = OpenClawToolMapper()
        tools = mapper.get_tools()
        assert len(tools) == 7

    def test_get_tools_filters_disabled(self):
        """Test get_tools filters disabled tools."""
        mapper = OpenClawToolMapper(enabled_tools=["search_documents", "save_artifact"])
        tools = mapper.get_tools()
        assert len(tools) == 2

    def test_is_tool_enabled(self):
        """Test is_tool_enabled check."""
        mapper = OpenClawToolMapper(enabled_tools=["search_documents"])
        assert mapper.is_tool_enabled("search_documents") is True
        # Empty list means nothing enabled
        mapper2 = OpenClawToolMapper(enabled_tools=[])
        assert mapper2.is_tool_enabled("search_documents") is False

    def test_default_instance_exists(self):
        """Test default_tool_mapper instance exists."""
        assert default_tool_mapper is not None
        assert len(default_tool_mapper.get_tools()) == 7


class TestToolDefinitions:
    """Test tool definitions structure."""

    def test_all_tools_have_names(self):
        """Test all tools have names."""
        for tool in OpenClawToolMapper.TOOL_DEFINITIONS:
            assert "name" in tool
            assert tool["name"]

    def test_all_tools_have_descriptions(self):
        """Test all tools have descriptions."""
        for tool in OpenClawToolMapper.TOOL_DEFINITIONS:
            assert "description" in tool
            assert tool["description"]

    def test_all_tools_have_input_schema(self):
        """Test all tools have input schemas."""
        for tool in OpenClawToolMapper.TOOL_DEFINITIONS:
            assert "input_schema" in tool

    def test_spawn_subagent_has_agent_type_enum(self):
        """Test spawn_subagent has correct enum."""
        for tool in OpenClawToolMapper.TOOL_DEFINITIONS:
            if tool["name"] == "spawn_subagent":
                props = tool["input_schema"]["properties"]
                assert "agent_type" in props
