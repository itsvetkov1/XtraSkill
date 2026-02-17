/// Assistant conversation state management with streaming support.
///
/// Simplified provider for Assistant threads (no artifacts, budget, or mode selection).
library;

import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';

import '../models/message.dart';
import '../models/skill.dart';
import '../models/thread.dart';
import '../services/ai_service.dart';
import '../services/thread_service.dart';

/// File attached for upload with next message
class AttachedFile {
  final String name;
  final int size;
  final Uint8List? bytes;
  final String contentType;

  AttachedFile({
    required this.name,
    required this.size,
    this.bytes,
    required this.contentType,
  });
}

/// Assistant conversation provider managing chat state and streaming
class AssistantConversationProvider extends ChangeNotifier {
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

  /// Status message (e.g., "Thinking...")
  String? _statusMessage;

  /// Whether AI is currently streaming a response
  bool _isStreaming = false;

  /// Loading state for initial thread load
  bool _loading = false;

  /// Error message if something failed
  String? _error;

  /// Whether the thread was not found (404)
  bool _isNotFound = false;

  /// Content of the last message that failed to send
  String? _lastFailedMessage;

  /// Whether there is partial content from an interrupted stream
  bool _hasPartialContent = false;

  /// Currently selected skill (for prepending to next message)
  Skill? _selectedSkill;

  /// Files attached for the next message
  final List<AttachedFile> _attachedFiles = [];

  /// When thinking indicator started (for elapsed time display)
  DateTime? _thinkingStartTime;

  /// Whether auto-retry has been attempted for current send
  bool _hasAutoRetried = false;

  AssistantConversationProvider({
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

  /// Currently selected skill
  Skill? get selectedSkill => _selectedSkill;

  /// Files attached for next message
  List<AttachedFile> get attachedFiles => _attachedFiles;

  /// Thinking start time (for elapsed time display)
  DateTime? get thinkingStartTime => _thinkingStartTime;

  /// Load a thread with its message history
  Future<void> loadThread(String threadId) async {
    _loading = true;
    _error = null;
    _isNotFound = false;
    notifyListeners();

    try {
      _thread = await _threadService.getThread(threadId);
      _messages = _thread?.messages ?? [];
      _loading = false;
      notifyListeners();
    } catch (e) {
      final errorMessage = e.toString();
      // Check if it's a 404 "not found" error
      if (errorMessage.contains('not found') ||
          errorMessage.contains('404')) {
        _isNotFound = true;
        _error = null;
      } else {
        _error = errorMessage;
        _isNotFound = false;
      }
      _loading = false;
      notifyListeners();
    }
  }

  /// Send a message and stream the AI response
  ///
  /// If a skill is selected, prepends skill context to the message.
  /// If files are attached, includes file references in the message.
  /// Clears skill and files after sending.
  Future<void> sendMessage(String content) async {
    if (_thread == null || _isStreaming) return;

    _error = null;
    _lastFailedMessage = content;
    _hasAutoRetried = false; // Reset auto-retry flag for new send

    // Prepend skill context if selected
    String messageContent = content;
    if (_selectedSkill != null) {
      messageContent = '[Using skill: ${_selectedSkill!.name}]\n\n$content';
    }

    // Include file references if attached
    if (_attachedFiles.isNotEmpty) {
      final fileList = _attachedFiles.map((f) => f.name).join(', ');
      messageContent = '$messageContent\n\n[Attached files: $fileList]';
    }

    // Add user message optimistically (will be confirmed by refresh)
    final userMessage = Message(
      id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
      role: MessageRole.user,
      content: content, // Show original user content without skill/file annotations
      createdAt: DateTime.now(),
    );
    _messages.add(userMessage);

    // Start streaming
    _isStreaming = true;
    _streamingText = '';
    _statusMessage = null;
    _thinkingStartTime = DateTime.now(); // Track thinking start time
    notifyListeners();

    try {
      await for (final event in _aiService.streamChat(_thread!.id, messageContent)) {
        if (event is TextDeltaEvent) {
          // First text delta means thinking has ended
          if (_thinkingStartTime != null) {
            _thinkingStartTime = null;
          }
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
          _thinkingStartTime = null;
          _hasAutoRetried = false;

          // Clear skill and files after successful send
          _selectedSkill = null;
          _attachedFiles.clear();

          notifyListeners();
        } else if (event is ErrorEvent) {
          _error = event.message;
          _isStreaming = false;
          _hasPartialContent = _streamingText.isNotEmpty;
          // DO NOT clear _streamingText - preserve partial content
          _statusMessage = null;
          _thinkingStartTime = null;
          notifyListeners();

          // Auto-retry once on error after 2-second delay
          if (!_hasAutoRetried) {
            _hasAutoRetried = true;
            await Future.delayed(const Duration(seconds: 2));
            if (!_isStreaming && _error != null) {
              // Still in error state, retry
              _error = null;
              _hasPartialContent = false;
              _streamingText = '';
              // Remove the optimistic user message to avoid duplicates
              if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
                _messages.removeLast();
              }
              await sendMessage(content); // Retry with original content
            }
          }
        }
      }
    } catch (e) {
      _error = e.toString();
      _isStreaming = false;
      _hasPartialContent = _streamingText.isNotEmpty;
      // DO NOT clear _streamingText - preserve partial content
      _statusMessage = null;
      _thinkingStartTime = null;
      notifyListeners();

      // Auto-retry once on error after 2-second delay
      if (!_hasAutoRetried) {
        _hasAutoRetried = true;
        await Future.delayed(const Duration(seconds: 2));
        if (!_isStreaming && _error != null) {
          // Still in error state, retry
          _error = null;
          _hasPartialContent = false;
          _streamingText = '';
          // Remove the optimistic user message to avoid duplicates
          if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
            _messages.removeLast();
          }
          await sendMessage(content); // Retry with original content
        }
      }
    }
  }

  /// Retry the last failed message
  void retryLastMessage() {
    if (_lastFailedMessage == null) return;

    final content = _lastFailedMessage!;
    _lastFailedMessage = null;
    _error = null;
    _hasPartialContent = false;
    _streamingText = '';

    // Remove the optimistic user message that was added on first attempt
    // to avoid duplicates when sendMessage adds it again
    if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
      _messages.removeLast();
    }

    sendMessage(content);
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
    _selectedSkill = null;
    _attachedFiles.clear();
    _thinkingStartTime = null;
    _hasAutoRetried = false;
    notifyListeners();
  }

  /// Clear error message and failed message state
  void clearError() {
    _error = null;
    _isNotFound = false;
    _lastFailedMessage = null;
    _hasPartialContent = false;
    _streamingText = '';
    notifyListeners();
  }

  /// Select a skill to prepend to next message
  void selectSkill(Skill skill) {
    _selectedSkill = skill;
    notifyListeners();
  }

  /// Clear selected skill
  void clearSkill() {
    _selectedSkill = null;
    notifyListeners();
  }

  /// Add a file to the pending attachment list
  void addAttachedFile(AttachedFile file) {
    _attachedFiles.add(file);
    notifyListeners();
  }

  /// Remove a file from the pending attachment list
  void removeAttachedFile(AttachedFile file) {
    _attachedFiles.remove(file);
    notifyListeners();
  }

  /// Clear all pending attached files
  void clearAttachedFiles() {
    _attachedFiles.clear();
    notifyListeners();
  }
}
