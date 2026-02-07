/// Comprehensive frontend logging service with buffering and connectivity monitoring.
///
/// Captures user actions, navigation, errors, and network state changes.
/// Logs are buffered in memory (max 1000 entries) for Phase 48 batch transmission.
library;

import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:logger/logger.dart';

import 'session_service.dart';

/// Singleton logging service that buffers logs and monitors network state
class LoggingService {
  static final LoggingService _instance = LoggingService._internal();

  /// Factory constructor returns the singleton instance
  factory LoggingService() => _instance;

  /// Private constructor sets up logger with production filter
  LoggingService._internal() {
    _logger = Logger(
      filter: ProductionFilter(), // Enable INFO/WARNING/ERROR in release mode
      printer: PrettyPrinter(
        methodCount: 0, // Disable method stack trace for cleaner output
        errorMethodCount: 5, // Show stack for errors
        lineLength: 120,
        colors: true,
        printEmojis: true,
        dateTimeFormat: DateTimeFormat.onlyTimeAndSinceStart,
      ),
    );
  }

  /// Logger instance for console output
  late final Logger _logger;

  /// Session service for session ID
  final SessionService _sessionService = SessionService();

  /// In-memory log buffer (max 1000 entries per SLOG-04)
  final List<Map<String, dynamic>> _buffer = [];

  /// Maximum buffer size before auto-trim
  static const int _maxBufferSize = 1000;

  /// Connectivity monitoring subscription
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;

  /// Timer for periodic flush (Phase 48)
  Timer? _flushTimer;

  /// Initialize logging service with connectivity monitoring
  void init() {
    // Start connectivity monitoring
    _connectivitySubscription = Connectivity()
        .onConnectivityChanged
        .listen((List<ConnectivityResult> results) {
      final isConnected =
          results.isNotEmpty && !results.contains(ConnectivityResult.none);
      logNetworkStateChange(isConnected);
    });

    // Phase 48: Periodic flush timer (placeholder for now)
    // _flushTimer = Timer.periodic(const Duration(minutes: 5), (_) => flush());
  }

  /// Log navigation event (route changes, screen views)
  void logNavigation(String routeName) {
    _log(
      level: 'INFO',
      message: routeName,
      category: 'navigation',
    );
  }

  /// Log user action (button clicks, form submissions)
  void logAction(String action, {Map<String, dynamic>? metadata}) {
    _log(
      level: 'INFO',
      message: action,
      category: 'action',
      metadata: metadata,
    );
  }

  /// Log error with exception type and stack trace
  void logError(
    dynamic error,
    StackTrace? stackTrace, {
    String? context,
  }) {
    _log(
      level: 'ERROR',
      message: '${error.runtimeType}: ${error.toString()}',
      category: 'error',
      metadata: {
        if (stackTrace != null) 'stackTrace': stackTrace.toString(),
        if (context != null) 'context': context,
      },
    );
  }

  /// Log network state change (connectivity monitoring)
  void logNetworkStateChange(bool isConnected) {
    _log(
      level: 'INFO',
      message: 'Network ${isConnected ? "connected" : "disconnected"}',
      category: 'network',
    );
  }

  /// Internal logging method that writes to console and buffers for backend
  void _log({
    required String level,
    required String message,
    required String category,
    Map<String, dynamic>? metadata,
  }) {
    // Console logging for development
    final logLevel = Level.values.byName(level.toLowerCase());
    _logger.log(logLevel, message);

    // Add structured entry to buffer for backend ingestion (Phase 48)
    final entry = {
      'timestamp': DateTime.now().toUtc().toIso8601String(),
      'level': level,
      'message': message,
      'category': category,
      'session_id': _sessionService.sessionId,
      'correlation_id': null, // Set by backend if in API request context
      if (metadata != null) ...metadata,
    };

    _buffer.add(entry);

    // Auto-trim buffer if exceeds max size (drop oldest entries)
    if (_buffer.length > _maxBufferSize) {
      _buffer.removeRange(0, _buffer.length - _maxBufferSize);
    }
  }

  /// Get buffered logs (for Phase 48 flush to backend)
  List<Map<String, dynamic>> get buffer => List.unmodifiable(_buffer);

  /// Clear buffer after successful flush (Phase 48)
  void clearBuffer() {
    _buffer.clear();
  }

  /// Dispose resources (cancel subscriptions, timers)
  void dispose() {
    _connectivitySubscription?.cancel();
    _flushTimer?.cancel();
  }
}
