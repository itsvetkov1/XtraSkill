/// Screen displaying all user's chats across projects.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/thread.dart';
import '../models/thread_sort.dart';
import '../providers/chats_provider.dart';
import '../providers/provider_provider.dart';

/// Screen displaying all user's chats across projects.
class ChatsScreen extends StatefulWidget {
  const ChatsScreen({super.key});

  @override
  State<ChatsScreen> createState() => _ChatsScreenState();
}

class _ChatsScreenState extends State<ChatsScreen> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Load threads on mount if not already loaded
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<ChatsProvider>();
      if (!provider.isInitialized) {
        provider.loadThreads();
      }
      // Restore search query from provider (if any)
      if (provider.searchQuery.isNotEmpty) {
        _searchController.text = provider.searchQuery;
      }
    });
    // Listen for scroll to load more
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      // Near bottom, load more
      context.read<ChatsProvider>().loadMoreThreads();
    }
  }

  Future<void> _createNewChat() async {
    final chatsProvider = context.read<ChatsProvider>();
    final providerProvider = context.read<ProviderProvider>();
    final thread = await chatsProvider.createNewChat(
      modelProvider: providerProvider.selectedProvider,
    );
    if (thread != null && mounted) {
      // Navigate to conversation view
      context.go('/chats/${thread.id}');
    }
  }

  void _clearSearch() {
    _searchController.clear();
    context.read<ChatsProvider>().clearSearch();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<ChatsProvider>(
        builder: (context, provider, child) {
          // Show spinner during initial load (before initialization)
          if (!provider.isInitialized && provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          // Show error state only if we have an error and no data
          if (provider.error != null && provider.threads.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Error: ${provider.error}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.loadThreads(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              // Header with New Chat button and search
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    // Title row with New Chat button
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Chats',
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                        FilledButton.icon(
                          onPressed: _createNewChat,
                          icon: const Icon(Icons.add),
                          label: const Text('New Chat'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    // Search bar
                    SearchBar(
                      hintText: 'Search chats...',
                      controller: _searchController,
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
                        context.read<ChatsProvider>().setSearchQuery(value);
                        // Trigger rebuild to show/hide clear button
                        setState(() {});
                      },
                    ),
                    const SizedBox(height: 8),
                    // Sort selector
                    SegmentedButton<ThreadSortOption>(
                      segments: ThreadSortOption.values
                          .map((option) => ButtonSegment(
                                value: option,
                                label: Text(option.label),
                              ))
                          .toList(),
                      selected: {provider.sortOption},
                      onSelectionChanged: (selected) {
                        context
                            .read<ChatsProvider>()
                            .setSortOption(selected.first);
                      },
                      showSelectedIcon: false,
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              // Thread list
              Expanded(
                child: provider.threads.isEmpty
                    ? _buildEmptyState(provider)
                    : _buildThreadList(provider),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEmptyState(ChatsProvider provider) {
    // Differentiate: search has no results vs no threads at all
    if (provider.searchQuery.isNotEmpty && provider.filteredThreads.isEmpty) {
      // Search returned no results
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
              "No chats matching '${provider.searchQuery}'",
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: _clearSearch,
              child: const Text('Clear search'),
            ),
          ],
        ),
      );
    }

    // Truly no threads
    return Center(
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
            'No chats yet',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Start a new conversation',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _createNewChat,
            icon: const Icon(Icons.add),
            label: const Text('New Chat'),
          ),
        ],
      ),
    );
  }

  Widget _buildThreadList(ChatsProvider provider) {
    final filteredThreads = provider.filteredThreads;

    // Check if filtered list is empty (search has no matches)
    if (filteredThreads.isEmpty) {
      return _buildEmptyState(provider);
    }

    // Only show load more indicator if initialized, has more, not searching, and not loading
    // Don't show load more when actively filtering (user can scroll to load all, then filter)
    final showLoadMore = provider.isInitialized &&
        provider.hasMore &&
        provider.searchQuery.isEmpty;

    return RefreshIndicator(
      onRefresh: () => provider.loadThreads(),
      child: ListView.builder(
        controller: _scrollController,
        itemCount: filteredThreads.length + (showLoadMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= filteredThreads.length) {
            // Show loading indicator at bottom when more pages exist
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: CircularProgressIndicator(),
              ),
            );
          }

          final thread = filteredThreads[index];
          return _ChatListTile(
            thread: thread,
            onTap: () => _navigateToThread(thread),
          );
        },
      ),
    );
  }

  void _navigateToThread(Thread thread) {
    if (thread.hasProject) {
      // Navigate to project thread view
      context.go('/projects/${thread.projectId}/threads/${thread.id}');
    } else {
      // Navigate to global chat view
      context.go('/chats/${thread.id}');
    }
  }
}

/// List tile for a chat thread with project badge.
class _ChatListTile extends StatelessWidget {
  final Thread thread;
  final VoidCallback onTap;

  const _ChatListTile({
    required this.thread,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListTile(
      onTap: onTap,
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.primaryContainer,
        child: Icon(
          Icons.chat_bubble,
          color: theme.colorScheme.onPrimaryContainer,
        ),
      ),
      title: Text(
        thread.title ?? 'New Chat',
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Row(
        children: [
          // Project badge or "No Project"
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: thread.hasProject
                  ? theme.colorScheme.secondaryContainer
                  : theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              thread.projectName ?? 'No Project',
              style: theme.textTheme.labelSmall?.copyWith(
                color: thread.hasProject
                    ? theme.colorScheme.onSecondaryContainer
                    : theme.colorScheme.outline,
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Message count
          Text(
            '${thread.messageCount ?? 0} messages',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ],
      ),
      trailing: Text(
        _formatDate(thread.lastActivityAt ?? thread.updatedAt),
        style: theme.textTheme.bodySmall?.copyWith(
          color: theme.colorScheme.outline,
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m ago';
    if (diff.inDays < 1) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${date.month}/${date.day}';
  }
}
