---
phase: 31
plan: 02
subsystem: frontend-testing
tags: [flutter, unit-tests, providers, mockito, document, thread]
requires: [31-01]
provides: [document-provider-tests, thread-provider-tests]
affects: [31-03, 31-04, 31-05]
tech-stack:
  added: []
  patterns: [upload-progress-testing, filtered-getter-testing]
key-files:
  created:
    - frontend/test/unit/providers/document_provider_test.dart
    - frontend/test/unit/providers/document_provider_test.mocks.dart
    - frontend/test/unit/providers/thread_provider_test.dart
    - frontend/test/unit/providers/thread_provider_test.mocks.dart
  modified: []
decisions:
  - id: doc-progress-callback
    choice: Test upload progress by capturing onSendProgress callback
    rationale: Allows simulating progress updates and asserting mid-upload state
  - id: filtered-threads-testing
    choice: Test filteredThreads getter with all 3 sort options and search queries
    rationale: Getter encapsulates complex filtering/sorting logic needing thorough coverage
  - id: skip-delete-timer
    choice: Skip timer-based undo/commit testing for delete operations
    rationale: Requires BuildContext and Timer which are difficult to mock in unit tests
metrics:
  duration: 8 minutes
  completed: 2026-02-02
---

# Phase 31 Plan 02: Document and Thread Provider Tests Summary

DocumentProvider and ThreadProvider unit tests with upload progress tracking and search/sort filtering verification.

## What Was Done

### Task 1: DocumentProvider Unit Tests
Created comprehensive unit tests for DocumentProvider covering:

1. **Initial State** (6 tests)
   - Empty documents list, no selected document, loading/uploading false
   - No error, uploadProgress 0

2. **loadDocuments** (4 tests)
   - Sets loading during call
   - Updates documents on success
   - Sets error on failure
   - Clears previous documents on new load

3. **uploadDocument** (5 tests)
   - Sets uploading true during upload
   - **Tracks upload progress via onSendProgress callback** - Key feature
   - Adds document to beginning of list on success
   - Resets uploadProgress to 0 after completion
   - Sets error and rethrows on failure

4. **selectDocument** (3 tests)
   - Loads document content and sets selectedDocument
   - Sets loading during call
   - Sets error on failure

5. **clearSelectedDocument/clearError** (2 tests)
   - Verify state reset and listener notification

6. **searchDocuments** (3 tests)
   - Returns search results on success
   - Does NOT modify documents list (key behavior)
   - Sets error and rethrows on failure

7. **notifyListeners** (3 tests)
   - Verifies listeners notified on state changes

**Total: 27 test cases, 438 lines**

### Task 2: ThreadProvider Unit Tests
Created comprehensive unit tests for ThreadProvider covering:

1. **Initial State** (7 tests)
   - Empty threads, no selected, loading false, no error
   - Empty searchQuery, sortOption = newest, empty filteredThreads

2. **loadThreads** (4 tests)
   - Sets loading during call
   - Updates threads on success
   - Rethrows error (different from DocumentProvider which swallows)
   - Sets error message on failure

3. **createThread** (5 tests)
   - Adds thread to beginning of list
   - Returns thread on success
   - Passes optional provider parameter
   - Rethrows error on failure

4. **selectThread** (4 tests)
   - Loads thread with messages
   - Sets selectedThread on success
   - Rethrows error on failure

5. **renameThread** (4 tests)
   - Updates thread in list
   - Updates selectedThread if same thread renamed
   - Returns thread on success
   - Sets error and returns null on failure (does NOT rethrow)

6. **clearThreads** (1 test)
   - Resets all state including search/sort

7. **setSearchQuery/clearSearch** (4 tests)
   - Updates searchQuery
   - Notifies listeners

8. **setSortOption** (2 tests)
   - Updates sortOption, notifies listeners

9. **filteredThreads** (9 tests)
   - **Filters by search query case-insensitively**
   - Returns all threads when query empty
   - **Sorts by newest** (updatedAt desc) - default
   - **Sorts by oldest** (updatedAt asc)
   - **Sorts alphabetically** (title asc)
   - Combines filter and sort correctly
   - Uses lastActivityAt when available
   - Handles null titles in alphabetical sort

10. **notifyListeners** (3 tests)
    - Verifies listeners notified appropriately

**Total: 45 test cases, 750 lines**

### Task 3: Mock Generation
- Generated MockDocumentService via @GenerateNiceMocks annotation
- Generated MockThreadService via @GenerateNiceMocks annotation
- Verified all 72 tests pass together

## Key Testing Patterns

### Upload Progress Callback Testing
```dart
test('tracks upload progress via onSendProgress callback', () async {
  ProgressCallback? capturedCallback;
  when(mockService.uploadDocument(
    any, any, any,
    onSendProgress: anyNamed('onSendProgress'),
  )).thenAnswer((invocation) async {
    capturedCallback = invocation.namedArguments[#onSendProgress];
    capturedCallback?.call(50, 100);
    expect(provider.uploadProgress, equals(0.5));
    capturedCallback?.call(100, 100);
    expect(provider.uploadProgress, equals(1.0));
    return Document(...);
  });
  await provider.uploadDocument('project-1', [1,2,3], 'test.txt');
});
```

### filteredThreads Getter Testing
```dart
test('sorts by newest (default) - updatedAt descending', () async {
  when(mockService.getThreads('project-1'))
      .thenAnswer((_) async => threads);
  await provider.loadThreads('project-1');

  expect(provider.sortOption, equals(ThreadSortOption.newest));
  final sorted = provider.filteredThreads;

  // Beta (Jan 3), Charlie (Jan 2), Alpha (Jan 1)
  expect(sorted[0].title, equals('Beta'));
  expect(sorted[1].title, equals('Charlie'));
  expect(sorted[2].title, equals('Alpha'));
});
```

## Verification Results

| Verification Step | Result |
|------------------|--------|
| DocumentProvider tests pass | 27 tests PASS |
| ThreadProvider tests pass | 45 tests PASS |
| Upload progress tracking tested | Callback captured and asserted |
| Search filtering tested | Case-insensitive matching verified |
| Sort options tested | newest/oldest/alphabetical all covered |
| Combined tests pass | 72 tests PASS |
| All providers tests pass | 243 tests PASS |

## Success Criteria Met

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| DocumentProvider test cases | 12+ | 27 | PASS |
| ThreadProvider test cases | 15+ | 45 | PASS |
| Upload progress callback testing | Yes | Implemented | PASS |
| filteredThreads getter tested | 3 sort options + search | All covered | PASS |
| All tests pass | flutter test | 72/72 pass | PASS |

## Deviations from Plan

None - plan executed exactly as written.

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| document_provider_test.dart | 438 | DocumentProvider unit tests |
| document_provider_test.mocks.dart | ~127 | Generated MockDocumentService |
| thread_provider_test.dart | 750 | ThreadProvider unit tests |
| thread_provider_test.mocks.dart | ~216 | Generated MockThreadService |

## Next Phase Readiness

**Ready for 31-03:** ProjectProvider and SettingsProvider tests
- Same testing pattern established
- Mockito mock generation working
- No blockers

## Commits

| Hash | Message |
|------|---------|
| 66fb8ea | test(31-02): add DocumentProvider unit tests |
| 5307489 | test(31-02): add ThreadProvider unit tests |
