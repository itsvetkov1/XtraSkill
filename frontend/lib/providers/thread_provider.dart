/// Thread state management provider.
library;

import 'package:flutter/foundation.dart';

import '../models/thread.dart';
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

  ThreadProvider({ThreadService? threadService})
      : _threadService = threadService ?? ThreadService();

  /// List of threads
  List<Thread> get threads => _threads;

  /// Currently selected thread
  Thread? get selectedThread => _selectedThread;

  /// Whether threads are being loaded
  bool get loading => _loading;

  /// Error message if operation failed
  String? get error => _error;

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
  ///
  /// Adds created thread to the list and updates state.
  Future<Thread> createThread(String projectId, String? title) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final thread = await _threadService.createThread(projectId, title);

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

  /// Clear threads list and selected thread
  ///
  /// Used when switching projects or logging out.
  void clearThreads() {
    _threads = [];
    _selectedThread = null;
    _error = null;
    _loading = false;
    notifyListeners();
  }

  /// Clear error message
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
