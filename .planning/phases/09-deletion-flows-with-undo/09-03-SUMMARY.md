---
phase: 09-deletion-flows-with-undo
plan: 03
subsystem: frontend-ui
tags: [delete-ui, confirmation-dialog, navigation, flutter]

dependency-graph:
  requires:
    - "09-02: Service delete methods and Provider optimistic delete with undo"
    - "Delete confirmation dialog widget (delete_confirmation_dialog.dart)"
  provides:
    - "Delete buttons on all resource screens"
    - "Confirmation flow before all deletions"
    - "Post-delete navigation (detail screens return to parent list)"
  affects:
    - "Phase 10: Loading and empty states after deletion"
    - "User can now delete all resource types from UI"

tech-stack:
  added: []
  patterns:
    - "PopupMenuButton for contextual delete options in lists"
    - "IconButton for delete in detail view headers"
    - "Long-press to show bottom sheet for message options"
    - "context.go() navigation after delete from detail screen"

file-tracking:
  key-files:
    created: []
    modified:
      - frontend/lib/screens/projects/project_detail_screen.dart
      - frontend/lib/screens/threads/thread_list_screen.dart
      - frontend/lib/screens/documents/document_list_screen.dart
      - frontend/lib/screens/conversation/conversation_screen.dart

decisions:
  - id: "09-03-d1"
    description: "IconButton for project delete in header row"
    rationale: "Consistent with edit button placement, visible but not prominent"
  - id: "09-03-d2"
    description: "PopupMenuButton for thread and document list items"
    rationale: "Allows extensibility for future options (rename, move, etc.)"
  - id: "09-03-d3"
    description: "Long-press bottom sheet for message deletion"
    rationale: "Mobile-friendly pattern for contextual actions on chat messages"

metrics:
  duration: "~5 minutes"
  completed: "2026-01-30"
---

# Phase 9 Plan 3: UI Integration with Confirmation Dialogs Summary

Integrate delete functionality into all resource screens with confirmation dialogs and post-delete navigation.

## One-liner

Delete buttons on project detail, thread list, document list, and conversation screens with confirmation dialogs calling provider optimistic delete methods.

## What Was Built

### 1. Project Detail Screen Delete

**File:** `frontend/lib/screens/projects/project_detail_screen.dart`

```dart
// Delete icon button in project header row
IconButton(
  icon: const Icon(Icons.delete_outline),
  tooltip: 'Delete Project',
  onPressed: () => _deleteProject(context),
),

// Delete method with cascade warning and navigation
Future<void> _deleteProject(BuildContext context) async {
  final confirmed = await showDeleteConfirmationDialog(
    context: context,
    itemType: 'project',
    cascadeMessage: 'This will delete all threads and documents in this project.',
  );

  if (confirmed && context.mounted) {
    context.read<ProjectProvider>().deleteProject(context, widget.projectId);
    context.go('/projects');  // Navigate back to projects list
  }
}
```

### 2. Thread List Screen Delete

**File:** `frontend/lib/screens/threads/thread_list_screen.dart`

```dart
// PopupMenuButton on each thread card
trailing: PopupMenuButton<String>(
  onSelected: (value) {
    if (value == 'delete') {
      _deleteThread(context, thread.id);
    }
  },
  itemBuilder: (context) => [
    const PopupMenuItem(
      value: 'delete',
      child: Row(
        children: [
          Icon(Icons.delete_outline),
          SizedBox(width: 8),
          Text('Delete'),
        ],
      ),
    ),
  ],
),

// Delete method with cascade warning
Future<void> _deleteThread(BuildContext context, String threadId) async {
  final confirmed = await showDeleteConfirmationDialog(
    context: context,
    itemType: 'thread',
    cascadeMessage: 'This will delete all messages in this thread.',
  );

  if (confirmed && context.mounted) {
    context.read<ThreadProvider>().deleteThread(context, threadId);
  }
}
```

### 3. Document List Screen Delete

**File:** `frontend/lib/screens/documents/document_list_screen.dart`

```dart
// PopupMenuButton with View and Delete options
PopupMenuButton<String>(
  onSelected: (value) {
    if (value == 'view') {
      Navigator.push(context, MaterialPageRoute(
        builder: (context) => DocumentViewerScreen(documentId: doc.id),
      ));
    } else if (value == 'delete') {
      _deleteDocument(context, doc.id);
    }
  },
  itemBuilder: (context) => [
    const PopupMenuItem(value: 'view', child: Row(...)),
    const PopupMenuItem(value: 'delete', child: Row(...)),
  ],
),

// Delete method (no cascade - documents have no children)
Future<void> _deleteDocument(BuildContext context, String documentId) async {
  final confirmed = await showDeleteConfirmationDialog(
    context: context,
    itemType: 'document',
  );

  if (confirmed && context.mounted) {
    context.read<DocumentProvider>().deleteDocument(context, documentId);
  }
}
```

### 4. Conversation Screen Message Delete

**File:** `frontend/lib/screens/conversation/conversation_screen.dart`

```dart
// Long-press handler shows bottom sheet
GestureDetector(
  onLongPress: () => _showMessageOptions(context, message),
  child: MessageBubble(message: message),
)

// Bottom sheet with delete option
void _showMessageOptions(BuildContext context, Message message) {
  showModalBottomSheet(
    context: context,
    builder: (sheetContext) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.delete_outline),
            title: const Text('Delete message'),
            onTap: () {
              Navigator.pop(sheetContext);
              _deleteMessage(context, message.id);
            },
          ),
        ],
      ),
    ),
  );
}

// Delete method (no cascade - messages have no children)
Future<void> _deleteMessage(BuildContext context, String messageId) async {
  final confirmed = await showDeleteConfirmationDialog(
    context: context,
    itemType: 'message',
  );

  if (confirmed && context.mounted) {
    context.read<ConversationProvider>().deleteMessage(
      context, widget.threadId, messageId,
    );
  }
}
```

## Commits

| Hash | Message |
|------|---------|
| 12c3e3d | feat(09-03): add delete button to project detail screen |
| bb7fb5f | feat(09-03): add delete options to thread and document lists |
| 5827617 | feat(09-03): add delete option for messages in conversation |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- Project detail screen has delete button with confirmation dialog
- Deleting project navigates back to projects list via context.go('/projects')
- Thread list items have PopupMenuButton with delete option
- Document list items have PopupMenuButton with view and delete options
- Conversation screen uses long-press bottom sheet for message delete
- All confirmation dialogs use the reusable showDeleteConfirmationDialog
- Project and thread deletions show cascade warnings
- Document and message deletions have no cascade (no children)
- Flutter analyze passes for all modified screens

## UI Pattern Reference

| Screen | Delete Trigger | Cascade Warning |
|--------|---------------|-----------------|
| ProjectDetailScreen | IconButton in header | "all threads and documents" |
| ThreadListScreen | PopupMenuButton on card | "all messages" |
| DocumentListScreen | PopupMenuButton on card | None |
| ConversationScreen | Long-press bottom sheet | None |

## Complete Deletion Flow (Phase 9)

With all three plans complete, the full deletion flow is:

1. **User triggers delete** (Plan 03) - button/menu in UI
2. **Confirmation dialog appears** (Plan 02) - neutral style, cascade info if applicable
3. **User confirms** - dialog returns true
4. **Provider removes optimistically** (Plan 02) - item disappears immediately
5. **SnackBar shows with Undo** (Plan 02) - 10-second window
6. **If Undo clicked** - item restored, no backend call
7. **If timer expires** - backend DELETE called (Plan 01)
8. **If backend fails** - item restored with error message
9. **Navigation** (Plan 03) - detail screens return to parent list

## Next Steps

- Phase 10: Loading states and empty states (after deletion empties a list)
- Add swipe-to-delete gesture for mobile (future enhancement)
- Consider batch delete selection mode (future enhancement)
