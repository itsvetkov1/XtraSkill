/// Artifact model for generated business analysis documents.
library;

import 'package:flutter/material.dart';

/// Types of business analysis artifacts (matches backend ArtifactType enum)
enum ArtifactType {
  userStories('user_stories'),
  acceptanceCriteria('acceptance_criteria'),
  requirementsDoc('requirements_doc'),
  brd('brd');

  final String value;
  const ArtifactType(this.value);

  static ArtifactType fromJson(String json) {
    return ArtifactType.values.firstWhere(
      (t) => t.value == json,
      orElse: () => ArtifactType.requirementsDoc,
    );
  }

  String get displayName {
    switch (this) {
      case ArtifactType.userStories:
        return 'User Stories';
      case ArtifactType.acceptanceCriteria:
        return 'Acceptance Criteria';
      case ArtifactType.requirementsDoc:
        return 'Requirements Doc';
      case ArtifactType.brd:
        return 'BRD';
    }
  }

  IconData get icon {
    switch (this) {
      case ArtifactType.userStories:
        return Icons.list_alt;
      case ArtifactType.acceptanceCriteria:
        return Icons.checklist;
      case ArtifactType.requirementsDoc:
        return Icons.description;
      case ArtifactType.brd:
        return Icons.article;
    }
  }

  String get description {
    switch (this) {
      case ArtifactType.userStories:
        return 'Generate user stories from requirements';
      case ArtifactType.acceptanceCriteria:
        return 'Create acceptance criteria for features';
      case ArtifactType.requirementsDoc:
        return 'Generate requirements documentation';
      case ArtifactType.brd:
        return 'Create Business Requirements Document';
    }
  }
}

/// Artifact model representing a generated document
class Artifact {
  final String id;
  final String threadId;
  final ArtifactType artifactType;
  final String title;
  final String? contentMarkdown; // Only loaded on expand (lazy)
  final DateTime createdAt;

  Artifact({
    required this.id,
    required this.threadId,
    required this.artifactType,
    required this.title,
    this.contentMarkdown,
    required this.createdAt,
  });

  factory Artifact.fromJson(Map<String, dynamic> json) {
    return Artifact(
      id: json['id'],
      threadId: json['thread_id'],
      artifactType: ArtifactType.fromJson(json['artifact_type']),
      title: json['title'],
      contentMarkdown: json['content_markdown'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  /// Create artifact from SSE event (minimal data, no content)
  factory Artifact.fromEvent({
    required String id,
    required String artifactType,
    required String title,
    required String threadId,
  }) {
    return Artifact(
      id: id,
      threadId: threadId,
      artifactType: ArtifactType.fromJson(artifactType),
      title: title,
      contentMarkdown: null, // Content loaded on demand
      createdAt: DateTime.now(),
    );
  }

  /// Copy with updated content (for lazy loading)
  Artifact copyWithContent(String content) {
    return Artifact(
      id: id,
      threadId: threadId,
      artifactType: artifactType,
      title: title,
      contentMarkdown: content,
      createdAt: createdAt,
    );
  }
}
