/// Mode change dialog with warning about context shift.
library;

import 'package:flutter/material.dart';

/// Dialog for selecting conversation mode with warning about context shift.
///
/// Returns the selected mode string or null if cancelled.
/// Modes: "meeting", "document_refinement"
class ModeChangeDialog extends StatefulWidget {
  /// Current mode value (null if not set)
  final String? currentMode;

  const ModeChangeDialog({
    super.key,
    this.currentMode,
  });

  /// Show the dialog and return selected mode or null
  static Future<String?> show(BuildContext context, {String? currentMode}) {
    return showDialog<String>(
      context: context,
      builder: (dialogContext) => ModeChangeDialog(currentMode: currentMode),
    );
  }

  @override
  State<ModeChangeDialog> createState() => _ModeChangeDialogState();
}

class _ModeChangeDialogState extends State<ModeChangeDialog> {
  late String? _selectedMode;

  @override
  void initState() {
    super.initState();
    _selectedMode = widget.currentMode;
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return AlertDialog(
      title: const Text('Change Conversation Mode'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Warning banner
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: colorScheme.tertiaryContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  size: 20,
                  color: colorScheme.onTertiaryContainer,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Changing mode may affect how the AI interprets previous messages in this conversation.',
                    style: TextStyle(
                      fontSize: 13,
                      color: colorScheme.onTertiaryContainer,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Mode options
          RadioListTile<String>(
            title: Row(
              children: [
                Icon(Icons.groups, size: 20, color: colorScheme.primary),
                const SizedBox(width: 12),
                const Text('Meeting Mode'),
              ],
            ),
            subtitle: const Text('Real-time discovery with stakeholders'),
            value: 'meeting',
            groupValue: _selectedMode,
            onChanged: (value) => setState(() => _selectedMode = value),
            contentPadding: EdgeInsets.zero,
          ),
          RadioListTile<String>(
            title: Row(
              children: [
                Icon(Icons.edit_document, size: 20, color: colorScheme.primary),
                const SizedBox(width: 12),
                const Text('Document Refinement'),
              ],
            ),
            subtitle: const Text('Refine existing requirements'),
            value: 'document_refinement',
            groupValue: _selectedMode,
            onChanged: (value) => setState(() => _selectedMode = value),
            contentPadding: EdgeInsets.zero,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: _selectedMode != null && _selectedMode != widget.currentMode
              ? () => Navigator.of(context).pop(_selectedMode)
              : null,
          child: const Text('Confirm'),
        ),
      ],
    );
  }
}
