/// Screen displaying all user's chats across projects.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/thread.dart';
import '../providers/chats_provider.dart';
import '../providers/provider_provider.dart';

/// Screen displaying all user's chats across projects.
class ChatsScreen extends StatefulWidget {
  const ChatsScreen({super.key});

  @override
  State<ChatsScreen> createState() => _ChatsScreenState();
}

class _ChatsScreenState extends State<ChatsScreen> {
  @override
  void initState() {
    super.initState();
    // Load threads on mount
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ChatsProvider>().loadThreads();
    });
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<ChatsProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.threads.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

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
              // Header with New Chat button
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
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
              ),
              const Divider(height: 1),
              // Thread list
              Expanded(
                child: provider.threads.isEmpty
                    ? _buildEmptyState()
                    : _buildThreadList(provider),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
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
    return RefreshIndicator(
      onRefresh: () => provider.loadThreads(),
      child: ListView.builder(
        itemCount: provider.threads.length + (provider.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= provider.threads.length) {
            // Load more trigger
            provider.loadMoreThreads();
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: CircularProgressIndicator(),
              ),
            );
          }

          final thread = provider.threads[index];
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
