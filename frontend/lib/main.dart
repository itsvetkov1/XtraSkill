import 'dart:ui' show PlatformDispatcher;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'core/theme.dart';
import 'utils/date_formatter.dart';
import 'utils/logging_observer.dart';
import 'services/logging_service.dart';
import 'providers/auth_provider.dart';
import 'providers/budget_provider.dart';
import 'providers/conversation_provider.dart';
import 'providers/document_column_provider.dart';
import 'providers/document_provider.dart';
import 'providers/project_provider.dart';
import 'providers/navigation_provider.dart';
import 'providers/theme_provider.dart';
import 'providers/provider_provider.dart';
import 'providers/thread_provider.dart';
import 'providers/chats_provider.dart';
import 'screens/auth/callback_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/chats_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/splash_screen.dart';
import 'screens/not_found_screen.dart';
import 'screens/projects/project_list_screen.dart';
import 'screens/projects/project_detail_screen.dart';
import 'screens/conversation/conversation_screen.dart';
import 'screens/documents/document_viewer_screen.dart';
import 'widgets/responsive_scaffold.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize date formatting locales for intl package (POLISH-01)
  await initializeDateFormatting();
  DateFormatter.init();

  // Load preferences to prevent state flash on startup (SET-06, NAV-01)
  final prefs = await SharedPreferences.getInstance();
  final themeProvider = await ThemeProvider.load(prefs);
  final navigationProvider = await NavigationProvider.load(prefs);
  final providerProvider = await ProviderProvider.load(prefs);

  // Initialize logging service with connectivity monitoring
  final loggingService = LoggingService();
  loggingService.init();

  // Global error handlers to prevent crashes and log errors
  FlutterError.onError = (FlutterErrorDetails details) {
    FlutterError.presentError(details); // Still show in console
    loggingService.logError(
      details.exception,
      details.stack,
      context: 'FlutterError: ${details.context}',
    );
  };

  PlatformDispatcher.instance.onError = (error, stack) {
    loggingService.logError(error, stack, context: 'PlatformError');
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

  // Enable URL reflection for browser history consistency (ROUTE-02)
  // Ensures browser back/forward works correctly with context.go() calls
  GoRouter.optionURLReflectsImperativeAPIs = true;

  // Use path-based URLs instead of hash-based for web
  usePathUrlStrategy();
  runApp(MyApp(
    themeProvider: themeProvider,
    navigationProvider: navigationProvider,
    providerProvider: providerProvider,
  ));
}

class MyApp extends StatefulWidget {
  final ThemeProvider themeProvider;
  final NavigationProvider navigationProvider;
  final ProviderProvider providerProvider;

  const MyApp({
    super.key,
    required this.themeProvider,
    required this.navigationProvider,
    required this.providerProvider,
  });

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
        ChangeNotifierProvider.value(value: widget.navigationProvider),
        ChangeNotifierProvider.value(value: widget.providerProvider),
        ChangeNotifierProvider(create: (_) => DocumentColumnProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => BudgetProvider()),
        ChangeNotifierProvider(create: (_) => ConversationProvider()),
        ChangeNotifierProvider(create: (_) => ProjectProvider()),
        ChangeNotifierProvider(create: (_) => DocumentProvider()),
        ChangeNotifierProvider(create: (_) => ThreadProvider()),
        ChangeNotifierProvider(create: (_) => ChatsProvider()),
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

  /// Derive selected navigation index from current path for proper sidebar highlighting
  ///
  /// This handles nested routes (e.g., /projects/:id highlights Projects)
  int _getSelectedIndex(String path) {
    if (path.startsWith('/home')) return 0;
    if (path.startsWith('/chats')) return 1;
    if (path.startsWith('/projects')) return 2;
    if (path.startsWith('/settings')) return 3;
    return 0; // Default to home
  }

  GoRouter _createRouter(BuildContext context) {
    final authProvider = context.read<AuthProvider>();

    return GoRouter(
      initialLocation: '/splash',
      observers: [LoggingNavigatorObserver()],
      redirect: (context, state) {
        final isAuthenticated = authProvider.isAuthenticated;
        final isLoading = authProvider.isLoading;
        final currentPath = state.matchedLocation;
        final currentUri = state.uri;
        final isSplash = currentPath == '/splash';
        final isLogin = currentPath == '/login';
        final isCallback = currentPath == '/auth/callback';

        // Extract existing returnUrl from query params
        final existingReturnUrl = currentUri.queryParameters['returnUrl'];

        // Callback: let CallbackScreen handle navigation (it reads from sessionStorage)
        if (isCallback) {
          return null; // Stay on callback, it handles its own navigation
        }

        // Authenticated user on splash/login: go to returnUrl or /home
        if (isAuthenticated && (isSplash || isLogin)) {
          if (existingReturnUrl != null) {
            return Uri.decodeComponent(existingReturnUrl);
          }
          return '/home';
        }

        // Loading: redirect to splash, preserve returnUrl
        // CRITICAL: Use state.uri.toString() to capture full URL including query params
        if (isLoading && !isSplash && !isLogin && !isCallback) {
          final intendedUrl = currentUri.toString();
          return '/splash?returnUrl=${Uri.encodeComponent(intendedUrl)}';
        }

        // Splash done loading, not authenticated: go to login with returnUrl
        if (isSplash && !isLoading && !isAuthenticated) {
          if (existingReturnUrl != null) {
            return '/login?returnUrl=$existingReturnUrl'; // Already encoded
          }
          return '/login';
        }

        // Unauthenticated on protected route: redirect to login with returnUrl
        if (!isAuthenticated && !isLoading && !isSplash && !isLogin && !isCallback) {
          final intendedUrl = currentUri.toString();
          return '/login?returnUrl=${Uri.encodeComponent(intendedUrl)}';
        }

        return null; // No redirect needed
      },
      routes: [
        // Unauthenticated routes OUTSIDE shell
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

        // Authenticated routes INSIDE shell with StatefulShellRoute.indexedStack
        // Each branch maintains its own navigation stack for state preservation
        StatefulShellRoute.indexedStack(
          builder: (context, state, navigationShell) {
            // Derive index from path for proper highlighting on nested routes
            // Using state.uri.path instead of navigationShell.currentIndex
            // ensures /projects/:id highlights Projects (index 1)
            final selectedIndex = _getSelectedIndex(state.uri.path);
            return ResponsiveScaffold(
              currentIndex: selectedIndex,
              onDestinationSelected: (index) {
                // Always go to initial location of the branch
                // This ensures Chats shows the list, not the last visited chat
                navigationShell.goBranch(index, initialLocation: true);
              },
              child: navigationShell,
            );
          },
          branches: [
            // Branch 0: Home
            StatefulShellBranch(
              routes: [
                GoRoute(
                  path: '/home',
                  builder: (context, state) => const HomeScreen(),
                ),
              ],
            ),
            // Branch 1: Chats (global threads)
            StatefulShellBranch(
              routes: [
                GoRoute(
                  path: '/chats',
                  builder: (context, state) => const ChatsScreen(),
                  routes: [
                    // Nested route for project-less thread conversation
                    GoRoute(
                      path: ':threadId',
                      builder: (context, state) {
                        final threadId = state.pathParameters['threadId']!;
                        return ConversationScreen(
                          projectId: null, // Project-less thread
                          threadId: threadId,
                        );
                      },
                    ),
                  ],
                ),
              ],
            ),
            // Branch 2: Projects (includes nested project detail route)
            StatefulShellBranch(
              routes: [
                GoRoute(
                  path: '/projects',
                  builder: (context, state) => const ProjectListScreen(),
                  routes: [
                    GoRoute(
                      path: ':id',
                      builder: (context, state) {
                        final id = state.pathParameters['id']!;
                        return ProjectDetailScreen(projectId: id);
                      },
                      routes: [
                        GoRoute(
                          path: 'threads/:threadId',
                          builder: (context, state) {
                            final projectId = state.pathParameters['id']!;
                            final threadId = state.pathParameters['threadId']!;
                            return ConversationScreen(
                              projectId: projectId,
                              threadId: threadId,
                            );
                          },
                        ),
                        GoRoute(
                          path: 'documents/:docId',
                          builder: (context, state) {
                            final docId = state.pathParameters['docId']!;
                            return DocumentViewerScreen(documentId: docId);
                          },
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
            // Branch 3: Settings
            StatefulShellBranch(
              routes: [
                GoRoute(
                  path: '/settings',
                  builder: (context, state) => const SettingsScreen(),
                ),
              ],
            ),
          ],
        ),
      ],
      refreshListenable: authProvider,
      errorBuilder: (context, state) {
        return NotFoundScreen(attemptedPath: state.uri.path);
      },
    );
  }
}
