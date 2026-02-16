/// Widget displaying partial AI response after stream interruption.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Displays partial AI response with copy capability after stream error
class ErrorStateMessage extends StatelessWidget {
  /// Partial text accumulated before error
  final String partialText;

  /// Callback when content is copied
  final VoidCallback? onCopy;

  const ErrorStateMessage({
    super.key,
    required this.partialText,
    this.onCopy,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: theme.colorScheme.surfaceContainerHighest,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(16),
            topRight: Radius.circular(16),
            bottomLeft: Radius.circular(4),
            bottomRight: Radius.circular(16),
          ),
          border: Border.all(
            color: theme.colorScheme.error.withValues(alpha: 0.3),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Incomplete response indicator
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.warning_amber_rounded,
                  size: 16,
                  color: theme.colorScheme.error,
                ),
                const SizedBox(width: 8),
                Text(
                  'Response incomplete',
                  style: TextStyle(
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                    color: theme.colorScheme.error,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Partial text content
            Text(
              partialText,
              style: TextStyle(
                fontSize: 15,
                height: 1.4,
                color: theme.colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 8),
            // Copy button
            Align(
              alignment: Alignment.centerRight,
              child: IconButton(
                icon: Icon(
                  Icons.copy,
                  size: 18,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                tooltip: 'Copy partial response',
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                onPressed: () => _copyToClipboard(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Copies partial content to clipboard
  /// CRITICAL: No async/await - Safari requires synchronous clipboard call
  void _copyToClipboard(BuildContext context) {
    try {
      Clipboard.setData(ClipboardData(text: partialText));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Partial response copied')),
      );
      onCopy?.call();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to copy')),
      );
    }
  }
}
