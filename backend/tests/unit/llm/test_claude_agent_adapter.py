"""Unit tests for ClaudeAgentAdapter.

Tests verify adapter SDK event translation without making real API calls.
Mocks the claude_agent_sdk.query function to simulate SDK event types.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import AsyncGenerator

from app.services.llm.claude_agent_adapter import ClaudeAgentAdapter, DEFAULT_MODEL
from app.services.llm.base import LLMProvider, StreamChunk
from app.services.llm import LLMFactory


# ============================================================================
# Mock Helper Functions
# ============================================================================

def make_stream_event(text: str):
    """Create mock StreamEvent with delta.text."""
    from claude_agent_sdk.types import StreamEvent
    event = MagicMock(spec=StreamEvent)
    event.delta = MagicMock()
    event.delta.text = text
    return event


def make_text_block(text: str):
    """Create mock TextBlock."""
    from claude_agent_sdk.types import TextBlock
    block = MagicMock(spec=TextBlock)
    block.text = text
    return block


def make_tool_use_block(id: str, name: str, input: dict):
    """Create mock ToolUseBlock."""
    from claude_agent_sdk.types import ToolUseBlock
    block = MagicMock(spec=ToolUseBlock)
    block.id = id
    block.name = name
    block.input = input
    return block


def make_tool_result_block(content: str):
    """Create mock ToolResultBlock."""
    from claude_agent_sdk.types import ToolResultBlock
    block = MagicMock(spec=ToolResultBlock)
    block.content = content
    return block


def make_assistant_message(blocks: list):
    """Create mock AssistantMessage with content blocks."""
    from claude_agent_sdk.types import AssistantMessage
    message = MagicMock(spec=AssistantMessage)
    message.content = blocks
    return message


def make_result_message(input_tokens: int, output_tokens: int):
    """Create mock ResultMessage with usage."""
    from claude_agent_sdk.types import ResultMessage
    message = MagicMock(spec=ResultMessage)
    message.usage = MagicMock()
    message.usage.input_tokens = input_tokens
    message.usage.output_tokens = output_tokens
    return message


async def async_generator(*items):
    """Create async generator from items."""
    for item in items:
        yield item


# ============================================================================
# Test Classes
# ============================================================================

class TestClaudeAgentAdapterInit:
    """Tests for ClaudeAgentAdapter initialization."""

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_initializes_with_api_key(self, mock_create_mcp, mock_get_url):
        """API key is stored in adapter instance."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = ClaudeAgentAdapter(api_key="test-api-key")

        assert adapter._api_key == "test-api-key"

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_uses_default_model(self, mock_create_mcp, mock_get_url):
        """DEFAULT_MODEL is used when no model specified."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = ClaudeAgentAdapter(api_key="test-key")

        assert adapter.model == DEFAULT_MODEL
        assert adapter.model == "claude-sonnet-4-5-20250514"

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_uses_custom_model(self, mock_create_mcp, mock_get_url):
        """Custom model parameter is respected."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = ClaudeAgentAdapter(
            api_key="test-key",
            model="claude-opus-4-20250514"
        )

        assert adapter.model == "claude-opus-4-20250514"

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_provider_returns_claude_code_sdk(self, mock_create_mcp, mock_get_url):
        """Provider property returns LLMProvider.CLAUDE_CODE_SDK."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = ClaudeAgentAdapter(api_key="test-key")

        assert adapter.provider == LLMProvider.CLAUDE_CODE_SDK
        assert adapter.provider.value == "claude-code-sdk"

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_mcp_server_url_set(self, mock_create_mcp, mock_get_url):
        """MCP HTTP server URL is obtained via get_mcp_http_server_url()."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = "http://localhost:8765/mcp"

        adapter = ClaudeAgentAdapter(api_key="test-key")

        assert adapter.mcp_server_url == "http://localhost:8765/mcp"

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_is_agent_provider(self, mock_create_mcp, mock_get_url):
        """is_agent_provider attribute is True."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = ClaudeAgentAdapter(api_key="test-key")

        assert adapter.is_agent_provider is True

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_set_context(self, mock_create_mcp, mock_get_url):
        """set_context stores db/project_id/thread_id."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = ClaudeAgentAdapter(api_key="test-key")
        mock_db = MagicMock()

        adapter.set_context(mock_db, "proj-123", "thread-456")

        assert adapter.db is mock_db
        assert adapter.project_id == "proj-123"
        assert adapter.thread_id == "thread-456"


class TestClaudeAgentAdapterStreamChat:
    """Tests for ClaudeAgentAdapter.stream_chat method."""

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter._documents_used_context')
    @patch('app.services.llm.claude_agent_adapter._thread_id_context')
    @patch('app.services.llm.claude_agent_adapter._project_id_context')
    @patch('app.services.llm.claude_agent_adapter._db_context')
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_text_streaming_via_stream_event(self, mock_query, mock_create_mcp, mock_get_url,
                                                    mock_db_ctx, mock_proj_ctx, mock_thread_ctx, mock_docs_ctx):
        """StreamEvent with delta.text yields text StreamChunk."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock query to yield StreamEvent with text
        mock_query.return_value = async_generator(
            make_stream_event("hello"),
            make_stream_event(" world"),
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify text chunks
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        assert len(text_chunks) == 2
        assert text_chunks[0].content == "hello"
        assert text_chunks[1].content == " world"

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_tool_use_visibility(self, mock_query, mock_create_mcp, mock_get_url):
        """ToolUseBlock yields tool_use StreamChunk for activity indicator."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        # Mock query to yield AssistantMessage with ToolUseBlock
        tool_block = make_tool_use_block(
            id="tool-123",
            name="mcp__ba__search_documents",
            input={"query": "test"}
        )
        mock_query.return_value = async_generator(
            make_assistant_message([tool_block]),
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify tool_use chunk
        tool_chunks = [c for c in chunks if c.chunk_type == "tool_use"]
        assert len(tool_chunks) == 1
        assert tool_chunks[0].tool_call["id"] == "tool-123"
        assert tool_chunks[0].tool_call["name"] == "mcp__ba__search_documents"
        assert tool_chunks[0].tool_call["input"] == {"query": "test"}

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_complete_with_usage(self, mock_query, mock_create_mcp, mock_get_url):
        """ResultMessage yields complete StreamChunk with usage stats."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        # Mock query to yield ResultMessage
        mock_query.return_value = async_generator(
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify complete chunk
        complete_chunks = [c for c in chunks if c.chunk_type == "complete"]
        assert len(complete_chunks) == 1
        assert complete_chunks[0].usage["input_tokens"] == 100
        assert complete_chunks[0].usage["output_tokens"] == 50

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter._documents_used_context')
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_complete_with_documents_used(self, mock_query, mock_create_mcp, mock_get_url, mock_docs_context):
        """Complete chunk includes documents_used from ContextVar."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        # Mock documents_used ContextVar
        mock_docs_context.get.return_value = [
            {"id": "doc-1", "filename": "test.pdf"}
        ]

        # Mock query to yield ResultMessage
        mock_query.return_value = async_generator(
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify documents_used in complete chunk metadata
        complete_chunks = [c for c in chunks if c.chunk_type == "complete"]
        assert len(complete_chunks) == 1
        assert complete_chunks[0].metadata["documents_used"] == [
            {"id": "doc-1", "filename": "test.pdf"}
        ]

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_artifact_created_detection(self, mock_query, mock_create_mcp, mock_get_url):
        """ToolResultBlock with ARTIFACT_CREATED marker yields metadata event."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        # Mock query to yield ToolResultBlock with ARTIFACT_CREATED marker
        tool_result = make_tool_result_block(
            'ARTIFACT_CREATED:{"id":"art-123","title":"Test Artifact","artifact_type":"user_stories"}|Success'
        )
        mock_query.return_value = async_generator(
            make_assistant_message([tool_result]),
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify artifact_created in metadata
        tool_chunks = [c for c in chunks if c.chunk_type == "tool_use" and c.metadata]
        assert len(tool_chunks) == 1
        assert "artifact_created" in tool_chunks[0].metadata
        assert tool_chunks[0].metadata["artifact_created"]["id"] == "art-123"
        assert tool_chunks[0].metadata["artifact_created"]["title"] == "Test Artifact"

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_error_handling(self, mock_query, mock_create_mcp, mock_get_url):
        """Exception from query yields error StreamChunk with diagnostic info."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        # Mock query to raise exception
        async def raise_error():
            yield make_stream_event("hello")
            raise RuntimeError("SDK connection failed")

        mock_query.return_value = raise_error()

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify error chunk
        error_chunks = [c for c in chunks if c.chunk_type == "error"]
        assert len(error_chunks) == 1
        assert "SDK connection failed" in error_chunks[0].error
        assert "turn" in error_chunks[0].error  # Contains turn count diagnostic

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter._documents_used_context')
    @patch('app.services.llm.claude_agent_adapter._thread_id_context')
    @patch('app.services.llm.claude_agent_adapter._project_id_context')
    @patch('app.services.llm.claude_agent_adapter._db_context')
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_multi_turn_text_continuity(self, mock_query, mock_create_mcp, mock_get_url,
                                              mock_db_ctx, mock_proj_ctx, mock_thread_ctx, mock_docs_ctx):
        """Multiple StreamEvents across turns yield continuous text stream."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock query to yield multiple text events
        mock_query.return_value = async_generator(
            make_stream_event("Turn 1 "),
            make_stream_event("text. "),
            make_stream_event("Turn 2 "),
            make_stream_event("text."),
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify all text chunks yielded in order
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        assert len(text_chunks) == 4
        full_text = "".join(c.content for c in text_chunks)
        assert full_text == "Turn 1 text. Turn 2 text."

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter._documents_used_context')
    @patch('app.services.llm.claude_agent_adapter._thread_id_context')
    @patch('app.services.llm.claude_agent_adapter._project_id_context')
    @patch('app.services.llm.claude_agent_adapter._db_context')
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_text_block_not_duplicated(self, mock_query, mock_create_mcp, mock_get_url,
                                             mock_db_ctx, mock_proj_ctx, mock_thread_ctx, mock_docs_ctx):
        """TextBlock after StreamEvent is not duplicated (already streamed)."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock query to yield StreamEvent followed by AssistantMessage with same text
        text_block = make_text_block("hello world")
        mock_query.return_value = async_generator(
            make_stream_event("hello world"),
            make_assistant_message([text_block]),
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify text only yielded once (from StreamEvent, not TextBlock)
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        assert len(text_chunks) == 1
        assert text_chunks[0].content == "hello world"

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.claude_agent_adapter.query')
    async def test_documents_used_from_tool_result_marker(self, mock_query, mock_create_mcp, mock_get_url):
        """DOCUMENTS_USED marker in ToolResultBlock is parsed for source attribution."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        # Mock query to yield ToolResultBlock with DOCUMENTS_USED marker
        tool_result = make_tool_result_block(
            'DOCUMENTS_USED:[{"id":"doc-1","filename":"test.pdf"}]|Here are the results'
        )
        mock_query.return_value = async_generator(
            make_assistant_message([tool_result]),
            make_result_message(100, 50)
        )

        adapter = ClaudeAgentAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify documents_used in complete chunk
        complete_chunks = [c for c in chunks if c.chunk_type == "complete"]
        assert len(complete_chunks) == 1
        assert len(complete_chunks[0].metadata["documents_used"]) == 1
        assert complete_chunks[0].metadata["documents_used"][0]["id"] == "doc-1"

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    def test_convert_messages_to_prompt(self, mock_create_mcp, mock_get_url):
        """_convert_messages_to_prompt formats messages correctly."""
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = ClaudeAgentAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "[USER]: Hello" in prompt
        assert "[ASSISTANT]: Hi there!" in prompt


class TestClaudeAgentAdapterFactory:
    """Tests for LLMFactory integration with ClaudeAgentAdapter."""

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.factory.settings')
    def test_factory_creates_adapter(self, mock_settings, mock_create_mcp, mock_get_url):
        """LLMFactory.create('claude-code-sdk') returns ClaudeAgentAdapter."""
        mock_settings.anthropic_api_key = "test-key"
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = LLMFactory.create("claude-code-sdk")

        assert isinstance(adapter, ClaudeAgentAdapter)
        assert adapter.provider == LLMProvider.CLAUDE_CODE_SDK

    @patch('app.services.llm.factory.settings')
    def test_factory_raises_without_api_key(self, mock_settings):
        """Factory raises ValueError when ANTHROPIC_API_KEY is not configured."""
        mock_settings.anthropic_api_key = None

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not configured"):
            LLMFactory.create("claude-code-sdk")

    @patch('app.services.llm.claude_agent_adapter.get_mcp_http_server_url')
    @patch('app.services.llm.claude_agent_adapter.create_ba_mcp_server')
    @patch('app.services.llm.factory.settings')
    def test_factory_passes_custom_model(self, mock_settings, mock_create_mcp, mock_get_url):
        """Factory passes custom model parameter to adapter."""
        mock_settings.anthropic_api_key = "test-key"
        mock_create_mcp.return_value = MagicMock()
        mock_get_url.return_value = None

        adapter = LLMFactory.create("claude-code-sdk", model="claude-opus-4-20250514")

        assert adapter.model == "claude-opus-4-20250514"
