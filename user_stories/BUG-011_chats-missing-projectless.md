# BUG-011: Chats Screen Not Showing Project-less Conversations

**Priority:** Critical
**Status:** Done
**Component:** Frontend - ChatsScreen / ChatsProvider
**Discovered:** 2026-02-01 (Phase 26 testing)
**Fixed:** 2026-02-01

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

- [x] All threads (project-less and project-based) display in Chats list
- [x] No stuck loading spinner
- [x] Page refresh correctly loads and displays all chats
- [x] Empty state only shows when truly no chats exist

---

## Fix

1. Added `_isInitialized` flag to ChatsProvider to track first load
2. Changed `_hasMore` initial value from `true` to `false`
3. Updated ChatsScreen to check initialization state before showing loading

**ChatsProvider changes:**
```dart
bool _isInitialized = false;
bool _hasMore = false; // Start false until first load confirms more pages
```

**Tests:**
- `backend/tests/test_global_threads.py` - API tests for global threads
- `frontend/test/widget/chats_screen_test.dart` - Widget tests
- `frontend/test/unit/chats_provider_test.dart` - Provider unit tests

---

## Technical References

- `frontend/lib/screens/chats_screen.dart` (FIXED)
- `frontend/lib/providers/chats_provider.dart` (FIXED)
- `frontend/lib/services/thread_service.dart`

---

*Created: 2026-02-01*
*Fixed: 2026-02-01*
