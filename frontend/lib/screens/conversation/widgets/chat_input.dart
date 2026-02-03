/// Chat input widget for sending messages.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Text input bar for sending chat messages
class ChatInput extends StatefulWidget {
  /// Callback when message is sent
  final void Function(String message) onSend;

  /// Callback when generate artifact button tapped
  final VoidCallback? onGenerateArtifact;

  /// Whether input is enabled
  final bool enabled;

  const ChatInput({
    super.key,
    required this.onSend,
    this.onGenerateArtifact,
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
      // Shift+Enter: manually insert newline (web doesn't handle this automatically)
      if (HardwareKeyboard.instance.isShiftPressed) {
        _insertNewline();
        return KeyEventResult.handled;
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

  /// Insert a newline at the current cursor position.
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
            if (widget.onGenerateArtifact != null)
              IconButton(
                onPressed: widget.enabled ? widget.onGenerateArtifact : null,
                icon: const Icon(Icons.auto_awesome),
                tooltip: 'Generate Artifact',
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
