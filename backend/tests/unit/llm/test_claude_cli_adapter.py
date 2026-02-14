"""Unit tests for ClaudeCLIAdapter.

Tests verify adapter initialization and integration without making real subprocess calls.
Phase 59 implements full subprocess-based stream_chat functionality.
"""

import pytest
from unittest.mock import patch

from app.services.llm.claude_cli_adapter import ClaudeCLIAdapter, DEFAULT_MODEL
from app.services.llm.base import LLMProvider
from app.services.llm import LLMFactory


class TestClaudeCLIAdapterInit:
    """Tests for ClaudeCLIAdapter initialization."""

    @patch('shutil.which', return_value='/usr/bin/claude')
    def test_initializes_with_api_key(self, mock_which):
        """API key is stored in adapter instance."""
        adapter = ClaudeCLIAdapter(api_key="test-api-key")

        assert adapter._api_key == "test-api-key"

    @patch('shutil.which', return_value='/usr/bin/claude')
    def test_uses_default_model(self, mock_which):
        """DEFAULT_MODEL is used when no model specified."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.model == DEFAULT_MODEL
        assert adapter.model == "claude-sonnet-4-5-20250929"

    @patch('shutil.which', return_value='/usr/bin/claude')
    def test_uses_custom_model(self, mock_which):
        """Custom model parameter is respected."""
        adapter = ClaudeCLIAdapter(
            api_key="test-key",
            model="claude-opus-4-20250514"
        )

        assert adapter.model == "claude-opus-4-20250514"

    @patch('shutil.which', return_value='/usr/bin/claude')
    def test_provider_returns_claude_code_cli(self, mock_which):
        """Provider property returns LLMProvider.CLAUDE_CODE_CLI."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.provider == LLMProvider.CLAUDE_CODE_CLI
        assert adapter.provider.value == "claude-code-cli"

    @patch('shutil.which', return_value=None)
    def test_raises_runtime_error_when_cli_not_found(self, mock_which):
        """Raises RuntimeError with install instructions when CLI not in PATH."""
        with pytest.raises(RuntimeError, match="Claude Code CLI not found"):
            ClaudeCLIAdapter(api_key="test-key")

    @patch('shutil.which', return_value='/usr/bin/claude')
    def test_is_agent_provider_true(self, mock_which):
        """Adapter has is_agent_provider=True for AIService routing."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.is_agent_provider is True

    @patch('shutil.which', return_value='/usr/bin/claude')
    def test_has_set_context_method(self, mock_which):
        """Adapter has set_context method for request-scoped context."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert hasattr(adapter, 'set_context')
        assert callable(adapter.set_context)


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
