/// Navigation state management provider.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Navigation provider managing sidebar expanded/collapsed state with persistent storage
///
/// Follows the ChangeNotifier pattern established in theme_provider.dart.
/// Persists sidebar state immediately on toggle to survive app crashes.
class NavigationProvider extends ChangeNotifier {
  /// SharedPreferences instance for persistent storage
  final SharedPreferences _prefs;

  /// Current sidebar expanded state (true = expanded, false = collapsed)
  bool _isSidebarExpanded;

  /// Storage key for sidebar expanded preference
  static const String _sidebarExpandedKey = 'sidebarExpanded';

  /// Private constructor for use by load() factory
  NavigationProvider(this._prefs, {bool? initialExpanded})
      : _isSidebarExpanded = initialExpanded ?? true;

  /// Load navigation provider with saved preference
  ///
  /// This factory enables async initialization in main() to load the saved
  /// sidebar state before MaterialApp renders, preventing state flash on
  /// app startup.
  ///
  /// Returns NavigationProvider with loaded preference, defaulting to expanded
  /// sidebar if no preference saved or if load fails.
  static Future<NavigationProvider> load(SharedPreferences prefs) async {
    try {
      // Load saved preference, default to true (expanded) if not set
      final isExpanded = prefs.getBool(_sidebarExpandedKey) ?? true;
      return NavigationProvider(prefs, initialExpanded: isExpanded);
    } catch (e) {
      // If SharedPreferences read fails (corrupted storage), default to expanded
      debugPrint('Failed to load navigation preference: $e');
      return NavigationProvider(prefs, initialExpanded: true);
    }
  }

  /// Whether sidebar is currently expanded
  bool get isSidebarExpanded => _isSidebarExpanded;

  /// Toggle sidebar between expanded and collapsed states with immediate persistence
  ///
  /// Saves preference immediately to SharedPreferences BEFORE notifying
  /// listeners. This ensures the preference survives if the app crashes
  /// or is force-closed after the toggle but before app shutdown.
  ///
  /// Error handling: If persistence fails (disk full, permission denied),
  /// the UI still updates but the preference won't survive app restart.
  /// This prioritizes user experience - the toggle always works visually.
  Future<void> toggleSidebar() async {
    _isSidebarExpanded = !_isSidebarExpanded;

    try {
      // Persist immediately before notifying listeners (critical for crash survival)
      await _prefs.setBool(_sidebarExpandedKey, _isSidebarExpanded);
    } catch (e) {
      // Handle SharedPreferences failures gracefully
      // User sees toggle, but preference may not survive restart
      debugPrint('Failed to persist sidebar preference: $e');
      // Don't block UI - continue with notifyListeners
    }

    notifyListeners();
  }
}
