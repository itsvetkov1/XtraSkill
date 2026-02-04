/// Document preview dialog for confirming file upload.
library;

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';

/// Dialog that shows a preview of a file before upload.
///
/// Displays filename, file size, and first 20 lines of content.
/// Returns true if user confirms upload, false if cancelled.
class DocumentPreviewDialog extends StatelessWidget {
  /// The file to preview
  final PlatformFile file;

  const DocumentPreviewDialog({super.key, required this.file});

  /// Show the preview dialog and return whether to proceed with upload.
  ///
  /// Returns true if user clicks Upload, false if user clicks Cancel.
  static Future<bool> show(BuildContext context, PlatformFile file) async {
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => DocumentPreviewDialog(file: file),
    );
    return result ?? false;
  }

  /// Formats file size in human-readable format (B/KB/MB)
  String _formatFileSize(int bytes) {
    if (bytes < 1024) {
      return '$bytes B';
    } else if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    } else {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
  }

  /// Extracts preview content from file bytes.
  ///
  /// Returns first [maxLines] lines with truncation indicator if more exist.
  String _getPreviewContent(List<int> bytes, {int maxLines = 20}) {
    if (bytes.isEmpty) return '(Empty file)';

    final content = utf8.decode(bytes, allowMalformed: true);
    final lines = content.split('\n');
    final previewLines = lines.take(maxLines);

    if (lines.length > maxLines) {
      return '${previewLines.join('\n')}\n\n... (${lines.length - maxLines} more lines)';
    }
    return previewLines.join('\n');
  }

  @override
  Widget build(BuildContext context) {
    final bytes = file.bytes ?? <int>[];
    final previewContent = _getPreviewContent(bytes);
    final fileSize = _formatFileSize(bytes.length);

    // Truncate filename if too long (keep extension visible)
    String displayName = file.name;
    if (displayName.length > 40) {
      final extension = displayName.contains('.')
          ? '.${displayName.split('.').last}'
          : '';
      final nameWithoutExt = displayName.substring(
        0,
        displayName.length - extension.length,
      );
      displayName =
          '${nameWithoutExt.substring(0, 40 - extension.length - 3)}...$extension';
    }

    return AlertDialog(
      title: Text('Preview: $displayName'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // File metadata
          Text(
            'Size: $fileSize',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 12),
          const Divider(),
          const SizedBox(height: 12),

          // Preview content with constrained height and scroll
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 300),
            child: SingleChildScrollView(
              child: SelectableText(
                previewContent,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('Upload'),
        ),
      ],
    );
  }
}
