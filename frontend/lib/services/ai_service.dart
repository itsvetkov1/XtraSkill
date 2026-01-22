/// AI service for streaming chat with Claude via SSE.
library;

import 'dart:convert';
import 'package:flutter_client_sse/constants/sse_request_type_enum.dart';
import 'package:flutter_client_sse/flutter_client_sse.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../core/config.dart';

/// Base class for chat events from SSE stream
abstract class ChatEvent {}

/// Text delta event - incremental text from AI
class TextDeltaEvent extends ChatEvent {
  final String text;
  TextDeltaEvent({required this.text});
}

/// Tool executing event - AI is searching documents
class ToolExecutingEvent extends ChatEvent {
  final String status;
  ToolExecutingEvent({required this.status});
}

/// Message complete event - response finished with usage stats
class MessageCompleteEvent extends ChatEvent {
  final String content;
  final int inputTokens;
  final int outputTokens;
  MessageCompleteEvent({
    required this.content,
    required this.inputTokens,
    required this.outputTokens,
  });
}

/// Error event - something went wrong
class ErrorEvent extends ChatEvent {
  final String message;
  ErrorEvent({required this.message});
}

/// AI service for streaming chat conversations
class AIService {
  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  /// Storage key for JWT token
  static const String _tokenKey = 'auth_token';

  AIService({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  /// Stream chat response from AI
  ///
  /// Connects to SSE endpoint and yields chat events as they arrive.
  /// [threadId] - ID of the thread to chat in
  /// [message] - User message content
  ///
  /// Yields ChatEvent subclasses:
  /// - TextDeltaEvent: Incremental text
  /// - ToolExecutingEvent: AI is using a tool
  /// - MessageCompleteEvent: Response complete
  /// - ErrorEvent: Error occurred
  Stream<ChatEvent> streamChat(String threadId, String message) async* {
    final token = await _storage.read(key: _tokenKey);
    if (token == null) {
      yield ErrorEvent(message: 'Not authenticated');
      return;
    }

    final url = '$apiBaseUrl/api/threads/$threadId/chat';

    try {
      // Use SSEClient to connect to streaming endpoint
      final stream = SSEClient.subscribeToSSE(
        method: SSERequestType.POST,
        url: url,
        header: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        body: {'content': message},
      );

      await for (final event in stream) {
        if (event.data == null || event.data!.isEmpty) continue;

        try {
          final data = jsonDecode(event.data!) as Map<String, dynamic>;

          switch (event.event) {
            case 'text_delta':
              yield TextDeltaEvent(text: data['text'] as String? ?? '');
              break;
            case 'tool_executing':
              yield ToolExecutingEvent(status: data['status'] as String? ?? 'Processing...');
              break;
            case 'message_complete':
              final usage = data['usage'] as Map<String, dynamic>?;
              yield MessageCompleteEvent(
                content: data['content'] as String? ?? '',
                inputTokens: usage?['input_tokens'] as int? ?? 0,
                outputTokens: usage?['output_tokens'] as int? ?? 0,
              );
              break;
            case 'error':
              yield ErrorEvent(message: data['message'] as String? ?? 'Unknown error');
              break;
          }
        } catch (e) {
          // Skip malformed events
          continue;
        }
      }
    } catch (e) {
      yield ErrorEvent(message: 'Connection error: $e');
    }
  }
}
