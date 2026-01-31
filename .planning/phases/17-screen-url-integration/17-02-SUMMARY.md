---
phase: 17-screen-url-integration
plan: 02
subsystem: frontend-ui
tags: [flutter, error-handling, navigation, go-router, browser-history]

dependency-graph:
  requires:
    - 17-01 (ResourceNotFoundState widget, isNotFound pattern)
  provides:
    - ConversationProvider.isNotFound 404 detection
    - ConversationScreen not-found UI
    - GoRouter browser history consistency
  affects:
    - 17-03 (Home screen URL integration)

tech-stack:
  added: []
  patterns:
    - Error state differentiation (not-found vs generic error)
    - GoRouter optionURLReflectsImperativeAPIs for browser history

key-files:
  created: []
  modified:
    - frontend/lib/providers/conversation_provider.dart
    - frontend/lib/screens/conversation/conversation_screen.dart
    - frontend/lib/main.dart

decisions:
  DEC-17-02-01: "Use speaker_notes_off_outlined icon for thread not-found (chat_bubble_off_outlined not in Flutter)"
  DEC-17-02-02: "Navigate to /projects/{projectId} (parent project, not /home)"
  DEC-17-02-03: "Set optionURLReflectsImperativeAPIs before usePathUrlStrategy()"

metrics:
  duration: ~4 minutes
  completed: 2026-01-31
---

# Phase 17 Plan 02: Thread Not-Found State Summary

**One-liner:** ConversationProvider.isNotFound flag for 404 detection, ConversationScreen not-found UI with "Back to Project" navigation, and GoRouter browser history option for consistent back/forward button behavior.

## What Was Built

### 1. ConversationProvider isNotFound Flag
Updated `frontend/lib/providers/conversation_provider.dart`:
- Added `_isNotFound` private field and `isNotFound` getter
- `loadThread()` detects 404 from error message ("not found" or "404")
- Sets `isNotFound=true` and `error=null` for 404 (mutually exclusive)
- Reset `isNotFound=false` at start of new load
- `clearConversation()` and `clearError()` both clear `isNotFound`
- Removed `rethrow` - screen handles not-found via state flag

### 2. ConversationScreen Not-Found UI
Updated `frontend/lib/screens/conversation/conversation_screen.dart`:
- Added `go_router` and `ResourceNotFoundState` imports
- Check `loading` BEFORE Scaffold (full-screen spinner)
- Check `isNotFound` BEFORE normal content (ERR-03)
- Shows ResourceNotFoundState with:
  - Icon: `Icons.speaker_notes_off_outlined`
  - Title: "Thread not found"
  - Message: "This conversation may have been deleted or you may not have access to it."
  - Button: "Back to Project" navigating to `/projects/{projectId}`

### 3. GoRouter Browser History Option
Updated `frontend/lib/main.dart`:
- Added `GoRouter.optionURLReflectsImperativeAPIs = true` before `usePathUrlStrategy()`
- Ensures browser back/forward works correctly with imperative navigation (`context.go()`)
- Set as static option before app runs

## Implementation Decisions

| Decision | Rationale |
|----------|-----------|
| Use speaker_notes_off_outlined icon | `chat_bubble_off_outlined` doesn't exist in Flutter Icons; `speaker_notes_off` conveys "conversation unavailable" |
| Navigate to parent project | Thread is nested under project - "Back to Project" is more helpful than "Back to Home" |
| Set optionURLReflectsImperativeAPIs before usePathUrlStrategy | GoRouter docs recommend setting static options early |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| a5a198f | feat | Add isNotFound flag to ConversationProvider |
| 488dbf3 | feat | Add not-found state to ConversationScreen |
| fbb772a | feat | Add GoRouter browser history option (ROUTE-02) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Changed icon from chat_bubble_off_outlined to speaker_notes_off_outlined**
- **Found during:** Task 2
- **Issue:** `Icons.chat_bubble_off_outlined` doesn't exist in Flutter
- **Fix:** Used `Icons.speaker_notes_off_outlined` which conveys similar meaning
- **Files modified:** `conversation_screen.dart`
- **Commit:** 488dbf3

## Verification

All verification criteria met:
- [x] `flutter analyze frontend/lib/providers/conversation_provider.dart` - No issues
- [x] `flutter analyze frontend/lib/screens/conversation/conversation_screen.dart` - No issues
- [x] `flutter analyze frontend/lib/main.dart` - No errors (info-level lints about print are pre-existing)
- [x] `flutter build web --no-tree-shake-icons` - Build succeeds

## Next Phase Readiness

Plan 17-03 can proceed immediately:
- Thread not-found pattern complete (mirrors project not-found from 17-01)
- Browser history behavior configured
- Home screen URL integration next
