/// Global chats state management provider.
library;

import 'package:flutter/foundation.dart';

import '../models/thread.dart';
import '../services/thread_service.dart';

/// Provider for global chats state management.
/// Manages all user threads across projects.
class ChatsProvider extends ChangeNotifier {
  final ThreadService _threadService;

  List<Thread> _threads = [];
  bool _isLoading = false;
  bool _isInitialized = false;
  String? _error;
  int _total = 0;
  int _currentPage = 1;
  bool _hasMore = false; // Start false until first load confirms more pages

  ChatsProvider({ThreadService? threadService})
      : _threadService = threadService ?? ThreadService();

  // Getters
  List<Thread> get threads => _threads;
  bool get isLoading => _isLoading;
  bool get isInitialized => _isInitialized;
  String? get error => _error;
  int get total => _total;
  bool get hasMore => _hasMore;

  /// Load threads (first page or refresh)
  Future<void> loadThreads() async {
    // Prevent duplicate loads
    if (_isLoading) return;

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _threadService.getGlobalThreads(page: 1);
      _threads = result.threads;
      _total = result.total;
      _currentPage = 1;
      _hasMore = result.hasMore;
      _isInitialized = true;
    } catch (e) {
      _error = e.toString();
      _hasMore = false; // Don't show load more on error
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Load more threads (pagination)
  Future<void> loadMoreThreads() async {
    // Only load more if initialized, not already loading, and has more pages
    if (!_isInitialized || _isLoading || !_hasMore) return;

    _isLoading = true;
    notifyListeners();

    try {
      final result =
          await _threadService.getGlobalThreads(page: _currentPage + 1);
      _threads.addAll(result.threads);
      _currentPage++;
      _hasMore = result.hasMore;
    } catch (e) {
      _error = e.toString();
      _hasMore = false; // Stop trying to load more on error
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Create a new project-less thread
  Future<Thread?> createNewChat({String? modelProvider}) async {
    try {
      final thread = await _threadService.createGlobalThread(
        title: null, // Will be "New Chat", auto-generates later
        projectId: null, // Project-less
        modelProvider: modelProvider,
      );
      // Add to beginning of list
      _threads.insert(0, thread);
      _total++;
      notifyListeners();
      return thread;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }

  /// Clear error state
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
