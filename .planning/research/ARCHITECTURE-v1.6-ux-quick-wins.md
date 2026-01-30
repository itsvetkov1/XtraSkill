# Architecture Patterns: v1.6 UX Quick Wins Integration

**Project:** BA Assistant v1.6 UX Quick Wins
**Researched:** 2026-01-30
**Confidence:** HIGH (based on existing codebase analysis)

## Executive Summary

This document describes how four UX quick wins features integrate with the existing Flutter Provider architecture:

1. **Retry failed AI messages** - ConversationProvider enhancement
2. **Copy AI responses** - UI-only (Clipboard API), no provider changes
3. **Rename threads** - ThreadProvider + ThreadService + Backend API
4. **Show auth provider icon** - AuthProvider read-only access

The existing architecture is well-structured with clear separation of concerns. All four features fit naturally into the current patterns with minimal architectural changes.

## Current Architecture Overview

```
+---------------------------------------------------------------------+
|                           main.dart                                  |
|                       (MultiProvider root)                           |
+---------------------------------------------------------------------+
|  Providers (ChangeNotifier)                                          |
|  +-- AuthProvider        - OAuth state, user info                    |
|  +-- ProjectProvider     - Project CRUD, selection                   |
|  +-- ThreadProvider      - Thread CRUD, selection                    |
|  +-- ConversationProvider- Messages, streaming, errors               |
|  +-- DocumentProvider    - Document uploads                          |
|  +-- ThemeProvider       - Light/dark mode                           |
|  +-- NavigationProvider  - Sidebar expanded state                    |
+---------------------------------------------------------------------+
|  Services (API layer)                                                |
|  +-- AuthService         - OAuth flows, token storage                |
|  +-- ProjectService      - Project API calls                         |
|  +-- ThreadService       - Thread API calls                          |
|  +-- AIService           - SSE streaming, message delete             |
+---------------------------------------------------------------------+
|  UI Screens                                                          |
|  +-- conversation_screen.dart                                        |
|  |   +-- widgets/                                                    |
|  |       +-- message_bubble.dart    <-- Copy button goes here        |
|  |       +-- streaming_message.dart                                  |
|  |       +-- chat_input.dart                                         |
|  +-- threads/                                                        |
|  |   +-- thread_list_screen.dart    <-- Rename menu option goes here |
|  +-- settings_screen.dart           <-- Auth provider icon goes here |
+---------------------------------------------------------------------+
```

## Feature 1: Retry Failed AI Messages

### Component Boundaries

| Component | Responsibility | Changes Required |
|-----------|----------------|------------------|
| **ConversationProvider** | Store failed message state, expose retry method | Add `_failedMessage`, `canRetry`, `retryLastMessage()` |
| **AIService** | No changes | Existing `streamChat()` handles retry |
| **ConversationScreen** | Show retry button when error + failed message | Add retry button to error banner |
| **MessageBubble** | No changes | Failed message displays normally |

### Data Flow

```
User sends message
    |
    v
ConversationProvider.sendMessage(content)
    |
    +-- Stores _pendingUserMessage (for retry)
    |
    v
AIService.streamChat(threadId, content)
    |
    +-- SUCCESS: _pendingUserMessage = null
    |
    +-- FAILURE:
        +-- _error = "Connection error: ..."
        +-- _failedMessage = _pendingUserMessage (preserved for retry)

User taps "Retry"
    |
    v
ConversationProvider.retryLastMessage()
    |
    +-- Reuses _failedMessage.content
    +-- Calls sendMessage() internally
```

### Implementation Strategy

```dart
// ConversationProvider additions
class ConversationProvider extends ChangeNotifier {
  // Existing fields...

  /// Message that failed to send (preserved for retry)
  Message? _failedMessage;

  /// Whether retry is available
  bool get canRetry => _failedMessage != null && !_isStreaming;

  /// Retry the last failed message
  Future<void> retryLastMessage() async {
    if (_failedMessage == null) return;

    final content = _failedMessage!.content;

    // Remove failed user message from list (will be re-added by sendMessage)
    _messages.removeWhere((m) => m.id == _failedMessage!.id);
    _failedMessage = null;
    _error = null;
    notifyListeners();

    // Retry sending
    await sendMessage(content);
  }

  // Modify sendMessage() to track pending message
  Future<void> sendMessage(String content) async {
    // ... existing code ...

    // Store reference for potential retry
    _pendingUserMessage = userMessage;

    try {
      await for (final event in _aiService.streamChat(...)) {
        // ... existing event handling ...

        if (event is MessageCompleteEvent) {
          _pendingUserMessage = null; // Success, clear pending
          // ... existing code ...
        } else if (event is ErrorEvent) {
          _failedMessage = _pendingUserMessage; // Preserve for retry
          // ... existing error handling ...
        }
      }
    } catch (e) {
      _failedMessage = _pendingUserMessage; // Preserve for retry
      // ... existing error handling ...
    }
  }
}
```

### UI Integration

```dart
// conversation_screen.dart - Error banner with retry button
if (provider.error != null)
  MaterialBanner(
    content: SelectableText(provider.error!),
    backgroundColor: Theme.of(context).colorScheme.errorContainer,
    actions: [
      if (provider.canRetry)
        TextButton(
          onPressed: provider.retryLastMessage,
          child: const Text('Retry'),
        ),
      TextButton(
        onPressed: provider.clearError,
        child: const Text('Dismiss'),
      ),
    ],
  ),
```

### No Backend Changes Required

Retry uses existing `streamChat()` endpoint with same payload.

---

## Feature 2: Copy AI Response Button

### Component Boundaries

| Component | Responsibility | Changes Required |
|-----------|----------------|------------------|
| **MessageBubble** | Display message + copy button for assistant | Add IconButton with Clipboard.setData() |
| **Clipboard API** | Flutter services/clipboard.dart | None (use existing) |
| **ConversationProvider** | None | No state management needed |

### Data Flow

```
User taps copy button on assistant message
    |
    v
Clipboard.setData(ClipboardData(text: message.content))
    |
    v
Show SnackBar: "Copied to clipboard"
```

### Implementation Strategy

This is UI-only - no provider or service changes required.

```dart
// message_bubble.dart modification
class MessageBubble extends StatelessWidget {
  final Message message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final isAssistant = message.role == MessageRole.assistant;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        // ... existing container styling ...
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            SelectableText(message.content, /* ... */),

            // Copy button for assistant messages only
            if (isAssistant) ...[
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerRight,
                child: IconButton(
                  icon: const Icon(Icons.copy, size: 18),
                  tooltip: 'Copy to clipboard',
                  style: IconButton.styleFrom(
                    minimumSize: const Size(32, 32),
                    padding: EdgeInsets.zero,
                  ),
                  onPressed: () async {
                    await Clipboard.setData(
                      ClipboardData(text: message.content),
                    );
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Copied to clipboard'),
                          duration: Duration(seconds: 2),
                        ),
                      );
                    }
                  },
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

### Alternative: Hover-Reveal Pattern

For cleaner UI, show copy button only on hover (desktop) or long-press menu (mobile):

```dart
// Desktop: MouseRegion with hover state
// Mobile: Include in existing long-press bottom sheet
```

Recommend starting with always-visible button for v1.6, then polish to hover-reveal in future milestone.

---

## Feature 3: Rename Thread Dialog

### Component Boundaries

| Component | Responsibility | Changes Required |
|-----------|----------------|------------------|
| **ThreadProvider** | Expose `updateThread()` method | Add `updateThread(threadId, title)` |
| **ThreadService** | Add `updateThread()` API call | Add PATCH `/threads/{id}` call |
| **Backend threads.py** | Add PATCH endpoint | Add `update_thread()` route |
| **ThreadListScreen** | Show rename option in popup menu | Add menu item + dialog |
| **ConversationScreen** | Optionally show rename in AppBar | Add edit icon button |

### Data Flow

```
User taps "Rename" in thread menu
    |
    v
Show AlertDialog with TextField (pre-filled with current title)
    |
    v
User edits title, taps "Save"
    |
    v
ThreadProvider.updateThread(threadId, newTitle)
    |
    +-- Optimistic update: Update thread in _threads list
    |
    v
ThreadService.updateThread(threadId, newTitle)
    |
    v
Backend PATCH /api/threads/{threadId}
    |
    +-- SUCCESS: notifyListeners() (already done optimistically)
    |
    +-- FAILURE: Rollback to original title, show error
```

### Backend API Addition

```python
# backend/app/routes/threads.py - ADD this endpoint

class ThreadUpdate(BaseModel):
    """Request model for updating a thread."""
    title: Optional[str] = Field(None, max_length=255)


@router.patch(
    "/threads/{thread_id}",
    response_model=ThreadResponse,
)
async def update_thread(
    thread_id: str,
    thread_data: ThreadUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update thread title.

    Args:
        thread_id: ID of the thread to update
        thread_data: Fields to update (currently only title)
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        Updated thread

    Raises:
        404: Thread not found or doesn't belong to user's project
        400: Invalid title length
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

    # Update fields
    if thread_data.title is not None:
        thread.title = thread_data.title if thread_data.title else None

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

### Service Layer Addition

```dart
// thread_service.dart - ADD this method

/// Update thread title
///
/// [threadId] - ID of the thread to update
/// [title] - New title (null to clear title)
///
/// Returns updated Thread object
/// Throws exception if request fails or unauthorized
Future<Thread> updateThread(String threadId, String? title) async {
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
    } else if (e.response?.statusCode == 400) {
      throw Exception('Invalid title');
    }
    throw Exception('Failed to update thread: ${e.message}');
  }
}
```

### Provider Layer Addition

```dart
// thread_provider.dart - ADD this method

/// Update thread title with optimistic UI
///
/// [threadId] - ID of the thread to update
/// [title] - New title (null to clear)
Future<void> updateThread(String threadId, String? title) async {
  // Find thread in list
  final index = _threads.indexWhere((t) => t.id == threadId);
  if (index == -1) return;

  // Store original for rollback
  final originalThread = _threads[index];

  // Optimistic update
  _threads[index] = Thread(
    id: originalThread.id,
    projectId: originalThread.projectId,
    title: title,
    createdAt: originalThread.createdAt,
    updatedAt: DateTime.now(),
    messageCount: originalThread.messageCount,
    messages: originalThread.messages,
  );
  notifyListeners();

  try {
    final updatedThread = await _threadService.updateThread(threadId, title);

    // Update with server response (for accurate timestamps)
    _threads[index] = updatedThread;

    // Update selected thread if it's the same one
    if (_selectedThread?.id == threadId) {
      _selectedThread = updatedThread;
    }

    notifyListeners();
  } catch (e) {
    // Rollback on failure
    _threads[index] = originalThread;
    _error = 'Failed to rename: $e';
    notifyListeners();
    rethrow;
  }
}
```

### UI Integration

```dart
// thread_list_screen.dart - Modify PopupMenuButton

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
          Icon(Icons.edit),
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
),

// Rename dialog method
void _showRenameDialog(BuildContext context, Thread thread) {
  final controller = TextEditingController(text: thread.title ?? '');
  final formKey = GlobalKey<FormState>();

  showDialog(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('Rename Conversation'),
      content: Form(
        key: formKey,
        child: TextFormField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Title',
            hintText: 'Enter conversation title',
            border: OutlineInputBorder(),
          ),
          autofocus: true,
          maxLength: 255,
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
          onPressed: () => Navigator.of(dialogContext).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () async {
            if (formKey.currentState!.validate()) {
              Navigator.of(dialogContext).pop();
              try {
                await context.read<ThreadProvider>().updateThread(
                  thread.id,
                  controller.text.isEmpty ? null : controller.text,
                );
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Conversation renamed')),
                  );
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Failed to rename: $e'),
                      backgroundColor: Theme.of(context).colorScheme.error,
                    ),
                  );
                }
              }
            }
          },
          child: const Text('Save'),
        ),
      ],
    ),
  );
}
```

---

## Feature 4: Show Auth Provider Icon

### Component Boundaries

| Component | Responsibility | Changes Required |
|-----------|----------------|------------------|
| **AuthProvider** | Expose `oauthProvider` getter | Parse from `/auth/me` response (already available) |
| **SettingsScreen** | Display provider icon next to email | Add icon based on provider |
| **Backend auth.py** | Already returns oauth_provider | No changes needed |

### Data Flow

```
App startup / Auth callback
    |
    v
AuthProvider.handleCallback() or checkAuthStatus()
    |
    v
AuthService.getCurrentUser()
    |
    v
Backend GET /auth/me returns { id, email, oauth_provider, display_name }
    |
    v
AuthProvider stores oauth_provider
    |
    v
SettingsScreen reads authProvider.oauthProvider
    |
    v
Display Google or Microsoft icon
```

### Implementation Strategy

**Step 1: Add oauthProvider to AuthProvider**

```dart
// auth_provider.dart - ADD field and getter

class AuthProvider extends ChangeNotifier {
  // Existing fields...
  String? _oauthProvider;  // "google" or "microsoft"

  /// OAuth provider used for authentication
  String? get oauthProvider => _oauthProvider;

  // Modify handleCallback and checkAuthStatus to store provider
  Future<void> handleCallback(String token) async {
    // ... existing code ...

    final user = await _authService.getCurrentUser();
    _userId = user['id'] as String?;
    _email = user['email'] as String?;
    _displayName = user['display_name'] as String?;
    _oauthProvider = user['oauth_provider'] as String?;  // ADD THIS

    // ... rest of existing code ...
  }

  Future<void> checkAuthStatus() async {
    // ... existing code ...

    if (isValid) {
      final user = await _authService.getCurrentUser();
      _userId = user['id'] as String?;
      _email = user['email'] as String?;
      _displayName = user['display_name'] as String?;
      _oauthProvider = user['oauth_provider'] as String?;  // ADD THIS
      _state = AuthState.authenticated;
    }

    // ... rest of existing code ...
  }

  Future<void> logout() async {
    // ... existing code ...
    _oauthProvider = null;  // ADD THIS
    // ... rest of existing code ...
  }
}
```

**Step 2: Display in SettingsScreen**

```dart
// settings_screen.dart - Modify _buildProfileTile

Widget _buildProfileTile(BuildContext context, AuthProvider authProvider) {
  final email = authProvider.email ?? 'Unknown';
  final displayName = authProvider.displayName;
  final initials = _getInitials(displayName ?? email);
  final provider = authProvider.oauthProvider;

  return ListTile(
    leading: CircleAvatar(
      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      child: Text(
        initials,
        style: TextStyle(
          color: Theme.of(context).colorScheme.onPrimaryContainer,
          fontWeight: FontWeight.bold,
        ),
      ),
    ),
    title: Row(
      children: [
        Text(displayName ?? email),
        const SizedBox(width: 8),
        // Provider icon
        if (provider != null) _buildProviderIcon(provider),
      ],
    ),
    subtitle: displayName != null ? Text(email) : null,
  );
}

Widget _buildProviderIcon(String provider) {
  // Use brand icons from Material or custom assets
  switch (provider) {
    case 'google':
      return Tooltip(
        message: 'Signed in with Google',
        child: Icon(
          Icons.g_mobiledata,  // Or use custom Google icon
          size: 20,
          color: Colors.red[700],
        ),
      );
    case 'microsoft':
      return Tooltip(
        message: 'Signed in with Microsoft',
        child: Icon(
          Icons.window,  // Or use custom Microsoft icon
          size: 18,
          color: Colors.blue[700],
        ),
      );
    default:
      return const SizedBox.shrink();
  }
}
```

### Alternative: Use Brand Icons Package

For proper brand icons, consider `font_awesome_flutter` or `simple_icons`:

```yaml
# pubspec.yaml
dependencies:
  font_awesome_flutter: ^10.7.0
```

```dart
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

Widget _buildProviderIcon(String provider) {
  switch (provider) {
    case 'google':
      return FaIcon(FontAwesomeIcons.google, size: 16);
    case 'microsoft':
      return FaIcon(FontAwesomeIcons.microsoft, size: 16);
    default:
      return const SizedBox.shrink();
  }
}
```

Recommend: Start with Material icons (no new dependency), add brand icons in polish phase.

---

## Suggested Build Order

Based on dependencies and complexity:

### Phase Order Rationale

```
1. Auth Provider Icon        [No dependencies, UI-only on existing data]
   +-- Depends on: Nothing new
   +-- Blocked by: Nothing
   +-- Effort: ~30 minutes

2. Copy Button               [No dependencies, UI-only]
   +-- Depends on: Nothing new
   +-- Blocked by: Nothing
   +-- Effort: ~1 hour

3. Retry Mechanism           [ConversationProvider only, no backend]
   +-- Depends on: Nothing new
   +-- Blocked by: Nothing
   +-- Effort: ~2 hours

4. Rename Thread             [Full stack: Backend + Service + Provider + UI]
   +-- Depends on: Backend PATCH endpoint
   +-- Blocked by: Backend deployment
   +-- Effort: ~3 hours (backend: 1hr, frontend: 2hr)
```

### Implementation Timeline

| Order | Feature | Layer Changes | Estimated Effort |
|-------|---------|---------------|------------------|
| 1 | Auth Provider Icon | AuthProvider (read existing), SettingsScreen | 30 min |
| 2 | Copy AI Response | MessageBubble only | 1 hour |
| 3 | Retry Failed Message | ConversationProvider, ConversationScreen | 2 hours |
| 4 | Rename Thread | Backend, ThreadService, ThreadProvider, ThreadListScreen | 3 hours |

**Total estimated effort:** 6.5 hours

---

## Patterns to Follow

### Existing Patterns (Continue Using)

1. **Optimistic UI Updates**
   - Already used in delete flows (Project, Thread, Message)
   - Apply to rename thread (update UI before backend confirms)

2. **Error Handling with Rollback**
   - Already implemented in `_commitPendingDelete()` methods
   - Apply to rename thread failure case

3. **SnackBar for Feedback**
   - Already used throughout app
   - Apply to copy confirmation, rename success/failure

4. **Provider + Service Separation**
   - Providers handle state and UI coordination
   - Services handle API calls
   - Keep this separation for all new features

5. **Consumer/context.read Pattern**
   - Use `Consumer<Provider>` for reactive UI
   - Use `context.read<Provider>()` for one-time actions (button callbacks)

### Anti-Patterns to Avoid

1. **Direct service calls from UI**
   - Always go through providers
   - Exception: Copy button (stateless, no provider needed)

2. **Storing UI state in providers**
   - Providers hold business state
   - Dialog open/close state stays in widget

3. **Blocking UI during API calls**
   - Use optimistic updates where possible
   - Show loading indicators, not frozen UI

---

## Testing Considerations

### Unit Tests (Provider Layer)

```dart
// Example test structure for retry mechanism
test('retryLastMessage reuses failed message content', () async {
  final provider = ConversationProvider(aiService: mockAiService);

  // Simulate failed message
  when(mockAiService.streamChat(any, any))
      .thenAnswer((_) => Stream.fromIterable([
        ErrorEvent(message: 'Connection failed'),
      ]));

  await provider.sendMessage('Hello');

  expect(provider.canRetry, isTrue);
  expect(provider.error, isNotNull);

  // Retry
  when(mockAiService.streamChat(any, any))
      .thenAnswer((_) => Stream.fromIterable([
        MessageCompleteEvent(content: 'Response', inputTokens: 10, outputTokens: 20),
      ]));

  await provider.retryLastMessage();

  expect(provider.canRetry, isFalse);
  expect(provider.error, isNull);
});
```

### Integration Tests (API Layer)

```dart
// Test rename thread endpoint
test('PATCH /threads/{id} updates title', () async {
  final response = await dio.patch(
    '/api/threads/$testThreadId',
    data: {'title': 'New Title'},
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );

  expect(response.statusCode, 200);
  expect(response.data['title'], 'New Title');
});
```

### Manual Testing Checklist

- [ ] Retry button appears only when error + failed message exists
- [ ] Retry clears error and removes duplicate user message
- [ ] Copy button shows only on assistant messages
- [ ] Copy shows "Copied" SnackBar confirmation
- [ ] Rename updates thread title in list
- [ ] Rename updates conversation screen AppBar title
- [ ] Provider icon displays correctly for Google users
- [ ] Provider icon displays correctly for Microsoft users

---

## Sources

- **Existing codebase analysis:** `frontend/lib/providers/`, `frontend/lib/services/`, `backend/app/routes/`
- **Flutter Clipboard API:** https://api.flutter.dev/flutter/services/Clipboard-class.html
- **Provider pattern:** Established patterns in existing codebase
- **Material Design 3:** Icon selection guidance

---

## Open Questions

1. **Retry mechanism:** Should retry auto-clear the error banner, or require explicit dismiss?
   - **Recommendation:** Auto-clear on retry to reduce user friction

2. **Copy button visibility:** Always visible, or hover-reveal (desktop) / long-press menu (mobile)?
   - **Recommendation:** Always visible for v1.6, polish to hover-reveal later

3. **Rename from conversation screen:** Should ConversationScreen also have rename capability?
   - **Recommendation:** Yes, add edit icon to AppBar for consistency

4. **Provider icons:** Use Material icons (no dependency) or brand icons (font_awesome_flutter)?
   - **Recommendation:** Material icons for v1.6, brand icons optional enhancement
