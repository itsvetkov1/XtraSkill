/// Chip widget showing attached file with remove button.
library;

import 'package:flutter/material.dart';

/// Small chip showing an attached file with file type icon and remove button
class DocumentAttachmentChip extends StatelessWidget {
  /// File name to display
  final String filename;

  /// File size in bytes
  final int fileSize;

  /// Callback when remove button tapped
  final VoidCallback onRemove;

  const DocumentAttachmentChip({
    super.key,
    required this.filename,
    required this.fileSize,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Chip(
      avatar: Icon(
        _getFileIcon(),
        size: 18,
      ),
      label: Text(
        _truncateFilename(filename),
        style: const TextStyle(fontSize: 13),
      ),
      deleteIcon: const Icon(Icons.close, size: 18),
      onDeleted: onRemove,
      visualDensity: VisualDensity.compact,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }

  /// Get file type icon based on file extension
  IconData _getFileIcon() {
    final extension = filename.split('.').last.toLowerCase();

    // Code files
    if (['dart', 'py', 'js', 'ts', 'java', 'cpp', 'c', 'h', 'swift', 'kt', 'go', 'rs'].contains(extension)) {
      return Icons.code;
    }

    // Documents
    if (['pdf', 'doc', 'docx', 'txt', 'md', 'rtf'].contains(extension)) {
      return Icons.description;
    }

    // Images
    if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'].contains(extension)) {
      return Icons.image;
    }

    // Spreadsheets
    if (['xls', 'xlsx', 'csv'].contains(extension)) {
      return Icons.table_chart;
    }

    // Presentations
    if (['ppt', 'pptx', 'key'].contains(extension)) {
      return Icons.slideshow;
    }

    // Archives
    if (['zip', 'tar', 'gz', 'rar', '7z'].contains(extension)) {
      return Icons.folder_zip;
    }

    // Default
    return Icons.insert_drive_file;
  }

  /// Truncate filename to ~20 chars with ellipsis
  String _truncateFilename(String name) {
    if (name.length <= 20) return name;

    // Try to preserve extension
    final parts = name.split('.');
    if (parts.length > 1) {
      final extension = parts.last;
      final nameWithoutExt = name.substring(0, name.length - extension.length - 1);
      final truncated = nameWithoutExt.substring(0, 15 - extension.length);
      return '$truncated...$extension';
    }

    return '${name.substring(0, 17)}...';
  }
}
