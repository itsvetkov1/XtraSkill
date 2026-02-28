# BUDGET-001: Design Token Budget Exhaustion UX

**Priority:** High
**Status:** Done
**Component:** Settings Screen, Conversation Screen

---

## User Story

As a user,
I want clear feedback when approaching or reaching my token budget limit,
So that I'm not surprised by blocked functionality.

---

## Problem

Settings shows usage bar but no specification for what happens at limit. User may hit cryptic errors.

---

## Acceptance Criteria

- [ ] Warning banner at 80% usage: "You've used 80% of your budget"
- [ ] Warning banner at 95% usage: "Almost at limit - X messages remaining (estimate)"
- [ ] At 100%: Clear "Budget exhausted" state in ConversationScreen
- [ ] Exhausted state: Can view history, cannot send new messages
- [ ] Message explaining reset period or upgrade path
- [ ] Graceful API error handling (not generic error)

---

## Technical References

- `frontend/lib/screens/settings_screen.dart`
- `frontend/lib/screens/conversation/conversation_screen.dart`
- `backend/app/routes/conversations.py`
