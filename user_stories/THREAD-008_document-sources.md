# THREAD-008: Show Which Documents AI Referenced

**Priority:** Medium
**Status:** Open
**Component:** Message Bubble, Conversation Screen

---

## User Story

As a user,
I want to see which documents the AI used in its response,
So that I can verify the source of information.

---

## Problem

AI shows "Searching documents..." status but response doesn't indicate which documents were referenced.

---

## Acceptance Criteria

- [ ] Assistant messages show source chips below content when documents were used
- [ ] Chips are clickable → open Document Viewer
- [ ] Format: "Sources: requirements.md, user-flows.txt"
- [ ] If no documents used, no chips shown

---

## Technical References

- `frontend/lib/screens/conversation/widgets/message_bubble.dart`
- `backend/app/services/document_search.py`
