import 'message.dart';

class Thread {
  final String id;
  final String projectId;
  final String? title;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int? messageCount; // Optional: only in list view
  final List<Message>? messages; // Optional: only in detail view
  final String? modelProvider; // LLM provider used for this thread

  Thread({
    required this.id,
    required this.projectId,
    this.title,
    required this.createdAt,
    required this.updatedAt,
    this.messageCount,
    this.messages,
    this.modelProvider,
  });

  factory Thread.fromJson(Map<String, dynamic> json) {
    return Thread(
      id: json['id'],
      projectId: json['project_id'],
      title: json['title'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      messageCount: json['message_count'] as int?,
      messages: json['messages'] != null
          ? (json['messages'] as List)
              .map((m) => Message.fromJson(m as Map<String, dynamic>))
              .toList()
          : null,
      modelProvider: json['model_provider'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'project_id': projectId,
      'title': title,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      if (messageCount != null) 'message_count': messageCount,
      if (messages != null)
        'messages': messages!.map((m) => m.toJson()).toList(),
      if (modelProvider != null) 'model_provider': modelProvider,
    };
  }
}
