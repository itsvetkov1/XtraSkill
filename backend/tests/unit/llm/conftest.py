"""Shared fixtures for LLM adapter unit tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import List, Dict, Any, Optional


async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


@pytest.fixture
def mock_anthropic_stream():
    """
    Factory for creating mock Anthropic stream context manager.

    Returns a factory function that creates a mock stream with:
    - Async context manager protocol (__aenter__/__aexit__)
    - text_stream async iterable
    - get_final_message() returning mock final message with content and usage
    """
    def _create(
        text_chunks: List[str],
        tool_blocks: Optional[List[MagicMock]] = None,
        usage: Optional[Dict[str, int]] = None
    ):
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_stream
        mock_stream.__aexit__.return_value = None

        # Create async generator for text_stream
        async def text_stream():
            for text in text_chunks:
                yield text

        mock_stream.text_stream = text_stream()

        # Final message mock
        mock_final = MagicMock()
        mock_final.content = tool_blocks or []
        mock_final.usage = MagicMock()
        mock_final.usage.input_tokens = (usage or {}).get("input_tokens", 10)
        mock_final.usage.output_tokens = (usage or {}).get("output_tokens", 5)
        mock_stream.get_final_message = AsyncMock(return_value=mock_final)

        return mock_stream

    return _create


@pytest.fixture
def mock_tool_use_block():
    """Factory for creating mock Anthropic tool_use content blocks."""
    def _create(
        tool_id: str = "toolu_01",
        name: str = "test_tool",
        input_data: Optional[Dict[str, Any]] = None
    ) -> MagicMock:
        block = MagicMock()
        block.type = "tool_use"
        block.id = tool_id
        block.name = name
        block.input = input_data or {}
        return block

    return _create


@pytest.fixture
def mock_gemini_stream():
    """
    Factory for creating mock Gemini streaming response.

    Returns a factory function that creates an async generator
    yielding mock chunks with text and usage_metadata.
    """
    def _create(
        text_chunks: List[str],
        usage: Optional[Dict[str, int]] = None
    ):
        async def stream():
            for text in text_chunks:
                chunk = MagicMock()
                chunk.text = text
                chunk.usage_metadata = None
                yield chunk

            # Final chunk with usage
            final = MagicMock()
            final.text = None
            final.usage_metadata = MagicMock()
            final.usage_metadata.prompt_token_count = (usage or {}).get("input_tokens", 10)
            final.usage_metadata.candidates_token_count = (usage or {}).get("output_tokens", 5)
            yield final

        return stream()

    return _create


@pytest.fixture
def mock_deepseek_stream():
    """
    Factory for creating mock DeepSeek (OpenAI-compatible) streaming response.

    Returns a factory function that creates an async generator
    yielding mock chunks with delta content and usage.
    """
    def _create(
        text_chunks: List[str],
        reasoning_chunks: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        usage: Optional[Dict[str, int]] = None
    ):
        async def stream():
            # Yield reasoning chunks (if any)
            for reasoning in (reasoning_chunks or []):
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta = MagicMock()
                chunk.choices[0].delta.content = None
                chunk.choices[0].delta.reasoning_content = reasoning
                chunk.choices[0].delta.tool_calls = None
                chunk.usage = None
                yield chunk

            # Yield text chunks
            for text in text_chunks:
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta = MagicMock()
                chunk.choices[0].delta.content = text
                chunk.choices[0].delta.reasoning_content = None
                chunk.choices[0].delta.tool_calls = None
                chunk.usage = None
                yield chunk

            # Yield tool calls (if any)
            for tool_call in (tool_calls or []):
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta = MagicMock()
                chunk.choices[0].delta.content = None
                chunk.choices[0].delta.reasoning_content = None

                mock_tool = MagicMock()
                mock_tool.id = tool_call.get("id", "call_01")
                mock_tool.function = MagicMock()
                mock_tool.function.name = tool_call.get("name", "test_func")
                mock_tool.function.arguments = tool_call.get("arguments", "{}")

                chunk.choices[0].delta.tool_calls = [mock_tool]
                chunk.usage = None
                yield chunk

            # Final chunk with usage
            final = MagicMock()
            final.choices = []
            final.usage = MagicMock()
            final.usage.prompt_tokens = (usage or {}).get("input_tokens", 10)
            final.usage.completion_tokens = (usage or {}).get("output_tokens", 5)
            yield final

        return stream()

    return _create
