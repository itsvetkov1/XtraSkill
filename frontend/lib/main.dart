import 'dart:ui' show PlatformDispatcher;

import 'package:flutter/foundation.dart' show kReleaseMode;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core/theme.dart';
import 'providers/auth_provider.dart';
import 'providers/conversation_provider.dart';
import 'providers/document_provider.dart';
import 'providers/project_provider.dart';
import 'providers/theme_provider.dart';
import 'providers/thread_provider.dart';
import 'screens/auth/callback_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/splash_screen.dart';
import 'screens/projects/project_list_screen.dart';
import 'screens/projects/project_detail_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load theme preference to prevent white flash on dark mode (SET-06)
  final prefs = await SharedPreferences.getInstance();
  final themeProvider = await ThemeProvider.load(prefs);

  // Global error handlers to prevent crashes
  FlutterError.onError = (FlutterErrorDetails details) {
    FlutterError.presentError(details);
    if (kReleaseMode) {
      print('FlutterError: ${details.exception}');
      print('StackTrace: ${details.stack}');
    }
  };

  PlatformDispatcher.instance.onError = (error, stack) {
    print('PlatformError: $error');
    print('StackTrace: $stack');
    return true; // Mark error as handled
  };

  ErrorWidget.builder = (FlutterErrorDetails details) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Something went wrong', style: TextStyle(fontSize: 18)),
            SizedBox(height: 8),
            Text('Please restart the app', style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  };

  // Use path-based URLs instead of hash-based for web
  usePathUrlStrategy();
  runApp(MyApp(themeProvider: themeProvider));
}

class MyApp extends StatefulWidget {
  final ThemeProvider themeProvider;

  const MyApp({super.key, required this.themeProvider});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late final GoRouter _routerInstance;
  bool _isRouterInitialized = false;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: widget.themeProvider),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ConversationProvider()),
        ChangeNotifierProvider(create: (_) => ProjectProvider()),
        ChangeNotifierProvider(create: (_) => DocumentProvider()),
        ChangeNotifierProvider(create: (_) => ThreadProvider()),
      ],
      child: Builder(
        builder: (context) {
          // Ensure router is initialized after providers are available
          if (!_isRouterInitialized) {
            _routerInstance = _createRouter(context);
            _isRouterInitialized = true;
          }

          return Consumer<ThemeProvider>(
            builder: (context, theme, _) {
              return MaterialApp.router(
                title: 'Business Analyst Assistant',
                theme: AppTheme.lightTheme,
                darkTheme: AppTheme.darkTheme,
                themeMode: theme.themeMode,
                routerConfig: _routerInstance,
                debugShowCheckedModeBanner: false,
              );
            },
          );
        },
      ),
    );
  }

  GoRouter _createRouter(BuildContext context) {
    final authProvider = context.read<AuthProvider>();

    return GoRouter(
      initialLocation: '/splash',
      redirect: (context, state) {
        final isAuthenticated = authProvider.isAuthenticated;
        final isLoading = authProvider.isLoading;
        final isSplash = state.matchedLocation == '/splash';
        final isLogin = state.matchedLocation == '/login';
        final isCallback = state.matchedLocation == '/auth/callback';

        // Callback screen: redirect to home when authenticated (processing complete)
        // Stay on callback if not authenticated (still processing or error)
        if (isCallback) {
          return isAuthenticated ? '/home' : null;
        }

        // If authenticated and on splash/login, redirect to home
        if (isAuthenticated && (isSplash || isLogin)) {
          return '/home';
        }

        // CRITICAL: If auth check is still loading, redirect to splash to wait
        // This prevents premature redirects to login when navigating directly to
        // protected routes (e.g., /settings) before auth state is restored
        if (isLoading && !isSplash && !isLogin && !isCallback) {
          return '/splash';
        }

        // If on splash and auth check complete (not loading) and not authenticated,
        // redirect to login
        if (isSplash && !isLoading && !isAuthenticated) {
          return '/login';
        }

        // If not authenticated (and not loading) and not on splash/login/callback,
        // redirect to login
        if (!isAuthenticated && !isLoading && !isSplash && !isLogin && !isCallback) {
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
        GoRoute(
          path: '/settings',
          builder: (context, state) => const SettingsScreen(),
        ),
      ],
      refreshListenable: authProvider,
    );
  }
}
