# Phase 23: Chat Input UX - Research

**Researched:** 2026-02-01
**Domain:** Flutter TextField keyboard handling and multiline expansion
**Confidence:** HIGH

## Summary

This phase implements standard chat input behavior where Enter sends messages and Shift+Enter inserts newlines, plus expanding the input area to 8-10 visible lines. This is a well-established pattern used by Slack, Discord, Teams, and other chat applications.

The Flutter implementation requires careful attention to keyboard event handling. The current `chat_input.dart` uses `onSubmitted` which works differently from proper Enter key interception. The recommended approach uses `FocusNode.onKeyEvent` with `TextInputAction.none` to properly distinguish Enter from Shift+Enter.

**Primary recommendation:** Use `FocusNode.onKeyEvent` callback with `HardwareKeyboard.instance.isShiftPressed` check, set `textInputAction: TextInputAction.none`, and configure `maxLines: 10` with `minLines: 1` for expandable input.

## Standard Stack

The implementation uses only Flutter's built-in widgets and services - no additional packages needed.

### Core
| Component | Source | Purpose | Why Standard |
|-----------|--------|---------|--------------|
| `FocusNode` | Flutter widgets | Keyboard event handling | Built-in, proper event interception |
| `HardwareKeyboard` | Flutter services | Modifier key detection | Official API for detecting Shift state |
| `LogicalKeyboardKey` | Flutter services | Key identification | Standard key comparison |
| `TextField` | Flutter material | Text input | Already in use, just needs reconfiguration |

### Supporting
| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `KeyEventResult` | Event handling result | Return `.handled` to consume Enter, `.ignored` for Shift+Enter |
| `TextEditingController` | Text manipulation | Already in use, no changes needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `FocusNode.onKeyEvent` | `Shortcuts` + `Actions` widgets | More boilerplate, better for complex shortcuts |
| `FocusNode.onKeyEvent` | `KeyboardListener` widget | Adds wrapper widget, same functionality |

**Installation:**
No new dependencies required. All components are part of Flutter's core libraries.

## Architecture Patterns

### Current Implementation
```
ChatInput (StatefulWidget)
├── TextEditingController
├── FocusNode
├── TextField (maxLines: 5, minLines: 1)
│   └── onSubmitted: calls _handleSend()
└── IconButton (send button)
```

### Recommended Implementation
```
ChatInput (StatefulWidget)
├── TextEditingController
├── FocusNode (with onKeyEvent)
├── TextField (maxLines: 10, minLines: 1)
│   └── textInputAction: TextInputAction.none
│   └── keyboardType: TextInputType.multiline
└── IconButton (send button)
```

### Pattern 1: FocusNode with onKeyEvent
**What:** Attach keyboard event handler directly to FocusNode
**When to use:** When you need to intercept keys before TextField processes them
**Example:**
```dart
// Source: Flutter docs + GitHub issue #116707
class _ChatInputState extends State<ChatInput> {
  final TextEditingController _controller = TextEditingController();
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode(onKeyEvent: _handleKeyEvent);
  }

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    // Only handle KeyDownEvent to avoid double-firing
    if (event is! KeyDownEvent) {
      return KeyEventResult.ignored;
    }

    // Check for Enter key
    if (event.logicalKey == LogicalKeyboardKey.enter) {
      // Shift+Enter: allow newline (ignore, let TextField handle it)
      if (HardwareKeyboard.instance.isShiftPressed) {
        return KeyEventResult.ignored;
      }

      // Plain Enter: send message
      _handleSend();
      return KeyEventResult.handled;
    }

    return KeyEventResult.ignored;
  }

  // ... rest of implementation
}
```

### Pattern 2: TextField Configuration for Expandable Input
**What:** Configure TextField to expand from 1 to N lines
**When to use:** Chat-style input that grows with content
**Example:**
```dart
// Source: Flutter API docs - TextField maxLines/minLines
TextField(
  controller: _controller,
  focusNode: _focusNode,
  enabled: widget.enabled,
  minLines: 1,        // Start at 1 line
  maxLines: 10,       // Expand up to 10 lines, then scroll
  keyboardType: TextInputType.multiline,
  textInputAction: TextInputAction.none,  // Critical: prevents Enter interception
  textCapitalization: TextCapitalization.sentences,
  decoration: InputDecoration(
    hintText: widget.enabled ? 'Type a message...' : 'Waiting for response...',
    // ... rest of decoration
  ),
)
```

### Anti-Patterns to Avoid
- **Using `onSubmitted` for Enter handling:** This callback fires on submit action, but doesn't let you distinguish Shift+Enter from Enter
- **Using `TextInputAction.done` or `.send`:** These intercept Enter at the system level before your handler sees it
- **Using deprecated `RawKeyboardListener`:** Migrate to `KeyboardListener` or `FocusNode.onKeyEvent`
- **Using `onKey` instead of `onKeyEvent`:** `onKey` is the old API, `onKeyEvent` is the new standard

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modifier key detection | Manual key tracking state | `HardwareKeyboard.instance.isShiftPressed` | Already tracks modifier state across events |
| Key event handling | RawKeyboardListener wrapping | `FocusNode.onKeyEvent` | Cleaner, official API, no extra widget |
| Multiline expansion | Custom height calculation | `minLines` + `maxLines` props | Built-in, handles edge cases |
| Keyboard action button | Custom keyboard config | `textInputAction: TextInputAction.none` | Prevents system-level Enter interception |

**Key insight:** Flutter's FocusNode already supports onKeyEvent - no need to wrap TextField in listener widgets.

## Common Pitfalls

### Pitfall 1: TextInputAction Blocking Enter Detection
**What goes wrong:** Enter key is intercepted before your handler runs
**Why it happens:** `TextInputAction.done` or `.send` causes system to handle Enter
**How to avoid:** Set `textInputAction: TextInputAction.none`
**Warning signs:** Shift+Enter and Enter behave the same way

### Pitfall 2: Double-Firing on KeyUp
**What goes wrong:** Send triggered twice, or newline inserted then message sent
**Why it happens:** KeyEvent fires for both KeyDown and KeyUp
**How to avoid:** Only handle `KeyDownEvent`, ignore `KeyUpEvent` and `KeyRepeatEvent`
**Warning signs:** Messages sent twice, unexpected behavior

### Pitfall 3: Using Deprecated API
**What goes wrong:** Code works but uses `RawKeyEvent` / `onKey`
**Why it happens:** Old tutorials and Stack Overflow answers
**How to avoid:** Use `KeyEvent` / `onKeyEvent` / `HardwareKeyboard`
**Warning signs:** Deprecation warnings in console

### Pitfall 4: Empty Message on Enter
**What goes wrong:** User presses Enter on empty input, error or bad behavior
**Why it happens:** Not checking for empty text before sending
**How to avoid:** Check `_controller.text.trim().isEmpty` before calling onSend
**Warning signs:** Empty messages sent, or errors when pressing Enter on empty input

### Pitfall 5: Focus Loss After Send
**What goes wrong:** Keyboard dismisses after sending, user has to tap again
**Why it happens:** Not re-requesting focus after clearing text
**How to avoid:** Call `_focusNode.requestFocus()` after clearing
**Warning signs:** Keyboard closes after every sent message

## Code Examples

Verified patterns from official sources:

### Complete ChatInput Implementation
```dart
// Source: Flutter docs + verified patterns from GitHub issues
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class ChatInput extends StatefulWidget {
  final void Function(String message) onSend;
  final bool enabled;

  const ChatInput({
    super.key,
    required this.onSend,
    this.enabled = true,
  });

  @override
  State<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<ChatInput> {
  final TextEditingController _controller = TextEditingController();
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode(onKeyEvent: _handleKeyEvent);
  }

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    // Only process key down events
    if (event is! KeyDownEvent) {
      return KeyEventResult.ignored;
    }

    // Check for Enter key
    if (event.logicalKey == LogicalKeyboardKey.enter) {
      // Shift+Enter: insert newline (let TextField handle it)
      if (HardwareKeyboard.instance.isShiftPressed) {
        return KeyEventResult.ignored;
      }

      // Plain Enter on non-empty text: send message
      if (_controller.text.trim().isNotEmpty && widget.enabled) {
        _handleSend();
        return KeyEventResult.handled;  // Consume the event
      }

      // Plain Enter on empty text: do nothing
      return KeyEventResult.handled;  // Still consume to prevent beep/action
    }

    return KeyEventResult.ignored;
  }

  void _handleSend() {
    final text = _controller.text.trim();
    if (text.isEmpty || !widget.enabled) return;

    widget.onSend(text);
    _controller.clear();
    _focusNode.requestFocus();
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          top: BorderSide(color: theme.colorScheme.outlineVariant),
        ),
      ),
      child: SafeArea(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                focusNode: _focusNode,
                enabled: widget.enabled,
                minLines: 1,
                maxLines: 10,  // Expand to ~8-10 lines then scroll
                keyboardType: TextInputType.multiline,
                textInputAction: TextInputAction.none,  // Critical!
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: widget.enabled
                      ? 'Type a message...'
                      : 'Waiting for response...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  filled: true,
                  fillColor: theme.colorScheme.surfaceContainerHighest,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 10,
                  ),
                ),
                // Remove onSubmitted - we handle Enter via FocusNode
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              onPressed: widget.enabled ? _handleSend : null,
              icon: const Icon(Icons.send),
              tooltip: 'Send message',
            ),
          ],
        ),
      ),
    );
  }
}
```

### Key Detection Helper
```dart
// Source: Flutter key-event-migration docs
KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
  // Type check first
  if (event is! KeyDownEvent) return KeyEventResult.ignored;

  // Modifier detection via HardwareKeyboard singleton
  final isShiftPressed = HardwareKeyboard.instance.isShiftPressed;
  final isCtrlPressed = HardwareKeyboard.instance.isControlPressed;

  // Key comparison via LogicalKeyboardKey
  if (event.logicalKey == LogicalKeyboardKey.enter) {
    // Handle Enter variants
  }

  return KeyEventResult.ignored;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `RawKeyboardListener` | `KeyboardListener` or `FocusNode.onKeyEvent` | Flutter 3.0+ | Simpler API, no wrapper widget needed |
| `RawKeyEvent` | `KeyEvent` | Flutter 3.0+ | Type-safe event handling |
| `event.isShiftPressed` | `HardwareKeyboard.instance.isShiftPressed` | Flutter 3.0+ | More reliable modifier detection |
| `onKey: (FocusNode, RawKeyEvent)` | `onKeyEvent: (FocusNode, KeyEvent)` | Flutter 3.0+ | New callback signature |

**Deprecated/outdated:**
- `RawKeyboardListener`: Deprecated, use `KeyboardListener` or `FocusNode.onKeyEvent`
- `RawKeyEvent`: Deprecated, use `KeyEvent`
- `onKey` callback: Deprecated, use `onKeyEvent` callback

## Open Questions

None. The implementation path is clear and well-documented.

## Sources

### Primary (HIGH confidence)
- [Flutter TextField API Documentation](https://api.flutter.dev/flutter/material/TextField-class.html) - keyboard handling, maxLines/minLines, textInputAction
- [Flutter Key Event Migration Guide](https://docs.flutter.dev/release/breaking-changes/key-event-migration) - FocusNode.onKeyEvent, HardwareKeyboard API
- [Flutter GitHub PR #167952](https://github.com/flutter/flutter/pull/167952) - Shift+Enter example using Shortcuts/Actions
- [Flutter GitHub Issue #116707](https://github.com/flutter/flutter/issues/116707) - Solution for Shift+Enter in multiline TextField

### Secondary (MEDIUM confidence)
- Community patterns verified with official Flutter documentation

### Tertiary (LOW confidence)
- None - all findings verified with primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using only Flutter built-in components
- Architecture: HIGH - Pattern verified in official Flutter issues and docs
- Pitfalls: HIGH - Documented in GitHub issues with solutions

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (stable Flutter APIs, unlikely to change soon)
