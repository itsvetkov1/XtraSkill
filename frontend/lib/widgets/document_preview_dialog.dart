/// Document preview dialog for confirming file upload.
library;

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
/// Dialog that shows a preview of a file before upload.
///
/// Displays filename, file size, and format-specific preview:
/// - CSV: Table preview with first 10 rows
/// - Text/Markdown: First 20 lines of content
/// - PDF/Word/Excel: File icon and info message
///
/// Returns true if user confirms upload, false if cancelled.
class DocumentPreviewDialog extends StatefulWidget {
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

  @override
  State<DocumentPreviewDialog> createState() => _DocumentPreviewDialogState();
}

class _DocumentPreviewDialogState extends State<DocumentPreviewDialog> {
  /// Parsed preview data for table formats
  Map<String, dynamic>? _tablePreview;

  @override
  void initState() {
    super.initState();
    _loadPreview();
  }

  /// Load preview based on file format
  void _loadPreview() {
    final ext = _getFileExtension(widget.file.name);
    if (_isCsvFile(ext)) {
      _tablePreview = _parseCsvPreview(widget.file.bytes ?? []);
    }
  }

  /// Extract file extension from filename
  String _getFileExtension(String filename) {
    final dotIndex = filename.lastIndexOf('.');
    return dotIndex >= 0 ? filename.substring(dotIndex + 1).toLowerCase() : '';
  }

  /// Check if file is CSV format
  bool _isCsvFile(String ext) => ext == 'csv';

  /// Check if file is table format (CSV only; Excel uses binary info view)
  bool _isTableFile(String ext) => ext == 'csv';

  /// Check if file is text format
  bool _isTextFile(String ext) => ext == 'txt' || ext == 'md';

  /// Check if file is binary format (PDF, Word, or Excel)
  bool _isBinaryFile(String ext) => ext == 'pdf' || ext == 'docx' || ext == 'xlsx';

  /// Parse CSV file for preview
  Map<String, dynamic>? _parseCsvPreview(List<int> bytes) {
    try {
      final content = utf8.decode(bytes, allowMalformed: true);
      final lines = content.split('\n').where((l) => l.trim().isNotEmpty).toList();
      if (lines.isEmpty) return null;

      final headers = lines[0].split(',');
      final previewRows = lines.skip(1).take(10).map((l) => l.split(',')).toList();

      return {
        'headers': headers,
        'preview_rows': previewRows,
        'total_rows': lines.length,
      };
    } catch (e) {
      return null;
    }
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

  /// Extracts preview content from file bytes (for text files).
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

  /// Build table preview for CSV files
  Widget _buildTablePreview(Map<String, dynamic> preview) {
    final headers = preview['headers'] as List<dynamic>;
    final previewRows = preview['preview_rows'] as List<dynamic>;
    final totalRows = preview['total_rows'] as int;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Table preview
        ConstrainedBox(
          constraints: const BoxConstraints(maxHeight: 400),
          child: SingleChildScrollView(
            scrollDirection: Axis.vertical,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                headingRowColor: WidgetStateProperty.all(
                  Theme.of(context).colorScheme.surfaceContainerHighest,
                ),
                columns: headers.map((h) => DataColumn(
                  label: Text(
                    h.toString(),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                )).toList(),
                rows: previewRows.map<DataRow>((row) {
                  final cells = row as List<dynamic>;
                  return DataRow(
                    cells: cells.map((cell) => DataCell(
                      Text(cell.toString()),
                    )).toList(),
                  );
                }).toList(),
              ),
            ),
          ),
        ),

        const SizedBox(height: 12),

        // Row count footer
        Text(
          'Showing first ${previewRows.length} of ${totalRows - 1} data rows',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }

  /// Build text preview for .txt and .md files
  Widget _buildTextPreview(List<int> bytes) {
    final previewContent = _getPreviewContent(bytes);

    return ConstrainedBox(
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
    );
  }

  /// Build info message for binary files (PDF/Word)
  Widget _buildBinaryInfo() {
    return Column(
      children: [
        Icon(
          Icons.description_outlined,
          size: 64,
          color: Theme.of(context).colorScheme.primary,
        ),
        const SizedBox(height: 16),
        Text(
          'Preview not available for this file type.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
            fontSize: 16,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Content will be extracted after upload.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final bytes = widget.file.bytes ?? <int>[];
    final fileSize = _formatFileSize(bytes.length);
    final ext = _getFileExtension(widget.file.name);

    // Truncate filename if too long (keep extension visible)
    String displayName = widget.file.name;
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
      content: SizedBox(
        width: _isTableFile(ext) ? 600 : 400,
        child: Column(
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

            // Format-specific preview
            if (_isTableFile(ext) && _tablePreview != null)
              _buildTablePreview(_tablePreview!)
            else if (_isTextFile(ext))
              _buildTextPreview(bytes)
            else if (_isBinaryFile(ext))
              _buildBinaryInfo()
            else
              const Text('Unknown file format'),
          ],
        ),
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
