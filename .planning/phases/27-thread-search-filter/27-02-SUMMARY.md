---
phase: 27
plan: 02
subsystem: frontend-thread-list
tags: [search, sort, flutter, provider, segmented-button]

requires:
  - 27-01 (ThreadSortOption enum)
provides:
  - Thread search/filter in project view
  - Thread sort options in project view
affects:
  - 27-03 (ChatsScreen search will follow same pattern)

tech-stack:
  added: []
  patterns:
    - SegmentedButton for sort options
    - SearchBar with clear button
    - filteredThreads computed getter

key-files:
  created:
    - frontend/test/widget/thread_list_screen_test.dart
    - frontend/test/widget/thread_list_screen_test.mocks.dart
  modified:
    - frontend/lib/providers/thread_provider.dart
    - frontend/lib/screens/threads/thread_list_screen.dart

decisions:
  - FILTER-PATTERN: Computed getter filteredThreads with in-memory filter/sort
  - SEARCH-SCOPE: Title-only search (case-insensitive)
  - SORT-OPTIONS: Newest (lastActivityAt), Oldest, Alphabetical (title)
  - STATE-RESET: clearThreads() resets search/sort to defaults
  - EMPTY-STATE: Distinguish "no threads" vs "no search matches"

metrics:
  duration: 4m
  completed: 2026-02-02
---

# Phase 27 Plan 02: Thread List Search/Sort Summary

**One-liner:** SearchBar and SegmentedButton for filtering/sorting project threads with immediate client-side filtering.

## What Was Done

### Task 1: Add filter state to ThreadProvider
- Added `_searchQuery` and `_sortOption` private fields
- Added `filteredThreads` computed getter with filter/sort logic
- Added `setSearchQuery`, `setSortOption`, `clearSearch` methods
- Updated `clearThreads()` to reset search/sort state

### Task 2: Add SearchBar and SegmentedButton UI to ThreadListScreen
- Added SearchBar with clear button for filtering by title
- Added SegmentedButton for sort options (Newest/Oldest/A-Z)
- Updated list to use `filteredThreads` instead of `threads`
- Added "No conversations matching 'X'" empty search state
- Updated date display to use `lastActivityAt`

### Task 3: Add Flutter tests
- Created 7 test cases covering search, sort, empty results, clear functionality
- All tests pass

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 8ab40c2 | feat | Add filter state to ThreadProvider |
| 3d4ebd1 | feat | Add SearchBar and SegmentedButton UI to ThreadListScreen |
| a61118d | test | Add Flutter tests for ThreadListScreen search/sort |

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

### Filter Implementation
```dart
List<Thread> get filteredThreads {
  var result = _threads.where((thread) {
    if (_searchQuery.isEmpty) return true;
    final title = thread.title?.toLowerCase() ?? '';
    return title.contains(_searchQuery.toLowerCase());
  }).toList();

  switch (_sortOption) {
    case ThreadSortOption.newest:
      result.sort((a, b) => (b.lastActivityAt ?? b.updatedAt)
          .compareTo(a.lastActivityAt ?? a.updatedAt));
    // ... other cases
  }
  return result;
}
```

### UI Pattern
- SearchBar with conditional trailing clear button
- SegmentedButton with showSelectedIcon: false for compact display
- Column layout: search controls at top, Expanded list below

## Verification Results

- `flutter analyze` - No new errors (existing print statements only)
- `flutter test test/widget/thread_list_screen_test.dart` - 7/7 pass

## Next Phase Readiness

Ready for 27-03 (ChatsScreen search/sort) - same pattern will apply:
1. Add search/sort state to ChatsProvider
2. Add filteredThreads getter to ChatsProvider
3. Add SearchBar and SegmentedButton to ChatsScreen
