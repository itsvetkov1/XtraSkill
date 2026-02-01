import 'message.dart';

class Thread {
  final String id;
  final String? projectId; // Nullable for project-less threads
  final String? projectName; // For global listing display
  final String? title;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? lastActivityAt; // For activity-based sorting
  final int? messageCount; // Optional: only in list view
  final List<Message>? messages; // Optional: only in detail view
  final String? modelProvider; // LLM provider used for this thread

  Thread({
    required this.id,
    this.projectId,
    this.projectName,
    this.title,
    required this.createdAt,
    required this.updatedAt,
    this.lastActivityAt,
    this.messageCount,
    this.messages,
    this.modelProvider,
  });

  /// Whether this thread belongs to a project
  bool get hasProject => projectId != null && projectId!.isNotEmpty;

  factory Thread.fromJson(Map<String, dynamic> json) {
    return Thread(
      id: json['id'],
      projectId: json['project_id'], // Can be null
      projectName: json['project_name'], // Can be null
      title: json['title'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      lastActivityAt: json['last_activity_at'] != null
          ? DateTime.parse(json['last_activity_at'])
          : null,
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
      if (projectId != null) 'project_id': projectId,
      if (projectName != null) 'project_name': projectName,
      'title': title,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      if (lastActivityAt != null)
        'last_activity_at': lastActivityAt!.toIso8601String(),
      if (messageCount != null) 'message_count': messageCount,
      if (messages != null)
        'messages': messages!.map((m) => m.toJson()).toList(),
      if (modelProvider != null) 'model_provider': modelProvider,
    };
  }
}

/// Paginated response for global thread listing
class PaginatedThreads {
  final List<Thread> threads;
  final int total;
  final int page;
  final int pageSize;
  final bool hasMore;

  PaginatedThreads({
    required this.threads,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.hasMore,
  });

  factory PaginatedThreads.fromJson(Map<String, dynamic> json) {
    return PaginatedThreads(
      threads: (json['threads'] as List<dynamic>)
          .map((t) => Thread.fromJson(t as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
      hasMore: json['has_more'] as bool,
    );
  }
}
