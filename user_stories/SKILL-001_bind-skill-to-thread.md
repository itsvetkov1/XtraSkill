# SKILL-001: Bind Selected Skill to Thread at Runtime

**Priority:** Critical
**Status:** Open
**Component:** Backend / Thread Model / Skill System
**Source:** ASSISTANT_FLOW_REVIEW.md — GAP-01

---

## User Story

As a user,
I want my selected skill to persist on the thread,
So that the AI uses that skill's guidance across my entire conversation, even after page refresh.

---

## Problem

The Thread model has `thread_type` and `model_provider` but no `skill_id` or `skill_name` field. When a user selects a skill from the skill browser (shipped in v3.1), there is no database column to persist which skill was chosen. This means:

1. After page refresh, the skill selection is lost
2. The backend cannot load the correct system prompt for the thread
3. Token tracking cannot attribute cost to a specific skill
4. The skill selection exists only in transient frontend state

This is a prerequisite for SKILL-002 (injecting the skill prompt) and SKILL-003 (backend enforcement).

---

## Acceptance Criteria

- [ ] Thread model has a `selected_skill` column (nullable string — the skill identifier)
- [ ] When a user selects a skill before starting a conversation, the skill ID is stored on the Thread
- [ ] When a user opens an existing thread, the previously selected skill is shown in the UI
- [ ] The `/threads/{id}` API response includes the `selected_skill` field
- [ ] The `/threads/{id}/chat` request can accept an optional `skill_id` parameter
- [ ] Alembic migration adds the column without breaking existing threads (nullable, default NULL)

---

## Design Decision Needed

**When can the skill change?**

- **Option A:** Skill is locked at thread creation — cannot change mid-conversation. Simpler, matches the BA assistant pattern where `thread_type` is immutable.
- **Option B:** Skill can change per-message — store `skill_id` on each Message, not on Thread. More flexible but adds complexity to context building.

Recommendation: Start with Option A. If mid-conversation skill switching becomes a requirement, migrate to Option B later.

---

## Technical References

- `backend/app/models.py` — Thread model definition
- `backend/app/routes/threads.py` — Thread CRUD endpoints
- `backend/app/services/skill_loader.py` — Skill loading service (already exists)
- `frontend/lib/models/thread_model.dart` — Frontend Thread model
- `frontend/lib/screens/conversation/widgets/skill_browser.dart` — Skill selection UI

---

## Related

- SKILL-002: Inject skill system prompt into assistant threads
- SKILL-003: Backend enforcement of skill selection
- Blocks: ISSUE-01 from ASSISTANT_FLOW_REVIEW.md

---

*Created: 2026-02-25*
*Source: Architecture review — assistant flow gaps*
