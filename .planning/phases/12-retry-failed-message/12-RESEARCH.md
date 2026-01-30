# Phase 12: Retry Failed Message - Research

**Researched:** 2026-01-30
**Domain:** Flutter error handling with retry, state management for failed operations
**Confidence:** HIGH

## Summary

This phase adds retry functionality when AI requests fail. The current implementation already has error handling with a MaterialBanner showing "Dismiss" action, but lacks the ability to retry. The solution requires tracking the last user message content when an error occurs, then resending it when the user taps "Retry".

The implementation is straightforward: extend `ConversationProvider` to store the last failed message content (`_lastFailedMessage`), modify the error banner to show both "Dismiss" and "Retry" actions, and implement a `retryLastMessage()` method that calls `sendMessage()` with the stored content. The existing patterns in the codebase (undo with pending state, error handling in providers) provide clear templates.

**Primary recommendation:** Add `_lastFailedMessage` field to `ConversationProvider`, populate it on error, clear it on success or dismiss, and add `retryLastMessage()` method that resends the stored content.

## Findings

### Current Error Handling Implementation

**Location:** `frontend/lib/screens/conversation/conversation_screen.dart` (lines 117-127)

The existing error banner implementation:
```dart
// Current implementation - only "Dismiss" action
if (provider.error != null)
  MaterialBanner(
    content: SelectableText(provider.error!),
    backgroundColor: Theme.of(context).colorScheme.errorContainer,
    actions: [
      TextButton(
        onPressed: provider.clearError,
        child: const Text('Dismiss'),
      ),
    ],
  ),
```

**What needs to change:**
- Add "Retry" action button
- Track last user message for retry capability
- Handle both network errors and API errors

**Confidence:** HIGH - Direct code inspection

### ConversationProvider State Management

**Location:** `frontend/lib/providers/conversation_provider.dart`

Current state fields relevant to retry:
```dart
String? _error;           // Error message when request fails
bool _isStreaming;        // Whether AI is currently streaming
String _streamingText;    // Accumulated text during streaming
```

**Error sources in sendMessage():**
1. **SSE ErrorEvent** (line 146-151): API/server errors streamed back
2. **Catch block** (line 154-159): Network errors, connection failures

Both error paths set `_error` and reset streaming state, but lose the original user message content.

**Confidence:** HIGH - Direct code inspection

### Failed Message Tracking Pattern

Based on the existing undo pattern from Phase 9 (`_pendingDelete`, `_pendingDeleteIndex`), the retry pattern should follow:

```dart
/// Content of the last message that failed to send
String? _lastFailedMessage;

/// Getter for UI to check if retry is available
String? get lastFailedMessage => _lastFailedMessage;

/// Whether retry is available
bool get canRetry => _lastFailedMessage != null && _error != null;
```

**When to populate:**
- Set `_lastFailedMessage = content` at the START of `sendMessage()`
- Clear on success (MessageCompleteEvent)
- Keep on error (ErrorEvent or catch block)
- Clear on explicit dismiss

**Confidence:** HIGH - Pattern matches established codebase conventions

### MaterialBanner Multiple Actions

**Source:** [Flutter MaterialBanner API](https://api.flutter.dev/flutter/material/MaterialBanner-class.html)

Key behavior for multiple actions:
- `actions` property takes `List<Widget>`
- Single action: placed beside content
- Multiple actions: positioned below content automatically
- Use `overflowAlignment` for horizontal alignment when stacked

**Recommended implementation:**
```dart
MaterialBanner(
  content: SelectableText(provider.error!),
  backgroundColor: Theme.of(context).colorScheme.errorContainer,
  actions: [
    TextButton(
      onPressed: provider.clearError,
      child: const Text('Dismiss'),
    ),
    if (provider.canRetry)
      TextButton(
        onPressed: provider.retryLastMessage,
        child: const Text('Retry'),
      ),
  ],
)
```

**Confidence:** HIGH - Official Flutter documentation

### Error Types to Handle

**RETRY-04 requires handling both network errors and API errors:**

| Error Type | Source | Example | Retryable? |
|------------|--------|---------|------------|
| Network error | catch block | Connection timeout, DNS failure | Yes |
| SSE ErrorEvent | AI service stream | API rate limit, server error | Yes |
| Authentication error | ErrorEvent | Token expired | No (needs re-login) |
| Not found error | ErrorEvent | Thread deleted | No |

**Recommendation:** Make all errors retryable. Authentication failures will fail again, prompting login redirect through existing auth flow. This simplifies logic and covers edge cases.

**Confidence:** HIGH - Error analysis from existing code

### Optimistic Message Handling

The current `sendMessage()` adds the user message optimistically:
```dart
final userMessage = Message(
  id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
  role: MessageRole.user,
  content: content,
  createdAt: DateTime.now(),
);
_messages.add(userMessage);
```

**Question:** Should the optimistic message be removed on error?

**Current behavior:** Message stays in the list even on error.

**Recommendation:** Keep current behavior. The user sees their message, sees the error, and can retry. If retry succeeds, the message is already there. This matches user expectations (their message was "sent" to the UI).

**Confidence:** MEDIUM - UX judgment call, but consistent with current behavior

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `provider` | 6.x | State management | ConversationProvider already handles state |
| `flutter/material.dart` | SDK built-in | MaterialBanner UI | Already in use for errors |

### Supporting
No additional libraries needed.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Provider state | Dedicated retry queue | Overkill for single message retry |
| MaterialBanner | SnackBar | MaterialBanner is already in use, better for persistent errors |
| Simple String storage | Command pattern | Over-engineering for this use case |

**Decision:** Extend existing provider with minimal new state. Zero new dependencies.

## Architecture Patterns

### Recommended Implementation

**ConversationProvider changes:**
```dart
class ConversationProvider extends ChangeNotifier {
  // ... existing fields ...

  /// Content of the last message that failed to send
  String? _lastFailedMessage;

  /// Whether retry is available
  bool get canRetry => _lastFailedMessage != null && _error != null;

  /// Send a message and stream the AI response
  Future<void> sendMessage(String content) async {
    if (_thread == null || _isStreaming) return;

    _error = null;
    _lastFailedMessage = content;  // Track for potential retry

    // Add user message optimistically
    final userMessage = Message(
      id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
      role: MessageRole.user,
      content: content,
      createdAt: DateTime.now(),
    );
    _messages.add(userMessage);

    _isStreaming = true;
    _streamingText = '';
    _statusMessage = null;
    notifyListeners();

    try {
      await for (final event in _aiService.streamChat(_thread!.id, content)) {
        if (event is TextDeltaEvent) {
          _streamingText += event.text;
          notifyListeners();
        } else if (event is ToolExecutingEvent) {
          _statusMessage = event.status;
          notifyListeners();
        } else if (event is MessageCompleteEvent) {
          // Success - clear failed message tracking
          _lastFailedMessage = null;

          final assistantMessage = Message(
            id: 'temp-assistant-${DateTime.now().millisecondsSinceEpoch}',
            role: MessageRole.assistant,
            content: _streamingText.isNotEmpty ? _streamingText : event.content,
            createdAt: DateTime.now(),
          );
          _messages.add(assistantMessage);

          _isStreaming = false;
          _streamingText = '';
          _statusMessage = null;
          notifyListeners();
        } else if (event is ErrorEvent) {
          // Keep _lastFailedMessage for retry
          _error = event.message;
          _isStreaming = false;
          _streamingText = '';
          _statusMessage = null;
          notifyListeners();
        }
      }
    } catch (e) {
      // Keep _lastFailedMessage for retry
      _error = e.toString();
      _isStreaming = false;
      _streamingText = '';
      _statusMessage = null;
      notifyListeners();
    }
  }

  /// Retry the last failed message
  void retryLastMessage() {
    if (_lastFailedMessage == null) return;

    final content = _lastFailedMessage!;
    _lastFailedMessage = null;
    _error = null;

    // Remove the optimistic user message that was added on first attempt
    // to avoid duplicates
    if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
      _messages.removeLast();
    }

    sendMessage(content);
  }

  /// Clear error message and failed message state
  void clearError() {
    _error = null;
    _lastFailedMessage = null;  // Also clear retry state on dismiss
    notifyListeners();
  }

  // ... rest of class ...
}
```

**ConversationScreen changes:**
```dart
// Error banner with Retry action
if (provider.error != null)
  MaterialBanner(
    content: SelectableText(provider.error!),
    backgroundColor: Theme.of(context).colorScheme.errorContainer,
    actions: [
      TextButton(
        onPressed: provider.clearError,
        child: const Text('Dismiss'),
      ),
      if (provider.canRetry)
        TextButton(
          onPressed: provider.retryLastMessage,
          child: const Text('Retry'),
        ),
    ],
  ),
```

### Anti-Patterns to Avoid

- **Storing full Message object for retry:** Only need the content string, simpler is better
- **Complex retry queue:** This is single-message retry, not a batch system
- **Automatic retry without user action:** User should control when to retry (network might still be down)
- **Hiding the error and auto-dismissing:** Error should persist until user acts
- **Leaving duplicate messages on retry:** Remove the first optimistic message before resending

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Error display | Custom toast/dialog | MaterialBanner (already in use) | Consistent with existing UX |
| State management | Dedicated retry service | Provider field | Follows established pattern |
| Retry logic | Exponential backoff system | Simple user-triggered resend | User controls timing |
| Message deduplication | Complex diff logic | Remove last user message before retry | Simple, predictable |

**Key insight:** This is fundamentally just storing a string and calling an existing method. The complexity is in getting the UX right, not the code.

## Common Pitfalls

### Pitfall 1: Duplicate User Messages on Retry
**What goes wrong:** User sees their message twice after retry
**Why it happens:** Original optimistic message stays, retry adds another
**How to avoid:** Remove the last user message before calling `sendMessage()` in `retryLastMessage()`
**Warning signs:** "Hello" appears twice in message list after retry

### Pitfall 2: Retry Available After Successful Response
**What goes wrong:** Retry button shows even when there's no error
**Why it happens:** `_lastFailedMessage` not cleared on success
**How to avoid:** Clear `_lastFailedMessage = null` in MessageCompleteEvent handler
**Warning signs:** Retry button visible when there's no error banner

### Pitfall 3: Losing Retry State on Dismiss
**What goes wrong:** User dismisses error, wants to retry, but can't
**Why it happens:** `clearError()` clears `_lastFailedMessage`
**How to avoid:** This is actually desired behavior - dismiss means "I don't want to retry"
**Warning signs:** None - this is correct UX

### Pitfall 4: Retry During Streaming
**What goes wrong:** Multiple simultaneous AI requests
**Why it happens:** User taps retry while previous request still running
**How to avoid:** `sendMessage()` already guards with `if (_isStreaming) return`
**Warning signs:** Race conditions, garbled responses

### Pitfall 5: Context Issues with Async
**What goes wrong:** "Looking up deactivated widget" error
**Why it happens:** User navigates away, async operation completes, tries to use stale context
**How to avoid:** UI reacts to provider state, not direct method calls. Provider methods don't need BuildContext.
**Warning signs:** Random crashes after navigation during error state

## Code Examples

### Complete RetryLastMessage Implementation
```dart
// Source: Pattern from existing ConversationProvider
/// Retry the last failed message
void retryLastMessage() {
  if (_lastFailedMessage == null) return;

  final content = _lastFailedMessage!;
  _lastFailedMessage = null;
  _error = null;

  // Remove duplicate: the optimistic message added on first attempt
  if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
    _messages.removeLast();
  }

  sendMessage(content);
}
```

### MaterialBanner with Conditional Retry
```dart
// Source: Flutter MaterialBanner API + existing codebase pattern
if (provider.error != null)
  MaterialBanner(
    content: SelectableText(provider.error!),
    backgroundColor: Theme.of(context).colorScheme.errorContainer,
    actions: [
      TextButton(
        onPressed: provider.clearError,
        child: const Text('Dismiss'),
      ),
      if (provider.canRetry)
        TextButton(
          onPressed: provider.retryLastMessage,
          child: const Text('Retry'),
        ),
    ],
  ),
```

### Test Pattern for Retry
```dart
// Source: Pattern from existing conversation_screen_test.dart
testWidgets('Retry button appears when message fails', (tester) async {
  when(mockConversationProvider.error).thenReturn('Connection failed');
  when(mockConversationProvider.canRetry).thenReturn(true);

  await tester.pumpWidget(/* ... */);
  await tester.pumpAndSettle();

  expect(find.text('Retry'), findsOneWidget);
  expect(find.text('Dismiss'), findsOneWidget);
});

testWidgets('Retry calls retryLastMessage on provider', (tester) async {
  when(mockConversationProvider.error).thenReturn('Connection failed');
  when(mockConversationProvider.canRetry).thenReturn(true);

  await tester.pumpWidget(/* ... */);
  await tester.pumpAndSettle();

  await tester.tap(find.text('Retry'));

  verify(mockConversationProvider.retryLastMessage()).called(1);
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Error-only display | Error + retry action | Modern UX standard | Better recovery experience |
| Auto-retry with backoff | User-triggered retry | Context-dependent | User controls timing, simpler |
| Store full request object | Store content string only | Simplicity preference | Less state to manage |

**Deprecated/outdated:**
- Automatic retry without user consent - modern UX prefers user control
- Complex retry queues for single operations - overkill for chat messages

## Open Questions

None. The implementation path is clear and follows established patterns.

## Sources

### Primary (HIGH confidence)
- [Flutter MaterialBanner API](https://api.flutter.dev/flutter/material/MaterialBanner-class.html) - Official documentation for MaterialBanner with multiple actions
- Codebase inspection: `conversation_provider.dart`, `conversation_screen.dart` - Existing error handling patterns
- Codebase inspection: Phase 9 `09-RESEARCH.md` - Pending state pattern for undo

### Secondary (MEDIUM confidence)
- [Flutter Mastery: Error Handling and Retry Strategies](https://fluttermasterylibrary.com/6/9/2/3/) - Community patterns for retry in Flutter
- [KindaCode: Working with MaterialBanner](https://www.kindacode.com/article/working-with-materialbanner-in-flutter/) - MaterialBanner usage examples

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new packages required
- Architecture: HIGH - Simple extension of existing provider pattern
- Pitfalls: HIGH - Identified from code analysis and established patterns
- UI changes: HIGH - MaterialBanner API is well-documented

**Research date:** 2026-01-30
**Valid until:** 90 days (stable Flutter SDK APIs, simple state management)

---
*Research completed: 2026-01-30*
