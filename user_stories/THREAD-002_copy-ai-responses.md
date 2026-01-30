# THREAD-002: Add Copy Functionality for AI Responses

**Priority:** Critical
**Status:** Open
**Component:** Message Bubble

---

## User Story

As a user,
I want to easily copy AI-generated content,
So that I can paste artifacts into other tools.

---

## Problem

Message Bubble has "Selectable text" but no explicit copy button. Mobile users struggle to select/copy long responses.

---

## Acceptance Criteria

- [ ] Copy icon button visible on all assistant messages
- [ ] Long-press menu includes "Copy" option (alongside Delete)
- [ ] Copy action copies full message to clipboard
- [ ] Snackbar confirms "Copied to clipboard"

---

## Technical References

- `frontend/lib/screens/conversation/widgets/message_bubble.dart`
