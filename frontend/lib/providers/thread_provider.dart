/// Thread state management provider.
library;

import 'dart:async';
import 'package:flutter/material.dart';

import '../models/thread.dart';
import '../models/thread_sort.dart';
import '../services/thread_service.dart';

/// Thread provider managing conversation thread state
class ThreadProvider extends ChangeNotifier {
  /// Thread service for API calls
  final ThreadService _threadService;

  /// List of threads for current project
  List<Thread> _threads = [];

  /// Currently selected thread with full message history
  Thread? _selectedThread;

  /// Loading state
  bool _loading = false;

  /// Error message
  String? _error;

  /// Item pending deletion (during undo window)
  Thread? _pendingDelete;

  /// Index where item was before removal (for restoration)
  int _pendingDeleteIndex = 0;

  /// Timer for deferred deletion
  Timer? _deleteTimer;

  /// Search query for filtering threads
  String _searchQuery = '';

  /// Sort option for thread list
  ThreadSortOption _sortOption = ThreadSortOption.newest;

  ThreadProvider({ThreadService? threadService})
      : _threadService = threadService ?? ThreadService();

  /// List of threads
  List<Thread> get threads => _threads;

  /// Currently selected thread
  Thread? get selectedThread => _selectedThread;

  /// Whether threads are being loaded
  bool get loading => _loading;

  /// Whether threads are being loaded (alias for skeleton loader compatibility)
  bool get isLoading => _loading;

  /// Error message if operation failed
  String? get error => _error;

  /// Current search query
  String get searchQuery => _searchQuery;

  /// Current sort option
  ThreadSortOption get sortOption => _sortOption;

  /// Filtered and sorted threads based on current search and sort state
  List<Thread> get filteredThreads {
    var result = _threads.where((thread) {
      if (_searchQuery.isEmpty) return true;
      final title = thread.title?.toLowerCase() ?? '';
      return title.contains(_searchQuery.toLowerCase());
    }).toList();

    switch (_sortOption) {
      case ThreadSortOption.newest:
        result.sort((a, b) => (b.lastActivityAt ?? b.updatedAt)
            .compareTo(a.lastActivityAt ?? a.updatedAt));
      case ThreadSortOption.oldest:
        result.sort((a, b) => (a.lastActivityAt ?? a.updatedAt)
            .compareTo(b.lastActivityAt ?? b.updatedAt));
      case ThreadSortOption.alphabetical:
        result.sort((a, b) =>
            (a.title ?? '').toLowerCase().compareTo((b.title ?? '').toLowerCase()));
    }
    return result;
  }

  /// Load threads for a project
  ///
  /// Fetches threads from API and updates state.
  /// Threads are ordered newest first.
  Future<void> loadThreads(String projectId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _threads = await _threadService.getThreads(projectId);
      _loading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _loading = false;
      notifyListeners();
      rethrow;
    }
  }

  /// Create a new thread in a project
  ///
  /// [projectId] - ID of the project
  /// [title] - Optional title for the thread
  /// [provider] - Optional LLM provider for the thread (e.g., 'anthropic', 'google', 'deepseek')
  ///
  /// Adds created thread to the list and updates state.
  Future<Thread> createThread(String projectId, String? title, {String? provider}) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final thread = await _threadService.createThread(projectId, title, provider: provider);

      // Add new thread to the beginning of list (newest first)
      _threads.insert(0, thread);

      _loading = false;
      notifyListeners();

      return thread;
    } catch (e) {
      _error = e.toString();
      _loading = false;
      notifyListeners();
      rethrow;
    }
  }

  /// Select a thread and load its full details with messages
  ///
  /// [threadId] - ID of the thread to select
  ///
  /// Fetches thread with message history and sets as selected.
  Future<void> selectThread(String threadId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _selectedThread = await _threadService.getThread(threadId);
      _loading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _loading = false;
      notifyListeners();
      rethrow;
    }
  }

  /// Rename a thread
  ///
  /// Updates thread title via API and syncs local state.
  /// Updates both _threads list and _selectedThread if applicable.
  Future<Thread?> renameThread(String threadId, String? title) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final updatedThread = await _threadService.renameThread(threadId, title);

      // Update in threads list
      final index = _threads.indexWhere((t) => t.id == threadId);
      if (index != -1) {
        _threads[index] = Thread(
          id: updatedThread.id,
          projectId: updatedThread.projectId,
          title: updatedThread.title,
          createdAt: updatedThread.createdAt,
          updatedAt: updatedThread.updatedAt,
          messageCount: _threads[index].messageCount, // Preserve local count
          modelProvider: _threads[index].modelProvider, // Preserve provider
        );
      }

      // Update selected thread if it's the same one
      if (_selectedThread?.id == threadId) {
        _selectedThread = updatedThread;
      }

      _error = null;
      return updatedThread;
    } catch (e) {
      _error = e.toString();
      return null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Clear threads list and selected thread
  ///
  /// Used when switching projects or logging out.
  void clearThreads() {
    _threads = [];
    _selectedThread = null;
    _error = null;
    _loading = false;
    _searchQuery = '';
    _sortOption = ThreadSortOption.newest;
    notifyListeners();
  }

  /// Clear error message
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Set search query for filtering threads
  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  /// Set sort option for thread ordering
  void setSortOption(ThreadSortOption option) {
    _sortOption = option;
    notifyListeners();
  }

  /// Clear search query
  void clearSearch() {
    _searchQuery = '';
    notifyListeners();
  }

  /// Delete thread with optimistic UI and undo support
  ///
  /// Immediately removes from list, shows SnackBar with undo.
  /// Actual deletion happens after 10 seconds unless undone.
  Future<void> deleteThread(BuildContext context, String threadId) async {
    // Find thread in list
    final index = _threads.indexWhere((t) => t.id == threadId);
    if (index == -1) return;

    // Cancel any previous pending delete (commit it immediately)
    if (_pendingDelete != null) {
      await _commitPendingDelete();
    }

    // Remove optimistically
    _pendingDelete = _threads[index];
    _pendingDeleteIndex = index;
    _threads.removeAt(index);

    // Clear selected if it was the deleted thread
    if (_selectedThread?.id == threadId) {
      _selectedThread = null;
    }

    notifyListeners();

    // Show undo SnackBar
    if (context.mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Thread deleted'),
          duration: const Duration(seconds: 10),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: () => _undoDelete(),
          ),
        ),
      );
    }

    // Start deletion timer
    _deleteTimer?.cancel();
    _deleteTimer = Timer(const Duration(seconds: 10), () {
      _commitPendingDelete();
    });
  }

  void _undoDelete() {
    _deleteTimer?.cancel();
    if (_pendingDelete != null) {
      // Restore at original position (or start if index invalid)
      final insertIndex = _pendingDeleteIndex.clamp(0, _threads.length);
      _threads.insert(insertIndex, _pendingDelete!);
      _pendingDelete = null;
      notifyListeners();
    }
  }

  Future<void> _commitPendingDelete() async {
    if (_pendingDelete == null) return;

    final threadToDelete = _pendingDelete!;
    final originalIndex = _pendingDeleteIndex;
    _pendingDelete = null;

    try {
      await _threadService.deleteThread(threadToDelete.id);
    } catch (e) {
      // Rollback: restore to list
      final insertIndex = originalIndex.clamp(0, _threads.length);
      _threads.insert(insertIndex, threadToDelete);
      _error = 'Failed to delete thread: $e';
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _deleteTimer?.cancel();
    super.dispose();
  }
}
