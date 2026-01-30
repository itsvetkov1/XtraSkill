/// Reusable delete confirmation dialog.
library;

import 'package:flutter/material.dart';

/// Show delete confirmation dialog
///
/// Returns true if user confirms deletion, false if cancelled.
/// Follows CONTEXT.md decisions:
/// - Summary cascade info only (no exact counts)
/// - Neutral visual style (no red/warning treatment)
/// - Generic item references ("Delete this project?")
/// - Button labels: "Delete" / "Cancel"
Future<bool> showDeleteConfirmationDialog({
  required BuildContext context,
  required String itemType,
  String? cascadeMessage,
}) async {
  final confirmed = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (BuildContext dialogContext) {
      return AlertDialog(
        title: Text('Delete this $itemType?'),
        content: cascadeMessage != null ? Text(cascadeMessage) : null,
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Delete'),
          ),
        ],
      );
    },
  );

  return confirmed ?? false;
}
