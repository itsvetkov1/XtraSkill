import 'package:flutter/material.dart';

/// Reusable not-found state widget for resources that don't exist.
///
/// Used when a valid URL route points to a deleted or inaccessible resource.
/// Distinct from EmptyState (no items yet) and ErrorState (network/server errors).
///
/// Key differences from EmptyState:
/// - Icon uses `theme.colorScheme.error` (not primary)
/// - Button icon is `Icons.arrow_back` (navigation away, not creation)
/// - No optional buttonIcon - always shows back arrow
///
/// Usage:
/// ```dart
/// ResourceNotFoundState(
///   icon: Icons.folder_off_outlined,
///   title: 'Project not found',
///   message: 'This project may have been deleted or you may not have access.',
///   buttonLabel: 'Back to Projects',
///   onPressed: () => context.go('/projects'),
/// )
/// ```
class ResourceNotFoundState extends StatelessWidget {
  /// Icon displayed at top (size: 64, error color)
  final IconData icon;

  /// Title text (e.g., "Project not found")
  final String title;

  /// Explanation message
  final String message;

  /// Label for navigation button
  final String buttonLabel;

  /// Navigation action
  final VoidCallback onPressed;

  const ResourceNotFoundState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    required this.buttonLabel,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 64,
              color: theme.colorScheme.error, // Error color, not primary
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style: theme.textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: onPressed,
              icon: const Icon(Icons.arrow_back),
              label: Text(buttonLabel),
            ),
          ],
        ),
      ),
    );
  }
}
