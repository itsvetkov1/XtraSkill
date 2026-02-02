/// Unit tests for AuthProvider (Phase 31).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import 'auth_provider_test.mocks.dart';

@GenerateNiceMocks([MockSpec<AuthService>()])
void main() {
  group('AuthProvider Unit Tests', () {
    late MockAuthService mockAuthService;
    late AuthProvider provider;

    setUp(() {
      mockAuthService = MockAuthService();
      provider = AuthProvider(authService: mockAuthService);
    });

    group('Initial State', () {
      test('starts in loading state', () {
        expect(provider.state, equals(AuthState.loading));
      });

      test('starts with isLoading true', () {
        expect(provider.isLoading, isTrue);
      });

      test('starts with isAuthenticated false', () {
        expect(provider.isAuthenticated, isFalse);
      });

      test('starts with null userId', () {
        expect(provider.userId, isNull);
      });

      test('starts with null email', () {
        expect(provider.email, isNull);
      });

      test('starts with null displayName', () {
        expect(provider.displayName, isNull);
      });

      test('starts with null authProvider', () {
        expect(provider.authProvider, isNull);
      });

      test('starts with null errorMessage', () {
        expect(provider.errorMessage, isNull);
      });
    });

    group('checkAuthStatus', () {
      test('sets authenticated when token is valid', () async {
        when(mockAuthService.isTokenValid()).thenAnswer((_) async => true);
        when(mockAuthService.getCurrentUser()).thenAnswer((_) async => {
              'id': 'user-123',
              'email': 'test@example.com',
              'display_name': 'Test User',
              'oauth_provider': 'google',
            });

        await provider.checkAuthStatus();
        // Allow microtask to complete
        await Future.delayed(Duration.zero);

        expect(provider.state, equals(AuthState.authenticated));
        expect(provider.isAuthenticated, isTrue);
        expect(provider.userId, equals('user-123'));
        expect(provider.email, equals('test@example.com'));
        expect(provider.displayName, equals('Test User'));
        expect(provider.authProvider, equals('google'));
      });

      test('sets unauthenticated when token is invalid', () async {
        when(mockAuthService.isTokenValid()).thenAnswer((_) async => false);

        await provider.checkAuthStatus();
        // Allow microtask to complete
        await Future.delayed(Duration.zero);

        expect(provider.state, equals(AuthState.unauthenticated));
        expect(provider.isAuthenticated, isFalse);
      });

      test('sets unauthenticated when isTokenValid throws', () async {
        when(mockAuthService.isTokenValid())
            .thenThrow(Exception('Token check failed'));

        await provider.checkAuthStatus();
        // Allow microtask to complete
        await Future.delayed(Duration.zero);

        expect(provider.state, equals(AuthState.unauthenticated));
        expect(provider.userId, isNull);
        expect(provider.email, isNull);
      });

      test('sets unauthenticated when getCurrentUser throws', () async {
        when(mockAuthService.isTokenValid()).thenAnswer((_) async => true);
        when(mockAuthService.getCurrentUser())
            .thenThrow(Exception('User fetch failed'));

        await provider.checkAuthStatus();
        // Allow microtask to complete
        await Future.delayed(Duration.zero);

        expect(provider.state, equals(AuthState.unauthenticated));
        expect(provider.userId, isNull);
        expect(provider.email, isNull);
        expect(provider.displayName, isNull);
        expect(provider.authProvider, isNull);
      });

      test('clears previous error on call', () async {
        // First, simulate an error state
        when(mockAuthService.loginWithGoogle())
            .thenThrow(Exception('Login failed'));
        await provider.loginWithGoogle();
        expect(provider.errorMessage, isNotNull);

        // Now check auth status - should clear error
        when(mockAuthService.isTokenValid()).thenAnswer((_) async => false);
        await provider.checkAuthStatus();
        await Future.delayed(Duration.zero);

        expect(provider.errorMessage, isNull);
      });
    });

    group('loginWithGoogle', () {
      test('sets loading state during call', () async {
        when(mockAuthService.loginWithGoogle()).thenAnswer((_) async {
          // During the call, state should be loading
          expect(provider.state, equals(AuthState.loading));
          return '';
        });

        await provider.loginWithGoogle();
      });

      test('clears error before call', () async {
        // Set up error state first
        when(mockAuthService.loginWithGoogle())
            .thenThrow(Exception('First error'));
        await provider.loginWithGoogle();
        expect(provider.errorMessage, isNotNull);

        // Second call should clear error initially
        when(mockAuthService.loginWithGoogle()).thenAnswer((_) async => '');

        await provider.loginWithGoogle();

        // State remains loading since token is handled by callback
        expect(provider.state, equals(AuthState.loading));
      });

      test('sets error state on failure', () async {
        when(mockAuthService.loginWithGoogle())
            .thenThrow(Exception('OAuth failed'));

        await provider.loginWithGoogle();

        expect(provider.state, equals(AuthState.error));
        expect(provider.errorMessage, contains('Google login failed'));
        expect(provider.errorMessage, contains('OAuth failed'));
      });

      test('calls authService.loginWithGoogle', () async {
        when(mockAuthService.loginWithGoogle()).thenAnswer((_) async => '');

        await provider.loginWithGoogle();

        verify(mockAuthService.loginWithGoogle()).called(1);
      });
    });

    group('loginWithMicrosoft', () {
      test('sets loading state during call', () async {
        when(mockAuthService.loginWithMicrosoft()).thenAnswer((_) async {
          expect(provider.state, equals(AuthState.loading));
          return '';
        });

        await provider.loginWithMicrosoft();
      });

      test('sets error state on failure', () async {
        when(mockAuthService.loginWithMicrosoft())
            .thenThrow(Exception('OAuth failed'));

        await provider.loginWithMicrosoft();

        expect(provider.state, equals(AuthState.error));
        expect(provider.errorMessage, contains('Microsoft login failed'));
        expect(provider.errorMessage, contains('OAuth failed'));
      });

      test('calls authService.loginWithMicrosoft', () async {
        when(mockAuthService.loginWithMicrosoft()).thenAnswer((_) async => '');

        await provider.loginWithMicrosoft();

        verify(mockAuthService.loginWithMicrosoft()).called(1);
      });
    });

    group('handleCallback', () {
      test('stores token and fetches user on success', () async {
        when(mockAuthService.storeToken('test-token'))
            .thenAnswer((_) async => {});
        when(mockAuthService.getCurrentUser()).thenAnswer((_) async => {
              'id': 'user-456',
              'email': 'callback@example.com',
              'display_name': 'Callback User',
              'oauth_provider': 'microsoft',
            });

        await provider.handleCallback('test-token');
        // Allow microtask to complete
        await Future.delayed(Duration.zero);

        verify(mockAuthService.storeToken('test-token')).called(1);
        verify(mockAuthService.getCurrentUser()).called(1);

        expect(provider.state, equals(AuthState.authenticated));
        expect(provider.userId, equals('user-456'));
        expect(provider.email, equals('callback@example.com'));
        expect(provider.displayName, equals('Callback User'));
        expect(provider.authProvider, equals('microsoft'));
        expect(provider.errorMessage, isNull);
      });

      test('sets loading state during call', () async {
        when(mockAuthService.storeToken(any)).thenAnswer((_) async {
          expect(provider.state, equals(AuthState.loading));
        });
        when(mockAuthService.getCurrentUser()).thenAnswer((_) async => {
              'id': 'user-123',
              'email': 'test@example.com',
            });

        await provider.handleCallback('token');
        await Future.delayed(Duration.zero);
      });

      test('sets error state when storeToken fails', () async {
        when(mockAuthService.storeToken(any))
            .thenThrow(Exception('Storage failed'));

        await provider.handleCallback('token');
        // Allow microtask to complete
        await Future.delayed(Duration.zero);

        expect(provider.state, equals(AuthState.error));
        expect(provider.errorMessage, contains('Authentication failed'));
        expect(provider.errorMessage, contains('Storage failed'));
      });

      test('sets error state when getCurrentUser fails', () async {
        when(mockAuthService.storeToken(any)).thenAnswer((_) async => {});
        when(mockAuthService.getCurrentUser())
            .thenThrow(Exception('User fetch failed'));

        await provider.handleCallback('token');
        // Allow microtask to complete
        await Future.delayed(Duration.zero);

        expect(provider.state, equals(AuthState.error));
        expect(provider.errorMessage, contains('Authentication failed'));
        expect(provider.errorMessage, contains('User fetch failed'));
      });
    });

    group('logout', () {
      test('clears user state on successful logout', () async {
        // First authenticate
        when(mockAuthService.isTokenValid()).thenAnswer((_) async => true);
        when(mockAuthService.getCurrentUser()).thenAnswer((_) async => {
              'id': 'user-123',
              'email': 'test@example.com',
              'display_name': 'Test User',
              'oauth_provider': 'google',
            });
        await provider.checkAuthStatus();
        await Future.delayed(Duration.zero);
        expect(provider.isAuthenticated, isTrue);

        // Now logout
        when(mockAuthService.logout()).thenAnswer((_) async => {});
        await provider.logout();
        await Future.delayed(Duration.zero);

        expect(provider.state, equals(AuthState.unauthenticated));
        expect(provider.userId, isNull);
        expect(provider.email, isNull);
        expect(provider.displayName, isNull);
        expect(provider.authProvider, isNull);
        expect(provider.errorMessage, isNull);
      });

      test('sets loading state during logout', () async {
        when(mockAuthService.logout()).thenAnswer((_) async {
          expect(provider.state, equals(AuthState.loading));
        });

        await provider.logout();
        await Future.delayed(Duration.zero);
      });

      test('clears state even when service logout fails', () async {
        when(mockAuthService.logout()).thenThrow(Exception('Logout error'));

        await provider.logout();
        await Future.delayed(Duration.zero);

        // Should still be unauthenticated - local state cleared
        expect(provider.state, equals(AuthState.unauthenticated));
        expect(provider.userId, isNull);
        expect(provider.email, isNull);
        expect(provider.displayName, isNull);
        expect(provider.authProvider, isNull);
      });

      test('calls authService.logout', () async {
        when(mockAuthService.logout()).thenAnswer((_) async => {});

        await provider.logout();
        await Future.delayed(Duration.zero);

        verify(mockAuthService.logout()).called(1);
      });
    });
  });
}
