# BUG-011: Chats Screen Not Showing Project-less Conversations

**Priority:** Critical
**Status:** Open
**Component:** Frontend - ChatsScreen / ChatsProvider
**Discovered:** 2026-02-01 (Phase 26 testing)

---

## Problem

The Chats screen is not displaying project-less conversations. Only project-based threads appear in the list.

API returns both types correctly (verified via Network tab), but frontend only renders project-based threads.

---

## Symptoms

1. Project-less chats created from Home/Chats don't appear in list
2. Constant spinner visible in middle of screen
3. After page refresh, shows "No chats" error state even when chats exist

---

## Root Cause (Suspected)

Possible issues:
1. ChatsProvider state not updating correctly after pagination fix
2. Thread filtering logic excluding project-less threads
3. hasMore flag causing infinite loading state

---

## Acceptance Criteria

- [ ] All threads (project-less and project-based) display in Chats list
- [ ] No stuck loading spinner
- [ ] Page refresh correctly loads and displays all chats
- [ ] Empty state only shows when truly no chats exist

---

## Technical References

- `frontend/lib/screens/chats_screen.dart`
- `frontend/lib/providers/chats_provider.dart`
- `frontend/lib/services/thread_service.dart`

---

*Created: 2026-02-01*
