# BUG-012: Chats Screen Stuck Loading State

**Priority:** Critical
**Status:** Done
**Component:** Frontend - ChatsScreen
**Discovered:** 2026-02-01 (Phase 26 testing)
**Fixed:** 2026-02-01

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

- [x] Initial load completes and hides spinner
- [x] Page refresh reloads all threads correctly
- [x] Loading states are accurate (loading during fetch, idle after)
- [x] Error states only show on actual errors

---

## Fix

1. Changed loading spinner condition to require both `!isInitialized` AND `isLoading`
2. Added `_isInitialized` flag to ChatsProvider
3. Fixed `_hasMore` initial state to `false`
4. Added duplicate load prevention guard

**ChatsScreen changes:**
```dart
// Show spinner during initial load (before initialization)
if (!provider.isInitialized && provider.isLoading) {
  return const Center(child: CircularProgressIndicator());
}
```

**ChatsProvider changes:**
```dart
Future<void> loadThreads() async {
  // Prevent duplicate loads
  if (_isLoading) return;
  // ...
  _isInitialized = true;
}
```

**Tests:**
- `frontend/test/widget/chats_screen_test.dart` - Widget tests
- `frontend/test/unit/chats_provider_test.dart` - Provider unit tests

---

## Technical References

- `frontend/lib/screens/chats_screen.dart` (FIXED)
- `frontend/lib/providers/chats_provider.dart` (FIXED)
- Commit f188b9b (pagination fix - base commit)

---

*Created: 2026-02-01*
*Fixed: 2026-02-01*
