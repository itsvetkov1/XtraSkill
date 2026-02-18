/// Skill model for Claude Code skills.
library;

/// A Claude Code skill that can be selected to prepend context to messages
class Skill {
  /// Skill name (e.g., "business-analyst")
  final String name;

  /// Human-readable description
  final String description;

  /// Path to skill file relative to project root
  final String skillPath;

  /// List of key features this skill provides
  final List<String> features;

  Skill({
    required this.name,
    required this.description,
    required this.skillPath,
    this.features = const [],
  });

  /// Create Skill from JSON
  factory Skill.fromJson(Map<String, dynamic> json) {
    return Skill(
      name: json['name'] as String,
      description: json['description'] as String,
      skillPath: json['skill_path'] as String,
      features: (json['features'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
    );
  }

  /// Convert Skill to JSON
  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'description': description,
      'skill_path': skillPath,
      'features': features,
    };
  }

  /// Get display name from skill name (converts "business-analyst" to "Business Analyst")
  String get displayName {
    return name
        .split('-')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }
}
