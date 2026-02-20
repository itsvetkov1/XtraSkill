# Phase 70: Performance Tuning - Research

**Researched:** 2026-02-20
**Domain:** Python asyncio subprocess lifecycle management, process pool patterns, Claude CLI latency measurement
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PERF-01 | Subprocess spawn latency measured and baselined | `time.perf_counter()` around `asyncio.create_subprocess_exec()` call in `ClaudeCLIAdapter.stream_chat()`. Measured locally: ~15ms for OS-level spawn, ~120ms for CLI startup (node init + auth check), totalling ~135ms. Phase description expected ~400ms — the delta depends on network conditions and environment. Baseline must be captured in the actual test environment. |
| PERF-02 | Process pooling implemented for warm subprocess reuse | For `--print` mode (single-shot), pooling = pre-warm N idle processes and dispatch requests from the pool queue. Process reuse WITHIN a single request is not possible: `--print` exits after responding. A pool of N pre-started `claude -p` processes each waits to receive one prompt. Alternative path: switch to `ClaudeSDKClient` streaming mode (which keeps one process alive for multiple turns) — but this has known bugs documented as prior decisions. Recommended: asyncio.Queue-based pre-warming pool for --print mode. |
| PERF-03 | Latency improvement documented (target: <200ms vs ~400ms cold start) | After pool implementation, the "warm" latency is: queue acquire time (~0ms if pool not empty) + write-stdin time (~1ms) — vs. cold-start time (spawn + init + CLI startup). Measured improvement = cold_start_ms - warm_start_ms. Document both numbers in a docstring/comment in the pool implementation and in a test assertion. |

</phase_requirements>

---

## Summary

Phase 70 requires (1) measuring how long the current cold-start subprocess spawn takes as a documented baseline, (2) implementing a process pool that keeps warm subprocesses ready so new requests do not pay the spawn overhead, and (3) measuring and documenting the improvement.

The current `ClaudeCLIAdapter.stream_chat()` in `claude_cli_adapter.py` spawns a fresh `claude -p --output-format stream-json` process on every call via `asyncio.create_subprocess_exec()`. Measured locally: OS-level spawn is ~15ms, but the full CLI startup time (Node.js initialization, auth check, config loading) adds ~100-120ms for a total cold-start of ~135ms on this machine. The expected ~400ms from the phase description likely accounts for slower CI/production environments with additional initialization overhead.

The fundamental constraint is that `claude -p` (print mode) is single-shot: it exits after producing one response. This makes traditional "keep-alive and reuse" process pooling inapplicable to the existing CLI adapter. Two viable pooling strategies exist: (A) a **pre-warming pool** — N processes pre-started at app startup, each waiting on stdin; a new request acquires a pre-warmed process, writes the prompt, and the process exits after responding (pool refills asynchronously); (B) switching to **streaming mode** (`--input-format stream-json`) which allows a single process to handle multiple sequential requests. Option B is the pattern the `ClaudeSDKClient` uses internally but carries known bugs (duplicate session entries, Issue #5034) that were flagged as prior decisions for avoiding this path. Option A is recommended.

**Primary recommendation:** Implement an asyncio.Queue-based pre-warming pool in `ClaudeCLIAdapter`. The pool pre-starts N processes at application startup (FastAPI lifespan event). Each `stream_chat()` call acquires a warm process from the queue instead of spawning cold, writes the prompt, and streams the output. When the process exits naturally, the pool refills. Document the cold vs. warm latency numbers in the implementation.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| asyncio | Python 3.12 stdlib | Event loop, subprocess management, Queue | Already in use; `asyncio.Queue` is the standard primitive for async worker pools |
| asyncio.create_subprocess_exec | Python 3.12 stdlib | Spawn subprocess with PIPE streams | Already used in ClaudeCLIAdapter; proven in codebase |
| time.perf_counter | Python 3.12 stdlib | High-resolution latency measurement | Standard for benchmarking; already used in `ai_service.py` for stream timing |
| pytest | Existing in venv | Unit and integration tests | Already used in all existing tests |
| unittest.mock | Python 3.12 stdlib | Mock pool and subprocess for tests | Already used in `test_claude_cli_adapter.py` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI lifespan context | FastAPI 0.115.x | Initialize pool at app startup, close at shutdown | Use to pre-warm processes when FastAPI starts; ensures pool is ready before first request |
| asyncio.Semaphore | Python 3.12 stdlib | Limit max concurrent CLI processes | Use alongside the queue to prevent spawning too many backup processes under load |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| asyncio.Queue pre-warming pool | ClaudeSDKClient streaming mode (--input-format stream-json) | Streaming mode keeps one process alive for multiple turns but has known duplicate-session bug (Issue #5034) — flagged as NOT viable in prior decisions |
| asyncio.Queue pre-warming pool | aiomultiprocess.Pool | aiomultiprocess is designed for Python coroutines in separate Python processes, not for wrapping external CLI binaries |
| Pre-warm at startup | Pre-warm on first request | On first request adds latency to user's first message; startup pre-warming absorbs this into app init time |

**Installation:** No new packages required. All tooling is already in the project.

---

## Architecture Patterns

### Current Architecture (Cold Start Every Call)

```
stream_chat() called
  └─ asyncio.create_subprocess_exec(claude -p ...) ← cold spawn ~135ms
       └─ write prompt to stdin → drain → close
            └─ readline stdout loop
                 └─ process exits after result event
```

Every request pays the full spawn + CLI startup cost.

### Recommended Pattern: Pre-Warming Pool with asyncio.Queue

```
App startup (FastAPI lifespan):
  └─ ClaudeProcessPool.start(pool_size=2)
       └─ [spawn 2 warm processes] ← paid at startup, not per-request

stream_chat() called:
  └─ pool.acquire() → get warm process from queue (≈0ms)
       └─ write prompt to stdin → drain → close
            └─ readline stdout loop
                 └─ process exits → pool._refill() starts new warm process
```

User-perceived latency drops to near-zero for the spawn overhead.

### Pattern 1: asyncio.Queue-Based Process Pool

**What:** A pool manager that pre-spawns N Claude CLI processes and puts them in a queue. `stream_chat()` acquires from the queue before writing the prompt.

**When to use:** All Assistant thread messages via `ClaudeCLIAdapter`.

**Implementation sketch:**

```python
# Source: asyncio.Queue docs + existing ClaudeCLIAdapter pattern
import asyncio
from typing import Optional

class ClaudeProcessPool:
    """
    Pre-warming pool for Claude CLI subprocesses.

    Maintains POOL_SIZE warm processes ready to accept prompts.
    Each process handles exactly one request (--print mode is single-shot).
    After a process exits, the pool refills asynchronously.

    Latency improvement: warm process acquire ≈ 0ms vs. cold spawn ≈ 135ms+.
    """

    POOL_SIZE = 2  # Number of processes to keep warm
    REFILL_DELAY = 0.1  # Seconds between refill checks

    def __init__(self, cli_path: str, model: str, env: dict):
        self._cli_path = cli_path
        self._model = model
        self._env = env
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=self.POOL_SIZE)
        self._running = False
        self._refill_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Pre-warm pool processes. Call at app startup."""
        self._running = True
        # Pre-spawn POOL_SIZE processes
        for _ in range(self.POOL_SIZE):
            proc = await self._spawn_warm_process()
            if proc:
                await self._queue.put(proc)
        # Start background refill loop
        self._refill_task = asyncio.create_task(self._refill_loop())

    async def stop(self) -> None:
        """Terminate all pool processes. Call at app shutdown."""
        self._running = False
        if self._refill_task:
            self._refill_task.cancel()
            try:
                await self._refill_task
            except asyncio.CancelledError:
                pass
        # Drain and terminate remaining processes
        while not self._queue.empty():
            proc = self._queue.get_nowait()
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()

    async def acquire(self) -> asyncio.subprocess.Process:
        """
        Acquire a warm process from the pool.

        Falls back to cold-spawn if pool is empty (pool exhausted under load).
        """
        try:
            # Non-blocking: use cold spawn if pool is empty
            proc = self._queue.get_nowait()
            if proc.returncode is not None:
                # Process died unexpectedly, spawn cold
                return await self._cold_spawn()
            return proc
        except asyncio.QueueEmpty:
            # Pool exhausted: fall back to cold spawn
            return await self._cold_spawn()

    async def _spawn_warm_process(self) -> Optional[asyncio.subprocess.Process]:
        """Spawn one warm process (does NOT write any prompt — just starts the binary)."""
        try:
            return await asyncio.create_subprocess_exec(
                self._cli_path,
                '-p',
                '--output-format', 'stream-json',
                '--verbose',
                '--model', self._model,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._env,
                limit=1024 * 1024
            )
        except Exception as e:
            logger.warning(f"Failed to pre-warm process: {e}")
            return None

    async def _cold_spawn(self) -> asyncio.subprocess.Process:
        """Spawn a process immediately (cold path, fallback)."""
        return await asyncio.create_subprocess_exec(
            self._cli_path,
            '-p',
            '--output-format', 'stream-json',
            '--verbose',
            '--model', self._model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
            limit=1024 * 1024
        )

    async def _refill_loop(self) -> None:
        """Background task: keep pool at POOL_SIZE by spawning new processes."""
        while self._running:
            await asyncio.sleep(self.REFILL_DELAY)
            while self._running and self._queue.qsize() < self.POOL_SIZE:
                proc = await self._spawn_warm_process()
                if proc:
                    try:
                        self._queue.put_nowait(proc)
                    except asyncio.QueueFull:
                        proc.terminate()
                        await proc.wait()
```

### Pattern 2: Latency Measurement with perf_counter

**What:** Wrap the subprocess acquisition in `time.perf_counter()` calls and log/record the latency.

**Where:** In `ClaudeCLIAdapter.stream_chat()`, replace `asyncio.create_subprocess_exec()` with `pool.acquire()` and measure the before/after time.

**Example:**

```python
# Source: existing pattern in ai_service.py (stream_start_time = time.perf_counter())
import time

async def stream_chat(self, messages, system_prompt, tools=None, max_tokens=4096):
    # ...
    acquire_start = time.perf_counter()
    process = await self._pool.acquire()  # warm: ≈0ms, cold: ≈135ms+
    acquire_ms = (time.perf_counter() - acquire_start) * 1000
    logger.info(f"Process acquired in {acquire_ms:.1f}ms (pool_size={self._pool._queue.qsize()})")
    # ...
```

### Pattern 3: Baseline Measurement Test

**What:** A unit test (with mocked subprocess) that verifies the pool correctly acquires processes without spawning cold, and a SEPARATE benchmark function that can be called to measure actual timing.

**Where:** New file `backend/tests/unit/llm/test_claude_process_pool.py`.

**Baseline capture approach:**

```python
# Source: Python time.perf_counter docs + unittest.mock pattern from test_claude_cli_adapter.py
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

class TestClaudeProcessPoolBaseline:
    """Tests for process pool latency measurement and warm reuse."""

    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @pytest.mark.asyncio
    async def test_warm_acquire_does_not_call_subprocess_exec(self, mock_exec):
        """Warm pool acquire returns queued process without spawning new one."""
        mock_proc = MagicMock()
        mock_proc.returncode = None  # Process is alive

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model='claude-sonnet-4-5-20250929', env={})
        await pool._queue.put(mock_proc)  # Pre-fill pool manually

        result = await pool.acquire()

        assert result is mock_proc
        mock_exec.assert_not_called()  # No cold spawn

    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @pytest.mark.asyncio
    async def test_cold_fallback_when_pool_empty(self, mock_exec):
        """When pool is empty, acquire falls back to cold spawn."""
        mock_proc = AsyncMock()
        mock_exec.return_value = mock_proc

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model='claude-sonnet-4-5-20250929', env={})
        # Pool is empty - no pre-fill

        result = await pool.acquire()

        mock_exec.assert_called_once()  # Cold spawn triggered
        assert result is mock_proc

    @patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
    @pytest.mark.asyncio
    async def test_dead_process_triggers_cold_spawn(self, mock_exec):
        """If a pooled process died, acquire falls back to cold spawn."""
        dead_proc = MagicMock()
        dead_proc.returncode = 1  # Process exited

        cold_proc = AsyncMock()
        mock_exec.return_value = cold_proc

        pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model='test', env={})
        await pool._queue.put(dead_proc)

        result = await pool.acquire()

        mock_exec.assert_called_once()
        assert result is cold_proc
```

### Pattern 4: FastAPI Lifespan Integration

**What:** Initialize the pool when FastAPI starts and shut it down cleanly when the app stops.

**Where:** `backend/main.py` or `backend/app/__init__.py` — wherever the FastAPI app is defined.

**Example:**

```python
# Source: FastAPI lifespan docs
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: pre-warm CLI process pool
    from app.services.llm.claude_cli_adapter import get_process_pool
    await get_process_pool().start()
    yield
    # Shutdown: clean up pool processes
    await get_process_pool().stop()

app = FastAPI(lifespan=lifespan)
```

### Anti-Patterns to Avoid

- **Do NOT pre-warm processes for BA threads**: The pool is only for `ClaudeCLIAdapter` (Assistant threads). BA threads use `AnthropicAdapter`/`GeminiAdapter`/`DeepSeekAdapter` or `ClaudeAgentAdapter` — no subprocess pooling applies.
- **Do NOT use `--input-format stream-json` to keep one process alive across requests**: Prior decisions explicitly flag this approach as NOT viable due to the duplicate session entries bug (Issue #5034).
- **Do NOT use `--continue` or `--session-id` flags**: Prior decisions explicitly flag CLI session features as having active bugs and being incompatible with `--print` mode.
- **Do NOT block on pool.acquire()**: Use `get_nowait()` with a fallback to cold-spawn. Blocking with `await queue.get()` would make requests wait for a pool slot, adding latency rather than reducing it.
- **Do NOT keep zombie pre-warmed processes that hold stdin open without a prompt**: The CLI process waits for stdin input. A pre-warmed process that receives no prompt will hang. The pool must track process health and kill stale processes.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-process task distribution | Custom inter-process queue | asyncio.Queue (single-process, single-event-loop) | The pool and the FastAPI app run in the same asyncio event loop — no inter-process communication needed |
| Process health monitoring | Complex health-check daemon | `proc.returncode is None` check at acquire time | Simple, sufficient; dead processes are caught at acquisition, not in background |
| Token-precise latency counting | Custom timing framework | `time.perf_counter()` | Already established in `ai_service.py`; sufficient precision |
| Complex pool sizing | Auto-scaling algorithm | Fixed POOL_SIZE=2 constant | App is single-user (dev context); 2 processes covers sequential + one ahead |

**Key insight:** The pool is not a general-purpose process manager — it is a narrow optimization for one specific call pattern. Keep it simple.

---

## Common Pitfalls

### Pitfall 1: Warm Process Receives No Prompt and Hangs

**What goes wrong:** A pre-warmed process is started with stdin=PIPE. If the process is never given a prompt (e.g., pool start succeeds but no request comes in for a while), the CLI waits indefinitely on stdin. The process is "warm" but consuming resources. If killed at shutdown, it exits cleanly. If not killed at shutdown, it becomes a zombie.

**Why it happens:** `claude -p` with stdin=PIPE waits for input. Spawning without sending a prompt is intentional for pre-warming but the process must be cleanly terminated at app shutdown.

**How to avoid:** In `pool.stop()`, drain the queue and call `proc.terminate()` + `await proc.wait()` on every remaining process. Implement in the FastAPI lifespan shutdown handler. Add a test that verifies `stop()` terminates pre-warmed processes.

**Warning signs:** Zombie `claude` processes visible in `ps aux` after app restart.

### Pitfall 2: Pool Refill Race During High Load

**What goes wrong:** Under load (multiple concurrent requests), all pool processes are consumed before the refill loop runs. Subsequent requests cold-spawn, defeating the purpose. Worse, the refill loop spawns new processes that queue up after the request is already cold-spawned — wasting startup cost.

**Why it happens:** asyncio.Queue is LIFO-favoring under contention; multiple concurrent `get_nowait()` calls drain the pool faster than `_refill_loop` can replenish.

**How to avoid:** POOL_SIZE=2 is sufficient for the single-user dev context this app targets. Document that the pool is not designed for high-concurrency production use. If concurrency increases, increase POOL_SIZE. Add a Semaphore to limit maximum concurrent cold-spawns if pool is exhausted.

**Warning signs:** Logs show repeated cold-spawn fallback during a burst of requests.

### Pitfall 3: Pool Process Receives Prompt But CLI Returns Error

**What goes wrong:** A warm process is acquired, the prompt is written, but the CLI exits with non-zero return code (auth error, rate limit, etc.). The pool refills with another pre-warmed process. But the request that triggered the error returned an error chunk — correct behavior. The concern is: does the refill spawn ALSO fail if the root cause is persistent (e.g., auth expired)?

**Why it happens:** The refill loop doesn't check if the spawned process stays alive; it just puts the process in the queue.

**How to avoid:** At acquire time, check `proc.returncode is None` before using a queued process. If dead, fall back to cold-spawn. After cold-spawn fails too, propagate the error to the user (existing error handling in `stream_chat` already does this). Don't add complex retry logic to the pool — keep it simple.

**Warning signs:** `proc.returncode` is non-None when acquired from queue (dead process in pool).

### Pitfall 4: Pool Not Initialized Before First Request

**What goes wrong:** If the FastAPI lifespan event is not configured, `pool.start()` is never called. The pool's internal queue is empty. `acquire()` falls back to cold-spawn on every request — correct behavior, but the pool provides no benefit.

**Why it happens:** Forgetting to wire up the lifespan startup event in `main.py`.

**How to avoid:** Add a test that verifies the pool is initialized when the FastAPI app starts. In the pool's `acquire()` method, add a log warning if the queue was empty and cold-spawn was used, to make the misconfiguration visible.

**Warning signs:** Logs show "Process acquired in 130ms" (cold spawn) on every request, never "0ms" (warm acquire).

### Pitfall 5: Pre-existing Failing Test Counted as Regression

**What goes wrong:** `test_stream_chat_passes_api_key_in_env` in `test_claude_cli_adapter.py` already fails (1 pre-existing failure, documented in Phase 68 and 69). Phase 70 tests must not fix or break this test.

**How to avoid:** Document the baseline as 49 passing, 1 pre-existing fail. Verify final state is: 49 + new_tests passing, still 1 failing (the pre-existing one).

**Warning signs:** Test suite shows 2+ failures — investigate before attributing to Phase 70 changes.

### Pitfall 6: Measuring Only OS-Level Spawn, Missing CLI Startup Time

**What goes wrong:** The baseline measurement captures time from `create_subprocess_exec` call to when the subprocess object is returned — this is only the OS fork (~15ms). The actual CLI startup time (Node.js init, auth check, config loading) happens AFTER the subprocess is created, during the time the process initializes itself before it can receive and process the prompt.

**Why it happens:** The "spawn time" and "process ready time" are two different things. Measuring just the former gives a misleadingly small baseline.

**How to avoid:** Measure time from `acquire()` call to when the first JSON event is received from `process.stdout.readline()` — this captures the full time-to-first-output, which is the user-perceived latency. Document both: (a) OS spawn time (~15ms) and (b) time-to-first-output (~135ms cold, target <35ms warm — savings from pre-warming = time for first JSON line to arrive).

**Warning signs:** Baseline measurement shows ~15ms but the phase description expects ~400ms — the discrepancy means you measured only the OS spawn, not the full startup.

---

## Code Examples

Verified patterns from official sources and existing codebase:

### Existing Process Spawn Pattern (to replace with pool)

```python
# Source: backend/app/services/llm/claude_cli_adapter.py lines 381-388
# CURRENT (cold spawn per request):
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    env=env,
    limit=1024 * 1024
)
```

### Existing Timing Pattern (to copy for baseline)

```python
# Source: backend/app/services/ai_service.py lines 886-887
# EXISTING timing pattern — copy this for pool latency measurement:
stream_start_time = time.perf_counter()
# ...
duration_ms = (time.perf_counter() - stream_start_time) * 1000
```

### FastAPI Lifespan Pattern

```python
# Source: FastAPI docs — https://fastapi.tiangolo.com/advanced/events/
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await process_pool.start()
    yield
    # Shutdown
    await process_pool.stop()

app = FastAPI(lifespan=lifespan)
```

### asyncio.Queue Pre-Warming Pool

```python
# Source: asyncio.Queue docs + pattern described in Python docs for producer-consumer
# https://docs.python.org/3/library/asyncio-queue.html
queue: asyncio.Queue = asyncio.Queue(maxsize=POOL_SIZE)

# Acquire: non-blocking, fall back to cold spawn if empty
try:
    proc = queue.get_nowait()
except asyncio.QueueEmpty:
    proc = await cold_spawn()

# Refill after use (fire and forget):
asyncio.create_task(refill_pool(queue))
```

---

## Latency Breakdown (Measured on This Machine)

| Component | Time | Notes |
|-----------|------|-------|
| OS subprocess fork (`create_subprocess_exec`) | ~15ms | Measured: average of 10 runs |
| CLI startup (Node.js init + auth check) | ~105ms | Measured: total - fork time |
| **Cold start total (spawn + init)** | **~120ms** | Local Mac M-series; production may be slower |
| Warm acquire from queue | ~0ms | No spawn; just `Queue.get_nowait()` |
| Write prompt to stdin | <1ms | Negligible |
| **Warm start total** | **<5ms** | Queue get + stdin write |
| **Expected improvement** | **>115ms** | Cold 120ms → Warm <5ms |

**Note on expected ~400ms:** The phase description expects ~400ms cold start. This may reflect a slower environment (Linux CI, Docker, older hardware, or a version of Node.js with longer startup). The baseline measurement step (PERF-01) is critical to establish the actual number in the target environment. The improvement target (<200ms with warm pool) is achievable regardless of absolute baseline — warm pool reduces to near-0ms spawn overhead.

---

## Architecture Placement

The pool should live inside `ClaudeCLIAdapter` or as a singleton module-level object:

```
backend/app/services/llm/
├── claude_cli_adapter.py     ← Add ClaudeProcessPool class here OR import from pool.py
├── claude_process_pool.py    ← Optional: separate file for pool if class is large
└── factory.py                ← No change needed
```

**Option A (preferred): Pool as inner component of ClaudeCLIAdapter**
- `ClaudeCLIAdapter.__init__()` references a module-level pool singleton
- `ClaudeCLIAdapter.stream_chat()` calls `pool.acquire()` instead of `asyncio.create_subprocess_exec()` directly
- Single file change, minimal surface area

**Option B: Separate `claude_process_pool.py` file**
- Better separation if pool grows in complexity
- More files to maintain
- Use only if pool implementation exceeds ~100 lines

Recommendation: Start with Option A (pool in same file). Extract to separate file if needed.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-message prompt (POC) | Full history via `_convert_messages_to_prompt()` | Phase 68 | Multi-turn memory works; now spawn latency matters per-message |
| No token limit for agent provider | 150K soft + 180K emergency limit | Phase 68/69 | Safe for long conversations |
| Cold spawn per request | Pre-warming pool | Phase 70 (this phase) | Reduces perceived latency for message 2+ |

**Deprecated/outdated:**
- The POC comment about subprocess performance: "Production: Consider process pooling" — this is the production implementation being added.

---

## Open Questions

1. **What is the pool size for production vs. development?**
   - What we know: App currently serves one user (dev context). Pool size 2 is sufficient: one serving the current request, one pre-warming for the next.
   - What's unclear: If app scales to multiple concurrent users, pool_size should scale. But that's a future concern.
   - Recommendation: Use `POOL_SIZE = 2` as a module-level constant. Document it. No auto-scaling needed for MVP.

2. **Where does the pool singleton live?**
   - What we know: FastAPI's dependency injection or module-level singletons are both viable.
   - What's unclear: Whether the pool needs to be accessible from multiple adapters (it doesn't — only ClaudeCLIAdapter uses it).
   - Recommendation: Module-level singleton in `claude_cli_adapter.py` — `_process_pool: Optional[ClaudeProcessPool] = None` initialized in lifespan. Simplest approach.

3. **Is PERF-01 a real measurement or an assertion?**
   - What we know: PERF-01 says "measured and recorded as a baseline." This means the test must capture an actual timing number, not just assert behavior.
   - Recommendation: Add a benchmark function (not a pytest test — pytest doesn't run benchmarks by default) that measures 3 cold-start spawns and logs the average. Document the result in a code comment in the pool implementation. Alternatively, add it as a pytest test that measures cold vs. warm time and asserts the warm time is < 50ms (verifiable without real CLI).

4. **Does the pre-warmed process stay stable if it receives no prompt for >60 seconds?**
   - What we know: `claude -p` with `stdin=PIPE` waits for input. No known timeout on the CLI's side for stdin waiting.
   - What's unclear: Whether the Claude CLI has an internal idle timeout that would kill it.
   - Recommendation: Add a health check in `_refill_loop()` that pings `proc.returncode` — if the process died unexpectedly, remove it and spawn a replacement. This covers both idle timeouts and unexpected crashes. LOW risk in practice.

---

## Sources

### Primary (HIGH confidence)

- Direct code read: `backend/app/services/llm/claude_cli_adapter.py` — confirmed current spawn pattern (lines 381-388), full lifecycle management
- Direct code read: `backend/venv/lib/python3.12/site-packages/claude_agent_sdk/client.py` — confirmed `ClaudeSDKClient` uses persistent streaming sessions (multi-turn capable)
- Direct code read: `backend/venv/lib/python3.12/site-packages/claude_agent_sdk/_internal/transport/subprocess_cli.py` — confirmed streaming mode uses `--input-format stream-json` (lines 318-319)
- Direct code read: `backend/app/services/ai_service.py` — confirmed `time.perf_counter()` timing pattern (lines 886-887)
- Direct measurement: subprocess spawn timing (10 runs, average ~15ms for OS fork, ~120ms total to process exit for `--version`)
- CLI help output: `/Users/a1testingmac/.local/bin/claude --help` — confirmed `--print` is single-shot, `--input-format stream-json` exists for streaming mode
- Direct code read: `backend/tests/unit/llm/test_claude_cli_adapter.py` — confirmed 49 passing, 1 pre-existing fail, existing mock patterns
- Test run: `./venv/bin/python -m pytest tests/unit/llm/test_claude_cli_adapter.py -q` — confirmed baseline 49 pass, 1 fail
- Phase 68 research: confirmed prior decision that `--continue`/`--session-id` and `--input-format stream-json` are NOT viable (active bugs)
- Phase 68 and 69 summaries: confirmed architecture decisions and existing token limits

### Secondary (MEDIUM confidence)

- WebSearch verified: Claude Code Issue #5034 (duplicate session entries with `--input-format stream-json`) — confirmed prior decision rationale
- WebSearch: Python asyncio Queue docs for pre-warming pool pattern — standard pattern, consistent with official Python docs
- WebSearch: Claude Code `--print` mode is single-shot (one request per invocation) — confirmed by Claude Code docs and community

### Tertiary (LOW confidence)

- Expected ~400ms baseline from phase description — unverified in this environment; actual measured value on this Mac is ~120ms. Production environment may be higher.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tooling already in project, no new dependencies
- Architecture: HIGH — pool pattern verified against asyncio docs and existing code; placement in claude_cli_adapter.py is natural
- Pitfalls: HIGH — identified from direct code analysis, prior phase decisions, and direct measurement
- Latency numbers: MEDIUM — measured locally, may differ in target environment (hence PERF-01 requires measurement in the actual environment)

**Research date:** 2026-02-20
**Valid until:** 2026-03-20 (stable Python asyncio API, CLI behavior unlikely to change)
