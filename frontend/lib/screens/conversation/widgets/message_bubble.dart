/// Message bubble widget for displaying conversation messages.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../models/message.dart';

/// Message bubble displaying user or assistant message
class MessageBubble extends StatelessWidget {
  /// The message to display
  final Message message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final theme = Theme.of(context);

    final textWidget = SelectableText(
      message.content,
      style: TextStyle(
        fontSize: 15, // Explicit font size for readability
        height: 1.4, // Line height for better readability
        color: isUser
            ? theme.colorScheme.onPrimary
            : theme.colorScheme.onSurface,
      ),
    );

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isUser
              ? theme.colorScheme.primary
              : theme.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 16),
          ),
        ),
        child: isUser
            ? textWidget
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  textWidget,
                  _buildCopyButton(context, theme),
                ],
              ),
      ),
    );
  }

  /// Builds the copy button for assistant messages
  Widget _buildCopyButton(BuildContext context, ThemeData theme) {
    return Align(
      alignment: Alignment.centerRight,
      child: IconButton(
        icon: Icon(
          Icons.copy,
          size: 18,
          color: theme.colorScheme.onSurfaceVariant,
        ),
        tooltip: 'Copy to clipboard',
        padding: EdgeInsets.zero,
        constraints: const BoxConstraints(),
        onPressed: () => _copyToClipboard(context),
      ),
    );
  }

  /// Copies message content to clipboard
  /// CRITICAL: No async/await - Safari requires synchronous clipboard call
  void _copyToClipboard(BuildContext context) {
    try {
      Clipboard.setData(ClipboardData(text: message.content));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Copied to clipboard')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to copy')),
      );
    }
  }
}
