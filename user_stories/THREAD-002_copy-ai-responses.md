# THREAD-002: Add Copy Functionality for AI Responses

**Priority:** Critical
**Status:** Done
**Component:** Message Bubble
**Completed:** 2026-01-30 (v1.6)

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

- [x] Copy icon button visible on all assistant messages
- [x] Long-press menu includes "Copy" option (alongside Delete)
- [x] Copy action copies full message to clipboard
- [x] Snackbar confirms "Copied to clipboard"

---

## Technical References

- `frontend/lib/screens/conversation/widgets/message_bubble.dart`
