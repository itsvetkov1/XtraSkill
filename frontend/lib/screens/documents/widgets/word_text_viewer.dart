import 'package:flutter/material.dart';

/// Widget for displaying Word document content with paragraph structure.
///
/// Features:
/// - Metadata header with document type icon
/// - Displays extracted text content from backend
/// - Paragraph structure preserved (double newlines)
/// - Larger line height (1.6) for readability
class WordTextViewer extends StatelessWidget {
  final String content;
  final Map<String, dynamic> metadata;

  const WordTextViewer({
    super.key,
    required this.content,
    required this.metadata,
  });

  @override
  Widget build(BuildContext context) {
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
              Icon(Icons.article, size: 18, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                'Word Document',
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
                fontSize: 14,
                height: 1.6,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
