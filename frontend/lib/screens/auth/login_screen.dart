/// Login screen with OAuth options.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../services/url_storage_service.dart';

/// Login screen with Google and Microsoft OAuth buttons
class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isMobile = screenWidth < 600;
    final maxWidth = isMobile ? screenWidth * 0.9 : 400.0;

    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: SingleChildScrollView(
            padding: EdgeInsets.all(isMobile ? 16.0 : 24.0),
            child: Consumer<AuthProvider>(
              builder: (context, authProvider, child) {
                return Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // App logo and title
                    Icon(
                      Icons.analytics_outlined,
                      size: isMobile ? 64 : 80,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    SizedBox(height: isMobile ? 20 : 24),
                    Text(
                      'Business Analyst Assistant',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            fontSize: isMobile ? 20 : null,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'AI-powered requirement discovery',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                    ),
                    SizedBox(height: isMobile ? 32 : 48),

                    // Show loading indicator if authenticating
                    if (authProvider.isLoading)
                      const Center(
                        child: CircularProgressIndicator(),
                      )
                    else ...[
                      // Google Sign In button
                      _OAuthButton(
                        onPressed: () => _handleGoogleLogin(context),
                        icon: Icons.g_mobiledata,
                        label: 'Sign in with Google',
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black87,
                      ),
                      const SizedBox(height: 16),

                      // Microsoft Sign In button
                      _OAuthButton(
                        onPressed: () => _handleMicrosoftLogin(context),
                        icon: Icons.window,
                        label: 'Sign in with Microsoft',
                        backgroundColor: const Color(0xFF00A4EF),
                        foregroundColor: Colors.white,
                      ),
                    ],

                    const SizedBox(height: 24),

                    // Show error message if authentication failed
                    if (authProvider.state == AuthState.error)
                      Card(
                        color: Theme.of(context).colorScheme.errorContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Row(
                            children: [
                              Icon(
                                Icons.error_outline,
                                color: Theme.of(context).colorScheme.error,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  authProvider.errorMessage ?? 'Authentication failed',
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                        color: Theme.of(context).colorScheme.onErrorContainer,
                                      ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  void _handleGoogleLogin(BuildContext context) {
    // Extract returnUrl from current URL query params
    final uri = GoRouterState.of(context).uri;
    final returnUrl = uri.queryParameters['returnUrl'];

    // Store before OAuth redirect (browser will leave app)
    if (returnUrl != null) {
      final urlStorage = UrlStorageService();
      urlStorage.storeReturnUrl(Uri.decodeComponent(returnUrl));
    }

    // Proceed with OAuth
    final authProvider = context.read<AuthProvider>();
    authProvider.loginWithGoogle();
  }

  void _handleMicrosoftLogin(BuildContext context) {
    // Extract returnUrl from current URL query params
    final uri = GoRouterState.of(context).uri;
    final returnUrl = uri.queryParameters['returnUrl'];

    // Store before OAuth redirect (browser will leave app)
    if (returnUrl != null) {
      final urlStorage = UrlStorageService();
      urlStorage.storeReturnUrl(Uri.decodeComponent(returnUrl));
    }

    // Proceed with OAuth
    final authProvider = context.read<AuthProvider>();
    authProvider.loginWithMicrosoft();
  }
}

/// Custom OAuth button widget
class _OAuthButton extends StatelessWidget {
  const _OAuthButton({
    required this.onPressed,
    required this.icon,
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final VoidCallback onPressed;
  final IconData icon;
  final String label;
  final Color backgroundColor;
  final Color foregroundColor;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: backgroundColor,
        foregroundColor: foregroundColor,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        elevation: 2,
        minimumSize: const Size(double.infinity, 48),
      ),
    );
  }
}
