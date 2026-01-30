# THREAD-001: Add Retry Mechanism for Failed AI Messages

**Priority:** Critical
**Status:** Done
**Component:** Conversation Screen
**Completed:** 2026-01-30 (v1.6)

---

## User Story

As a user,
I want to retry a failed AI request without retyping my message,
So that network issues don't waste my effort.

---

## Problem

Error banner only shows "Dismiss" - no way to retry. User must retype their message if AI response fails.

---

## Acceptance Criteria

- [x] Error banner shows "Dismiss | Retry" actions
- [x] Retry resends the last user message
- [x] ConversationProvider stores last sent message for retry
- [x] Works for both network errors and API errors

---

## Technical References

- `frontend/lib/screens/conversation/conversation_screen.dart`
- `frontend/lib/providers/conversation_provider.dart`
