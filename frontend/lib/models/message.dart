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

class Message {
  final String id;
  final MessageRole role;
  final String content;
  final DateTime createdAt;

  Message({
    required this.id,
    required this.role,
    required this.content,
    required this.createdAt,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'],
      role: MessageRole.fromJson(json['role']),
      content: json['content'],
      createdAt: DateTime.parse(json['created_at']),
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
