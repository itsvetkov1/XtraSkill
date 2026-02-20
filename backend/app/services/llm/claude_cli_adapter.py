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
import time
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


def _build_cli_env() -> dict:
    """
    Build environment dictionary for Claude CLI subprocess.

    Filters out CLAUDECODE and CLAUDE_CODE_ENTRYPOINT to prevent
    nested session detection by the CLI binary.

    Returns:
        dict: Filtered environment suitable for CLI subprocess
    """
    return {k: v for k, v in os.environ.items()
            if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}


class ClaudeProcessPool:
    """
    Pre-warming pool for Claude CLI subprocesses.

    Maintains POOL_SIZE warm processes ready to accept prompts.
    Each process handles exactly one request (--print mode is single-shot).
    After a process exits naturally, the refill loop spawns a replacement.

    Latency improvement:
      Cold start (no pool): ~120-400ms (OS spawn + Node.js init + auth check)
      Warm acquire (pool):  <5ms (asyncio.Queue.get_nowait)
      Measured baseline:    See test_claude_process_pool.py

    Usage:
        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model='claude-sonnet-...')
        await pool.start()          # Pre-warm at app startup
        proc = await pool.acquire() # Get warm process for a request
        await pool.stop()           # Clean shutdown at app shutdown

    Anti-patterns:
        - Do NOT use --input-format stream-json (known bugs, Issue #5034)
        - Do NOT use --continue or --session-id (active bugs, incompatible with --print)
        - Do NOT block on queue.get() — use get_nowait() with cold fallback
        - Do NOT share processes across requests — each claude -p is single-shot
    """

    POOL_SIZE = 2       # Number of processes to keep warm (sufficient for single-user dev)
    REFILL_DELAY = 0.1  # Seconds between refill loop checks

    def __init__(self, cli_path: str, model: str):
        """
        Initialize pool without starting it.

        Args:
            cli_path: Absolute path to claude CLI binary
            model: Model identifier to pass with --model flag
        """
        self._cli_path = cli_path
        self._model = model
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=self.POOL_SIZE)
        self._running = False
        self._refill_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """
        Pre-warm POOL_SIZE processes and start background refill loop.

        Call at app startup (FastAPI lifespan). Processes are pre-started
        with stdin=PIPE, waiting to receive a prompt. If spawn fails, the
        slot is skipped (cold spawn will be used as fallback for requests).
        """
        self._running = True
        # Pre-spawn POOL_SIZE processes
        for _ in range(self.POOL_SIZE):
            proc = await self._spawn_warm_process()
            if proc:
                try:
                    self._queue.put_nowait(proc)
                except asyncio.QueueFull:
                    # Queue full (shouldn't happen during startup, but defensive)
                    proc.terminate()
                    await proc.wait()
        # Start background refill loop
        self._refill_task = asyncio.create_task(self._refill_loop())

    async def stop(self) -> None:
        """
        Cancel refill loop and terminate all remaining warm processes.

        Call at app shutdown (FastAPI lifespan). Pre-warmed processes that
        never received a prompt are cleaned up here to prevent zombie processes.
        """
        self._running = False
        if self._refill_task:
            self._refill_task.cancel()
            try:
                await self._refill_task
            except asyncio.CancelledError:
                pass
        # Drain queue and terminate remaining processes
        while not self._queue.empty():
            try:
                proc = self._queue.get_nowait()
                if proc.returncode is None:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        proc.kill()
                        await proc.wait()
            except asyncio.QueueEmpty:
                break

    async def acquire(self) -> asyncio.subprocess.Process:
        """
        Acquire a warm process from the pool.

        Tries queue.get_nowait() first (O(1), no spawn overhead). If the
        dequeued process is dead (returncode is not None), falls through to
        cold spawn. If pool is empty, falls through to cold spawn.

        Returns:
            asyncio.subprocess.Process: Warm or cold-spawned process ready
                                         to receive a prompt via stdin.
        """
        try:
            proc = self._queue.get_nowait()
            if proc.returncode is not None:
                # Process died unexpectedly while queued — fall back to cold spawn
                logger.warning("Pool process died while queued, falling back to cold spawn")
                return await self._cold_spawn()
            return proc
        except asyncio.QueueEmpty:
            # Pool exhausted — fall back to cold spawn transparently
            logger.warning("Process pool empty, falling back to cold spawn")
            return await self._cold_spawn()

    async def _spawn_warm_process(self) -> Optional[asyncio.subprocess.Process]:
        """
        Spawn one warm process and return it, or None on failure.

        The spawned process has stdin=PIPE and waits for a prompt.
        Returns None if spawn fails (logged as warning, not error).
        """
        try:
            env = _build_cli_env()
            return await asyncio.create_subprocess_exec(
                self._cli_path,
                '-p',
                '--output-format', 'stream-json',
                '--verbose',
                '--model', self._model,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                limit=1024 * 1024  # 1MB line buffer (same as stream_chat)
            )
        except Exception as e:
            logger.warning(f"Failed to pre-warm process: {e}")
            return None

    async def _cold_spawn(self) -> asyncio.subprocess.Process:
        """
        Spawn a process immediately (cold path fallback).

        Unlike _spawn_warm_process, raises on failure since this is
        on the critical path for a user request.
        """
        env = _build_cli_env()
        return await asyncio.create_subprocess_exec(
            self._cli_path,
            '-p',
            '--output-format', 'stream-json',
            '--verbose',
            '--model', self._model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            limit=1024 * 1024  # 1MB line buffer (same as stream_chat)
        )

    async def _refill_loop(self) -> None:
        """
        Background task that keeps the pool at POOL_SIZE.

        Checks every REFILL_DELAY seconds and spawns new processes
        until the queue is full again. Handles QueueFull by terminating
        any excess process.
        """
        while self._running:
            await asyncio.sleep(self.REFILL_DELAY)
            while self._running and self._queue.qsize() < self.POOL_SIZE:
                proc = await self._spawn_warm_process()
                if proc:
                    try:
                        self._queue.put_nowait(proc)
                    except asyncio.QueueFull:
                        # Queue was filled by another task between checks
                        proc.terminate()
                        await proc.wait()


# Module-level singleton for the process pool
_process_pool: Optional[ClaudeProcessPool] = None


def get_process_pool() -> Optional[ClaudeProcessPool]:
    """Return the module-level process pool singleton, or None if not initialized."""
    return _process_pool


async def init_process_pool(cli_path: str, model: str) -> ClaudeProcessPool:
    """
    Initialize and start the module-level process pool singleton.

    Args:
        cli_path: Absolute path to claude CLI binary
        model: Model identifier for pre-warmed processes

    Returns:
        ClaudeProcessPool: Started pool instance
    """
    global _process_pool
    pool = ClaudeProcessPool(cli_path=cli_path, model=model)
    await pool.start()
    _process_pool = pool
    return pool


async def shutdown_process_pool() -> None:
    """Stop and clear the module-level process pool singleton."""
    global _process_pool
    if _process_pool:
        await _process_pool.stop()
        _process_pool = None


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
        Convert full conversation history to multi-turn prompt string for CLI.

        Replaces POC implementation that only used the last user message.
        Now formats all user/assistant messages with role labels and separators
        so the CLI subprocess receives complete conversation context.

        Format:
          Human: [user text]

          ---

          Assistant: [assistant text]

          ---

          Human: [next user text]

        Rules:
        - Role labels: Human / Assistant (Anthropic native format)
        - Separator: '---' between turns
        - System messages: excluded
        - Empty assistant messages (tool_use only, no text): skipped
        - Multi-part content: text blocks kept; tool_use replaced with annotation;
          tool_result blocks (in user messages) skipped; thinking blocks excluded

        Args:
            messages: Full conversation history in standard format

        Returns:
            str: Multi-turn prompt text for CLI stdin
        """
        if not messages:
            return ""

        parts = []
        prev_label = None
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                label = "Human"
            elif role == "assistant":
                label = "Assistant"
            else:
                # Skip system messages and unknown roles
                continue

            # Warn on consecutive same-role messages (role alternation violation)
            if prev_label is not None and label == prev_label:
                logger.warning(
                    f"Role alternation violation: consecutive '{role}' messages detected. "
                    "This may cause unexpected CLI behavior."
                )

            text = self._extract_text_content(content)

            # Skip empty messages (e.g., tool_use-only assistant turns)
            if not text.strip():
                continue

            parts.append(f"{label}: {text}")
            prev_label = label

        return "\n\n---\n\n".join(parts)

    def _extract_text_content(self, content: Any) -> str:
        """
        Extract readable text from message content.

        Handles string content directly.
        For list content, processes each block:
        - text blocks: included as-is
        - thinking blocks: excluded (internal reasoning, not final response)
        - tool_use blocks: replaced with brief annotation (only when text blocks also present)
        - tool_result blocks: skipped (part of user messages, not conversation text)

        If a message consists ONLY of tool_use blocks (no text blocks), the result
        will be empty — the caller's empty-check will then skip the entire message.
        This covers silent tool-only assistant turns (e.g., save_artifact without text).

        Args:
            content: Message content (str or list of content blocks)

        Returns:
            str: Extracted text, empty string if nothing readable
        """
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            tool_annotations = []
            has_text_blocks = False

            for part in content:
                if not isinstance(part, dict):
                    continue
                block_type = part.get("type", "")
                if block_type == "text":
                    text_parts.append(part.get("text", ""))
                    has_text_blocks = True
                elif block_type == "thinking":
                    pass  # Exclude internal reasoning
                elif block_type == "tool_use":
                    tool_name = part.get("name", "")
                    if "search_documents" in tool_name:
                        tool_annotations.append("[searched documents]")
                    else:
                        tool_annotations.append("[performed an action]")
                elif block_type == "tool_result":
                    pass  # Skip tool results (can be very long, not conversation text)

            # Only include tool annotations when text blocks are also present.
            # Tool-use-only messages (no text) return empty → caller skips them.
            if has_text_blocks:
                return "\n".join(text_parts + tool_annotations)
            return "\n".join(text_parts)

        return str(content)

    def _translate_event(self, event: Dict[str, Any]) -> Optional[StreamChunk]:
        """
        Translate CLI JSON event to StreamChunk format.

        Actual CLI stream-json output format:
        - type: "system" (init, hooks) -> ignored
        - type: "assistant" with message.content blocks -> text/tool_use StreamChunk
        - type: "result" with usage -> StreamChunk(chunk_type="complete")

        Args:
            event: Parsed JSON event from CLI stdout

        Returns:
            StreamChunk or None if event type not handled
        """
        event_type = event.get("type")

        # Assistant message: contains full response content blocks
        # Format: {"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}, ...]}}
        if event_type == "assistant":
            message = event.get("message", {})
            content_blocks = message.get("content", [])

            # Collect all text blocks into a single text chunk
            text_parts = []
            for block in content_blocks:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    # Emit tool use chunk (return first tool_use found)
                    chunk = StreamChunk(
                        chunk_type="tool_use",
                        tool_call={
                            "id": block.get("id"),
                            "name": block.get("name"),
                            "input": block.get("input")
                        }
                    )
                    tool_name = block.get("name", "")
                    if "search_documents" in tool_name:
                        chunk.metadata = {"tool_status": "Searching project documents..."}
                    elif "save_artifact" in tool_name:
                        chunk.metadata = {"tool_status": "Generating artifact..."}
                    return chunk

            if text_parts:
                return StreamChunk(
                    chunk_type="text",
                    content="".join(text_parts)
                )

        # Result: final completion with usage and cost
        # Format: {"type": "result", "subtype": "success", "usage": {...}, "result": "..."}
        elif event_type == "result":
            usage = event.get("usage", {})
            return StreamChunk(
                chunk_type="complete",
                usage={
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0)
                }
            )

        # System events (init, hooks) — skip silently
        elif event_type == "system":
            return None

        # Error events
        elif event_type == "error":
            return StreamChunk(
                chunk_type="error",
                error=event.get("message", "Unknown CLI error")
            )

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

        Process acquisition:
        - If process pool is initialized: acquires warm process from pool
          (pool.acquire latency <5ms vs cold spawn ~120-400ms).
        - If pool is not initialized: falls back to cold spawn directly.
        Latency is logged on every acquisition via time.perf_counter().

        Args:
            messages: Conversation history
            system_prompt: System instructions (includes MCP tool descriptions)
            tools: Ignored (CLI uses tool descriptions from system prompt)
            max_tokens: Ignored (CLI uses model defaults)

        Yields:
            StreamChunk: Normalized streaming events
        """
        if not self.db or not self.thread_id:
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

            # Prepend system prompt to prompt text with clear delimiter.
            # This allows CLI to interpret tool descriptions from the system prompt.
            # NOTE: For multi-turn history, prompt_text now contains the full conversation
            # with Human:/Assistant: role labels and '---' separators between turns.
            # The outer [USER]: wrapper is kept for backward compatibility — the CLI
            # receives the full conversation history after the [SYSTEM]: marker.
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

            # Acquire process: prefer warm pool over cold spawn
            # Measure acquisition latency via perf_counter (PERF-01)
            pool = get_process_pool()
            acquire_start = time.perf_counter()

            if pool is not None:
                process = await pool.acquire()
                acquire_ms = (time.perf_counter() - acquire_start) * 1000
                logger.info(
                    f"Process acquired from pool in {acquire_ms:.1f}ms "
                    f"(queue_size={pool._queue.qsize()})"
                )
            else:
                # Pool not initialized — fall back to cold spawn directly
                logger.warning("Process pool not initialized, using cold spawn")
                env = _build_cli_env()
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    limit=1024 * 1024  # 1MB line buffer (default 64KB too small for BRDs)
                )
                acquire_ms = (time.perf_counter() - acquire_start) * 1000
                logger.info(f"Process cold-spawned in {acquire_ms:.1f}ms")

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
