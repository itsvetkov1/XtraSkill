/// Conversation screen for AI-powered chat.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/message.dart';
import '../../models/project.dart';
import '../../providers/conversation_provider.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../../widgets/mode_selector.dart';
import '../../widgets/project_picker_dialog.dart';
import '../../widgets/resource_not_found_state.dart';
import '../threads/thread_rename_dialog.dart';
import 'widgets/add_to_project_button.dart';
import 'widgets/chat_input.dart';
import 'widgets/error_state_message.dart';
import 'widgets/message_bubble.dart';
import 'widgets/provider_indicator.dart';
import 'widgets/streaming_message.dart';

/// Main conversation screen with message list and input
class ConversationScreen extends StatefulWidget {
  /// Project ID this thread belongs to (null for project-less threads)
  final String? projectId;

  /// Thread ID to display
  final String threadId;

  const ConversationScreen({
    super.key,
    this.projectId,
    required this.threadId,
  });

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

  /// Show rename dialog for current thread
  void _showRenameDialog() {
    final provider = context.read<ConversationProvider>();
    final thread = provider.thread;
    if (thread == null) return;

    showDialog<bool>(
      context: context,
      builder: (dialogContext) => ThreadRenameDialog(
        threadId: thread.id,
        currentTitle: thread.title,
      ),
    ).then((renamed) {
      // Reload thread to get updated title
      if (renamed == true && mounted) {
        provider.loadThread(widget.threadId);
      }
    });
  }

  /// Show project picker and handle association
  Future<void> _showAddToProjectDialog() async {
    final selectedProject = await showDialog<Project>(
      context: context,
      builder: (dialogContext) => const ProjectPickerDialog(),
    );

    if (selectedProject != null && mounted) {
      final provider = context.read<ConversationProvider>();
      final success = await provider.associateWithProject(selectedProject.id);

      if (!success && mounted) {
        // Show error snackbar with retry
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(provider.error ?? 'Failed to add to project'),
            action: SnackBarAction(
              label: 'Retry',
              onPressed: _showAddToProjectDialog,
            ),
          ),
        );
      }
      // Success: header updates in-place via loadThread() (no snackbar per CONTEXT.md)
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

        // Show loading indicator (full screen, not in scaffold)
        if (provider.loading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        // Show not-found state (ERR-03) - full screen, not in scaffold
        if (provider.isNotFound) {
          return Scaffold(
            appBar: AppBar(title: const Text('Thread')),
            body: ResourceNotFoundState(
              icon: Icons.speaker_notes_off_outlined,
              title: 'Thread not found',
              message:
                  'This conversation may have been deleted or you may not have access to it.',
              buttonLabel: widget.projectId != null ? 'Back to Project' : 'Back to Chats',
              onPressed: () {
                if (widget.projectId != null) {
                  context.go('/projects/${widget.projectId}');
                } else {
                  context.go('/chats');
                }
              },
            ),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: Text(provider.thread?.title ?? 'New Conversation'),
            actions: [
              IconButton(
                icon: const Icon(Icons.edit_outlined),
                tooltip: 'Rename conversation',
                onPressed: provider.thread != null ? _showRenameDialog : null,
              ),
              // Options menu with "Add to Project" for project-less threads
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert),
                tooltip: 'More options',
                onSelected: (value) {
                  if (value == 'add_to_project') {
                    _showAddToProjectDialog();
                  }
                },
                itemBuilder: (context) => [
                  // Only show for project-less threads
                  if (provider.thread != null && !provider.thread!.hasProject)
                    const PopupMenuItem<String>(
                      value: 'add_to_project',
                      child: Row(
                        children: [
                          Icon(Icons.folder_open_outlined, size: 20),
                          SizedBox(width: 12),
                          Text('Add to Project'),
                        ],
                      ),
                    ),
                ],
              ),
            ],
          ),
          body: Column(
            children: [
              // Error banner with connection-specific message
              if (provider.error != null)
                MaterialBanner(
                  content: Text(
                    provider.hasPartialContent
                        ? 'Connection lost - response incomplete'
                        : provider.error!,
                  ),
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
                child: _buildMessageList(provider),
              ),

              // Toolbar row: Provider indicator + Add to Project button
              Row(
                children: [
                  // Provider indicator
                  ProviderIndicator(
                    provider: provider.thread?.modelProvider,
                  ),
                  const Spacer(),
                  // Add to Project button (only for project-less threads)
                  if (provider.thread != null && !provider.thread!.hasProject)
                    AddToProjectButton(
                      onPressed: _showAddToProjectDialog,
                    ),
                ],
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

    // Calculate extra item count for streaming or error state messages
    final hasExtraItem = provider.isStreaming ||
        (provider.hasPartialContent && !provider.isStreaming);

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 16),
      itemCount: messages.length + (hasExtraItem ? 1 : 0),
      itemBuilder: (context, index) {
        // Error state partial message at the end (when not streaming)
        if (provider.hasPartialContent &&
            !provider.isStreaming &&
            index == messages.length) {
          return ErrorStateMessage(
            partialText: provider.streamingText,
          );
        }

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
