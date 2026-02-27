# BUG-024: Dead Code — AgentService Not Wired into Production Path

**Priority:** High
**Status:** Done
**Component:** Backend / Services / Agent Service
**Discovered:** 2026-02-25

---

## User Story

As a developer,
I want dead code removed from the codebase,
So that I can trust every file in the project is part of the running system.

---

## Problem

`AgentService` in `backend/app/services/agent_service.py` implements the Claude Agent SDK streaming flow with MCP tools — the same flow that `ClaudeAgentAdapter` implements. However, `AgentService` is **not instantiated by any route**. `conversations.py` uses `AIService` exclusively.

This creates:

1. **Maintenance double burden** — two places to update when Agent SDK behavior changes
2. **Developer confusion** — unclear which code path is active in production
3. **Behavioral divergence** — `AgentService` has `max_turns=3` while `ClaudeAgentAdapter` has no turn limit. If someone accidentally wires in the wrong path, behavior silently differs

### Evidence

```
conversations.py → uses AIService
AIService → uses ClaudeAgentAdapter (for claude-code-sdk provider)
AgentService → NOT imported by any route module
```

---

## Acceptance Criteria

**Option A: Remove (recommended)**
- [ ] Delete `backend/app/services/agent_service.py`
- [ ] Remove any imports of `AgentService` elsewhere
- [ ] Verify no tests reference it (if they do, remove those too)

**Option B: Document as test harness**
- [ ] Add a prominent comment at the top: `# STANDALONE TEST HARNESS — not part of production request path`
- [ ] Move to `backend/tests/` or `backend/app/services/_experimental/`
- [ ] Document why it exists and when it should be used

---

## Technical References

- `backend/app/services/agent_service.py` — The dead code
- `backend/app/services/ai_service.py` — The active service (uses ClaudeAgentAdapter)
- `backend/app/services/llm/claude_agent_adapter.py` — The active Agent SDK adapter
- `backend/app/routes/conversations.py` — Route that uses AIService

---

*Created: 2026-02-25*
*Source: ASSISTANT_FLOW_REVIEW.md — ISSUE-02*
