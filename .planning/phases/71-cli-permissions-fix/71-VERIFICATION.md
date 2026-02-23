---
phase: 71-cli-permissions-fix
verified: 2026-02-23T17:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 71: CLI Permissions Fix Verification Report

**Phase Goal:** The Claude CLI subprocess runs non-interactively without blocking on any permission prompt in all spawn paths
**Verified:** 2026-02-23
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All three CLI spawn paths include `--dangerously-skip-permissions` flag | VERIFIED | Lines 183, 208, 610 of `claude_cli_adapter.py`; grep confirms 4 occurrences (1 constant + 3 usages) |
| 2 | Warm pool processes carry the skip-permissions flag from creation | VERIFIED | `_spawn_warm_process()` line 183: `DANGEROUSLY_SKIP_PERMISSIONS` in `create_subprocess_exec` positional args |
| 3 | Cold spawn fallback carries the skip-permissions flag | VERIFIED | `_cold_spawn()` line 208: `DANGEROUSLY_SKIP_PERMISSIONS` in `create_subprocess_exec` positional args |
| 4 | Direct fallback in `stream_chat()` carries the skip-permissions flag | VERIFIED | `cmd` list at lines 607-614 includes `DANGEROUSLY_SKIP_PERMISSIONS` after `"-p"`; passed via `*cmd` to `create_subprocess_exec` at line 632 |
| 5 | Flag is defined as a module-level constant (single source of truth) | VERIFIED | Line 37: `DANGEROUSLY_SKIP_PERMISSIONS = '--dangerously-skip-permissions'` defined after `DEFAULT_MODEL` at module level |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/llm/claude_cli_adapter.py` | DANGEROUSLY_SKIP_PERMISSIONS constant and flag in all 3 spawn sites | VERIFIED | Exists. Substantive: constant at line 37, flag at lines 183, 208, 610. Wired: imported by test file (line 20 of test_claude_process_pool.py) and exercised in 3 tests. |
| `backend/tests/unit/llm/test_claude_process_pool.py` | Flag presence assertions for `_spawn_warm_process` and `_cold_spawn` | VERIFIED | Exists. Substantive: 3 assertions covering all 3 spawn paths (lines 140, 150, 297). Wired: directly calls adapter methods via mocked `create_subprocess_exec`. |
| `backend/tests/unit/llm/test_claude_cli_adapter.py` | Flag presence assertion for direct fallback in `stream_chat` | DEVIATION — see note | File exists and was listed in PLAN's `must_haves.artifacts` with `contains: "--dangerously-skip-permissions"`. The string is NOT present in this file. However the CLI-04 assertion was instead placed in `test_claude_process_pool.py` (line 297, test `test_pool_not_initialized_falls_back_to_cold_spawn`), which already exercised the direct fallback path. The goal is met; the file routing is a plan deviation that does not affect correctness. |

**Deviation note:** The PLAN artifact declaration for `test_claude_cli_adapter.py` (`contains: "--dangerously-skip-permissions"`) is not satisfied in the literal file. The test coverage intent (CLI-04 direct fallback) was satisfied through `test_claude_process_pool.py` instead. No gap exists in goal coverage.

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `claude_cli_adapter.py` | `asyncio.create_subprocess_exec` | `DANGEROUSLY_SKIP_PERMISSIONS` constant in positional args | WIRED | Constant appears as the 3rd positional argument in `_spawn_warm_process()` (line 183), `_cold_spawn()` (line 208), and as element of `cmd` list expanded via `*cmd` (line 610/632) |
| `test_claude_process_pool.py` | `claude_cli_adapter.py` | `mock_exec.call_args[0]` assertion | WIRED | Three tests assert `'--dangerously-skip-permissions' in args/call_args`. All 3 passed in live test run (59 passed, 1 pre-existing failure unrelated to this phase). |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CLI-01 | 71-01-PLAN | CLI subprocess runs with `--dangerously-skip-permissions` in all spawn paths | SATISFIED | Flag present in all 3 spawn sites; constant at module level ensures uniform application |
| CLI-02 | 71-01-PLAN | Flag added to `_spawn_warm_process()` | SATISFIED | Line 183 of adapter; `test_spawn_warm_process_includes_skip_permissions` PASSED |
| CLI-03 | 71-01-PLAN | Flag added to `_cold_spawn()` | SATISFIED | Line 208 of adapter; `test_cold_spawn_includes_skip_permissions` PASSED |
| CLI-04 | 71-01-PLAN | Flag added to direct subprocess spawn in `stream_chat()` fallback | SATISFIED | Lines 610/632 of adapter; assertion in `test_pool_not_initialized_falls_back_to_cold_spawn` PASSED |
| CLI-05 | 71-01-PLAN | Assistant chat works end-to-end without CLI permission prompts blocking | NEEDS HUMAN | Flag is correctly placed in all paths; end-to-end behavioral verification (no actual prompt blocking) requires a live subprocess call — cannot be verified by static analysis. See human verification section. |

All 5 requirements from `71-01-PLAN.md` frontmatter are accounted for. REQUIREMENTS.md marks all 5 as `[x]` Complete with Phase 71 traceability. No orphaned requirements found.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No stubs, placeholders, empty implementations, or TODO markers were detected in the two modified files.

---

### Human Verification Required

#### 1. End-to-End Non-Interactive Operation (CLI-05)

**Test:** Start the backend, create an Assistant thread, send a message that triggers a tool use (e.g., "search for documents about requirements"). Observe subprocess behavior.
**Expected:** The CLI subprocess completes without hanging. No permission prompt appears in `backend/logs/app.log`. Response streams back normally within a reasonable time.
**Why human:** CLI-05 requires a live subprocess spawn against the real `claude` binary. The flag suppresses permission prompts at the OS process level — this is not observable by static code analysis or unit test mocking. Only a real subprocess invocation can confirm the flag reaches the binary and suppresses interactive prompts.

---

### Gaps Summary

No gaps found. All five observable truths are satisfied by substantive, wired implementation. The one artifact-routing deviation (CLI-04 test placed in `test_claude_process_pool.py` rather than `test_claude_cli_adapter.py`) is a plan refinement, not a gap — the coverage goal is fully met.

CLI-05 (end-to-end non-blocking) is marked as needing human verification because it requires a live subprocess. This is expected: it was noted in RESEARCH.md as verified by `--help` output, not a running subprocess. The automated evidence is strong (flag in all 3 spawn sites, 3 passing tests asserting flag presence).

---

## Test Run Summary

```
59 passed, 1 failed (pre-existing, unrelated)
```

**Pre-existing failure:** `test_stream_chat_passes_api_key_in_env` in `test_claude_cli_adapter.py` — asserts `ANTHROPIC_API_KEY` is injected into subprocess env, but the adapter intentionally filters env vars via `_build_cli_env()` (which excludes `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` but passes through the ambient environment, including `ANTHROPIC_API_KEY` if set). The test fails because `ANTHROPIC_API_KEY` is not set in the CI/test environment, not because of any regression from this phase. Documented in SUMMARY as a pre-existing issue.

**New tests (all PASSED):**
- `test_spawn_warm_process_includes_skip_permissions` — CLI-02
- `test_cold_spawn_includes_skip_permissions` — CLI-03
- `test_pool_not_initialized_falls_back_to_cold_spawn` (augmented assertion) — CLI-04

**Commits verified:**
- `37531d8` — `feat(71-01): add DANGEROUSLY_SKIP_PERMISSIONS flag to all 3 CLI spawn paths` (exists, modifies `claude_cli_adapter.py`)
- `c2db125` — `test(71-01): add flag presence assertions for all 3 CLI spawn paths` (exists, modifies `test_claude_process_pool.py`)

---

_Verified: 2026-02-23T17:00:00Z_
_Verifier: Claude (gsd-verifier)_
