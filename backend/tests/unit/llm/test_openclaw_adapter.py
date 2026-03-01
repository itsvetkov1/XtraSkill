"""Unit tests for OpenClaw adapter in LLM tests directory."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, '/home/i_tsvetkov/XtraSkill/backend')

from app.services.llm.openclaw_adapter import OpenClawAdapter, create_openclaw_adapter
from app.services.llm.base import LLMProvider, StreamChunk


class TestLLMProviderOpenClaw:
    """Test LLMProvider enum includes OpenClaw."""

    def test_openclaw_in_providers(self):
        """Test OpenClaw is in LLMProvider enum."""
        providers = [p.value for p in LLMProvider]
        assert "openclaw" in providers

    def test_openclaw_enum_value(self):
        """Test OpenClaw enum value is correct."""
        assert LLMProvider.OPENCLAW.value == "openclaw"


class TestOpenClawAdapterLLM:
    """Test OpenClawAdapter in LLM context."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for tests."""
        return OpenClawAdapter(
            api_key="test-key",
            model="claude-sonnet",
            gateway_url="http://localhost:8080",
            agent_id="dev",
        )

    def test_adapter_has_provider_property(self, adapter):
        """Test adapter has provider property."""
        assert hasattr(adapter, 'provider')

    def test_adapter_provider_is_openclaw(self, adapter):
        """Test adapter provider is OpenClaw."""
        assert adapter.provider == LLMProvider.OPENCLAW

    def test_adapter_initialization_params(self, adapter):
        """Test adapter stores initialization params."""
        assert adapter._api_key == "test-key"
        assert adapter._model == "claude-sonnet"
        assert adapter._gateway_url == "http://localhost:8080"
        assert adapter._agent_id == "dev"


class TestCreateOpenClawAdapter:
    """Test factory function for creating adapter."""

    @patch('app.services.llm.openclaw_adapter.settings')
    def test_create_adapter_with_defaults(self, mock_settings):
        """Test create_openclaw_adapter with default settings."""
        mock_settings.openclaw_api_key = "key-from-settings"
        mock_settings.openclaw_gateway_url = "http://settings:8080"
        mock_settings.openclaw_agent_id = "forger"

        adapter = create_openclaw_adapter()

        assert adapter._api_key == "key-from-settings"
        assert adapter._gateway_url == "http://settings:8080"
        assert adapter._agent_id == "forger"

    @patch('app.services.llm.openclaw_adapter.settings')
    def test_create_adapter_raises_without_key(self, mock_settings):
        """Test create_openclaw_adapter raises without API key."""
        mock_settings.openclaw_api_key = ""

        with pytest.raises(ValueError) as exc:
            create_openclaw_adapter()

        assert "OPENCLAW_API_KEY" in str(exc.value)


class TestStreamChunkOpenClaw:
    """Test StreamChunk works with OpenClaw."""

    def test_stream_chunk_text(self):
        """Test text chunk creation."""
        chunk = StreamChunk(chunk_type="text", content="Hello")
        assert chunk.chunk_type == "text"
        assert chunk.content == "Hello"

    def test_stream_chunk_thinking(self):
        """Test thinking chunk creation."""
        chunk = StreamChunk(chunk_type="thinking", thinking_content="Reasoning...")
        assert chunk.chunk_type == "thinking"
        assert chunk.thinking_content == "Reasoning..."

    def test_stream_chunk_tool_use(self):
        """Test tool_use chunk creation."""
        chunk = StreamChunk(
            chunk_type="tool_use",
            tool_call={"id": "call_123", "name": "search", "input": {"query": "test"}}
        )
        assert chunk.chunk_type == "tool_use"
        assert chunk.tool_call["name"] == "search"

    def test_stream_chunk_complete(self):
        """Test complete chunk with usage."""
        chunk = StreamChunk(
            chunk_type="complete",
            usage={"input_tokens": 100, "output_tokens": 50}
        )
        assert chunk.chunk_type == "complete"
        assert chunk.usage["input_tokens"] == 100

    def test_stream_chunk_error(self):
        """Test error chunk creation."""
        chunk = StreamChunk(chunk_type="error", error="Something went wrong")
        assert chunk.chunk_type == "error"
        assert chunk.error == "Something went wrong"
