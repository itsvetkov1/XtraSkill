"""
Tests to verify which AI service architecture is active.

Created: 2026-02-04
Purpose: Confirm whether Claude Agent SDK or direct API approach is used.

Results will show:
- If test_direct_api_approach passes: Direct anthropic package is in use
- If test_agent_sdk_approach passes: Claude Agent SDK is in use
"""
import pytest
import ast
import importlib.util
from pathlib import Path


class TestServiceArchitecture:
    """Verify which AI service is wired into the routes."""

    def test_conversations_route_imports_ai_service(self):
        """
        Verify conversations.py imports AIService from ai_service, NOT AgentService.

        This is the definitive test - it checks what the route actually uses.
        """
        route_file = Path(__file__).parent.parent / "app" / "routes" / "conversations.py"
        source = route_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "ai_service" in node.module:
                    imports.append(("ai_service", [alias.name for alias in node.names]))
                if node.module and "agent_service" in node.module:
                    imports.append(("agent_service", [alias.name for alias in node.names]))

        # Should import from ai_service
        ai_service_imports = [i for i in imports if i[0] == "ai_service"]
        assert len(ai_service_imports) > 0, "Route should import from ai_service"
        assert "AIService" in ai_service_imports[0][1], "Route should import AIService class"

        # Should NOT import from agent_service
        agent_service_imports = [i for i in imports if i[0] == "agent_service"]
        assert len(agent_service_imports) == 0, "Route should NOT import from agent_service"

    def test_ai_service_has_hardcoded_system_prompt(self):
        """
        Verify ai_service.py has a hardcoded SYSTEM_PROMPT constant.

        The direct API approach embeds the system prompt in the code.
        """
        service_file = Path(__file__).parent.parent / "app" / "services" / "ai_service.py"
        source = service_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Find module-level assignments
        system_prompt_found = False
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT":
                        system_prompt_found = True
                        # Check it's a string constant
                        assert isinstance(node.value, ast.Constant), "SYSTEM_PROMPT should be a string constant"
                        assert isinstance(node.value.value, str), "SYSTEM_PROMPT should be a string"
                        assert len(node.value.value) > 1000, "SYSTEM_PROMPT should be substantial (>1000 chars)"

        assert system_prompt_found, "ai_service.py should have SYSTEM_PROMPT constant"

    def test_ai_service_does_not_use_skill_loader(self):
        """
        Verify ai_service.py does NOT import skill_loader.

        The direct API approach doesn't need the skill loader.
        """
        service_file = Path(__file__).parent.parent / "app" / "services" / "ai_service.py"
        source = service_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "skill_loader" in node.module:
                    pytest.fail("ai_service.py should NOT import skill_loader")



    def test_system_prompt_contains_business_analyst_content(self):
        """
        Verify SYSTEM_PROMPT contains key business analyst instructions.

        This confirms the skill content was properly transformed.
        """
        service_file = Path(__file__).parent.parent / "app" / "services" / "ai_service.py"
        source = service_file.read_text(encoding="utf-8")

        # Key phrases that should be in the system prompt
        required_phrases = [
            "business requirements",
            "one question at a time",  # or variant
            "BRD",  # Business Requirements Document
            "discovery",
            "save_artifact",
            "search_documents"
        ]

        for phrase in required_phrases:
            assert phrase.lower() in source.lower(), f"SYSTEM_PROMPT should contain '{phrase}'"


class TestToolDefinitions:
    """Verify tool definitions are in the correct location."""

    def test_ai_service_defines_tools_inline(self):
        """
        Verify ai_service.py defines tools as dict constants.

        The direct API approach uses inline tool definitions.
        """
        service_file = Path(__file__).parent.parent / "app" / "services" / "ai_service.py"
        source = service_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        tool_constants = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if "TOOL" in target.id:
                            tool_constants.append(target.id)

        assert "DOCUMENT_SEARCH_TOOL" in tool_constants, "Should define DOCUMENT_SEARCH_TOOL"
        assert "SAVE_ARTIFACT_TOOL" in tool_constants, "Should define SAVE_ARTIFACT_TOOL"


class TestRuntimeVerification:
    """Tests that verify runtime behavior (require imports)."""

    def test_ai_service_class_exists_and_instantiates(self):
        """Verify AIService can be imported and instantiated."""
        from app.services.ai_service import AIService

        # Should instantiate without error
        service = AIService(provider="anthropic")
        assert service is not None
        assert hasattr(service, "stream_chat")
        assert hasattr(service, "tools")
        assert len(service.tools) == 2  # search_documents, save_artifact

    def test_ai_service_system_prompt_is_substantial(self):
        """Verify SYSTEM_PROMPT is loaded and substantial."""
        from app.services.ai_service import SYSTEM_PROMPT

        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 5000, "SYSTEM_PROMPT should be >5000 chars"
        assert "<system_prompt>" in SYSTEM_PROMPT, "Should use XML format"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
