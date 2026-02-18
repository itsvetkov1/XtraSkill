/// Skill discovery service for Claude Code skills.
///
/// Fetches available skills from backend API and caches them.
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/skill.dart';
import 'api_client.dart';

/// Service for discovering and caching Claude Code skills
class SkillService {
  /// HTTP client for API requests
  final Dio _dio;

  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  SkillService({
    Dio? dio,
    FlutterSecureStorage? storage,
  })  : _dio = dio ?? ApiClient().dio,
        _storage = storage ?? const FlutterSecureStorage();

  /// Storage key for JWT token
  static const String _tokenKey = 'auth_token';

  /// Get authorization header with JWT token
  Future<Map<String, String>> _getAuthHeaders() async {
    final token = await _storage.read(key: _tokenKey);
    if (token == null) {
      throw Exception('No authentication token found');
    }
    return {
      'Authorization': 'Bearer $token',
    };
  }

  /// Cached skills to avoid repeated API calls
  List<Skill>? _cachedSkills;

  /// Get available skills (cached after first call)
  Future<List<Skill>> getSkills() async {
    // Return cached skills if available
    if (_cachedSkills != null) return _cachedSkills!;

    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.get(
        '/api/skills',
        options: Options(headers: headers),
      );
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
