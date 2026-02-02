"""Unit tests for GeminiAdapter.

Tests verify adapter behavior without making real API calls
by mocking the google.genai.Client where it's used in the adapter module.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.llm.gemini_adapter import GeminiAdapter, DEFAULT_MODEL
from app.services.llm.base import LLMProvider, StreamChunk


# Patch path: patch where it's used, not where it's defined
GENAI_CLIENT_PATH = 'app.services.llm.gemini_adapter.genai.Client'


class TestGeminiAdapterInit:
    """Tests for GeminiAdapter initialization."""

    def test_initializes_with_api_key(self):
        """Client is created with provided API key."""
        with patch(GENAI_CLIENT_PATH) as MockClient:
            adapter = GeminiAdapter(api_key="test-api-key")

            MockClient.assert_called_once_with(api_key="test-api-key")
            assert adapter._api_key == "test-api-key"

    def test_uses_default_model(self):
        """DEFAULT_MODEL is used when no model specified."""
        with patch(GENAI_CLIENT_PATH):
            adapter = GeminiAdapter(api_key="test-key")

            assert adapter.model == DEFAULT_MODEL
            assert adapter.model == "gemini-3-flash-preview"

    def test_uses_custom_model(self):
        """Custom model parameter is respected."""
        with patch(GENAI_CLIENT_PATH):
            adapter = GeminiAdapter(
                api_key="test-key",
                model="gemini-1.5-pro"
            )

            assert adapter.model == "gemini-1.5-pro"

    def test_provider_returns_google(self):
        """Provider property returns LLMProvider.GOOGLE."""
        with patch(GENAI_CLIENT_PATH):
            adapter = GeminiAdapter(api_key="test-key")

            assert adapter.provider == LLMProvider.GOOGLE


class TestGeminiAdapterStreamChat:
    """Tests for GeminiAdapter.stream_chat method (streaming without tools)."""

    @pytest.mark.asyncio
    async def test_yields_text_chunks(self, mock_gemini_stream):
        """Text content is yielded as text chunks."""
        mock_stream = mock_gemini_stream(["Hello", " world"])

        with patch(GENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.aio.models.generate_content_stream = AsyncMock(
                return_value=mock_stream
            )

            adapter = GeminiAdapter(api_key="test-key")

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
    async def test_yields_complete_with_usage(self, mock_gemini_stream):
        """Complete chunk includes correct usage statistics."""
        mock_stream = mock_gemini_stream(
            text_chunks=["Response"],
            usage={"input_tokens": 100, "output_tokens": 50}
        )

        with patch(GENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.aio.models.generate_content_stream = AsyncMock(
                return_value=mock_stream
            )

            adapter = GeminiAdapter(api_key="test-key")

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
    async def test_converts_messages_to_gemini_format(self, mock_gemini_stream):
        """Messages are converted to Gemini format."""
        mock_stream = mock_gemini_stream(["Response"])

        with patch(GENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value
            mock_client.aio.models.generate_content_stream = AsyncMock(
                return_value=mock_stream
            )

            adapter = GeminiAdapter(api_key="test-key")

            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=messages,
                system_prompt="Be helpful."
            ):
                chunks.append(chunk)

            # Verify generate_content_stream was called
            mock_client.aio.models.generate_content_stream.assert_called_once()

            # Check contents were passed (converted from messages)
            call_kwargs = mock_client.aio.models.generate_content_stream.call_args[1]
            assert "contents" in call_kwargs


class TestGeminiAdapterNonStreaming:
    """Tests for GeminiAdapter non-streaming tool calls."""

    @pytest.mark.asyncio
    async def test_uses_non_streaming_for_tools(self):
        """Tool calls use non-streaming API due to Gemini limitation."""
        with patch(GENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value

            # Mock non-streaming response
            mock_response = MagicMock()
            mock_response.candidates = [MagicMock()]
            mock_response.candidates[0].content.parts = []
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 10
            mock_response.usage_metadata.candidates_token_count = 5

            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response
            )

            adapter = GeminiAdapter(api_key="test-key")

            tools = [{
                "name": "save_artifact",
                "description": "Save an artifact",
                "input_schema": {"type": "object"}
            }]

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Create artifact"}],
                system_prompt="You are helpful.",
                tools=tools
            ):
                chunks.append(chunk)

            # Verify non-streaming endpoint was called
            mock_client.aio.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_yields_tool_use_from_function_call(self):
        """Function calls in response are yielded as tool_use chunks."""
        with patch(GENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value

            # Mock response with function call
            mock_part = MagicMock()
            mock_part.text = None
            mock_part.function_call = MagicMock()
            mock_part.function_call.id = None  # Gemini may not provide id
            mock_part.function_call.name = "save_artifact"
            mock_part.function_call.args = {"title": "Test"}

            mock_response = MagicMock()
            mock_response.candidates = [MagicMock()]
            mock_response.candidates[0].content.parts = [mock_part]
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 10
            mock_response.usage_metadata.candidates_token_count = 5

            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response
            )

            adapter = GeminiAdapter(api_key="test-key")

            tools = [{"name": "save_artifact", "description": "Save"}]

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Create"}],
                system_prompt="You are helpful.",
                tools=tools
            ):
                chunks.append(chunk)

            tool_chunks = [c for c in chunks if c.chunk_type == "tool_use"]
            assert len(tool_chunks) == 1
            assert tool_chunks[0].tool_call["name"] == "save_artifact"
            assert tool_chunks[0].tool_call["input"] == {"title": "Test"}


class TestGeminiAdapterRetry:
    """Tests for GeminiAdapter retry logic."""

    @pytest.mark.asyncio
    async def test_retries_on_429_error(self, mock_gemini_stream):
        """Retries on rate limit (429) error."""
        from google.genai import errors

        with patch(GENAI_CLIENT_PATH) as MockClient:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                mock_client = MockClient.return_value

                # Create a proper APIError - signature: (code, response_json, response=None)
                mock_error = errors.APIError(429, {"error": {"message": "Rate limited"}})
                mock_error.message = "Rate limited"

                call_count = 0
                async def mock_stream_calls(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise mock_error
                    return mock_gemini_stream(["Success"])

                mock_client.aio.models.generate_content_stream = AsyncMock(
                    side_effect=mock_stream_calls
                )

                adapter = GeminiAdapter(api_key="test-key")

                chunks = []
                async for chunk in adapter.stream_chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    system_prompt="You are helpful."
                ):
                    chunks.append(chunk)

                # Should have retried
                assert call_count == 2
                mock_sleep.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_retries_on_500_error(self, mock_gemini_stream):
        """Retries on server error (500)."""
        from google.genai import errors

        with patch(GENAI_CLIENT_PATH) as MockClient:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                mock_client = MockClient.return_value

                # Create a proper APIError - signature: (code, response_json, response=None)
                mock_error = errors.APIError(500, {"error": {"message": "Server error"}})
                mock_error.message = "Server error"

                call_count = 0
                async def mock_stream_calls(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise mock_error
                    return mock_gemini_stream(["Success"])

                mock_client.aio.models.generate_content_stream = AsyncMock(
                    side_effect=mock_stream_calls
                )

                adapter = GeminiAdapter(api_key="test-key")

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
        from google.genai import errors

        with patch(GENAI_CLIENT_PATH) as MockClient:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                mock_client = MockClient.return_value

                # Create a proper APIError - signature: (code, response_json, response=None)
                mock_error = errors.APIError(429, {"error": {"message": "Rate limited"}})
                mock_error.message = "Rate limited"

                # Always raises error (exceeds retry count)
                mock_client.aio.models.generate_content_stream = AsyncMock(
                    side_effect=mock_error
                )

                adapter = GeminiAdapter(api_key="test-key")

                chunks = []
                async for chunk in adapter.stream_chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    system_prompt="You are helpful."
                ):
                    chunks.append(chunk)

                error_chunks = [c for c in chunks if c.chunk_type == "error"]
                assert len(error_chunks) == 1
                assert "429" in error_chunks[0].error


class TestGeminiAdapterErrors:
    """Tests for GeminiAdapter error handling."""

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """API errors yield error chunks."""
        from google.genai import errors

        with patch(GENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value

            # Create a proper APIError - signature: (code, response_json, response=None)
            mock_error = errors.APIError(401, {"error": {"message": "Invalid API key"}})
            mock_error.message = "Invalid API key"

            mock_client.aio.models.generate_content_stream = AsyncMock(
                side_effect=mock_error
            )

            adapter = GeminiAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            error_chunks = [c for c in chunks if c.chunk_type == "error"]
            assert len(error_chunks) == 1
            assert "Gemini error" in error_chunks[0].error
            assert "401" in error_chunks[0].error

    @pytest.mark.asyncio
    async def test_handles_unexpected_error(self):
        """Unexpected errors yield error chunks."""
        with patch(GENAI_CLIENT_PATH) as MockClient:
            mock_client = MockClient.return_value

            mock_client.aio.models.generate_content_stream = AsyncMock(
                side_effect=RuntimeError("Connection failed")
            )

            adapter = GeminiAdapter(api_key="test-key")

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


class TestGeminiAdapterMessageConversion:
    """Tests for message format conversion."""

    def test_converts_user_role(self):
        """User role is preserved."""
        with patch(GENAI_CLIENT_PATH):
            adapter = GeminiAdapter(api_key="test-key")

            messages = [{"role": "user", "content": "Hello"}]
            contents = adapter._convert_messages(messages)

            assert len(contents) == 1
            assert contents[0].role == "user"

    def test_converts_assistant_to_model(self):
        """Assistant role is converted to 'model'."""
        with patch(GENAI_CLIENT_PATH):
            adapter = GeminiAdapter(api_key="test-key")

            messages = [{"role": "assistant", "content": "Hello"}]
            contents = adapter._convert_messages(messages)

            assert len(contents) == 1
            assert contents[0].role == "model"

    def test_handles_multi_part_content(self):
        """Multi-part content (list) is handled."""
        with patch(GENAI_CLIENT_PATH):
            adapter = GeminiAdapter(api_key="test-key")

            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Part 1"},
                    {"type": "text", "text": "Part 2"}
                ]
            }]
            contents = adapter._convert_messages(messages)

            assert len(contents) == 1
            # Multiple parts should be combined
            assert len(contents[0].parts) == 2
