/// Screen displaying Assistant-type threads only.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../models/thread.dart';
import '../../services/thread_service.dart';
import '../../widgets/empty_state.dart';
import 'assistant_create_dialog.dart';

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

  // Delete with undo support
  Thread? _pendingDelete;
  int _pendingDeleteIndex = 0;
  Timer? _deleteTimer;

  @override
  void initState() {
    super.initState();
    _loadThreads();
  }

  @override
  void dispose() {
    _deleteTimer?.cancel();
    super.dispose();
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

  Future<void> _deleteThread(Thread thread) async {
    final index = _threads.indexWhere((t) => t.id == thread.id);
    if (index == -1) return;

    // Commit any previous pending delete immediately
    if (_pendingDelete != null) {
      await _commitPendingDelete();
    }

    // Optimistically remove from list
    setState(() {
      _pendingDelete = _threads[index];
      _pendingDeleteIndex = index;
      _threads.removeAt(index);
    });

    if (mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Thread deleted'),
          duration: const Duration(seconds: 10),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: _undoDelete,
          ),
        ),
      );
    }

    _deleteTimer?.cancel();
    _deleteTimer = Timer(const Duration(seconds: 10), () {
      _commitPendingDelete();
    });
  }

  void _undoDelete() {
    _deleteTimer?.cancel();
    if (_pendingDelete != null) {
      setState(() {
        final insertIndex = _pendingDeleteIndex.clamp(0, _threads.length);
        _threads.insert(insertIndex, _pendingDelete!);
        _pendingDelete = null;
      });
    }
  }

  Future<void> _commitPendingDelete() async {
    if (_pendingDelete == null) return;
    final threadToDelete = _pendingDelete!;
    final originalIndex = _pendingDeleteIndex;
    _pendingDelete = null;

    try {
      final threadService = ThreadService();
      await threadService.deleteThread(threadToDelete.id);
    } catch (e) {
      // Rollback on failure
      if (mounted) {
        setState(() {
          final insertIndex = originalIndex.clamp(0, _threads.length);
          _threads.insert(insertIndex, threadToDelete);
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to delete thread: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  Future<void> _showCreateDialog() async {
    final thread = await AssistantCreateDialog.show(context);
    if (thread != null && mounted) {
      // Add to local list (optimistic)
      setState(() {
        _threads.insert(0, thread);
      });
      // Navigate to conversation screen
      context.go('/assistant/${thread.id}');
    }
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
