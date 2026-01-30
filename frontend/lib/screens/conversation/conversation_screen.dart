/// Conversation screen for AI-powered chat.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/message.dart';
import '../../providers/conversation_provider.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../../widgets/mode_selector.dart';
import 'widgets/chat_input.dart';
import 'widgets/message_bubble.dart';
import 'widgets/streaming_message.dart';

/// Main conversation screen with message list and input
class ConversationScreen extends StatefulWidget {
  /// Thread ID to display
  final String threadId;

  const ConversationScreen({super.key, required this.threadId});

  @override
  State<ConversationScreen> createState() => _ConversationScreenState();
}

class _ConversationScreenState extends State<ConversationScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // Load thread on mount
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ConversationProvider>().loadThread(widget.threadId);
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    // Clear conversation state when leaving - use post frame to avoid setState during build
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        context.read<ConversationProvider>().clearConversation();
      }
    });
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  /// Show message options bottom sheet
  void _showMessageOptions(BuildContext context, Message message) {
    showModalBottomSheet(
      context: context,
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.delete_outline),
              title: const Text('Delete message'),
              onTap: () {
                Navigator.pop(sheetContext);
                _deleteMessage(context, message.id);
              },
            ),
          ],
        ),
      ),
    );
  }

  /// Delete message with confirmation
  Future<void> _deleteMessage(BuildContext context, String messageId) async {
    final confirmed = await showDeleteConfirmationDialog(
      context: context,
      itemType: 'message',
      // No cascade message - messages don't have children
    );

    if (confirmed && context.mounted) {
      context.read<ConversationProvider>().deleteMessage(
            context,
            widget.threadId,
            messageId,
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ConversationProvider>(
      builder: (context, provider, child) {
        // Scroll to bottom when messages change
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (provider.messages.isNotEmpty || provider.isStreaming) {
            _scrollToBottom();
          }
        });

        return Scaffold(
          appBar: AppBar(
            title: Text(provider.thread?.title ?? 'New Conversation'),
          ),
          body: Column(
            children: [
              // Error banner
              if (provider.error != null)
                MaterialBanner(
                  content: SelectableText(provider.error!),
                  backgroundColor: Theme.of(context).colorScheme.errorContainer,
                  actions: [
                    TextButton(
                      onPressed: provider.clearError,
                      child: const Text('Dismiss'),
                    ),
                  ],
                ),

              // Message list
              Expanded(
                child: provider.loading
                    ? const Center(child: CircularProgressIndicator())
                    : _buildMessageList(provider),
              ),

              // Chat input
              ChatInput(
                onSend: provider.sendMessage,
                enabled: !provider.isStreaming,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMessageList(ConversationProvider provider) {
    final messages = provider.messages;

    if (messages.isEmpty && !provider.isStreaming) {
      return SingleChildScrollView(
        child: Column(
          children: [
            // Guidance text
            Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
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
                    'Choose a mode to begin, or just start typing to ask about your requirements.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            // Mode selector below
            ModeSelector(
              onModeSelected: (mode) {
                // Send mode selection as user message
                provider.sendMessage(mode);
              },
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 16),
      itemCount: messages.length + (provider.isStreaming ? 1 : 0),
      itemBuilder: (context, index) {
        // Streaming message at the end
        if (provider.isStreaming && index == messages.length) {
          return StreamingMessage(
            text: provider.streamingText,
            statusMessage: provider.statusMessage,
          );
        }

        final message = messages[index];
        return GestureDetector(
          onLongPress: () => _showMessageOptions(context, message),
          child: MessageBubble(message: message),
        );
      },
    );
  }
}
