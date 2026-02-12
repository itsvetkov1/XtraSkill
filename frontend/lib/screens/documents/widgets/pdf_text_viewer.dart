import 'package:flutter/material.dart';

/// Widget for displaying PDF content as text with page markers.
///
/// Features:
/// - Metadata header showing page count
/// - Displays extracted text content from backend
/// - Page markers ([Page N]) visible in text
/// - Monospace font for readability
class PdfTextViewer extends StatelessWidget {
  final String content;
  final Map<String, dynamic> metadata;

  const PdfTextViewer({
    super.key,
    required this.content,
    required this.metadata,
  });

  @override
  Widget build(BuildContext context) {
    final pageCount = metadata['page_count'] ?? 0;

    return Column(
      children: [
        // Metadata header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            border: Border(
              bottom: BorderSide(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
          ),
          child: Row(
            children: [
              Icon(Icons.picture_as_pdf, size: 18, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                '$pageCount pages',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
        ),
        // Content
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: SelectableText(
              content,
              style: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 14,
                height: 1.5,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
