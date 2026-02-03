/// Artifact service for fetching and exporting artifacts.
library;

import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:file_saver/file_saver.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../core/config.dart';
import '../models/artifact.dart';

/// Service for artifact API operations
class ArtifactService {
  final Dio _dio;
  final FlutterSecureStorage _storage;
  static const String _tokenKey = 'auth_token';

  ArtifactService({Dio? dio, FlutterSecureStorage? storage})
      : _dio = dio ?? Dio(),
        _storage = storage ?? const FlutterSecureStorage();

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

  /// Fetch artifact with full content
  Future<Artifact> getArtifact(String artifactId) async {
    try {
      final headers = await _getHeaders();
      final response = await _dio.get(
        '$apiBaseUrl/api/artifacts/$artifactId',
        options: Options(headers: headers),
      );
      return Artifact.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw Exception('Artifact not found');
      }
      throw Exception('Failed to load artifact: ${e.message}');
    }
  }

  /// List artifacts for a thread (without content)
  Future<List<Artifact>> listThreadArtifacts(String threadId) async {
    try {
      final headers = await _getHeaders();
      final response = await _dio.get(
        '$apiBaseUrl/api/threads/$threadId/artifacts',
        options: Options(headers: headers),
      );
      return (response.data as List)
          .map((json) => Artifact.fromJson(json))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw Exception('Thread not found');
      }
      throw Exception('Failed to load artifacts: ${e.message}');
    }
  }

  /// Export artifact and trigger download
  ///
  /// [format] must be one of: 'md', 'pdf', 'docx'
  /// Returns the filename that was downloaded.
  Future<String> exportArtifact({
    required String artifactId,
    required String format,
    required String title,
  }) async {
    try {
      final headers = await _getHeaders();
      final response = await _dio.get<List<int>>(
        '$apiBaseUrl/api/artifacts/$artifactId/export/$format',
        options: Options(
          responseType: ResponseType.bytes,
          headers: headers,
        ),
      );

      // Generate meaningful filename per PITFALL-12
      final safeName = title
          .replaceAll(RegExp(r'[^\w\s-]'), '')
          .replaceAll(RegExp(r'\s+'), '_')
          .toLowerCase();
      final date = DateTime.now().toIso8601String().split('T')[0];
      final filename = '${safeName}_$date';

      await FileSaver.instance.saveFile(
        name: filename,
        bytes: Uint8List.fromList(response.data!),
        ext: format,
        mimeType: _getMimeType(format),
      );

      return '$filename.$format';
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw Exception('Artifact not found');
      } else if (e.response?.statusCode == 500) {
        // PDF export may fail without GTK
        throw Exception('Export failed - PDF may require additional setup');
      }
      throw Exception('Export failed: ${e.message}');
    }
  }

  MimeType _getMimeType(String format) {
    switch (format) {
      case 'md':
        return MimeType.text;
      case 'pdf':
        return MimeType.pdf;
      case 'docx':
        return MimeType.microsoftWord;
      default:
        return MimeType.other;
    }
  }
}
