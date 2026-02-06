/// Widget displaying artifact generation progress.
library;

import 'dart:async';
import 'package:flutter/material.dart';

/// Displays progress indicator during artifact generation
class GeneratingIndicator extends StatefulWidget {
  /// Type of artifact being generated (e.g., "User Stories")
  final String artifactType;

  /// Callback when cancel button tapped
  final VoidCallback? onCancel;

  /// Delay before showing reassurance text
  final Duration reassuranceDelay;

  const GeneratingIndicator({
    super.key,
    required this.artifactType,
    this.onCancel,
    this.reassuranceDelay = const Duration(seconds: 15),
  });

  @override
  State<GeneratingIndicator> createState() => _GeneratingIndicatorState();
}

class _GeneratingIndicatorState extends State<GeneratingIndicator> {
  bool _showReassurance = false;
  Timer? _reassuranceTimer;

  @override
  void initState() {
    super.initState();
    _reassuranceTimer = Timer(widget.reassuranceDelay, () {
      if (mounted) {
        setState(() => _showReassurance = true);
      }
    });
  }

  @override
  void dispose() {
    _reassuranceTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: null,
              backgroundColor: theme.colorScheme.surfaceContainerHighest,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  'Generating ${widget.artifactType}...',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
              if (widget.onCancel != null)
                TextButton(
                  onPressed: widget.onCancel,
                  child: const Text('Cancel'),
                ),
            ],
          ),
          if (_showReassurance) ...[
            const SizedBox(height: 4),
            Text(
              'This may take a moment...',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
