/// Skill discovery service for Claude Code skills.
///
/// Fetches available skills from backend API and caches them.
library;

import 'package:flutter/foundation.dart';

import '../models/skill.dart';
import 'api_client.dart';

/// Service for discovering and caching Claude Code skills
class SkillService {
  /// Dio client for API calls
  final _dio = ApiClient().dio;

  /// Cached skills to avoid repeated API calls
  List<Skill>? _cachedSkills;

  /// Get available skills (cached after first call)
  Future<List<Skill>> getSkills() async {
    // Return cached skills if available
    if (_cachedSkills != null) return _cachedSkills!;

    try {
      final response = await _dio.get('/api/skills');
      final List<dynamic> data = response.data as List<dynamic>;
      _cachedSkills = data.map((json) => Skill.fromJson(json as Map<String, dynamic>)).toList();
      return _cachedSkills!;
    } catch (e) {
      debugPrint('Failed to load skills: $e');
      return []; // Graceful degradation
    }
  }

  /// Clear cached skills (forces reload on next getSkills call)
  void clearCache() {
    _cachedSkills = null;
  }
}
