/// Streaming message widget for Assistant chat with thinking timer and markdown rendering.
library;

import 'dart:async';
import 'package:flutter/material.dart';

import 'markdown_message.dart';

/// Widget displaying streaming AI response with thinking indicator and elapsed time
class AssistantStreamingMessage extends StatefulWidget {
  /// Text accumulated so far
  final String text;

  /// Optional status message (e.g., "Searching documents...")
  final String? statusMessage;

  /// When thinking started (for elapsed time display)
  final DateTime? thinkingStartTime;

  const AssistantStreamingMessage({
    super.key,
    required this.text,
    this.statusMessage,
    this.thinkingStartTime,
  });

  @override
  State<AssistantStreamingMessage> createState() => _AssistantStreamingMessageState();
}

class _AssistantStreamingMessageState extends State<AssistantStreamingMessage> {
  Timer? _timer;
  int _elapsedSeconds = 0;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  @override
  void didUpdateWidget(AssistantStreamingMessage oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Restart timer if thinkingStartTime changed
    if (widget.thinkingStartTime != oldWidget.thinkingStartTime) {
      _timer?.cancel();
      _startTimer();
    }

    // Stop timer if thinkingStartTime is cleared (thinking ended)
    if (widget.thinkingStartTime == null && oldWidget.thinkingStartTime != null) {
      _timer?.cancel();
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _startTimer() {
    if (widget.thinkingStartTime == null) return;

    // Calculate initial elapsed time
    _elapsedSeconds = DateTime.now().difference(widget.thinkingStartTime!).inSeconds;

    // Update every second
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          _elapsedSeconds = DateTime.now().difference(widget.thinkingStartTime!).inSeconds;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: theme.colorScheme.surfaceContainerHighest,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(16),
            topRight: Radius.circular(16),
            bottomLeft: Radius.circular(4),
            bottomRight: Radius.circular(16),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Show thinking indicator with elapsed time when no text yet
            if (widget.text.isEmpty && widget.statusMessage == null && widget.thinkingStartTime != null)
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Thinking... (${_elapsedSeconds}s)',
                    style: TextStyle(
                      fontStyle: FontStyle.italic,
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),

            // Show status message if present
            if (widget.statusMessage != null) ...[
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    widget.statusMessage!,
                    style: TextStyle(
                      fontStyle: FontStyle.italic,
                      color: theme.colorScheme.onSurfaceVariant,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              if (widget.text.isNotEmpty) const SizedBox(height: 8),
            ],

            // Show accumulated text with markdown if present
            if (widget.text.isNotEmpty)
              MarkdownMessage(
                content: widget.text,
                isStreaming: true,
              ),
          ],
        ),
      ),
    );
  }
}
