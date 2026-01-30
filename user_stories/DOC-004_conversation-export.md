# DOC-004: Document Conversation Export Feature

**Priority:** Medium
**Status:** Open
**Component:** Conversation Screen (Documentation)

---

## User Story

As a user,
I want to export an entire conversation thread,
So that I can share or archive the full discussion.

---

## Problem

Feature Summary mentions "Export to Markdown, PDF, Word" but ConversationScreen doesn't show how to export full thread.

---

## Acceptance Criteria

- [ ] Clarify: Is this per-artifact or per-thread export?
- [ ] If per-thread: Add export button to ConversationScreen AppBar
- [ ] Document export flow in spec
- [ ] Export includes: all messages, timestamps, mode, artifacts

---

## Technical References

- `frontend/lib/screens/conversation/conversation_screen.dart`
- `backend/app/services/export_service.py`
