/// Conversation screen for AI-powered chat.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/constants.dart';
import '../../models/message.dart';
import '../../models/project.dart';
import '../../providers/budget_provider.dart';
import '../../providers/conversation_provider.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../../widgets/mode_change_dialog.dart';
import '../../widgets/mode_selector.dart';
import '../../widgets/project_picker_dialog.dart';
import '../../widgets/resource_not_found_state.dart';
import '../threads/thread_rename_dialog.dart';
import 'widgets/add_to_project_button.dart';
import 'widgets/artifact_card.dart';
import 'widgets/artifact_type_picker.dart';
import 'widgets/chat_input.dart';
import 'widgets/error_state_message.dart';
import 'widgets/generating_indicator.dart';
import 'widgets/generation_error_state.dart';
import 'widgets/message_bubble.dart';
import 'widgets/budget_warning_banner.dart';
import 'widgets/mode_badge.dart';
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
    // Load thread and refresh budget on mount
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ConversationProvider>().loadThread(widget.threadId);
      context.read<BudgetProvider>().refresh();
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

  /// Show mode change dialog and update thread mode
  Future<void> _showModeChangeDialog() async {
    final provider = context.read<ConversationProvider>();
    final currentMode = provider.thread?.conversationMode;

    final selectedMode = await ModeChangeDialog.show(
      context,
      currentMode: currentMode,
    );

    if (selectedMode != null && selectedMode != currentMode && mounted) {
      final success = await provider.updateMode(selectedMode);

      if (!success && mounted) {
        // Show error snackbar
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(provider.error ?? 'Failed to change mode'),
            action: SnackBarAction(
              label: 'Retry',
              onPressed: _showModeChangeDialog,
            ),
          ),
        );
      }
      // Success: UI updates in-place via loadThread() (no snackbar)
    }
  }

  /// Show thread info bottom sheet
  void _showThreadInfo() {
    final thread = context.read<ConversationProvider>().thread;
    if (thread == null) return;

    final providerConfig = ProviderConfigs.getConfig(thread.modelProvider);

    showModalBottomSheet(
      context: context,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Text(
                'Thread Info',
                style: Theme.of(sheetContext).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 16),
              // Title
              ListTile(
                leading: const Icon(Icons.chat_bubble_outline),
                title: const Text('Title'),
                subtitle: Text(thread.title ?? 'New Conversation'),
                dense: true,
              ),
              // Provider
              ListTile(
                leading: Icon(providerConfig.icon, color: providerConfig.color),
                title: const Text('Provider'),
                subtitle: Row(
                  children: [
                    Text(providerConfig.displayName),
                    if (providerConfig.isExperimental) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Theme.of(sheetContext).colorScheme.secondaryContainer,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'EXPERIMENTAL',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: Theme.of(sheetContext).colorScheme.onSecondaryContainer,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                dense: true,
              ),
              // Model name (only for providers with modelName)
              if (providerConfig.modelName != null)
                ListTile(
                  leading: const Icon(Icons.memory),
                  title: const Text('Model'),
                  subtitle: Text(providerConfig.modelName!),
                  dense: true,
                ),
              // Mode
              ListTile(
                leading: Icon(thread.modeIcon),
                title: const Text('Mode'),
                subtitle: Text(thread.modeDisplayName),
                dense: true,
              ),
              // Created date
              ListTile(
                leading: const Icon(Icons.calendar_today),
                title: const Text('Created'),
                subtitle: Text(_formatDate(thread.createdAt)),
                dense: true,
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }

  /// Format date for display in thread info
  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} '
           '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }

  /// Show artifact type picker and handle selection
  Future<void> _showArtifactTypePicker() async {
    final selection = await ArtifactTypePicker.show(context);

    if (selection != null && mounted) {
      final provider = context.read<ConversationProvider>();

      // Build prompt and artifact type label
      String prompt;
      String artifactType;

      if (selection.isCustom) {
        prompt = selection.customPrompt!;
        artifactType = 'Artifact'; // Generic label for custom
      } else {
        prompt = 'Generate ${selection.presetType!.displayName} from this conversation.';
        artifactType = selection.presetType!.displayName;
      }

      // Call generateArtifact (NOT sendMessage) for silent generation
      provider.generateArtifact(prompt, artifactType);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer2<ConversationProvider, BudgetProvider>(
      builder: (context, provider, budgetProvider, child) {
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

        // Determine if chat input should be enabled
        // Disabled when streaming, generating artifact, OR when budget is exhausted
        final inputEnabled = !provider.isStreaming &&
            !provider.isGeneratingArtifact &&
            budgetProvider.status != BudgetStatus.exhausted;

        return Scaffold(
          appBar: AppBar(
            title: Text(provider.thread?.title ?? 'New Conversation'),
            actions: [
              // Mode badge (shows current mode, tap to change)
              if (provider.thread != null)
                ModeBadge(
                  mode: provider.thread!.conversationMode,
                  onTap: _showModeChangeDialog,
                ),
              IconButton(
                icon: const Icon(Icons.info_outline),
                tooltip: 'Thread info',
                onPressed: provider.thread != null ? _showThreadInfo : null,
              ),
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
              // Budget warning banner (above error banner - budget status is more important)
              BudgetWarningBanner(
                status: budgetProvider.status,
                percentage: budgetProvider.percentage,
              ),

              // Error banner with connection-specific message
              // Hide for generation errors - those show in GenerationErrorState widget
              if (provider.error != null && !provider.lastOperationWasGeneration)
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

              // Chat input - disabled when streaming, generating, or budget exhausted
              ChatInput(
                onSend: (message) {
                  provider.sendMessage(message);
                  // Refresh budget after sending message
                  budgetProvider.refresh();
                },
                onGenerateArtifact: _showArtifactTypePicker,
                enabled: inputEnabled,
                isGenerating: provider.isGeneratingArtifact,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMessageList(ConversationProvider provider) {
    final messages = provider.messages;

    if (messages.isEmpty && !provider.isStreaming && !provider.isGeneratingArtifact) {
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
              onModeSelected: (mode) async {
                // Convert display name to mode value and update thread
                final modeValue = mode.contains('Meeting') ? 'meeting' : 'document_refinement';
                await provider.updateMode(modeValue);
                // Send mode selection as user message
                provider.sendMessage(mode);
              },
            ),
          ],
        ),
      );
    }

    // Calculate extra items for streaming, error, and generation states
    final hasStreamingItem = provider.isStreaming;
    final hasPartialErrorItem = provider.hasPartialContent && !provider.isStreaming;
    final hasGeneratingItem = provider.isGeneratingArtifact;
    final hasGenerationError = provider.canRetryGeneration;

    final artifactCount = provider.artifacts.length;
    final extraItemCount = (hasStreamingItem ? 1 : 0) +
        (hasPartialErrorItem ? 1 : 0) +
        (hasGeneratingItem ? 1 : 0) +
        (hasGenerationError ? 1 : 0);

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 16),
      itemCount: messages.length + artifactCount + extraItemCount,
      itemBuilder: (context, index) {
        // Regular messages
        if (index < messages.length) {
          final message = messages[index];
          return GestureDetector(
            onLongPress: () => _showMessageOptions(context, message),
            child: MessageBubble(
              message: message,
              projectId: widget.projectId, // Pass for document navigation (SRC-03)
            ),
          );
        }

        // Artifacts (after messages)
        if (index < messages.length + artifactCount) {
          final artifactIndex = index - messages.length;
          final artifact = provider.artifacts[artifactIndex];
          return ArtifactCard(
            artifact: artifact,
            threadId: widget.threadId,
          );
        }

        // Special states (after artifacts)
        final specialIndex = index - messages.length - artifactCount;
        int currentSpecialItem = 0;

        // Generating indicator
        if (hasGeneratingItem) {
          if (specialIndex == currentSpecialItem) {
            return GeneratingIndicator(
              artifactType: provider.generatingArtifactType ?? 'Artifact',
              onCancel: () {
                provider.cancelGeneration();
              },
            );
          }
          currentSpecialItem++;
        }

        // Generation error state
        if (hasGenerationError) {
          if (specialIndex == currentSpecialItem) {
            return GenerationErrorState(
              onRetry: provider.retryLastGeneration,
              onDismiss: provider.clearError,
            );
          }
          currentSpecialItem++;
        }

        // Streaming message (existing)
        if (hasStreamingItem) {
          if (specialIndex == currentSpecialItem) {
            return StreamingMessage(
              text: provider.streamingText,
              statusMessage: provider.statusMessage,
            );
          }
          currentSpecialItem++;
        }

        // Error state partial message (existing)
        if (hasPartialErrorItem) {
          if (specialIndex == currentSpecialItem) {
            return ErrorStateMessage(
              partialText: provider.streamingText,
            );
          }
          currentSpecialItem++;
        }

        return const SizedBox.shrink();
      },
    );
  }
}
