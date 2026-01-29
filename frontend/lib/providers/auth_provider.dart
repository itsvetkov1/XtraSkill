/// Authentication state management provider.
library;

import 'package:flutter/foundation.dart';

import '../services/auth_service.dart';

/// Authentication state enumeration
enum AuthState {
  /// User is not authenticated
  unauthenticated,

  /// Authentication in progress
  loading,

  /// User is authenticated
  authenticated,

  /// Authentication error occurred
  error,
}

/// Authentication provider managing user authentication state
class AuthProvider extends ChangeNotifier {
  /// Auth service for OAuth flows and token management
  final AuthService _authService;

  // Start in loading state to prevent premature redirects before auth check completes
  // This ensures GoRouter's redirect waits for checkAuthStatus() to finish
  AuthState _state = AuthState.loading;
  String? _userId;
  String? _email;
  String? _displayName;
  String? _errorMessage;

  AuthProvider({AuthService? authService})
      : _authService = authService ?? AuthService();

  /// Current authentication state
  AuthState get state => _state;

  /// Whether user is authenticated
  bool get isAuthenticated => _state == AuthState.authenticated;

  /// Whether authentication is in progress
  bool get isLoading => _state == AuthState.loading;

  /// Current user ID (null if not authenticated)
  String? get userId => _userId;

  /// Current user email (null if not authenticated)
  String? get email => _email;

  /// Current user display name (null if not authenticated or not available)
  String? get displayName => _displayName;

  /// Error message if authentication failed
  String? get errorMessage => _errorMessage;

  /// Check authentication status on app startup
  ///
  /// Loads stored token and validates it.
  /// If valid, fetches current user info and sets authenticated state.
  Future<void> checkAuthStatus() async {
    _state = AuthState.loading;
    _errorMessage = null; // Clear any previous error messages
    notifyListeners();

    try {
      // Check if token exists and is valid
      final isValid = await _authService.isTokenValid();

      if (isValid) {
        // Fetch current user information
        final user = await _authService.getCurrentUser();
        _userId = user['id'] as String?;
        _email = user['email'] as String?;
        _displayName = user['display_name'] as String?;
        _state = AuthState.authenticated;
      } else {
        _state = AuthState.unauthenticated;
      }
    } catch (e) {
      // Token validation or user fetch failed
      _state = AuthState.unauthenticated;
      _userId = null;
      _email = null;
      _displayName = null;
    }

    // Use Future.microtask to defer notification to avoid Flutter Web
    // text editing race condition during router rebuild
    Future.microtask(() => notifyListeners());
  }

  /// Login with Google OAuth provider
  Future<void> loginWithGoogle() async {
    _state = AuthState.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      // Initiate OAuth flow (opens browser)
      await _authService.loginWithGoogle();

      // Note: Actual token is handled by callback screen
      // This method just initiates the flow
      // State will be updated when callback screen calls handleCallback()
    } catch (e) {
      _state = AuthState.error;
      _errorMessage = 'Google login failed: ${e.toString()}';
      notifyListeners();
    }
  }

  /// Login with Microsoft OAuth provider
  Future<void> loginWithMicrosoft() async {
    _state = AuthState.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      // Initiate OAuth flow (opens browser)
      await _authService.loginWithMicrosoft();

      // Note: Actual token is handled by callback screen
      // This method just initiates the flow
      // State will be updated when callback screen calls handleCallback()
    } catch (e) {
      _state = AuthState.error;
      _errorMessage = 'Microsoft login failed: ${e.toString()}';
      notifyListeners();
    }
  }

  /// Handle OAuth callback with token
  ///
  /// Called by callback screen when it receives token from OAuth redirect
  ///
  /// Stores token, fetches user info, updates state to authenticated
  Future<void> handleCallback(String token) async {
    print('DEBUG AuthProvider: handleCallback called with token length: ${token.length}');
    _state = AuthState.loading;
    notifyListeners();

    try {
      // Store token
      print('DEBUG AuthProvider: Storing token...');
      await _authService.storeToken(token);
      print('DEBUG AuthProvider: Token stored successfully');

      // Fetch user information
      print('DEBUG AuthProvider: Fetching user info...');
      final user = await _authService.getCurrentUser();
      print('DEBUG AuthProvider: User info received: $user');

      _userId = user['id'] as String?;
      _email = user['email'] as String?;
      _displayName = user['display_name'] as String?;

      _state = AuthState.authenticated;
      _errorMessage = null;
      print('DEBUG AuthProvider: State set to authenticated');
    } catch (e) {
      print('DEBUG AuthProvider: ERROR - ${e.toString()}');
      _state = AuthState.error;
      _errorMessage = 'Authentication failed: ${e.toString()}';
    }

    // Use Future.microtask to defer notification to avoid Flutter Web
    // text editing race condition during router rebuild
    Future.microtask(() {
      notifyListeners();
      print('DEBUG AuthProvider: Notified listeners, final state: $_state');
    });
  }

  /// Logout current user
  Future<void> logout() async {
    _state = AuthState.loading;
    notifyListeners();

    try {
      await _authService.logout();

      _userId = null;
      _email = null;
      _displayName = null;
      _state = AuthState.unauthenticated;
      _errorMessage = null;
    } catch (e) {
      // Even if backend logout fails, clear local state
      _userId = null;
      _email = null;
      _displayName = null;
      _state = AuthState.unauthenticated;
    }

    // Use Future.microtask to defer notification to avoid Flutter Web
    // text editing race condition during router rebuild
    Future.microtask(() => notifyListeners());
  }

  /// Login with OAuth provider (generic)
  ///
  /// Kept for backwards compatibility with existing login_screen.dart
  @Deprecated('Use loginWithGoogle() or loginWithMicrosoft() instead')
  Future<void> login(String provider) async {
    if (provider == 'google') {
      await loginWithGoogle();
    } else if (provider == 'microsoft') {
      await loginWithMicrosoft();
    }
  }
}
