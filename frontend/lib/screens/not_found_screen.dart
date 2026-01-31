import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// 404 error page shown when GoRouter cannot match a route.
///
/// Displays the attempted path and provides navigation back to home.
/// Used by GoRouter's errorBuilder in main.dart.
class NotFoundScreen extends StatelessWidget {
  /// The URL path that was attempted but not found.
  final String attemptedPath;

  const NotFoundScreen({super.key, required this.attemptedPath});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Page Not Found'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: theme.colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              '404 - Page Not Found',
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'The page "$attemptedPath" does not exist.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => context.go('/home'),
              icon: const Icon(Icons.home),
              label: const Text('Go to Home'),
            ),
          ],
        ),
      ),
    );
  }
}
