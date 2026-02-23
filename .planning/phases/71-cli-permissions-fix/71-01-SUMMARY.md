---
phase: 71-cli-permissions-fix
plan: 01
subsystem: backend-llm-adapter
tags: [cli, subprocess, permissions, testing]
dependency_graph:
  requires: []
  provides: [non-interactive-cli-subprocess]
  affects: [claude-cli-adapter, process-pool]
tech_stack:
  added: []
  patterns: [module-level-constant, flag-injection]
key_files:
  created: []
  modified:
    - backend/app/services/llm/claude_cli_adapter.py
    - backend/tests/unit/llm/test_claude_process_pool.py
key_decisions:
  - "--dangerously-skip-permissions is hardcoded (always on) — no env var toggle, no config option"
  - "Flag placed immediately after '-p' to group operating-mode flags together"
  - "Defined as DANGEROUSLY_SKIP_PERMISSIONS module-level constant (single source of truth)"
metrics:
  duration: "2m 23s"
  completed_date: "2026-02-23"
  tasks_completed: 2
  files_modified: 2
requirements_satisfied:
  - CLI-01
  - CLI-02
  - CLI-03
  - CLI-04
  - CLI-05
---

# Phase 71 Plan 01: CLI Permissions Fix Summary

**One-liner:** Added `--dangerously-skip-permissions` constant and flag to all 3 Claude CLI subprocess spawn paths, with test assertions confirming presence in each path.

## What Was Built

The Claude CLI binary prompts for user permission on certain operations. In a backend subprocess context, these prompts block indefinitely. This plan adds `--dangerously-skip-permissions` to every subprocess spawn path so the backend runs fully non-interactively.

**Changes made:**

1. `backend/app/services/llm/claude_cli_adapter.py` — Added `DANGEROUSLY_SKIP_PERMISSIONS = '--dangerously-skip-permissions'` constant at module level (after `DEFAULT_MODEL`), then inserted the constant into 3 spawn sites:
   - `_spawn_warm_process()`: after `-p` in `create_subprocess_exec` call (line 183)
   - `_cold_spawn()`: after `-p` in `create_subprocess_exec` call (line 208)
   - `stream_chat()` direct fallback `cmd` list: after `-p` (line 610)

2. `backend/tests/unit/llm/test_claude_process_pool.py` — Added import for `DANGEROUSLY_SKIP_PERMISSIONS`, two new test methods, and one new assertion:
   - `test_spawn_warm_process_includes_skip_permissions` (CLI-02): asserts flag in `_spawn_warm_process` args
   - `test_cold_spawn_includes_skip_permissions` (CLI-03): asserts flag in `_cold_spawn` args
   - Assertion added to `test_pool_not_initialized_falls_back_to_cold_spawn` (CLI-04): asserts flag in direct fallback args

## Task Results

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add DANGEROUSLY_SKIP_PERMISSIONS constant and flag in all 3 spawn sites | 37531d8 | backend/app/services/llm/claude_cli_adapter.py |
| 2 | Add test assertions for flag presence in all 3 spawn paths | c2db125 | backend/tests/unit/llm/test_claude_process_pool.py |

## Verification Results

- `grep -c "DANGEROUSLY_SKIP_PERMISSIONS" backend/app/services/llm/claude_cli_adapter.py` = **4** (1 constant + 3 usages)
- `grep -c "dangerously-skip-permissions" backend/tests/unit/llm/test_claude_process_pool.py` = **6** (exceeds minimum 3)
- Test run: **59 passed, 1 failed** (failure is pre-existing `test_stream_chat_passes_api_key_in_env` unrelated to this plan)
- New tests: `test_spawn_warm_process_includes_skip_permissions` PASSED, `test_cold_spawn_includes_skip_permissions` PASSED, `test_pool_not_initialized_falls_back_to_cold_spawn` PASSED (with new assertion)

## Deviations from Plan

None - plan executed exactly as written.

## Pre-existing Issues Noted (Out of Scope)

- `test_stream_chat_passes_api_key_in_env` in `test_claude_cli_adapter.py` was failing before this plan began (the adapter does not inject `ANTHROPIC_API_KEY` into the subprocess env via `_build_cli_env()` — it filters env vars). This is unrelated to the CLI permissions fix and was not introduced by this plan. Logged for future investigation.

## Self-Check: PASSED

Files exist:
- `backend/app/services/llm/claude_cli_adapter.py` — FOUND (modified)
- `backend/tests/unit/llm/test_claude_process_pool.py` — FOUND (modified)

Commits exist:
- `37531d8` — FOUND (feat(71-01): add DANGEROUSLY_SKIP_PERMISSIONS flag to all 3 CLI spawn paths)
- `c2db125` — FOUND (test(71-01): add flag presence assertions for all 3 CLI spawn paths)
