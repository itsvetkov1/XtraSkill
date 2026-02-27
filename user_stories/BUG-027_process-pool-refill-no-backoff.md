# BUG-027: Process Pool Refill Loop Has No Backoff

**Priority:** Low
**Status:** Done
**Component:** Backend / LLM Adapters / Claude CLI
**Discovered:** 2026-02-25

---

## User Story

As a developer running the backend,
I want the process pool to handle spawn failures gracefully,
So that a misconfigured CLI or auth issue doesn't flood logs with thousands of warnings per minute.

---

## Problem

`ClaudeProcessPool._refill_loop()` in `claude_cli_adapter.py` retries every 100ms indefinitely when process spawning fails:

```python
async def _refill_loop(self) -> None:
    while self._running:
        await asyncio.sleep(self.REFILL_DELAY)  # 0.1 seconds
        while self._running and self._queue.qsize() < self.POOL_SIZE:
            proc = await self._spawn_warm_process()
            ...
```

If `_spawn_warm_process()` fails (CLI binary not found, auth expired, disk full, etc.), the loop:
- Retries every 100ms — 600 attempts per minute
- Logs a warning on each failure
- Never backs off
- Never stops trying
- Never alerts that the pool is degraded

On a misconfigured dev machine, this produces thousands of log lines per minute.

---

## Acceptance Criteria

- [ ] Implement exponential backoff on consecutive spawn failures (e.g., 100ms → 200ms → 400ms → ... → 30s max)
- [ ] After N consecutive failures (e.g., 10), log at ERROR level with a clear message: "Process pool unable to maintain warm processes — check CLI installation and auth"
- [ ] Reset backoff counter on successful spawn
- [ ] Optionally: add a max retry count before the pool marks itself as degraded

---

## Technical References

- `backend/app/services/llm/claude_cli_adapter.py` — `ClaudeProcessPool._refill_loop()`
- `REFILL_DELAY = 0.1` — Current retry interval (100ms)
- `POOL_SIZE = 2` — Target pool size

---

*Created: 2026-02-25*
*Source: ASSISTANT_FLOW_REVIEW.md — ISSUE-09*
