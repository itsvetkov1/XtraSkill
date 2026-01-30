# Phase 11: Copy AI Response - Research

**Researched:** 2026-01-30
**Domain:** Flutter Clipboard API, Cross-Platform Text Copy
**Confidence:** HIGH

## Summary

This phase adds a one-tap copy button to assistant message bubbles. Flutter's built-in `Clipboard.setData()` from `dart:services` handles the actual copy operation with zero new dependencies. The existing codebase already uses `ScaffoldMessenger.showSnackBar()` extensively, so the feedback pattern is established.

The main technical risk is Safari/WebKit browser restrictions that require clipboard operations to execute synchronously within the user gesture handler - no `await` before `setData()`. The implementation is straightforward: modify `MessageBubble` to add an `IconButton` that calls `Clipboard.setData()` directly in the `onPressed` callback (no async/await), then show the snackbar.

**Primary recommendation:** Add copy icon to `MessageBubble` for assistant messages only, call clipboard synchronously, then show snackbar feedback.

## Findings

### Message Bubble Implementation

**Location:** `frontend/lib/screens/conversation/widgets/message_bubble.dart`

The current implementation is a simple `StatelessWidget` wrapping a `Container` with `SelectableText`:

```dart
// Lines 9-52 of message_bubble.dart
class MessageBubble extends StatelessWidget {
  final Message message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final theme = Theme.of(context);

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        // ... constraints, decoration
        child: SelectableText(
          message.content,  // <-- This is what we copy
          // ... styling
        ),
      ),
    );
  }
}
```

**Key observations:**
- `message.content` is already accessible as a `String` - direct access to copy content
- `isUser` boolean already exists - use to conditionally show copy icon for assistant messages only
- Currently returns a simple widget tree - will need to add icon button to layout

**Modification approach:**
1. Wrap content in a `Column` or `Stack` to add icon
2. Add `IconButton` with copy icon (`Icons.copy` or `Icons.content_copy`)
3. Position icon subtly (top-right corner, or below text)
4. Only show for `!isUser` messages

### Clipboard API

**Source:** [Flutter Clipboard class](https://api.flutter.dev/flutter/services/Clipboard-class.html)

**Import:** `import 'package:flutter/services.dart';`

**Core pattern:**
```dart
import 'package:flutter/services.dart';

// Synchronous call within user gesture handler
void _copyToClipboard(String text) {
  Clipboard.setData(ClipboardData(text: text));
  // Show feedback AFTER (can be async)
}
```

**Key methods:**
| Method | Signature | Purpose |
|--------|-----------|---------|
| `setData` | `static Future<void> setData(ClipboardData data)` | Write to clipboard |
| `getData` | `static Future<ClipboardData?> getData(String format)` | Read from clipboard |
| `kTextPlain` | Constant | Format identifier for plain text |

**ClipboardData:** Only supports plain text currently via the `text` property.

**Confidence:** HIGH - Official Flutter SDK, verified via api.flutter.dev

### Feedback Patterns

The codebase has an established SnackBar pattern used in multiple places:

**Pattern from `document_upload_screen.dart` (lines 54-58):**
```dart
ScaffoldMessenger.of(context).showSnackBar(
  const SnackBar(
    content: Text('Document uploaded successfully'),
    backgroundColor: Colors.green,
  ),
);
```

**Pattern from `conversation_provider.dart` (lines 209-218):**
```dart
ScaffoldMessenger.of(context).clearSnackBars();
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(
    content: const Text('Message deleted'),
    duration: const Duration(seconds: 10),
    action: SnackBarAction(
      label: 'Undo',
      onPressed: () => _undoDelete(),
    ),
  ),
);
```

**For copy feature:**
- Simple success message: `"Copied to clipboard"`
- Short duration (default 4 seconds is fine)
- No action needed (no undo for copy)
- Use `Colors.green` or theme default

**Confidence:** HIGH - Direct observation of existing codebase patterns

### Cross-Platform Considerations

**CRITICAL: Safari/WebKit Async Restriction**

**Source:** [Flutter Issue #106046](https://github.com/flutter/flutter/issues/106046)

Safari browsers require clipboard access to happen synchronously within the user gesture handler. Using `await` before `Clipboard.setData()` will fail with:

```
PlatformException(copy_fail, Clipboard.setData failed, null, null)
```

**Workaround:** Call `setData()` without await in the button handler:

```dart
// CORRECT - works on Safari
onPressed: () {
  Clipboard.setData(ClipboardData(text: message.content));
  // Then show snackbar (can be async, clipboard already done)
  ScaffoldMessenger.of(context).showSnackBar(...);
}

// WRONG - fails on Safari
onPressed: () async {
  await Clipboard.setData(ClipboardData(text: message.content));
  ScaffoldMessenger.of(context).showSnackBar(...);
}
```

**Platform summary:**
| Platform | Behavior | Notes |
|----------|----------|-------|
| Android | Works | No special handling |
| iOS | Works | No special handling |
| Web (Chrome) | Works | No special handling |
| Web (Safari) | Requires sync call | No `await` before setData |
| Web (Firefox) | Works | No special handling |
| Windows | Works | Ensure non-null text |
| macOS | Works | No special handling |

**Error handling:** The `setData()` call can fail. Wrap in try-catch and show error snackbar:

```dart
onPressed: () {
  try {
    Clipboard.setData(ClipboardData(text: message.content));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Copied to clipboard')),
    );
  } catch (e) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Failed to copy: $e')),
    );
  }
}
```

**Confidence:** HIGH - Verified via Flutter GitHub issues and official documentation

### Message Data Access

The `MessageBubble` widget already receives the full `Message` object:

```dart
class MessageBubble extends StatelessWidget {
  final Message message;  // Full message object
```

**Message model (`models/message.dart`):**
```dart
class Message {
  final String id;
  final MessageRole role;
  final String content;  // <-- Full text content to copy
  final DateTime createdAt;
}
```

**Access pattern:** `message.content` - direct string access, no API calls needed.

**Confidence:** HIGH - Direct code inspection

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `flutter/services.dart` | SDK built-in | Clipboard API | Official Flutter SDK, no dependencies |
| `flutter/material.dart` | SDK built-in | SnackBar feedback | Already in use throughout app |

### Supporting
No additional libraries needed.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Built-in Clipboard | `clipboard` package | Adds dependency, no benefit for text-only |
| Built-in Clipboard | `super_clipboard` package | Richer media support, overkill for text |

**Decision:** Use built-in Flutter SDK. Zero new dependencies required.

## Architecture Patterns

### Recommended Implementation

Modify `MessageBubble` to conditionally show copy icon for assistant messages:

```dart
// message_bubble.dart
class MessageBubble extends StatelessWidget {
  final Message message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    // ... existing setup

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        // ... existing constraints, decoration
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            SelectableText(message.content, ...),
            if (!isUser) _buildCopyButton(context),
          ],
        ),
      ),
    );
  }

  Widget _buildCopyButton(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: IconButton(
        icon: Icon(Icons.copy, size: 18),
        tooltip: 'Copy to clipboard',
        onPressed: () => _copyToClipboard(context),
      ),
    );
  }

  void _copyToClipboard(BuildContext context) {
    try {
      Clipboard.setData(ClipboardData(text: message.content));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Copied to clipboard')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to copy')),
      );
    }
  }
}
```

### Anti-Patterns to Avoid

- **Async clipboard call:** Do NOT use `await Clipboard.setData()` - breaks Safari
- **Separate copy button widget:** Keep it in `MessageBubble` for simplicity, no need for extraction
- **Copy on user messages:** Users typed those, they already have the text - copy only assistant responses

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Clipboard access | Platform channels | `Clipboard.setData()` | Cross-platform handled by Flutter |
| User feedback | Custom toast | `ScaffoldMessenger.showSnackBar()` | Established pattern in codebase |
| Copy icon | Custom SVG | `Icons.copy` or `Icons.content_copy` | Material icon, consistent with app |

**Key insight:** This feature is trivially simple with Flutter's built-in tools. The main complexity is knowing about the Safari async restriction.

## Common Pitfalls

### Pitfall 1: Async Clipboard on Web
**What goes wrong:** `Clipboard.setData()` called with `await` fails silently on Safari/WebKit
**Why it happens:** Browser security requires clipboard access within synchronous user gesture
**How to avoid:** Never use `await` before `setData()`. Call it directly, show snackbar after.
**Warning signs:** Works in Chrome, fails in Safari

### Pitfall 2: Missing Error Handling
**What goes wrong:** Clipboard operation fails (permissions, secure context) with no user feedback
**Why it happens:** `setData()` can throw but is often called without try-catch
**How to avoid:** Wrap in try-catch, show error snackbar on failure
**Warning signs:** Silent failures, users think copy worked but it didn't

### Pitfall 3: Copy Button on User Messages
**What goes wrong:** Cluttered UI with unnecessary copy buttons
**Why it happens:** Developer adds copy to all messages without considering UX
**How to avoid:** Only show copy on assistant messages (`!isUser`)
**Warning signs:** Users rarely copy their own typed messages

## Code Examples

### Complete Copy Implementation
```dart
// Source: Flutter SDK + codebase patterns
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void _copyToClipboard(BuildContext context, String text) {
  try {
    // CRITICAL: No await - synchronous for Safari compatibility
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Copied to clipboard')),
    );
  } catch (e) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Failed to copy')),
    );
  }
}
```

### Copy Icon Button
```dart
// Source: Material Design + codebase patterns
IconButton(
  icon: Icon(
    Icons.copy,
    size: 18,
    color: theme.colorScheme.onSurfaceVariant,
  ),
  tooltip: 'Copy to clipboard',
  padding: EdgeInsets.zero,
  constraints: const BoxConstraints(),
  onPressed: () => _copyToClipboard(context, message.content),
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `clipboard` package | Built-in `Clipboard` class | Always available | No external dependency needed |

**Deprecated/outdated:**
- Third-party clipboard packages for simple text copy - use built-in `Clipboard` class instead

## Open Questions

None. Implementation path is clear.

## Sources

### Primary (HIGH confidence)
- [Flutter Clipboard class](https://api.flutter.dev/flutter/services/Clipboard-class.html) - Official API documentation
- [Clipboard.setData method](https://api.flutter.dev/flutter/services/Clipboard/setData.html) - Method signature and behavior
- Codebase inspection: `message_bubble.dart`, `conversation_screen.dart`, SnackBar patterns

### Secondary (MEDIUM confidence)
- [Flutter Issue #106046](https://github.com/flutter/flutter/issues/106046) - Safari async clipboard restriction, workarounds

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Flutter SDK built-in, no dependencies
- Architecture: HIGH - Simple widget modification
- Pitfalls: HIGH - Safari issue well-documented in Flutter issues

**Research date:** 2026-01-30
**Valid until:** 90 days (stable Flutter SDK APIs, unlikely to change)

---
*Research completed: 2026-01-30*
