"""
OpenClaw Adapter for LLM Provider Abstraction.

Implements LLMAdapter interface for OpenClaw Gateway integration.
Provides multi-model flexibility and access to OpenClaw skills as tools.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional

import httpx

from .base import LLMAdapter, LLMProvider, StreamChunk
from app.config import settings

logger = logging.getLogger(__name__)


class OpenClawAdapter(LLMAdapter):
    """
    OpenClaw Gateway adapter.
    
    Connects to OpenClaw Gateway to use agents as LLM providers.
    Supports session reuse for conversation continuity.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "default",
        gateway_url: str = "http://localhost:8080",
        agent_id: str = "dev",
    ):
        """
        Initialize OpenClaw adapter.
        
        Args:
            api_key: OpenClaw API key
            model: Model to use (default from gateway)
            gateway_url: OpenClaw Gateway URL
            agent_id: Which agent to use (dev, forger, personal, alfa)
        """
        self._api_key = api_key
        self._model = model
        self._gateway_url = gateway_url.rstrip("/")
        self._agent_id = agent_id
        self._client: Optional[httpx.AsyncClient] = None
        
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENCLAW

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._gateway_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response from OpenClaw Gateway.
        
        Args:
            messages: Conversation history [{"role": "user"|"assistant", "content": "..."}]
            system_prompt: System instructions
            tools: Tool definitions (passed to OpenClaw agent)
            max_tokens: Max response tokens
            
        Yields:
            StreamChunk objects
        """
        client = await self._get_client()
        
        # Convert messages to OpenClaw format
        openclaw_messages = []
        
        # Add system prompt as first message if present
        if system_prompt:
            openclaw_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Convert user/assistant messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle content as string or list
            if isinstance(content, list):
                # Multi-modal content - extract text for now
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") == "image":
                            text_parts.append(f"[Image: {part.get('source', {}).get('url', 'unknown')}]")
                content = "\n".join(text_parts)
            
            openclaw_messages.append({
                "role": role,
                "content": str(content)
            })

        # Build request payload
        payload = {
            "messages": openclaw_messages,
            "model": self._model,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        # Add tools if provided
        if tools:
            # OpenClaw uses its own tool format, pass as context
            payload["tools"] = tools
            payload["agent_id"] = self._agent_id

        try:
            # Call OpenClaw Gateway chat endpoint
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
            ) as response:
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield StreamChunk(
                        chunk_type="error",
                        error=f"OpenClaw Gateway error {response.status_code}: {error_text.decode() if error_text else 'Unknown'}"
                    )
                    return

                # Parse SSE stream
                async for line in response.aiter_lines():
                    if not line.strip() or not line.startswith("data:"):
                        continue
                    
                    try:
                        data = json.loads(line[5:])  # Remove "data: " prefix
                        
                        # Handle different event types from OpenClaw
                        event_type = data.get("type", "")
                        
                        if event_type == "content" or event_type == "text":
                            content = data.get("content", "") or data.get("delta", "")
                            if content:
                                yield StreamChunk(chunk_type="text", content=content)
                                
                        elif event_type == "thinking" or event_type == "reasoning":
                            thinking = data.get("content", "") or data.get("thinking", "")
                            if thinking:
                                yield StreamChunk(chunk_type="thinking", thinking_content=thinking)
                                
                        elif event_type == "tool_use" or event_type == "tool_call":
                            tool_call = {
                                "id": data.get("id", ""),
                                "name": data.get("name", ""),
                                "input": data.get("input", {}),
                            }
                            yield StreamChunk(chunk_type="tool_use", tool_call=tool_call)
                            
                        elif event_type == "tool_result":
                            # Tool results handled by OpenClaw internally
                            pass
                            
                        elif event_type == "complete" or event_type == "done":
                            usage = data.get("usage", {})
                            yield StreamChunk(
                                chunk_type="complete",
                                usage={
                                    "input_tokens": usage.get("input_tokens", 0),
                                    "output_tokens": usage.get("output_tokens", 0),
                                }
                            )
                            
                        elif event_type == "error":
                            error = data.get("error", data.get("message", "Unknown error"))
                            yield StreamChunk(chunk_type="error", error=error)
                            
                    except json.JSONDecodeError:
                        # Skip non-JSON lines
                        continue
                        
        except httpx.ConnectError as e:
            yield StreamChunk(
                chunk_type="error",
                error=f"Cannot connect to OpenClaw Gateway at {self._gateway_url}: {e}"
            )
        except httpx.TimeoutException as e:
            yield StreamChunk(
                chunk_type="error",
                error=f"OpenClaw Gateway timeout: {e}"
            )
        except Exception as e:
            logger.exception("OpenClaw adapter error")
            yield StreamChunk(chunk_type="error", error=str(e))


# Factory function for creating adapter with settings
def create_openclaw_adapter() -> OpenClawAdapter:
    """
    Create OpenClaw adapter from application settings.
    
    Returns:
        OpenClawAdapter configured from settings
        
    Raises:
        ValueError: If required settings are missing
    """
    api_key = getattr(settings, "openclaw_api_key", None)
    if not api_key:
        raise ValueError("OPENCLAW_API_KEY not configured")
    
    gateway_url = getattr(settings, "openclaw_gateway_url", "http://localhost:8080")
    agent_id = getattr(settings, "openclaw_agent_id", "dev")
    
    return OpenClawAdapter(
        api_key=api_key,
        gateway_url=gateway_url,
        agent_id=agent_id,
    )
