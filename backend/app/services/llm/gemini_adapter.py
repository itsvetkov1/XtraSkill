"""
Google Gemini Adapter.

Implements the LLMAdapter interface for Google's Gemini models
using the google-genai SDK with async streaming support.
"""
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional

from google import genai
from google.genai import types, errors

from .base import LLMAdapter, LLMProvider, StreamChunk

# Retry configuration (per CONTEXT.md: 2 retries, fixed delay)
MAX_RETRIES = 2
RETRY_DELAY = 1.0  # seconds

# Default model (configurable via GEMINI_MODEL env var)
DEFAULT_MODEL = "gemini-3-flash-preview"


class GeminiAdapter(LLMAdapter):
    """
    Google Gemini adapter implementation.

    Provides streaming chat using google-genai SDK.
    Thinking content is hidden per CONTEXT.md decision.
    """

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
    ):
        """
        Initialize the Gemini adapter.

        Args:
            api_key: Google API key for authentication
            model: Gemini model to use (defaults to gemini-3-flash-preview)
        """
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.client = genai.Client(api_key=api_key)

    @property
    def provider(self) -> LLMProvider:
        """Return the Google provider identifier."""
        return LLMProvider.GOOGLE

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat from Gemini, yielding StreamChunk objects.

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
        # Convert messages to Gemini format
        contents = self._convert_messages(messages)

        # Build config
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            thinking_config=types.ThinkingConfig(thinking_budget=8192),
            # Note: NOT including include_thoughts=True per CONTEXT.md
        )

        # Handle tools if provided (non-streaming required for Gemini tools)
        if tools:
            # Gemini doesn't support streaming + tools, use non-streaming
            async for chunk in self._non_streaming_with_tools(
                contents, config, tools
            ):
                yield chunk
            return

        # Streaming without tools
        for attempt in range(MAX_RETRIES + 1):
            try:
                async for chunk in self._stream_impl(contents, config):
                    yield chunk
                return  # Success
            except errors.APIError as e:
                if self._is_retryable(e) and attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                yield StreamChunk(
                    chunk_type="error",
                    error=f"Gemini error ({e.code}): {e.message}",
                )
                return
            except Exception as e:
                yield StreamChunk(
                    chunk_type="error",
                    error=f"Gemini unexpected error: {str(e)}",
                )
                return

    async def _stream_impl(
        self,
        contents: list,
        config: types.GenerateContentConfig,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Internal streaming implementation."""
        usage = {"input_tokens": 0, "output_tokens": 0}

        async for chunk in await self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield StreamChunk(chunk_type="text", content=chunk.text)

            # Track usage from final chunk
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                usage["input_tokens"] = chunk.usage_metadata.prompt_token_count or 0
                usage["output_tokens"] = chunk.usage_metadata.candidates_token_count or 0

        yield StreamChunk(chunk_type="complete", usage=usage)

    async def _non_streaming_with_tools(
        self,
        contents: list,
        config: types.GenerateContentConfig,
        tools: List[Dict[str, Any]],
    ) -> AsyncGenerator[StreamChunk, None]:
        """Handle tool use (requires non-streaming for Gemini)."""
        try:
            # Convert tools to Gemini format
            gemini_tools = self._convert_tools(tools)
            config.tools = gemini_tools

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            # Process response
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    yield StreamChunk(chunk_type="text", content=part.text)
                if hasattr(part, 'function_call') and part.function_call:
                    yield StreamChunk(
                        chunk_type="tool_use",
                        tool_call={
                            "id": getattr(part.function_call, 'id', f"call_{id(part)}"),
                            "name": part.function_call.name,
                            "input": dict(part.function_call.args) if part.function_call.args else {},
                        },
                    )

            # Usage
            usage = {"input_tokens": 0, "output_tokens": 0}
            if response.usage_metadata:
                usage["input_tokens"] = response.usage_metadata.prompt_token_count or 0
                usage["output_tokens"] = response.usage_metadata.candidates_token_count or 0

            yield StreamChunk(chunk_type="complete", usage=usage)

        except errors.APIError as e:
            yield StreamChunk(
                chunk_type="error",
                error=f"Gemini error ({e.code}): {e.message}",
            )
        except Exception as e:
            yield StreamChunk(
                chunk_type="error",
                error=f"Gemini unexpected error: {str(e)}",
            )

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> list:
        """Convert messages from Anthropic format to Gemini format."""
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = msg.get("content", "")
            if isinstance(content, str):
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part(text=content)]
                ))
            elif isinstance(content, list):
                # Handle multi-part content (text blocks)
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(types.Part(text=block.get("text", "")))
                    elif isinstance(block, dict) and block.get("type") == "tool_result":
                        parts.append(types.Part(text=f"Tool result: {block.get('content', '')}"))
                if parts:
                    contents.append(types.Content(role=role, parts=parts))
        return contents

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> list:
        """Convert tools from Anthropic format to Gemini format."""
        gemini_tools = []
        for tool in tools:
            gemini_tools.append(types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool.get("name", ""),
                        description=tool.get("description", ""),
                        parameters=tool.get("input_schema", {}),
                    )
                ]
            ))
        return gemini_tools

    def _is_retryable(self, error: errors.APIError) -> bool:
        """Check if error is retryable (rate limit or server error)."""
        return error.code in (429, 500, 503)
