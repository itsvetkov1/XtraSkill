/// Collapsible artifact card with export functionality.
library;

import 'package:flutter/material.dart';

import '../../../models/artifact.dart';
import '../../../services/artifact_service.dart';

/// Collapsible card for displaying generated artifacts
class ArtifactCard extends StatefulWidget {
  /// The artifact to display
  final Artifact artifact;

  /// Thread ID for context
  final String threadId;

  const ArtifactCard({
    super.key,
    required this.artifact,
    required this.threadId,
  });

  @override
  State<ArtifactCard> createState() => _ArtifactCardState();
}

class _ArtifactCardState extends State<ArtifactCard> {
  final ArtifactService _artifactService = ArtifactService();
  bool _expanded = false;
  bool _loadingContent = false;
  String? _loadedContent;
  String? _error;
  bool _exporting = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final artifact = widget.artifact;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.primaryContainer.withValues(alpha: 0.1),
        border: Border(
          left: BorderSide(
            color: theme.colorScheme.primary,
            width: 4,
          ),
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header - always visible
          ListTile(
            leading: CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(
                artifact.artifactType.icon,
                color: theme.colorScheme.onPrimaryContainer,
                size: 20,
              ),
            ),
            title: Text(
              artifact.title,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(artifact.artifactType.displayName),
            trailing: IconButton(
              icon: Icon(_expanded ? Icons.expand_less : Icons.expand_more),
              onPressed: _toggleExpand,
            ),
            onTap: _toggleExpand,
          ),

          // Export buttons - always visible per CONTEXT.md
          _buildExportRow(theme),

          // Content - only when expanded
          if (_expanded) _buildContent(theme),
        ],
      ),
    );
  }

  Widget _buildExportRow(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.only(left: 16, right: 16, bottom: 8),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _ExportButton(
            icon: Icons.description_outlined,
            label: 'MD',
            tooltip: 'Export as Markdown',
            onPressed: _exporting ? null : () => _export('md'),
          ),
          const SizedBox(width: 8),
          _ExportButton(
            icon: Icons.picture_as_pdf_outlined,
            label: 'PDF',
            tooltip: 'Export as PDF',
            onPressed: _exporting ? null : () => _export('pdf'),
          ),
          const SizedBox(width: 8),
          _ExportButton(
            icon: Icons.article_outlined,
            label: 'Word',
            tooltip: 'Export as Word',
            onPressed: _exporting ? null : () => _export('docx'),
          ),
          if (_exporting) ...[
            const SizedBox(width: 8),
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildContent(ThemeData theme) {
    if (_loadingContent) {
      return const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null) {
      return Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              _error!,
              style: TextStyle(color: theme.colorScheme.error),
            ),
            TextButton(
              onPressed: _loadContent,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    final content = _loadedContent ?? widget.artifact.contentMarkdown;
    if (content == null) {
      return const Padding(
        padding: EdgeInsets.all(16),
        child: Text('No content available'),
      );
    }

    return Container(
      constraints: const BoxConstraints(maxHeight: 400),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Text(
          content,
          style: theme.textTheme.bodyMedium,
        ),
      ),
    );
  }

  void _toggleExpand() {
    setState(() => _expanded = !_expanded);

    // Lazy load content on first expand per PITFALL-08
    if (_expanded && _loadedContent == null && widget.artifact.contentMarkdown == null) {
      _loadContent();
    }
  }

  Future<void> _loadContent() async {
    setState(() {
      _loadingContent = true;
      _error = null;
    });

    try {
      final artifact = await _artifactService.getArtifact(widget.artifact.id);
      setState(() {
        _loadedContent = artifact.contentMarkdown;
        _loadingContent = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loadingContent = false;
      });
    }
  }

  Future<void> _export(String format) async {
    setState(() => _exporting = true);

    try {
      final filename = await _artifactService.exportArtifact(
        artifactId: widget.artifact.id,
        format: format,
        title: widget.artifact.title,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Exported: $filename'),
            action: SnackBarAction(
              label: 'OK',
              onPressed: () {},
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Export failed: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _exporting = false);
      }
    }
  }
}

/// Small export button with icon and label
class _ExportButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String tooltip;
  final VoidCallback? onPressed;

  const _ExportButton({
    required this.icon,
    required this.label,
    required this.tooltip,
    this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: OutlinedButton.icon(
        onPressed: onPressed,
        icon: Icon(icon, size: 16),
        label: Text(label, style: const TextStyle(fontSize: 12)),
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
      ),
    );
  }
}
