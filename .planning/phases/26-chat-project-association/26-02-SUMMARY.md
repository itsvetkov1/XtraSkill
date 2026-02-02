---
phase: 26
plan: 02
subsystem: frontend-ui
tags: [threads, association, picker, dialog, toolbar]

dependency-graph:
  requires: [phase-26-01-backend-api]
  provides: [chat-project-association-ui]
  affects: [user-workflow]

tech-stack:
  patterns:
    - dialog-confirmation-flow
    - dual-entry-point
    - provider-consumer

file-tracking:
  key-files:
    created:
      - frontend/lib/screens/conversation/widgets/add_to_project_button.dart
      - frontend/lib/widgets/project_picker_dialog.dart
    modified:
      - frontend/lib/services/thread_service.dart
      - frontend/lib/providers/conversation_provider.dart
      - frontend/lib/screens/conversation/conversation_screen.dart

decisions:
  - id: DUAL-ENTRY-POINT
    choice: "Both toolbar button and options menu for Add to Project"
    reason: "Maximizes discoverability and matches user expectations"
  - id: IN-PLACE-UPDATE
    choice: "No success snackbar, header updates in-place"
    reason: "Visual feedback is immediate (button disappears), snackbar would be redundant"

metrics:
  duration: "~3 minutes"
  completed: "2026-02-02"
---

# Phase 26 Plan 02: Chat-Project Association UI Summary

Built frontend UI for associating project-less chats with projects: toolbar button, options menu, project picker modal, and confirmation dialog.

## One-liner

Project-less chats can now be permanently added to projects via toolbar button or options menu with confirmation flow.

## Changes Made

### Task 1: Add service and provider methods

**Files modified:**
- `frontend/lib/services/thread_service.dart`
- `frontend/lib/providers/conversation_provider.dart`

**Changes:**
1. Added `ThreadService.associateWithProject(threadId, projectId)` method
   - Calls PATCH /api/threads/{id} with project_id in body
   - Handles 400 (already associated) and 404 (not found) errors
2. Added `ConversationProvider.associateWithProject(projectId)` method
   - Calls service method and reloads thread on success
   - Returns bool for success/failure indication

### Task 2: Create AddToProjectButton and ProjectPickerDialog widgets

**Files created:**
- `frontend/lib/screens/conversation/widgets/add_to_project_button.dart`
- `frontend/lib/widgets/project_picker_dialog.dart`

**Changes:**
1. `AddToProjectButton` - TextButton with folder icon and "Add to Project" label
2. `ProjectPickerDialog` - Modal dialog with:
   - Project list from ProjectProvider
   - Loading, error, and empty states
   - Confirmation sub-dialog: "Add to [Project]?"
   - Returns selected Project or null if cancelled

### Task 3: Integrate into ConversationScreen

**Files modified:**
- `frontend/lib/screens/conversation/conversation_screen.dart`

**Changes:**
1. Added `_showAddToProjectDialog()` method
2. Added PopupMenuButton in AppBar actions with "Add to Project" option
3. Added toolbar Row with ProviderIndicator and AddToProjectButton
4. Both entry points conditionally shown only for project-less threads
5. Error handling with snackbar and retry option

## Bug Fixes During Testing

Three bugs were discovered and fixed during regression testing:

1. **BUG-013:** GlobalThreadListResponse missing `created_at` field - caused null type error on Chats refresh
2. **BUG-014:** Project-scoped thread creation missing `last_activity_at` - caused project threads not appearing in global list
3. **BUG-015:** Shift+Enter not creating newline on web - required manual newline insertion

All fixes include tests in `backend/tests/test_global_threads.py` and `frontend/test/widget/chat_input_test.dart`.

## Verification Results

| Check | Status |
|-------|--------|
| Toolbar button visible for project-less chats | PASS |
| Options menu shows "Add to Project" | PASS |
| Project picker modal loads projects | PASS |
| Confirmation dialog appears on selection | PASS |
| Association updates header in-place | PASS |
| Button/menu hidden after association | PASS |
| Associated chat in project's thread list | PASS |
| Persists after page refresh | PASS |

## Requirements Satisfied

- CHATS-08: Chat detail shows project or "No Project" with add button
- CHATS-09: Add to Project button in header (toolbar area)
- CHATS-10: Add to Project in options menu
- CHATS-11: Project selection modal
- CHATS-12: After association, chat in project's list
- CHATS-13: Association is permanent

## Deviations from Plan

None significant - plan executed as written with bug fixes added during testing.

## Phase 26 Complete

All requirements for chat-project association are satisfied. Users can now:
1. Create project-less chats from Home or Chats section
2. Add them to any existing project via toolbar button or menu
3. View associated chats in both global Chats list and project's thread list
