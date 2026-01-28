/// Widget tests for login screen.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/providers/auth_provider.dart';
import 'package:frontend/screens/auth/login_screen.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';

import 'login_screen_test.mocks.dart';

@GenerateNiceMocks([MockSpec<AuthProvider>()])
void main() {
  group('LoginScreen Widget Tests', () {
    late MockAuthProvider mockAuthProvider;

    setUp(() {
      mockAuthProvider = MockAuthProvider();
      // Default mock behavior
      when(mockAuthProvider.isLoading).thenReturn(false);
      when(mockAuthProvider.state).thenReturn(AuthState.unauthenticated);
      when(mockAuthProvider.errorMessage).thenReturn(null);
    });

    testWidgets('Login screen displays OAuth buttons', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthProvider>.value(
            value: mockAuthProvider,
            child: const LoginScreen(),
          ),
        ),
      );

      expect(find.text('Sign in with Google'), findsOneWidget);
      expect(find.text('Sign in with Microsoft'), findsOneWidget);
    });

    testWidgets('Login screen shows app branding', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthProvider>.value(
            value: mockAuthProvider,
            child: const LoginScreen(),
          ),
        ),
      );

      expect(find.text('Business Analyst Assistant'), findsOneWidget);
      expect(find.text('AI-powered requirement discovery'), findsOneWidget);
      expect(find.byIcon(Icons.analytics_outlined), findsOneWidget);
    });

    testWidgets('Login screen shows loading indicator when authenticating',
        (tester) async {
      when(mockAuthProvider.isLoading).thenReturn(true);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthProvider>.value(
            value: mockAuthProvider,
            child: const LoginScreen(),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Sign in with Google'), findsNothing);
      expect(find.text('Sign in with Microsoft'), findsNothing);
    });

    testWidgets('Login screen shows error message on authentication failure',
        (tester) async {
      when(mockAuthProvider.state).thenReturn(AuthState.error);
      when(mockAuthProvider.errorMessage).thenReturn('OAuth login failed');

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthProvider>.value(
            value: mockAuthProvider,
            child: const LoginScreen(),
          ),
        ),
      );

      expect(find.text('OAuth login failed'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('Login screen buttons are disabled during loading',
        (tester) async {
      when(mockAuthProvider.isLoading).thenReturn(false);

      await tester.pumpWidget(
        MaterialApp(
          home: ChangeNotifierProvider<AuthProvider>.value(
            value: mockAuthProvider,
            child: const LoginScreen(),
          ),
        ),
      );

      expect(find.text('Sign in with Google'), findsOneWidget);
      expect(find.text('Sign in with Microsoft'), findsOneWidget);
    });
  });
}
