# THREAD-007: Add Dedicated Artifact Generation UI

**Priority:** High
**Status:** Done
**Component:** Conversation Screen

---

## User Story

As a user,
I want a clear way to generate and manage artifacts,
So that I don't have to remember specific prompts.

---

## Problem

Artifact generation requires typing specific phrases. No dedicated UI, no artifact management, export is unclear.

---

## Acceptance Criteria

- [ ] "Generate Artifact" button/FAB in ConversationScreen
- [ ] Artifact type picker: User Stories, Acceptance Criteria, BRD, Custom
- [ ] Generated artifacts visually distinct from chat (card/section)
- [ ] Each artifact has inline export buttons (Markdown, PDF, Word)
- [ ] Artifacts section/tab for viewing all generated artifacts

---

## Technical References

- `frontend/lib/screens/conversation/conversation_screen.dart`
- `backend/app/services/export_service.py`
