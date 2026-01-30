import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/document.dart';

/// Service for document-related API calls.
///
/// Handles file upload, document listing, viewing, and search.
class DocumentService {
  /// HTTP client for API requests
  final Dio _dio;

  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  /// Backend API base URL
  final String _baseUrl;

  DocumentService({
    String? baseUrl,
    Dio? dio,
    FlutterSecureStorage? storage,
  })  : _baseUrl = baseUrl ?? 'http://localhost:8000',
        _dio = dio ?? Dio(),
        _storage = storage ?? const FlutterSecureStorage();

  /// Storage key for JWT token
  static const String _tokenKey = 'auth_token';

  /// Get authorization headers with JWT token
  Future<Options> _getAuthHeaders() async {
    final token = await _storage.read(key: _tokenKey);
    return Options(
      headers: {
        'Authorization': 'Bearer $token',
      },
    );
  }

  /// Upload a document to a project.
  ///
  /// [projectId] - ID of the project to upload to
  /// [fileBytes] - File content as bytes
  /// [filename] - Name of the file
  /// [onSendProgress] - Optional callback for upload progress
  Future<Document> uploadDocument(
    String projectId,
    List<int> fileBytes,
    String filename, {
    void Function(int sent, int total)? onSendProgress,
  }) async {
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(
        fileBytes,
        filename: filename,
      ),
    });

    final response = await _dio.post(
      '$_baseUrl/api/projects/$projectId/documents',
      data: formData,
      options: await _getAuthHeaders(),
      onSendProgress: onSendProgress,
    );

    return Document.fromJson(response.data);
  }

  /// Get list of documents in a project.
  ///
  /// Returns metadata only (no content).
  Future<List<Document>> getDocuments(String projectId) async {
    final response = await _dio.get('/projects/$projectId/documents');
    return (response.data as List)
        .map((json) => Document.fromJson(json))
        .toList();
  }

  /// Get document content by ID.
  ///
  /// Returns full document with decrypted content.
  Future<Document> getDocumentContent(String documentId) async {
    final response = await _dio.get('/documents/$documentId',
      options: await _getAuthHeaders(),
    );
    return Document.fromJson(response.data);
  }

  /// Search documents within a project.
  ///
  /// [projectId] - ID of the project to search in
  /// [query] - Search query (FTS5 syntax)
  ///
  /// Returns list of search results with snippets and relevance scores.
  Future<List<DocumentSearchResult>> searchDocuments(
    String projectId,
    String query,
  ) async {
    final response = await _dio.get(
      '/projects/$projectId/documents/search',
      queryParameters: {'q': query},
    );

    return (response.data as List)
        .map((json) => DocumentSearchResult.fromJson(json))
        .toList();
  }

  /// Delete a document by ID
  ///
  /// Returns successfully if deleted, throws on error.
  Future<void> deleteDocument(String id) async {
    try {
      final options = await _getAuthHeaders();
      await _dio.delete(
        '$_baseUrl/api/documents/$id',
        options: options,
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('Unauthorized - please login again');
      } else if (e.response?.statusCode == 404) {
        throw Exception('Document not found');
      }
      throw Exception('Failed to delete document: ${e.message}');
    }
  }
}

/// Document search result with snippet and relevance score.
class DocumentSearchResult {
  final String id;
  final String filename;
  final String snippet;
  final double score;

  DocumentSearchResult({
    required this.id,
    required this.filename,
    required this.snippet,
    required this.score,
  });

  factory DocumentSearchResult.fromJson(Map<String, dynamic> json) {
    return DocumentSearchResult(
      id: json['id'],
      filename: json['filename'],
      snippet: json['snippet'],
      score: (json['score'] as num).toDouble(),
    );
  }
}
