/// Screen displaying Assistant-type threads only.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../models/thread.dart';
import '../../services/thread_service.dart';
import '../../providers/thread_provider.dart';
import '../../widgets/empty_state.dart';

/// Screen displaying Assistant-type threads with create/delete functionality.
///
/// Shows only threads with thread_type=assistant (filtered by backend API).
/// Provides a minimal, focused interface for Assistant conversations.
class AssistantListScreen extends StatefulWidget {
  const AssistantListScreen({super.key});

  @override
  State<AssistantListScreen> createState() => _AssistantListScreenState();
}

class _AssistantListScreenState extends State<AssistantListScreen> {
  final ThreadService _threadService = ThreadService();
  List<Thread> _threads = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadThreads();
  }

  Future<void> _loadThreads() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final threads = await _threadService.getAssistantThreads();
      if (mounted) {
        setState(() {
          _threads = threads;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  /// Public method for refreshing threads (used after thread creation in Plan 63-02)
  Future<void> refreshThreads() async {
    await _loadThreads();
  }

  void _deleteThread(Thread thread) {
    final threadProvider = context.read<ThreadProvider>();
    threadProvider.deleteThread(context, thread.id);
    // Remove from local list optimistically
    setState(() {
      _threads.removeWhere((t) => t.id == thread.id);
    });
  }

  void _showCreateDialog() {
    // Wired in Plan 63-02
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // Header row: "Assistant" title + "New Thread" button
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Assistant',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                FilledButton.icon(
                  onPressed: _showCreateDialog,
                  icon: const Icon(Icons.add),
                  label: const Text('New Thread'),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          // Thread list or empty state
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? _buildErrorState()
                    : _threads.isEmpty
                        ? _buildEmptyState()
                        : _buildThreadList(),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('Error: $_error'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadThreads,
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return EmptyState(
      icon: Icons.add_circle_outline,
      title: 'No conversations yet',
      message: 'Start your first conversation with the Assistant.',
      buttonLabel: 'New Conversation',
      buttonIcon: Icons.add,
      onPressed: _showCreateDialog,
    );
  }

  Widget _buildThreadList() {
    return RefreshIndicator(
      onRefresh: _loadThreads,
      child: ListView.builder(
        itemCount: _threads.length,
        itemBuilder: (context, index) {
          final thread = _threads[index];
          return _ThreadListTile(
            thread: thread,
            onTap: () => context.go('/assistant/${thread.id}'),
            onDelete: () => _deleteThread(thread),
          );
        },
      ),
    );
  }
}

/// List tile for an Assistant thread with timestamp and delete button.
class _ThreadListTile extends StatelessWidget {
  final Thread thread;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _ThreadListTile({
    required this.thread,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      onTap: onTap,
      title: Text(
        thread.title ?? 'Untitled',
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(_formatTimestamp(thread.lastActivityAt ?? thread.updatedAt)),
      trailing: IconButton(
        icon: const Icon(Icons.delete_outline, size: 20),
        tooltip: 'Delete',
        onPressed: onDelete,
      ),
    );
  }

  String _formatTimestamp(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m ago';
    if (diff.inDays < 1) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${date.month}/${date.day}';
  }
}
