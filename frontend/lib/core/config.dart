/// Application configuration constants.
library;

import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// API configuration
class ApiConfig {
  /// Base URL for the backend API
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// API endpoints
  static const String health = '/health';
  static const String auth = '/auth';
}

/// Platform detection helpers
class PlatformHelper {
  /// Check if running on web platform
  static bool get isWeb => kIsWeb;

  /// Check if running on mobile (Android or iOS)
  static bool get isMobile => !kIsWeb && (Platform.isAndroid || Platform.isIOS);

  /// Check if running on desktop (Windows, macOS, Linux)
  static bool get isDesktop =>
      !kIsWeb && (Platform.isWindows || Platform.isMacOS || Platform.isLinux);

  /// Check if running on Android
  static bool get isAndroid => !kIsWeb && Platform.isAndroid;

  /// Check if running on iOS
  static bool get isIOS => !kIsWeb && Platform.isIOS;
}

/// Debug mode flag
const bool isDebugMode = bool.fromEnvironment('DEBUG', defaultValue: true);

/// Convenience export for API base URL
const String apiBaseUrl = ApiConfig.baseUrl;

/// Responsive breakpoints (in logical pixels)
class Breakpoints {
  /// Mobile breakpoint (phones)
  static const double mobile = 600;

  /// Tablet breakpoint
  static const double tablet = 900;

  /// Desktop breakpoint
  static const double desktop = 1200;
}
