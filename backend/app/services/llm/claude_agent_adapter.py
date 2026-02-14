"""
Claude Agent SDK Adapter.

Implements LLMAdapter interface for Claude Agent SDK integration.
Translates SDK streaming events to StreamChunk format and handles multi-turn
agent loops with MCP tool integration.

Architecture note (from research PITFALL-04):
The Agent SDK handles tool execution internally via MCP servers.
Unlike other adapters where AIService runs an external tool loop,
this adapter bypasses the manual tool loop. The SDK's agent loop
calls tools automatically via the MCP server from mcp_tools.py.
"""
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from uuid import uuid4

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import (
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    StreamEvent,
)

from .base import LLMAdapter, LLMProvider, StreamChunk
from app.services.mcp_tools import (
    create_ba_mcp_server,
    get_mcp_http_server_url,
    register_db_session,
    unregister_db_session,
    _db_context,
    _project_id_context,
    _thread_id_context,
    _documents_used_context,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5-20250514"


class ClaudeAgentAdapter(LLMAdapter):
    """
    Claude Agent SDK adapter.

    Translates Agent SDK streaming events (AssistantMessage, StreamEvent,
    ResultMessage) to StreamChunk format. Uses shared MCP tools from
    mcp_tools.py for search_documents and save_artifact.

    The SDK handles tool execution internally via MCP, so AIService
    must bypass its manual tool loop when using this adapter.
    """

    # Signal to AIService that this adapter handles tools internally
    is_agent_provider = True

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize Claude Agent SDK adapter.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-sonnet-4-5-20250514)
        """
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

        # Create MCP server for tools (in-process for POC)
        self.mcp_server = create_ba_mcp_server()

        # Check if HTTP MCP server is available
        self.mcp_server_url = get_mcp_http_server_url()

        # Context will be set before each stream_chat call
        self.db = None
        self.project_id = None
        self.thread_id = None

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.CLAUDE_CODE_SDK

    def set_context(self, db, project_id: str, thread_id: str):
        """
        Set request context for this adapter.

        Called by AIService before stream_chat() to provide database
        session and request context.

        Args:
            db: SQLAlchemy AsyncSession
            project_id: Project ID for document search
            thread_id: Thread ID for artifact association
        """
        self.db = db
        self.project_id = project_id
        self.thread_id = thread_id

    def _convert_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """
        Convert message history to prompt string for SDK.

        Args:
            messages: Conversation history in standard format

        Returns:
            str: Formatted prompt string
        """
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, str):
                prompt_parts.append(f"[{role.upper()}]: {content}")
            elif isinstance(content, list):
                # Handle tool results or multi-part content
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "tool_result":
                            prompt_parts.append(f"[TOOL_RESULT]: {part.get('content', '')}")
                        elif part.get("type") == "text":
                            prompt_parts.append(f"[{role.upper()}]: {part.get('text', '')}")
                        else:
                            prompt_parts.append(
                                f"[{role.upper()}]: {part.get('content', part.get('text', ''))}"
                            )

        return "\n\n".join(prompt_parts)

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response using Claude Agent SDK.

        Translates SDK events to StreamChunk format for consistent interface.
        The SDK handles tool execution internally via MCP.

        Args:
            messages: Conversation history
            system_prompt: System instructions
            tools: Ignored (SDK uses MCP tools, not Anthropic tool format)
            max_tokens: Maximum tokens (ignored by SDK, uses model defaults)

        Yields:
            StreamChunk: Normalized streaming events
        """
        if not self.db or not self.project_id or not self.thread_id:
            yield StreamChunk(
                chunk_type="error",
                error="Adapter context not set. Call set_context() before stream_chat()."
            )
            return

        # Generate session ID for HTTP transport (if available)
        session_id = str(uuid4())

        # For POC: Use ContextVars since HTTP MCP server not yet implemented
        # Set context variables for tools
        _db_context.set(self.db)
        _project_id_context.set(self.project_id)
        _thread_id_context.set(self.thread_id)
        _documents_used_context.set([])  # Initialize for source attribution

        # Build prompt from messages
        prompt = self._convert_messages_to_prompt(messages)

        # Configure SDK options
        # NOTE: Phase 58 POC uses in-process MCP. HTTP transport would be configured here:
        # mcp_servers={"ba": {"type": "http", "url": self.mcp_server_url, "headers": {...}}}
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"ba": self.mcp_server},  # In-process MCP for POC
            allowed_tools=[
                "mcp__ba__search_documents",
                "mcp__ba__save_artifact",
            ],
            permission_mode="acceptEdits",
            include_partial_messages=True,  # Enable StreamEvent for incremental text
            model=self.model,
            # No max_turns limit for POC (per locked decision)
        )

        documents_used = []  # Track source attribution
        turn_count = 0

        try:
            async for message in query(prompt=prompt, options=options):
                # StreamEvent: Incremental text deltas
                if isinstance(message, StreamEvent):
                    if hasattr(message, 'delta') and message.delta:
                        delta = message.delta
                        if hasattr(delta, 'text') and delta.text:
                            yield StreamChunk(chunk_type="text", content=delta.text)

                # AssistantMessage: Complete blocks (text, tool_use, tool_result)
                elif isinstance(message, AssistantMessage):
                    turn_count += 1
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Text already streamed via StreamEvent when include_partial_messages=True
                            # Don't yield again to avoid duplication
                            pass

                        elif isinstance(block, ToolUseBlock):
                            # Tool activity indicator
                            yield StreamChunk(
                                chunk_type="tool_use",
                                tool_call={
                                    "id": block.id,
                                    "name": block.name,
                                    "input": block.input
                                }
                            )

                        elif isinstance(block, ToolResultBlock):
                            # Check for special markers in tool result
                            if hasattr(block, 'content'):
                                content = block.content
                                if isinstance(content, str):
                                    # Check for ARTIFACT_CREATED marker
                                    if "ARTIFACT_CREATED:" in content:
                                        try:
                                            marker_start = content.index("ARTIFACT_CREATED:") + len("ARTIFACT_CREATED:")
                                            marker_end = content.index("|", marker_start)
                                            event_json = content[marker_start:marker_end]
                                            artifact_data = json.loads(event_json)
                                            # Yield artifact event via metadata
                                            yield StreamChunk(
                                                chunk_type="tool_use",
                                                metadata={"artifact_created": artifact_data}
                                            )
                                        except (ValueError, json.JSONDecodeError) as e:
                                            logger.warning(f"Failed to parse artifact event: {e}")

                                    # Check for DOCUMENTS_USED marker (HTTP mode)
                                    if "DOCUMENTS_USED:" in content:
                                        try:
                                            marker_start = content.index("DOCUMENTS_USED:") + len("DOCUMENTS_USED:")
                                            marker_end = content.index("|", marker_start)
                                            docs_json = content[marker_start:marker_end]
                                            docs = json.loads(docs_json)
                                            # Append to local documents_used list
                                            for doc in docs:
                                                if not any(d['id'] == doc['id'] for d in documents_used):
                                                    documents_used.append(doc)
                                        except (ValueError, json.JSONDecodeError) as e:
                                            logger.warning(f"Failed to parse documents_used: {e}")

                # ResultMessage: Final result with usage
                elif isinstance(message, ResultMessage):
                    usage_data = {"input_tokens": 0, "output_tokens": 0}
                    if hasattr(message, 'usage') and message.usage:
                        usage_data = {
                            "input_tokens": getattr(message.usage, 'input_tokens', 0),
                            "output_tokens": getattr(message.usage, 'output_tokens', 0)
                        }

                    # Get documents_used from ContextVar (for in-process MCP)
                    try:
                        contextvar_docs = _documents_used_context.get()
                        for doc in contextvar_docs:
                            if not any(d['id'] == doc['id'] for d in documents_used):
                                documents_used.append(doc)
                    except LookupError:
                        pass

                    # Yield completion with usage and source attribution
                    yield StreamChunk(
                        chunk_type="complete",
                        usage=usage_data,
                        metadata={"documents_used": documents_used}
                    )
                    return

            # If no ResultMessage received, yield completion anyway
            logger.warning("No ResultMessage received from SDK query")
            yield StreamChunk(
                chunk_type="complete",
                usage={"input_tokens": 0, "output_tokens": 0},
                metadata={"documents_used": documents_used}
            )

        except Exception as e:
            logger.error(f"Agent SDK error (turn {turn_count}): {e}", exc_info=True)
            yield StreamChunk(
                chunk_type="error",
                error=f"Agent SDK error (turn {turn_count}): {str(e)}"
            )

        finally:
            # Cleanup: Unregister session if using HTTP transport
            # (Not needed for POC since we're using ContextVars)
            pass
