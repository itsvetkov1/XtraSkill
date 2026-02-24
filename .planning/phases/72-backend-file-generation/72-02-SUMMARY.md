---
phase: 72-backend-file-generation
plan: "02"
subsystem: backend
tags: [mcp, claude-cli, artifact-generation, session-lifecycle, sse]
dependency_graph:
  requires:
    - phase: 72-01
      provides: FastMCP server at /mcp, session registry (register_mcp_session/unregister_mcp_session), ArtifactType.GENERATED_FILE
  provides:
    - --mcp-config and --tools '' flags in all 3 CLI spawn paths (warm pool, cold spawn, no-pool direct)
    - ARTIFACT_CREATED marker detection in _translate_event() returning StreamChunk metadata
    - ASSISTANT_FILE_GEN_PROMPT constant with session_token placeholder
    - artifact_generation parameter threaded from conversations.py -> stream_chat() -> _stream_agent_chat()
    - MCP session lifecycle (register before stream, unregister in finally)
  affects:
    - frontend/lib (consumes artifact_created SSE event)
    - backend/app/services/llm/claude_cli_adapter.py
    - backend/app/services/ai_service.py
    - backend/app/routes/conversations.py
tech_stack:
  added: []
  patterns:
    - artifact_generation bool parameter threaded top-to-bottom without touching BA code path
    - session_token initialized before try block so finally can always clean up (even on pre-stream errors)
    - ARTIFACT_CREATED marker scanned from CLI result text (mirrors existing mcp_tools.py protocol)
key_files:
  created: []
  modified:
    - backend/app/services/llm/claude_cli_adapter.py
    - backend/app/services/ai_service.py
    - backend/app/routes/conversations.py
decisions:
  - "Session token initialized before try block so finally cleanup is guaranteed even when setup fails"
  - "Outer try/except/finally pattern (not nested) keeps session lifecycle simple and readable"
  - "--mcp-config applied universally to all spawn paths; BA threads ignore MCP since their prompt doesn't reference it"
patterns_established:
  - "Pattern: Module constant for MCP config JSON (MCP_CONFIG_JSON) — single source of truth for all spawn paths"
  - "Pattern: session_token = '' before try, set conditionally inside, cleaned in finally — ensures no leaked sessions"
requirements_completed: [GEN-01, GEN-02]
metrics:
  duration: 217s
  completed: "2026-02-24"
  tasks_completed: 2
  files_modified: 3
---

# Phase 72 Plan 02: End-to-End Wiring (CLI Adapter + AI Service + Conversations) Summary

**artifact_generation=true in POST body now triggers MCP-connected CLI subprocess with file-gen system prompt, session token registry, and ARTIFACT_CREATED SSE event back to the client.**

## Performance

- **Duration:** 217s (~3.6 min)
- **Started:** 2026-02-24T15:21:36Z
- **Completed:** 2026-02-24T15:25:13Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- All 3 CLI subprocess spawn paths (warm pool, cold spawn, no-pool direct) now include `--mcp-config` pointing to `http://127.0.0.1:8000/mcp` and `--tools ""` to disable built-in tools
- `_translate_event()` now scans `result` events for `ARTIFACT_CREATED:` markers and populates `StreamChunk.metadata`, completing the signal path from MCP tool call to SSE event
- `artifact_generation` parameter flows end-to-end: `conversations.py` -> `stream_chat()` -> `_stream_agent_chat()` with BA thread behavior completely unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: --mcp-config/--tools flags + ARTIFACT_CREATED detection** - `fd0b0b8` (feat)
2. **Task 2: artifact_generation threading + file-gen system prompt** - `9d160bf` (feat)

**Plan metadata:** (docs commit — see state updates below)

## Files Created/Modified

- `backend/app/services/llm/claude_cli_adapter.py` — Added MCP_SERVER_URL/MCP_CONFIG_JSON constants; added --mcp-config and --tools '' to _spawn_warm_process, _cold_spawn, and stream_chat fallback cmd; replaced _translate_event result branch with ARTIFACT_CREATED detection
- `backend/app/services/ai_service.py` — Added import uuid as _uuid; added ASSISTANT_FILE_GEN_PROMPT constant; updated _stream_agent_chat() and stream_chat() signatures to accept artifact_generation; added session lifecycle (register/unregister) around stream loop
- `backend/app/routes/conversations.py` — Updated stream_chat() call to pass artifact_generation=body.artifact_generation

## Decisions Made

1. **session_token initialized before try block:** The `session_token = ""` variable is set before the outer `try:` block so that the `finally: if session_token: unregister_mcp_session(session_token)` runs unconditionally even if an exception occurs during setup (e.g., in `set_context()` or `estimate_messages_tokens()`).

2. **Single outer try/except/finally (not nested):** The original code had one try/except. Rather than adding a nested try/except/finally inside it, the structure was kept as one flat try/except/finally. This is cleaner and the `session_token` guard handles the "wasn't set yet" case automatically.

3. **--mcp-config applied to all spawn paths universally:** BA assistant threads will also spawn with `--mcp-config` but their system prompt never mentions the `save_artifact` tool, so the MCP server is never called. This is simpler than conditional flag injection and matches the research guidance.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Indentation error when adding inner try block inside existing try**

- **Found during:** Task 2 (`_stream_agent_chat` modification)
- **Issue:** First edit attempt inserted `try:` inside the outer try block but left the async for loop body at incorrect indentation (not inside the new inner try). Python syntax error: `expected 'except' or 'finally' block`.
- **Fix:** Restructured to single outer `try/except/finally` with `session_token = ""` hoisted before the try block. Simpler and avoids nested-try complexity.
- **Files modified:** `backend/app/services/ai_service.py`
- **Verification:** `ast.parse()` returned no SyntaxError; all 5 plan verification checks passed.
- **Committed in:** `9d160bf` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** The structural change (hoisting session_token before try vs nested inner try) produces identical behavior. No scope creep.

## Issues Encountered

None beyond the indentation fix documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 72 (Backend File Generation) is complete — both plans done
- The full backend pipeline is wired: `artifact_generation=true` POST -> file-gen prompt with session token -> CLI subprocess with --mcp-config -> MCP save_artifact call -> ARTIFACT_CREATED marker in result -> artifact_created SSE event
- Phase 73 (Frontend File Generation) can now implement the Flutter-side `generateFile()` call and `artifact_created` event handler

---

*Phase: 72-backend-file-generation*
*Completed: 2026-02-24*

## Self-Check: PASSED

Files exist:
- `backend/app/services/llm/claude_cli_adapter.py` — FOUND (modified)
- `backend/app/services/ai_service.py` — FOUND (modified)
- `backend/app/routes/conversations.py` — FOUND (modified)

Commits exist:
- fd0b0b8 — FOUND (feat(72-02): add --mcp-config and --tools flags...)
- 9d160bf — FOUND (feat(72-02): thread artifact_generation through ai_service...)
