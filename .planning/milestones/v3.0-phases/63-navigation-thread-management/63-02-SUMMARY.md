---
phase: 63-navigation-thread-management
plan: 02
subsystem: frontend-thread-management
tags: [thread-creation, thread-deletion, undo-pattern, assistant]

dependency_graph:
  requires: [63-01-assistant-navigation]
  provides: [assistant-thread-creation, assistant-thread-deletion-with-undo]
  affects: [assistant-list-screen, thread-service]

tech_stack:
  added: [assistant-create-dialog, thread-creation-api]
  patterns: [dialog-with-validation, undo-snackbar-pattern, optimistic-ui-updates]

key_files:
  created:
    - frontend/lib/screens/assistant/assistant_create_dialog.dart
  modified:
    - frontend/lib/screens/assistant/assistant_list_screen.dart
    - frontend/lib/services/thread_service.dart

decisions:
  - "Assistant thread creation requires title (not optional like BA threads)"
  - "No project selector or mode selector in Assistant dialog (simplified design)"
  - "Delete uses local undo pattern (not ThreadProvider) for independent state management"
  - "10-second undo window with timer-based hard delete"
  - "Failed deletes roll back optimistically-removed threads"

metrics:
  duration_minutes: 2
  tasks_completed: 2
  files_created: 1
  files_modified: 2
  commits: 2
  completed_at: "2026-02-17"
---

# Phase 63 Plan 02: Assistant Thread Creation & Deletion with Undo Summary

**One-liner:** Implemented simplified thread creation dialog for Assistant (title required, description optional) with post-create navigation and delete-with-undo snackbar (10-second countdown, rollback on failure).

## What Was Built

### Task 1: Thread Creation with Dialog (Commit a2ab1e9)
- **ThreadService.createAssistantThread()**: New method posting to `/api/threads` with `thread_type='assistant'`, no project_id
  - Parameters: `title` (required), `description` (optional)
  - Returns Thread object for immediate navigation
- **AssistantCreateDialog**: Simplified creation dialog (no project/mode selectors)
  - **Title field**: TextFormField with required validation, 255 char limit, autofocus, hint: "e.g., Debug CSS Layout"
  - **Description field**: TextFormField, optional, multi-line (maxLines: 3), hint: "Optional details about this conversation"
  - **Static show()**: Returns `Future<Thread?>` for caller convenience
  - **Loading state**: Create button shows spinner during API call
  - **Error handling**: Shows error snackbar on failure
- **AssistantListScreen._showCreateDialog()**: Wired to dialog
  - Opens AssistantCreateDialog via static show() method
  - On success: inserts new thread at top of local list (optimistic)
  - Navigates to `/assistant/:threadId` immediately
  - On cancel/error: no navigation

### Task 2: Delete with Undo (Commit 87b2f84)
- **AssistantListScreen delete flow**: Full undo implementation with local state
  - **State fields**: `_pendingDelete`, `_pendingDeleteIndex`, `_deleteTimer`
  - **_deleteThread()**: Commits any previous pending delete, removes thread optimistically, shows snackbar with "Undo" action, starts 10-second timer
  - **_undoDelete()**: Cancels timer, restores thread to original position in list
  - **_commitPendingDelete()**: Calls ThreadService.deleteThread() after timer expires or when new delete triggered
  - **Rollback on failure**: On API error, thread reinserted at original position with error snackbar
  - **Timer cleanup**: dispose() cancels timer to prevent memory leaks
- **Removed unused imports**: ThreadProvider and Provider no longer used (delete manages own state)

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

✅ `flutter analyze` passes with no errors (39 pre-existing info/warnings in other files)
✅ AssistantCreateDialog file created at correct path
✅ Title validation enforces non-empty requirement (`grep 'Title is required'`)
✅ No project selector in dialog (`grep 'project'` count: 1 occurrence in comment only)
✅ Post-creation navigation to `/assistant/:threadId` (`grep 'context.go.*assistant'`)
✅ ThreadService sets `thread_type='assistant'` (`grep 'thread_type.*assistant'`)
✅ Delete shows "Undo" action in snackbar (`grep 'Undo'`)
✅ 10-second timer for hard delete (`grep 'Timer'`)
✅ `_commitPendingDelete()` method exists for hard delete
✅ Timer cancelled in dispose() for cleanup

## Technical Notes

### Title Required vs Optional
BA thread creation allows optional titles (empty = "Untitled"). Assistant threads require titles because:
- Assistant is a general-purpose tool (not document-specific)
- Users should name their conversations explicitly
- No default context like "Meeting Notes" or "Refinement Session"

Validation enforces this:
```dart
validator: (value) {
  if (value == null || value.trim().isEmpty) {
    return 'Title is required';
  }
  if (value.length > 255) {
    return 'Title must be 255 characters or less';
  }
  return null;
},
```

### Local Undo Pattern
Delete uses local state management instead of ThreadProvider because:
1. **Independent state**: AssistantListScreen manages its own `_threads` list
2. **Simpler flow**: No provider dependency, direct ThreadService calls
3. **Optimistic UI**: Immediate removal from list, rollback on failure
4. **Timer-based commit**: 10-second window for undo, automatic hard delete after timeout

Pattern matches Material Design undo snackbar guidelines:
- Immediate optimistic action (thread disappears)
- Clear undo affordance (button + countdown)
- Rollback on failure (reinsert at original position)

### Post-Creation Navigation
Dialog returns Thread object to caller (not void):
```dart
static Future<Thread?> show(BuildContext context) {
  return showDialog<Thread>(
    context: context,
    builder: (context) => const AssistantCreateDialog(),
  );
}
```

Caller handles navigation:
```dart
final thread = await AssistantCreateDialog.show(context);
if (thread != null && mounted) {
  setState(() {
    _threads.insert(0, thread);
  });
  context.go('/assistant/${thread.id}');
}
```

This pattern:
- Separates concerns (dialog creates, caller navigates)
- Enables reuse (dialog doesn't know navigation context)
- Supports testing (can mock without router)

## Dependencies Satisfied

### Requires (from Plan 63-01)
- ✅ /assistant route infrastructure exists
- ✅ AssistantListScreen with refreshThreads() method
- ✅ Thread delete flow basic structure

### Provides (for Phase 63-03/64)
- ✅ Full thread creation flow for Assistant
- ✅ Full thread deletion flow with undo
- ✅ createAssistantThread() API method
- ✅ Simplified dialog pattern for Assistant features

## Next Steps (Phase 64)

1. **Conversation screen**: Reuse existing ConversationScreen with assistant thread routing
2. **Message handling**: Ensure messages work for thread_type='assistant'
3. **Documents**: Add document upload support to Assistant conversations
4. **Artifacts**: Ensure BRD/PRD generation works for Assistant threads

## Commits

| Hash | Message | Files |
|------|---------|-------|
| a2ab1e9 | feat(63-02): create AssistantCreateDialog and wire thread creation with navigation | assistant_create_dialog.dart (new), assistant_list_screen.dart, thread_service.dart |
| 87b2f84 | feat(63-02): implement delete with undo snackbar for Assistant threads | assistant_list_screen.dart |

## Self-Check

Verifying all claimed artifacts exist:

**Created Files:**
- ✅ frontend/lib/screens/assistant/assistant_create_dialog.dart

**Modified Files:**
- ✅ frontend/lib/screens/assistant/assistant_list_screen.dart
- ✅ frontend/lib/services/thread_service.dart

**Commits:**
- ✅ a2ab1e9 (Thread creation with dialog)
- ✅ 87b2f84 (Delete with undo)

**Self-Check: PASSED** ✅
