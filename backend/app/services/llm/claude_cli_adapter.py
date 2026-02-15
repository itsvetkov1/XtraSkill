"""
Claude Code CLI Subprocess Adapter.

Implements LLMAdapter interface for Claude Code CLI subprocess integration.
Spawns Claude Code CLI as an async subprocess, parses line-delimited JSON from stdout,
and translates events to StreamChunk format with robust process lifecycle management.

Architecture note:
This adapter spawns Claude Code CLI as a subprocess with --output-format stream-json,
parses line-delimited JSON from stdout, and translates events to StreamChunk format.
Process lifecycle management (cleanup, zombie prevention) is critical.

Known limitations (POC scope):
- Partial message streaming not supported; only complete events are emitted
- MCP tools communicated via system prompt (no .mcp.json file or MCP server config)
- No hard timeout on subprocess (per locked decision: no request timeout for POC)
"""
import asyncio
import json
import logging
import os
import shutil
from typing import AsyncGenerator, Dict, Any, List, Optional

from .base import LLMAdapter, LLMProvider, StreamChunk
from app.services.mcp_tools import (
    _db_context,
    _project_id_context,
    _thread_id_context,
    _documents_used_context,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class ClaudeCLIAdapter(LLMAdapter):
    """
    Claude Code CLI subprocess adapter.

    Spawns CLI process with --output-format stream-json, parses
    line-delimited JSON output, translates to StreamChunk format.

    Uses shared MCP tools via system prompt for search_documents and
    save_artifact (POC approach).

    IMPORTANT: This adapter handles tool execution internally via CLI's
    agent loop. AIService must NOT execute tools manually.
    """

    # Signal to AIService that this adapter handles tools internally
    is_agent_provider = True

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize Claude CLI adapter.

        Args:
            api_key: Anthropic API key (passed via environment to CLI)
            model: Model to use (default: claude-sonnet-4-5-20250929)

        Raises:
            RuntimeError: If claude CLI not found in PATH
        """
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL

        # Verify CLI available
        cli_path = shutil.which("claude")
        if not cli_path:
            raise RuntimeError(
                "Claude Code CLI not found in PATH. "
                "Install claude-agent-sdk (v0.1.35+) which bundles the CLI, "
                "or install Claude Code separately."
            )
        self.cli_path = cli_path
        logger.info(f"Claude CLI found at: {cli_path}")

        # Context will be set before each stream_chat call
        self.db = None
        self.project_id = None
        self.thread_id = None

    @property
    def provider(self) -> LLMProvider:
        """Return the provider identifier."""
        return LLMProvider.CLAUDE_CODE_CLI

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
        Convert message history to prompt string for CLI.

        CLI accepts prompt via -p flag, not structured messages.
        For POC: Extract last user message.

        Args:
            messages: Conversation history in standard format

        Returns:
            str: Prompt text for CLI
        """
        if not messages:
            return ""

        # For POC: Use last user message
        # Production: Format multi-turn conversation with role labels
        last_message = messages[-1]
        content = last_message.get("content", "")

        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle multi-part content (text + images)
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            return "\n".join(text_parts)

        return str(content)

    def _translate_event(self, event: Dict[str, Any]) -> Optional[StreamChunk]:
        """
        Translate CLI JSON event to StreamChunk format.

        Maps CLI event types to StreamChunk:
        - type: "stream_event" with content_block_delta -> StreamChunk(chunk_type="text")
        - type: "assistant_message" with tool_use blocks -> StreamChunk(chunk_type="tool_use")
        - type: "result" -> StreamChunk(chunk_type="complete")
        - type: "error" -> StreamChunk(chunk_type="error")

        Args:
            event: Parsed JSON event from CLI stdout

        Returns:
            StreamChunk or None if event type not handled
        """
        event_type = event.get("type")

        # StreamEvent: Incremental text deltas
        if event_type == "stream_event":
            inner_event = event.get("event", {})
            if inner_event.get("type") == "content_block_delta":
                delta = inner_event.get("delta", {})
                if delta.get("type") == "text_delta":
                    return StreamChunk(
                        chunk_type="text",
                        content=delta.get("text", "")
                    )

        # AssistantMessage: Tool use blocks
        elif event_type == "assistant_message":
            content = event.get("content", [])
            for block in content:
                if block.get("type") == "tool_use":
                    # Emit tool use chunk
                    chunk = StreamChunk(
                        chunk_type="tool_use",
                        tool_call={
                            "id": block.get("id"),
                            "name": block.get("name"),
                            "input": block.get("input")
                        }
                    )

                    # Add tool status metadata for user-friendly indicators
                    tool_name = block.get("name", "")
                    if "search_documents" in tool_name:
                        chunk.metadata = {"tool_status": "Searching project documents..."}
                    elif "save_artifact" in tool_name:
                        chunk.metadata = {"tool_status": "Generating artifact..."}

                    return chunk

        # ResultMessage: Final completion with usage
        elif event_type == "result":
            usage = event.get("usage", {})
            return StreamChunk(
                chunk_type="complete",
                usage={
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0)
                }
            )

        # Error events
        elif event_type == "error":
            return StreamChunk(
                chunk_type="error",
                error=event.get("message", "Unknown CLI error")
            )

        # Log unhandled event types for debugging
        logger.debug(f"Unhandled CLI event type: {event_type}")
        return None

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response by spawning CLI subprocess.

        Spawns `claude -p --output-format stream-json`, parses JSON
        events from stdout, translates to StreamChunk format.

        The CLI's agent loop handles tool execution autonomously by reading
        tool descriptions from the system prompt. No .mcp.json file or MCP
        server configuration is needed for POC.

        Args:
            messages: Conversation history
            system_prompt: System instructions (includes MCP tool descriptions)
            tools: Ignored (CLI uses tool descriptions from system prompt)
            max_tokens: Ignored (CLI uses model defaults)

        Yields:
            StreamChunk: Normalized streaming events
        """
        if not self.db or not self.project_id or not self.thread_id:
            yield StreamChunk(
                chunk_type="error",
                error="Adapter context not set. Call set_context() before stream_chat()."
            )
            return

        # Set ContextVars for MCP tools (POC approach)
        _db_context.set(self.db)
        _project_id_context.set(self.project_id)
        _thread_id_context.set(self.thread_id)
        _documents_used_context.set([])  # Initialize for source attribution

        process = None
        received_result = False  # Track if CLI sent result event

        try:
            # Build prompt from messages
            prompt_text = self._convert_messages_to_prompt(messages)

            # Prepend system prompt to prompt text with clear delimiter
            # This allows CLI to interpret tool descriptions from the system prompt
            combined_prompt = f"[SYSTEM]: {system_prompt}\n\n[USER]: {prompt_text}"

            # Build CLI command
            # NOTE: Do NOT pass --system-prompt flag, use combined prompt instead
            # NOTE: Do NOT pass --include-partial-messages (excluded from POC scope)
            # NOTE: Prompt passed via stdin to avoid Windows 8,191 char command line limit
            cmd = [
                self.cli_path,
                "-p",  # Print mode (non-interactive, reads prompt from stdin)
                "--output-format", "stream-json",
                "--verbose",
                "--model", self.model,
            ]

            # Environment with API key
            env = {**os.environ, "ANTHROPIC_API_KEY": self._api_key}

            # Create subprocess with stdin pipe for prompt delivery
            logger.info(f"Spawning CLI subprocess: {self.cli_path} -p ...")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Write prompt via stdin and close (avoids Windows cmd line length limit)
            process.stdin.write(combined_prompt.encode('utf-8'))
            await process.stdin.drain()
            process.stdin.close()
            await process.stdin.wait_closed()

            # Stream output line-by-line
            turn_count = 0
            async for line in process.stdout:
                decoded = line.decode('utf-8').strip()
                if not decoded:
                    continue

                try:
                    event = json.loads(decoded)

                    # Track turns for debugging
                    if event.get("type") == "assistant_message":
                        turn_count += 1

                    # Track if we received result event
                    if event.get("type") == "result":
                        received_result = True

                    # Translate and yield
                    chunk = self._translate_event(event)
                    if chunk:
                        yield chunk

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON: {decoded[:100]} - {e}")

            # Wait for process completion
            returncode = await process.wait()

            # Check for errors
            if returncode != 0:
                stderr_output = await process.stderr.read()
                error_msg = stderr_output.decode('utf-8') if stderr_output else "Unknown error"
                logger.error(f"CLI subprocess failed (exit {returncode}): {error_msg}")
                yield StreamChunk(
                    chunk_type="error",
                    error=f"CLI subprocess failed (exit {returncode}): {error_msg}"
                )
                return

            # If no result event received from CLI, yield fallback completion
            if not received_result:
                # Get documents_used from ContextVar for source attribution
                documents_used = []
                try:
                    documents_used = _documents_used_context.get()
                except LookupError:
                    pass

                yield StreamChunk(
                    chunk_type="complete",
                    usage={"input_tokens": 0, "output_tokens": 0},
                    metadata={"documents_used": documents_used}
                )

        except Exception as e:
            logger.error(f"CLI subprocess error (turn {turn_count if 'turn_count' in locals() else 0}): {e}", exc_info=True)
            yield StreamChunk(
                chunk_type="error",
                error=f"CLI error: {str(e)}"
            )

        finally:
            # CRITICAL: Cleanup to prevent zombie processes
            if process and process.returncode is None:
                logger.warning("CLI subprocess still running, terminating...")
                process.terminate()
                try:
                    # Wait for graceful shutdown with timeout
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                    logger.info("CLI subprocess terminated gracefully")
                except asyncio.TimeoutError:
                    # Force kill if graceful termination fails
                    logger.warning("CLI subprocess did not terminate, killing...")
                    process.kill()
                    await process.wait()
                    logger.info("CLI subprocess killed")
