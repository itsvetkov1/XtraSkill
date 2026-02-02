---
phase: 31-frontend-provider-service-tests
plan: 03
subsystem: frontend-provider-tests
tags: [unit-tests, flutter, providers, streaming, mockito]

dependency-graph:
  requires: [31-01, 31-02]
  provides: [ConversationProvider-tests, ChatsProvider-expansion]
  affects: [31-04, 31-05]

tech-stack:
  added: []
  patterns: [stream-mocking, SSE-event-testing, listener-notification-testing]

key-files:
  created:
    - frontend/test/unit/providers/conversation_provider_test.dart
    - frontend/test/unit/providers/conversation_provider_test.mocks.dart
  modified:
    - frontend/test/unit/chats_provider_test.dart

decisions:
  - id: stream-event-mocking
    choice: "Mock AIService.streamChat to return Stream.fromIterable with event sequence"
    rationale: "Synchronous stream testing without async complications"
  - id: listener-verification
    choice: "Count notifyListeners calls via addListener callback"
    rationale: "Standard Flutter pattern for ChangeNotifier testing"

metrics:
  duration: ~8 minutes
  completed: 2026-02-02
  tests-added: 53
---

# Phase 31 Plan 03: ConversationProvider & ChatsProvider Tests Summary

**One-liner:** ConversationProvider streaming tests with SSE event mocking and ChatsProvider edge case expansion.

## What Was Built

### ConversationProvider Tests (40 test cases)
New comprehensive test suite covering:
- **Initial State (9 tests):** null thread, empty messages, empty streamingText, null statusMessage, isStreaming false, loading false, no error, isNotFound false, canRetry false
- **loadThread (6 tests):** loading state, thread/messages on success, isNotFound on 404, error on failures, state reset on new load
- **sendMessage (5 tests):** null thread guard, streaming guard, optimistic user message, streaming state, retry content storage
- **Streaming events (7 tests):** TextDeltaEvent appends, ToolExecutingEvent sets status, MessageCompleteEvent adds message and clears state, ErrorEvent handling, exception handling
- **clearConversation (1 test):** Full state reset
- **clearError (3 tests):** Clears error, isNotFound, and _lastFailedMessage
- **canRetry (2 tests):** True only when both _lastFailedMessage and error set
- **retryLastMessage (2 tests):** Guard for null, removes duplicate user message
- **associateWithProject (3 tests):** Returns false if no thread, calls service, handles errors
- **Listener notifications (2 tests):** Notifies on loadThread and streaming

### ChatsProvider Tests Expansion (+13 test cases)
Extended existing test suite from 22 to 35 tests:
- **loadThreads edge cases (3 tests):** isLoading false after success/failure, threads replaced on reload
- **loadMoreThreads edge cases (2 tests):** No duplicate loads while loading, page increment verification
- **createNewChat edge cases (2 tests):** Works without initialization, increments total before first load
- **Listener notifications (5 tests):** Notifications for loadThreads, loadMoreThreads, createNewChat success/failure, clearError
- **Project association (1 test):** Handles projectId and projectName correctly

## Technical Approach

### Stream Event Testing Pattern
```dart
when(mockAIService.streamChat('t1', 'Hi')).thenAnswer((_) async* {
  yield TextDeltaEvent(text: 'Hello');
  yield TextDeltaEvent(text: ' World');
  yield MessageCompleteEvent(
    content: 'Hello World',
    inputTokens: 10,
    outputTokens: 20,
  );
});
```

### Listener Notification Testing
```dart
test('notifies listeners during streaming', () async {
  var notifyCount = 0;
  provider.addListener(() => notifyCount++);

  // ... trigger operations

  expect(notifyCount, greaterThanOrEqualTo(4));
});
```

## Verification Results

| Verification | Result |
|--------------|--------|
| ConversationProvider tests pass | 40/40 pass |
| ChatsProvider tests pass | 35/35 pass |
| SSE streaming events tested | Yes (TextDelta, ToolExecuting, MessageComplete, Error) |
| FPROV-05 covered | Yes |
| FPROV-06 covered | Yes |

## Artifacts

| File | Lines | Purpose |
|------|-------|---------|
| `conversation_provider_test.dart` | 594 | ConversationProvider unit tests |
| `conversation_provider_test.mocks.dart` | ~200 | Generated MockAIService, MockThreadService |
| `chats_provider_test.dart` | 862 | Expanded ChatsProvider tests |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| da476b2 | test | Add ConversationProvider unit tests (40 tests) |
| 2fd4381 | test | Expand ChatsProvider tests for FPROV-06 (+13 tests) |

## Deviations from Plan

None - plan executed exactly as written.

## Requirements Covered

- **FPROV-05:** MessagesProvider/ConversationProvider tests - streaming chat flow, message management, retry mechanism
- **FPROV-06:** ChatsProvider expansion - additional edge cases, listener verification

## Test Statistics

| Metric | Value |
|--------|-------|
| ConversationProvider tests | 40 |
| ChatsProvider tests | 35 (22 original + 13 new) |
| Total tests added | 53 |
| Total provider tests | 278 |

## Next Steps

- Plan 31-04: ThreadProvider and ProjectProvider tests
- Plan 31-05: Service layer tests (AIService, ThreadService, ProjectService)
