/// Logging state management provider.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/logging_service.dart';

/// Logging provider managing enable/disable state with persistent storage
///
/// Follows the ChangeNotifier pattern established in theme_provider.dart.
/// Persists logging preference immediately on toggle to survive app crashes.
/// When disabled, clears log buffer for privacy.
class LoggingProvider extends ChangeNotifier {
  /// SharedPreferences instance for persistent storage
  final SharedPreferences _prefs;

  /// Current logging enabled state (true = enabled, false = disabled)
  bool _isLoggingEnabled;

  /// Storage key for logging preference
  static const String _loggingKey = 'isLoggingEnabled';

  /// Private constructor for use by load() factory
  LoggingProvider(this._prefs, {bool? initialEnabled})
      : _isLoggingEnabled = initialEnabled ?? true;

  /// Load logging provider with saved preference
  ///
  /// This factory enables async initialization in main() to load the saved
  /// logging preference before app starts, ensuring consistent state.
  ///
  /// Returns LoggingProvider with loaded preference, defaulting to enabled
  /// if no preference saved or if load fails.
  static Future<LoggingProvider> load(SharedPreferences prefs) async {
    try {
      // Load saved preference, default to true (enabled for pilot)
      final isEnabled = prefs.getBool(_loggingKey) ?? true;
      return LoggingProvider(prefs, initialEnabled: isEnabled);
    } catch (e) {
      // If SharedPreferences read fails (corrupted storage), default to enabled
      debugPrint('Failed to load logging preference: $e');
      return LoggingProvider(prefs, initialEnabled: true);
    }
  }

  /// Whether logging is currently enabled
  bool get isLoggingEnabled => _isLoggingEnabled;

  /// Toggle logging on/off with immediate persistence
  ///
  /// Saves preference immediately to SharedPreferences BEFORE notifying
  /// listeners. This ensures the preference survives if the app crashes
  /// or is force-closed after the toggle but before app shutdown.
  ///
  /// When disabled, clears the log buffer for privacy protection.
  ///
  /// Error handling: If persistence fails (disk full, permission denied),
  /// the UI still updates but the preference won't survive app restart.
  /// This prioritizes user experience - the toggle always works visually.
  Future<void> toggleLogging() async {
    _isLoggingEnabled = !_isLoggingEnabled;

    try {
      // Persist immediately before notifying listeners (critical for crash survival)
      await _prefs.setBool(_loggingKey, _isLoggingEnabled);
    } catch (e) {
      // Handle SharedPreferences failures gracefully
      // User sees toggle, but preference may not survive restart
      debugPrint('Failed to persist logging preference: $e');
      // Don't block UI - continue with service update and notifyListeners
    }

    // Update LoggingService state
    LoggingService().isEnabled = _isLoggingEnabled;

    notifyListeners();
  }
}
