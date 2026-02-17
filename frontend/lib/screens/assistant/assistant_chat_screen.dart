/// Assistant chat screen for AI-powered conversation.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/message.dart';
import '../../providers/assistant_conversation_provider.dart';
import '../../widgets/resource_not_found_state.dart';
import 'widgets/assistant_message_bubble.dart';
import 'widgets/assistant_streaming_message.dart';

/// Main chat screen for Assistant threads
class AssistantChatScreen extends StatefulWidget {
  /// Thread ID to display
  final String threadId;

  const AssistantChatScreen({
    super.key,
    required this.threadId,
  });

  @override
  State<AssistantChatScreen> createState() => _AssistantChatScreenState();
}

class _AssistantChatScreenState extends State<AssistantChatScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _inputController = TextEditingController();
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode(onKeyEvent: _handleKeyEvent);

    // Load thread on mount
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AssistantConversationProvider>().loadThread(widget.threadId);
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _inputController.dispose();
    _focusNode.dispose();

    // Clear conversation state when leaving
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        context.read<AssistantConversationProvider>().clearConversation();
      }
    });

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
      if (_inputController.text.trim().isNotEmpty) {
        _handleSend();
        return KeyEventResult.handled;
      }

      return KeyEventResult.handled;
    }

    return KeyEventResult.ignored;
  }

  /// Insert newline at cursor position
  void _insertNewline() {
    final text = _inputController.text;
    final selection = _inputController.selection;

    final newText = text.replaceRange(selection.start, selection.end, '\n');
    _inputController.text = newText;

    _inputController.selection = TextSelection.collapsed(
      offset: selection.start + 1,
    );
  }

  void _handleSend() {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;

    final provider = context.read<AssistantConversationProvider>();
    if (provider.isStreaming) return;

    provider.sendMessage(text);
    _inputController.clear();
    _focusNode.requestFocus();
    _scrollToBottom();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      // Use post-frame callback to ensure layout is complete
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AssistantConversationProvider>(
      builder: (context, provider, child) {
        // Auto-scroll when messages change or streaming updates
        if (provider.messages.isNotEmpty || provider.isStreaming) {
          _scrollToBottom();
        }

        // Show loading indicator
        if (provider.loading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        // Show not-found state
        if (provider.isNotFound) {
          return Scaffold(
            appBar: AppBar(title: const Text('Thread')),
            body: ResourceNotFoundState(
              icon: Icons.speaker_notes_off_outlined,
              title: 'Thread not found',
              message: 'This conversation may have been deleted or you may not have access to it.',
              buttonLabel: 'Back to Assistant',
              onPressed: () => context.go('/assistant'),
            ),
          );
        }

        // Show error state (full screen)
        if (provider.error != null && !provider.hasPartialContent) {
          return Scaffold(
            appBar: AppBar(
              title: Text(provider.thread?.title ?? 'Assistant'),
            ),
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.error_outline,
                    size: 64,
                    color: Theme.of(context).colorScheme.error,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Failed to load conversation',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    provider.error!,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 24),
                  FilledButton.icon(
                    onPressed: () => provider.loadThread(widget.threadId),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            ),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: Text(provider.thread?.title ?? 'Assistant'),
          ),
          body: Column(
            children: [
              // Error banner with partial content
              if (provider.error != null && provider.hasPartialContent)
                MaterialBanner(
                  content: const Text('Connection lost - response incomplete'),
                  backgroundColor: Theme.of(context).colorScheme.errorContainer,
                  actions: [
                    TextButton(
                      onPressed: provider.clearError,
                      child: const Text('Dismiss'),
                    ),
                    if (provider.canRetry)
                      TextButton(
                        onPressed: provider.retryLastMessage,
                        child: const Text('Retry'),
                      ),
                  ],
                ),

              // Message list
              Expanded(
                child: SelectionArea(
                  child: _buildMessageList(provider),
                ),
              ),

              // Temporary chat input (will be replaced in Plan 64-04)
              _buildChatInput(provider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMessageList(AssistantConversationProvider provider) {
    final messages = provider.messages;

    // Empty state
    if (messages.isEmpty && !provider.isStreaming) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.chat_bubble_outline,
                size: 64,
                color: Theme.of(context).colorScheme.outline,
              ),
              const SizedBox(height: 16),
              Text(
                'Start a conversation',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'Ask about your business requirements or start a discussion.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      );
    }

    // Calculate extra items for streaming
    final hasStreamingItem = provider.isStreaming;
    final extraItemCount = hasStreamingItem ? 1 : 0;

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 16),
      itemCount: messages.length + extraItemCount,
      itemBuilder: (context, index) {
        // Regular messages
        if (index < messages.length) {
          final message = messages[index];
          final isLastMessage = index == messages.length - 1;
          final showRetry = isLastMessage &&
                           provider.error != null &&
                           message.role == MessageRole.assistant;

          return AssistantMessageBubble(
            message: message,
            onRetry: showRetry ? provider.retryLastMessage : null,
          );
        }

        // Streaming message
        if (hasStreamingItem && index == messages.length) {
          return AssistantStreamingMessage(
            text: provider.streamingText,
            statusMessage: provider.statusMessage,
            thinkingStartTime: provider.thinkingStartTime,
          );
        }

        return const SizedBox.shrink();
      },
    );
  }

  Widget _buildChatInput(AssistantConversationProvider provider) {
    final theme = Theme.of(context);
    final inputEnabled = !provider.isStreaming;

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          top: BorderSide(color: theme.colorScheme.outlineVariant),
        ),
      ),
      child: SafeArea(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _inputController,
                focusNode: _focusNode,
                enabled: inputEnabled,
                maxLines: 4,
                minLines: 1,
                keyboardType: TextInputType.multiline,
                textInputAction: TextInputAction.none,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: inputEnabled
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
            const SizedBox(width: 8),
            IconButton.filled(
              onPressed: inputEnabled ? _handleSend : null,
              icon: const Icon(Icons.send),
              tooltip: 'Send message',
            ),
          ],
        ),
      ),
    );
  }
}
