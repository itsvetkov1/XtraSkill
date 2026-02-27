# SKILL-002: Inject Skill System Prompt into Assistant Threads

**Priority:** Critical
**Status:** Open
**Component:** Backend / AI Service / Skill System
**Source:** ASSISTANT_FLOW_REVIEW.md — ISSUE-01, GAP-02

---

## User Story

As a user who selects a skill for my conversation,
I want the AI to actually follow that skill's instructions,
So that I get the specialized behavior the skill promises.

---

## Problem

This is the most critical finding from the assistant flow review. The v3.1 milestone shipped a skill browser UI and selection mechanism, but **selected skills are never injected into the runtime system prompt**. The system prompt for assistant threads is always empty:

```python
# ai_service.py line 931 — LOGIC-01
system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""
```

Every assistant conversation starts with a blank-slate Claude — no guidance, no persona, no constraints. The skill is purely a UI label with no backend effect.

The `skill_loader.py` service already exists and works. It loads skill SKILL.md content and returns it as a string. The problem is that **nobody calls it** in the assistant flow path.

---

## Acceptance Criteria

- [ ] When an assistant thread has a skill bound (via SKILL-001), the skill's system prompt is loaded at chat time
- [ ] The loaded skill prompt is passed to the CLI adapter as the system prompt
- [ ] Threads without a skill bound continue to work (empty system prompt, same as today)
- [ ] The skill prompt is visible in debug logs (at DEBUG level, not INFO — it may contain large text)
- [ ] BA assistant threads are NOT affected (they have their own system prompt logic)

---

## Design Decision: Prompt Injection Method

Three options identified in the review:

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Append** | Base system prompt + skill content appended | Allows shared instructions across skills | May conflict with skill instructions |
| **B: Replace** | Skill SKILL.md IS the entire system prompt | Clean, skill has full control | No shared guardrails across skills |
| **C: Context** | Skill content injected as first user message context | Works with any adapter | Not a true system prompt, weaker steering |

**Recommendation:** Option B for now. Skills should be self-contained. If shared guardrails become necessary, introduce a `_base_prompt.md` that skill authors include via a template.

---

## Implementation Notes

The fix is conceptually small — the plumbing already exists:

1. `skill_loader.py` can load skill content by name
2. `AIService.stream_chat()` already computes `system_prompt`
3. `ClaudeCLIAdapter` already accepts a system prompt parameter

The change: in the `else` branch of LOGIC-01, check if the thread has a `selected_skill`, load it via `skill_loader`, and use it as the system prompt.

---

## Technical References

- `backend/app/services/ai_service.py:931` — LOGIC-01, the empty system prompt branch
- `backend/app/services/skill_loader.py` — Existing skill loading service
- `backend/app/services/llm/claude_cli_adapter.py:264` — Where system prompt is assembled into CLI input
- Depends on: SKILL-001 (skill must be persisted on thread to load it)

---

## Related

- SKILL-001: Bind selected skill to thread (prerequisite)
- SKILL-003: Backend enforcement of skill selection
- ISSUE-01 from ASSISTANT_FLOW_REVIEW.md

---

*Created: 2026-02-25*
*Source: Architecture review — critical gap in assistant flow*
