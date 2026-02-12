/// Source attribution chips showing documents used in AI response.
library;

import 'package:flutter/material.dart';

import '../../../services/ai_service.dart';

/// Collapsible section showing source documents used in a response
class SourceChips extends StatefulWidget {
  /// List of document sources
  final List<DocumentSource> sources;

  /// Callback when a source chip is tapped
  final void Function(String documentId, String filename)? onSourceTap;

  const SourceChips({
    super.key,
    required this.sources,
    this.onSourceTap,
  });

  @override
  State<SourceChips> createState() => _SourceChipsState();
}

class _SourceChipsState extends State<SourceChips> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    // SRC-04: Don't show anything if no documents used
    if (widget.sources.isEmpty) return const SizedBox.shrink();

    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Collapsible header per CONTEXT.md
          InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            borderRadius: BorderRadius.circular(4),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.source_outlined,
                    size: 16,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _expanded
                        ? 'Hide sources'
                        : '${widget.sources.length} source${widget.sources.length == 1 ? '' : 's'} used',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  Icon(
                    _expanded ? Icons.expand_less : Icons.expand_more,
                    size: 16,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ],
              ),
            ),
          ),

          // Chips - only when expanded
          if (_expanded) _buildChips(theme),
        ],
      ),
    );
  }

  Widget _buildChips(ThemeData theme) {
    // Per PITFALL-13: Use Wrap widget for overflow handling
    final visibleSources = widget.sources;

    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Wrap(
        spacing: 8,
        runSpacing: 4,
        children: [
          for (final source in visibleSources)
            ActionChip(
              avatar: Icon(
                _getSourceIcon(source),
                size: 16,
                color: theme.colorScheme.onSecondaryContainer,
              ),
              label: Text(
                _getChipLabel(source),
                style: TextStyle(
                  fontSize: 12,
                  color: theme.colorScheme.onSecondaryContainer,
                ),
              ),
              tooltip: _getTooltip(source),
              backgroundColor:
                  theme.colorScheme.secondaryContainer.withValues(alpha: 0.5),
              side: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.5),
              ),
              onPressed: () =>
                  widget.onSourceTap?.call(source.id, source.filename),
            ),
        ],
      ),
    );
  }

  IconData _getSourceIcon(DocumentSource source) {
    final ct = source.contentType ?? 'text/plain';
    if (ct.contains('spreadsheet') || ct == 'text/csv') return Icons.table_chart;
    if (ct == 'application/pdf') return Icons.picture_as_pdf;
    if (ct.contains('wordprocessing')) return Icons.article;
    return Icons.description_outlined;
  }

  String _getChipLabel(DocumentSource source) {
    final name = _truncateFilename(source.filename);
    final metadata = source.metadata;
    if (metadata == null) return name;

    // Excel: show sheet name
    final sheetNames = metadata['sheet_names'] as List?;
    if (sheetNames != null && sheetNames.isNotEmpty) {
      return '$name (${sheetNames[0]})';
    }

    // PDF: show page count
    final pageCount = metadata['page_count'];
    if (pageCount != null) {
      return '$name ($pageCount pg)';
    }

    return name;
  }

  String _getTooltip(DocumentSource source) {
    final metadata = source.metadata;
    if (metadata == null) return source.filename;

    // Build richer tooltip with metadata
    final parts = [source.filename];

    final sheetNames = metadata['sheet_names'] as List?;
    if (sheetNames != null && sheetNames.isNotEmpty) {
      parts.add('Sheet: ${sheetNames[0]}');
    }

    final pageCount = metadata['page_count'];
    if (pageCount != null) {
      parts.add('$pageCount pages');
    }

    return parts.join(' • ');
  }

  String _truncateFilename(String filename) {
    if (filename.length <= 25) return filename;
    // Keep extension visible
    final dotIndex = filename.lastIndexOf('.');
    if (dotIndex > 0 && filename.length - dotIndex <= 5) {
      final ext = filename.substring(dotIndex);
      final name = filename.substring(0, dotIndex);
      if (name.length > 20) {
        return '${name.substring(0, 17)}...$ext';
      }
    }
    return '${filename.substring(0, 22)}...';
  }
}
