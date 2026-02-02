"""Unit tests for DeepSeekAdapter.

Tests verify adapter behavior without making real API calls
by mocking the openai.AsyncOpenAI client where it's used in the adapter module.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.llm.deepseek_adapter import (
    DeepSeekAdapter, DEFAULT_MODEL, DEEPSEEK_BASE_URL
)
from app.services.llm.base import LLMProvider, StreamChunk


# Patch path: patch where it's used, not where it's defined
OPENAI_CLIENT_PATH = 'app.services.llm.deepseek_adapter.AsyncOpenAI'


class TestDeepSeekAdapterInit:
    """Tests for DeepSeekAdapter initialization."""

    def test_initializes_with_api_key(self):
        """Client is created with provided API key and DeepSeek base URL."""
        with patch(OPENAI_CLIENT_PATH) as MockClient:
            adapter = DeepSeekAdapter(api_key="test-api-key")

            MockClient.assert_called_once_with(
                api_key="test-api-key",
                base_url=DEEPSEEK_BASE_URL
            )
            assert adapter._api_key == "test-api-key"

    def test_uses_default_model(self):
        """DEFAULT_MODEL is used when no model specified."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            assert adapter.model == DEFAULT_MODEL
            assert adapter.model == "deepseek-reasoner"

    def test_uses_custom_model(self):
        """Custom model parameter is respected."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(
                api_key="test-key",
                model="deepseek-chat"
            )

            assert adapter.model == "deepseek-chat"

    def test_provider_returns_deepseek(self):
        """Provider property returns LLMProvider.DEEPSEEK."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            assert adapter.provider == LLMProvider.DEEPSEEK

    def test_base_url_is_deepseek(self):
        """Base URL points to DeepSeek API."""
        with patch(OPENAI_CLIENT_PATH) as MockClient:
            DeepSeekAdapter(api_key="test-key")

            call_kwargs = MockClient.call_args[1]
            assert call_kwargs["base_url"] == "https://api.deepseek.com"


class TestDeepSeekAdapterStreamChat:
    """Tests for DeepSeekAdapter.stream_chat method."""

    @pytest.mark.asyncio
    async def test_yields_text_chunks(self, mock_deepseek_stream):
        """Text content is yielded as text chunks."""
        mock_stream = mock_deepseek_stream(["Hello", " world"])

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream
            )

            adapter = DeepSeekAdapter(api_key="test-key")

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
    async def test_yields_complete_with_usage(self, mock_deepseek_stream):
        """Complete chunk includes correct usage statistics."""
        mock_stream = mock_deepseek_stream(
            text_chunks=["Response"],
            usage={"input_tokens": 100, "output_tokens": 50}
        )

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream
            )

            adapter = DeepSeekAdapter(api_key="test-key")

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
    async def test_prepends_system_prompt(self, mock_deepseek_stream):
        """System prompt is prepended as system message."""
        mock_stream = mock_deepseek_stream(["Response"])

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream
            )

            adapter = DeepSeekAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are a business analyst."
            ):
                chunks.append(chunk)

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            messages = call_kwargs["messages"]

            # First message should be system
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are a business analyst."


class TestDeepSeekAdapterReasoningHidden:
    """Tests for reasoning_content filtering (per CONTEXT.md)."""

    @pytest.mark.asyncio
    async def test_reasoning_content_not_yielded(self, mock_deepseek_stream):
        """Reasoning content is NOT yielded to user (per CONTEXT.md)."""
        mock_stream = mock_deepseek_stream(
            text_chunks=["Final answer"],
            reasoning_chunks=["Let me think...", "Step 1..."]
        )

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream
            )

            adapter = DeepSeekAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Think about this"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            text_chunks = [c for c in chunks if c.chunk_type == "text"]
            # Only the final answer, not reasoning
            assert len(text_chunks) == 1
            assert text_chunks[0].content == "Final answer"

            # Verify no thinking chunks leaked
            all_content = [c.content for c in chunks if c.content]
            assert "Let me think" not in str(all_content)
            assert "Step 1" not in str(all_content)


class TestDeepSeekAdapterToolCalls:
    """Tests for tool call handling."""

    @pytest.mark.asyncio
    async def test_yields_tool_use_chunks(self, mock_deepseek_stream):
        """Tool calls are yielded as tool_use chunks."""
        mock_stream = mock_deepseek_stream(
            text_chunks=[],
            tool_calls=[{
                "id": "call_abc123",
                "name": "save_artifact",
                "arguments": '{"title": "Test", "content": "Content"}'
            }]
        )

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream
            )

            adapter = DeepSeekAdapter(api_key="test-key")

            tools = [{"name": "save_artifact", "description": "Save"}]

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Create artifact"}],
                system_prompt="You are helpful.",
                tools=tools
            ):
                chunks.append(chunk)

            tool_chunks = [c for c in chunks if c.chunk_type == "tool_use"]
            assert len(tool_chunks) == 1
            assert tool_chunks[0].tool_call["id"] == "call_abc123"
            assert tool_chunks[0].tool_call["name"] == "save_artifact"
            assert tool_chunks[0].tool_call["input"] == {
                "title": "Test",
                "content": "Content"
            }

    @pytest.mark.asyncio
    async def test_converts_tools_to_openai_format(self, mock_deepseek_stream):
        """Tools are converted from Anthropic to OpenAI format."""
        mock_stream = mock_deepseek_stream(["Response"])

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream
            )

            adapter = DeepSeekAdapter(api_key="test-key")

            # Anthropic format tools
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

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            openai_tools = call_kwargs["tools"]

            # Should be converted to OpenAI function calling format
            assert openai_tools[0]["type"] == "function"
            assert openai_tools[0]["function"]["name"] == "save_artifact"
            assert openai_tools[0]["function"]["parameters"] == {
                "type": "object",
                "properties": {"title": {"type": "string"}}
            }


class TestDeepSeekAdapterRetry:
    """Tests for retry logic on transient errors."""

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit(self, mock_deepseek_stream):
        """Retries on RateLimitError."""
        from openai import RateLimitError

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                mock_client = MockClient.return_value

                call_count = 0
                async def mock_create(**kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise RateLimitError(
                            message="Rate limited",
                            response=MagicMock(status_code=429),
                            body={"error": {"message": "Rate limited"}}
                        )
                    return mock_deepseek_stream(["Success"])

                mock_client.chat.completions.create = AsyncMock(
                    side_effect=mock_create
                )

                adapter = DeepSeekAdapter(api_key="test-key")

                chunks = []
                async for chunk in adapter.stream_chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    system_prompt="You are helpful."
                ):
                    chunks.append(chunk)

                assert call_count == 2
                mock_sleep.assert_called_once_with(1.0)

                text_chunks = [c for c in chunks if c.chunk_type == "text"]
                assert len(text_chunks) == 1
                assert text_chunks[0].content == "Success"

    @pytest.mark.asyncio
    async def test_retries_on_500_error(self, mock_deepseek_stream):
        """Retries on APIStatusError with 500 status code."""
        from openai import APIStatusError

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                mock_client = MockClient.return_value

                call_count = 0
                async def mock_create(**kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise APIStatusError(
                            message="Server error",
                            response=MagicMock(status_code=500),
                            body={"error": {"message": "Internal error"}}
                        )
                    return mock_deepseek_stream(["Success"])

                mock_client.chat.completions.create = AsyncMock(
                    side_effect=mock_create
                )

                adapter = DeepSeekAdapter(api_key="test-key")

                chunks = []
                async for chunk in adapter.stream_chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    system_prompt="You are helpful."
                ):
                    chunks.append(chunk)

                assert call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_yields_error(self):
        """After max retries, yields error chunk."""
        from openai import RateLimitError

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                mock_client = MockClient.return_value

                # Always fails
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=RateLimitError(
                        message="Rate limited",
                        response=MagicMock(status_code=429),
                        body={"error": {"message": "Rate limited"}}
                    )
                )

                adapter = DeepSeekAdapter(api_key="test-key")

                chunks = []
                async for chunk in adapter.stream_chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    system_prompt="You are helpful."
                ):
                    chunks.append(chunk)

                error_chunks = [c for c in chunks if c.chunk_type == "error"]
                assert len(error_chunks) == 1
                assert "rate limit" in error_chunks[0].error.lower()


class TestDeepSeekAdapterErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """APIError yields error chunk."""
        from openai import APIError

        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value

            mock_client.chat.completions.create = AsyncMock(
                side_effect=APIError(
                    message="Invalid API key",
                    request=MagicMock(),
                    body={"error": {"message": "Invalid key"}}
                )
            )

            adapter = DeepSeekAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            error_chunks = [c for c in chunks if c.chunk_type == "error"]
            assert len(error_chunks) == 1
            assert "DeepSeek API error" in error_chunks[0].error

    @pytest.mark.asyncio
    async def test_handles_unexpected_error(self):
        """Unexpected errors yield error chunk."""
        with patch(OPENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value

            mock_client.chat.completions.create = AsyncMock(
                side_effect=RuntimeError("Connection failed")
            )

            adapter = DeepSeekAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            error_chunks = [c for c in chunks if c.chunk_type == "error"]
            assert len(error_chunks) == 1
            assert "unexpected error" in error_chunks[0].error.lower()
            assert "Connection failed" in error_chunks[0].error


class TestDeepSeekAdapterMessageConversion:
    """Tests for message format conversion."""

    def test_converts_string_content(self):
        """String content is passed directly."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            messages = [{"role": "user", "content": "Hello"}]
            result = adapter._convert_messages(messages, "System")

            # First is system, second is user
            assert result[0] == {"role": "system", "content": "System"}
            assert result[1] == {"role": "user", "content": "Hello"}

    def test_converts_multipart_content(self):
        """List content (Anthropic format) is converted."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Part 1"},
                    {"type": "text", "text": "Part 2"}
                ]
            }]
            result = adapter._convert_messages(messages, "System")

            # Text parts should be joined
            assert result[1]["content"] == "Part 1\nPart 2"

    def test_handles_tool_result_content(self):
        """Tool result blocks are converted to text."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            messages = [{
                "role": "user",
                "content": [
                    {"type": "tool_result", "content": "Tool output here"}
                ]
            }]
            result = adapter._convert_messages(messages, "System")

            assert "Tool result: Tool output here" in result[1]["content"]


class TestDeepSeekAdapterToolParsing:
    """Tests for tool argument parsing."""

    def test_parses_valid_json_arguments(self):
        """Valid JSON arguments are parsed."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            result = adapter._parse_tool_args('{"key": "value"}')
            assert result == {"key": "value"}

    def test_handles_empty_arguments(self):
        """Empty/None arguments return empty dict."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            assert adapter._parse_tool_args(None) == {}
            assert adapter._parse_tool_args("") == {}

    def test_handles_invalid_json(self):
        """Invalid JSON returns raw value."""
        with patch(OPENAI_CLIENT_PATH):
            adapter = DeepSeekAdapter(api_key="test-key")

            result = adapter._parse_tool_args("not json")
            assert result == {"raw": "not json"}
