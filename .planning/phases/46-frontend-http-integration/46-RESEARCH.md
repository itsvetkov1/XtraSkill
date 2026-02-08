# Phase 46: Frontend HTTP Integration - Research

**Researched:** 2026-02-08
**Domain:** Flutter Dio HTTP interceptors, correlation ID headers, request/response logging
**Confidence:** HIGH

## Summary

Phase 46 integrates correlation ID tracking and HTTP logging into the Flutter frontend by creating a Dio interceptor that attaches X-Correlation-ID headers to all outgoing requests and logs request/response metadata through the existing LoggingService (created in Phase 45).

The standard approach is to create a singleton Dio instance with a custom interceptor that:
1. Generates or reuses correlation IDs per request using uuid package (already added in Phase 45)
2. Adds X-Correlation-ID to request headers in onRequest
3. Logs API calls with endpoint, method, status, and duration in onResponse/onError
4. Integrates with existing LoggingService for buffering and backend transmission

This phase builds on Phase 45's LoggingService singleton and adds a new `logApi()` method to handle HTTP-specific logging with endpoint, method, status, and duration metadata.

**Primary recommendation:** Create ApiClient singleton wrapper around Dio with custom InterceptorsWrapper (not QueuedInterceptor, since we don't need sequential processing). Refactor all existing services to use this shared instance. LogInterceptor should be added last to capture all modifications.

## Standard Stack

The established libraries/tools for HTTP logging and correlation ID tracking in Flutter:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| dio | 5.9.1 | HTTP client | Industry standard for Flutter networking, supports interceptors, FormData, timeouts |
| uuid | 4.5.2 | UUID generation | Already added in Phase 45 for session IDs, RFC-compliant v4 generation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logger | 2.6.2 | Console logging | Already added in Phase 45, used by LoggingService for debug output |
| flutter_secure_storage | 10.0.0 | JWT token storage | Already in use, accessed by services for auth headers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dio | http package | Dio provides interceptors, better error handling, FormData support built-in |
| Custom interceptor | dio_interceptor_seq package | Overkill - package designed for Seq server integration, we need simple header injection |
| InterceptorsWrapper | QueuedInterceptorsWrapper | QueuedInterceptor adds unnecessary overhead for logging - only needed for token refresh scenarios |

**Installation:**
No new dependencies needed - all packages already installed in Phase 45.

## Architecture Patterns

### Recommended Project Structure
```
lib/
├── services/
│   ├── api_client.dart        # NEW: Singleton Dio wrapper with interceptors
│   ├── logging_service.dart   # EXISTING: Add logApi() method
│   ├── auth_service.dart      # REFACTOR: Use ApiClient.dio
│   ├── project_service.dart   # REFACTOR: Use ApiClient.dio
│   └── [other services]       # REFACTOR: Use ApiClient.dio
└── core/
    └── config.dart            # EXISTING: API base URL
```

### Pattern 1: Singleton ApiClient with Dio Interceptor
**What:** Centralized Dio instance with correlation ID and logging interceptors
**When to use:** All HTTP requests should route through this singleton
**Example:**
```dart
// Source: Based on official Dio docs + community best practices
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio dio;
  final LoggingService _loggingService = LoggingService();
  final Uuid _uuid = const Uuid();

  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    // Add correlation ID + logging interceptor FIRST
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        // Generate correlation ID if not already set
        final correlationId = options.headers['X-Correlation-ID'] as String? ?? _uuid.v4();
        options.headers['X-Correlation-ID'] = correlationId;

        // Store for logging in onResponse/onError
        options.extra['correlation_id'] = correlationId;
        options.extra['start_time'] = DateTime.now().millisecondsSinceEpoch;

        handler.next(options);
      },
      onResponse: (response, handler) {
        _logRequest(response.requestOptions, response.statusCode, null);
        handler.next(response);
      },
      onError: (error, handler) {
        _logRequest(error.requestOptions, error.response?.statusCode, error);
        handler.reject(error);
      },
    ));

    // Add LogInterceptor LAST for debugging (only in debug mode)
    if (kDebugMode) {
      dio.interceptors.add(LogInterceptor(
        responseBody: false,
        requestBody: false,
        logPrint: (o) => debugPrint(o.toString()),
      ));
    }
  }

  void _logRequest(RequestOptions options, int? statusCode, DioException? error) {
    final startTime = options.extra['start_time'] as int?;
    final duration = startTime != null
        ? DateTime.now().millisecondsSinceEpoch - startTime
        : null;
    final correlationId = options.extra['correlation_id'] as String?;

    _loggingService.logApi(
      endpoint: options.path,
      method: options.method,
      statusCode: statusCode,
      durationMs: duration,
      correlationId: correlationId,
      error: error?.toString(),
    );
  }
}
```

### Pattern 2: LoggingService.logApi() Method
**What:** Add HTTP-specific logging method to existing LoggingService
**When to use:** Called by ApiClient interceptor for all requests
**Example:**
```dart
// In LoggingService class
void logApi({
  required String endpoint,
  required String method,
  int? statusCode,
  int? durationMs,
  String? correlationId,
  String? error,
}) {
  final level = error != null
      ? 'ERROR'
      : (statusCode != null && statusCode >= 400 ? 'WARNING' : 'INFO');

  final message = error != null
      ? '$method $endpoint - Error: $error'
      : '$method $endpoint ${statusCode ?? ""}';

  _log(
    level: level,
    message: message,
    category: 'api',
    metadata: {
      'endpoint': endpoint,
      'method': method,
      if (statusCode != null) 'status_code': statusCode,
      if (durationMs != null) 'duration_ms': durationMs,
      if (correlationId != null) 'correlation_id': correlationId,
      if (error != null) 'error': error,
    },
  );
}
```

### Pattern 3: Service Refactoring to Use ApiClient
**What:** Replace individual Dio instances with shared ApiClient.dio
**When to use:** All existing services (auth, project, document, thread, artifact, AI)
**Example:**
```dart
// BEFORE (current pattern):
class ProjectService {
  final Dio _dio;
  ProjectService({Dio? dio}) : _dio = dio ?? Dio();
}

// AFTER (use ApiClient):
class ProjectService {
  final Dio _dio;
  ProjectService({Dio? dio}) : _dio = dio ?? ApiClient().dio;
}
```

### Anti-Patterns to Avoid
- **Using QueuedInterceptor for logging:** Adds unnecessary sequential processing overhead. Only use for token refresh scenarios where race conditions matter.
- **Adding LogInterceptor first:** Must be added last, otherwise modifications by following interceptors won't be logged.
- **Logging in production without debugPrint wrapper:** Use `logPrint: (o) => debugPrint(o.toString())` to respect Flutter's debug/release modes.
- **Reusing correlation IDs across requests:** Each HTTP request should generate a new correlation ID (not shared with session ID).
- **Measuring duration with Stopwatch in onRequest/onResponse:** Stopwatch can log inflated durations. Use millisecondsSinceEpoch subtraction in extra data.
- **Forgetting handler.next()/handler.reject():** Interceptor chain will break if you don't call handler methods.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP request duration timing | Stopwatch in onRequest/onResponse | Store timestamp in options.extra, calculate in onResponse | Stopwatch can report inflated times (600ms vs 53ms actual). Storing start time in extra data gives accurate request-only duration. |
| Correlation ID propagation | Manual header injection per service | Dio interceptor onRequest | Interceptors guarantee all requests include the header, even ones you forget to manually add. |
| Request/response logging | print() or debugPrint() in each service | Dio's LogInterceptor + custom logging interceptor | LogInterceptor handles formatting, your interceptor handles structured logging to LoggingService. |
| Dio singleton instance | Creating Dio() in each service constructor | ApiClient singleton wrapper | Single configuration point, shared interceptors, consistent timeouts/headers across all services. |

**Key insight:** Dio interceptors are the standard solution for cross-cutting HTTP concerns (auth, logging, correlation). Don't scatter this logic across individual service classes.

## Common Pitfalls

### Pitfall 1: Using Interceptor Instead of InterceptorsWrapper
**What goes wrong:** Implementing full Interceptor class requires overriding all methods (onRequest, onResponse, onError) even if you only need one.
**Why it happens:** Developers follow examples that extend Interceptor base class.
**How to avoid:** Use InterceptorsWrapper for inline definitions - it's the recommended wrapper approach in Dio 5.9.x.
**Warning signs:** Boilerplate code with empty onRequest/onResponse/onError overrides.

### Pitfall 2: LogInterceptor Added Before Custom Interceptors
**What goes wrong:** LogInterceptor logs requests before your custom interceptor modifies them (e.g., before correlation ID is added).
**Why it happens:** Developers add LogInterceptor first when configuring Dio.
**How to avoid:** Always add LogInterceptor LAST. Official Dio docs state: "should be added last to capture all modifications by other interceptors."
**Warning signs:** Debug logs show requests without correlation ID headers, but backend receives them.

### Pitfall 3: Not Storing Correlation ID in options.extra
**What goes wrong:** Correlation ID generated in onRequest is not available in onResponse/onError for logging.
**Why it happens:** Developers assume they can access request headers in response/error callbacks.
**How to avoid:** Store correlation ID (and start time) in `options.extra` map - it's preserved throughout request lifecycle.
**Warning signs:** Logs show different correlation IDs for request start vs completion.

### Pitfall 4: Forgetting to Call handler.next() or handler.reject()
**What goes wrong:** Request hangs indefinitely without completing or failing.
**Why it happens:** Developers write conditional logic that misses calling handler methods in some branches.
**How to avoid:** Every code path in interceptor must call handler.next(), handler.resolve(), or handler.reject(). No early returns without handler calls.
**Warning signs:** App freezes on HTTP requests, timeout errors occur even for fast endpoints.

### Pitfall 5: Using print() in Interceptors for Production
**What goes wrong:** Console logs appear in production builds, exposing sensitive data.
**Why it happens:** Developers use print() or default LogInterceptor without restricting to debug mode.
**How to avoid:** Wrap LogInterceptor in `if (kDebugMode)` check, use `debugPrint()` with logPrint callback.
**Warning signs:** Production apps have verbose console output visible in release builds.

### Pitfall 6: Multiple Dio Instances with Different Configurations
**What goes wrong:** Some services have interceptors, some don't. Inconsistent timeouts. Different base URLs.
**Why it happens:** Each service creates its own Dio() instance independently.
**How to avoid:** Use ApiClient singleton pattern. Services receive Dio instance via constructor dependency injection (for testing) but default to ApiClient().dio.
**Warning signs:** Only some API calls have correlation IDs. Timeout behavior varies by service.

### Pitfall 7: Attempting to Modify Response Headers
**What goes wrong:** Trying to add X-Correlation-ID to response headers in onResponse interceptor.
**Why it happens:** Developers think client-side code can modify HTTP response headers.
**How to avoid:** Response headers come from the server - they're read-only on client. Backend middleware adds X-Correlation-ID to response headers (already done in Phase 43).
**Warning signs:** Code attempts `response.headers['X-Correlation-ID'] = id` with no effect.

## Code Examples

Verified patterns from official sources and current project structure:

### Complete ApiClient Implementation
```dart
// Source: Dio 5.9.1 official docs + Flutter best practices
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

import '../core/config.dart';
import 'logging_service.dart';

/// Singleton Dio wrapper with correlation ID and logging interceptors
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio dio;
  final LoggingService _loggingService = LoggingService();
  final Uuid _uuid = const Uuid();

  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    // Correlation ID + logging interceptor
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (RequestOptions options, RequestInterceptorHandler handler) {
        // Generate or preserve correlation ID
        final correlationId = options.headers['X-Correlation-ID'] as String? ?? _uuid.v4();
        options.headers['X-Correlation-ID'] = correlationId;

        // Store in extra for access in onResponse/onError
        options.extra['correlation_id'] = correlationId;
        options.extra['start_time'] = DateTime.now().millisecondsSinceEpoch;

        handler.next(options);
      },
      onResponse: (Response response, ResponseInterceptorHandler handler) {
        _logRequest(
          options: response.requestOptions,
          statusCode: response.statusCode,
          error: null,
        );
        handler.next(response);
      },
      onError: (DioException error, ErrorInterceptorHandler handler) {
        _logRequest(
          options: error.requestOptions,
          statusCode: error.response?.statusCode,
          error: error,
        );
        handler.reject(error);
      },
    ));

    // LogInterceptor LAST (debug mode only)
    if (kDebugMode) {
      dio.interceptors.add(LogInterceptor(
        responseBody: false,
        requestBody: false,
        logPrint: (o) => debugPrint(o.toString()),
      ));
    }
  }

  void _logRequest({
    required RequestOptions options,
    int? statusCode,
    DioException? error,
  }) {
    final startTime = options.extra['start_time'] as int?;
    final durationMs = startTime != null
        ? DateTime.now().millisecondsSinceEpoch - startTime
        : null;
    final correlationId = options.extra['correlation_id'] as String?;

    _loggingService.logApi(
      endpoint: options.path,
      method: options.method,
      statusCode: statusCode,
      durationMs: durationMs,
      correlationId: correlationId,
      error: error?.toString(),
    );
  }
}
```

### Adding logApi() to LoggingService
```dart
// In logging_service.dart - add this method to LoggingService class
/// Log API request/response (HTTP calls with timing and correlation ID)
void logApi({
  required String endpoint,
  required String method,
  int? statusCode,
  int? durationMs,
  String? correlationId,
  String? error,
}) {
  // Determine log level based on status/error
  final level = error != null
      ? 'ERROR'
      : (statusCode != null && statusCode >= 400 ? 'WARNING' : 'INFO');

  final message = error != null
      ? '$method $endpoint - Error: $error'
      : '$method $endpoint ${statusCode ?? "pending"}';

  _log(
    level: level,
    message: message,
    category: 'api',
    metadata: {
      'endpoint': endpoint,
      'method': method,
      if (statusCode != null) 'status_code': statusCode,
      if (durationMs != null) 'duration_ms': durationMs,
      if (correlationId != null) 'correlation_id': correlationId,
      if (error != null) 'error': error,
    },
  );
}
```

### Refactoring Existing Service to Use ApiClient
```dart
// BEFORE: ProjectService with own Dio instance
class ProjectService {
  final Dio _dio;
  final FlutterSecureStorage _storage;
  final String _baseUrl;

  ProjectService({
    String? baseUrl,
    Dio? dio,
    FlutterSecureStorage? storage,
  }) : _baseUrl = baseUrl ?? 'http://localhost:8000',
       _dio = dio ?? Dio(),
       _storage = storage ?? const FlutterSecureStorage();
  // ...
}

// AFTER: ProjectService using ApiClient singleton
class ProjectService {
  final Dio _dio;
  final FlutterSecureStorage _storage;

  ProjectService({
    Dio? dio,
    FlutterSecureStorage? storage,
  }) : _dio = dio ?? ApiClient().dio,
       _storage = storage ?? const FlutterSecureStorage();
  // ...
  // Note: Remove _baseUrl field - now in ApiClient's BaseOptions
  // Change requests from '$_baseUrl/api/projects' to '/api/projects'
}
```

### Testing with Custom Dio Instance
```dart
// In tests, inject mock Dio to bypass interceptors
void main() {
  test('ProjectService.getProjects returns project list', () async {
    final mockDio = MockDio();
    final service = ProjectService(dio: mockDio);
    // Test without hitting real interceptors
  });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| interceptors.lock() | QueuedInterceptor | Dio 5.x (2023+) | lock() deprecated, QueuedInterceptor is replacement for sequential processing |
| Stopwatch for timing | options.extra timestamps | Community best practice | More accurate request-only duration (avoids inflated times) |
| Each service creates Dio() | Singleton ApiClient pattern | Industry standard (2024+) | Consistent configuration, shared interceptors, easier testing |
| print() debugging | LogInterceptor with debugPrint | Dio 5.x + Flutter best practices | Respects debug/release modes, cleaner console output |
| Duration in seconds (int) | Duration objects | Dio 5.x breaking change | connectTimeout/receiveTimeout now use Duration(seconds: N) |

**Deprecated/outdated:**
- `interceptors.lock()` mechanism: Use QueuedInterceptor for sequential processing
- Integer timeout values: Use `Duration(seconds: 30)` instead of raw integers
- Manual correlation ID per service: Use interceptor for automatic injection

## Open Questions

Things that couldn't be fully resolved:

1. **Should correlation IDs be preserved across retries?**
   - What we know: Each HTTP request generates new correlation ID in onRequest
   - What's unclear: If Dio automatically retries a failed request, should it reuse the same correlation ID or generate a new one?
   - Recommendation: Current implementation generates new ID per onRequest call, which includes retries. This is acceptable - each attempt is a distinct HTTP request. If retry correlation is needed, store original ID in options.extra and reuse.

2. **How does SSE streaming (AIService) interact with interceptors?**
   - What we know: AIService uses flutter_client_sse for streaming, not Dio
   - What's unclear: Whether SSE requests should also include correlation IDs
   - Recommendation: Phase 46 focuses on Dio requests only. SSE correlation could be Phase 47 or 48 enhancement if needed.

3. **Should we log request/response bodies for debugging?**
   - What we know: LogInterceptor supports `requestBody: true` and `responseBody: true`
   - What's unclear: Whether to enable body logging in debug mode (could expose sensitive data)
   - Recommendation: Keep `requestBody: false` and `responseBody: false` even in debug mode. Bodies can contain auth tokens, personal data. If needed for debugging, enable temporarily and never commit.

## Sources

### Primary (HIGH confidence)
- [Dio 5.9.1 Official Package](https://pub.dev/packages/dio) - Interceptor types, BaseOptions, LogInterceptor configuration
- [Dio InterceptorsWrapper API](https://pub.dev/documentation/dio/latest/dio/Interceptor-class.html) - Official API documentation for interceptor implementation
- [Dio BaseOptions API](https://pub.dev/documentation/dio/latest/dio/BaseOptions-class.html) - Configuration for timeouts, headers, baseUrl

### Secondary (MEDIUM confidence)
- [Using Dio Interceptors for Logging in Flutter](https://tillitsdone.com/blogs/dio-interceptors-in-flutter-guide/) - Best practices for logging interceptors
- [Dio Interceptors in Flutter (Flutter Community)](https://medium.com/flutter-community/dio-interceptors-in-flutter-17be4214f363) - Community patterns for interceptor implementation
- [Implementing a Singleton Dio Client in Flutter](https://medium.com/@imaakashagrawal/implementing-a-singleton-dio-client-in-flutter-with-error-handling-retry-logic-and-debounce-ae7aa2f0f502) - Singleton pattern with error handling
- [Efficient Refresh Token Handling with Queued Interceptors](https://medium.com/@muhammad.kuifatieh/efficient-refresh-token-handling-in-dio-with-queued-interceptors-cc846dfdebf9) - When to use QueuedInterceptor vs Interceptor

### Tertiary (LOW confidence)
- [Track request duration GitHub issue](https://github.com/cfug/dio/issues/2027) - Community discussion on timing measurement (unresolved, no official solution)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Dio 5.9.1 is current stable, uuid already in project
- Architecture: HIGH - ApiClient singleton pattern is industry standard, verified with official Dio docs
- Pitfalls: HIGH - Based on official docs, GitHub issues, and community articles with concrete examples

**Research date:** 2026-02-08
**Valid until:** ~30 days (Dio is stable, breaking changes unlikely)
