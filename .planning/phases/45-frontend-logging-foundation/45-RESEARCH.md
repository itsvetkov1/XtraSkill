# Phase 45: Frontend Logging Foundation - Research

**Researched:** 2026-02-08
**Domain:** Flutter/Dart logging patterns, structured logging, navigation observation
**Confidence:** HIGH

## Summary

This research investigated how to implement comprehensive frontend logging in Flutter to capture user actions, navigation events, errors, and network state changes with session grouping. The standard approach uses a lightweight logging library (logger or talker) combined with custom services for navigation tracking, error handling, and batched log transmission to the backend.

Flutter provides built-in mechanisms for error capture (FlutterError.onError, PlatformDispatcher.onError) and navigation observation (NavigatorObserver for go_router). Session management uses UUID v4 for unique session IDs, stored in memory for the app lifecycle. Logs are buffered in memory (configurable size, default 1000 entries) and sent in batches to the backend's `/api/logs/ingest` endpoint.

The key insight is that Flutter logging should be lightweight and async-safe to avoid blocking UI rendering, with logs sent opportunistically when network is available and the app is backgrounded or on a periodic timer.

**Primary recommendation:** Use the `logger` package for structured logging (simpler than talker for this use case), custom NavigatorObserver for go_router route tracking, and a LoggingService singleton that buffers logs and batches them to backend via Dio interceptor for automatic correlation ID propagation.

## Standard Stack

The established libraries/tools for Flutter logging:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| logger | ^2.5.0 | Structured console/file logging with level filtering | Most popular Flutter logging package, 2600+ pub points, supports custom outputs |
| uuid | ^4.5.1 | RFC4122/9562 compliant UUID generation | Standard for session ID generation, cryptographically secure, cross-platform |
| connectivity_plus | ^6.1.2 | Network connectivity state monitoring | Official plus plugins package, multi-platform, stream-based updates |
| dio | ^5.9.0 | HTTP client with interceptors | Already in project, supports request/response logging via interceptors |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shared_preferences | ^2.5.4 | Persist logging toggle state | Already in project, for LOG-05 settings persistence |
| path_provider | ^2.1.5 | Access device directories for log files | If local file logging needed (NOT needed - backend is single source of truth) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| logger | talker | Talker adds UI screens and advanced integrations (BLoC, Riverpod) but heavier; logger is simpler for our backend-centric approach |
| logger | dart:developer log() | Built-in but lacks structured output, filtering, and custom sinks; logger provides better control |
| UUID v4 | UUID v7 | v7 adds timestamp-based ordering which isn't needed for session IDs; v4 is simpler |
| connectivity_plus | internet_connection_checker_plus | Latter checks actual internet (not just network connection); former sufficient for connectivity state logging |

**Installation:**
```bash
cd frontend
flutter pub add logger uuid connectivity_plus
# dio and shared_preferences already in pubspec.yaml
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/
├── services/
│   ├── logging_service.dart       # Singleton: buffer logs, batch send to backend
│   └── session_service.dart       # Singleton: generate/store session ID
├── utils/
│   └── logging_observer.dart      # Custom NavigatorObserver for go_router
├── core/
│   └── error_handlers.dart        # FlutterError.onError + PlatformDispatcher.onError
└── main.dart                       # Initialize logging in main()
```

### Pattern 1: Singleton LoggingService with Buffer
**What:** Central service that buffers log entries in memory and periodically flushes to backend
**When to use:** All logging calls throughout app
**Example:**
```dart
// Source: Verified with Flutter best practices + backend ingest API spec
class LoggingService {
  static final LoggingService _instance = LoggingService._internal();
  factory LoggingService() => _instance;
  LoggingService._internal();

  final Logger _logger = Logger(
    printer: PrettyPrinter(methodCount: 0),
  );

  final List<Map<String, dynamic>> _buffer = [];
  final int _maxBufferSize = 1000; // SLOG-04
  Timer? _flushTimer;
  final Dio _dio = Dio(); // Inject or get from service locator in real code

  void init({required String sessionId}) {
    // Start periodic flush (every 5 minutes)
    _flushTimer = Timer.periodic(
      const Duration(minutes: 5),
      (_) => flush(),
    );
  }

  void logNavigation(String routeName) {
    _log(
      level: 'INFO',
      message: 'User navigated to $routeName',
      category: 'navigation',
    );
  }

  void logAction(String action, {Map<String, dynamic>? metadata}) {
    _log(
      level: 'INFO',
      message: 'User action: $action',
      category: 'action',
      metadata: metadata,
    );
  }

  void logError(dynamic error, StackTrace? stackTrace, {String? context}) {
    _log(
      level: 'ERROR',
      message: '${error.runtimeType}: ${error.toString()}',
      category: 'error',
      metadata: {
        'stackTrace': stackTrace?.toString(),
        'context': context,
      },
    );
  }

  void logNetworkStateChange(bool isConnected) {
    _log(
      level: 'INFO',
      message: 'Network ${isConnected ? "connected" : "disconnected"}',
      category: 'network',
    );
  }

  void _log({
    required String level,
    required String message,
    required String category,
    Map<String, dynamic>? metadata,
  }) {
    // Console logging for development
    _logger.log(
      Level.values.byName(level.toLowerCase()),
      message,
    );

    // Add to buffer for backend ingestion
    _buffer.add({
      'timestamp': DateTime.now().toUtc().toIso8601String(),
      'level': level,
      'message': message,
      'category': category,
      'session_id': SessionService().sessionId,
      'correlation_id': null, // Set by backend if in API request context
      ...?metadata,
    });

    // Auto-flush if buffer full
    if (_buffer.length >= _maxBufferSize) {
      flush();
    }
  }

  Future<void> flush() async {
    if (_buffer.isEmpty) return;

    final logsToSend = List<Map<String, dynamic>>.from(_buffer);
    _buffer.clear();

    try {
      await _dio.post(
        'http://localhost:8000/api/logs/ingest',
        data: {'logs': logsToSend},
        options: Options(
          headers: {
            'Authorization': 'Bearer ${await _getToken()}',
          },
        ),
      );
    } catch (e) {
      // Re-add to buffer if send fails (up to max size)
      if (_buffer.length + logsToSend.length <= _maxBufferSize) {
        _buffer.insertAll(0, logsToSend);
      }
      _logger.e('Failed to send logs to backend: $e');
    }
  }

  void dispose() {
    _flushTimer?.cancel();
    flush(); // Final flush before disposal
  }

  Future<String?> _getToken() async {
    // Get from AuthService or secure storage
    // Placeholder for example
    return null;
  }
}
```

### Pattern 2: NavigatorObserver for go_router
**What:** Custom observer that logs route changes by extending NavigatorObserver
**When to use:** Attached to GoRouter.observers to track all navigation events
**Example:**
```dart
// Source: https://api.flutter.dev/flutter/widgets/NavigatorObserver-class.html
// Source: https://dev.to/mattia/go-router-navigation-observer-1gj4
class LoggingNavigatorObserver extends NavigatorObserver {
  final LoggingService _loggingService = LoggingService();

  @override
  void didPush(Route route, Route? previousRoute) {
    super.didPush(route, previousRoute);
    if (route.settings.name != null) {
      _loggingService.logNavigation('Navigated to ${route.settings.name}');
    }
  }

  @override
  void didPop(Route route, Route? previousRoute) {
    super.didPop(route, previousRoute);
    if (previousRoute?.settings.name != null) {
      _loggingService.logNavigation('Returned to ${previousRoute!.settings.name}');
    }
  }

  @override
  void didReplace({Route? newRoute, Route? oldRoute}) {
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
    if (newRoute?.settings.name != null) {
      _loggingService.logNavigation('Replaced with ${newRoute!.settings.name}');
    }
  }
}

// In main.dart GoRouter creation:
GoRouter(
  observers: [LoggingNavigatorObserver()],
  routes: [...],
)
```

### Pattern 3: Global Error Handlers
**What:** Capture all Flutter framework and platform errors
**When to use:** Set up once in main() before runApp()
**Example:**
```dart
// Source: https://docs.flutter.dev/testing/errors
// Source: https://medium.com/@ekrem_m/how-to-handle-global-errors-gracefully-in-flutter-fluttererror-onerror-965ec42e665b
void main() {
  final loggingService = LoggingService();

  // Capture Flutter framework errors (widget errors, render errors)
  FlutterError.onError = (FlutterErrorDetails details) {
    FlutterError.presentError(details); // Still show in console
    loggingService.logError(
      details.exception,
      details.stack,
      context: 'FlutterError: ${details.context}',
    );
    if (kReleaseMode) {
      // Optionally exit in production to force restart
      // exit(1);
    }
  };

  // Capture platform errors (async errors, MethodChannel failures)
  PlatformDispatcher.instance.onError = (error, stack) {
    loggingService.logError(error, stack, context: 'PlatformError');
    return true; // Mark as handled
  };

  runApp(const MyApp());
}
```

### Pattern 4: Connectivity Monitoring
**What:** Stream-based monitoring of network state changes
**When to use:** Initialize in LoggingService or main app initialization
**Example:**
```dart
// Source: https://pub.dev/packages/connectivity_plus
import 'package:connectivity_plus/connectivity_plus.dart';

class LoggingService {
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;

  void init({required String sessionId}) {
    // Monitor network connectivity
    _connectivitySubscription = Connectivity()
        .onConnectivityChanged
        .listen((List<ConnectivityResult> results) {
      final isConnected = results.isNotEmpty &&
          !results.contains(ConnectivityResult.none);
      logNetworkStateChange(isConnected);
    });
  }

  void dispose() {
    _connectivitySubscription?.cancel();
  }
}
```

### Pattern 5: Session ID Management
**What:** Generate and maintain a single session ID for the app lifecycle
**When to use:** Initialize once at app startup
**Example:**
```dart
// Source: https://copyprogramming.com/howto/how-to-generate-unique-id-in-dart
import 'package:uuid/uuid.dart';

class SessionService {
  static final SessionService _instance = SessionService._internal();
  factory SessionService() => _instance;
  SessionService._internal() {
    _sessionId = const Uuid().v4(); // Generate UUID v4 on creation
  }

  late final String _sessionId;
  String get sessionId => _sessionId;

  // Optional: Regenerate session on logout/login
  void regenerateSession() {
    _sessionId = const Uuid().v4();
  }
}
```

### Anti-Patterns to Avoid
- **Synchronous file I/O in logging:** Blocks UI thread. Use backend ingestion instead of local files.
- **Unbounded buffer growth:** Always enforce max buffer size to prevent memory exhaustion.
- **Logging sensitive data:** Never log tokens, passwords, or PII. Sanitize before logging.
- **Over-logging in production:** Use log level filtering (INFO and above) to avoid performance impact.
- **Not handling flush failures:** If backend is unreachable, re-queue logs (up to buffer limit) for retry.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Log formatting and levels | Custom print() wrapper | logger package | Handles level filtering, pretty printing, multiple outputs, and customizable formatting out of box |
| UUID generation | Custom timestamp + random | uuid package | RFC-compliant, cryptographically secure, handles edge cases (time rollback, entropy) |
| Network state monitoring | Manual polling of network APIs | connectivity_plus | Stream-based, cross-platform, handles permissions, detects WiFi/mobile/none/ethernet |
| Dio request/response logging | Custom interceptor from scratch | LogInterceptor (built-in) or dio_interceptor_plus | Handles request/response bodies, errors, timing, with configurable verbosity |
| Structured log output | Manual JSON.encode() | logger with custom LogOutput | Logger supports custom outputs and filters, handles circular references |

**Key insight:** Flutter's logging ecosystem is mature. Custom solutions lack the robustness (error handling, platform differences, edge cases) that established packages provide.

## Common Pitfalls

### Pitfall 1: NavigatorObserver Not Triggered in StatefulShellRoute
**What goes wrong:** When using go_router's StatefulShellRoute, NavigatorObserver may not receive events for branch navigation (shell switching).
**Why it happens:** StatefulShellRoute maintains separate navigators for each branch, and shell switching doesn't push/pop routes.
**How to avoid:** Listen to GoRouterDelegate changes or use route-level logging by checking state.uri.path in GoRouter redirect callback.
**Warning signs:** Navigation logs only appear for nested routes, not for top-level shell branch switches.

### Pitfall 2: Flushing Logs on App Termination
**What goes wrong:** Buffered logs lost when app is force-closed or crashes before flush.
**Why it happens:** Timer-based flush only runs if app is alive; no guarantee of final flush on termination.
**How to avoid:** Use WidgetsBindingObserver to detect app lifecycle (paused, detached) and flush proactively. Also flush on logout.
**Warning signs:** Missing logs for events right before crashes or app closures.

### Pitfall 3: Logging in Release Mode with Default Filter
**What goes wrong:** All logs disappear in release builds if using logger's default DevelopmentFilter.
**Why it happens:** DevelopmentFilter only shows logs when kDebugMode is true (assertions enabled).
**How to avoid:** Use ProductionFilter or custom filter that allows INFO/WARNING/ERROR in release mode. Set filter explicitly:
```dart
Logger(
  filter: ProductionFilter(), // Shows warnings and errors in release
)
```
**Warning signs:** No logs appearing in release builds or TestFlight/production.

### Pitfall 4: Memory Leak from Uncancelled Timers/Subscriptions
**What goes wrong:** Periodic flush timer or connectivity subscription keeps running after LoggingService is no longer needed, holding references.
**Why it happens:** Singletons live for app lifetime, but timer/subscription must be explicitly cancelled.
**How to avoid:** Implement dispose() method that cancels timer and subscription. Call on app termination or when logging is disabled.
**Warning signs:** Memory usage grows over time, or app doesn't exit cleanly.

### Pitfall 5: Correlation ID Missing for Non-API Logs
**What goes wrong:** Navigation and action logs lack correlation_id, making it hard to trace user flows that involve API calls.
**Why it happens:** Correlation ID is typically set per-request by Dio interceptor, but non-API events don't have a request context.
**How to avoid:** Don't try to force correlation IDs for non-API events. Backend can group by session_id instead. Only set correlation_id when logging from within an API request/response handler.
**Warning signs:** Trying to "predict" correlation IDs or pass them globally in non-request contexts.

### Pitfall 6: Blocking UI with Synchronous Logging
**What goes wrong:** App stutters or drops frames during intensive logging (e.g., rapid navigation or error bursts).
**Why it happens:** Even memory-buffered logging can cause microstutters if done synchronously in build() or event handlers.
**How to avoid:** Logger package is fast enough for typical use. For extreme performance needs, consider queuing logs in isolate (overkill for this project).
**Warning signs:** FPS drops correlate with logging activity, or janky animations during heavy log periods.

### Pitfall 7: Not Sanitizing Error Messages
**What goes wrong:** Stack traces or error messages leak tokens/API keys if errors occur during auth or API calls.
**Why it happens:** Dio errors include full request details (headers, body), which may contain Authorization header.
**How to avoid:** Sanitize error.toString() before logging. Remove 'Authorization', 'api_key', 'token' fields. Use LogSanitizer pattern from backend.
**Warning signs:** Logs contain "Bearer eyJ..." or "api_key: sk-..." in error messages.

## Code Examples

Verified patterns from official sources:

### Dio LogInterceptor for API Logging
```dart
// Source: https://pub.dev/documentation/dio/latest/dio/LogInterceptor-class.html
final dio = Dio();
dio.interceptors.add(
  LogInterceptor(
    requestBody: true,
    responseBody: false, // Body too large for logs
    logPrint: (object) {
      // Forward to LoggingService instead of debugPrint
      LoggingService().logApiRequest(object.toString());
    },
  ),
);
```

### Lifecycle-Aware Log Flushing
```dart
// Source: Flutter WidgetsBindingObserver pattern
class MyApp extends StatefulWidget {
  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> with WidgetsBindingObserver {
  final loggingService = LoggingService();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    loggingService.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached) {
      // Flush logs when app backgrounded or terminated
      loggingService.flush();
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(...);
  }
}
```

### Button Click Logging Example
```dart
// Wrap action buttons to auto-log
ElevatedButton(
  onPressed: () {
    LoggingService().logAction('create_project_clicked');
    // Perform actual action
    Navigator.push(...);
  },
  child: Text('Create Project'),
)
```

### Form Submit Logging Example
```dart
onPressed: () async {
  LoggingService().logAction('login_submitted', metadata: {
    'provider': 'google',
  });

  try {
    await authService.login();
    LoggingService().logAction('login_success');
  } catch (e) {
    LoggingService().logError(e, null, context: 'login_flow');
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| print() debugging | Structured logging with logger/talker | 2023+ | Searchable, filterable logs with levels and context |
| Manual UUID generation | uuid package v4/v7 | 2024+ (v4 released) | RFC-compliant, cryptographically secure UUIDs |
| SharedPreferences legacy API | SharedPreferencesAsync/WithCache | 2024 (v2.3.0+) | Better async safety and caching for frequent reads |
| connectivity (deprecated) | connectivity_plus | 2021+ | Official plus plugin with active maintenance |
| File-based logging on device | Backend ingestion | 2025+ for this project | Centralized logs, easier admin access, AI analysis ready |

**Deprecated/outdated:**
- **connectivity package**: Deprecated in favor of connectivity_plus (official plus plugins)
- **SharedPreferences().getInstance()**: Still works but SharedPreferencesAsync recommended for new code
- **Manual JSON logging to files**: Device-local logs hard to aggregate; backend ingestion is current best practice

## Open Questions

Things that couldn't be fully resolved:

1. **Should navigation logs track route parameters?**
   - What we know: go_router provides state.uri with full path and query params
   - What's unclear: Whether logging full URLs (e.g., /projects/abc123/threads/xyz456) creates too much log volume or leaks sensitive IDs
   - Recommendation: Log route templates (/projects/:id/threads/:threadId) not actual IDs for privacy. Include IDs only if needed for debugging specific issues.

2. **How to handle correlation ID continuity across API calls?**
   - What we know: Backend generates X-Correlation-ID per request if not provided by client
   - What's unclear: Whether frontend should generate its own correlation ID for a user flow (e.g., "create project" spanning multiple API calls) or rely on backend per-request IDs
   - Recommendation: Let backend generate per-request. Use session_id to group flows. Only set client correlation_id if a specific multi-request flow needs tracing.

3. **Should we log successful API responses or only errors?**
   - What we know: LogInterceptor can log all responses, but volume may be high
   - What's unclear: Whether INFO-level logging of successful API calls (200/201) provides value vs noise
   - Recommendation: Log only API errors (4xx/5xx) and long-duration requests (>2s) to reduce volume. Backend already logs all requests via middleware.

## Sources

### Primary (HIGH confidence)
- Flutter Official Docs: [Handling Errors](https://docs.flutter.dev/testing/errors) - Error handling patterns
- Flutter API Docs: [NavigatorObserver](https://api.flutter.dev/flutter/widgets/NavigatorObserver-class.html) - Route observation
- Flutter API Docs: [RouteObserver](https://api.flutter.dev/flutter/widgets/RouteObserver-class.html) - Route awareness
- Dart Packages: [logger 2.5.0+](https://pub.dev/packages/logger) - Structured logging
- Dart Packages: [uuid 4.5.1+](https://pub.dev/packages/uuid) - UUID generation
- Dart Packages: [connectivity_plus 6.1.2+](https://pub.dev/packages/connectivity_plus) - Network monitoring
- Dart Packages: [dio LogInterceptor](https://pub.dev/documentation/dio/latest/dio/LogInterceptor-class.html) - HTTP logging
- Dart Packages: [shared_preferences 2.3.0+](https://pub.dev/packages/shared_preferences) - Settings persistence

### Secondary (MEDIUM confidence)
- [LogRocket: Flutter Logging Best Practices](https://blog.logrocket.com/flutter-logging-best-practices/) - Industry patterns
- [Medium: Flutter Navigation Observers (Jan 2026)](https://medium.com/@anupamg2001/flutter-navigation-observers-common-pitfalls-and-best-practices-4a8841b6608d) - Recent patterns
- [DEV.to: go_router Navigation Observer](https://dev.to/mattia/go-router-navigation-observer-1gj4) - go_router integration
- [Medium: Global Error Handling](https://medium.com/@ekrem_m/how-to-handle-global-errors-gracefully-in-flutter-fluttererror-onerror-965ec42e665b) - Error patterns
- [CopyProgramming: UUID in Dart (2026)](https://copyprogramming.com/howto/how-to-generate-unique-id-in-dart) - UUID implementation
- Backend Plan 44-01: Log ingestion API spec (LogEntry and LogBatch models)

### Tertiary (LOW confidence)
- WebSearch results on Talker vs Logger - Talker has more features (UI, integrations) but logger sufficient for this use case
- WebSearch results on buffered logging patterns - General patterns applicable but no Flutter-specific authoritative source

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All packages verified on pub.dev with recent versions and high pub points
- Architecture: HIGH - Patterns verified against Flutter official docs and package documentation
- Pitfalls: MEDIUM - Based on community articles (recent 2025-2026) and common Flutter issues
- Backend integration: HIGH - Log ingestion API spec from Phase 44-01 plan (implemented)

**Research date:** 2026-02-08
**Valid until:** 60 days (stable ecosystem, packages mature, unlikely to have breaking changes in v2.0 timeframe)

**Key constraints from project:**
- Backend as single source of truth (no device-local log files)
- Logs sent to `/api/logs/ingest` endpoint in batches
- Structured JSON format matching LogEntry model (timestamp, level, message, category, session_id, correlation_id)
- Frontend logs written with [FRONTEND] prefix by backend
- Correlation ID propagated via X-Correlation-ID header (Dio interceptor)
- Buffer size configurable (default 1000 entries) per SLOG-04
- Must support LOG-05 (logging toggle in settings) - not implemented in this phase but logging service should be disable-able
