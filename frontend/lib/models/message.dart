/// Message model for conversation messages.
library;

import '../services/ai_service.dart';

/// Role of the message sender
enum MessageRole {
  user,
  assistant;

  String toJson() => name;

  static MessageRole fromJson(String json) {
    return MessageRole.values.firstWhere(
      (role) => role.name == json,
      orElse: () => MessageRole.user,
    );
  }
}

/// Message in a conversation thread
class Message {
  final String id;
  final MessageRole role;
  final String content;
  final DateTime createdAt;

  /// Source documents used to generate this response (SRC-01)
  final List<DocumentSource> documentsUsed;

  Message({
    required this.id,
    required this.role,
    required this.content,
    required this.createdAt,
    this.documentsUsed = const [], // Default empty per SRC-04
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'],
      role: MessageRole.fromJson(json['role']),
      content: json['content'],
      createdAt: DateTime.parse(json['created_at']),
      // documentsUsed not in existing backend history response, will be empty
      documentsUsed: const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'role': role.toJson(),
      'content': content,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
