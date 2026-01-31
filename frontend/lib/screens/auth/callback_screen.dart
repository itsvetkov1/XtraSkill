/// OAuth callback screen handling redirect from OAuth providers.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../services/url_storage_service.dart';

/// Callback screen for OAuth redirect
///
/// Handles URL with token parameter: /auth/callback?token={jwt_token}
/// Extracts token, stores it, and navigates to home screen
class CallbackScreen extends StatefulWidget {
  const CallbackScreen({super.key});

  @override
  State<CallbackScreen> createState() => _CallbackScreenState();
}

class _CallbackScreenState extends State<CallbackScreen> {
  bool _isProcessing = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    // Process callback after widget is built
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _processCallback();
    });
  }

  Future<void> _processCallback() async {
    if (!mounted) return;

    try {
      // Extract token from URL query parameters
      final uri = GoRouterState.of(context).uri;
      print('DEBUG: Full URI: $uri');
      print('DEBUG: Query params: ${uri.queryParameters}');

      final token = uri.queryParameters['token'];
      print('DEBUG: Extracted token: ${token?.substring(0, 20)}...');

      if (token == null || token.isEmpty) {
        print('DEBUG: No token found!');
        setState(() {
          _error = 'No authentication token received';
          _isProcessing = false;
        });
        return;
      }

      // Handle callback through auth provider
      print('DEBUG: Calling handleCallback...');
      final authProvider = context.read<AuthProvider>();
      await authProvider.handleCallback(token);

      print('DEBUG: After handleCallback - isAuthenticated: ${authProvider.isAuthenticated}');
      print('DEBUG: Error message: ${authProvider.errorMessage}');

      // Navigate to return URL or home on success
      if (mounted && authProvider.isAuthenticated) {
        // Get stored return URL from sessionStorage
        final urlStorage = UrlStorageService();
        final returnUrl = urlStorage.getReturnUrl();
        print('DEBUG: Retrieved returnUrl from storage: $returnUrl');

        // Clear after retrieval (one-time use, prevents stale redirects)
        urlStorage.clearReturnUrl();

        // Validate returnUrl (security: prevent open redirect)
        String destination = '/home';
        if (returnUrl != null && returnUrl.startsWith('/')) {
          destination = returnUrl;
          print('DEBUG: Using returnUrl as destination: $destination');
        } else if (returnUrl != null) {
          print('DEBUG: Invalid returnUrl (not relative path), falling back to /home');
        }

        // Navigate directly - don't rely on GoRouter redirect
        context.go(destination);
      } else if (mounted) {
        print('DEBUG: Authentication failed, showing error');
        setState(() {
          _error = authProvider.errorMessage ?? 'Authentication failed';
          _isProcessing = false;
        });
      }
    } catch (e) {
      print('DEBUG: Exception caught: $e');
      setState(() {
        _error = 'Failed to process authentication: ${e.toString()}';
        _isProcessing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: _isProcessing
            ? Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 24),
                  Text(
                    'Completing authentication...',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ],
              )
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.error_outline,
                    size: 64,
                    color: Theme.of(context).colorScheme.error,
                  ),
                  const SizedBox(height: 24),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32.0),
                    child: SelectableText(
                      _error ?? 'Authentication failed',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                  ),
                  const SizedBox(height: 32),
                  ElevatedButton(
                    onPressed: () => context.go('/login'),
                    child: const Text('Return to Login'),
                  ),
                ],
              ),
      ),
    );
  }
}
