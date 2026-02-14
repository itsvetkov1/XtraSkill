"""LLM testing fixtures including MockLLMAdapter."""

from typing import Any, AsyncGenerator, Dict, List, Optional
import pytest

from app.services.llm.base import LLMAdapter, LLMProvider, StreamChunk


class MockLLMAdapter(LLMAdapter):
    """
    Mock LLM adapter for testing without real API calls.

    Configurable to return:
    - Text responses (default)
    - Tool calls
    - Errors
    - Custom chunk sequences

    Usage:
        # Simple text response
        adapter = MockLLMAdapter(responses=["Hello", " world"])

        # Tool call response
        adapter = MockLLMAdapter(tool_calls=[{
            "id": "call_1",
            "name": "save_artifact",
            "input": {"title": "Test"}
        }])

        # Error simulation
        adapter = MockLLMAdapter(raise_error="API rate limit")

        # Custom chunks
        adapter = MockLLMAdapter(chunks=[
            StreamChunk(chunk_type="text", content="Hello"),
            StreamChunk(chunk_type="complete", usage={"input_tokens": 10, "output_tokens": 5})
        ])
    """

    # Signal that this is NOT an agent provider (handles tools manually in AIService)
    is_agent_provider = False

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        responses: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        raise_error: Optional[str] = None,
        chunks: Optional[List[StreamChunk]] = None,
        usage: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize MockLLMAdapter with configurable behavior.

        Args:
            provider: Provider to report (default: ANTHROPIC)
            responses: List of text strings to yield as text chunks
            tool_calls: List of tool call dicts to yield as tool_use chunks
            raise_error: If set, yields an error chunk with this message
            chunks: If set, yields these exact chunks (overrides responses/tool_calls)
            usage: Token usage to report in complete chunk (default: 10/5)
        """
        self._provider = provider
        self._responses = responses or []
        self._tool_calls = tool_calls or []
        self._raise_error = raise_error
        self._chunks = chunks
        self._usage = usage or {"input_tokens": 10, "output_tokens": 5}

        # Track calls for assertions
        self.call_history: List[Dict[str, Any]] = []

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream mock response chunks."""
        # Record the call
        self.call_history.append({
            "messages": messages,
            "system_prompt": system_prompt,
            "tools": tools,
            "max_tokens": max_tokens,
        })

        # If error configured, yield error chunk
        if self._raise_error:
            yield StreamChunk(chunk_type="error", error=self._raise_error)
            return

        # If custom chunks provided, yield those
        if self._chunks:
            for chunk in self._chunks:
                yield chunk
            return

        # Yield text responses
        for text in self._responses:
            yield StreamChunk(chunk_type="text", content=text)

        # Yield tool calls
        for tool_call in self._tool_calls:
            yield StreamChunk(chunk_type="tool_use", tool_call=tool_call)

        # Yield completion
        yield StreamChunk(chunk_type="complete", usage=self._usage)


@pytest.fixture
def mock_llm_adapter():
    """Factory fixture for creating MockLLMAdapter instances."""
    def _create(
        responses: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        raise_error: Optional[str] = None,
        **kwargs
    ) -> MockLLMAdapter:
        return MockLLMAdapter(
            responses=responses,
            tool_calls=tool_calls,
            raise_error=raise_error,
            **kwargs
        )
    return _create


@pytest.fixture
def mock_llm_text_response():
    """Pre-configured MockLLMAdapter that returns simple text."""
    return MockLLMAdapter(responses=["This is a test response from the mock LLM."])


@pytest.fixture
def mock_llm_tool_response():
    """Pre-configured MockLLMAdapter that returns a tool call."""
    return MockLLMAdapter(tool_calls=[{
        "id": "toolu_01",
        "name": "save_artifact",
        "input": {
            "artifact_type": "brd",
            "title": "Test BRD",
            "content_markdown": "# Test BRD\n\nTest content."
        }
    }])


@pytest.fixture
def mock_llm_error():
    """Pre-configured MockLLMAdapter that returns an error."""
    return MockLLMAdapter(raise_error="API rate limit exceeded")
