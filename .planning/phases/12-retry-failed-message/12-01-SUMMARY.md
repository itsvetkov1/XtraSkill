---
phase: 12-retry-failed-message
plan: 01
subsystem: frontend-ux
tags: [flutter, error-handling, retry, state-management, provider]

dependency-graph:
  requires:
    - "Phase 3: Conversation screen with error display"
  provides:
    - "Retry functionality for failed AI messages"
    - "ConversationProvider._lastFailedMessage state tracking"
    - "canRetry getter for UI state"
    - "retryLastMessage() method"
  affects:
    - "Future error handling improvements"
    - "Offline mode considerations"

tech-stack:
  added: []
  patterns:
    - "Failed state tracking in provider"
    - "Conditional action buttons in MaterialBanner"
    - "Duplicate prevention on retry"

key-files:
  created: []
  modified:
    - "frontend/lib/providers/conversation_provider.dart"
    - "frontend/lib/screens/conversation/conversation_screen.dart"

decisions:
  - id: "12-01-D1"
    choice: "Store only content string, not full Message"
    alternatives: ["Store full Message object", "Command pattern with request metadata"]
    rationale: "Simplest solution - only need the text to resend"

metrics:
  duration: "5 minutes"
  completed: "2026-01-30"
---

# Phase 12 Plan 01: Retry Failed Message - Implementation Summary

**One-liner:** Failed message state tracking with retry button in error banner using provider pattern

## What Was Built

Added retry functionality to the conversation screen that allows users to resend their message when an AI request fails.

### ConversationProvider Changes

- Added `_lastFailedMessage` field to store failed message content
- Added `canRetry` getter (returns true when error exists with stored message)
- Modified `sendMessage()` to set `_lastFailedMessage` at start and clear on success
- Added `retryLastMessage()` method with duplicate message prevention
- Modified `clearError()` to also clear retry state (dismiss = "I don't want to retry")

### UI Changes

- Modified error banner in `conversation_screen.dart` to show conditional "Retry" button
- "Dismiss" button always visible (clears error and retry state)
- "Retry" button visible only when `canRetry` is true

### Duplicate Prevention Logic

The `retryLastMessage()` method removes the last user message before calling `sendMessage()`:

```dart
if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
  _messages.removeLast();
}
```

This prevents the user from seeing their message twice after a successful retry.

## Requirements Coverage

| Requirement | Implementation | Verified |
|-------------|---------------|----------|
| RETRY-01: Error banner shows "Dismiss \| Retry" | MaterialBanner with conditional Retry button | Yes |
| RETRY-02: Retry resends last user message | `retryLastMessage()` calls `sendMessage(content)` | Yes |
| RETRY-03: Failed message state tracked | `_lastFailedMessage` field in provider | Yes |
| RETRY-04: Works for network/API errors | Both error paths preserve `_lastFailedMessage` | Yes |

## Technical Implementation

### State Flow

1. User sends message -> `_lastFailedMessage = content`
2. If success -> `_lastFailedMessage = null`
3. If error -> `_lastFailedMessage` remains set
4. User taps Retry -> removes duplicate, clears state, resends
5. User taps Dismiss -> clears both error and `_lastFailedMessage`

### Files Modified

| File | Changes |
|------|---------|
| `conversation_provider.dart` | +28 lines (field, getter, methods, integration) |
| `conversation_screen.dart` | +5 lines (conditional Retry button) |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| Flutter analyze (conversation_provider.dart) | No issues |
| Flutter analyze (conversation_screen.dart) | No issues |
| Flutter build web | Success |
| Code inspection - _lastFailedMessage | Present at line 54 |
| Code inspection - canRetry | Present at line 84 |
| Code inspection - retryLastMessage() | Present at lines 191-205 |
| Code inspection - Retry button | Present in MaterialBanner actions |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 6e8ee8e | feat | Add retry state tracking and retryLastMessage method |
| 99cbc92 | feat | Add retry button to error banner UI |

## Next Phase Readiness

Phase 12 complete. Ready for Phase 13 (Display Authenticated User).

No blockers or concerns.

---

*Summary created: 2026-01-30*
