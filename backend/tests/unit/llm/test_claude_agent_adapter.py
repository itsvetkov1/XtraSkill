"""Unit tests for ClaudeAgentAdapter.

Tests verify adapter stub behavior without making real API calls.
The stub raises NotImplementedError until Phase 58 implements stream_chat.
"""

import pytest
from unittest.mock import patch

from app.services.llm.claude_agent_adapter import ClaudeAgentAdapter, DEFAULT_MODEL
from app.services.llm.base import LLMProvider
from app.services.llm import LLMFactory


class TestClaudeAgentAdapterInit:
    """Tests for ClaudeAgentAdapter initialization."""

    def test_initializes_with_api_key(self):
        """API key is stored in adapter instance."""
        adapter = ClaudeAgentAdapter(api_key="test-api-key")

        assert adapter._api_key == "test-api-key"

    def test_uses_default_model(self):
        """DEFAULT_MODEL is used when no model specified."""
        adapter = ClaudeAgentAdapter(api_key="test-key")

        assert adapter.model == DEFAULT_MODEL
        assert adapter.model == "claude-sonnet-4-5-20250514"

    def test_uses_custom_model(self):
        """Custom model parameter is respected."""
        adapter = ClaudeAgentAdapter(
            api_key="test-key",
            model="claude-opus-4-20250514"
        )

        assert adapter.model == "claude-opus-4-20250514"

    def test_provider_returns_claude_code_sdk(self):
        """Provider property returns LLMProvider.CLAUDE_CODE_SDK."""
        adapter = ClaudeAgentAdapter(api_key="test-key")

        assert adapter.provider == LLMProvider.CLAUDE_CODE_SDK
        assert adapter.provider.value == "claude-code-sdk"


class TestClaudeAgentAdapterStreamChat:
    """Tests for ClaudeAgentAdapter.stream_chat method."""

    @pytest.mark.asyncio
    async def test_stream_chat_raises_not_implemented(self):
        """stream_chat raises NotImplementedError with Phase 58 message."""
        adapter = ClaudeAgentAdapter(api_key="test-key")

        with pytest.raises(NotImplementedError, match="Phase 58"):
            async for _ in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                pass


class TestClaudeAgentAdapterFactory:
    """Tests for LLMFactory integration with ClaudeAgentAdapter."""

    @patch('app.services.llm.factory.settings')
    def test_factory_creates_adapter(self, mock_settings):
        """LLMFactory.create('claude-code-sdk') returns ClaudeAgentAdapter."""
        mock_settings.anthropic_api_key = "test-key"

        adapter = LLMFactory.create("claude-code-sdk")

        assert isinstance(adapter, ClaudeAgentAdapter)
        assert adapter.provider == LLMProvider.CLAUDE_CODE_SDK

    @patch('app.services.llm.factory.settings')
    def test_factory_raises_without_api_key(self, mock_settings):
        """Factory raises ValueError when ANTHROPIC_API_KEY is not configured."""
        mock_settings.anthropic_api_key = None

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not configured"):
            LLMFactory.create("claude-code-sdk")

    @patch('app.services.llm.factory.settings')
    def test_factory_passes_custom_model(self, mock_settings):
        """Factory passes custom model parameter to adapter."""
        mock_settings.anthropic_api_key = "test-key"

        adapter = LLMFactory.create("claude-code-sdk", model="claude-opus-4-20250514")

        assert adapter.model == "claude-opus-4-20250514"
