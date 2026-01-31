"""
Anthropic Claude Adapter.

Implements the LLMAdapter interface for Anthropic's Claude models,
extracting streaming logic from the original ai_service.py.

This adapter handles:
- Claude API client instantiation
- Streaming message API calls
- Response normalization to StreamChunk format
- Anthropic-specific error handling

The adapter does NOT handle:
- Tool execution (stays in AIService)
- Tool use loops (stays in AIService)
- SSE event formatting (stays in route handler)
"""
import anthropic
from typing import AsyncGenerator, Dict, Any, List, Optional

from .base import LLMAdapter, LLMProvider, StreamChunk


# Default Claude model
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class AnthropicAdapter(LLMAdapter):
    """
    Anthropic Claude adapter implementation.

    Provides streaming chat capabilities using the Anthropic SDK,
    normalizing responses to the StreamChunk format.
    """

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
    ):
        """
        Initialize the Anthropic adapter.

        Args:
            api_key: Anthropic API key for authentication
            model: Claude model to use (defaults to claude-sonnet-4-5-20250929)
        """
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    @property
    def provider(self) -> LLMProvider:
        """Return the Anthropic provider identifier."""
        return LLMProvider.ANTHROPIC

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response from Claude, yielding StreamChunk objects.

        This method handles a SINGLE API call. Tool use loops remain in
        the calling AIService code.

        Args:
            messages: Conversation history
            system_prompt: System instructions for the model
            tools: Optional list of tool definitions (Anthropic format)
            max_tokens: Maximum tokens in the response

        Yields:
            StreamChunk objects:
            - "text" chunks as content streams
            - "tool_use" chunks if model requests tool calls
            - "complete" chunk with usage statistics
            - "error" chunk if an error occurs
        """
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                tools=tools or [],
                system=system_prompt,
            ) as stream:
                # Stream text content as it arrives
                async for text in stream.text_stream:
                    yield StreamChunk(chunk_type="text", content=text)

                # Get final message for tool calls and usage
                final = await stream.get_final_message()

                # Yield tool_use chunks if present
                for block in final.content:
                    if block.type == "tool_use":
                        yield StreamChunk(
                            chunk_type="tool_use",
                            tool_call={
                                "id": block.id,
                                "name": block.name,
                                "input": block.input,
                            },
                        )

                # Yield complete chunk with usage statistics
                yield StreamChunk(
                    chunk_type="complete",
                    content="",  # Content already streamed
                    usage={
                        "input_tokens": final.usage.input_tokens,
                        "output_tokens": final.usage.output_tokens,
                    },
                )

        except anthropic.APIError as e:
            yield StreamChunk(
                chunk_type="error",
                error=f"Anthropic API error: {str(e)}",
            )
        except Exception as e:
            yield StreamChunk(
                chunk_type="error",
                error=f"Unexpected error: {str(e)}",
            )
