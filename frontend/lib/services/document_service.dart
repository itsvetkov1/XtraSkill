import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:file_saver/file_saver.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/document.dart';
import 'api_client.dart';

/// Service for document-related API calls.
///
/// Handles file upload, document listing, viewing, and search.
class DocumentService {
  /// HTTP client for API requests
  final Dio _dio;

  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  DocumentService({
    Dio? dio,
    FlutterSecureStorage? storage,
  })  : _dio = dio ?? ApiClient().dio,
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
      '/api/projects/$projectId/documents',
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
    final response = await _dio.get('/api/projects/$projectId/documents',
      options: await _getAuthHeaders(),
    );
    return (response.data as List)
        .map((json) => Document.fromJson(json))
        .toList();
  }

  /// Get document content by ID.
  ///
  /// Returns full document with decrypted content.
  Future<Document> getDocumentContent(String documentId) async {
    final response = await _dio.get('/api/documents/$documentId',
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
      '/api/projects/$projectId/documents/search',
      queryParameters: {'q': query},
      options: await _getAuthHeaders(),
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
        '/api/documents/$id',
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

  /// Download document binary content by ID.
  ///
  /// Returns raw file bytes for binary documents (Excel, PDF, Word, etc).
  Future<List<int>> downloadDocument(String documentId) async {
    final response = await _dio.get(
      '/api/documents/$documentId/download',
      options: Options(
        responseType: ResponseType.bytes,
        headers: (await _getAuthHeaders()).headers,
      ),
    );
    return response.data as List<int>;
  }

  /// Upload document to an Assistant thread (not a project).
  ///
  /// [threadId] - ID of the thread to upload to
  /// [filename] - Name of the file
  /// [bytes] - File content as bytes
  /// [contentType] - MIME type of the file
  Future<Map<String, dynamic>> uploadThreadDocument(
    String threadId,
    String filename,
    Uint8List bytes,
    String contentType,
  ) async {
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(
        bytes,
        filename: filename,
        contentType: DioMediaType.parse(contentType),
      ),
    });

    final response = await _dio.post(
      '/api/threads/$threadId/documents',
      data: formData,
      options: await _getAuthHeaders(),
    );
    return response.data as Map<String, dynamic>;
  }

  /// List documents uploaded to an Assistant thread.
  ///
  /// [threadId] - ID of the thread
  Future<List<Map<String, dynamic>>> getThreadDocuments(String threadId) async {
    final response = await _dio.get(
      '/api/threads/$threadId/documents',
      options: await _getAuthHeaders(),
    );
    return List<Map<String, dynamic>>.from(response.data as List);
  }

  /// Export document data to Excel or CSV format.
  ///
  /// [documentId] - ID of the document to export
  /// [format] - Export format: 'xlsx' or 'csv'
  ///
  /// Downloads the generated file and saves it using FileSaver.
  Future<void> exportDocument(String documentId, String format) async {
    final endpoint = '/api/documents/$documentId/export/$format';

    // Download binary from backend
    final response = await _dio.get(
      endpoint,
      options: Options(
        responseType: ResponseType.bytes,
        headers: (await _getAuthHeaders()).headers,
      ),
    );

    // Extract filename from Content-Disposition header
    String filename = 'export.$format';
    final contentDisposition = response.headers.value('content-disposition');
    if (contentDisposition != null) {
      final filenameMatch = RegExp(r'filename="(.+)"').firstMatch(contentDisposition);
      if (filenameMatch != null) {
        filename = filenameMatch.group(1)!;
      }
    }

    // Determine MIME type and extension
    final mimeType = format == 'xlsx' ? MimeType.microsoftExcel : MimeType.csv;
    final nameWithoutExt = filename.replaceAll(RegExp(r'\.[^.]+$'), '');
    final ext = format == 'xlsx' ? 'xlsx' : 'csv';

    // Save file using FileSaver (cross-platform download)
    await FileSaver.instance.saveFile(
      name: nameWithoutExt,
      bytes: Uint8List.fromList(response.data as List<int>),
      ext: ext,
      mimeType: mimeType,
    );
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
