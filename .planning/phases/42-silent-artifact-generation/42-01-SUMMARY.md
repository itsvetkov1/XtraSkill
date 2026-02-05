---
phase: 42-silent-artifact-generation
plan: 01
subsystem: backend-api
tags: [streaming, sse, artifact-generation, deduplication, pydantic]

dependency-graph:
  requires:
    - phase-40 (prompt engineering deduplication rules)
    - phase-41 (structural history filtering)
  provides:
    - ChatRequest.artifact_generation field for silent mode
    - Conditional message persistence (skip user+assistant save)
    - SSE text_delta suppression in silent mode
    - Ephemeral in-memory instruction for artifact-only generation
  affects:
    - 42-02 (frontend generateArtifact function will call this endpoint with flag)
    - 42-03 (integration testing of full silent generation pipeline)

tech-stack:
  added: []
  patterns:
    - conditional-persistence (flag-based message save skip)
    - sse-event-filtering (selective event suppression in generator)
    - ephemeral-context (in-memory conversation append, not persisted)

key-files:
  created: []
  modified:
    - backend/app/routes/conversations.py

decisions:
  - id: DEC-42-01-01
    decision: "text_delta is the only SSE event suppressed in silent mode"
    rationale: "message_complete needed for usage tracking, artifact_created for frontend state, tool_executing for UX feedback, error for debugging"
  - id: DEC-42-01-02
    decision: "Ephemeral instruction appended to conversation context in-memory only"
    rationale: "Guides model to generate artifact without conversational text, never persisted to DB"
  - id: DEC-42-01-03
    decision: "Token tracking remains unconditional in silent mode"
    rationale: "Per ERR-04 requirement - all API calls must be tracked for budget enforcement"

metrics:
  duration: "~2 minutes"
  completed: "2026-02-05"
  tasks: 1/1
  tests-passed: 13/13
---

# Phase 42 Plan 01: Silent Artifact Generation Backend Support Summary

**One-liner:** ChatRequest flag-gated conditional persistence, SSE text_delta suppression, and ephemeral instruction append for silent artifact generation mode.

## What Was Done

### Task 1: Extend ChatRequest and add conditional persistence with event filtering

Modified `backend/app/routes/conversations.py` with 8 targeted changes:

1. **ChatRequest model**: Added `artifact_generation: bool = Field(default=False)` -- opt-in flag, backward-compatible.

2. **Conditional user message save**: Wrapped `save_message(db, thread_id, "user", ...)` in `if not body.artifact_generation` guard.

3. **Ephemeral instruction**: When `artifact_generation=True`, appends an in-memory-only user message to the conversation context instructing the model to generate the artifact silently (no conversational text, just tool call).

4. **text_delta suppression**: Added `continue` guard that skips yielding `text_delta` events when in silent mode. All other events (message_complete, artifact_created, tool_executing, error) pass through.

5. **Conditional text accumulation**: Only accumulates streamed text when NOT in silent mode (optimization -- text won't be saved anyway).

6. **Conditional assistant message save**: Wrapped `save_message(db, thread_id, "assistant", ...)` in `if not body.artifact_generation` guard.

7. **Conditional summary update**: Wrapped `maybe_update_summary()` in `if not body.artifact_generation` guard.

8. **Error logging**: Added `logger.error()` for silent generation failures with thread context for debugging.

### What Was NOT Changed (by design)

- Token tracking remains unconditional (budget enforcement in all modes)
- Thread activity timestamp update remains unconditional
- `validate_thread_access` and `check_user_budget` remain unchanged
- `delete_message` endpoint remains unchanged

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| ChatRequest accepts artifact_generation (default=False) | PASS |
| Normal chat flow unaffected | PASS (13/13 existing tests) |
| Silent mode skips user message save | PASS (conditional guard) |
| Silent mode skips assistant message save | PASS (conditional guard) |
| text_delta suppressed in silent mode | PASS (continue guard) |
| message_complete/artifact_created preserved | PASS (no guard on these) |
| Token tracking unconditional | PASS (no artifact_generation check) |
| Summary update skipped in silent mode | PASS (conditional guard) |
| Error logging for silent failures | PASS (logger.error in except) |

## Commits

| Hash | Message |
|------|---------|
| 6893ee2 | feat(42-01): add silent artifact generation support to streaming endpoint |

## Next Phase Readiness

Plan 42-02 (frontend generateArtifact function) can now proceed. The backend endpoint accepts `artifact_generation: true` in the ChatRequest body and handles all conditional behavior. The frontend needs to:
- Create a `generateArtifact()` function separate from `sendMessage()`
- Send requests with `artifact_generation: true` in the JSON body
- Handle the reduced SSE event stream (no text_delta, still gets artifact_created and message_complete)
