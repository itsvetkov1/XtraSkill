# SKILL-003: Backend Enforcement of Skill Selection

**Priority:** High
**Status:** Open
**Component:** Backend / Skills API / Chat Route
**Source:** ASSISTANT_FLOW_REVIEW.md — GAP-03

---

## User Story

As a developer,
I want the backend to enforce skill selection end-to-end,
So that the skill browser UI and the runtime behavior are connected, not just cosmetic.

---

## Problem

`backend/app/routes/skills.py` serves skill metadata for the browser UI. But once a skill is selected:

1. The skill name is NOT sent on the `/chat` request
2. The skill is NOT persisted on the thread (addressed by SKILL-001)
3. The backend cannot enforce "apply this skill's system prompt" (addressed by SKILL-002)
4. The backend cannot enforce "only use tools defined in this skill" (this story)

This story covers the API contract: ensuring the chat request carries skill context and the backend validates it.

---

## Acceptance Criteria

- [ ] The `/threads/{id}/chat` endpoint accepts an optional `skill_id` field in the request body
- [ ] If `skill_id` is provided, the backend validates it exists in the skill registry
- [ ] If `skill_id` is provided but the thread already has a different skill bound, return 400 with clear error message
- [ ] If the skill defines specific tools, only those tools are available to the LLM (future — when assistant threads gain tool support)
- [ ] API error responses include the skill name and the expected skill for the thread

---

## Technical References

- `backend/app/routes/skills.py` — Skill metadata API
- `backend/app/routes/conversations.py` — Chat endpoint (needs skill_id in request schema)
- `backend/app/services/ai_service.py` — Where skill context should be validated
- Depends on: SKILL-001 (thread must have skill column)

---

## Related

- SKILL-001: Bind selected skill to thread (prerequisite)
- SKILL-002: Inject skill system prompt (prerequisite)

---

*Created: 2026-02-25*
*Source: Architecture review — assistant flow gaps*
