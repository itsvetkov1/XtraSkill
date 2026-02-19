---
phase: 68-core-conversation-memory-fix
plan: 02
subsystem: frontend-tests
tags: [flutter, unit-tests, mockito, provider, conversation]
dependency_graph:
  requires:
    - frontend/lib/providers/assistant_conversation_provider.dart
    - frontend/lib/services/ai_service.dart
    - frontend/lib/services/thread_service.dart
    - frontend/lib/services/document_service.dart
    - frontend/lib/models/message.dart
    - frontend/lib/models/thread.dart
    - frontend/lib/models/skill.dart
  provides:
    - frontend/test/unit/providers/assistant_conversation_provider_test.dart
    - frontend/test/unit/providers/assistant_conversation_provider_test.mocks.dart
  affects:
    - frontend test suite (28 new tests)
tech_stack:
  added: []
  patterns:
    - mockito GenerateNiceMocks for AIService, ThreadService, DocumentService
    - async* stream mocking for ChatEvent streams
    - listener-based state capture for async notification testing
key_files:
  created:
    - frontend/test/unit/providers/assistant_conversation_provider_test.dart
    - frontend/test/unit/providers/assistant_conversation_provider_test.mocks.dart
  modified:
    - frontend/test/unit/chats_provider_test.mocks.dart (regenerated)
    - frontend/test/unit/providers/conversation_provider_test.mocks.dart (regenerated)
    - frontend/test/unit/providers/document_provider_test.mocks.dart (regenerated)
    - frontend/test/unit/providers/thread_provider_test.mocks.dart (regenerated)
decisions:
  - "Auto-retry tests cannot use 'both calls fail' pattern — provider has infinite retry bug (reset _hasAutoRetried on each sendMessage). Used listener-based canRetry capture instead."
  - "Error handling tests use one-error-then-succeed pattern (first call errors, auto-retry succeeds) to avoid 2-second delays and infinite loops."
metrics:
  duration_minutes: 7
  completed_date: "2026-02-19"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 4
  tests_added: 28
---

# Phase 68 Plan 02: AssistantConversationProvider Unit Tests Summary

28 Flutter unit tests for AssistantConversationProvider covering thread loading, message sending with streaming, error handling with auto-retry awareness, skill prepending, and conversation state reset.

## What Was Built

Created `frontend/test/unit/providers/assistant_conversation_provider_test.dart` following the exact pattern from `conversation_provider_test.dart`. Generated `assistant_conversation_provider_test.mocks.dart` via build_runner.

### Test Coverage

| Group | Tests | Key Assertions |
|-------|-------|----------------|
| loadThread | 5 | success (3 messages), 404 detection, generic error, loading state |
| sendMessage | 6 | user message added before response, assistant message added, history preserved, streaming text accumulation, isStreaming lifecycle, null thread guard |
| error handling | 4 | isStreaming false after error, partial content on mid-stream error, canRetry false initially, canRetry true during error notification |
| retryLastMessage | 2 | no-op without failed message, retry removes duplicate and succeeds |
| skill selection | 4 | set skill, clear skill, skill context prepended to content, skill cleared after send |
| clearConversation | 1 | all 10 state fields reset |
| initial state | 6 | thread null, messages empty, canRetry/isStreaming/error false, no skill |

**Total: 28 tests, all passing**

## Deviations from Plan

### Auto-fixed Issues

None — tests written as planned.

### Design Decisions (Not Bugs)

**1. [Rule 1 - Bug Discovery] Auto-retry creates infinite recursion when both initial and retry calls fail**

- **Found during:** Error handling test authoring
- **Issue:** `AssistantConversationProvider._hasAutoRetried` is reset to `false` at the start of every `sendMessage()` call (line 170). When the auto-retry call also fails, `_hasAutoRetried` is false again, triggering another auto-retry, creating an infinite loop.
- **Impact on tests:** Cannot write a test where both calls fail — the test times out after 30 seconds.
- **Test approach:** Used two strategies:
  1. `canRetry is true` test: Added a listener to capture `canRetry` state immediately when the first error notification fires (before the 2-second delay).
  2. Error path tests: Used first-call-errors, second-call-succeeds pattern to exercise error code paths without triggering infinite loop.
- **Note:** The underlying infinite-retry bug in the provider is deferred to `deferred-items.md` — it was pre-existing and out of scope for this plan (plan 02 is test-only).
- **Files modified:** `assistant_conversation_provider_test.dart` (test design adaptation only)

## Self-Check: PASSED

All files created and commits verified:
- FOUND: `frontend/test/unit/providers/assistant_conversation_provider_test.dart`
- FOUND: `frontend/test/unit/providers/assistant_conversation_provider_test.mocks.dart`
- FOUND: `68-02-SUMMARY.md`
- FOUND commit: `6f943c4` (test(68-02): add AssistantConversationProvider unit tests with mocks)
- FOUND commit: `35c8bbe` (chore(68-02): regenerate test mocks via build_runner)
