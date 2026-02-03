/// Bottom sheet picker for artifact type selection.
library;

import 'package:flutter/material.dart';

import '../../../models/artifact.dart';

/// Result from artifact type picker - either preset type or custom prompt
class ArtifactTypeSelection {
  final ArtifactType? presetType;
  final String? customPrompt;

  const ArtifactTypeSelection.preset(ArtifactType type)
      : presetType = type,
        customPrompt = null;

  const ArtifactTypeSelection.custom(String prompt)
      : presetType = null,
        customPrompt = prompt;

  bool get isCustom => customPrompt != null;
}

/// Bottom sheet for selecting artifact type to generate
class ArtifactTypePicker extends StatefulWidget {
  const ArtifactTypePicker({super.key});

  /// Show the picker as a modal bottom sheet
  static Future<ArtifactTypeSelection?> show(BuildContext context) {
    return showModalBottomSheet<ArtifactTypeSelection>(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (sheetContext) => const ArtifactTypePicker(),
    );
  }

  @override
  State<ArtifactTypePicker> createState() => _ArtifactTypePickerState();
}

class _ArtifactTypePickerState extends State<ArtifactTypePicker> {
  final TextEditingController _customController = TextEditingController();
  bool _showCustomInput = false;

  @override
  void dispose() {
    _customController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Icon(
                  Icons.auto_awesome,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(width: 8),
                Text(
                  'Generate Artifact',
                  style: theme.textTheme.titleLarge,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Select the type of document to generate from this conversation',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),

            // Preset type cards
            ...ArtifactType.values.map((type) => _buildTypeCard(context, type)),

            // Custom option card
            _buildCustomCard(context, theme),

            // Custom input field (shown when Custom selected)
            if (_showCustomInput) ...[
              const SizedBox(height: 8),
              TextField(
                controller: _customController,
                autofocus: true,
                maxLines: 3,
                decoration: InputDecoration(
                  hintText: 'Describe what you want to generate...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  suffixIcon: IconButton(
                    icon: const Icon(Icons.send),
                    onPressed: _submitCustom,
                  ),
                ),
                onSubmitted: (_) => _submitCustom(),
              ),
            ],

            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  Widget _buildTypeCard(BuildContext context, ArtifactType type) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: theme.colorScheme.primaryContainer,
          child: Icon(
            type.icon,
            color: theme.colorScheme.onPrimaryContainer,
          ),
        ),
        title: Text(type.displayName),
        subtitle: Text(
          type.description,
          style: theme.textTheme.bodySmall,
        ),
        trailing: Icon(
          Icons.chevron_right,
          color: theme.colorScheme.onSurfaceVariant,
        ),
        onTap: () => Navigator.pop(context, ArtifactTypeSelection.preset(type)),
      ),
    );
  }

  Widget _buildCustomCard(BuildContext context, ThemeData theme) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: _showCustomInput
          ? theme.colorScheme.primaryContainer.withValues(alpha: 0.3)
          : null,
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: theme.colorScheme.secondaryContainer,
          child: Icon(
            Icons.edit_note,
            color: theme.colorScheme.onSecondaryContainer,
          ),
        ),
        title: const Text('Custom'),
        subtitle: Text(
          'Write your own generation prompt',
          style: theme.textTheme.bodySmall,
        ),
        trailing: Icon(
          _showCustomInput ? Icons.expand_less : Icons.chevron_right,
          color: theme.colorScheme.onSurfaceVariant,
        ),
        onTap: () {
          setState(() => _showCustomInput = !_showCustomInput);
        },
      ),
    );
  }

  void _submitCustom() {
    final prompt = _customController.text.trim();
    if (prompt.isNotEmpty) {
      Navigator.pop(context, ArtifactTypeSelection.custom(prompt));
    }
  }
}
