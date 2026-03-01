"""Unit tests for OpenClaw adapter."""
import pytest

import sys
sys.path.insert(0, '/home/i_tsvetkov/XtraSkill/backend')

from app.services.llm.openclaw_adapter import OpenClawAdapter
from app.services.llm.base import LLMProvider, StreamChunk


class TestOpenClawAdapter:
    """Test cases for OpenClawAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return OpenClawAdapter(
            api_key="test-key",
            model="default",
            gateway_url="http://localhost:8080",
            agent_id="dev",
        )

    def test_provider(self, adapter):
        """Test provider property returns correct enum."""
        assert adapter.provider == LLMProvider.OPENCLAW

    def test_adapter_stores_config(self, adapter):
        """Test adapter stores configuration."""
        assert adapter._api_key == "test-key"
        assert adapter._model == "default"
        assert adapter._gateway_url == "http://localhost:8080"
        assert adapter._agent_id == "dev"

    def test_close_sets_client_to_none(self, adapter):
        """Test close method can be called."""
        # Client is None initially
        assert adapter._client is None
        
        # Close should work even without client
        import asyncio
        asyncio.run(adapter.close())
        assert adapter._client is None


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
