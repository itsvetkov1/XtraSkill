/// Thread management service for conversation organization.
library;

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/thread.dart';
import '../models/message.dart';

/// Thread service handling API calls for conversation threads
class ThreadService {
  /// HTTP client for API requests
  final Dio _dio;

  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  /// Backend API base URL
  final String _baseUrl;

  ThreadService({
    String? baseUrl,
    Dio? dio,
    FlutterSecureStorage? storage,
  })  : _baseUrl = baseUrl ?? 'http://localhost:8000',
        _dio = dio ?? Dio(),
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

  /// Get list of threads for a project
  ///
  /// Returns threads ordered by created_at DESC (newest first)
  /// Includes message_count for each thread
  ///
  /// Throws exception if request fails or unauthorized
  Future<List<Thread>> getThreads(String projectId) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.get(
        '$_baseUrl/api/projects/$projectId/threads',
        options: Options(headers: headers),
      );

      final threadsData = response.data as List;
      return threadsData
          .map((json) => Thread.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Project not found');
      }
      throw Exception('Failed to load threads: ${e.message}');
    }
  }

  /// Create a new thread in a project
  ///
  /// [projectId] - ID of the project to create thread in
  /// [title] - Optional title for the thread (null for untitled threads)
  ///
  /// Returns created Thread object
  /// Throws exception if request fails or unauthorized
  Future<Thread> createThread(String projectId, String? title) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.post(
        '$_baseUrl/api/projects/$projectId/threads',
        options: Options(headers: headers),
        data: {
          if (title != null && title.isNotEmpty) 'title': title,
        },
      );

      return Thread.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Project not found');
      } else if (e.response?.statusCode == 400) {
        throw Exception('Invalid thread data');
      }
      throw Exception('Failed to create thread: ${e.message}');
    }
  }

  /// Get thread details with full message history
  ///
  /// [threadId] - ID of the thread to retrieve
  ///
  /// Returns Thread object with messages array populated
  /// Messages are ordered chronologically (oldest first)
  ///
  /// Throws exception if thread not found or unauthorized
  Future<Thread> getThread(String threadId) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.get(
        '$_baseUrl/api/threads/$threadId',
        options: Options(headers: headers),
      );

      return Thread.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Thread not found');
      }
      throw Exception('Failed to load thread: ${e.message}');
    }
  }
}
