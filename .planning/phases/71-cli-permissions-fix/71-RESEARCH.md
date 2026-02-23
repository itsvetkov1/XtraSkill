# Phase 71: CLI Permissions Fix - Research

**Researched:** 2026-02-23
**Domain:** Claude CLI subprocess argument configuration (Python asyncio subprocess)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Flag applies to ALL thread types (BA analysis + Assistant) — both run non-interactively
- Flag applies uniformly to ALL three spawn paths (warm pool, cold spawn, direct fallback)
- No tool restrictions — CLI can use all tools freely in the controlled backend environment
- Security hardening is a future concern (v2.0 backlog), not this phase
- Flag is hardcoded — always on, no env var toggle, no config option
- Add the flag to ALL code locations: the `cmd` list in `stream_chat()` AND both `_spawn_warm_process()` and `_cold_spawn()` subprocess calls
- No CLI version validation at startup — let it fail loudly at first use if the flag isn't supported
- If the CLI rejects the flag, surface the error to the user as a setup issue (don't silently retry without it)

### Claude's Discretion

- Exact placement of the flag in argument lists
- Whether to extract the flag as a constant or inline it
- Test structure and assertions

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLI-01 | Claude CLI subprocess runs with `--dangerously-skip-permissions` flag in all spawn paths (warm pool, cold spawn, direct) | Flag confirmed present and active in CLI v2.1.50; three spawn paths identified in code |
| CLI-02 | `--dangerously-skip-permissions` flag added to `_spawn_warm_process()` in ClaudeProcessPool | Target: `create_subprocess_exec` call at line 179 of `claude_cli_adapter.py` |
| CLI-03 | `--dangerously-skip-permissions` flag added to `_cold_spawn()` in ClaudeProcessPool | Target: `create_subprocess_exec` call at line 203 of `claude_cli_adapter.py` |
| CLI-04 | `--dangerously-skip-permissions` flag added to direct subprocess spawn in `stream_chat()` fallback path | Target: `create_subprocess_exec` call at line 628 of `claude_cli_adapter.py` |
| CLI-05 | Assistant chat works end-to-end without CLI permission prompts blocking | Verified: flag is a passthrough that suppresses all permission dialogs, confirmed by `--help` output |
</phase_requirements>

## Summary

Phase 71 is a targeted, mechanical change to a single file: `backend/app/services/llm/claude_cli_adapter.py`. The Claude CLI binary (v2.1.50, confirmed installed at path resolved by `shutil.which("claude")`) supports the `--dangerously-skip-permissions` flag, which bypasses all permission checks. The CLI `--help` confirms the exact flag name and its behaviour. No other files need to change.

The file has three independent subprocess spawn sites. Each currently builds an argument list (`cmd`) that does NOT include `--dangerously-skip-permissions`. The warm pool path (`_spawn_warm_process`) and cold fallback path (`_cold_spawn`) each call `asyncio.create_subprocess_exec` with an inline argument list. The direct fallback path in `stream_chat()` builds a `cmd` list variable then passes `*cmd` to `create_subprocess_exec`. All three must receive the flag.

Existing tests in `test_claude_process_pool.py` and `test_claude_cli_adapter.py` mock `asyncio.create_subprocess_exec` and capture call args, making it straightforward to assert the flag is present. New tests can follow the exact same pattern as existing ones.

**Primary recommendation:** Add `'--dangerously-skip-permissions'` as a constant `DANGEROUSLY_SKIP_PERMISSIONS = '--dangerously-skip-permissions'` at module level, insert it after `-p` in all three `create_subprocess_exec` argument lists, then add one assertion per spawn path in the test files confirming the constant appears in call args.

## Standard Stack

### Core

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Claude CLI binary | 2.1.50 (installed) | Subprocess being invoked | The adapter exists to wrap this binary |
| Python asyncio | stdlib | Non-blocking subprocess management | Already in use throughout adapter |
| `asyncio.create_subprocess_exec` | stdlib | Spawn CLI subprocess | Already in use at all three spawn sites |

### Supporting

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| `unittest.mock.patch` | stdlib | Mock subprocess in tests | Already established pattern in test suite |
| pytest-asyncio | project dependency | Async test execution | Already used in all LLM adapter tests |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `--dangerously-skip-permissions` | `--allow-dangerously-skip-permissions` | `--allow-dangerously-skip-permissions` only enables the flag as an *option* without activating it by default — does NOT suppress prompts. Use `--dangerously-skip-permissions` which actively bypasses checks. |
| Constant `DANGEROUSLY_SKIP_PERMISSIONS` | Inline string at each site | Constant provides single source of truth; inline is simpler but risks typo divergence across 3 sites |

## Architecture Patterns

### Recommended Project Structure

No structural changes — single file modification:

```
backend/app/services/llm/
└── claude_cli_adapter.py    # Three spawn sites receive the new flag
backend/tests/unit/llm/
├── test_claude_process_pool.py   # Add 3 tests: one per spawn path
└── test_claude_cli_adapter.py    # Optionally extend existing cold-spawn test
```

### Pattern 1: Module-Level Flag Constant

**What:** Define the flag once at module level, reference in all three spawn sites.
**When to use:** When the same string literal must appear in multiple locations with zero drift risk.
**Example:**

```python
# At module level, after DEFAULT_MODEL
DANGEROUSLY_SKIP_PERMISSIONS = '--dangerously-skip-permissions'
```

Then each `create_subprocess_exec` call includes it:

```python
# _spawn_warm_process():
return await asyncio.create_subprocess_exec(
    self._cli_path,
    '-p',
    DANGEROUSLY_SKIP_PERMISSIONS,   # <-- added
    '--output-format', 'stream-json',
    '--verbose',
    '--model', self._model,
    ...
)
```

```python
# _cold_spawn():
return await asyncio.create_subprocess_exec(
    self._cli_path,
    '-p',
    DANGEROUSLY_SKIP_PERMISSIONS,   # <-- added
    '--output-format', 'stream-json',
    '--verbose',
    '--model', self._model,
    ...
)
```

```python
# stream_chat() cmd list (direct fallback):
cmd = [
    self.cli_path,
    "-p",
    DANGEROUSLY_SKIP_PERMISSIONS,   # <-- added
    "--output-format", "stream-json",
    "--verbose",
    "--model", self.model,
]
```

### Pattern 2: Test Assertion for Flag Presence

**What:** Assert the flag constant appears in `call_args` of the mocked `create_subprocess_exec`.
**When to use:** After each spawn-path change, add a corresponding test.
**Example (follows existing test structure in test_claude_process_pool.py):**

```python
@pytest.mark.asyncio
@patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
async def test_spawn_warm_process_includes_skip_permissions(self, mock_exec):
    """CLI-02: _spawn_warm_process includes --dangerously-skip-permissions."""
    mock_exec.return_value = make_mock_process(returncode=None)

    pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model=DEFAULT_MODEL)
    await pool._spawn_warm_process()

    args = mock_exec.call_args[0]  # positional args to create_subprocess_exec
    assert '--dangerously-skip-permissions' in args
```

```python
@pytest.mark.asyncio
@patch('app.services.llm.claude_cli_adapter.asyncio.create_subprocess_exec')
async def test_cold_spawn_includes_skip_permissions(self, mock_exec):
    """CLI-03: _cold_spawn includes --dangerously-skip-permissions."""
    mock_exec.return_value = make_mock_process(returncode=None)

    pool = ClaudeProcessPool(cli_path='/usr/bin/claude', model=DEFAULT_MODEL)
    await pool._cold_spawn()

    args = mock_exec.call_args[0]
    assert '--dangerously-skip-permissions' in args
```

For CLI-04 (direct fallback in `stream_chat`), the existing test
`test_pool_not_initialized_falls_back_to_cold_spawn` already calls the direct path;
add an assertion to it or create a sibling that checks `call_args`.

### Anti-Patterns to Avoid

- **Using `--allow-dangerously-skip-permissions` instead of `--dangerously-skip-permissions`:** The `--allow-dangerously-skip-permissions` flag only enables the option without activating bypass. Confirmed by `--help` output — they are distinct flags. Use the one that BYPASSES, not the one that ALLOWS.
- **Only updating two of three spawn paths:** All three call sites (`_spawn_warm_process`, `_cold_spawn`, and the direct fallback in `stream_chat`) are independent. Missing one leaves an intermittent permission-blocked path.
- **Wrapping flag in a list inside `create_subprocess_exec`:** `create_subprocess_exec` takes positional args or `*list`; the flag must be a plain string, not a nested list.
- **Adding the flag after `--model self._model`:** Argument order does not matter for the Claude CLI, but placing it immediately after `-p` is conventional and matches the flag's conceptual grouping (operating mode flags before output flags).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting permission prompts at runtime | Custom stdout-watcher for prompt text | `--dangerously-skip-permissions` flag | The flag prevents prompts from ever appearing; detection is brittle |
| Env-var toggle for the flag | Conditional logic checking `os.environ` | Hardcode always-on per locked decision | Added complexity with no benefit in controlled backend environment |
| CLI version check at startup | Parse `claude --version` | None — fail loudly at first use | Per locked decision; CLI is already verified present by `shutil.which` |

**Key insight:** The entire change is additive (one string in three argument lists) — there is nothing to hand-roll.

## Common Pitfalls

### Pitfall 1: Wrong Flag Name

**What goes wrong:** Using `--allow-dangerously-skip-permissions` instead of `--dangerously-skip-permissions`.
**Why it happens:** The `--help` output lists both flags adjacently; `--allow-dangerously-skip-permissions` sounds like it enables permission bypass.
**How to avoid:** `--allow-dangerously-skip-permissions` only makes the bypass *available* as a user-selectable option — it does not suppress prompts. `--dangerously-skip-permissions` actively bypasses all checks. Confirmed by `--help` description: "Bypass all permission checks."
**Warning signs:** Subprocess still blocks on permission prompts after the change.

### Pitfall 2: Missing the Third Spawn Path

**What goes wrong:** Updating `_spawn_warm_process` and `_cold_spawn` but forgetting the direct `create_subprocess_exec` call in `stream_chat()` (the "pool not initialized" path, lines 628-635).
**Why it happens:** The third path is visually buried inside the warm-pool conditional and looks like dead code in normal operation. It is the fallback when `get_process_pool()` returns `None`.
**How to avoid:** The `cmd` list at line 604 does NOT feed the pool paths — the pool processes are pre-spawned. The direct call at line 628 uses `*cmd` directly. Both `cmd` and the pool path argument lists must have the flag.
**Warning signs:** Permission prompts appear when the pool is exhausted or not initialized.

### Pitfall 3: Test Assertion Checks Wrong Level

**What goes wrong:** Test asserts flag is in `mock_exec.call_args.args` but flag is actually passed as keyword argument or vice versa.
**Why it happens:** `create_subprocess_exec` receives the CLI path and flags as positional args (`*args`). The test should check `mock_exec.call_args[0]` (positional tuple), not `mock_exec.call_args[1]` (keyword dict).
**How to avoid:** Inspect `mock_exec.call_args[0]` — it is a tuple of all positional args starting with `cli_path`. The flag will be one of those.
**Warning signs:** Test passes even without the flag, or `AssertionError` on valid code.

## Code Examples

Verified patterns from direct codebase inspection:

### Current `_spawn_warm_process` Argument List (before change)

```python
# Source: backend/app/services/llm/claude_cli_adapter.py lines 178-193
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
    limit=1024 * 1024
)
```

After change — add `'--dangerously-skip-permissions'` after `'-p'`:

```python
return await asyncio.create_subprocess_exec(
    self._cli_path,
    '-p',
    '--dangerously-skip-permissions',
    '--output-format', 'stream-json',
    '--verbose',
    '--model', self._model,
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    env=env,
    limit=1024 * 1024
)
```

### Current `_cold_spawn` Argument List (before change)

```python
# Source: backend/app/services/llm/claude_cli_adapter.py lines 202-214
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
    limit=1024 * 1024
)
```

After change — identical pattern to `_spawn_warm_process`.

### Current `stream_chat` Direct Fallback `cmd` List (before change)

```python
# Source: backend/app/services/llm/claude_cli_adapter.py lines 604-610
cmd = [
    self.cli_path,
    "-p",
    "--output-format", "stream-json",
    "--verbose",
    "--model", self.model,
]
```

After change:

```python
cmd = [
    self.cli_path,
    "-p",
    "--dangerously-skip-permissions",
    "--output-format", "stream-json",
    "--verbose",
    "--model", self.model,
]
```

### CLI Help Output (Confirmed on Installed Binary)

```
--allow-dangerously-skip-permissions
    Enable bypassing all permission checks as an option, without it
    being enabled by default. Recommended only for sandboxes with no
    internet access.
--dangerously-skip-permissions
    Bypass all permission checks. Recommended only for sandboxes with
    no internet access.
```

Source: `claude --help` on CLI v2.1.50 (installed, verified via `shutil.which`)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Permission prompts blocked non-interactive subprocesses | `--dangerously-skip-permissions` suppresses all prompts | Available in current CLI v2.1.50 | Backend can spawn fully non-interactive CLI processes |

**No deprecated flags:** The flag is a current feature of the installed binary.

## Open Questions

None. All required information is available from:
1. Direct inspection of `claude --help` (flag exists, named correctly)
2. Direct inspection of `claude_cli_adapter.py` (three spawn sites are exactly as described in requirements)
3. Direct inspection of the test files (established mock patterns to follow)

## Sources

### Primary (HIGH confidence)

- `claude --help` on v2.1.50 — confirmed `--dangerously-skip-permissions` flag name, description ("Bypass all permission checks"), and distinction from `--allow-dangerously-skip-permissions`
- `backend/app/services/llm/claude_cli_adapter.py` — direct codebase inspection; three spawn sites located at lines 178, 202, and 628
- `backend/tests/unit/llm/test_claude_process_pool.py` — direct codebase inspection; established mock patterns, helper functions, and assertion styles confirmed

### Secondary (MEDIUM confidence)

None required — all findings backed by primary sources.

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — inspected installed binary and existing codebase
- Architecture: HIGH — three spawn sites are exact line numbers from live file
- Pitfalls: HIGH — wrong flag name confirmed by `--help` output; missing third path confirmed by code structure

**Research date:** 2026-02-23
**Valid until:** 2026-03-25 (CLI flags are stable; flag confirmed in installed v2.1.50)
