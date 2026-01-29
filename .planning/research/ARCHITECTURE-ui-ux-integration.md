# Architecture Patterns: Flutter UI/UX Integration

**Project:** Business Analyst Assistant - Beta v1.5
**Domain:** Flutter cross-platform app with Provider state management
**Researched:** 2026-01-29

## Executive Summary

The Beta v1.5 UI/UX improvements should follow **minimal disruption architecture** by extending the existing Provider pattern with four new providers: NavigationProvider, ThemeProvider, DeletionProvider, and SettingsProvider. Each provider has clear boundaries and single responsibilities, integrating seamlessly with existing AuthProvider, ProjectProvider, DocumentProvider, ThreadProvider, and ConversationProvider.

**Key architectural decision:** Use Provider pattern consistently (not Riverpod/Bloc) to maintain velocity and avoid migration complexity. While Provider is considered "legacy" in 2026, it remains viable for this project's scale and the solo developer context.

**Integration strategy:** New providers coordinate with existing providers through notifications but do NOT create circular dependencies. NavigationProvider listens to AuthProvider for logout navigation. DeletionProvider notifies ProjectProvider/ThreadProvider/DocumentProvider after successful deletes. ThemeProvider operates independently.

## Recommended Architecture

### Provider Hierarchy and Dependencies

```
MaterialApp (root)
├── MultiProvider
    ├── AuthProvider (existing)
    ├── ThemeProvider (NEW - independent)
    ├── NavigationProvider (NEW - listens to AuthProvider)
    ├── SettingsProvider (NEW - reads from AuthProvider)
    ├── ProjectProvider (existing)
    ├── DocumentProvider (existing)
    ├── ThreadProvider (existing)
    ├── ConversationProvider (existing)
    └── DeletionProvider (NEW - coordinates with all CRUD providers)
```

**Dependency rules:**
- One-way dependencies only: New providers → Existing providers
- No circular dependencies: Existing providers do NOT reference new providers
- Communication via notifications: Providers use `notifyListeners()` to trigger UI updates
- Shared state access via `context.read<T>()` and `context.watch<T>()`

## Component Boundaries

### 1. NavigationProvider (NEW)

**Responsibility:** Manage navigation state across responsive breakpoints.

**State:**
```dart
class NavigationProvider extends ChangeNotifier {
  int _selectedIndex = 0;           // Current navigation destination
  bool _isSidebarExpanded = true;   // Desktop sidebar expanded/collapsed
  bool _isMobileDrawerOpen = false; // Mobile drawer open/closed
  String _currentRoute = '/home';   // Current route path

  // Getters
  int get selectedIndex => _selectedIndex;
  bool get isSidebarExpanded => _isSidebarExpanded;
  bool get isMobileDrawerOpen => _isMobileDrawerOpen;
  String get currentRoute => _currentRoute;

  // Methods
  void selectDestination(int index) { ... }
  void toggleSidebar() { ... }
  void openMobileDrawer() { ... }
  void closeMobileDrawer() { ... }
  void updateRoute(String route) { ... }
}
```

**Integration points:**
- **Listens to:** AuthProvider (via `context.read<AuthProvider>()`) to reset navigation on logout
- **Used by:** Scaffold widgets, navigation components (Drawer, NavigationRail)
- **Persistence:** None required (navigation state resets on app restart by design)

**When to rebuild:**
- User selects different destination
- Sidebar expand/collapse toggle
- Mobile drawer open/close
- Route changes (tracked via GoRouter listeners)

**Breakpoint logic:**
```dart
// In responsive layout builder
final width = MediaQuery.of(context).size.width;
if (width < 600) {
  // Mobile: Hamburger + Drawer
  return Scaffold(
    drawer: AppDrawer(),
    appBar: AppBar(leading: IconButton(...)),
  );
} else if (width < 900) {
  // Tablet: NavigationRail (collapsed sidebar)
  return Row(
    children: [
      NavigationRail(extended: false, ...),
      Expanded(child: content),
    ],
  );
} else {
  // Desktop: NavigationRail (expanded sidebar) or permanent Drawer
  return Row(
    children: [
      NavigationRail(extended: true, ...),
      Expanded(child: content),
    ],
  );
}
```

**Pitfall:** Do NOT persist `_isMobileDrawerOpen` across rebuilds. Drawer should close when route changes.

### 2. ThemeProvider (NEW)

**Responsibility:** Manage light/dark/system theme mode with persistence.

**State:**
```dart
class ThemeProvider extends ChangeNotifier {
  late SharedPreferences _prefs;
  ThemeMode _themeMode = ThemeMode.system;

  ThemeMode get themeMode => _themeMode;
  bool get isDarkMode => _themeMode == ThemeMode.dark;
  bool get isLightMode => _themeMode == ThemeMode.light;
  bool get isSystemMode => _themeMode == ThemeMode.system;

  // Initialize with persisted preference
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
    final modeString = _prefs.getString('theme_mode') ?? 'system';
    _themeMode = _parseThemeMode(modeString);
    notifyListeners();
  }

  // Update theme and persist
  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    await _prefs.setString('theme_mode', mode.toString());
    notifyListeners();
  }

  // Toggle between light and dark (for simple toggle switch)
  Future<void> toggleTheme() async {
    if (_themeMode == ThemeMode.dark) {
      await setThemeMode(ThemeMode.light);
    } else {
      await setThemeMode(ThemeMode.dark);
    }
  }
}
```

**Integration points:**
- **Listens to:** Nothing (fully independent)
- **Used by:** MaterialApp (themeMode parameter), Settings screen
- **Persistence:** SharedPreferences (`theme_mode` key)

**MaterialApp integration:**
```dart
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [...],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, _) {
          return MaterialApp.router(
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: themeProvider.themeMode, // Dynamic theme switching
            routerConfig: _router(context),
          );
        },
      ),
    );
  }
}
```

**When to rebuild:**
- User changes theme in Settings
- App initializes and loads persisted preference

**Why SharedPreferences (not secure storage):**
- Theme preference is non-sensitive data
- SharedPreferences is faster and simpler
- Secure storage (flutter_secure_storage) is for JWT tokens, not UI preferences

**Pitfall:** Must call `initialize()` before MaterialApp builds. Use FutureBuilder or initialization flag.

### 3. SettingsProvider (NEW - OPTIONAL)

**Responsibility:** Aggregate user settings from multiple sources.

**State:**
```dart
class SettingsProvider extends ChangeNotifier {
  final AuthProvider _authProvider;
  final ThemeProvider _themeProvider;

  SettingsProvider({
    required AuthProvider authProvider,
    required ThemeProvider themeProvider,
  })  : _authProvider = authProvider,
        _themeProvider = themeProvider;

  // Delegate to other providers
  String? get userEmail => _authProvider.email;
  String? get userId => _authProvider.userId;
  ThemeMode get themeMode => _themeProvider.themeMode;

  // Token budget (future: fetch from backend API)
  int? _tokenBudget;
  bool _loadingBudget = false;

  int? get tokenBudget => _tokenBudget;
  bool get loadingBudget => _loadingBudget;

  Future<void> loadTokenBudget() async {
    _loadingBudget = true;
    notifyListeners();

    try {
      // TODO: Call backend API to get token usage
      // final response = await _dio.get('/users/me/token-budget');
      // _tokenBudget = response.data['remaining'];
      _tokenBudget = 50000; // Placeholder
    } catch (e) {
      _tokenBudget = null;
    } finally {
      _loadingBudget = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _authProvider.logout();
  }

  Future<void> changeTheme(ThemeMode mode) async {
    await _themeProvider.setThemeMode(mode);
    notifyListeners(); // Notify settings screen to rebuild
  }
}
```

**Integration points:**
- **Depends on:** AuthProvider, ThemeProvider (passed via constructor or `context.read`)
- **Used by:** Settings screen
- **Persistence:** None (delegates to other providers)

**Why NOT just use AuthProvider/ThemeProvider directly in Settings screen?**
- Encapsulation: Settings screen has single provider dependency
- Future extensibility: Can add settings-specific logic (e.g., notification preferences, language)
- Aggregation: Token budget fetching belongs in settings context

**Alternative pattern (simpler):**
Settings screen can directly use `context.watch<AuthProvider>()` and `context.watch<ThemeProvider>()`. SettingsProvider is optional for this project's scale.

**Recommendation:** Skip SettingsProvider initially. Use direct provider access in Settings screen. Add SettingsProvider later if settings logic grows complex.

### 4. DeletionProvider (NEW)

**Responsibility:** Coordinate cascade deletes with optimistic UI updates and rollback.

**State:**
```dart
class DeletionProvider extends ChangeNotifier {
  final Dio _dio;
  String _baseUrl;

  bool _deleting = false;
  String? _error;

  bool get deleting => _deleting;
  String? get error => _error;

  /// Delete project with cascade (deletes threads, documents, messages)
  Future<bool> deleteProject(String projectId, ProjectProvider projectProvider) async {
    _deleting = true;
    _error = null;
    notifyListeners();

    // Save current state for rollback
    final projects = List<Project>.from(projectProvider.projects);
    final selectedProject = projectProvider.selectedProject;

    // Optimistic update: Remove from UI immediately
    final index = projects.indexWhere((p) => p.id == projectId);
    if (index != -1) {
      projects.removeAt(index);
      projectProvider._projects = projects; // Direct state mutation
      if (selectedProject?.id == projectId) {
        projectProvider._selectedProject = null;
      }
      projectProvider.notifyListeners();
    }

    try {
      // Backend cascade delete
      await _dio.delete('$_baseUrl/projects/$projectId');

      _deleting = false;
      notifyListeners();
      return true;
    } catch (e) {
      // Rollback: Restore previous state
      projectProvider._projects = projects;
      projectProvider._selectedProject = selectedProject;
      projectProvider.notifyListeners();

      _error = 'Delete failed: ${e.toString()}';
      _deleting = false;
      notifyListeners();
      return false;
    }
  }

  /// Delete thread
  Future<bool> deleteThread(String threadId, ThreadProvider threadProvider) async {
    // Similar pattern: optimistic update → backend call → rollback on error
    ...
  }

  /// Delete document
  Future<bool> deleteDocument(String documentId, DocumentProvider documentProvider) async {
    // Similar pattern
    ...
  }

  /// Delete individual message
  Future<bool> deleteMessage(String messageId, ConversationProvider conversationProvider) async {
    // Similar pattern
    ...
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
```

**Integration points:**
- **Depends on:** Dio (HTTP client), ProjectProvider, ThreadProvider, DocumentProvider, ConversationProvider
- **Used by:** Deletion confirmation dialogs
- **Persistence:** None (transient deletion state)

**Optimistic update pattern:**
1. Save current state (for rollback)
2. Immediately update UI (remove item from list)
3. Call backend API (cascade delete)
4. On success: State already updated, just mark done
5. On failure: Restore previous state, show error

**Why separate DeletionProvider (not methods in existing providers)?**
- Single Responsibility: Deletion logic with rollback is complex
- Cross-provider coordination: Deleting project affects ProjectProvider, ThreadProvider, DocumentProvider
- Error handling: Centralized rollback logic
- UI state: Manages "deleting" spinner state

**Pitfall:** Direct state mutation (`provider._projects = ...`) breaks encapsulation. Better approach:

```dart
// Add to existing providers
class ProjectProvider extends ChangeNotifier {
  void optimisticallyRemoveProject(String projectId) {
    _projects.removeWhere((p) => p.id == projectId);
    if (_selectedProject?.id == projectId) {
      _selectedProject = null;
    }
    notifyListeners();
  }

  void rollbackProject(Project project) {
    _projects.insert(0, project); // Add back
    notifyListeners();
  }
}
```

Then DeletionProvider calls:
```dart
final deletedProject = projects.firstWhere((p) => p.id == projectId);
projectProvider.optimisticallyRemoveProject(projectId);

try {
  await _dio.delete('$_baseUrl/projects/$projectId');
  return true;
} catch (e) {
  projectProvider.rollbackProject(deletedProject);
  return false;
}
```

**Recommendation:** Add `optimisticallyRemove*` and `rollback*` methods to existing providers. DeletionProvider orchestrates the flow.

## Data Flow Patterns

### Pattern 1: Responsive Navigation

```
User interaction (tap nav item)
    ↓
NavigationProvider.selectDestination(index)
    ↓
NavigationProvider._selectedIndex updated
    ↓
notifyListeners()
    ↓
Consumer<NavigationProvider> rebuilds
    ↓
GoRouter.go(routePath)
    ↓
Screen navigates
    ↓
NavigationProvider.updateRoute(newRoute) (called by route observer)
```

**Key insight:** NavigationProvider tracks BOTH user selection AND current route. This allows:
- Highlighting active nav item after deep link navigation
- Preserving selection across screen rebuilds
- Syncing nav state with GoRouter

**Implementation with GoRouter:**
```dart
GoRouter(
  routes: [...],
  observers: [NavigationObserver()], // Custom observer
);

class NavigationObserver extends NavigatorObserver {
  @override
  void didPush(Route route, Route? previousRoute) {
    final navProvider = context.read<NavigationProvider>();
    navProvider.updateRoute(route.settings.name ?? '/');
  }
}
```

### Pattern 2: Theme Toggle with Persistence

```
User toggles theme switch in Settings
    ↓
ThemeProvider.setThemeMode(ThemeMode.dark)
    ↓
SharedPreferences.setString('theme_mode', 'dark')
    ↓
ThemeProvider._themeMode = ThemeMode.dark
    ↓
notifyListeners()
    ↓
Consumer<ThemeProvider> in MaterialApp rebuilds
    ↓
MaterialApp.themeMode updated
    ↓
Flutter rebuilds entire widget tree with dark theme
```

**Performance concern:** Theme changes trigger full app rebuild. This is expected and acceptable (happens once per theme toggle).

**System preference sync:**
```dart
// Listen to system theme changes (optional enhancement)
import 'dart:ui' as ui;

void initState() {
  super.initState();
  ui.PlatformDispatcher.instance.onPlatformBrightnessChanged = () {
    if (themeProvider.isSystemMode) {
      // System brightness changed, trigger rebuild
      setState(() {});
    }
  };
}
```

### Pattern 3: Cascade Delete with Rollback

```
User taps delete button
    ↓
Show confirmation dialog
    ↓
User confirms
    ↓
DeletionProvider.deleteProject(projectId, projectProvider)
    ↓
[Optimistic Update Phase]
    DeletionProvider._deleting = true → Show spinner
    ProjectProvider.optimisticallyRemoveProject(projectId)
    UI shows project removed
    ↓
[Backend Phase]
    await dio.delete('/projects/$projectId')
    ↓
[Success Path]
    DeletionProvider._deleting = false
    Navigation back to projects list
    ↓
[Error Path]
    ProjectProvider.rollbackProject(deletedProject)
    DeletionProvider._error = 'Failed to delete'
    Show error snackbar
    Project reappears in list
```

**Why cascade delete on backend (not client)?**
- Data integrity: Backend enforces referential integrity
- Atomicity: Either all deletes succeed or none
- Performance: Client doesn't need to delete hundreds of messages individually

**Backend implementation (Python/FastAPI):**
```python
@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    # SQLAlchemy cascade delete (configured in models)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)  # Cascades to threads, documents, messages
    db.commit()
    return {"status": "deleted"}
```

### Pattern 4: Settings Screen Aggregation

**Simple approach (no SettingsProvider):**
```dart
class SettingsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final themeProvider = context.watch<ThemeProvider>();

    return Scaffold(
      body: Column(
        children: [
          // Profile section
          ListTile(
            title: Text(authProvider.email ?? 'Unknown'),
            subtitle: Text('User ID: ${authProvider.userId}'),
          ),

          // Theme toggle
          SwitchListTile(
            title: Text('Dark Mode'),
            value: themeProvider.isDarkMode,
            onChanged: (value) {
              themeProvider.setThemeMode(
                value ? ThemeMode.dark : ThemeMode.light,
              );
            },
          ),

          // Logout
          ListTile(
            title: Text('Logout'),
            onTap: () => authProvider.logout(),
          ),
        ],
      ),
    );
  }
}
```

**Complex approach (with SettingsProvider):**
Only needed if settings screen has its own complex state (e.g., unsaved changes, validation).

## Integration Strategy with Existing Providers

### Constraint: No Breaking Changes

Existing screens must continue working without modification until UI/UX phase.

**Strategy:**
1. Add new providers to MultiProvider in main.dart
2. New screens use new providers
3. Existing screens ignore new providers
4. Gradual migration as screens are updated

**main.dart update:**
```dart
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Existing providers (unchanged)
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ConversationProvider()),
        ChangeNotifierProvider(create: (_) => ProjectProvider()),
        ChangeNotifierProvider(create: (_) => DocumentProvider()),
        ChangeNotifierProvider(create: (_) => ThreadProvider()),

        // NEW providers for Beta v1.5
        ChangeNotifierProvider(
          create: (_) => ThemeProvider()..initialize(),
        ),
        ChangeNotifierProvider(create: (_) => NavigationProvider()),
        ChangeNotifierProvider(create: (_) => DeletionProvider()),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, _) {
          return MaterialApp.router(
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: themeProvider.themeMode, // NEW: Dynamic theme
            routerConfig: _router(context),
          );
        },
      ),
    );
  }
}
```

### Coordination Rules

**Rule 1: New providers listen to existing providers**
- NavigationProvider listens to AuthProvider (logout navigation)
- SettingsProvider reads from AuthProvider/ThemeProvider

**Rule 2: Existing providers do NOT reference new providers**
- ProjectProvider does NOT import NavigationProvider
- AuthProvider does NOT import ThemeProvider

**Rule 3: Communication via notifications**
```dart
// GOOD: NavigationProvider listens to AuthProvider
class NavigationProvider extends ChangeNotifier {
  void resetOnLogout(BuildContext context) {
    context.read<AuthProvider>().addListener(() {
      if (!context.read<AuthProvider>().isAuthenticated) {
        _selectedIndex = 0;
        _currentRoute = '/login';
        notifyListeners();
      }
    });
  }
}

// BAD: Circular dependency
class AuthProvider extends ChangeNotifier {
  NavigationProvider? _navProvider; // NO! Circular dependency
}
```

### Migration Path

**Phase 1: Add new providers (non-breaking)**
- Add ThemeProvider, NavigationProvider, DeletionProvider to MultiProvider
- No UI changes yet
- Verify app still works

**Phase 2: Implement Settings screen**
- New screen uses AuthProvider + ThemeProvider
- Add logout functionality
- Add theme toggle

**Phase 3: Add sidebar navigation**
- Update Scaffold in existing screens to include NavigationRail/Drawer
- Use NavigationProvider to track selection
- Responsive layout based on breakpoints

**Phase 4: Add deletion flows**
- Add delete buttons to Project/Thread/Document screens
- Use DeletionProvider for optimistic updates
- Add confirmation dialogs

**Phase 5: Polish**
- Update empty states
- Add breadcrumbs
- Improve date formatting

## Architecture Anti-Patterns (Avoid)

### Anti-Pattern 1: Global State Singletons

**BAD:**
```dart
class NavigationState {
  static final NavigationState instance = NavigationState._();
  NavigationState._();

  int selectedIndex = 0;
  // No notifyListeners, no reactivity
}
```

**Why bad:** Global singletons bypass Provider's dependency injection and notification system. Widgets can't rebuild when state changes.

**GOOD:** Use Provider pattern consistently.

### Anti-Pattern 2: Circular Provider Dependencies

**BAD:**
```dart
class ThemeProvider extends ChangeNotifier {
  late NavigationProvider _navProvider; // Circular!
}

class NavigationProvider extends ChangeNotifier {
  late ThemeProvider _themeProvider; // Circular!
}
```

**Why bad:** Circular dependencies cause initialization issues and make testing impossible.

**GOOD:** One-way dependencies. Use `context.read<T>()` to access providers when needed.

### Anti-Pattern 3: Over-nesting Consumers

**BAD:**
```dart
Consumer<AuthProvider>(
  builder: (context, auth, _) => Consumer<ThemeProvider>(
    builder: (context, theme, _) => Consumer<NavigationProvider>(
      builder: (context, nav, _) => Widget(...),
    ),
  ),
)
```

**Why bad:** Hard to read, excessive nesting.

**GOOD:** Use `context.watch<T>()` in build method or single Consumer with multiple providers:
```dart
Widget build(BuildContext context) {
  final auth = context.watch<AuthProvider>();
  final theme = context.watch<ThemeProvider>();
  final nav = context.watch<NavigationProvider>();

  return Widget(...);
}
```

### Anti-Pattern 4: Business Logic in Widgets

**BAD:**
```dart
class ProjectScreen extends StatelessWidget {
  Future<void> _deleteProject(String id) async {
    // Optimistic update logic in widget
    setState(() { projects.remove(id); });
    try {
      await dio.delete('/projects/$id');
    } catch (e) {
      setState(() { projects.add(id); }); // Rollback
    }
  }
}
```

**Why bad:** Widget is responsible for both UI and business logic. Hard to test, violates separation of concerns.

**GOOD:** Move deletion logic to DeletionProvider.

### Anti-Pattern 5: Storing Dio/Storage Instances in Providers

**BAD:**
```dart
class ThemeProvider extends ChangeNotifier {
  final FlutterSecureStorage _storage = FlutterSecureStorage(); // Hardcoded
}
```

**Why bad:** Can't inject mocks for testing.

**GOOD:**
```dart
class ThemeProvider extends ChangeNotifier {
  final SharedPreferences _prefs; // Injected via constructor

  ThemeProvider({required SharedPreferences prefs}) : _prefs = prefs;
}
```

## Build Order and Dependencies

### Suggested Implementation Order

**Milestone 1: Foundation (Week 1)**
1. ThemeProvider + SharedPreferences persistence
2. Update MaterialApp to use ThemeProvider
3. Settings screen (logout + theme toggle)
4. Test theme persistence across app restarts

**Milestone 2: Navigation (Week 1-2)**
1. NavigationProvider
2. Responsive layout helper (breakpoint logic)
3. Mobile Drawer component
4. Desktop NavigationRail component
5. Update existing screens to use new navigation
6. Test navigation state across routes

**Milestone 3: Deletion (Week 2)**
1. Backend cascade delete endpoints (Python/FastAPI)
2. DeletionProvider with optimistic updates
3. Confirmation dialog component
4. Delete buttons in Project/Thread/Document screens
5. Test rollback on network failures

**Milestone 4: Polish (Week 2-3)**
1. Empty state components
2. Breadcrumb navigation
3. Date formatting utilities
4. Enhanced Home screen
5. Visual consistency pass

**Dependencies:**
- ThemeProvider is independent (can be built first)
- NavigationProvider depends on ThemeProvider (for sidebar theming)
- DeletionProvider depends on navigation (post-delete navigation)
- Settings screen depends on ThemeProvider + AuthProvider

### Critical Path

```
ThemeProvider → Settings screen → NavigationProvider → Deletion flows → Polish
    ↓                                      ↓
MaterialApp theme switching         Responsive layouts
```

**Blocker:** ThemeProvider must be complete before Settings screen. Settings screen should be complete before NavigationProvider (Settings is a navigation destination).

## Responsive Layout Strategy

### Breakpoints (Already Defined)

- **Mobile:** < 600px
- **Tablet:** 600-900px
- **Desktop:** ≥ 900px

### Navigation Pattern by Breakpoint

| Breakpoint | Navigation UI | Behavior |
|------------|---------------|----------|
| Mobile (<600px) | Hamburger + Drawer | Drawer slides in from left, closes on route change |
| Tablet (600-900px) | NavigationRail (collapsed) | Always visible, icons only, no labels |
| Desktop (≥900px) | NavigationRail (expanded) | Always visible, icons + labels |

### Implementation Pattern

```dart
class ResponsiveScaffold extends StatelessWidget {
  final Widget body;
  final String title;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final navProvider = context.watch<NavigationProvider>();

    if (width < 600) {
      // Mobile: Hamburger + Drawer
      return Scaffold(
        appBar: AppBar(
          title: Text(title),
          leading: IconButton(
            icon: Icon(Icons.menu),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        drawer: AppDrawer(),
        body: body,
      );
    } else {
      // Tablet/Desktop: Sidebar + Content
      return Scaffold(
        body: Row(
          children: [
            AppNavigationRail(extended: width >= 900),
            Expanded(
              child: Column(
                children: [
                  AppBar(title: Text(title), automaticallyImplyLeading: false),
                  Expanded(child: body),
                ],
              ),
            ),
          ],
        ),
      );
    }
  }
}
```

**Key insight:** Use a single `ResponsiveScaffold` wrapper for all screens. This ensures consistent navigation behavior.

### When to Switch Layout

**Trigger:** MediaQuery width change (device rotation, window resize)

**Behavior:**
- Layout switches instantly (no animation)
- Navigation state preserved (selectedIndex stays same)
- Drawer closes if switching from mobile to tablet/desktop
- No route change (user stays on same screen)

**Implementation:**
```dart
// ResponsiveScaffold automatically handles layout switching
// No manual logic needed
Widget build(BuildContext context) {
  return ResponsiveScaffold(
    title: 'Projects',
    body: ProjectListView(),
  );
}
```

## Testing Considerations

### Unit Testing Providers

**Pattern:**
```dart
void main() {
  group('ThemeProvider', () {
    late ThemeProvider provider;
    late MockSharedPreferences mockPrefs;

    setUp(() {
      mockPrefs = MockSharedPreferences();
      provider = ThemeProvider(prefs: mockPrefs);
    });

    test('initializes with system theme by default', () {
      expect(provider.themeMode, ThemeMode.system);
    });

    test('persists theme change to SharedPreferences', () async {
      await provider.setThemeMode(ThemeMode.dark);

      verify(mockPrefs.setString('theme_mode', 'ThemeMode.dark')).called(1);
      expect(provider.themeMode, ThemeMode.dark);
    });
  });
}
```

### Integration Testing Navigation

**Pattern:**
```dart
void main() {
  testWidgets('Navigation persists selection across route changes', (tester) async {
    await tester.pumpWidget(MyApp());

    // Tap Projects nav item
    await tester.tap(find.byIcon(Icons.folder));
    await tester.pumpAndSettle();

    // Verify route changed
    expect(find.text('Projects'), findsOneWidget);

    // Verify nav item still selected after rebuild
    final navProvider = tester.element(find.byType(MyApp))
        .read<NavigationProvider>();
    expect(navProvider.selectedIndex, 1); // Projects index
  });
}
```

### Testing Optimistic Updates

**Pattern:**
```dart
void main() {
  test('DeletionProvider rolls back on error', () async {
    final mockDio = MockDio();
    final projectProvider = ProjectProvider();
    final deletionProvider = DeletionProvider(dio: mockDio);

    // Setup: Project list with one project
    projectProvider._projects = [Project(id: '1', name: 'Test')];

    // Mock backend error
    when(mockDio.delete(any)).thenThrow(DioException(type: DioExceptionType.connectionError));

    // Execute delete
    final success = await deletionProvider.deleteProject('1', projectProvider);

    // Verify: Rollback occurred
    expect(success, false);
    expect(projectProvider.projects.length, 1);
    expect(deletionProvider.error, isNotNull);
  });
}
```

## Sources

- [Flutter Provider Official Docs - Simple State Management](https://docs.flutter.dev/data-and-backend/state-mgmt/simple)
- [Best Flutter State Management Libraries 2026 - Foresight Mobile](https://foresightmobile.com/blog/best-flutter-state-management)
- [Flutter Optimistic State Pattern - Official Docs](https://docs.flutter.dev/app-architecture/design-patterns/optimistic-state)
- [adaptive_theme Package - Theme Persistence](https://pub.dev/packages/adaptive_theme)
- [SharedPreferences vs Secure Storage - Program Tom](https://programtom.com/dev/2024/07/01/flutter-shared_preferences-and-secure_storage/)
- [Responsive Layouts in Flutter - Code With Andrea](https://codewithandrea.com/articles/flutter-responsive-layouts-split-view-drawer-navigation/)
- [Optimistic State in Flutter Explained - Medium](https://medium.com/@geraldnuraj/optimistic-state-in-flutter-explained-3dec68ae6252)
- [Flutter Store Key-Value Data on Disk](https://docs.flutter.dev/cookbook/persistence/key-value)

---

## Confidence Assessment

| Component | Confidence | Rationale |
|-----------|------------|-----------|
| Provider integration | HIGH | Existing codebase uses Provider consistently, patterns are well-established |
| Theme persistence | HIGH | SharedPreferences is standard approach for non-sensitive settings |
| Navigation state | HIGH | NavigationRail/Drawer patterns are documented by Flutter team |
| Optimistic updates | MEDIUM | Pattern is well-known, but rollback implementation requires careful testing |
| Responsive breakpoints | HIGH | Project already defines breakpoints, implementation is straightforward |

## Open Questions for Phase-Specific Research

1. **Token budget API**: How should Settings screen fetch token usage? New backend endpoint needed?
2. **Navigation deep linking**: Should NavigationProvider sync with GoRouter's redirect logic?
3. **Deletion confirmation UX**: Modal dialog vs. bottom sheet? Platform-specific patterns?
4. **Theme transition animation**: Should theme switches animate or change instantly?
5. **Sidebar collapse persistence**: Should desktop sidebar expanded/collapsed state persist across app restarts?

These questions can be answered during implementation phase with quick prototyping.
