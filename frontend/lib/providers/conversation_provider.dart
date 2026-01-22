/// Conversation state management with streaming support.
library;

import 'package:flutter/foundation.dart';

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

  /// Load a thread with its message history
  Future<void> loadThread(String threadId) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      _thread = await _threadService.getThread(threadId);
      _messages = _thread?.messages ?? [];
      _loading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _loading = false;
      notifyListeners();
      rethrow;
    }
  }

  /// Send a message and stream the AI response
  Future<void> sendMessage(String content) async {
    if (_thread == null || _isStreaming) return;

    _error = null;

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

          // Clear streaming state
          _isStreaming = false;
          _streamingText = '';
          _statusMessage = null;
          notifyListeners();

          // Optionally refresh thread to get server-confirmed messages
          // await loadThread(_thread!.id);
        } else if (event is ErrorEvent) {
          _error = event.message;
          _isStreaming = false;
          _streamingText = '';
          _statusMessage = null;
          notifyListeners();
        }
      }
    } catch (e) {
      _error = e.toString();
      _isStreaming = false;
      _streamingText = '';
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
    _loading = false;
    notifyListeners();
  }

  /// Clear error message
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
