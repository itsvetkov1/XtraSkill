/// Mode badge widget for AppBar displaying current conversation mode.
library;

import 'package:flutter/material.dart';

/// Displays current conversation mode as a tappable chip in the AppBar.
///
/// Shows icon + short label. If mode is null, shows "Select Mode" with outline style.
/// If mode is set, shows filled chip with mode icon/name.
class ModeBadge extends StatelessWidget {
  /// Current mode value ("meeting", "document_refinement", or null)
  final String? mode;

  /// Callback when badge is tapped to change mode
  final VoidCallback onTap;

  const ModeBadge({
    super.key,
    required this.mode,
    required this.onTap,
  });

  /// Get display name for mode
  String get _displayName {
    switch (mode) {
      case 'meeting':
        return 'Meeting';
      case 'document_refinement':
        return 'Refinement';
      default:
        return 'Select Mode';
    }
  }

  /// Get icon for mode
  IconData get _icon {
    switch (mode) {
      case 'meeting':
        return Icons.groups;
      case 'document_refinement':
        return Icons.edit_document;
      default:
        return Icons.chat_bubble_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    // Use filled style when mode is set, outline when not
    if (mode != null) {
      return ActionChip(
        avatar: Icon(_icon, size: 16),
        label: Text(_displayName),
        onPressed: onTap,
        backgroundColor: colorScheme.secondaryContainer,
        labelStyle: TextStyle(color: colorScheme.onSecondaryContainer),
        side: BorderSide.none,
        visualDensity: VisualDensity.compact,
      );
    }

    // Outline style for "Select Mode"
    return ActionChip(
      avatar: Icon(_icon, size: 16, color: colorScheme.outline),
      label: Text(_displayName),
      onPressed: onTap,
      backgroundColor: Colors.transparent,
      labelStyle: TextStyle(color: colorScheme.outline),
      side: BorderSide(color: colorScheme.outline),
      visualDensity: VisualDensity.compact,
    );
  }
}
