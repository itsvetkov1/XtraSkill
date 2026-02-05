/// Progress indicator for silent artifact generation.
library;

import 'dart:async';
import 'package:flutter/material.dart';

/// Progress indicator for silent artifact generation.
///
/// Shows indeterminate progress bar with typed label,
/// optional cancel button, and reassurance text after delay.
class GeneratingIndicator extends StatefulWidget {
  /// Type of artifact being generated (for label: "Generating [type]...")
  final String artifactType;

  /// Callback when user cancels generation
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
          // Indeterminate progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: null, // Indeterminate
              backgroundColor: theme.colorScheme.surfaceContainerHighest,
            ),
          ),
          const SizedBox(height: 12),

          // Label row with cancel button
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

          // Reassurance text (after delay)
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
