class Document {
  final String id;
  final String filename;
  final String? content;
  final DateTime createdAt;
  final String? contentType;
  final Map<String, dynamic>? metadata;

  Document({
    required this.id,
    required this.filename,
    required this.createdAt,
    this.content,
    this.contentType,
    this.metadata,
  });

  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'],
      filename: json['filename'],
      createdAt: DateTime.parse(json['created_at']),
      content: json['content'],
      contentType: json['content_type'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'filename': filename,
      'created_at': createdAt.toIso8601String(),
      if (content != null) 'content': content,
      if (contentType != null) 'content_type': contentType,
      if (metadata != null) 'metadata': metadata,
    };
  }

  /// Returns true if document is a table format (Excel or CSV)
  bool get isTableFormat {
    final ct = contentType ?? '';
    return ct.contains('spreadsheet') || ct == 'text/csv';
  }

  /// Returns true if document is a rich format (not plain text)
  bool get isRichFormat {
    final ct = contentType ?? '';
    return ct.contains('spreadsheet') || ct == 'text/csv' ||
           ct == 'application/pdf' || ct.contains('wordprocessing');
  }
}
