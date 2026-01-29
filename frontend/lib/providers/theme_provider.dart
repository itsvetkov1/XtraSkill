/// Theme state management provider.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Theme provider managing light/dark mode with persistent storage
///
/// Follows the ChangeNotifier pattern established in auth_provider.dart.
/// Persists theme preference immediately on toggle to survive app crashes.
class ThemeProvider extends ChangeNotifier {
  /// SharedPreferences instance for persistent storage
  final SharedPreferences _prefs;

  /// Current dark mode state (true = dark, false = light)
  bool _isDarkMode;

  /// Storage key for theme preference
  static const String _themeKey = 'isDarkMode';

  /// Private constructor for use by load() factory
  ThemeProvider(this._prefs, {bool? initialDarkMode})
      : _isDarkMode = initialDarkMode ?? false;

  /// Load theme provider with saved preference
  ///
  /// This factory enables async initialization in main() to load the saved
  /// theme preference before MaterialApp renders, preventing white flash on
  /// dark mode startup (SET-06 requirement).
  ///
  /// Returns ThemeProvider with loaded preference, defaulting to light theme
  /// if no preference saved or if load fails.
  static Future<ThemeProvider> load(SharedPreferences prefs) async {
    try {
      // Load saved preference, default to false (light theme) if not set
      final isDarkMode = prefs.getBool(_themeKey) ?? false;
      return ThemeProvider(prefs, initialDarkMode: isDarkMode);
    } catch (e) {
      // If SharedPreferences read fails (corrupted storage), default to light
      debugPrint('Failed to load theme preference: $e');
      return ThemeProvider(prefs, initialDarkMode: false);
    }
  }

  /// Whether dark mode is currently enabled
  bool get isDarkMode => _isDarkMode;

  /// Current theme mode for MaterialApp
  ThemeMode get themeMode => _isDarkMode ? ThemeMode.dark : ThemeMode.light;

  /// Toggle between light and dark themes with immediate persistence
  ///
  /// Saves preference immediately to SharedPreferences BEFORE notifying
  /// listeners. This ensures the preference survives if the app crashes
  /// or is force-closed after the toggle but before app shutdown.
  ///
  /// Error handling: If persistence fails (disk full, permission denied),
  /// the UI still updates but the preference won't survive app restart.
  /// This prioritizes user experience - the toggle always works visually.
  Future<void> toggleTheme() async {
    _isDarkMode = !_isDarkMode;

    try {
      // Persist immediately before notifying listeners (critical for crash survival)
      await _prefs.setBool(_themeKey, _isDarkMode);
    } catch (e) {
      // Handle SharedPreferences failures gracefully
      // User sees toggle, but preference may not survive restart
      debugPrint('Failed to persist theme preference: $e');
      // Don't block UI - continue with notifyListeners
    }

    notifyListeners();
  }
}
