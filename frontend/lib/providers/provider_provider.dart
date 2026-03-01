/// LLM provider state management provider.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Provider managing LLM provider selection with persistent storage
///
/// Follows the ChangeNotifier pattern established in theme_provider.dart.
/// Persists provider preference immediately on change to survive app restarts.
class ProviderProvider extends ChangeNotifier {
  /// SharedPreferences instance for persistent storage
  final SharedPreferences _prefs;

  /// Currently selected LLM provider
  String _selectedProvider;

  /// Storage key for provider preference
  static const String _providerKey = 'defaultLlmProvider';

  /// List of available LLM providers
  static const List<String> _availableProviders = [
    'anthropic',
    'google',
    'deepseek',
    'claude-code-sdk',
    'claude-code-cli',
    'openclaw',
  ];

  /// Private constructor for use by load() factory
  ProviderProvider(this._prefs, {String? initialProvider})
      : _selectedProvider = initialProvider ?? 'anthropic';

  /// Load provider preference from SharedPreferences
  ///
  /// This factory enables async initialization in main() to load the saved
  /// provider preference before MaterialApp renders, ensuring the correct
  /// provider is selected from app startup.
  ///
  /// Returns ProviderProvider with loaded preference, defaulting to 'anthropic'
  /// if no preference saved or if load fails.
  static Future<ProviderProvider> load(SharedPreferences prefs) async {
    try {
      // Load saved preference, default to 'anthropic' if not set
      final savedProvider = prefs.getString(_providerKey) ?? 'anthropic';
      // Validate saved provider is in allowed list
      final provider = _availableProviders.contains(savedProvider)
          ? savedProvider
          : 'anthropic';
      return ProviderProvider(prefs, initialProvider: provider);
    } catch (e) {
      // If SharedPreferences read fails (corrupted storage), default to anthropic
      debugPrint('Failed to load provider preference: $e');
      return ProviderProvider(prefs, initialProvider: 'anthropic');
    }
  }

  /// Currently selected LLM provider
  String get selectedProvider => _selectedProvider;

  /// List of available LLM providers
  List<String> get providers => List.unmodifiable(_availableProviders);

  /// Set the selected LLM provider with immediate persistence
  ///
  /// Saves preference immediately to SharedPreferences BEFORE notifying
  /// listeners. This ensures the preference survives if the app crashes
  /// or is force-closed after the change but before app shutdown.
  ///
  /// Throws ArgumentError if provider is not in the allowed list.
  ///
  /// Error handling: If persistence fails (disk full, permission denied),
  /// the UI still updates but the preference won't survive app restart.
  /// This prioritizes user experience - the selection always works visually.
  Future<void> setProvider(String provider) async {
    if (!_availableProviders.contains(provider)) {
      throw ArgumentError(
        'Invalid provider: $provider. Must be one of: ${_availableProviders.join(", ")}',
      );
    }

    _selectedProvider = provider;

    try {
      // Persist immediately before notifying listeners (critical for crash survival)
      await _prefs.setString(_providerKey, provider);
    } catch (e) {
      // Handle SharedPreferences failures gracefully
      // User sees selection change, but preference may not survive restart
      debugPrint('Failed to persist provider preference: $e');
      // Don't block UI - continue with notifyListeners
    }

    notifyListeners();
  }
}
