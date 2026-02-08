/// AI service for streaming chat with Claude via SSE.
library;

import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_client_sse/constants/sse_request_type_enum.dart';
import 'package:flutter_client_sse/flutter_client_sse.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../core/config.dart';
import 'api_client.dart';

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
  final List<DocumentSource> documentsUsed;
  MessageCompleteEvent({
    required this.content,
    required this.inputTokens,
    required this.outputTokens,
    this.documentsUsed = const [],
  });
}

/// Error event - something went wrong
class ErrorEvent extends ChatEvent {
  final String message;
  ErrorEvent({required this.message});
}

/// Artifact created event - generated artifact saved
class ArtifactCreatedEvent extends ChatEvent {
  final String id;
  final String artifactType;
  final String title;
  ArtifactCreatedEvent({
    required this.id,
    required this.artifactType,
    required this.title,
  });
}

/// Documents used data - attached to MessageCompleteEvent
class DocumentSource {
  final String id;
  final String filename;
  DocumentSource({required this.id, required this.filename});

  factory DocumentSource.fromJson(Map<String, dynamic> json) {
    return DocumentSource(
      id: json['id'] as String,
      filename: json['filename'] as String,
    );
  }
}

/// AI service for streaming chat conversations
class AIService {
  /// HTTP client for API requests
  final Dio _dio;

  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  /// Storage key for JWT token
  static const String _tokenKey = 'auth_token';

  AIService({Dio? dio, FlutterSecureStorage? storage})
      : _dio = dio ?? ApiClient().dio,
        _storage = storage ?? const FlutterSecureStorage();

  /// Get authorization headers with JWT token
  Future<Map<String, String>> _getHeaders() async {
    final token = await _storage.read(key: _tokenKey);
    if (token == null) {
      throw Exception('Not authenticated');
    }
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  /// Stream chat response from AI
  ///
  /// Connects to SSE endpoint and yields chat events as they arrive.
  /// [threadId] - ID of the thread to chat in
  /// [message] - User message content
  /// [artifactGeneration] - If true, request silent artifact generation (no text_delta events)
  ///
  /// Yields ChatEvent subclasses:
  /// - TextDeltaEvent: Incremental text
  /// - ToolExecutingEvent: AI is using a tool
  /// - MessageCompleteEvent: Response complete
  /// - ErrorEvent: Error occurred
  Stream<ChatEvent> streamChat(
    String threadId,
    String message, {
    bool artifactGeneration = false,
  }) async* {
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
        body: {
          'content': message,
          if (artifactGeneration) 'artifact_generation': true,
        },
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
              final docsUsedJson = data['documents_used'] as List<dynamic>?;
              final docsUsed = docsUsedJson
                  ?.map((d) => DocumentSource.fromJson(d as Map<String, dynamic>))
                  .toList() ?? [];
              yield MessageCompleteEvent(
                content: data['content'] as String? ?? '',
                inputTokens: usage?['input_tokens'] as int? ?? 0,
                outputTokens: usage?['output_tokens'] as int? ?? 0,
                documentsUsed: docsUsed,
              );
              break;
            case 'artifact_created':
              yield ArtifactCreatedEvent(
                id: data['id'] as String? ?? '',
                artifactType: data['artifact_type'] as String? ?? 'requirements_doc',
                title: data['title'] as String? ?? 'Untitled',
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

  /// Delete a message from a thread
  ///
  /// Returns successfully if deleted, throws on error.
  Future<void> deleteMessage(String threadId, String messageId) async {
    try {
      final headers = await _getHeaders();
      await _dio.delete(
        '/api/threads/$threadId/messages/$messageId',
        options: Options(headers: headers),
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('Unauthorized - please login again');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Message not found');
      }
      throw Exception('Failed to delete message: ${e.message}');
    }
  }
}
