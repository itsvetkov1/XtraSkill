# BUG-015: Shift+Enter Not Creating New Line

**Priority:** High
**Status:** Done
**Component:** Frontend - ChatInput
**Discovered:** 2026-02-02 (Phase 26 regression testing)
**Fixed:** 2026-02-02

---

## Problem

In the chat input, pressing Shift+Enter did not create a new line. Users expected:
- Enter = send message
- Shift+Enter = insert newline

Instead, Shift+Enter had no visible effect.

---

## Root Cause

The original implementation returned `KeyEventResult.ignored` for Shift+Enter, expecting the TextField to handle the newline insertion:

```dart
if (HardwareKeyboard.instance.isShiftPressed) {
  return KeyEventResult.ignored;  // Let TextField handle it
}
```

On Flutter web, this doesn't work reliably. The TextField doesn't automatically insert a newline when the key event is ignored. The web platform handles key events differently than native platforms.

---

## Acceptance Criteria

- [x] Shift+Enter inserts newline at cursor position
- [x] Enter sends message (existing behavior preserved)
- [x] Multi-line messages display correctly
- [x] Cursor moves to after the newline

---

## Fix

Manually insert the newline character instead of relying on TextField:

```dart
if (HardwareKeyboard.instance.isShiftPressed) {
  _insertNewline();
  return KeyEventResult.handled;
}

void _insertNewline() {
  final text = _controller.text;
  final selection = _controller.selection;

  // Insert newline at cursor position
  final newText = text.replaceRange(selection.start, selection.end, '\n');
  _controller.text = newText;

  // Move cursor after the newline
  _controller.selection = TextSelection.collapsed(
    offset: selection.start + 1,
  );
}
```

**Tests:** `frontend/test/widget/chat_input_test.dart`

---

## Technical References

- `frontend/lib/screens/conversation/widgets/chat_input.dart` (FIXED)
- Flutter web key event handling differences

---

*Created: 2026-02-02*
*Fixed: 2026-02-02*
