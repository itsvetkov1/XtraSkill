"""
LLM Provider Abstraction Base Module.

Defines the abstract base class for LLM adapters, the StreamChunk dataclass
for normalized streaming responses, and the LLMProvider enum for supported providers.

This module enables multi-provider support (Anthropic, Google Gemini, DeepSeek)
while maintaining a consistent interface for the AI service layer.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Dict, Any, List, Optional


class LLMProvider(str, Enum):
    """
    Supported LLM providers.

    Each provider has a corresponding adapter implementation that handles
    the provider-specific API calls and response normalization.
    """
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    CLAUDE_CODE_SDK = "claude-code-sdk"
    CLAUDE_CODE_CLI = "claude-code-cli"


@dataclass
class StreamChunk:
    """
    Normalized streaming response chunk from any LLM provider.

    Used by the route handler to generate SSE events. All provider-specific
    response formats are converted to this common structure.

    Attributes:
        chunk_type: Type of chunk - one of:
            - "text": Regular text content
            - "thinking": Reasoning/thinking content (for providers that support it)
            - "tool_use": Tool call request from the model
            - "tool_result": Result of tool execution (internal use)
            - "complete": Final message with usage statistics
            - "error": Error occurred during streaming
        content: Text content for "text" chunks, empty for others
        thinking_content: Reserved for future providers (Gemini, DeepSeek) that
            expose reasoning/thinking content separately. Always None for Anthropic.
        tool_call: For "tool_use" chunks: {"id": str, "name": str, "input": dict}
        usage: For "complete" chunks: {"input_tokens": int, "output_tokens": int}
        error: For "error" chunks: Error message string
    """
    chunk_type: str
    content: str = ""
    thinking_content: Optional[str] = None
    tool_call: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class LLMAdapter(ABC):
    """
    Abstract base class for LLM provider adapters.

    Each provider (Anthropic, Google, DeepSeek) implements this interface
    to provide a consistent streaming chat API regardless of the underlying
    provider SDK.

    The adapter handles:
    - Provider-specific client instantiation
    - Message format conversion (if needed)
    - Streaming response normalization to StreamChunk
    - Provider-specific error handling

    The adapter does NOT handle:
    - Tool execution (stays in AIService)
    - Tool use loops (stays in AIService)
    - SSE event formatting (stays in route handler)
    """

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """
        Return the provider identifier.

        Returns:
            LLMProvider enum value for this adapter
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response, yielding normalized StreamChunk objects.

        This method handles a SINGLE API call to the provider. Tool use loops
        and multi-turn conversation handling remain in the calling code.

        Args:
            messages: Conversation history in provider-agnostic format
                [{"role": "user"|"assistant", "content": str|list}, ...]
            system_prompt: System instructions for the model
            tools: Optional list of tool definitions in Anthropic format
                (adapters convert to provider-specific format if needed)
            max_tokens: Maximum tokens in the response

        Yields:
            StreamChunk objects for each piece of the streaming response:
            - Multiple "text" chunks as content streams
            - Optional "tool_use" chunks if model requests tool calls
            - Final "complete" chunk with usage statistics
            - "error" chunk if an error occurs

        Note:
            This is an async generator. Use with `async for`:
            ```
            async for chunk in adapter.stream_chat(messages, system_prompt):
                if chunk.chunk_type == "text":
                    print(chunk.content)
            ```
        """
        # This yield is required to make this an async generator
        # Concrete implementations will override this entirely
        yield StreamChunk(chunk_type="error", error="Not implemented")
