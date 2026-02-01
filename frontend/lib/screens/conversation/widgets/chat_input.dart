/// Chat input widget for sending messages.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Text input bar for sending chat messages
class ChatInput extends StatefulWidget {
  /// Callback when message is sent
  final void Function(String message) onSend;

  /// Whether input is enabled
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

  /// Handle keyboard events for Enter to send, Shift+Enter for newline.
  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    // Only process key down events (avoid double-firing)
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
        return KeyEventResult.handled;
      }

      // Plain Enter on empty text: consume event (do nothing)
      return KeyEventResult.handled;
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
                maxLines: 10,
                minLines: 1,
                keyboardType: TextInputType.multiline,
                textInputAction: TextInputAction.none,
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
