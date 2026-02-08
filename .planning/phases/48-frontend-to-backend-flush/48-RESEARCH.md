# Phase 48: Frontend-to-Backend Flush - Research

**Researched:** 2026-02-08
**Domain:** Flutter app lifecycle + HTTP log batching
**Confidence:** HIGH

## Summary

This phase implements the log flushing mechanism that sends buffered frontend logs to the backend for centralized storage. The existing infrastructure is well-prepared:

- **LoggingService** already buffers logs (max 1000 entries) with correct fields (timestamp, level, message, category, session_id)
- **Backend /api/logs/ingest** endpoint exists and validates LogBatch with max 1000 entries
- **ApiClient** singleton provides authenticated HTTP with correlation IDs

The implementation requires:
1. A `flush()` method that POSTs buffered logs to backend
2. `Timer.periodic` for 5-minute interval flush
3. `AppLifecycleListener` for pause/terminate flush
4. Optional persistence fallback if flush fails (deferred complexity decision)

**Primary recommendation:** Use `AppLifecycleListener` (Flutter 3.13+) for lifecycle events and `Timer.periodic` for interval flush. Keep in-memory only for Phase 48 (no persistence layer) to maintain simplicity.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flutter | 3.13+ | AppLifecycleListener | Native lifecycle API, cleaner than WidgetsBindingObserver mixin |
| dart:async | built-in | Timer.periodic | Standard interval mechanism, already used in logging_service.dart |
| Dio | ^5.9.0 | HTTP POST to backend | Already in use via ApiClient singleton |
| flutter_secure_storage | ^10.0.0 | JWT token retrieval | Already in use for authentication |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shared_preferences | ^2.5.4 | Flush interval config | Already available, store user preference |
| connectivity_plus | ^6.1.2 | Network state check | Already wired in LoggingService, check before flush |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AppLifecycleListener | WidgetsBindingObserver mixin | WidgetsBindingObserver requires mixin on StatefulWidget, AppLifecycleListener is standalone and cleaner |
| In-memory buffer | flutter_persistent_queue | Adds complexity, unnecessary for pilot phase |
| Timer.periodic | Ticker | Ticker is for UI animations, Timer is correct for background tasks |

**Installation:**
No new dependencies needed - all required packages already in pubspec.yaml.

## Architecture Patterns

### Recommended Component Structure

```
frontend/lib/services/
├── logging_service.dart     # Add flush() method and lifecycle binding
└── api_client.dart          # Already handles authentication
```

### Pattern 1: Lifecycle-Aware Service

**What:** LoggingService creates AppLifecycleListener to respond to pause/detach events
**When to use:** When a singleton service needs lifecycle awareness without being a widget
**Example:**

```dart
// Source: Flutter API docs - AppLifecycleListener class
class LoggingService {
  AppLifecycleListener? _lifecycleListener;

  void init() {
    // Existing connectivity monitoring...

    // Lifecycle listener for flush-on-pause
    _lifecycleListener = AppLifecycleListener(
      onPause: _onAppPause,
      onDetach: _onAppDetach,
    );

    // Periodic timer
    _flushTimer = Timer.periodic(
      Duration(minutes: _flushIntervalMinutes),
      (_) => flush(),
    );
  }

  void _onAppPause() {
    // Flush synchronously before app goes to background
    flush();
  }

  void _onAppDetach() {
    // Final flush before app terminates
    flush();
  }

  void dispose() {
    _lifecycleListener?.dispose();
    _flushTimer?.cancel();
  }
}
```

### Pattern 2: Authenticated Log Flush

**What:** Flush method gets auth token, POSTs log batch, clears buffer on success
**When to use:** For any authenticated batch operation
**Example:**

```dart
// Follows existing service patterns (document_service.dart, thread_service.dart)
Future<void> flush() async {
  if (_buffer.isEmpty) return;
  if (!_isEnabled) return;

  // Check network connectivity first
  final connectivity = await Connectivity().checkConnectivity();
  if (connectivity.contains(ConnectivityResult.none)) {
    // No network - keep buffer for next attempt
    return;
  }

  try {
    final token = await _storage.read(key: 'auth_token');
    if (token == null) {
      // Not authenticated - keep buffer for later
      return;
    }

    // Copy buffer to send (in case new logs added during POST)
    final logsToSend = List<Map<String, dynamic>>.from(_buffer);

    await ApiClient().dio.post(
      '/api/logs/ingest',
      data: {'logs': logsToSend},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );

    // Success - remove sent logs from buffer
    _buffer.removeRange(0, logsToSend.length);
  } catch (e) {
    // Flush failed - keep logs for retry
    // Silent fail - don't spam console with flush errors
  }
}
```

### Pattern 3: Configurable Flush Interval

**What:** Store flush interval in SharedPreferences, allow user adjustment
**When to use:** When configuration should persist and potentially be user-controlled
**Example:**

```dart
class LoggingConfig {
  static const String _flushIntervalKey = 'log_flush_interval_minutes';
  static const int _defaultIntervalMinutes = 5;

  static Future<int> getFlushInterval(SharedPreferences prefs) async {
    return prefs.getInt(_flushIntervalKey) ?? _defaultIntervalMinutes;
  }

  static Future<void> setFlushInterval(SharedPreferences prefs, int minutes) async {
    await prefs.setInt(_flushIntervalKey, minutes);
  }
}
```

### Anti-Patterns to Avoid

- **Blocking flush on app terminate:** App may be killed before async operation completes. Use fire-and-forget with short timeout.
- **Retrying indefinitely:** If backend is down, don't block the buffer. Cap retries and accept data loss gracefully.
- **Logging flush errors to LoggingService:** Creates infinite loop. Use debugPrint for flush debugging.
- **Flushing when not authenticated:** User may not be logged in. Silent fail and keep buffer.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Lifecycle callbacks | StatefulWidget mixin | AppLifecycleListener | Cleaner API, works with non-widget services |
| Periodic execution | Custom async loop | Timer.periodic | Handles cancellation, well-tested |
| HTTP retries | Manual retry loop | dio_smart_retry (optional) | Handles exponential backoff correctly |
| Network check | Polling connectivity | connectivity_plus stream | Already subscribed in LoggingService |

**Key insight:** The existing infrastructure handles most complexity. Focus on wiring flush() into lifecycle events and timer, not building new abstractions.

## Common Pitfalls

### Pitfall 1: Timer Not Cancelled on Dispose

**What goes wrong:** Timer keeps firing after app closes, causing resource leaks
**Why it happens:** Forgetting to call timer?.cancel() in dispose()
**How to avoid:** Always pair Timer.periodic with cancel() in dispose() - already structured in current code
**Warning signs:** Console errors about setState on disposed widget (though service is not a widget)

### Pitfall 2: Buffer Mutation During Flush

**What goes wrong:** New logs added while POST in-flight, then entire buffer cleared
**Why it happens:** async flush() doesn't protect against concurrent _log() calls
**How to avoid:** Copy buffer before sending, then remove only sent items:
```dart
final logsToSend = List<Map<String, dynamic>>.from(_buffer);
await post(logsToSend);
_buffer.removeRange(0, logsToSend.length);
```
**Warning signs:** Missing logs between flush cycles

### Pitfall 3: Flush During Background Causes Crash

**What goes wrong:** iOS kills app during long network request in background
**Why it happens:** iOS aggressively terminates background work after ~30 seconds
**How to avoid:** Set short timeout (5-10 seconds) on flush POST. Accept data loss over crash.
**Warning signs:** App crashes when returning from background

### Pitfall 4: Infinite Error Loop

**What goes wrong:** Flush error logged to LoggingService, triggers new log, triggers flush...
**Why it happens:** Using LoggingService.logError() for flush failures
**How to avoid:** Use debugPrint() or ignore flush errors entirely
**Warning signs:** Rapidly growing buffer, performance degradation

### Pitfall 5: Flush When Not Authenticated

**What goes wrong:** 401 errors spam backend logs
**Why it happens:** Trying to POST before user logs in
**How to avoid:** Check token exists before attempting flush. If no token, silently skip.
**Warning signs:** Backend 401 errors with frontend source

## Code Examples

### Full Flush Implementation

```dart
// Source: Project patterns + Flutter API docs
import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_client.dart';

/// Additions to LoggingService for Phase 48
class LoggingService {
  // ... existing fields ...

  /// Lifecycle listener for pause/terminate flush
  AppLifecycleListener? _lifecycleListener;

  /// Secure storage for auth token
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  /// Storage key for JWT token
  static const String _tokenKey = 'auth_token';

  /// Default flush interval in minutes
  static const int _defaultFlushIntervalMinutes = 5;

  /// Current flush interval (configurable via SLOG-05)
  int _flushIntervalMinutes = _defaultFlushIntervalMinutes;

  /// Flag to prevent concurrent flushes
  bool _isFlushInProgress = false;

  void init() {
    // Existing connectivity monitoring...

    // Set up lifecycle listener
    _lifecycleListener = AppLifecycleListener(
      onPause: () => flush(),
      onDetach: () => flush(),
    );

    // Set up periodic flush timer
    _flushTimer = Timer.periodic(
      Duration(minutes: _flushIntervalMinutes),
      (_) => flush(),
    );
  }

  /// Flush buffered logs to backend
  Future<void> flush() async {
    // Skip if nothing to send
    if (_buffer.isEmpty) return;

    // Skip if logging disabled
    if (!_isEnabled) return;

    // Skip if already flushing (prevent concurrent POSTs)
    if (_isFlushInProgress) return;

    // Check network connectivity
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity.contains(ConnectivityResult.none)) {
      debugPrint('[LoggingService] Skipping flush - no network');
      return;
    }

    // Check authentication
    final token = await _storage.read(key: _tokenKey);
    if (token == null) {
      debugPrint('[LoggingService] Skipping flush - not authenticated');
      return;
    }

    _isFlushInProgress = true;

    try {
      // Copy buffer to avoid mutation during async POST
      final logsToSend = List<Map<String, dynamic>>.from(_buffer);

      await ApiClient().dio.post(
        '/api/logs/ingest',
        data: {'logs': logsToSend},
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
          sendTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
        ),
      );

      // Success - remove sent logs
      _buffer.removeRange(0, logsToSend.length);
      debugPrint('[LoggingService] Flushed ${logsToSend.length} logs');

    } catch (e) {
      // Silent fail - logs remain in buffer for retry
      debugPrint('[LoggingService] Flush failed: $e');
    } finally {
      _isFlushInProgress = false;
    }
  }

  /// Update flush interval (SLOG-05)
  void setFlushInterval(int minutes) {
    _flushIntervalMinutes = minutes;

    // Recreate timer with new interval
    _flushTimer?.cancel();
    _flushTimer = Timer.periodic(
      Duration(minutes: _flushIntervalMinutes),
      (_) => flush(),
    );
  }

  void dispose() {
    _lifecycleListener?.dispose();
    _flushTimer?.cancel();
    _connectivitySubscription?.cancel();
    // Final flush attempt on dispose
    flush();
  }
}
```

### Backend Expected Format

```dart
// Must match backend LogBatch/LogEntry models
final requestBody = {
  'logs': [
    {
      'timestamp': '2026-02-08T12:34:56.789Z',  // ISO 8601 UTC
      'level': 'INFO',                           // DEBUG/INFO/WARNING/ERROR/CRITICAL
      'message': 'User navigated to Projects',   // Human-readable
      'category': 'navigation',                  // navigation/action/error/network/api
      'session_id': 'uuid-v4-here',             // From SessionService
      'correlation_id': null,                    // Set by API interceptor context
    }
  ]
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WidgetsBindingObserver mixin | AppLifecycleListener class | Flutter 3.13 | Cleaner API, works with non-widget classes |
| Manual retry loops | dio_smart_retry package | 2023 | Exponential backoff handled correctly |
| SharedPreferences sync | SharedPreferencesAsync | 2024 | Better reliability, but sync still works for simple cases |

**Deprecated/outdated:**
- `WidgetsBindingObserver.didChangeAppLifecycleState`: Still works but AppLifecycleListener is preferred for new code

## Open Questions

1. **Persistence on flush failure**
   - What we know: Phase 48 success criteria says "Buffered logs persist until successfully delivered"
   - What's unclear: Does "persist" mean in-memory (survives flush attempts) or on-disk (survives app restart)?
   - Recommendation: Interpret as in-memory for Phase 48. Buffer persists across failed flushes. If on-disk persistence needed, create Phase 49 using flutter_persistent_queue.

2. **Flush interval configurability scope**
   - What we know: SLOG-05 says "configurable (default: 5 minutes)"
   - What's unclear: Is this developer-configurable (code constant) or user-configurable (settings UI)?
   - Recommendation: Start with code constant. Add settings UI only if needed.

3. **Logout behavior**
   - What we know: On logout, user is no longer authenticated
   - What's unclear: Should we flush before clearing auth token?
   - Recommendation: Yes, attempt flush before logout to capture final session logs.

## Sources

### Primary (HIGH confidence)
- Flutter API docs - AppLifecycleListener: https://api.flutter.dev/flutter/widgets/AppLifecycleListener-class.html
- Flutter API docs - AppLifecycleState: https://api.flutter.dev/flutter/dart-ui/AppLifecycleState.html
- Existing codebase - logging_service.dart, api_client.dart, auth patterns

### Secondary (MEDIUM confidence)
- LogRocket - Timer.periodic: https://blog.logrocket.com/understanding-flutter-timer-class-timer-periodic/
- dio_smart_retry package: https://pub.dev/packages/dio_smart_retry

### Tertiary (LOW confidence)
- flutter_persistent_queue (not needed for Phase 48): https://github.com/oakromulo/flutter_persistent_queue

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All required dependencies already in pubspec.yaml
- Architecture: HIGH - Follows established service patterns in codebase
- Pitfalls: HIGH - Well-documented Flutter lifecycle gotchas
- Flush implementation: HIGH - Straightforward pattern, existing auth patterns to follow

**Research date:** 2026-02-08
**Valid until:** 60 days (stable domain, established patterns)
