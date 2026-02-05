/// Error state shown when silent artifact generation fails.
library;

import 'package:flutter/material.dart';

/// Error state shown when silent artifact generation fails.
///
/// Shows generic user-friendly error message with Retry and Dismiss actions.
/// No technical error details are shown (per CONTEXT.md decision).
class GenerationErrorState extends StatelessWidget {
  /// Callback when user taps Retry
  final VoidCallback onRetry;

  /// Callback when user taps Dismiss
  final VoidCallback onDismiss;

  const GenerationErrorState({
    super.key,
    required this.onRetry,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Error icon + message
          Row(
            children: [
              Icon(
                Icons.error_outline,
                color: theme.colorScheme.onErrorContainer,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Something went wrong. Please try again.',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onErrorContainer,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Action buttons
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: onDismiss,
                child: const Text('Dismiss'),
              ),
              const SizedBox(width: 8),
              FilledButton.tonal(
                onPressed: onRetry,
                child: const Text('Retry'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
