# DELETE-001: Document Undo Behavior for Threads and Documents

**Priority:** High
**Status:** Done

**Resolution:** Already implemented. Both threads and documents have 10-second undo via SnackBar. Thread undo in `thread_provider.dart:241`, Document undo in `document_provider.dart:142`. Uses same pattern as project delete.
**Component:** Thread List, Document List

---

## User Story

As a user,
I want consistent undo behavior when deleting any resource,
So that I can recover from mistakes.

---

## Problem

Project delete has 10-second undo. Thread/document delete behavior not documented - may not have undo.

---

## Acceptance Criteria

- [ ] Clarify: Do threads/documents have undo? Document the decision
- [ ] If yes: Implement 10-second undo matching project behavior
- [ ] If no: Document why (e.g., cascade complexity) and ensure confirmation dialog is clear
- [ ] Update spec with consistent delete behavior section

---

## Technical References

- `frontend/lib/screens/threads/thread_list_screen.dart`
- `frontend/lib/screens/documents/document_list_screen.dart`
- `frontend/lib/widgets/delete_confirmation_dialog.dart`
