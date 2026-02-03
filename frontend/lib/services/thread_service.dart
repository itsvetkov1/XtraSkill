/// Thread management service for conversation organization.
library;

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/thread.dart';

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
  /// [provider] - Optional LLM provider for the thread (defaults to user preference)
  ///
  /// Returns created Thread object
  /// Throws exception if request fails or unauthorized
  Future<Thread> createThread(String projectId, String? title, {String? provider}) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.post(
        '$_baseUrl/api/projects/$projectId/threads',
        options: Options(headers: headers),
        data: {
          if (title != null && title.isNotEmpty) 'title': title,
          if (provider != null) 'model_provider': provider,
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

  /// Delete a thread by ID
  ///
  /// Returns successfully if deleted, throws on error.
  /// Backend cascades to messages in thread.
  Future<void> deleteThread(String id) async {
    try {
      final headers = await _getAuthHeaders();
      await _dio.delete(
        '$_baseUrl/api/threads/$id',
        options: Options(headers: headers),
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Unauthorized - please login again');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Thread not found');
      }
      throw Exception('Failed to delete thread: ${e.message}');
    }
  }

  /// Rename a thread
  ///
  /// [threadId] - ID of the thread to rename
  /// [title] - New title (or null to clear)
  ///
  /// Returns updated Thread object
  Future<Thread> renameThread(String threadId, String? title) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.patch(
        '$_baseUrl/api/threads/$threadId',
        options: Options(headers: headers),
        data: {
          'title': title,
        },
      );

      return Thread.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Thread not found');
      }
      throw Exception('Failed to rename thread: ${e.message}');
    }
  }

  /// Get all threads for current user (global listing)
  ///
  /// Returns paginated list of all user threads across all projects.
  /// Sorted by last_activity_at DESC (most recently active first).
  ///
  /// [page] - Page number (1-indexed)
  /// [pageSize] - Number of threads per page
  Future<PaginatedThreads> getGlobalThreads({
    int page = 1,
    int pageSize = 25,
  }) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.get(
        '$_baseUrl/api/threads?page=$page&page_size=$pageSize',
        options: Options(headers: headers),
      );

      return PaginatedThreads.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      }
      throw Exception('Failed to load threads: ${e.message}');
    }
  }

  /// Create a thread (optionally without project)
  ///
  /// [title] - Optional title for the thread
  /// [projectId] - Optional project ID (null for project-less thread)
  /// [modelProvider] - Optional LLM provider
  ///
  /// Returns created Thread object
  Future<Thread> createGlobalThread({
    String? title,
    String? projectId,
    String? modelProvider,
  }) async {
    try {
      final headers = await _getAuthHeaders();
      final data = <String, dynamic>{};
      if (title != null) data['title'] = title;
      if (projectId != null) data['project_id'] = projectId;
      if (modelProvider != null) data['model_provider'] = modelProvider;

      final response = await _dio.post(
        '$_baseUrl/api/threads',
        options: Options(headers: headers),
        data: data,
      );

      return Thread.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      } else if (e.response?.statusCode == 400) {
        throw Exception('Invalid thread data');
      }
      throw Exception('Failed to create thread: ${e.message}');
    }
  }

  /// Update conversation mode for a thread
  ///
  /// [threadId] - ID of the thread to update
  /// [mode] - Conversation mode ("meeting" or "document_refinement")
  ///
  /// Returns updated Thread object
  /// Throws exception if mode is invalid (400) or thread not found (404)
  Future<Thread> updateThreadMode(String threadId, String mode) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.patch(
        '$_baseUrl/api/threads/$threadId',
        options: Options(headers: headers),
        data: {'conversation_mode': mode},
      );

      return Thread.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      } else if (e.response?.statusCode == 400) {
        throw Exception('Invalid mode. Valid options: meeting, document_refinement');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Thread not found');
      }
      throw Exception('Failed to update mode: ${e.message}');
    }
  }

  /// Associate a project-less thread with a project
  ///
  /// [threadId] - ID of the thread to associate
  /// [projectId] - ID of the project to associate with
  ///
  /// Returns updated Thread object
  /// Throws exception if thread already has project (400) or project not found (404)
  Future<Thread> associateWithProject(String threadId, String projectId) async {
    try {
      final headers = await _getAuthHeaders();
      final response = await _dio.patch(
        '$_baseUrl/api/threads/$threadId',
        options: Options(headers: headers),
        data: {'project_id': projectId},
      );

      return Thread.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        throw Exception('Authentication required');
      } else if (e.response?.statusCode == 400) {
        throw Exception('Thread already associated with a project');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Thread or project not found');
      }
      throw Exception('Failed to associate thread: ${e.message}');
    }
  }
}
