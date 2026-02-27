"""
DeepSeek Adapter.

Implements the LLMAdapter interface for DeepSeek models
using the OpenAI SDK with base_url override.

DeepSeek is OpenAI-compatible, so we use the openai package
with a different base URL.
"""
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, List, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APIStatusError

from .base import LLMAdapter, LLMProvider, StreamChunk

# Retry configuration (per CONTEXT.md: 2 retries, fixed delay)
MAX_RETRIES = 2
RETRY_DELAY = 1.0  # seconds

# Default model (configurable via DEEPSEEK_MODEL env var)
DEFAULT_MODEL = "deepseek-reasoner"

# DeepSeek API base URL
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekAdapter(LLMAdapter):
    """
    DeepSeek adapter implementation.

    Uses OpenAI SDK with base_url override for API compatibility.
    Reasoning content is hidden per CONTEXT.md decision.

    CRITICAL: reasoning_content must NOT be included in subsequent
    messages - the API returns 400 if you pass it back.
    """

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
    ):
        """
        Initialize the DeepSeek adapter.

        Args:
            api_key: DeepSeek API key for authentication
            model: DeepSeek model to use (defaults to deepseek-reasoner)
        """
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL,
        )

    @property
    def provider(self) -> LLMProvider:
        """Return the DeepSeek provider identifier."""
        return LLMProvider.DEEPSEEK

    @property
    def supports_tools(self) -> bool:
        """deepseek-reasoner has unstable tool support — use document injection instead."""
        return self.model != "deepseek-reasoner"

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat from DeepSeek, yielding StreamChunk objects.

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
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages, system_prompt)

        # Build request kwargs
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "stream": True,
            "max_tokens": max_tokens,
        }

        # Add tools if provided (use deepseek-chat for tools, not deepseek-reasoner)
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            # Note: deepseek-reasoner may have unstable tool support per RESEARCH.md
            # Consider using deepseek-chat for tool calls if issues arise

        # Streaming with retry
        for attempt in range(MAX_RETRIES + 1):
            try:
                async for chunk in self._stream_impl(**kwargs):
                    yield chunk
                return  # Success
            except RateLimitError as e:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                yield StreamChunk(
                    chunk_type="error",
                    error=f"DeepSeek rate limit exceeded (429): {str(e)}",
                )
                return
            except APIStatusError as e:
                if self._is_retryable(e) and attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                yield StreamChunk(
                    chunk_type="error",
                    error=f"DeepSeek error ({e.status_code}): {e.message}",
                )
                return
            except APIError as e:
                yield StreamChunk(
                    chunk_type="error",
                    error=f"DeepSeek API error: {str(e)}",
                )
                return
            except Exception as e:
                yield StreamChunk(
                    chunk_type="error",
                    error=f"DeepSeek unexpected error: {str(e)}",
                )
                return

    async def _stream_impl(self, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Internal streaming implementation."""
        usage = {"input_tokens": 0, "output_tokens": 0}

        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Handle reasoning_content (hide per CONTEXT.md)
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                # Skip yielding reasoning content to user
                # Could optionally store in database per Claude's discretion
                pass

            # Handle regular content
            if delta.content:
                yield StreamChunk(chunk_type="text", content=delta.content)

            # Handle tool calls
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tool_call in delta.tool_calls:
                    if tool_call.function:
                        yield StreamChunk(
                            chunk_type="tool_use",
                            tool_call={
                                "id": tool_call.id or f"call_{id(tool_call)}",
                                "name": tool_call.function.name or "",
                                "input": self._parse_tool_args(tool_call.function.arguments),
                            },
                        )

            # Track usage from final chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                usage["input_tokens"] = chunk.usage.prompt_tokens or 0
                usage["output_tokens"] = chunk.usage.completion_tokens or 0

        yield StreamChunk(chunk_type="complete", usage=usage)

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
    ) -> List[Dict[str, Any]]:
        """
        Convert messages to OpenAI/DeepSeek format with system prompt.

        Args:
            messages: Messages in provider-agnostic format
            system_prompt: System instructions for the model

        Returns:
            Messages in OpenAI format with system prompt prepended
        """
        openai_messages = [{"role": "system", "content": system_prompt}]

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, str):
                openai_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Handle multi-part content (Anthropic format)
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_result":
                            text_parts.append(f"Tool result: {block.get('content', '')}")
                if text_parts:
                    openai_messages.append({"role": role, "content": "\n".join(text_parts)})

        return openai_messages

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tools from Anthropic format to OpenAI format.

        Args:
            tools: Tool definitions in Anthropic format

        Returns:
            Tool definitions in OpenAI function calling format
        """
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return openai_tools

    def _parse_tool_args(self, arguments: Optional[str]) -> Dict[str, Any]:
        """
        Parse tool arguments from JSON string.

        Args:
            arguments: JSON string of arguments or None

        Returns:
            Parsed dictionary or empty dict if parsing fails
        """
        if not arguments:
            return {}
        try:
            return json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            return {"raw": arguments}

    def _is_retryable(self, error: APIStatusError) -> bool:
        """
        Check if error is retryable (rate limit or server error).

        Args:
            error: API status error with status_code

        Returns:
            True if error should be retried
        """
        return error.status_code in (429, 500, 503)
