/// Conversation screen for AI-powered chat.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/conversation_provider.dart';
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
                'Ask about your requirements and I\'ll help identify edge cases, suggest clarifications, and reference your project documents.',
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

        return MessageBubble(message: messages[index]);
      },
    );
  }
}
