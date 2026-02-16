/// Message bubble widget for displaying conversation messages.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../../models/message.dart';
import 'source_chips.dart';

/// Message bubble displaying user or assistant message
class MessageBubble extends StatelessWidget {
  /// The message to display
  final Message message;

  /// Project ID for document navigation (optional)
  final String? projectId;

  const MessageBubble({
    super.key,
    required this.message,
    this.projectId,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final theme = Theme.of(context);

    final textWidget = Text(
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
                  // Source chips for assistant messages (SRC-01, SRC-02)
                  if (message.documentsUsed.isNotEmpty)
                    SourceChips(
                      sources: message.documentsUsed,
                      onSourceTap: (documentId, filename) =>
                          _openDocument(context, documentId, filename),
                    ),
                  _buildCopyButton(context, theme),
                ],
              ),
      ),
    );
  }

  /// Opens document in Document Viewer (SRC-03)
  void _openDocument(BuildContext context, String documentId, String filename) {
    if (projectId != null) {
      // Navigate to document viewer within project context
      context.push('/projects/$projectId/documents/$documentId');
    } else {
      // Show document in bottom sheet preview for project-less threads
      _showDocumentPreview(context, documentId, filename);
    }
  }

  /// Show document in bottom sheet for project-less threads
  void _showDocumentPreview(
      BuildContext context, String documentId, String filename) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (sheetContext) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (_, scrollController) => Column(
          children: [
            // Handle bar
            Container(
              margin: const EdgeInsets.only(top: 8),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            // Header
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const Icon(Icons.description_outlined),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      filename,
                      style: Theme.of(context).textTheme.titleMedium,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(sheetContext),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            // Content placeholder - would need document fetch
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.description_outlined,
                      size: 48,
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Document: $filename',
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'ID: $documentId',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ),
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
