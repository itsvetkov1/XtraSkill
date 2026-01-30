---
phase: 09-deletion-flows-with-undo
plan: 02
subsystem: frontend-deletion
tags: [delete-ui, optimistic-update, undo, snackbar, flutter]

dependency-graph:
  requires:
    - "09-01: Backend DELETE endpoints"
    - "Existing service patterns (ProjectService, ThreadService, etc.)"
    - "Existing provider patterns (ProjectProvider, ThreadProvider, etc.)"
  provides:
    - "Service delete methods calling backend endpoints"
    - "Provider optimistic delete with 10-second undo window"
    - "Reusable delete confirmation dialog widget"
  affects:
    - "09-03: Delete UI integration will use these provider methods"
    - "Future: Empty state handling when last item deleted"

tech-stack:
  added: []
  patterns:
    - "Optimistic UI updates (remove from list immediately, revert on error)"
    - "Timer-based deferred backend calls (10-second undo window)"
    - "SnackBar with action for undo functionality"
    - "context.mounted check after async operations"

file-tracking:
  key-files:
    created:
      - frontend/lib/widgets/delete_confirmation_dialog.dart
    modified:
      - frontend/lib/services/project_service.dart
      - frontend/lib/services/thread_service.dart
      - frontend/lib/services/document_service.dart
      - frontend/lib/services/ai_service.dart
      - frontend/lib/providers/project_provider.dart
      - frontend/lib/providers/thread_provider.dart
      - frontend/lib/providers/document_provider.dart
      - frontend/lib/providers/conversation_provider.dart

decisions:
  - id: "09-02-d1"
    description: "10-second undo window with Timer-based deferred deletion"
    rationale: "Balance between user recovery time and expected deletion confirmation"
  - id: "09-02-d2"
    description: "Single pending delete per provider (commit previous before new delete)"
    rationale: "Simplifies state management, prevents accumulating uncommitted deletes"
  - id: "09-02-d3"
    description: "Neutral confirmation dialog style (no red buttons)"
    rationale: "Per CONTEXT.md - deletes are normal operations, not scary warnings"

metrics:
  duration: "~8 minutes"
  completed: "2026-01-30"
---

# Phase 9 Plan 2: Frontend Deletion Services and Providers Summary

Implement frontend deletion infrastructure with service methods, provider delete logic with optimistic UI and undo support, and reusable confirmation dialog.

## One-liner

Service delete methods calling backend + Provider optimistic delete with 10-second undo window + SnackBar with Undo action.

## What Was Built

### 1. Service Delete Methods

**Files:** All service files in `frontend/lib/services/`

```dart
// ProjectService
Future<void> deleteProject(String id) async {
  final headers = await _getHeaders();
  await _dio.delete('$_baseUrl/api/projects/$id', options: Options(headers: headers));
}

// ThreadService
Future<void> deleteThread(String id) async { ... }

// DocumentService
Future<void> deleteDocument(String id) async { ... }

// AIService
Future<void> deleteMessage(String threadId, String messageId) async { ... }
```

All methods handle 401/404 errors consistently.

### 2. Delete Confirmation Dialog

**File:** `frontend/lib/widgets/delete_confirmation_dialog.dart`

```dart
Future<bool> showDeleteConfirmationDialog({
  required BuildContext context,
  required String itemType,
  String? cascadeMessage,
}) async {
  final confirmed = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (dialogContext) => AlertDialog(
      title: Text('Delete this $itemType?'),
      content: cascadeMessage != null ? Text(cascadeMessage) : null,
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: Text('Cancel')),
        TextButton(onPressed: () => Navigator.pop(dialogContext, true), child: Text('Delete')),
      ],
    ),
  );
  return confirmed ?? false;
}
```

### 3. Provider Optimistic Delete Pattern

**Files:** All provider files in `frontend/lib/providers/`

Each provider implements the same pattern:

```dart
// State fields
Project? _pendingDelete;
int _pendingDeleteIndex = 0;
Timer? _deleteTimer;

// Delete method
Future<void> deleteProject(BuildContext context, String projectId) async {
  // 1. Find and remove from list
  _pendingDelete = _projects[index];
  _pendingDeleteIndex = index;
  _projects.removeAt(index);

  // 2. Show SnackBar with Undo
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
    content: Text('Project deleted'),
    duration: Duration(seconds: 10),
    action: SnackBarAction(label: 'Undo', onPressed: _undoDelete),
  ));

  // 3. Start 10-second timer
  _deleteTimer = Timer(Duration(seconds: 10), _commitPendingDelete);
}

// Undo method
void _undoDelete() {
  _deleteTimer?.cancel();
  _projects.insert(_pendingDeleteIndex, _pendingDelete!);
  _pendingDelete = null;
  notifyListeners();
}

// Commit method (called after 10 seconds)
Future<void> _commitPendingDelete() async {
  try {
    await _projectService.deleteProject(_pendingDelete!.id);
  } catch (e) {
    // Rollback on error
    _projects.insert(_pendingDeleteIndex, _pendingDelete!);
    _error = 'Failed to delete: $e';
    notifyListeners();
  }
}
```

ConversationProvider additionally stores `_pendingDeleteThreadId` for the backend call.

## Commits

| Hash | Message |
|------|---------|
| 17e9e7d | feat(09-02): add delete methods to all services |
| d6dbc07 | feat(09-02): create reusable delete confirmation dialog |
| d4084f1 | feat(09-02): add optimistic delete with undo to all providers |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- All services have delete methods (deleteProject, deleteThread, deleteDocument, deleteMessage)
- Delete confirmation dialog exists at lib/widgets/delete_confirmation_dialog.dart
- All providers have delete methods with optimistic removal
- All providers show SnackBar with Undo action (10-second duration)
- All providers have _undoDelete() that restores item
- All providers have _commitPendingDelete() that calls service and rolls back on error
- All providers cancel timer in dispose()
- Flutter analyze passes with no errors (only pre-existing warnings)

## Provider Method Reference

| Provider | Delete Method | Service Call |
|----------|--------------|--------------|
| ProjectProvider | deleteProject(context, projectId) | _projectService.deleteProject(id) |
| ThreadProvider | deleteThread(context, threadId) | _threadService.deleteThread(id) |
| DocumentProvider | deleteDocument(context, documentId) | _service.deleteDocument(id) |
| ConversationProvider | deleteMessage(context, threadId, messageId) | _aiService.deleteMessage(threadId, messageId) |

## Next Steps

- 09-03: Wire delete UI buttons to call these provider methods
- Add swipe-to-delete gestures where appropriate
- Handle empty state when last item in list is deleted
