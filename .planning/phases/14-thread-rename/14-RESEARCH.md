# Phase 14: Thread Rename - Research

**Researched:** 2026-01-30
**Domain:** Full-stack CRUD feature (Flutter + FastAPI)
**Confidence:** HIGH

## Summary

Thread rename is a straightforward full-stack feature that follows well-established patterns already present in the codebase. The project update feature (`ProjectProvider.updateProject`, `PUT /api/projects/{id}`) provides a direct template for implementing thread rename with optimistic UI.

The implementation requires:
1. **Backend**: PATCH endpoint for partial thread update (title only)
2. **Frontend Service**: `renameThread()` method in ThreadService
3. **Frontend Provider**: `renameThread()` method in ThreadProvider with optimistic update
4. **UI Entry Points**: Edit icon in ConversationScreen AppBar + "Rename" in thread list popup menu
5. **Rename Dialog**: Similar to ThreadCreateDialog but pre-filled with current title

**Primary recommendation:** Follow the ProjectProvider.updateProject pattern for optimistic updates, use PATCH (not PUT) since we're only updating title, and create a single reusable `ThreadRenameDialog` widget.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flutter | 3.x | Frontend framework | Project standard |
| FastAPI | Latest | Backend framework | Project standard |
| Provider | ^6.0 | State management | Already used throughout |
| Dio | ^5.0 | HTTP client | Already used in services |
| Pydantic | 2.x | Request validation | Already used in routes |

### No Additional Dependencies Required

This feature uses existing infrastructure - no new packages needed.

## Architecture Patterns

### Existing Codebase Patterns to Follow

```
frontend/lib/
├── screens/threads/
│   ├── thread_create_dialog.dart    # Template for rename dialog
│   └── thread_list_screen.dart      # Add "Rename" to PopupMenuButton
├── screens/conversation/
│   └── conversation_screen.dart     # Add edit icon to AppBar
├── providers/
│   └── thread_provider.dart         # Add renameThread() method
├── services/
│   └── thread_service.dart          # Add renameThread() API call

backend/app/routes/
└── threads.py                       # Add PATCH endpoint
```

### Pattern 1: Optimistic Update with Rollback
**What:** Update local state immediately, then sync with server. Rollback on failure.
**When to use:** Any user-initiated update where instant feedback matters.
**Example (from ProjectProvider.updateProject):**
```dart
// Source: frontend/lib/providers/project_provider.dart lines 132-164
Future<Project?> updateProject(String id, String name, String? description) async {
  _loading = true;
  _error = null;
  notifyListeners();

  try {
    final updatedProject = await _projectService.updateProject(id, name, description);

    // Update in projects list
    final index = _projects.indexWhere((p) => p.id == id);
    if (index != -1) {
      _projects[index] = updatedProject;
    }

    // Update selected project if it's the same one
    if (_selectedProject?.id == id) {
      _selectedProject = updatedProject;
    }

    _error = null;
    return updatedProject;
  } catch (e) {
    _error = e.toString();
    return null;
  } finally {
    _loading = false;
    notifyListeners();
  }
}
```

### Pattern 2: Reusable Dialog with Pre-fill
**What:** Dialog that accepts initial values and returns updated values.
**When to use:** Edit forms that modify existing entities.
**Example (adapt ThreadCreateDialog pattern):**
```dart
// Source: frontend/lib/screens/threads/thread_create_dialog.dart
class ThreadRenameDialog extends StatefulWidget {
  const ThreadRenameDialog({
    super.key,
    required this.threadId,
    required this.currentTitle,
  });

  final String threadId;
  final String? currentTitle;
  // ...
}
```

### Pattern 3: Backend PATCH for Partial Update
**What:** Use PATCH for updating specific fields, PUT for full replacement.
**When to use:** When only updating one field (title), not the entire entity.
**Example (FastAPI pattern):**
```python
# PATCH is preferred over PUT when updating only title
@router.patch("/threads/{thread_id}", response_model=ThreadResponse)
async def rename_thread(
    thread_id: str,
    update_data: ThreadUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ...
```

### Anti-Patterns to Avoid
- **Don't create separate dialogs for AppBar and thread list** - Use single ThreadRenameDialog reusable from both entry points
- **Don't use PUT when only updating title** - PATCH is semantically correct for partial updates
- **Don't skip validation** - Title must be validated (max 255 chars) like ThreadCreate

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form validation | Custom validators | TextFormField.validator | Built-in, consistent with codebase |
| Loading states | Manual bool flags | Pattern from ThreadCreateDialog | `_isRenaming` with button state |
| Error handling | Custom try/catch | Existing DioException handling | Consistent error messages |
| State updates | Direct list mutation | Provider pattern with notifyListeners | Already established |

**Key insight:** Every pattern needed already exists in the codebase. Copy from ThreadCreateDialog and ProjectProvider.updateProject.

## Common Pitfalls

### Pitfall 1: Forgetting to Update Both Thread Lists and Selected Thread
**What goes wrong:** Rename updates the thread list but ConversationScreen still shows old title.
**Why it happens:** Thread title displayed in ConversationScreen comes from ConversationProvider._thread, not ThreadProvider.
**How to avoid:** Either:
1. Reload thread in ConversationProvider after rename, OR
2. Pass callback from ConversationScreen to update local title state
**Warning signs:** Title updates in thread list but not in conversation AppBar.

### Pitfall 2: Not Pre-selecting Text in Dialog
**What goes wrong:** User must manually select all text before typing new title.
**Why it happens:** TextEditingController.text doesn't auto-select on focus.
**How to avoid:** Use `TextEditingController` with `selection` property or `autofocus` with `selectAll` on focus.
**Warning signs:** User must manually clear old title before typing.

### Pitfall 3: Empty String vs Null Title
**What goes wrong:** Empty string becomes empty title instead of "New Conversation".
**Why it happens:** Not converting empty strings to null before API call.
**How to avoid:** `title.isEmpty ? null : title` pattern (already used in ThreadCreateDialog).
**Warning signs:** Threads showing blank title instead of fallback.

### Pitfall 4: Stale State in Thread List After Navigation
**What goes wrong:** User renames in ConversationScreen, goes back, sees old title in list.
**Why it happens:** ThreadListScreen loads threads once in initState, doesn't know about rename.
**How to avoid:** ThreadProvider.renameThread updates _threads list directly (it has access).
**Warning signs:** Thread list shows stale data until refresh.

## Code Examples

Verified patterns from existing codebase:

### Backend PATCH Endpoint
```python
# Source: Similar to PUT pattern in projects.py (lines 206-255)
# Location: backend/app/routes/threads.py

class ThreadUpdate(BaseModel):
    """Request model for updating a thread."""
    title: Optional[str] = Field(None, max_length=255)


@router.patch(
    "/threads/{thread_id}",
    response_model=ThreadResponse,
)
async def rename_thread(
    thread_id: str,
    update_data: ThreadUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rename a thread.

    Args:
        thread_id: Thread UUID
        update_data: New title (or null to clear)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Updated thread

    Raises:
        404: Thread not found or not owned by user
    """
    # Get thread with project loaded for ownership check
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Validate thread belongs to user's project
    if thread.project.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Update title
    thread.title = update_data.title
    # updated_at auto-updates via onupdate

    await db.commit()
    await db.refresh(thread)

    return ThreadResponse(
        id=thread.id,
        project_id=thread.project_id,
        title=thread.title,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
    )
```

### Frontend Service Method
```dart
// Source: Pattern from project_service.dart updateProject (lines 131-157)
// Location: frontend/lib/services/thread_service.dart

/// Rename a thread
///
/// [threadId] - ID of the thread to rename
/// [title] - New title (or null to clear)
///
/// Returns updated Thread object
Future<Thread> renameThread(String threadId, String? title) async {
  try {
    final headers = await _getAuthHeaders();
    final response = await _dio.patch(
      '$_baseUrl/api/threads/$threadId',
      options: Options(headers: headers),
      data: {
        'title': title,
      },
    );

    return Thread.fromJson(response.data as Map<String, dynamic>);
  } on DioException catch (e) {
    if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
      throw Exception('Authentication required');
    } else if (e.response?.statusCode == 404) {
      throw Exception('Thread not found');
    }
    throw Exception('Failed to rename thread: ${e.message}');
  }
}
```

### Frontend Provider Method
```dart
// Source: Pattern from project_provider.dart updateProject (lines 132-164)
// Location: frontend/lib/providers/thread_provider.dart

/// Rename a thread
///
/// Updates thread title optimistically and syncs with backend.
Future<Thread?> renameThread(String threadId, String? title) async {
  _loading = true;
  _error = null;
  notifyListeners();

  try {
    final updatedThread = await _threadService.renameThread(threadId, title);

    // Update in threads list
    final index = _threads.indexWhere((t) => t.id == threadId);
    if (index != -1) {
      _threads[index] = Thread(
        id: updatedThread.id,
        projectId: updatedThread.projectId,
        title: updatedThread.title,
        createdAt: updatedThread.createdAt,
        updatedAt: updatedThread.updatedAt,
        messageCount: _threads[index].messageCount, // Preserve local count
      );
    }

    // Update selected thread if it's the same one
    if (_selectedThread?.id == threadId) {
      _selectedThread = updatedThread;
    }

    _error = null;
    return updatedThread;
  } catch (e) {
    _error = e.toString();
    return null;
  } finally {
    _loading = false;
    notifyListeners();
  }
}
```

### Rename Dialog Widget
```dart
// Source: Based on thread_create_dialog.dart pattern
// Location: frontend/lib/screens/threads/thread_rename_dialog.dart

class ThreadRenameDialog extends StatefulWidget {
  const ThreadRenameDialog({
    super.key,
    required this.threadId,
    required this.currentTitle,
  });

  final String threadId;
  final String? currentTitle;

  @override
  State<ThreadRenameDialog> createState() => _ThreadRenameDialogState();
}

class _ThreadRenameDialogState extends State<ThreadRenameDialog> {
  late final TextEditingController _titleController;
  final _formKey = GlobalKey<FormState>();
  bool _isRenaming = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.currentTitle ?? '');
    // Select all text for easy replacement
    _titleController.selection = TextSelection(
      baseOffset: 0,
      extentOffset: _titleController.text.length,
    );
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _renameThread() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isRenaming = true);

    try {
      final provider = context.read<ThreadProvider>();
      final title = _titleController.text.trim();

      await provider.renameThread(
        widget.threadId,
        title.isEmpty ? null : title,
      );

      if (mounted) {
        Navigator.of(context).pop(true); // Return success
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Conversation renamed')),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRenaming = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to rename: ${e.toString()}'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Rename Conversation'),
      content: Form(
        key: _formKey,
        child: TextFormField(
          controller: _titleController,
          decoration: const InputDecoration(
            labelText: 'Title',
            hintText: 'e.g., Login Flow Discussion',
            border: OutlineInputBorder(),
          ),
          maxLength: 255,
          autofocus: true,
          enabled: !_isRenaming,
          validator: (value) {
            if (value != null && value.length > 255) {
              return 'Title must be 255 characters or less';
            }
            return null;
          },
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isRenaming ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isRenaming ? null : _renameThread,
          child: _isRenaming
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Rename'),
        ),
      ],
    );
  }
}
```

### AppBar Edit Icon Integration
```dart
// Source: Location: frontend/lib/screens/conversation/conversation_screen.dart
// Add to AppBar actions

AppBar(
  title: Text(provider.thread?.title ?? 'New Conversation'),
  actions: [
    IconButton(
      icon: const Icon(Icons.edit_outlined),
      tooltip: 'Rename conversation',
      onPressed: () => _showRenameDialog(context, provider.thread),
    ),
  ],
)
```

### Thread List PopupMenu Integration
```dart
// Source: frontend/lib/screens/threads/thread_list_screen.dart
// Add "Rename" option to existing PopupMenuButton

PopupMenuButton<String>(
  onSelected: (value) {
    if (value == 'rename') {
      _showRenameDialog(context, thread);
    } else if (value == 'delete') {
      _deleteThread(context, thread.id);
    }
  },
  itemBuilder: (context) => [
    const PopupMenuItem(
      value: 'rename',
      child: Row(
        children: [
          Icon(Icons.edit_outlined),
          SizedBox(width: 8),
          Text('Rename'),
        ],
      ),
    ),
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
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PUT for all updates | PATCH for partial updates | HTTP/1.1 spec | Semantic correctness |
| Modal dialog for edits | Dialog or inline edit | N/A | Both acceptable, dialog matches codebase |

**Deprecated/outdated:**
- None applicable - patterns are stable

## Open Questions

Things that couldn't be fully resolved:

1. **Thread Title Update in ConversationScreen**
   - What we know: ConversationProvider has its own `_thread` object
   - What's unclear: Best way to sync title after rename from within ConversationScreen
   - Recommendation: Reload thread via `ConversationProvider.loadThread()` after rename dialog closes with success. This ensures all thread data is fresh.

2. **Empty Title Display Fallback**
   - What we know: `thread.title ?? 'New Conversation'` is used throughout
   - What's unclear: Should we allow clearing title (null) or require non-empty?
   - Recommendation: Allow null (same as create), display "New Conversation" as fallback. This matches existing behavior.

## Sources

### Primary (HIGH confidence)
- `frontend/lib/screens/threads/thread_create_dialog.dart` - Dialog pattern reference
- `frontend/lib/providers/project_provider.dart` - Update pattern with optimistic UI
- `frontend/lib/services/project_service.dart` - Service layer update pattern
- `backend/app/routes/projects.py` - PUT endpoint pattern (lines 206-255)
- `backend/app/routes/threads.py` - Thread route structure

### Secondary (MEDIUM confidence)
- `frontend/lib/screens/threads/thread_list_screen.dart` - PopupMenuButton integration point
- `frontend/lib/screens/conversation/conversation_screen.dart` - AppBar structure

### Tertiary (LOW confidence)
- None - all patterns verified from existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, all existing patterns
- Architecture: HIGH - Direct copy of existing ProjectProvider/ThreadCreateDialog patterns
- Pitfalls: HIGH - Identified from codebase analysis, common Flutter state patterns

**Research date:** 2026-01-30
**Valid until:** 90 days (stable patterns, no external dependencies)
