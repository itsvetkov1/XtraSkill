// For web platform - uses dart:html sessionStorage
import 'dart:html' as html;

/// Service for storing and retrieving return URLs through authentication flows.
///
/// Uses browser sessionStorage which:
/// - Persists through page refresh (survives OAuth redirect)
/// - Clears automatically when tab/window closes (ephemeral, correct for returnUrl)
/// - Is isolated per origin (secure)
class UrlStorageService {
  static const String _returnUrlKey = 'auth_return_url';

  /// Store return URL before OAuth redirect (browser will leave app)
  void storeReturnUrl(String url) {
    html.window.sessionStorage[_returnUrlKey] = url;
  }

  /// Retrieve return URL after OAuth callback
  String? getReturnUrl() {
    return html.window.sessionStorage[_returnUrlKey];
  }

  /// Clear return URL after successful navigation (one-time use)
  void clearReturnUrl() {
    html.window.sessionStorage.remove(_returnUrlKey);
  }
}
