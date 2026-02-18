/// Full-featured chat input for Assistant with file attachment and skill selection.
library;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../providers/assistant_conversation_provider.dart';
import '../../../utils/skill_emoji.dart';
import 'document_attachment_chip.dart';
import 'skill_selector.dart';

/// Complete chat input widget for Assistant threads
///
/// Layout:
/// ```
/// [Skill chip]  [File chip 1] [File chip 2]  ← chips above (if present)
/// [📎] [_____text input_____] [🧩] [→]
///  ^              ^              ^    ^
///  attach      3-4 lines       skills send
///  (left)      multi-line       (right, grouped)
/// ```
class AssistantChatInput extends StatefulWidget {
  /// Callback when message is sent
  final void Function(String message) onSend;

  /// Whether input is enabled (disabled during streaming)
  final bool enabled;

  /// Provider for skill and file state
  final AssistantConversationProvider provider;

  const AssistantChatInput({
    super.key,
    required this.onSend,
    required this.enabled,
    required this.provider,
  });

  @override
  State<AssistantChatInput> createState() => _AssistantChatInputState();
}

class _AssistantChatInputState extends State<AssistantChatInput> {
  final TextEditingController _controller = TextEditingController();
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode(onKeyEvent: _handleKeyEvent);
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  /// Handle keyboard events for Enter to send, Shift+Enter for newline
  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) {
      return KeyEventResult.ignored;
    }

    if (event.logicalKey == LogicalKeyboardKey.enter) {
      // Shift+Enter: insert newline
      if (HardwareKeyboard.instance.isShiftPressed) {
        _insertNewline();
        return KeyEventResult.handled;
      }

      // Plain Enter: send message
      if (_controller.text.trim().isNotEmpty && widget.enabled) {
        _handleSend();
        return KeyEventResult.handled;
      }

      return KeyEventResult.handled;
    }

    return KeyEventResult.ignored;
  }

  /// Insert newline at cursor position
  void _insertNewline() {
    final text = _controller.text;
    final selection = _controller.selection;

    final newText = text.replaceRange(selection.start, selection.end, '\n');
    _controller.text = newText;

    _controller.selection = TextSelection.collapsed(
      offset: selection.start + 1,
    );
  }

  void _handleSend() {
    final text = _controller.text.trim();
    if (text.isEmpty || !widget.enabled) return;

    widget.onSend(text);
    _controller.clear();
    _focusNode.requestFocus();
  }

  /// Open file picker for attachment
  Future<void> _handleAttachFiles() async {
    if (!widget.enabled) return;

    try {
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
        type: FileType.any,
      );

      if (result != null) {
        for (final file in result.files) {
          // Create AttachedFile from picked file
          final attachedFile = AttachedFile(
            name: file.name,
            size: file.size,
            bytes: file.bytes,
            contentType: file.extension ?? 'application/octet-stream',
          );
          widget.provider.addAttachedFile(attachedFile);
        }
      }
    } catch (e) {
      debugPrint('File picker error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasSkill = widget.provider.selectedSkill != null;
    final hasFiles = widget.provider.attachedFiles.isNotEmpty;
    final hasChips = hasSkill || hasFiles;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          top: BorderSide(color: theme.colorScheme.outlineVariant),
        ),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Chips area (skill + files)
            if (hasChips) _buildChipsArea(theme),

            // Input row
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                // Attachment button (left)
                IconButton(
                  icon: const Icon(Icons.attach_file),
                  tooltip: 'Attach files',
                  onPressed: widget.enabled ? _handleAttachFiles : null,
                ),

                // Text input
                Expanded(
                  child: TextField(
                    controller: _controller,
                    focusNode: _focusNode,
                    enabled: widget.enabled,
                    maxLines: null,
                    minLines: 3,
                    keyboardType: TextInputType.multiline,
                    textInputAction: TextInputAction.none,
                    textCapitalization: TextCapitalization.sentences,
                    decoration: InputDecoration(
                      hintText: widget.enabled
                          ? 'Type a message...'
                          : 'Waiting for response...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: theme.colorScheme.surfaceContainerHighest,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                    ),
                  ),
                ),

                // Skills button
                SkillSelector(
                  onSkillSelected: widget.provider.selectSkill,
                ),

                // Send button
                IconButton.filled(
                  onPressed: widget.enabled && _controller.text.trim().isNotEmpty
                      ? _handleSend
                      : null,
                  icon: const Icon(Icons.send),
                  tooltip: 'Send message',
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Build chips area (skill chip + file chips)
  Widget _buildChipsArea(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, left: 8, right: 8),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          // Skill chip
          if (widget.provider.selectedSkill != null)
            Chip(
              avatar: Text(
                getSkillEmoji(widget.provider.selectedSkill!.name),
                style: const TextStyle(fontSize: 16),
              ),
              label: Text(
                widget.provider.selectedSkill!.name,
                style: TextStyle(
                  fontSize: 13,
                  color: theme.colorScheme.onPrimary,
                ),
              ),
              deleteIcon: Icon(
                Icons.close,
                size: 18,
                color: theme.colorScheme.onPrimary,
              ),
              onDeleted: widget.provider.clearSkill,
              backgroundColor: theme.colorScheme.primary,
              visualDensity: VisualDensity.compact,
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),

          // File chips
          ...widget.provider.attachedFiles.map((file) {
            return DocumentAttachmentChip(
              filename: file.name,
              fileSize: file.size,
              onRemove: () => widget.provider.removeAttachedFile(file),
            );
          }),
        ],
      ),
    );
  }
}
