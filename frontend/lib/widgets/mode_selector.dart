/// ChoiceChip-based mode selector for AI conversation modes.
library;

import 'package:flutter/material.dart';

/// Displays Meeting Mode and Document Refinement Mode as tappable chips
/// for starting a conversation with a specific AI mode.
class ModeSelector extends StatelessWidget {
  /// Callback when user selects a mode
  /// Returns the full mode name: "Meeting Mode" or "Document Refinement Mode"
  final ValueChanged<String> onModeSelected;

  const ModeSelector({super.key, required this.onModeSelected});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Select conversation mode:',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12.0,
            runSpacing: 8.0,
            children: [
              ActionChip(
                avatar: const Icon(Icons.groups, size: 18),
                label: const Text('Meeting Mode'),
                onPressed: () => onModeSelected('Meeting Mode'),
              ),
              ActionChip(
                avatar: const Icon(Icons.edit_document, size: 18),
                label: const Text('Document Refinement'),
                onPressed: () => onModeSelected('Document Refinement Mode'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Meeting Mode: Real-time discovery with stakeholders\n'
            'Document Refinement: Refine existing requirements',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
        ],
      ),
    );
  }
}
