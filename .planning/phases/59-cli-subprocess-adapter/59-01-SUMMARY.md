---
phase: 59-cli-subprocess-adapter
plan: 01
subsystem: llm-adapter
tags: [asyncio, subprocess, json-streaming, claude-cli, mcp-tools]

# Dependency graph
requires:
  - phase: 57-claude-code-foundation
    provides: MCP tool definitions (search_documents, save_artifact) and LLMProvider.CLAUDE_CODE_CLI enum
  - phase: 58-agent-sdk-adapter
    provides: Agent provider routing pattern (is_agent_provider, set_context), StreamChunk.metadata field
provides:
  - ClaudeCLIAdapter.stream_chat() subprocess-based implementation with JSON event translation
  - Subprocess lifecycle management (terminate → kill cleanup) preventing zombie processes
  - CLI availability verification at init time with clear error messages
  - ContextVar-based MCP tool context propagation (POC approach)
affects: [60-evaluation, testing, production-hardening]

# Tech tracking
tech-stack:
  added: []  # No new dependencies - uses stdlib asyncio, json, shutil
  patterns:
    - "Async subprocess lifecycle with try/finally cleanup"
    - "Line-delimited JSON stream parsing from stdout"
    - "Event translation layer mapping CLI events to StreamChunk format"
    - "Agent provider pattern reuse (is_agent_provider=True for AIService routing)"

key-files:
  created: []
  modified:
    - backend/app/services/llm/claude_cli_adapter.py
    - backend/tests/unit/llm/test_claude_cli_adapter.py

key-decisions:
  - "Use combined prompt approach (prepend system prompt to user prompt) instead of --system-prompt flag for POC"
  - "Exclude --include-partial-messages from CLI flags (deferred to production scope)"
  - "Track received_result flag to prevent duplicate completion chunks"
  - "Use ContextVars for MCP tool context (subprocess inherits context in-process for POC)"

patterns-established:
  - "Subprocess cleanup protocol: terminate() → wait(5s) → kill() if timeout"
  - "JSON event parsing with JSONDecodeError handling and debug logging for unhandled types"
  - "Tool status metadata emission for user-friendly indicators (search_documents, save_artifact)"

# Metrics
duration: 212s
completed: 2026-02-14
---

# Phase 59 Plan 01: CLI Subprocess Adapter Summary

**AsyncIO subprocess spawning CLI with stream-json output, robust process cleanup, and 4-event-type JSON translation to StreamChunk format**

## Performance

- **Duration:** 3 min 32 sec (212 seconds)
- **Started:** 2026-02-14T15:26:10Z
- **Completed:** 2026-02-14T15:29:42Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Full ClaudeCLIAdapter.stream_chat() implementation replacing NotImplementedError stub
- Subprocess lifecycle management with zombie process prevention (terminate/kill in finally block)
- JSON event translation for all 4 CLI event types (stream_event, assistant_message, result, error)
- CLI availability verification at init with clear RuntimeError if not in PATH
- Zero regressions - all 241 unit tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement ClaudeCLIAdapter with subprocess lifecycle and JSON event translation** - `7a88a3c` (feat)
2. **Task 2: Verify adapter integrates with existing factory and AIService routing** - `112686b` (test)

## Files Created/Modified
- `backend/app/services/llm/claude_cli_adapter.py` - Replaced stub with full implementation (331 insertions, 17 deletions)
- `backend/tests/unit/llm/test_claude_cli_adapter.py` - Updated tests to mock CLI availability, removed NotImplementedError test (26 insertions, 17 deletions)

## Decisions Made

**1. Combined prompt approach for POC**
- Prepend system prompt to user prompt with `[SYSTEM]:` and `[USER]:` delimiters
- Rationale: Simpler than --system-prompt flag, allows CLI to interpret tool descriptions inline
- Impact: POC-appropriate, production may use --system-prompt for cleaner separation

**2. Exclude --include-partial-messages flag**
- Not passed to CLI subprocess
- Rationale: Partial message streaming deferred to production scope per plan
- Impact: Complete events only, acceptable for POC quality comparison

**3. Track received_result flag**
- Prevents duplicate completion chunks when CLI emits result event
- Rationale: Avoid double-counting usage tokens and duplicate metadata
- Impact: Correct usage reporting, clean event stream

**4. ContextVar for MCP tool context**
- Use _db_context, _project_id_context, _thread_id_context from mcp_tools.py
- Rationale: Subprocess runs in same process, ContextVars accessible
- Impact: POC-appropriate, production subprocess would need HTTP MCP server

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed research patterns precisely.

## User Setup Required

None - no external service configuration required. CLI availability verified at runtime with clear error message if missing.

## Next Phase Readiness

**Ready for Phase 60 (Evaluation):**
- ClaudeCLIAdapter fully functional, matches ClaudeAgentAdapter interface
- Both adapters (SDK and CLI) use same agent provider routing in AIService
- Zero test regressions, all 241 unit tests pass
- POC limitations documented (partial messages, MCP context via ContextVar)

**Known limitations for production hardening:**
- MCP tool context via ContextVar (works for POC, production subprocess needs HTTP transport)
- No --include-partial-messages flag (complete events only)
- Combined prompt approach (system prompt prepended to user prompt)
- No hard timeout on subprocess (per locked decision: no request timeout for POC)

**Quality comparison metrics to track in Phase 60:**
- Multi-turn conversation handling (SDK vs CLI agent loops)
- Event stream completeness (any CLI events lost in translation?)
- Source attribution accuracy (documents_used tracking)
- Token usage reporting (input/output token counts)
- Subprocess overhead (memory usage, process cleanup verification)

## Self-Check: PASSED

All files verified:
- backend/app/services/llm/claude_cli_adapter.py
- backend/tests/unit/llm/test_claude_cli_adapter.py

All commits verified:
- 7a88a3c (Task 1: feat)
- 112686b (Task 2: test)

---
*Phase: 59-cli-subprocess-adapter*
*Completed: 2026-02-14*
