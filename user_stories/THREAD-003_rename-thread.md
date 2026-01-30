# THREAD-003: Add Ability to Rename Thread After Creation

**Priority:** Critical
**Status:** Done
**Component:** Conversation Screen, Thread List
**Completed:** 2026-01-30 (v1.6)

---

## User Story

As a user,
I want to rename a conversation thread after starting it,
So that I can give it a meaningful name once the topic becomes clear.

---

## Problem

Thread title can only be set at creation. Users end up with many "Untitled" threads.

---

## Acceptance Criteria

- [x] Edit icon in ConversationScreen AppBar opens rename dialog
- [x] "Rename" option added to Thread List PopupMenu
- [x] Pre-fills current title in text field
- [x] Empty title defaults to "Untitled"

---

## Technical References

- `frontend/lib/screens/threads/thread_create_dialog.dart`
- `frontend/lib/screens/conversation/conversation_screen.dart`
- `frontend/lib/screens/threads/thread_list_screen.dart`
