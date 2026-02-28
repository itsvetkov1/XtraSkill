# BUG-016: Artifact Generation Multiplies on Repeated Requests

**Priority:** Critical
**Status:** Done

**Resolution:** Marker-based fix implemented. See commit f36d456 on minimax branch.
**Component:** Agent / Artifact Generation

---

## User Story

As a user, I want each artifact generation request to produce exactly one artifact,
so that I don't have to manually delete duplicates after every generation attempt.

---

## Problem

When a user sends an artifact generation request (via the "Generate Artifact" button
or by typing a trigger phrase like "generate user stories"), the app generates
multiple artifacts instead of one. The count of generated artifacts increases with
each successive attempt within the same thread — observed pattern: 1st attempt = 1
artifact, 2nd attempt = 2 artifacts, 3rd attempt = 3, and so on up to 6 observed.

The user stopped the generation on the 6th attempt because it appeared to be an
infinite loop.

### Root Cause

The issue is in the backend pipeline, not the frontend. Every chat request rebuilds
the full conversation context by loading **all** messages in the thread with no
filtering (`conversation_service.py:94-101`). This entire history — including all
prior artifact generation requests and their responses — is flattened into a single
prompt and sent to the model.

**NOTE:** The active service is `ai_service.py`, NOT `agent_service.py`.
- `agent_service.py` uses Claude Agent SDK but is **dead code** (never wired to routes)
- `ai_service.py` uses direct `anthropic` package with hardcoded `SYSTEM_PROMPT`
- See `backend/tests/test_service_architecture.py` for verification tests

The system prompt (`ai_service.py:114-617`) and the `SAVE_ARTIFACT_TOOL` description
(`ai_service.py:649-683`) contain instructions about when to use the tool, but there
is no instruction telling the model to **ignore prior generation requests already
present in the conversation history**. The model has no way to distinguish between
"this request was already fulfilled in a previous turn" and "this is a new, pending
request."

As a result, when the model sees N prior generation requests in the history, it
treats them as N actionable requests and attempts to generate N artifacts. The
tool loop in `ai_service.py:773-875` continues until no more tool calls are made,
but does not prevent the accumulation effect across turns.

### Reproduction Steps

1. Open any thread (project or project-less)
2. Click the artifact generation button (e.g. "User Stories") or type a generation
   request
3. If the first attempt fails or produces an artifact, send another generation
   request in the **same thread**
4. Observe that the second attempt generates 2 artifacts
5. Repeat — each subsequent attempt generates one more artifact than the last

### Affected Files

- `backend/app/services/conversation_service.py` — `build_conversation_context()`
  loads all messages without filtering or marking fulfilled requests
- `backend/app/services/ai_service.py` — `stream_chat()` flattens full history
  into a single prompt; `SAVE_ARTIFACT_TOOL` description lacks "only latest request"
  semantics; `SYSTEM_PROMPT` (hardcoded XML) has no rule to skip prior artifact
  requests
- `backend/app/routes/conversations.py` — route handler passes unfiltered context
  to AIService

**Dead code (not used):**
- `backend/app/services/agent_service.py` — Claude Agent SDK approach, never wired
- `.claude/business-analyst/SKILL.md` — Not loaded at runtime

---

## Acceptance Criteria

- [ ] Sending a single artifact generation request produces exactly one artifact
- [ ] Sending a second generation request in the same thread produces exactly one
      new artifact, regardless of how many prior requests exist in history
- [ ] Previously fulfilled generation requests in conversation history do not cause
      the model to re-generate artifacts
- [ ] Behavior is consistent across all artifact types (User Stories, Acceptance
      Criteria, Requirements Doc, Custom)
- [ ] Behavior is consistent whether the prior request succeeded or failed

---

## Technical References

**Active code path (direct API approach):**
- `backend/app/services/conversation_service.py:77-117` — `build_conversation_context()`
- `backend/app/services/ai_service.py:114-617` — `SYSTEM_PROMPT` (hardcoded XML)
- `backend/app/services/ai_service.py:649-683` — `SAVE_ARTIFACT_TOOL` definition
- `backend/app/services/ai_service.py:755-882` — `AIService.stream_chat()` with tool loop
- `backend/app/routes/conversations.py:85-211` — `/threads/{thread_id}/chat` endpoint

**Dead code (Agent SDK approach - not used):**
- `backend/app/services/agent_service.py` — Entire file unused
- `backend/app/services/skill_loader.py` — Only imported by agent_service
- `.claude/business-analyst/SKILL.md` — Not loaded at runtime

**Architecture verification:**
- `backend/tests/test_service_architecture.py` — 10 tests confirming active approach
