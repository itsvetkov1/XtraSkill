/// Message bubble widget for Assistant chat messages.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../models/message.dart';
import 'markdown_message.dart';

/// Message bubble for Assistant chat with markdown rendering and copy/retry controls
class AssistantMessageBubble extends StatelessWidget {
  /// The message to display
  final Message message;

  /// Callback for retry action (shown on error for last message)
  final VoidCallback? onRetry;

  const AssistantMessageBubble({
    super.key,
    required this.message,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final theme = Theme.of(context);

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
        child: isUser ? _buildUserMessage(context, theme) : _buildAssistantMessage(context, theme),
      ),
    );
  }

  /// Build user message content with optional attachment chips
  Widget _buildUserMessage(BuildContext context, ThemeData theme) {
    // Parse attachments from message content if present
    final attachments = _parseAttachments(message.content);

    // Display message text without the attachment note
    final displayText = message.content;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Message text
        Text(
          displayText,
          style: TextStyle(
            fontSize: 15,
            height: 1.4,
            color: theme.colorScheme.onPrimary,
          ),
        ),
        // Attachment chips (if any)
        if (attachments.isNotEmpty) ...[
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: attachments.map((filename) => _buildAttachmentChip(context, theme, filename)).toList(),
          ),
        ],
      ],
    );
  }

  /// Parse attachment filenames from message content
  List<String> _parseAttachments(String content) {
    // Look for "[Attached files: file1.pdf, file2.xlsx]" pattern
    final regex = RegExp(r'\[Attached files: ([^\]]+)\]');
    final match = regex.firstMatch(content);
    if (match != null) {
      final fileList = match.group(1) ?? '';
      return fileList.split(',').map((f) => f.trim()).where((f) => f.isNotEmpty).toList();
    }
    return [];
  }

  /// Build a small attachment chip
  Widget _buildAttachmentChip(BuildContext context, ThemeData theme, String filename) {
    // Choose icon based on file extension
    final icon = _getFileIcon(filename);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: theme.colorScheme.onPrimary.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 14,
            color: theme.colorScheme.onPrimary,
          ),
          const SizedBox(width: 4),
          Text(
            filename,
            style: TextStyle(
              fontSize: 12,
              color: theme.colorScheme.onPrimary,
            ),
          ),
        ],
      ),
    );
  }

  /// Get appropriate icon for file type
  IconData _getFileIcon(String filename) {
    final ext = filename.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':
        return Icons.picture_as_pdf;
      case 'doc':
      case 'docx':
        return Icons.description;
      case 'xls':
      case 'xlsx':
        return Icons.table_chart;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return Icons.image;
      case 'txt':
        return Icons.text_snippet;
      default:
        return Icons.insert_drive_file;
    }
  }

  /// Build assistant message content with markdown and controls
  Widget _buildAssistantMessage(BuildContext context, ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Render content with markdown
        MarkdownMessage(content: message.content),
        const SizedBox(height: 8),
        // Controls row: copy button + retry button (if applicable)
        Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            // Retry button (only if onRetry callback provided)
            if (onRetry != null) ...[
              TextButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Retry'),
                style: TextButton.styleFrom(
                  foregroundColor: theme.colorScheme.error,
                ),
              ),
              const SizedBox(width: 8),
            ],
            // Copy button
            IconButton(
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
          ],
        ),
      ],
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
