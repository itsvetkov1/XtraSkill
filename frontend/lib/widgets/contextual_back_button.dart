/// Contextual back button showing destination context.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../providers/project_provider.dart';

/// Back button that shows the destination name instead of a generic arrow
///
/// Displays contextual information about where the back action will navigate:
/// - /projects/:id -> "<- Projects"
/// - /projects/:id/threads/:tid -> "<- {Project Name}"
///
/// For root pages (/home, /projects, /settings), no back button is shown.
///
/// Usage:
/// ```dart
/// AppBar(
///   leading: const ContextualBackButton(),
///   // ...
/// )
/// ```
class ContextualBackButton extends StatelessWidget {
  /// Whether to show only the icon (no label text)
  final bool iconOnly;

  const ContextualBackButton({
    super.key,
    this.iconOnly = false,
  });

  @override
  Widget build(BuildContext context) {
    final parentLabel = _getParentLabel(context);

    // No parent (root page) - no back button
    if (parentLabel == null) {
      return const SizedBox.shrink();
    }

    // Check if we can actually pop
    if (!context.canPop()) {
      return const SizedBox.shrink();
    }

    if (iconOnly) {
      return IconButton(
        icon: const Icon(Icons.arrow_back),
        tooltip: parentLabel,
        onPressed: () => context.pop(),
      );
    }

    return TextButton.icon(
      onPressed: () => context.pop(),
      icon: const Icon(Icons.arrow_back, size: 20),
      label: Text(parentLabel),
      style: TextButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }

  /// Determine the parent page label based on current route
  String? _getParentLabel(BuildContext context) {
    final path = GoRouterState.of(context).uri.path;

    // Root pages have no back button
    if (path == '/home' || path == '/projects' || path == '/settings' || path == '/chats' || path == '/assistant') {
      return null;
    }

    // /assistant/:threadId -> Back to Assistant
    if (path.startsWith('/assistant/')) {
      return 'Assistant';
    }

    // /projects/:id -> Back to Projects
    if (RegExp(r'^/projects/[^/]+$').hasMatch(path)) {
      return 'Projects';
    }

    // /projects/:id/threads/:tid -> Back to {Project Name}
    if (path.contains('/threads/')) {
      final projectProvider = context.read<ProjectProvider>();
      return projectProvider.selectedProject?.name ?? 'Project';
    }

    // /projects/:id/documents/:did -> Back to {Project Name}
    if (path.contains('/documents/')) {
      final projectProvider = context.read<ProjectProvider>();
      return projectProvider.selectedProject?.name ?? 'Project';
    }

    // Generic fallback for nested routes
    final segments = path.split('/').where((s) => s.isNotEmpty).toList();
    if (segments.length > 1) {
      // Return the parent segment name
      final parentSegment = segments[segments.length - 2];
      return _formatSegmentLabel(parentSegment);
    }

    return null;
  }

  /// Format a path segment into a human-readable label
  String _formatSegmentLabel(String segment) {
    // Skip UUIDs
    if (RegExp(
            r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        .hasMatch(segment)) {
      return 'Back';
    }

    // Capitalize first letter
    return segment.isEmpty
        ? 'Back'
        : '${segment[0].toUpperCase()}${segment.substring(1).toLowerCase()}';
  }
}
