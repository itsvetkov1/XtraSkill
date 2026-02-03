/// Conversation state management with streaming support.
library;

import 'dart:async';
import 'package:flutter/material.dart';

import '../models/message.dart';
import '../models/thread.dart';
import '../services/ai_service.dart';
import '../services/thread_service.dart';

/// Conversation provider managing chat state and streaming
class ConversationProvider extends ChangeNotifier {
  /// AI service for streaming chat
  final AIService _aiService;

  /// Thread service for loading thread details
  final ThreadService _threadService;

  /// Current thread being viewed
  Thread? _thread;

  /// Messages in the current conversation
  List<Message> _messages = [];

  /// Text accumulated during streaming
  String _streamingText = '';

  /// Status message (e.g., "Searching documents...")
  String? _statusMessage;

  /// Whether AI is currently streaming a response
  bool _isStreaming = false;

  /// Loading state for initial thread load
  bool _loading = false;

  /// Error message if something failed
  String? _error;

  /// Whether the thread was not found (404)
  bool _isNotFound = false;

  /// Message pending deletion (during undo window)
  Message? _pendingDelete;

  /// Index where message was before removal (for restoration)
  int _pendingDeleteIndex = 0;

  /// Thread ID for pending delete (needed for backend call)
  String? _pendingDeleteThreadId;

  /// Timer for deferred deletion
  Timer? _deleteTimer;

  /// Content of the last message that failed to send
  String? _lastFailedMessage;

  /// Whether there is partial content from an interrupted stream
  bool _hasPartialContent = false;

  ConversationProvider({
    AIService? aiService,
    ThreadService? threadService,
  })  : _aiService = aiService ?? AIService(),
        _threadService = threadService ?? ThreadService();

  /// Current thread
  Thread? get thread => _thread;

  /// Messages in conversation
  List<Message> get messages => _messages;

  /// Text being streamed from AI
  String get streamingText => _streamingText;

  /// Status message during tool execution
  String? get statusMessage => _statusMessage;

  /// Whether AI is streaming
  bool get isStreaming => _isStreaming;

  /// Whether loading thread
  bool get loading => _loading;

  /// Error message
  String? get error => _error;

  /// Not-found state - true when API returned 404
  bool get isNotFound => _isNotFound;

  /// Whether retry is available
  bool get canRetry => _lastFailedMessage != null && _error != null;

  /// Whether there is partial content from an interrupted stream
  bool get hasPartialContent => _hasPartialContent;

  /// Load a thread with its message history
  Future<void> loadThread(String threadId) async {
    _loading = true;
    _error = null;
    _isNotFound = false; // Reset on new load
    notifyListeners();

    try {
      _thread = await _threadService.getThread(threadId);
      _messages = _thread?.messages ?? [];
      _loading = false;
      notifyListeners();
    } catch (e) {
      final errorMessage = e.toString();
      // Check if it's a 404 "not found" error (from thread_service.dart)
      if (errorMessage.contains('not found') ||
          errorMessage.contains('404')) {
        _isNotFound = true;
        _error = null; // Not a "real" error, just not found
      } else {
        _error = errorMessage;
        _isNotFound = false;
      }
      _loading = false;
      notifyListeners();
      // Remove rethrow - let screen handle the not-found state
    }
  }

  /// Send a message and stream the AI response
  Future<void> sendMessage(String content) async {
    if (_thread == null || _isStreaming) return;

    _error = null;
    _lastFailedMessage = content;

    // Add user message optimistically (will be confirmed by refresh)
    final userMessage = Message(
      id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
      role: MessageRole.user,
      content: content,
      createdAt: DateTime.now(),
    );
    _messages.add(userMessage);

    // Start streaming
    _isStreaming = true;
    _streamingText = '';
    _statusMessage = null;
    notifyListeners();

    try {
      await for (final event in _aiService.streamChat(_thread!.id, content)) {
        if (event is TextDeltaEvent) {
          _streamingText += event.text;
          notifyListeners();
        } else if (event is ToolExecutingEvent) {
          _statusMessage = event.status;
          notifyListeners();
        } else if (event is MessageCompleteEvent) {
          // Add assistant message to list
          final assistantMessage = Message(
            id: 'temp-assistant-${DateTime.now().millisecondsSinceEpoch}',
            role: MessageRole.assistant,
            content: _streamingText.isNotEmpty ? _streamingText : event.content,
            createdAt: DateTime.now(),
          );
          _messages.add(assistantMessage);

          // Clear streaming state and retry state on success
          _isStreaming = false;
          _streamingText = '';
          _statusMessage = null;
          _lastFailedMessage = null;
          notifyListeners();

          // Optionally refresh thread to get server-confirmed messages
          // await loadThread(_thread!.id);
        } else if (event is ErrorEvent) {
          _error = event.message;
          _isStreaming = false;
          _hasPartialContent = _streamingText.isNotEmpty;
          // DO NOT clear _streamingText - preserve partial content per PITFALL-01
          _statusMessage = null;
          notifyListeners();
        }
      }
    } catch (e) {
      _error = e.toString();
      _isStreaming = false;
      _hasPartialContent = _streamingText.isNotEmpty;
      // DO NOT clear _streamingText - preserve partial content per PITFALL-01
      _statusMessage = null;
      notifyListeners();
    }
  }

  /// Clear current conversation state
  void clearConversation() {
    _thread = null;
    _messages = [];
    _streamingText = '';
    _statusMessage = null;
    _isStreaming = false;
    _error = null;
    _isNotFound = false;
    _loading = false;
    _hasPartialContent = false;
    notifyListeners();
  }

  /// Clear error message and failed message state
  void clearError() {
    _error = null;
    _isNotFound = false;
    _lastFailedMessage = null; // Dismiss means "I don't want to retry"
    _hasPartialContent = false;
    _streamingText = ''; // Clear partial content on dismiss
    notifyListeners();
  }

  /// Retry the last failed message
  void retryLastMessage() {
    if (_lastFailedMessage == null) return;

    final content = _lastFailedMessage!;
    _lastFailedMessage = null;
    _error = null;
    _hasPartialContent = false;
    _streamingText = ''; // Clear partial content on retry

    // Remove the optimistic user message that was added on first attempt
    // to avoid duplicates when sendMessage adds it again
    if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
      _messages.removeLast();
    }

    sendMessage(content);
  }

  /// Delete message with optimistic UI and undo support
  ///
  /// Immediately removes from list, shows SnackBar with undo.
  /// Actual deletion happens after 10 seconds unless undone.
  Future<void> deleteMessage(
    BuildContext context,
    String threadId,
    String messageId,
  ) async {
    // Find message in list
    final index = _messages.indexWhere((m) => m.id == messageId);
    if (index == -1) return;

    // Cancel any previous pending delete (commit it immediately)
    if (_pendingDelete != null) {
      await _commitPendingDelete();
    }

    // Remove optimistically
    _pendingDelete = _messages[index];
    _pendingDeleteIndex = index;
    _pendingDeleteThreadId = threadId;
    _messages.removeAt(index);

    notifyListeners();

    // Show undo SnackBar
    if (context.mounted) {
      ScaffoldMessenger.of(context).clearSnackBars();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Message deleted'),
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
      // Restore at original position (or end if index invalid)
      final insertIndex = _pendingDeleteIndex.clamp(0, _messages.length);
      _messages.insert(insertIndex, _pendingDelete!);
      _pendingDelete = null;
      _pendingDeleteThreadId = null;
      notifyListeners();
    }
  }

  Future<void> _commitPendingDelete() async {
    if (_pendingDelete == null || _pendingDeleteThreadId == null) return;

    final messageToDelete = _pendingDelete!;
    final threadId = _pendingDeleteThreadId!;
    final originalIndex = _pendingDeleteIndex;
    _pendingDelete = null;
    _pendingDeleteThreadId = null;

    try {
      await _aiService.deleteMessage(threadId, messageToDelete.id);
    } catch (e) {
      // Rollback: restore to list
      final insertIndex = originalIndex.clamp(0, _messages.length);
      _messages.insert(insertIndex, messageToDelete);
      _error = 'Failed to delete message: $e';
      notifyListeners();
    }
  }

  /// Associate current thread with a project
  ///
  /// Returns true on success, false on failure.
  /// On success, reloads thread to update UI state.
  /// On failure, sets error message.
  Future<bool> associateWithProject(String projectId) async {
    if (_thread == null) return false;

    try {
      await _threadService.associateWithProject(_thread!.id, projectId);
      // Reload thread to get updated project info
      await loadThread(_thread!.id);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Update conversation mode for current thread
  ///
  /// Returns true on success, false on failure.
  /// On success, reloads thread to update UI state.
  /// On failure, sets error message.
  Future<bool> updateMode(String mode) async {
    if (_thread == null) return false;

    try {
      await _threadService.updateThreadMode(_thread!.id, mode);
      // Reload thread to get updated mode
      await loadThread(_thread!.id);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  @override
  void dispose() {
    _deleteTimer?.cancel();
    super.dispose();
  }
}
