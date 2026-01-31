/// Breadcrumb navigation widget for route-based path display.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../providers/conversation_provider.dart';
import '../providers/project_provider.dart';

/// Data class representing a single breadcrumb segment
class Breadcrumb {
  /// Display label for this breadcrumb
  final String label;

  /// Route to navigate to when clicked (null = current page, not clickable)
  final String? route;

  const Breadcrumb(this.label, [this.route]);
}

/// Breadcrumb navigation bar displaying clickable path segments
///
/// Parses the current route and builds a breadcrumb trail showing the
/// navigation hierarchy. Clickable segments navigate to their routes,
/// while the current page (last segment) is non-clickable and bold.
///
/// Examples:
/// - /home -> "Home"
/// - /projects -> "Projects"
/// - /projects/:id -> "Projects > Project Name"
/// - /settings -> "Settings"
class BreadcrumbBar extends StatelessWidget {
  /// Maximum visible breadcrumbs before truncation (for narrow screens)
  final int? maxVisible;

  const BreadcrumbBar({super.key, this.maxVisible});

  @override
  Widget build(BuildContext context) {
    final path = GoRouterState.of(context).uri.path;
    final breadcrumbs = _buildBreadcrumbs(context, path);

    if (breadcrumbs.isEmpty) return const SizedBox();

    // Apply truncation for narrow screens
    final displayBreadcrumbs = _applyTruncation(breadcrumbs);

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (int i = 0; i < displayBreadcrumbs.length; i++) ...[
            if (i > 0)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Icon(
                  Icons.chevron_right,
                  size: 16,
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
            _buildBreadcrumbItem(context, displayBreadcrumbs[i]),
          ],
        ],
      ),
    );
  }

  /// Build breadcrumb list from current path
  List<Breadcrumb> _buildBreadcrumbs(BuildContext context, String path) {
    final breadcrumbs = <Breadcrumb>[];
    final segments = path.split('/').where((s) => s.isNotEmpty).toList();

    // Root or /home -> Home
    if (path == '/' || path == '/home') {
      return [const Breadcrumb('Home')];
    }

    // /settings -> Settings
    if (path == '/settings') {
      return [const Breadcrumb('Settings')];
    }

    // /projects routes
    if (segments.isNotEmpty && segments[0] == 'projects') {
      // /projects -> Projects (just the list, no parent link)
      if (segments.length == 1) {
        return [const Breadcrumb('Projects')];
      }

      // /projects/:id or /projects/:id/threads/:threadId
      breadcrumbs.add(const Breadcrumb('Projects', '/projects'));

      // Add project name (segments[1] is the project ID)
      if (segments.length >= 2) {
        final projectProvider = context.read<ProjectProvider>();
        final projectName =
            projectProvider.selectedProject?.name ?? 'Project';

        // If we have threads segment, project name links to project detail
        if (segments.length >= 4 && segments[2] == 'threads') {
          final projectId = segments[1];
          breadcrumbs.add(Breadcrumb(projectName, '/projects/$projectId'));

          // Add thread/conversation name
          final conversationProvider = context.read<ConversationProvider>();
          final threadTitle =
              conversationProvider.thread?.title ?? 'Conversation';
          breadcrumbs.add(Breadcrumb(threadTitle));
        } else {
          // Just /projects/:id - project name is current page (no link)
          breadcrumbs.add(Breadcrumb(projectName));
        }
      }

      return breadcrumbs;
    }

    // Fallback: use path segments as labels
    for (int i = 0; i < segments.length; i++) {
      final isLast = i == segments.length - 1;
      final label = _formatSegmentLabel(segments[i]);
      final route = isLast ? null : '/${segments.sublist(0, i + 1).join('/')}';
      breadcrumbs.add(Breadcrumb(label, route));
    }

    return breadcrumbs;
  }

  /// Apply truncation for narrow screens if maxVisible is set
  List<Breadcrumb> _applyTruncation(List<Breadcrumb> breadcrumbs) {
    if (maxVisible == null || breadcrumbs.length <= maxVisible!) {
      return breadcrumbs;
    }

    // Show "..." followed by the last N breadcrumbs
    final truncated = <Breadcrumb>[
      const Breadcrumb('...'),
      ...breadcrumbs.skip(breadcrumbs.length - maxVisible! + 1),
    ];

    return truncated;
  }

  /// Format a path segment into a human-readable label
  String _formatSegmentLabel(String segment) {
    // Skip UUIDs (they look like: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    if (RegExp(
            r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        .hasMatch(segment)) {
      return 'Item';
    }

    // Capitalize first letter and replace hyphens/underscores with spaces
    return segment
        .replaceAll(RegExp(r'[-_]'), ' ')
        .split(' ')
        .map((word) => word.isEmpty
            ? ''
            : '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}')
        .join(' ');
  }

  /// Build a single breadcrumb item (clickable or static)
  Widget _buildBreadcrumbItem(BuildContext context, Breadcrumb breadcrumb) {
    if (breadcrumb.route != null) {
      // Clickable breadcrumb
      return TextButton(
        onPressed: () => context.go(breadcrumb.route!),
        style: TextButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
        child: Text(
          breadcrumb.label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.primary,
              ),
        ),
      );
    }

    // Current page (non-clickable, bold)
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Text(
        breadcrumb.label,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }
}
