# THREAD-001: Add Retry Mechanism for Failed AI Messages

**Priority:** Critical
**Status:** Open
**Component:** Conversation Screen

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

- [ ] Error banner shows "Dismiss | Retry" actions
- [ ] Retry resends the last user message
- [ ] ConversationProvider stores last sent message for retry
- [ ] Works for both network errors and API errors

---

## Technical References

- `frontend/lib/screens/conversation/conversation_screen.dart`
- `frontend/lib/providers/conversation_provider.dart`
