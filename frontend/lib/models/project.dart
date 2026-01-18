class Project {
  final String id;
  final String name;
  final String? description;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<Map<String, dynamic>>? documents;
  final List<Map<String, dynamic>>? threads;

  Project({
    required this.id,
    required this.name,
    this.description,
    required this.createdAt,
    required this.updatedAt,
    this.documents,
    this.threads,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      documents: json['documents'] != null
          ? List<Map<String, dynamic>>.from(json['documents'])
          : null,
      threads: json['threads'] != null
          ? List<Map<String, dynamic>>.from(json['threads'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      if (documents != null) 'documents': documents,
      if (threads != null) 'threads': threads,
    };
  }
}
