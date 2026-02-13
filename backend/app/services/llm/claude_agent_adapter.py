"""
Claude Agent SDK Adapter (Stub).

Implements LLMAdapter interface for Claude Agent SDK integration.
This is a stub — actual stream_chat implementation comes in Phase 58.

Architecture note (from research PITFALL-04):
The Agent SDK handles tool execution internally via MCP servers.
Unlike other adapters where AIService runs an external tool loop,
this adapter will bypass the manual tool loop. The SDK's agent loop
calls tools automatically via the MCP server from mcp_tools.py.
"""
from typing import AsyncGenerator, Dict, Any, List, Optional
from .base import LLMAdapter, LLMProvider, StreamChunk

DEFAULT_MODEL = "claude-sonnet-4-5-20250514"


class ClaudeAgentAdapter(LLMAdapter):
    """
    Claude Agent SDK adapter stub.

    Will translate Agent SDK streaming events (AssistantMessage, StreamEvent,
    ResultMessage) to StreamChunk format. Uses shared MCP tools from
    mcp_tools.py for search_documents and save_artifact.

    Phase 58 will implement the actual stream_chat method.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.CLAUDE_CODE_SDK

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        raise NotImplementedError(
            "ClaudeAgentAdapter.stream_chat not yet implemented. "
            "Implementation planned for Phase 58."
        )
        # Required yield to satisfy async generator type
        yield  # pragma: no cover
