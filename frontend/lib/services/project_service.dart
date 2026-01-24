/// Project API service for CRUD operations.
library;

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/project.dart';

/// Service for project API operations
class ProjectService {
  /// HTTP client for API requests
  final Dio _dio;

  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  /// Backend API base URL
  final String _baseUrl;

  ProjectService({
    String? baseUrl,
    Dio? dio,
    FlutterSecureStorage? storage,
  })  : _baseUrl = baseUrl ?? 'http://localhost:8000',
        _dio = dio ?? Dio(),
        _storage = storage ?? const FlutterSecureStorage();

  /// Storage key for JWT token
  static const String _tokenKey = 'auth_token';

  /// Get authorization headers with JWT token
  Future<Map<String, String>> _getHeaders() async {
    final token = await _storage.read(key: _tokenKey);
    if (token == null) {
      throw Exception('Not authenticated');
    }
    return {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    };
  }

  /// Get all projects for current user
  ///
  /// Returns list of projects ordered by updated_at DESC
  /// Throws exception if not authenticated or request fails
  Future<List<Project>> getProjects() async {
    try {
      final headers = await _getHeaders();
      final response = await _dio.get(
        '$_baseUrl/api/projects',
        options: Options(headers: headers),
      );

      final List<dynamic> data = response.data;
      return data.map((json) => Project.fromJson(json)).toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('Unauthorized - please login again');
      }
      throw Exception('Failed to load projects: ${e.message}');
    }
  }

  /// Create a new project
  ///
  /// Args:
  ///   name: Project name (required, 1-255 chars)
  ///   description: Optional project description
  ///
  /// Returns created project
  /// Throws exception if validation fails or request fails
  Future<Project> createProject(String name, String? description) async {
    try {
      final headers = await _getHeaders();
      final response = await _dio.post(
        '$_baseUrl/api/projects',
        data: {
          'name': name,
          'description': description,
        },
        options: Options(headers: headers),
      );

      return Project.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('Unauthorized - please login again');
      } else if (e.response?.statusCode == 422) {
        throw Exception('Validation error: ${e.response?.data}');
      }
      throw Exception('Failed to create project: ${e.message}');
    }
  }

  /// Get project details with documents and threads
  ///
  /// Args:
  ///   id: Project UUID
  ///
  /// Returns project with documents and threads loaded
  /// Throws exception if not found or not owned by user
  Future<Project> getProject(String id) async {
    try {
      final headers = await _getHeaders();
      final response = await _dio.get(
        '$_baseUrl/api/projects/$id',
        options: Options(headers: headers),
      );

      return Project.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('Unauthorized - please login again');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Project not found');
      }
      throw Exception('Failed to load project: ${e.message}');
    }
  }

  /// Update project name and description
  ///
  /// Args:
  ///   id: Project UUID
  ///   name: Updated project name (required, 1-255 chars)
  ///   description: Updated project description
  ///
  /// Returns updated project
  /// Throws exception if not found or validation fails
  Future<Project> updateProject(
    String id,
    String name,
    String? description,
  ) async {
    try {
      final headers = await _getHeaders();
      final response = await _dio.put(
        '$_baseUrl/api/projects/$id',
        data: {
          'name': name,
          'description': description,
        },
        options: Options(headers: headers),
      );

      return Project.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('Unauthorized - please login again');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Project not found');
      } else if (e.response?.statusCode == 422) {
        throw Exception('Validation error: ${e.response?.data}');
      }
      throw Exception('Failed to update project: ${e.message}');
    }
  }
}
