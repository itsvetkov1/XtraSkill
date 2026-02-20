"""Unit tests for ClaudeProcessPool.

Tests verify pool pre-warming, warm acquire, cold fallback, dead process
handling, start/stop lifecycle, latency logging, and documentation.

Test baseline: 49 existing + 1 pre-existing fail in test_claude_cli_adapter.py
New tests in this file: 8
Expected final state: 57 passing, 1 pre-existing fail.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
import unittest.mock

from app.services.llm.claude_cli_adapter import (
    ClaudeProcessPool,
    ClaudeCLIAdapter,
    DEFAULT_MODEL,
    get_process_pool,
    init_process_pool,
    shutdown_process_pool,
)
from app.services.llm.base import StreamChunk


# ============================================================================
# Helper Functions
# ============================================================================

def make_mock_process(returncode=None):
    """
    Create a mock subprocess process.

    Args:
        returncode: Process exit code (None = still running, int = exited)

    Returns:
        MagicMock: Mock process with terminate/wait/kill attributes
    """
    proc = MagicMock()
    proc.returncode = returncode
    proc.terminate = MagicMock()
    proc.kill = MagicMock()
    proc.wait = AsyncMock(return_value=returncode if returncode is not None else 0)
    proc.stdin = MagicMock()
    proc.stdin.write = MagicMock()
    proc.stdin.drain = AsyncMock()
    proc.stdin.close = MagicMock()
    proc.stdin.wait_closed = AsyncMock()
    proc.stdout = MagicMock()
    proc.stderr = AsyncMock()
    proc.stderr.read = AsyncMock(return_value=b"")
    return proc


async def make_async_stdout(lines):
    """Async generator that yields encoded lines from a list."""
    for line in lines:
        yield (line + "\n").encode("utf-8")


# ============================================================================
# Pool Tests
# ============================================================================

class TestClaudeProcessPool:
    """Tests for ClaudeProcessPool class lifecycle and acquire behavior."""

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    async def test_warm_acquire_returns_queued_process(self, mock_exec):
        """
        PERF-02: Warm pool acquire returns pre-queued process without spawning.

        Pre-fill the queue with a live mock process. Call acquire().
        Assert the mock process is returned and create_subprocess_exec was NOT called.
        """
        alive_proc = make_mock_process(returncode=None)

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model=DEFAULT_MODEL)
        await pool._queue.put(alive_proc)

        result = await pool.acquire()

        assert result is alive_proc
        mock_exec.assert_not_called()  # No cold spawn — warm process was used

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    async def test_cold_fallback_when_pool_empty(self, mock_exec):
        """
        PERF-02: When pool is empty, acquire falls back to cold spawn transparently.

        Leave queue empty. Assert create_subprocess_exec is called once (cold spawn).
        """
        cold_proc = make_mock_process(returncode=None)
        mock_exec.return_value = cold_proc

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model=DEFAULT_MODEL)
        # Pool queue intentionally left empty

        result = await pool.acquire()

        mock_exec.assert_called_once()  # Cold spawn triggered
        assert result is cold_proc

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    async def test_dead_process_triggers_cold_spawn(self, mock_exec):
        """
        PERF-02: Dead process in pool (returncode != None) triggers cold spawn.

        Pool health check at acquire time detects dead process and falls back
        to cold spawn instead of returning the stale process.
        """
        dead_proc = make_mock_process(returncode=1)  # Process exited with error
        cold_proc = make_mock_process(returncode=None)
        mock_exec.return_value = cold_proc

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model=DEFAULT_MODEL)
        await pool._queue.put(dead_proc)

        result = await pool.acquire()

        # Cold spawn was triggered for the dead process
        mock_exec.assert_called_once()
        assert result is cold_proc
        assert result is not dead_proc

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    async def test_start_prewarms_pool(self, mock_exec):
        """
        PERF-02: pool.start() pre-warms POOL_SIZE processes and fills the queue.

        Mock create_subprocess_exec to return alive processes. After start(),
        queue should have POOL_SIZE items ready.
        """
        # Create POOL_SIZE mock processes for pre-warming
        warm_procs = [make_mock_process(returncode=None) for _ in range(ClaudeProcessPool.POOL_SIZE)]
        mock_exec.side_effect = warm_procs

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model=DEFAULT_MODEL)
        await pool.start()

        # Cancel the refill task to stop background activity
        if pool._refill_task:
            pool._refill_task.cancel()
            try:
                await pool._refill_task
            except asyncio.CancelledError:
                pass

        # Queue should contain POOL_SIZE warm processes
        assert pool._queue.qsize() == ClaudeProcessPool.POOL_SIZE
        assert mock_exec.call_count == ClaudeProcessPool.POOL_SIZE

    @pytest.mark.asyncio
    async def test_stop_terminates_remaining_processes(self):
        """
        PERF-02: pool.stop() terminates all processes remaining in the queue.

        Put 2 mock processes in queue. Call pool.stop(). Assert terminate() was
        called on both to prevent zombie processes.
        """
        proc1 = make_mock_process(returncode=None)
        proc2 = make_mock_process(returncode=None)

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model=DEFAULT_MODEL)
        pool._running = True
        await pool._queue.put(proc1)
        await pool._queue.put(proc2)

        await pool.stop()

        # Both processes should have been terminated
        proc1.terminate.assert_called_once()
        proc2.terminate.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.get_process_pool')
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_acquire_latency_logged(
        self, mock_which, mock_get_pool,
        mock_db_ctx, mock_proj_ctx, mock_thread_ctx, mock_docs_ctx
    ):
        """
        PERF-01: stream_chat() logs acquire latency with 'Process acquired' and 'ms'.

        Patch logger and pool. Call stream_chat() with pool initialized.
        Assert log message contains 'Process acquired' and 'ms'.
        """
        # Set up mock ContextVars
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        # Set up a mock pool with a live process
        warm_proc = make_mock_process(returncode=None)
        warm_proc.stdout = make_async_stdout([
            '{"type": "result", "subtype": "success", "usage": {"input_tokens": 5, "output_tokens": 3}}'
        ])

        mock_pool = MagicMock()
        mock_pool.acquire = AsyncMock(return_value=warm_proc)
        mock_pool._queue = MagicMock()
        mock_pool._queue.qsize = MagicMock(return_value=1)
        mock_get_pool.return_value = mock_pool

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        with unittest.mock.patch('app.services.llm.claude_cli_adapter.logger') as mock_logger:
            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

        # Find the "Process acquired" log message
        info_calls = [str(c) for c in mock_logger.info.call_args_list]
        acquire_logs = [c for c in info_calls if "Process acquired" in c]
        assert len(acquire_logs) > 0, f"Expected 'Process acquired' log, got: {info_calls}"
        assert any("ms" in c for c in acquire_logs), f"Expected 'ms' in log, got: {acquire_logs}"

    @pytest.mark.asyncio
    @patch('app.services.llm.claude_cli_adapter._documents_used_context')
    @patch('app.services.llm.claude_cli_adapter._thread_id_context')
    @patch('app.services.llm.claude_cli_adapter._project_id_context')
    @patch('app.services.llm.claude_cli_adapter._db_context')
    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @patch('app.services.llm.claude_cli_adapter.get_process_pool', return_value=None)
    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    async def test_pool_not_initialized_falls_back_to_cold_spawn(
        self, mock_which, mock_get_pool, mock_exec,
        mock_db_ctx, mock_proj_ctx, mock_thread_ctx, mock_docs_ctx
    ):
        """
        PERF-02: When get_process_pool() returns None, stream_chat() still works via cold spawn.

        Graceful degradation: pool not initialized should not cause errors — it falls
        back to direct asyncio.create_subprocess_exec() call.
        """
        mock_db_ctx.set.return_value = None
        mock_proj_ctx.set.return_value = None
        mock_thread_ctx.set.return_value = None
        mock_docs_ctx.set.return_value = None

        cold_proc = make_mock_process(returncode=0)
        cold_proc.stdout = make_async_stdout([
            '{"type": "result", "subtype": "success", "usage": {"input_tokens": 3, "output_tokens": 2}}'
        ])
        mock_exec.return_value = cold_proc

        adapter = ClaudeCLIAdapter(api_key="test-key")
        adapter.set_context(MagicMock(), "proj-1", "thread-1")

        chunks = []
        async for chunk in adapter.stream_chat(
            messages=[{"role": "user", "content": "Hello"}],
            system_prompt="You are helpful."
        ):
            chunks.append(chunk)

        # Should have fallen back to cold spawn
        mock_exec.assert_called_once()
        # Should have received the complete chunk (no error)
        complete_chunks = [c for c in chunks if c.chunk_type == "complete"]
        assert len(complete_chunks) == 1

    def test_latency_documentation_exists(self):
        """
        PERF-03: ClaudeProcessPool docstring documents cold vs warm latency.

        Asserts that the class docstring contains quantified latency numbers
        for both cold start and warm acquire paths.
        """
        docstring = ClaudeProcessPool.__doc__
        assert docstring is not None, "ClaudeProcessPool must have a docstring"
        assert "Cold start" in docstring, "Docstring must document cold start latency"
        assert "Warm acquire" in docstring, "Docstring must document warm acquire latency"
        # Verify numeric latency values are present
        assert "120" in docstring or "400" in docstring, \
            "Docstring must contain cold start latency numbers (120ms or 400ms)"
        assert "5ms" in docstring, \
            "Docstring must contain warm acquire latency number (<5ms)"
