"""Unit tests for AnthropicAdapter.

Tests verify adapter behavior without making real API calls
by mocking the anthropic.AsyncAnthropic client.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.llm.anthropic_adapter import AnthropicAdapter, DEFAULT_MODEL
from app.services.llm.base import LLMProvider, StreamChunk


class TestAnthropicAdapterInit:
    """Tests for AnthropicAdapter initialization."""

    def test_initializes_with_api_key(self):
        """Client is created with provided API key."""
        with patch('anthropic.AsyncAnthropic') as MockClient:
            adapter = AnthropicAdapter(api_key="test-api-key")

            MockClient.assert_called_once_with(api_key="test-api-key")
            assert adapter._api_key == "test-api-key"

    def test_uses_default_model(self):
        """DEFAULT_MODEL is used when no model specified."""
        with patch('anthropic.AsyncAnthropic'):
            adapter = AnthropicAdapter(api_key="test-key")

            assert adapter.model == DEFAULT_MODEL
            assert adapter.model == "claude-sonnet-4-5-20250929"

    def test_uses_custom_model(self):
        """Custom model parameter is respected."""
        with patch('anthropic.AsyncAnthropic'):
            adapter = AnthropicAdapter(
                api_key="test-key",
                model="claude-opus-4-20250514"
            )

            assert adapter.model == "claude-opus-4-20250514"

    def test_provider_returns_anthropic(self):
        """Provider property returns LLMProvider.ANTHROPIC."""
        with patch('anthropic.AsyncAnthropic'):
            adapter = AnthropicAdapter(api_key="test-key")

            assert adapter.provider == LLMProvider.ANTHROPIC


class TestAnthropicAdapterStreamChat:
    """Tests for AnthropicAdapter.stream_chat method."""

    @pytest.mark.asyncio
    async def test_yields_text_chunks(self, mock_anthropic_stream):
        """Text content is yielded as text chunks."""
        mock_stream = mock_anthropic_stream(["Hello", " world"])

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            text_chunks = [c for c in chunks if c.chunk_type == "text"]
            assert len(text_chunks) == 2
            assert text_chunks[0].content == "Hello"
            assert text_chunks[1].content == " world"

    @pytest.mark.asyncio
    async def test_yields_tool_use_chunks(
        self, mock_anthropic_stream, mock_tool_use_block
    ):
        """Tool use blocks are yielded as tool_use chunks."""
        tool_block = mock_tool_use_block(
            tool_id="toolu_abc123",
            name="save_artifact",
            input_data={"title": "Test", "content": "Content"}
        )
        mock_stream = mock_anthropic_stream(
            text_chunks=[],
            tool_blocks=[tool_block]
        )

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Create an artifact"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            tool_chunks = [c for c in chunks if c.chunk_type == "tool_use"]
            assert len(tool_chunks) == 1
            assert tool_chunks[0].tool_call["id"] == "toolu_abc123"
            assert tool_chunks[0].tool_call["name"] == "save_artifact"
            assert tool_chunks[0].tool_call["input"] == {
                "title": "Test",
                "content": "Content"
            }

    @pytest.mark.asyncio
    async def test_yields_complete_with_usage(self, mock_anthropic_stream):
        """Complete chunk includes correct usage statistics."""
        mock_stream = mock_anthropic_stream(
            text_chunks=["Hi"],
            usage={"input_tokens": 100, "output_tokens": 50}
        )

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            complete_chunks = [c for c in chunks if c.chunk_type == "complete"]
            assert len(complete_chunks) == 1
            assert complete_chunks[0].usage == {
                "input_tokens": 100,
                "output_tokens": 50
            }

    @pytest.mark.asyncio
    async def test_passes_messages_to_api(self, mock_anthropic_stream):
        """Messages are passed to the stream() call."""
        mock_stream = mock_anthropic_stream(["Response"])

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "How are you?"}
            ]

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=messages,
                system_prompt="Be helpful."
            ):
                chunks.append(chunk)

            # Verify stream() was called with correct args
            mock_client.messages.stream.assert_called_once()
            call_kwargs = mock_client.messages.stream.call_args[1]
            assert call_kwargs["messages"] == messages

    @pytest.mark.asyncio
    async def test_passes_system_prompt(self, mock_anthropic_stream):
        """System prompt is passed to the API."""
        mock_stream = mock_anthropic_stream(["Response"])

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are a business analyst assistant."
            ):
                chunks.append(chunk)

            call_kwargs = mock_client.messages.stream.call_args[1]
            assert call_kwargs["system"] == "You are a business analyst assistant."

    @pytest.mark.asyncio
    async def test_passes_tools_when_provided(self, mock_anthropic_stream):
        """Tools are passed to the API when provided."""
        mock_stream = mock_anthropic_stream(["Response"])

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            tools = [{
                "name": "save_artifact",
                "description": "Save an artifact",
                "input_schema": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}}
                }
            }]

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful.",
                tools=tools
            ):
                chunks.append(chunk)

            call_kwargs = mock_client.messages.stream.call_args[1]
            assert call_kwargs["tools"] == tools

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Anthropic API errors yield error chunks."""
        import anthropic

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value

            # Create mock API error
            mock_error = anthropic.APIError(
                message="Rate limit exceeded",
                request=MagicMock(),
                body={"error": {"message": "Rate limit"}}
            )

            # Make stream context manager raise the error
            mock_stream = AsyncMock()
            mock_stream.__aenter__.side_effect = mock_error
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            error_chunks = [c for c in chunks if c.chunk_type == "error"]
            assert len(error_chunks) == 1
            assert "Anthropic API error" in error_chunks[0].error

    @pytest.mark.asyncio
    async def test_handles_unexpected_error(self):
        """Unexpected errors yield error chunks."""
        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value

            # Make stream context manager raise unexpected error
            mock_stream = AsyncMock()
            mock_stream.__aenter__.side_effect = RuntimeError("Connection failed")
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            error_chunks = [c for c in chunks if c.chunk_type == "error"]
            assert len(error_chunks) == 1
            assert "Unexpected error" in error_chunks[0].error
            assert "Connection failed" in error_chunks[0].error

    @pytest.mark.asyncio
    async def test_passes_max_tokens(self, mock_anthropic_stream):
        """Max tokens parameter is passed to the API."""
        mock_stream = mock_anthropic_stream(["Response"])

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful.",
                max_tokens=8192
            ):
                chunks.append(chunk)

            call_kwargs = mock_client.messages.stream.call_args[1]
            assert call_kwargs["max_tokens"] == 8192

    @pytest.mark.asyncio
    async def test_uses_configured_model(self, mock_anthropic_stream):
        """Configured model is passed to the API."""
        mock_stream = mock_anthropic_stream(["Response"])

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(
                api_key="test-key",
                model="claude-opus-4-20250514"
            )

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            call_kwargs = mock_client.messages.stream.call_args[1]
            assert call_kwargs["model"] == "claude-opus-4-20250514"
