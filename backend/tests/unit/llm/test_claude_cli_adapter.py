"""Unit tests for ClaudeCLIAdapter.

Tests verify adapter initialization, subprocess lifecycle management,
event translation, and error handling without making real subprocess calls.
Mocks asyncio.create_subprocess_exec and shutil.which for isolated testing.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import unittest.mock

from app.services.llm.claude_cli_adapter import ClaudeCLIAdapter, DEFAULT_MODEL
from app.services.llm.base import LLMProvider, StreamChunk
from app.services.llm import LLMFactory


# ============================================================================
# Mock Helper Functions
# ============================================================================

async def make_stdout_lines(lines):
    """Create async iterator from list of JSON strings."""
    for line in lines:
        yield (line + "\n").encode("utf-8")


def make_mock_process(stdout_lines, returncode=0, stderr_output=b""):
    """Create mock subprocess process with controllable stdout/stderr/stdin.

    Args:
        stdout_lines: List of JSON strings to yield from stdout
        returncode: Process exit code
        stderr_output: Bytes to return from stderr.read()

    Returns:
        Mock process object with async stdout iterator and stdin pipe
    """
    process = MagicMock()
    process.stdout = make_stdout_lines(stdout_lines)

    # Mock stderr
    stderr_mock = AsyncMock()
    stderr_mock.read = AsyncMock(return_value=stderr_output)
    process.stderr = stderr_mock

    # Mock stdin (prompt delivered via stdin pipe)
    stdin_mock = MagicMock()
    stdin_mock.write = MagicMock()
    stdin_mock.drain = AsyncMock()
    stdin_mock.close = MagicMock()
    stdin_mock.wait_closed = AsyncMock()
    process.stdin = stdin_mock

    # Mock process control
    process.returncode = returncode
    process.wait = AsyncMock(return_value=returncode)
    process.terminate = MagicMock()
    process.kill = MagicMock()

    return process


# ============================================================================
# Test Classes
# ============================================================================

class TestClaudeCLIAdapterInit:
    """Tests for ClaudeCLIAdapter initialization."""

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_initializes_with_api_key(self, mock_which):
        """API key is stored in adapter instance."""
        adapter = ClaudeCLIAdapter(api_key="test-api-key")

        assert adapter._api_key == "test-api-key"

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_uses_default_model(self, mock_which):
        """DEFAULT_MODEL is used when no model specified."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.model == DEFAULT_MODEL
        assert adapter.model == "claude-sonnet-4-5-20250929"

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_uses_custom_model(self, mock_which):
        """Custom model parameter is respected."""
        adapter = ClaudeCLIAdapter(
            api_key="test-key",
            model="claude-opus-4-20250514"
        )

        assert adapter.model == "claude-opus-4-20250514"

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_provider_returns_claude_code_cli(self, mock_which):
        """Provider property returns LLMProvider.CLAUDE_CODE_CLI."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.provider == LLMProvider.CLAUDE_CODE_CLI
        assert adapter.provider.value == "claude-code-cli"

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value=None)
    def test_raises_runtime_error_when_cli_not_found(self, mock_which):
        """Raises RuntimeError with install instructions when CLI not in PATH."""
        with pytest.raises(RuntimeError, match="Claude Code CLI not found"):
            ClaudeCLIAdapter(api_key="test-key")

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_stores_cli_path(self, mock_which):
        """CLI path is stored from shutil.which result."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.cli_path == '/usr/bin/claude'
        mock_which.assert_called_once_with("claude")

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_is_agent_provider_true(self, mock_which):
        """Adapter has is_agent_provider=True for AIService routing."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        assert adapter.is_agent_provider is True

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_has_set_context_method(self, mock_which):
        """Adapter has set_context method for request-scoped context."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        mock_db = MagicMock()

        adapter.set_context(mock_db, "proj-123", "thread-456")

        assert adapter.db is mock_db
        assert adapter.project_id == "proj-123"
        assert adapter.thread_id == "thread-456"


class TestClaudeCLIAdapterEventTranslation:
    """Tests for _translate_event method (actual CLI stream-json format)."""

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_translates_assistant_text_content(self, mock_which):
        """Assistant message with text content translates to text StreamChunk."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Hello world"}
                ]
            }
        }

        chunk = adapter._translate_event(event)

        assert chunk is not None
        assert chunk.chunk_type == "text"
        assert chunk.content == "Hello world"

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_translates_assistant_multi_text_blocks(self, mock_which):
        """Multiple text blocks are concatenated into single text chunk."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Hello "},
                    {"type": "text", "text": "world"}
                ]
            }
        }

        chunk = adapter._translate_event(event)

        assert chunk is not None
        assert chunk.chunk_type == "text"
        assert chunk.content == "Hello world"

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_translates_assistant_tool_use(self, mock_which):
        """Assistant message with tool_use translates to tool_use StreamChunk."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_123",
                        "name": "save_artifact",
                        "input": {"title": "BRD"}
                    }
                ]
            }
        }

        chunk = adapter._translate_event(event)

        assert chunk is not None
        assert chunk.chunk_type == "tool_use"
        assert chunk.tool_call["id"] == "tool_123"
        assert chunk.tool_call["name"] == "save_artifact"
        assert chunk.tool_call["input"] == {"title": "BRD"}

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_translates_result_event(self, mock_which):
        """Result event translates to complete StreamChunk with usage."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "result",
            "subtype": "success",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 200
            }
        }

        chunk = adapter._translate_event(event)

        assert chunk is not None
        assert chunk.chunk_type == "complete"
        assert chunk.usage["input_tokens"] == 100
        assert chunk.usage["output_tokens"] == 200

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_translates_error_event(self, mock_which):
        """Error event translates to error StreamChunk."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "error",
            "message": "Rate limited"
        }

        chunk = adapter._translate_event(event)

        assert chunk is not None
        assert chunk.chunk_type == "error"
        assert chunk.error == "Rate limited"

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_returns_none_for_unknown_event(self, mock_which):
        """Unknown event type returns None."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {"type": "unknown_type"}

        chunk = adapter._translate_event(event)

        assert chunk is None

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_system_events_return_none(self, mock_which):
        """System events (init, hooks) are silently ignored."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "system",
            "subtype": "init",
            "session_id": "abc123"
        }

        chunk = adapter._translate_event(event)

        assert chunk is None

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_use_search_documents_metadata(self, mock_which):
        """search_documents tool use includes tool_status metadata."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_456",
                        "name": "mcp__ba__search_documents",
                        "input": {"query": "test"}
                    }
                ]
            }
        }

        chunk = adapter._translate_event(event)

        assert chunk is not None
        assert chunk.metadata is not None
        assert chunk.metadata["tool_status"] == "Searching project documents..."

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_use_save_artifact_metadata(self, mock_which):
        """save_artifact tool use includes tool_status metadata."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_789",
                        "name": "mcp__ba__save_artifact",
                        "input": {"title": "Doc"}
                    }
                ]
            }
        }

        chunk = adapter._translate_event(event)

        assert chunk is not None
        assert chunk.metadata is not None
        assert chunk.metadata["tool_status"] == "Generating artifact..."


class TestClaudeCLIAdapterStreamChat:
    """Tests for stream_chat method."""

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_yields_text_chunks(self, mock_which, mock_subprocess,
                                                   mock_db_ctx, mock_proj_ctx,
                                                   mock_thread_ctx, mock_docs_ctx):
        """stream_chat yields text chunks from assistant messages."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock process with actual CLI format: system init, assistant message, result
        stdout_lines = [
            '{"type": "system", "subtype": "init", "session_id": "test-123"}',
            '{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello world"}]}}',
            '{"type": "result", "subtype": "success", "usage": {"input_tokens": 10, "output_tokens": 5}, "result": "Hello world"}'
        ]
        mock_process = make_mock_process(stdout_lines, returncode=0)
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify text chunk from assistant message
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        assert len(text_chunks) == 1
        assert text_chunks[0].content == "Hello world"

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_yields_complete_chunk(self, mock_which, mock_subprocess,
                                                      mock_db_ctx, mock_proj_ctx,
                                                      mock_thread_ctx, mock_docs_ctx):
        """stream_chat yields complete chunk with usage from result event."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock process with result event
        stdout_lines = [
            '{"type": "result", "subtype": "success", "usage": {"input_tokens": 100, "output_tokens": 50}}'
        ]
        mock_process = make_mock_process(stdout_lines, returncode=0)
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify complete chunk
        complete_chunks = [c for c in chunks if c.chunk_type == "complete"]
        assert len(complete_chunks) == 1
        assert complete_chunks[0].usage["input_tokens"] == 100
        assert complete_chunks[0].usage["output_tokens"] == 50

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_yields_error_on_process_failure(self, mock_which, mock_subprocess,
                                                                mock_db_ctx, mock_proj_ctx,
                                                                mock_thread_ctx, mock_docs_ctx):
        """stream_chat yields error chunk when subprocess fails."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock process with non-zero exit code
        mock_process = make_mock_process(
            stdout_lines=[],
            returncode=1,
            stderr_output=b"CLI error: rate limited"
        )
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify error chunk
        error_chunks = [c for c in chunks if c.chunk_type == "error"]
        assert len(error_chunks) == 1
        assert "exit 1" in error_chunks[0].error
        assert "rate limited" in error_chunks[0].error

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_yields_error_when_context_not_set(self, mock_which):
        """stream_chat yields error when context not set before calling."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        # Don't call set_context()

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify error chunk
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "error"
        assert "context not set" in chunks[0].error.lower()

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_skips_empty_lines(self, mock_which, mock_subprocess,
                                                  mock_db_ctx, mock_proj_ctx,
                                                  mock_thread_ctx, mock_docs_ctx):
        """stream_chat skips empty lines in stdout."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Include empty lines between actual CLI events
        async def stdout_with_empty():
            yield b'{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}}\n'
            yield b'\n'
            yield b'{"type": "assistant", "message": {"content": [{"type": "text", "text": " world"}]}}\n'

        mock_process = MagicMock()
        mock_process.stdout = stdout_with_empty()
        mock_process.returncode = 0
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.stderr = AsyncMock()
        mock_process.stderr.read = AsyncMock(return_value=b"")
        stdin_mock = MagicMock()
        stdin_mock.write = MagicMock()
        stdin_mock.drain = AsyncMock()
        stdin_mock.close = MagicMock()
        stdin_mock.wait_closed = AsyncMock()
        mock_process.stdin = stdin_mock
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify only 2 text chunks (empty line skipped)
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        assert len(text_chunks) == 2

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_handles_json_decode_error(self, mock_which, mock_subprocess,
                                                          mock_db_ctx, mock_proj_ctx,
                                                          mock_thread_ctx, mock_docs_ctx):
        """stream_chat handles malformed JSON gracefully (logs warning, no crash)."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Include malformed JSON between valid CLI events
        stdout_lines = [
            '{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}}',
            'MALFORMED JSON{{{',
            '{"type": "assistant", "message": {"content": [{"type": "text", "text": " world"}]}}'
        ]
        mock_process = make_mock_process(stdout_lines, returncode=0)
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify malformed line was skipped but processing continued
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        assert len(text_chunks) == 2
        assert text_chunks[0].content == "Hello"
        assert text_chunks[1].content == " world"

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_spawns_subprocess_with_correct_args(self, mock_which, mock_subprocess,
                                                                     mock_db_ctx, mock_proj_ctx,
                                                                     mock_thread_ctx, mock_docs_ctx):
        """stream_chat spawns subprocess with correct CLI path and flags."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        mock_process = make_mock_process([], returncode=0)
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify subprocess call
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args

        # Check positional args (command) — prompt NOT in args (sent via stdin)
        assert call_args[0][0] == '/usr/bin/claude'
        assert '-p' in call_args[0]
        assert '--output-format' in call_args[0]
        assert 'stream-json' in call_args[0]
        assert '--verbose' in call_args[0]
        assert '--model' in call_args[0]
        assert 'claude-sonnet-4-5-20250929' in call_args[0]

        # Verify stdin pipe is configured (prompt delivered via stdin)
        call_kwargs = mock_subprocess.call_args[1]
        assert call_kwargs.get("stdin") == asyncio.subprocess.PIPE

        # Verify prompt was written to stdin
        mock_process.stdin.write.assert_called_once()
        written_bytes = mock_process.stdin.write.call_args[0][0]
        # [SYSTEM]: outer wrapper is preserved (combined_prompt outer wrapper, unchanged)
        assert b"[SYSTEM]:" in written_bytes
        # Inner message now uses Human: label (multi-turn format)
        assert b"Human:" in written_bytes

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_passes_api_key_in_env(self, mock_which, mock_subprocess,
                                                      mock_db_ctx, mock_proj_ctx,
                                                      mock_thread_ctx, mock_docs_ctx):
        """stream_chat passes ANTHROPIC_API_KEY in subprocess environment."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        mock_process = make_mock_process([], returncode=0)
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="secret-key-123")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify env contains API key
        call_kwargs = mock_subprocess.call_args[1]
        assert "env" in call_kwargs
        assert call_kwargs["env"]["ANTHROPIC_API_KEY"] == "secret-key-123"

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_stream_chat_sets_contextvars(self, mock_which, mock_subprocess,
                                                  mock_db_ctx, mock_proj_ctx,
                                                  mock_thread_ctx, mock_docs_ctx):
        """stream_chat sets ContextVars before spawning subprocess."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        mock_process = make_mock_process([], returncode=0)
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        mock_db = MagicMock()
        adapter.set_context(mock_db, "proj-123", "thread-456")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify ContextVars were set
        mock_db_ctx.set.assert_called_once_with(mock_db)
        mock_proj_ctx.set.assert_called_once_with("proj-123")
        mock_thread_ctx.set.assert_called_once_with("thread-456")
        mock_docs_ctx.set.assert_called_once_with([])


class TestClaudeCLIAdapterSubprocessCleanup:
    """Tests for subprocess cleanup in finally block."""

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_cleanup_terminates_running_process(self, mock_which, mock_subprocess,
                                                       mock_db_ctx, mock_proj_ctx,
                                                       mock_thread_ctx, mock_docs_ctx):
        """Cleanup terminates process still running after iteration."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock process that doesn't complete normally
        async def stdout_then_hang():
            yield b'{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}}\n'
            # Stream ends but process stays alive

        mock_process = MagicMock()
        mock_process.stdout = stdout_then_hang()
        mock_process.returncode = None  # Still running
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.stderr = AsyncMock()
        mock_process.stderr.read = AsyncMock(return_value=b"")
        stdin_mock = MagicMock()
        stdin_mock.write = MagicMock()
        stdin_mock.drain = AsyncMock()
        stdin_mock.close = MagicMock()
        stdin_mock.wait_closed = AsyncMock()
        mock_process.stdin = stdin_mock
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify terminate was called
        mock_process.terminate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.asyncio.wait_for')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_cleanup_kills_on_timeout(self, mock_which, mock_wait_for, mock_subprocess,
                                             mock_db_ctx, mock_proj_ctx,
                                             mock_thread_ctx, mock_docs_ctx):
        """Cleanup kills process if terminate doesn't work within timeout."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock wait_for to timeout
        mock_wait_for.side_effect = asyncio.TimeoutError()

        # Mock process that doesn't terminate gracefully
        async def stdout_then_hang():
            yield b'{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}}\n'

        mock_process = MagicMock()
        mock_process.stdout = stdout_then_hang()
        mock_process.returncode = None
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.stderr = AsyncMock()
        mock_process.stderr.read = AsyncMock(return_value=b"")
        stdin_mock = MagicMock()
        stdin_mock.write = MagicMock()
        stdin_mock.drain = AsyncMock()
        stdin_mock.close = MagicMock()
        stdin_mock.wait_closed = AsyncMock()
        mock_process.stdin = stdin_mock
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify kill was called after timeout
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_cleanup_not_called_when_process_completed(self, mock_which, mock_subprocess,
                                                              mock_db_ctx, mock_proj_ctx,
                                                              mock_thread_ctx, mock_docs_ctx):
        """Cleanup doesn't terminate process that completed normally."""
        # Mock ContextVar set operations
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Mock process that completes normally
        stdout_lines = [
            '{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}}'
        ]
        mock_process = make_mock_process(stdout_lines, returncode=0)
        mock_subprocess.return_value = mock_process

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Verify terminate NOT called (returncode was set)
        mock_process.terminate.assert_not_called()
        mock_process.kill.assert_not_called()


class TestClaudeCLIAdapterMessageConversion:
    """Tests for _convert_messages_to_prompt method."""

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_converts_string_content(self, mock_which):
        """Single user message with string content is correctly labeled with Human: prefix."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        # After fix: output is "Human: Hello, how are you?" (with role label)
        assert "Human: Hello, how are you?" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_converts_list_content(self, mock_which):
        """List content with text parts is extracted correctly with Human: label."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "First part."},
                    {"type": "text", "text": "Second part."}
                ]
            }
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "Human:" in prompt
        assert "First part." in prompt
        assert "Second part." in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_handles_empty_messages(self, mock_which):
        """Empty message list returns empty string."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        prompt = adapter._convert_messages_to_prompt([])

        assert prompt == ""

    # --- NEW TESTS (TEST-01: multi-turn conversation) ---

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_three_turn_conversation_has_all_messages(self, mock_which):
        """3-turn conversation includes all turns in output with correct labels."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "Human: Hello" in prompt
        assert "Assistant: Hi there" in prompt
        assert "Human: How are you?" in prompt
        assert prompt.count("---") == 2  # Two separators for three turns

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_ten_turn_conversation_preserves_all(self, mock_which):
        """10-turn conversation includes all turns (no truncation in formatter)."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = []
        for i in range(5):
            messages.append({"role": "user", "content": f"User message {i}"})
            messages.append({"role": "assistant", "content": f"Assistant message {i}"})

        prompt = adapter._convert_messages_to_prompt(messages)

        for i in range(5):
            assert f"User message {i}" in prompt
            assert f"Assistant message {i}" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_uses_human_assistant_labels(self, mock_which):
        """Role labels are Human:/Assistant: (Anthropic native format), not [USER]:/[ASSISTANT]:."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "Human:" in prompt
        assert "Assistant:" in prompt
        # Ensure NOT the old bracket format
        assert "[USER]:" not in prompt
        assert "[ASSISTANT]:" not in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_uses_triple_dash_separator(self, mock_which):
        """Turns are separated by '---' lines."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "---" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_single_message_no_separator(self, mock_which):
        """Single message produces no separator."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Just one message"},
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "---" not in prompt
        assert "Human: Just one message" in prompt

    # --- NEW TESTS (TEST-02: multi-part content) ---

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_use_blocks_replaced_with_annotation(self, mock_which):
        """tool_use blocks with search_documents are replaced with [searched documents]."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Search for docs"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me search."},
                    {"type": "tool_use", "id": "t1", "name": "search_documents",
                     "input": {"query": "test"}}
                ]
            },
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "[searched documents]" in prompt
        assert "Let me search." in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_generic_tool_use_annotation(self, mock_which):
        """Non-search tool_use blocks are replaced with [performed an action]."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Do something"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Sure."},
                    {"type": "tool_use", "id": "t2", "name": "save_artifact",
                     "input": {"title": "BRD"}}
                ]
            },
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "[performed an action]" in prompt
        assert "Sure." in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_use_only_assistant_messages_skipped(self, mock_which):
        """Assistant messages with only tool_use (no text) are skipped entirely."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Do something"},
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "save_artifact",
                     "input": {"title": "Doc"}}
                ]
            },
            {"role": "user", "content": "Thanks"},
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        # Tool-only assistant message should not appear
        assert "Assistant:" not in prompt
        assert "Human: Do something" in prompt
        assert "Human: Thanks" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_thinking_blocks_excluded(self, mock_which):
        """Thinking blocks in assistant messages are excluded from output."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "What is 2+2?"},
            {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "Let me reason step by step..."},
                    {"type": "text", "text": "The answer is 4."}
                ]
            },
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "The answer is 4." in prompt
        assert "Let me reason step by step..." not in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_result_user_messages_skipped(self, mock_which):
        """User messages containing only tool_result blocks are skipped (empty text)."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "Search"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Searching."},
                    {"type": "tool_use", "id": "t1", "name": "search_documents",
                     "input": {"query": "test"}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "t1",
                     "content": "Result: found 3 documents"}
                ]
            },
            {"role": "user", "content": "What did you find?"},
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        # Tool result message (3rd message) should be skipped — text is empty
        assert "Result: found 3 documents" not in prompt
        assert "Human: What did you find?" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_system_messages_excluded(self, mock_which):
        """System role messages are excluded from formatted output."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]

        prompt = adapter._convert_messages_to_prompt(messages)

        assert "You are helpful." not in prompt
        assert "Human: Hello" in prompt

    # --- NEW TESTS (TEST-03: BA flow regression) ---

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_ba_flow_uses_agent_service_not_cli_adapter(self, mock_which):
        """ClaudeCLIAdapter has is_agent_provider=True and doesn't reference agent_service patterns."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        # Verify the routing flag is set correctly
        assert adapter.is_agent_provider is True

        # Verify adapter is for CLI, not agent SDK
        from app.services.llm.base import LLMProvider
        assert adapter.provider == LLMProvider.CLAUDE_CODE_CLI

        # The adapter should have _convert_messages_to_prompt (not [USER]/[ASSISTANT] bracket format)
        messages = [{"role": "user", "content": "test"}]
        prompt = adapter._convert_messages_to_prompt(messages)

        # CLI adapter uses Human:/Assistant: (not [USER]:/[ASSISTANT]: which is agent_service pattern)
        assert "Human:" in prompt
        assert "[USER]:" not in prompt

    # --- NEW TESTS (CONV-03: role alternation warning) ---

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_warns_on_consecutive_same_role_messages(self, mock_which):
        """Consecutive same-role messages trigger a warning but are still included."""
        adapter = ClaudeCLIAdapter(api_key="test-key")

        messages = [
            {"role": "user", "content": "First question"},
            {"role": "user", "content": "Second question without assistant response"},
        ]

        with unittest.mock.patch(
            'app.services.llm.claude_cli_adapter.logger'
        ) as mock_logger:
            prompt = adapter._convert_messages_to_prompt(messages)

        # Warning should have been logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "alternation" in warning_call.lower() or "consecutive" in warning_call.lower()

        # Both messages still appear (warning, not error)
        assert "Human: First question" in prompt
        assert "Human: Second question without assistant response" in prompt


class TestClaudeCLIAdapterFactory:
    """Tests for LLMFactory integration with ClaudeCLIAdapter."""

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    @patch('app.services.llm.factory.settings')
    def test_factory_creates_adapter(self, mock_settings, mock_which):
        """LLMFactory.create('claude-code-cli') returns ClaudeCLIAdapter."""
        mock_settings.anthropic_api_key = "test-key"

        adapter = LLMFactory.create("claude-code-cli")

        assert isinstance(adapter, ClaudeCLIAdapter)
        assert adapter.provider == LLMProvider.CLAUDE_CODE_CLI

    @patch('app.services.llm.factory.settings')
    def test_factory_raises_without_api_key(self, mock_settings):
        """Factory raises ValueError when ANTHROPIC_API_KEY is not configured."""
        mock_settings.anthropic_api_key = None

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not configured"):
            LLMFactory.create("claude-code-cli")

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    @patch('app.services.llm.factory.settings')
    def test_factory_passes_custom_model(self, mock_settings, mock_which):
        """Factory passes custom model parameter to adapter."""
        mock_settings.anthropic_api_key = "test-key"

        adapter = LLMFactory.create("claude-code-cli", model="claude-opus-4-20250514")

        assert adapter.model == "claude-opus-4-20250514"
