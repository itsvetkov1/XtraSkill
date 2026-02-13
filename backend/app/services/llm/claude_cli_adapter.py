"""
Claude Code CLI Subprocess Adapter (Stub).

Implements LLMAdapter interface for Claude Code CLI subprocess integration.
This is a stub — actual stream_chat implementation comes in Phase 59.

Architecture note:
This adapter will spawn Claude Code CLI as a subprocess with
--output-format stream-json, parse line-delimited JSON from stdout,
and translate events to StreamChunk format. Process lifecycle
management (timeout, cleanup, zombie prevention) is critical.
"""
from typing import AsyncGenerator, Dict, Any, List, Optional
from .base import LLMAdapter, LLMProvider, StreamChunk

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class ClaudeCLIAdapter(LLMAdapter):
    """
    Claude Code CLI subprocess adapter stub.

    Will spawn CLI process, parse JSON stream output, and translate
    to StreamChunk format. Uses shared MCP tools from mcp_tools.py
    via MCP config passed to CLI.

    Phase 59 will implement the actual stream_chat method.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.CLAUDE_CODE_CLI

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        raise NotImplementedError(
            "ClaudeCLIAdapter.stream_chat not yet implemented. "
            "Implementation planned for Phase 59."
        )
        # Required yield to satisfy async generator type
        yield  # pragma: no cover
