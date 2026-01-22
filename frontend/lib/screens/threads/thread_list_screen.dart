/// Thread list screen showing conversations within a project.
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../providers/thread_provider.dart';
import 'thread_create_dialog.dart';

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
  @override
  void initState() {
    super.initState();
    // Load threads when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ThreadProvider>().loadThreads(widget.projectId);
    });
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      return 'Today ${DateFormat.jm().format(date)}';
    } else if (difference.inDays == 1) {
      return 'Yesterday';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} days ago';
    } else {
      return DateFormat.yMMMd().format(date);
    }
  }

  void _showCreateDialog() {
    showDialog(
      context: context,
      builder: (context) => ThreadCreateDialog(projectId: widget.projectId),
    );
  }

  void _onThreadTap(String threadId) {
    // Phase 3: Navigate to thread detail/conversation screen
    // For now, show placeholder
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Thread conversation view coming in Phase 3'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<ThreadProvider>(
        builder: (context, provider, child) {
          // Show loading indicator
          if (provider.loading && provider.threads.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          // Show error message
          if (provider.error != null && provider.threads.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.error_outline,
                    size: 48,
                    color: Theme.of(context).colorScheme.error,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading conversations',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(provider.error!),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.loadThreads(widget.projectId),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          // Show empty state
          if (provider.threads.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.chat_bubble_outline,
                    size: 64,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No conversations yet',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const Text('Start a conversation to discuss requirements'),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: _showCreateDialog,
                    icon: const Icon(Icons.add_comment),
                    label: const Text('New Conversation'),
                  ),
                ],
              ),
            );
          }

          // Show threads list
          return RefreshIndicator(
            onRefresh: () => provider.loadThreads(widget.projectId),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: provider.threads.length,
              itemBuilder: (context, index) {
                final thread = provider.threads[index];
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
                    subtitle: Text(
                      'Created ${_formatDate(thread.createdAt)} • $messageCount messages',
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _onThreadTap(thread.id),
                  ),
                );
              },
            ),
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
}
