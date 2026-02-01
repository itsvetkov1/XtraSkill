# BUG-012: Chats Screen Stuck Loading State

**Priority:** Critical
**Status:** Open
**Component:** Frontend - ChatsScreen
**Discovered:** 2026-02-01 (Phase 26 testing)

---

## Problem

The Chats screen shows a constant spinner in the middle and fails to properly display threads after:
1. Initial load
2. Page refresh
3. Navigation back to Chats

---

## Symptoms

1. Spinner never stops
2. Page refresh clears all chats and shows empty/error state
3. Threads that were just created don't appear

---

## Root Cause (Suspected)

After pagination fix (f188b9b), the loading state management may be broken:
1. `isLoading` not resetting properly
2. `hasMore` flag incorrect
3. Initial `loadThreads()` not completing

---

## Acceptance Criteria

- [ ] Initial load completes and hides spinner
- [ ] Page refresh reloads all threads correctly
- [ ] Loading states are accurate (loading during fetch, idle after)
- [ ] Error states only show on actual errors

---

## Technical References

- `frontend/lib/screens/chats_screen.dart`
- `frontend/lib/providers/chats_provider.dart`
- Commit f188b9b (pagination fix)

---

*Created: 2026-02-01*
