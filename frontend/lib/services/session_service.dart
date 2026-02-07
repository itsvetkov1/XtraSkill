/// Session management for logging context.
///
/// Generates and maintains a UUID v4 session ID for the app lifecycle.
/// Session ID is used to group frontend logs for debugging and analysis.
library;

import 'package:uuid/uuid.dart';

/// Singleton service that provides a unique session ID for the app lifecycle
class SessionService {
  static final SessionService _instance = SessionService._internal();

  /// Factory constructor returns the singleton instance
  factory SessionService() => _instance;

  /// Private constructor generates UUID v4 on creation
  SessionService._internal() {
    _sessionId = const Uuid().v4();
  }

  /// Unique session identifier (UUID v4)
  late final String _sessionId;

  /// Get the current session ID
  String get sessionId => _sessionId;

  /// Regenerate session ID (useful on logout/login transitions)
  void regenerateSession() {
    _sessionId = const Uuid().v4();
  }
}
