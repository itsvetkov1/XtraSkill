# THREAD-009: Clarify Message Count Definition

**Priority:** Medium
**Status:** Open
**Component:** Thread List Screen (Documentation)

---

## User Story

As a user,
I want to understand what the message count means,
So that I can gauge thread length.

---

## Problem

Thread list shows "message count" but spec doesn't define if it's total, user-only, or includes AI.

---

## Acceptance Criteria

- [ ] Update spec: "Message count includes both user and assistant messages"
- [ ] Format in UI: "12 messages" (total) or "6 exchanges" (pairs)
- [ ] Consistent with actual implementation

---

## Technical References

- `frontend/lib/screens/threads/thread_list_screen.dart`
- `.planning/APP-FEATURES-AND-FLOWS.md`
