# Phase 9: Deletion Flows with Undo - Research

**Researched:** 2026-01-30
**Domain:** Flutter deletion flows with undo capability, FastAPI cascade delete endpoints, optimistic UI updates
**Confidence:** HIGH

## Summary

Phase 9 implements deletion capabilities for projects, threads, documents, and messages with confirmation dialogs, undo support via SnackBar, and optimistic UI updates. The user's decisions from CONTEXT.md constrain the implementation: generic confirmation dialogs showing summary impact info only (no counts), neutral visual style, and "Delete"/"Cancel" buttons.

The implementation requires:
1. **Backend delete endpoints** for each resource type (projects, threads, documents, messages) with cascade behavior
2. **Frontend delete methods** in services and providers with optimistic UI updates
3. **Confirmation dialogs** following the established pattern from logout (Phase 8)
4. **Undo SnackBar mechanism** with 10-second timer and deferred hard delete
5. **Rollback logic** when backend delete fails

The existing codebase already has:
- SQLite cascade deletes configured via foreign keys with `ondelete="CASCADE"` and `passive_deletes=True` in relationships
- `PRAGMA foreign_keys=ON` enabled via SQLAlchemy event listener in `database.py`
- Optimistic update pattern established in `ConversationProvider` (adds temp messages before confirmation)
- Confirmation dialog pattern from logout in `settings_screen.dart`

**Primary recommendation:** Implement frontend-held undo (soft delete in UI, hard delete after 10-second expiry) rather than database soft delete. Use existing Provider patterns with optimistic removal and rollback on error.

## Standard Stack

The established libraries/tools for this phase are already in the project:

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `provider` | 6.x | State management | Providers already handle list state for projects/threads/documents |
| `dio` | 5.x | HTTP client | All services already use Dio for API calls |
| `go_router` | 14.x | Navigation | Post-delete navigation already supported |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Material 3 widgets | Built-in | UI components | AlertDialog, SnackBar, SnackBarAction |

### No New Dependencies Required
This phase uses only existing packages. Key widgets from Flutter's material library:
- `AlertDialog` - Confirmation dialogs (same pattern as logout)
- `ScaffoldMessenger.of(context).showSnackBar()` - Undo SnackBar display
- `SnackBarAction` - Undo button within SnackBar

## Architecture Patterns

### Recommended Project Structure (Additions)
```
lib/
├── providers/
│   ├── project_provider.dart   # ADD: deleteProject() with optimistic UI
│   ├── thread_provider.dart    # ADD: deleteThread() with optimistic UI
│   ├── document_provider.dart  # ADD: deleteDocument() with optimistic UI
│   └── conversation_provider.dart  # ADD: deleteMessage() with optimistic UI
├── services/
│   ├── project_service.dart    # ADD: deleteProject() API call
│   ├── thread_service.dart     # ADD: deleteThread() API call
│   ├── document_service.dart   # ADD: deleteDocument() API call
│   └── ai_service.dart         # (messages deleted via thread cascade)
├── widgets/
│   └── delete_confirmation_dialog.dart  # NEW: Reusable delete confirmation
└── screens/
    └── (existing screens add delete triggers)

backend/app/
├── routes/
│   ├── projects.py             # ADD: DELETE /projects/{id}
│   ├── threads.py              # ADD: DELETE /threads/{id}
│   ├── documents.py            # ADD: DELETE /documents/{id}
│   └── conversations.py        # ADD: DELETE /threads/{id}/messages/{id}
```

### Pattern 1: Optimistic Delete with Undo
**What:** Remove item from UI immediately, defer actual deletion until undo window expires
**When to use:** All deletions (DEL-06, DEL-07 requirements)
**Example:**
```dart
// Source: Flutter docs optimistic state pattern
class ProjectProvider extends ChangeNotifier {
  List<Project> _projects = [];
  Project? _pendingDelete;
  Timer? _deleteTimer;

  Future<void> deleteProject(
    BuildContext context,
    String projectId,
  ) async {
    // 1. Find and remove from list optimistically
    final index = _projects.indexWhere((p) => p.id == projectId);
    if (index == -1) return;

    _pendingDelete = _projects[index];
    _projects.removeAt(index);
    notifyListeners();

    // 2. Show SnackBar with undo action
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Project deleted'),
        duration: const Duration(seconds: 10),
        action: SnackBarAction(
          label: 'Undo',
          onPressed: _undoDelete,
        ),
      ),
    );

    // 3. Start timer for actual deletion
    _deleteTimer?.cancel();
    _deleteTimer = Timer(const Duration(seconds: 10), () {
      _commitDelete(context);
    });
  }

  void _undoDelete() {
    _deleteTimer?.cancel();
    if (_pendingDelete != null) {
      _projects.insert(0, _pendingDelete!);
      _pendingDelete = null;
      notifyListeners();
    }
  }

  Future<void> _commitDelete(BuildContext context) async {
    if (_pendingDelete == null) return;

    try {
      await _projectService.deleteProject(_pendingDelete!.id);
      _pendingDelete = null;
    } catch (e) {
      // Rollback: restore to list
      _projects.insert(0, _pendingDelete!);
      _pendingDelete = null;
      notifyListeners();

      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to delete: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }
}
```

### Pattern 2: Confirmation Dialog (Per CONTEXT.md Decisions)
**What:** Standard AlertDialog with summary impact info, neutral styling
**When to use:** Before all delete operations (DEL-01 through DEL-04)
**Example:**
```dart
// Source: Pattern from settings_screen.dart logout confirmation
// CONTEXT.md: Summary cascade info only, neutral visual style, "Delete"/"Cancel" buttons
Future<bool?> showDeleteConfirmation({
  required BuildContext context,
  required String itemType, // "project", "thread", "document", "message"
  String? cascadeInfo, // "This will delete all threads and messages"
}) {
  return showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (BuildContext dialogContext) {
      return AlertDialog(
        title: Text('Delete this $itemType?'),
        content: cascadeInfo != null ? Text(cascadeInfo) : null,
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            // CONTEXT.md: Neutral visual style - no red/warning treatment
            child: const Text('Delete'),
          ),
        ],
      );
    },
  );
}
```

### Pattern 3: Backend Cascade Delete Endpoint
**What:** DELETE endpoint that relies on database cascade for related records
**When to use:** All resource deletions
**Example:**
```python
# Source: Pattern from existing projects.py routes
@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a project and all related data (threads, documents, messages).

    SQLite cascade deletes handle related records automatically via
    foreign key ON DELETE CASCADE configuration.

    Args:
        project_id: Project UUID
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        401: If user not authenticated
        404: If project not found or not owned by user
    """
    # Query project
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    # Verify project exists and is owned by current user
    if not project or project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Delete project - cascades to threads, documents, messages
    await db.delete(project)
    await db.commit()

    # Return 204 No Content (no response body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### Pattern 4: Post-Delete Navigation
**What:** Navigate to parent screen after delete is confirmed (not on undo)
**When to use:** When deleting from detail screen (project detail, thread view)
**Example:**
```dart
// Source: GoRouter navigation patterns from main.dart
Future<void> _deleteCurrentProject(BuildContext context) async {
  final confirmed = await showDeleteConfirmation(
    context: context,
    itemType: 'project',
    cascadeInfo: 'This will delete all threads and documents',
  );

  if (confirmed == true && context.mounted) {
    final provider = context.read<ProjectProvider>();
    provider.deleteProject(context, widget.projectId);

    // Navigate back to projects list
    // GoRouter handles this via context.go() for clean navigation
    context.go('/projects');
  }
}
```

### Anti-Patterns to Avoid
- **Database soft delete for short-term undo:** Adds complexity, "deleted" field everywhere, no benefit for 10-second undo window
- **Blocking UI during delete timer:** User should be able to continue using app while undo is available
- **Multiple pending deletes:** Handle one at a time, cancel previous if new delete initiated
- **Navigating before undo expires:** Navigation should be immediate, undo still works
- **Using context after async without mounted check:** Always check `context.mounted` after await

## Don't Hand-Roll

Problems with existing solutions that should NOT be custom-built:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Undo timer | Custom countdown/lifecycle management | `Timer` class with `cancel()` | Handles edge cases, cancellation |
| Cascade delete logic | Manual deletion of related records | Database ON DELETE CASCADE | Already configured, atomic, faster |
| Confirmation dialogs | Custom modal/bottom sheet | AlertDialog with showDialog | Material pattern, accessible |
| SnackBar display | Custom toast/notification | ScaffoldMessenger.showSnackBar | Handles queue, duration, actions |
| List item removal animation | Manual AnimatedList management | Simple ListView with optimistic state | ListView rebuilds efficiently |

**Key insight:** The 10-second undo window is best implemented as frontend-held state (item removed from list, pending actual deletion) rather than database soft delete. This avoids modifying all queries to filter deleted items.

## Common Pitfalls

### Pitfall 1: SnackBar Auto-Dismiss with Actions
**What goes wrong:** SnackBar stays on screen forever when action is set
**Why it happens:** Flutter issue - SnackBar may not auto-dismiss with actions in some versions
**How to avoid:**
- Explicitly set `duration: const Duration(seconds: 10)`
- Timer handles actual deletion regardless of SnackBar state
- Call `ScaffoldMessenger.of(context).clearSnackBars()` before showing new one
**Warning signs:** SnackBar persists indefinitely after 10 seconds

### Pitfall 2: BuildContext After Timer Callback
**What goes wrong:** "deactivated widget" error when showing error SnackBar
**Why it happens:** User navigated away, Timer callback fires with stale context
**How to avoid:**
- Store a `BuildContext` reference carefully, or use `GlobalKey<ScaffoldMessengerState>`
- Check `context.mounted` before using context in timer callback
- Consider using provider-level error state instead of direct SnackBar
**Warning signs:** Random crashes after navigation during undo window

### Pitfall 3: Race Condition with Multiple Deletes
**What goes wrong:** Undo restores wrong item, or items lost
**Why it happens:** Multiple items deleted before undo expires
**How to avoid:**
- Cancel previous timer when new delete initiated
- Clear previous pending delete (commit it immediately)
- Or queue deletes and restore in LIFO order
**Warning signs:** Wrong item restored on undo

### Pitfall 4: Orphaned Data After Failed Delete
**What goes wrong:** Item removed from UI but backend delete failed, user loses data
**Why it happens:** No rollback logic when API call fails
**How to avoid:**
- Always implement rollback: restore item to list on error
- Show error SnackBar explaining failure
- Don't clear pending delete until API confirms success
**Warning signs:** Data disappears, user reports lost work

### Pitfall 5: Cascade Delete Missing in SQLite
**What goes wrong:** Parent deleted but children remain (orphaned records)
**Why it happens:** SQLite requires `PRAGMA foreign_keys = ON` for each connection
**How to avoid:**
- Already handled in `database.py` via event listener
- Verify with test: delete project, query threads for that project_id
- Use `passive_deletes=True` on relationships to let DB handle it
**Warning signs:** Database grows with orphaned records over time

### Pitfall 6: Delete Button Placement Consistency
**What goes wrong:** Users can't find delete, or accidentally delete
**Why it happens:** Inconsistent placement across screens
**How to avoid:**
- Consistent placement: header/toolbar icon on detail screens, swipe or long-press on list items
- Consider "..." menu with delete option (less accidental)
- CONTEXT.md leaves this to Claude's discretion
**Warning signs:** User feedback about accidental deletes or hidden delete

## Code Examples

Verified patterns from the existing codebase:

### Backend: DELETE Project Endpoint
```python
# Source: Extension of existing projects.py
from fastapi import Response

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete project with cascade to threads, documents, messages."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project or project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    await db.delete(project)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### Backend: DELETE Thread Endpoint
```python
# Source: Extension of existing threads.py
@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete thread with cascade to messages and artifacts."""
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread or thread.project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    await db.delete(thread)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### Backend: DELETE Document Endpoint
```python
# Source: Extension of existing documents.py
@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document from project."""
    stmt = select(Document).join(Project).where(
        Document.id == document_id,
        Project.user_id == current_user["user_id"]
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    await db.delete(doc)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### Backend: DELETE Message Endpoint
```python
# Source: Extension of conversations.py
@router.delete(
    "/threads/{thread_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_message(
    thread_id: str,
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a single message from thread."""
    # Verify thread belongs to user
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread or thread.project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    # Find and delete message
    stmt = select(Message).where(
        Message.id == message_id,
        Message.thread_id == thread_id
    )
    message = (await db.execute(stmt)).scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    await db.delete(message)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### Frontend: Service Delete Methods
```dart
// Source: Pattern from existing project_service.dart
// Add to ProjectService
Future<void> deleteProject(String id) async {
  try {
    final headers = await _getHeaders();
    await _dio.delete(
      '$_baseUrl/api/projects/$id',
      options: Options(headers: headers),
    );
  } on DioException catch (e) {
    if (e.response?.statusCode == 401) {
      throw Exception('Unauthorized - please login again');
    } else if (e.response?.statusCode == 404) {
      throw Exception('Project not found');
    }
    throw Exception('Failed to delete project: ${e.message}');
  }
}

// Similar pattern for ThreadService, DocumentService
```

### Frontend: Provider Delete with Undo
```dart
// Source: Pattern combining optimistic state and existing provider patterns
import 'dart:async';

class ProjectProvider extends ChangeNotifier {
  // ... existing fields ...

  /// Item pending deletion (during undo window)
  Project? _pendingDelete;

  /// Timer for deferred deletion
  Timer? _deleteTimer;

  /// Delete project with optimistic UI and undo support
  ///
  /// Immediately removes from list, shows SnackBar with undo.
  /// Actual deletion happens after 10 seconds unless undone.
  Future<void> deleteProject(BuildContext context, String projectId) async {
    // Find project in list
    final index = _projects.indexWhere((p) => p.id == projectId);
    if (index == -1) return;

    // Cancel any previous pending delete (commit it immediately)
    if (_pendingDelete != null) {
      await _commitPendingDelete();
    }

    // Remove optimistically
    _pendingDelete = _projects[index];
    _projects.removeAt(index);

    // Clear selected if it was the deleted project
    if (_selectedProject?.id == projectId) {
      _selectedProject = null;
    }

    notifyListeners();

    // Show undo SnackBar
    if (context.mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Project deleted'),
          duration: const Duration(seconds: 10),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: () => _undoDelete(),
          ),
        ),
      );
    }

    // Start deletion timer
    _deleteTimer?.cancel();
    _deleteTimer = Timer(const Duration(seconds: 10), () {
      _commitPendingDelete();
    });
  }

  void _undoDelete() {
    _deleteTimer?.cancel();
    if (_pendingDelete != null) {
      _projects.insert(0, _pendingDelete!);
      _pendingDelete = null;
      notifyListeners();
    }
  }

  Future<void> _commitPendingDelete() async {
    if (_pendingDelete == null) return;

    final projectToDelete = _pendingDelete!;
    _pendingDelete = null;

    try {
      await _projectService.deleteProject(projectToDelete.id);
    } catch (e) {
      // Rollback: restore to list
      _projects.insert(0, projectToDelete);
      _error = 'Failed to delete project: $e';
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _deleteTimer?.cancel();
    super.dispose();
  }
}
```

### Frontend: Reusable Confirmation Dialog
```dart
// Source: Pattern from settings_screen.dart logout confirmation
// CONTEXT.md decisions applied

/// Show delete confirmation dialog
///
/// Returns true if user confirms deletion, false otherwise.
/// Follows CONTEXT.md: summary cascade info, neutral style, Delete/Cancel buttons.
Future<bool> showDeleteConfirmationDialog({
  required BuildContext context,
  required String itemType,
  String? cascadeMessage,
}) async {
  final confirmed = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (BuildContext dialogContext) {
      return AlertDialog(
        title: Text('Delete this $itemType?'),
        content: cascadeMessage != null ? Text(cascadeMessage) : null,
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Delete'),
          ),
        ],
      );
    },
  );

  return confirmed ?? false;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Database soft delete with `deleted_at` column | Frontend-held undo with timer | Always for short-term undo | Simpler queries, no schema changes |
| Synchronous delete then confirm | Optimistic UI with rollback | Modern UX pattern | Faster perceived performance |
| Custom undo UI | SnackBar with SnackBarAction | Flutter standard | Consistent Material behavior |

**Deprecated/outdated:**
- `Scaffold.of(context).showSnackBar()` - Use `ScaffoldMessenger.of(context)` instead
- Manual orphan cleanup after delete - Use database cascade deletes

## Database Schema Analysis

### Existing Foreign Key Configuration
The database already has proper cascade delete configuration:

```python
# From models.py - Project relationships
documents: Mapped[List["Document"]] = relationship(
    back_populates="project",
    cascade="all, delete-orphan",
    passive_deletes=True
)
threads: Mapped[List["Thread"]] = relationship(
    back_populates="project",
    cascade="all, delete-orphan",
    passive_deletes=True
)

# Thread relationships
messages: Mapped[List["Message"]] = relationship(
    back_populates="thread",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
artifacts: Mapped[List["Artifact"]] = relationship(
    back_populates="thread",
    cascade="all, delete-orphan",
    passive_deletes=True,
)

# Foreign keys with ondelete="CASCADE"
project_id: Mapped[str] = mapped_column(
    String(36),
    ForeignKey("projects.id", ondelete="CASCADE"),
    ...
)
```

### PRAGMA foreign_keys Verification
Already enabled in `database.py`:

```python
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Cascade Relationships Summary
| Parent | Children | Delete Cascade |
|--------|----------|----------------|
| Project | Documents, Threads | Yes (ON DELETE CASCADE) |
| Thread | Messages, Artifacts | Yes (ON DELETE CASCADE) |
| User | Projects, TokenUsage | Yes (ON DELETE CASCADE) |

## Open Questions

1. **Delete Button Placement (Claude's Discretion)**
   - What we know: CONTEXT.md leaves this to discretion
   - Options: Swipe-to-delete on list items, context menu, icon in detail header
   - Recommendation: Icon button in detail screen header (consistent, discoverable, hard to trigger accidentally), optional swipe on list items for power users

2. **Multiple Pending Deletes**
   - What we know: Timer-based undo with single pending delete
   - What's unclear: What if user deletes 3 items in quick succession?
   - Recommendation: Commit previous pending delete immediately when new delete initiated (simplest, predictable)

3. **Navigation After Delete from Detail Screen**
   - What we know: Need to leave detail screen after deleting current item
   - What's unclear: Should navigation wait for undo window? What if user undoes after navigation?
   - Recommendation: Navigate immediately to parent, undo still works (restores item, user can navigate back)

## Sources

### Primary (HIGH confidence)
- [Flutter Official Optimistic State Pattern](https://docs.flutter.dev/app-architecture/design-patterns/optimistic-state) - Official Flutter documentation for optimistic UI updates
- [SQLAlchemy Cascades Documentation](https://docs.sqlalchemy.org/en/21/orm/cascades.html) - Authoritative source for cascade delete configuration
- Existing codebase: `database.py`, `models.py`, `settings_screen.dart` - Established patterns

### Secondary (MEDIUM confidence)
- [Flutter SnackBar API](https://api.flutter.dev/flutter/material/SnackBar-class.html) - SnackBar with action patterns
- [Flutter AlertDialog API](https://api.flutter.dev/flutter/material/AlertDialog-class.html) - Confirmation dialog patterns
- [SQLModel Cascade Delete](https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/cascade-delete-relationships/) - Additional cascade delete examples

### Tertiary (LOW confidence)
- [Medium: Optimistic State in Flutter](https://medium.com/@geraldnuraj/optimistic-state-in-flutter-explained-3dec68ae6252) - Community pattern explanation
- [Flutter Mastery: Optimistic UI Updates](https://fluttermasterylibrary.com/7/9/3/1/) - Additional examples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new packages required, all patterns verified from existing code
- Architecture: HIGH - Follows established provider/service patterns in codebase
- Backend changes: HIGH - Clear extension of existing endpoints, cascade already configured
- Undo mechanism: HIGH - Flutter SnackBar + Timer is standard, well-documented pattern
- Pitfalls: MEDIUM - Based on common Flutter async/state issues and SQLite foreign key behavior

**Research date:** 2026-01-30
**Valid until:** 2026-03-30 (60 days - stable patterns, no external dependencies changing)
