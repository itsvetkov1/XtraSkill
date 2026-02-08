/// Singleton API client with Dio interceptor for correlation ID tracking and logging.
///
/// All HTTP requests route through this client to ensure:
/// - X-Correlation-ID header on every request (for backend log tracing)
/// - API call logging with endpoint, method, status, duration
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

import '../core/config.dart';
import 'logging_service.dart';

/// Singleton API client with shared Dio instance
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();

  /// Factory constructor returns singleton instance
  factory ApiClient() => _instance;

  /// Dio HTTP client with configured interceptors
  late final Dio dio;

  /// Private constructor initializes Dio with interceptors
  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    // Add correlation ID and logging interceptor FIRST
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          // Generate correlation ID for request tracing
          final correlationId = const Uuid().v4();
          options.headers['X-Correlation-ID'] = correlationId;

          // Store in extra for response/error handlers
          options.extra['correlation_id'] = correlationId;
          options.extra['start_time'] = DateTime.now().millisecondsSinceEpoch;

          handler.next(options);
        },
        onResponse: (response, handler) {
          _logApiCall(
            response.requestOptions,
            response.statusCode,
            null,
          );
          handler.next(response);
        },
        onError: (error, handler) {
          _logApiCall(
            error.requestOptions,
            error.response?.statusCode,
            error,
          );
          handler.reject(error);
        },
      ),
    );

    // Add debug LogInterceptor LAST (only in debug mode)
    if (kDebugMode) {
      dio.interceptors.add(
        LogInterceptor(
          responseBody: false,
          requestBody: false,
          logPrint: (o) => debugPrint(o.toString()),
        ),
      );
    }
  }

  /// Log API call with timing and correlation ID
  void _logApiCall(
    RequestOptions options,
    int? statusCode,
    DioException? error,
  ) {
    final startTime = options.extra['start_time'] as int?;
    final durationMs = startTime != null
        ? DateTime.now().millisecondsSinceEpoch - startTime
        : null;
    final correlationId = options.extra['correlation_id'] as String?;

    LoggingService().logApi(
      endpoint: options.path,
      method: options.method,
      statusCode: statusCode,
      durationMs: durationMs,
      correlationId: correlationId,
      error: error?.message,
    );
  }
}
