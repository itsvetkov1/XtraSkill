import 'package:flutter/material.dart';

/// Reusable empty state widget for consistent empty state presentation.
///
/// Implements ONBOARD-01 to ONBOARD-03 requirements:
/// - Themed icon (large, primary color)
/// - Encouraging message (title + body text)
/// - FilledButton CTA to create first item
///
/// Usage:
/// ```dart
/// EmptyState(
///   icon: Icons.folder_outlined,
///   title: 'No projects yet',
///   message: 'Create your first project to start capturing requirements.',
///   buttonLabel: 'Create Project',
///   onPressed: () => _createProject(),
/// )
/// ```
class EmptyState extends StatelessWidget {
  /// Large icon displayed at top (size: 64, themed primary color)
  final IconData icon;

  /// Title text displayed below icon (titleLarge style)
  final String title;

  /// Encouraging message displayed below title (bodyMedium, centered)
  final String message;

  /// Label for the CTA button
  final String buttonLabel;

  /// Callback when CTA button is pressed
  final VoidCallback onPressed;

  /// Optional icon for the button (defaults to Icons.add)
  final IconData? buttonIcon;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    required this.buttonLabel,
    required this.onPressed,
    this.buttonIcon,
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
              color: theme.colorScheme.primary,
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
              icon: Icon(buttonIcon ?? Icons.add),
              label: Text(buttonLabel),
            ),
          ],
        ),
      ),
    );
  }
}
