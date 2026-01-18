class Document {
  final String id;
  final String filename;
  final String? content;
  final DateTime createdAt;

  Document({
    required this.id,
    required this.filename,
    required this.createdAt,
    this.content,
  });

  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'],
      filename: json['filename'],
      createdAt: DateTime.parse(json['created_at']),
      content: json['content'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'filename': filename,
      'created_at': createdAt.toIso8601String(),
      if (content != null) 'content': content,
    };
  }
}
