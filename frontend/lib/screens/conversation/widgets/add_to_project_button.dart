/// Button to add current chat to a project.
library;

import 'package:flutter/material.dart';

/// Toolbar button for adding chat to project
///
/// Displays icon + "Add to Project" label.
/// Only shown for project-less chats.
class AddToProjectButton extends StatelessWidget {
  /// Callback when button is pressed
  final VoidCallback onPressed;

  const AddToProjectButton({
    super.key,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: TextButton.icon(
        icon: const Icon(Icons.folder_open_outlined, size: 18),
        label: const Text('Add to Project'),
        style: TextButton.styleFrom(
          foregroundColor: Theme.of(context).colorScheme.primary,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        ),
        onPressed: onPressed,
      ),
    );
  }
}
