import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

import 'core/theme.dart';
import 'providers/auth_provider.dart';
import 'providers/document_provider.dart';
import 'services/document_service.dart';
import 'core/api_client.dart';
import 'providers/project_provider.dart';
import 'providers/thread_provider.dart';
import 'screens/auth/callback_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/splash_screen.dart';
import 'screens/projects/project_list_screen.dart';
import 'screens/projects/project_detail_screen.dart';

void main() {
  // Use path-based URLs instead of hash-based for web
  usePathUrlStrategy();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ProjectProvider()),
        ChangeNotifierProvider(create: (_) => ThreadProvider()),
      ],
      child: Builder(
        builder: (context) {
          return MaterialApp.router(
            title: 'Business Analyst Assistant',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: ThemeMode.system,
            routerConfig: _router(context),
            debugShowCheckedModeBanner: false,
          );
        },
      ),
    );
  }

  GoRouter _router(BuildContext context) {
    final authProvider = context.read<AuthProvider>();

    return GoRouter(
      initialLocation: '/splash',
      redirect: (context, state) {
        final isAuthenticated = authProvider.isAuthenticated;
        final isSplash = state.matchedLocation == '/splash';
        final isLogin = state.matchedLocation == '/login';
        final isCallback = state.matchedLocation == '/auth/callback';

        // Allow callback screen to process OAuth redirect
        if (isCallback) return null;

        // If authenticated and on splash/login, redirect to home
        if (isAuthenticated && (isSplash || isLogin)) {
          return '/home';
        }

        // If not authenticated and not on splash/login/callback, redirect to login
        if (!isAuthenticated && !isSplash && !isLogin && !isCallback) {
          return '/login';
        }

        return null; // No redirect needed
      },
      routes: [
        GoRoute(
          path: '/splash',
          builder: (context, state) => const SplashScreen(),
        ),
        GoRoute(
          path: '/login',
          builder: (context, state) => const LoginScreen(),
        ),
        GoRoute(
          path: '/auth/callback',
          builder: (context, state) => const CallbackScreen(),
        ),
        GoRoute(
          path: '/home',
          builder: (context, state) => const HomeScreen(),
        ),
        GoRoute(
          path: '/projects',
          builder: (context, state) => const ProjectListScreen(),
        ),
        GoRoute(
          path: '/projects/:id',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return ProjectDetailScreen(projectId: id);
          },
        ),
      ],
      refreshListenable: authProvider,
    );
  }
}
