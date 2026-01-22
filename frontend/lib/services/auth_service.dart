/// OAuth authentication service for Google and Microsoft providers.
library;

import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:url_launcher/url_launcher.dart';

/// Authentication service handling OAuth flows and token management
class AuthService {
  /// HTTP client for API requests
  final Dio _dio;

  /// Secure storage for JWT tokens
  final FlutterSecureStorage _storage;

  /// Backend API base URL
  final String _baseUrl;

  AuthService({
    String? baseUrl,
    Dio? dio,
    FlutterSecureStorage? storage,
  })  : _baseUrl = baseUrl ?? 'http://localhost:8002',
        _dio = dio ?? Dio(),
        _storage = storage ?? const FlutterSecureStorage();

  /// Storage key for JWT token
  static const String _tokenKey = 'auth_token';

  /// Login with Google OAuth provider
  ///
  /// Opens browser for OAuth consent, waits for callback with token.
  /// Token is stored securely and returned.
  ///
  /// Returns JWT token string
  /// Throws exception if OAuth flow fails
  Future<String> loginWithGoogle() async {
    return _performOAuthLogin('google');
  }

  /// Login with Microsoft OAuth provider
  ///
  /// Opens browser for OAuth consent, waits for callback with token.
  /// Token is stored securely and returned.
  ///
  /// Returns JWT token string
  /// Throws exception if OAuth flow fails
  Future<String> loginWithMicrosoft() async {
    return _performOAuthLogin('microsoft');
  }

  /// Internal OAuth flow implementation
  Future<String> _performOAuthLogin(String provider) async {
    try {
      // Step 1: Get authorization URL from backend
      final response = await _dio.post(
        '$_baseUrl/auth/$provider/initiate',
      );

      final authUrl = response.data['auth_url'] as String;
      // State is stored on backend for CSRF validation

      // Step 2: Launch browser with authorization URL
      final uri = Uri.parse(authUrl);
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        throw Exception('Could not launch OAuth URL');
      }

      // Step 3: Token will be delivered via callback redirect
      // In real implementation, this would wait for deep link callback
      // For MVP web flow, user will be redirected back to app with token
      // The callback screen handles token extraction and storage

      // Return empty string - actual token handled by callback screen
      // This is just to maintain function signature
      return '';
    } catch (e) {
      throw Exception('OAuth login failed: $e');
    }
  }

  /// Store JWT token in secure storage
  Future<void> storeToken(String token) async {
    print('DEBUG AuthService: Storing token (length: ${token.length})');
    await _storage.write(key: _tokenKey, value: token);
    print('DEBUG AuthService: Token stored successfully');
  }

  /// Retrieve stored JWT token
  ///
  /// Returns token string if found, null otherwise
  Future<String?> getStoredToken() async {
    final token = await _storage.read(key: _tokenKey);
    print('DEBUG AuthService: Retrieved token: ${token != null ? "Found (${token.length} chars)" : "NULL"}');
    return token;
  }

  /// Check if stored token is valid
  ///
  /// Validates token expiration by decoding JWT payload
  ///
  /// Returns true if token exists and is not expired
  Future<bool> isTokenValid() async {
    final token = await getStoredToken();
    if (token == null) return false;

    try {
      // Decode JWT payload (middle segment between dots)
      final parts = token.split('.');
      if (parts.length != 3) return false;

      // Decode base64 payload
      final payload = parts[1];
      final normalized = base64Url.normalize(payload);
      final decoded = utf8.decode(base64Url.decode(normalized));
      final payloadMap = json.decode(decoded) as Map<String, dynamic>;

      // Check expiration
      final exp = payloadMap['exp'] as int?;
      if (exp == null) return false;

      final expiryDate = DateTime.fromMillisecondsSinceEpoch(exp * 1000);
      return DateTime.now().isBefore(expiryDate);
    } catch (e) {
      return false;
    }
  }

  /// Get current authenticated user information
  ///
  /// Requires valid JWT token in storage
  ///
  /// Returns user data map with id, email, oauth_provider
  /// Throws exception if token invalid or request fails
  Future<Map<String, dynamic>> getCurrentUser() async {
    final token = await getStoredToken();
    if (token == null) {
      throw Exception('No authentication token found');
    }

    try {
      final response = await _dio.get(
        '$_baseUrl/auth/me',
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
          },
        ),
      );

      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to get user info: $e');
    }
  }

  /// Logout current user
  ///
  /// Deletes JWT token from secure storage
  /// Optionally calls backend logout endpoint (stateless, for consistency)
  Future<void> logout() async {
    // Delete token from storage
    await _storage.delete(key: _tokenKey);

    // Optional: Call backend logout endpoint
    try {
      await _dio.post('$_baseUrl/auth/logout');
    } catch (e) {
      // Ignore backend errors - token already deleted locally
    }
  }
}
