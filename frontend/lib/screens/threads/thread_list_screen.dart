/// Thread list screen showing conversations within a project.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:skeletonizer/skeletonizer.dart';

import '../../models/thread.dart';
import '../../models/thread_sort.dart';
import '../../providers/thread_provider.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/delete_confirmation_dialog.dart';
import '../../widgets/empty_state.dart';
import 'thread_create_dialog.dart';
import 'thread_rename_dialog.dart';

/// Screen showing list of conversation threads in a project
class ThreadListScreen extends StatefulWidget {
  const ThreadListScreen({
    super.key,
    required this.projectId,
  });

  final String projectId;

  @override
  State<ThreadListScreen> createState() => _ThreadListScreenState();
}

class _ThreadListScreenState extends State<ThreadListScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Load threads when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<ThreadProvider>();
      provider.loadThreads(widget.projectId);
      // Restore search query if any
      if (provider.searchQuery.isNotEmpty) {
        _searchController.text = provider.searchQuery;
      }
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _clearSearch() {
    _searchController.clear();
    context.read<ThreadProvider>().clearSearch();
  }

  void _showCreateDialog() {
    showDialog(
      context: context,
      builder: (context) => ThreadCreateDialog(projectId: widget.projectId),
    );
  }

  void _onThreadTap(String threadId) {
    context.go('/projects/${widget.projectId}/threads/$threadId');
  }

  /// Delete thread with confirmation
  Future<void> _deleteThread(BuildContext context, String threadId) async {
    final confirmed = await showDeleteConfirmationDialog(
      context: context,
      itemType: 'thread',
      cascadeMessage: 'This will delete all messages in this thread.',
    );

    if (confirmed && context.mounted) {
      context.read<ThreadProvider>().deleteThread(context, threadId);
    }
  }

  /// Show rename dialog for a thread
  void _showRenameDialog(Thread thread) {
    showDialog(
      context: context,
      builder: (context) => ThreadRenameDialog(
        threadId: thread.id,
        currentTitle: thread.title,
      ),
    );
  }

  /// Create placeholder thread for skeleton loader
  Thread _createPlaceholderThread() {
    return Thread(
      id: 'placeholder',
      projectId: widget.projectId,
      title: 'Loading conversation title',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
      messageCount: 5,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<ThreadProvider>(
        builder: (context, provider, child) {
          // Show error as SnackBar
          if (provider.error != null) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Failed to load conversations. ${provider.error}'),
                    action: SnackBarAction(
                      label: 'Retry',
                      onPressed: () => provider.loadThreads(widget.projectId),
                    ),
                    duration: const Duration(seconds: 5),
                  ),
                );
                provider.clearError();
              }
            });
          }

          // Show empty state when not loading and no threads at all
          if (!provider.isLoading && provider.threads.isEmpty) {
            return EmptyState(
              icon: Icons.chat_bubble_outline,
              title: 'No conversations yet',
              message: 'Start a conversation to discuss requirements with AI assistance.',
              buttonLabel: 'Start Conversation',
              buttonIcon: Icons.add_comment,
              onPressed: _showCreateDialog,
            );
          }

          // Show threads list with search/sort controls
          return Column(
            children: [
              // Search and sort controls
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    // Search bar
                    SearchBar(
                      controller: _searchController,
                      hintText: 'Search conversations...',
                      leading: const Icon(Icons.search),
                      trailing: _searchController.text.isNotEmpty
                          ? [
                              IconButton(
                                icon: const Icon(Icons.clear),
                                onPressed: _clearSearch,
                              ),
                            ]
                          : null,
                      onChanged: (value) {
                        provider.setSearchQuery(value);
                        // Trigger rebuild to show/hide clear button
                        setState(() {});
                      },
                    ),
                    const SizedBox(height: 12),
                    // Sort options
                    SegmentedButton<ThreadSortOption>(
                      segments: ThreadSortOption.values
                          .map((option) => ButtonSegment<ThreadSortOption>(
                                value: option,
                                label: Text(option.label),
                              ))
                          .toList(),
                      selected: {provider.sortOption},
                      onSelectionChanged: (selected) {
                        provider.setSortOption(selected.first);
                      },
                      showSelectedIcon: false,
                    ),
                  ],
                ),
              ),
              // Thread list or empty search results
              Expanded(
                child: _buildContent(provider),
              ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateDialog,
        icon: const Icon(Icons.add_comment),
        label: const Text('New Conversation'),
      ),
    );
  }

  /// Build content based on loading/empty/search state
  Widget _buildContent(ThreadProvider provider) {
    // Show "no matches" message when search has no results
    if (provider.searchQuery.isNotEmpty && provider.filteredThreads.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.search_off,
              size: 64,
              color: Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(
              "No conversations matching '${provider.searchQuery}'",
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            TextButton.icon(
              onPressed: _clearSearch,
              icon: const Icon(Icons.clear),
              label: const Text('Clear search'),
            ),
          ],
        ),
      );
    }

    // Show thread list with skeleton loader
    return RefreshIndicator(
      onRefresh: () => provider.loadThreads(widget.projectId),
      child: Skeletonizer(
        enabled: provider.isLoading,
        child: ListView.builder(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          itemCount: provider.isLoading ? 4 : provider.filteredThreads.length,
          itemBuilder: (context, index) {
            final thread = provider.isLoading
                ? _createPlaceholderThread()
                : provider.filteredThreads[index];
            final title = thread.title ?? 'New Conversation';
            final messageCount = thread.messageCount ?? 0;

            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: ListTile(
                leading: Icon(
                  Icons.chat_bubble_outline,
                  color: Theme.of(context).colorScheme.primary,
                ),
                title: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                subtitle: Row(
                  children: [
                    Icon(
                      Icons.schedule,
                      size: 14,
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      DateFormatter.format(thread.lastActivityAt ?? thread.updatedAt),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                    ),
                    const SizedBox(width: 12),
                    Icon(
                      Icons.message_outlined,
                      size: 14,
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '$messageCount',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                    ),
                  ],
                ),
                trailing: provider.isLoading
                    ? const Icon(Icons.chevron_right)
                    : PopupMenuButton<String>(
                        onSelected: (value) {
                          if (value == 'rename') {
                            _showRenameDialog(thread);
                          } else if (value == 'delete') {
                            _deleteThread(context, thread.id);
                          }
                        },
                        itemBuilder: (context) => [
                          const PopupMenuItem(
                            value: 'rename',
                            child: Row(
                              children: [
                                Icon(Icons.edit_outlined),
                                SizedBox(width: 8),
                                Text('Rename'),
                              ],
                            ),
                          ),
                          const PopupMenuItem(
                            value: 'delete',
                            child: Row(
                              children: [
                                Icon(Icons.delete_outline),
                                SizedBox(width: 8),
                                Text('Delete'),
                              ],
                            ),
                          ),
                        ],
                      ),
                onTap: provider.isLoading ? null : () => _onThreadTap(thread.id),
              ),
            );
          },
        ),
      ),
    );
  }
}
