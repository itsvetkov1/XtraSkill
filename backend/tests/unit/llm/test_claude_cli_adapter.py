"""Unit tests for ClaudeCLIAdapter.

Tests verify adapter stub behavior without making real API calls.
The stub raises NotImplementedError until Phase 59 implements stream_chat.
"""

import pytest
from unittest.mock import patch

from app.services.llm.claude_cli_adapter import ClaudeCLIAdapter, DEFAULT_MODEL
from app.services.llm.base import LLMProvider
from app.services.llm import LLMFactory


class TestClaudeCLIAdapterInit:
    """Tests for ClaudeCLIAdapter initialization."""

    def test_initializes_with_api_key(self):
        """API key is stored in adapter instance."""
        adapter = ClaudeCLIAdapter(api_key="test-api-key")

        assert adapter._api_key == "test-api-key"

    def test_uses_default_model(self):
        """DEFAULT_MODEL is used when no model specified."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.model == DEFAULT_MODEL
        assert adapter.model == "claude-sonnet-4-5-20250929"

    def test_uses_custom_model(self):
        """Custom model parameter is respected."""
        adapter = ClaudeCLIAdapter(
            api_key="test-key",
            model="claude-opus-4-20250514"
        )

        assert adapter.model == "claude-opus-4-20250514"

    def test_provider_returns_claude_code_cli(self):
        """Provider property returns LLMProvider.CLAUDE_CODE_CLI."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.provider == LLMProvider.CLAUDE_CODE_CLI
        assert adapter.provider.value == "claude-code-cli"


class TestClaudeCLIAdapterStreamChat:
    """Tests for ClaudeCLIAdapter.stream_chat method."""

    @pytest.mark.asyncio
    async def test_stream_chat_raises_not_implemented(self):
        """stream_chat raises NotImplementedError with Phase 59 message."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        with pytest.raises(NotImplementedError, match="Phase 59"):
            async for _ in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                pass


class TestClaudeCLIAdapterFactory:
    """Tests for LLMFactory integration with ClaudeCLIAdapter."""

    @patch('app.services.llm.factory.settings')
    def test_factory_creates_adapter(self, mock_settings):
        """LLMFactory.create('claude-code-cli') returns ClaudeCLIAdapter."""
        mock_settings.anthropic_api_key = "test-key"

        adapter = LLMFactory.create("claude-code-cli")

        assert isinstance(adapter, ClaudeCLIAdapter)
        assert adapter.provider == LLMProvider.CLAUDE_CODE_CLI

    @patch('app.services.llm.factory.settings')
    def test_factory_raises_without_api_key(self, mock_settings):
        """Factory raises ValueError when ANTHROPIC_API_KEY is not configured."""
        mock_settings.anthropic_api_key = None

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not configured"):
            LLMFactory.create("claude-code-cli")

    @patch('app.services.llm.factory.settings')
    def test_factory_passes_custom_model(self, mock_settings):
        """Factory passes custom model parameter to adapter."""
        mock_settings.anthropic_api_key = "test-key"

        adapter = LLMFactory.create("claude-code-cli", model="claude-opus-4-20250514")

        assert adapter.model == "claude-opus-4-20250514"
