# Pitfalls Research: Flutter UI/UX Excellence

**Domain:** Flutter Navigation, Theming, Deletion, and Polish Features
**Researched:** 2026-01-29
**Confidence:** HIGH

**Project Context:** Business Analyst Assistant Beta v1.5
- Solo developer with limited testing capacity
- Cross-platform deployment (web, Android, iOS)
- Existing MVP users (breaking changes not acceptable)
- Executive demos upcoming (polish critical, bugs highly visible)

## Critical Pitfalls

### Pitfall 1: BuildContext Used Across Async Gaps

**What goes wrong:**
Deletion confirmations, theme switches, and navigation operations fail with `use_build_context_synchronously` lint errors or crash with `setState() called after dispose()`. The widget showing the confirmation dialog or snackbar is disposed while async operations (database deletes, API calls) are still running, causing context operations to fail.

**Why it happens:**
Flutter's linter detects when BuildContext is used after an `await` statement. During the async gap, the widget may be removed from the tree (user navigates away, parent rebuilds), making the context invalid. Common in deletion workflows: show dialog → await user response → await database delete → show snackbar confirmation.

**How to avoid:**
```dart
// ✅ CORRECT: Check mounted before using context
Future<void> deleteProject(BuildContext context, String projectId) async {
  final confirmed = await showDialog<bool>(/*...*/);
  if (!context.mounted) return;  // Check after first async gap

  if (confirmed == true) {
    await apiService.deleteProject(projectId);
    if (!context.mounted) return;  // Check after second async gap

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Project deleted')),
    );
  }
}

// ❌ WRONG: Using context without checking mounted
Future<void> deleteProject(BuildContext context, String projectId) async {
  final confirmed = await showDialog<bool>(/*...*/);
  if (confirmed == true) {
    await apiService.deleteProject(projectId);
    ScaffoldMessenger.of(context).showSnackBar(/*...*/);  // May crash
  }
}
```

**Warning signs:**
- Lint warnings: `use_build_context_synchronously`
- Runtime exceptions: `setState() called after dispose()`
- Snackbars don't appear after deletions
- Navigation operations fail silently

**Phase to address:**
Beta v1.5 deletion feature implementation — enforce `context.mounted` checks in code review for all async operations involving Navigator, dialogs, or ScaffoldMessenger.

---

### Pitfall 2: SQLite Foreign Keys Disabled by Default

**What goes wrong:**
Deleting a project doesn't cascade to threads, documents, and messages. Orphaned data accumulates in the database. Users see deleted projects' threads still appearing in lists, or clicking into a thread shows "Project not found" errors.

**Why it happens:**
SQLite disables foreign key constraints by default for backward compatibility. Even if you define `ON DELETE CASCADE` in table schemas, the constraints are silently ignored unless `PRAGMA foreign_keys = ON` is executed on every database connection. The sqflite plugin doesn't enable this automatically.

**How to avoid:**
```dart
// ✅ CORRECT: Enable foreign keys on every connection
Future<Database> _initDatabase() async {
  final db = await openDatabase(
    path,
    version: 1,
    onCreate: (db, version) async {
      await db.execute('PRAGMA foreign_keys = ON');  // Enable BEFORE creating tables
      await _createTables(db);
    },
    onOpen: (db) async {
      await db.execute('PRAGMA foreign_keys = ON');  // Enable on existing DB
    },
  );
  return db;
}

// Verify in tests
test('foreign keys are enabled', () async {
  final result = await db.rawQuery('PRAGMA foreign_keys');
  expect(result.first['foreign_keys'], 1);  // 1 = enabled, 0 = disabled
});

// ❌ WRONG: Assuming CASCADE works without PRAGMA
await db.execute('''
  CREATE TABLE threads (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
  )
''');
// ^ This constraint is IGNORED without PRAGMA
```

**Warning signs:**
- Orphaned records in database after deletions
- `SELECT COUNT(*) FROM threads WHERE project_id NOT IN (SELECT id FROM projects)` returns non-zero
- Foreign key violations don't throw errors when they should
- Database size keeps growing despite deletions

**Phase to address:**
Beta v1.5 deletion implementation — add `PRAGMA foreign_keys = ON` in database initialization, write integration tests verifying cascade deletes work correctly across all entity types.

---

### Pitfall 3: SharedPreferences Theme Persistence Not Guaranteed

**What goes wrong:**
User switches to dark theme, app restarts, theme reverts to light mode. Especially common on web platform where SharedPreferences data becomes inaccessible after page reload despite being in browser localStorage. On iOS, users report settings "forgotten" between app launches.

**Why it happens:**
SharedPreferences documentation explicitly states: "Data may be persisted to disk asynchronously, and there is no guarantee that writes will be persisted to disk after returning." The plugin cannot guarantee persistence across app restarts. On web, timing issues cause data to be written after the page unloads. On iOS, background app termination may happen before async writes complete.

**How to avoid:**
```dart
// ✅ CORRECT: Use SharedPreferencesAsync (Flutter 3.7+) or verify writes
import 'package:shared_preferences/shared_preferences.dart';

class ThemeService {
  static const _themeKey = 'theme_mode';

  Future<void> saveThemeMode(ThemeMode mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_themeKey, mode.toString());

    // Verify write succeeded
    final verified = prefs.getString(_themeKey);
    if (verified != mode.toString()) {
      throw Exception('Theme persistence failed - retry');
    }
  }

  Future<ThemeMode> loadThemeMode() async {
    final prefs = await SharedPreferences.getInstance();
    final stored = prefs.getString(_themeKey);

    if (stored == null) {
      // No stored preference - use system default
      return ThemeMode.system;
    }

    return ThemeMode.values.firstWhere(
      (e) => e.toString() == stored,
      orElse: () => ThemeMode.system,
    );
  }
}

// Initialize theme BEFORE MaterialApp builds
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final themeMode = await ThemeService().loadThemeMode();

  runApp(MyApp(initialTheme: themeMode));
}

// ❌ WRONG: Fire-and-forget writes, load after MaterialApp builds
void saveTheme(ThemeMode mode) {
  SharedPreferences.getInstance().then((prefs) {
    prefs.setString('theme', mode.toString());  // May not persist
  });
}
```

**Warning signs:**
- User complaints about settings not persisting
- Inconsistent theme behavior between sessions
- Web console shows localStorage access timing errors
- Theme flickers to default then switches on startup (FOUC equivalent)

**Phase to address:**
Beta v1.5 Settings page implementation — load theme before MaterialApp initialization, add retry logic for failed writes, verify theme persistence in integration tests across all three platforms.

---

### Pitfall 4: Theme Flash on App Startup (FOUC)

**What goes wrong:**
App loads with light theme for 100-500ms, then switches to dark theme. Users see white flash before dark theme applies. Especially jarring in dark environments. Called "Flash of Unstyled Content" in web development, Flutter equivalent happens when theme loads after MaterialApp builds.

**Why it happens:**
MaterialApp initializes with default theme immediately while async SharedPreferences loading happens in background. The widget tree builds with light theme, then rebuilds when stored theme loads, causing visible flash.

**How to avoid:**
```dart
// ✅ CORRECT: Load theme BEFORE MaterialApp
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load theme synchronously before app starts
  final prefs = await SharedPreferences.getInstance();
  final storedTheme = prefs.getString('theme_mode');
  final initialTheme = storedTheme != null
    ? ThemeMode.values.firstWhere((e) => e.toString() == storedTheme)
    : ThemeMode.system;

  runApp(MyApp(initialTheme: initialTheme));
}

class MyApp extends StatefulWidget {
  final ThemeMode initialTheme;

  const MyApp({required this.initialTheme});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late ThemeMode _themeMode;

  @override
  void initState() {
    super.initState();
    _themeMode = widget.initialTheme;  // Use pre-loaded theme
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      themeMode: _themeMode,  // Already loaded - no flash
      theme: ThemeData.light(),
      darkTheme: ThemeData.dark(),
      // ...
    );
  }
}

// ❌ WRONG: Load theme after MaterialApp builds
class MyApp extends StatefulWidget {
  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  ThemeMode _themeMode = ThemeMode.light;  // Defaults to light

  @override
  void initState() {
    super.initState();
    _loadTheme();  // Async - causes flash
  }

  Future<void> _loadTheme() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _themeMode = /* load from prefs */;  // Rebuild - flash!
    });
  }
}
```

**Warning signs:**
- White flash visible on app launch (especially in dark mode)
- Material color transitions on startup
- Theme "pops in" after brief delay
- E2E tests capture screenshots showing theme inconsistency

**Phase to address:**
Beta v1.5 Settings page implementation — move theme loading to `main()` before `runApp()`, test theme initialization on all platforms, verify no flash in manual testing.

---

### Pitfall 5: MediaQuery Rebuild Thrashing in Responsive Layouts

**What goes wrong:**
Sidebar switches between NavigationDrawer and NavigationRail repeatedly when window is resized near breakpoint (e.g., 600px). Each switch triggers expensive rebuilds of the entire widget tree. App becomes unresponsive during window resizing. Layout "stutters" or flickers between states.

**Why it happens:**
Using `MediaQuery.of(context)` causes widget to rebuild on every MediaQuery change (size, padding, orientation, platform brightness, etc.). During window resize, MediaQuery updates continuously. Without optimization, every pixel change triggers full tree rebuild. Threshold checks without hysteresis cause thrashing when size oscillates around breakpoint.

**How to avoid:**
```dart
// ✅ CORRECT: Use MediaQuery.sizeOf() and add hysteresis
class ResponsiveScaffold extends StatelessWidget {
  static const _mobileBreakpoint = 600.0;
  static const _hysteresis = 50.0;  // Prevent thrashing

  @override
  Widget build(BuildContext context) {
    // Only rebuild on size changes, not all MediaQuery changes
    final size = MediaQuery.sizeOf(context);
    final isWideLayout = size.width > _mobileBreakpoint + _hysteresis;

    return Scaffold(
      drawer: isWideLayout ? null : _buildDrawer(),
      body: Row(
        children: [
          if (isWideLayout) _buildNavigationRail(),
          Expanded(child: _buildContent()),
        ],
      ),
    );
  }
}

// Alternative: Use LayoutBuilder for local constraints
class ResponsiveScaffold extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Only rebuilds this widget, not entire tree
        final isWideLayout = constraints.maxWidth > 600;
        return Scaffold(/*...*/);
      },
    );
  }
}

// ❌ WRONG: MediaQuery.of() with no hysteresis
class ResponsiveScaffold extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);  // Rebuilds on ALL changes
    final isWideLayout = mediaQuery.size.width > 600;  // Exact threshold - thrashes

    // Entire tree rebuilds on every MediaQuery change
    return Scaffold(/*...*/);
  }
}
```

**Warning signs:**
- Dropped frames during window resize (DevTools Performance overlay)
- Layout switches back and forth rapidly at specific window sizes
- High CPU usage during resize operations
- Janky animations when transitioning between layouts
- Build method called excessively (check with `debugPrint` in build)

**Phase to address:**
Beta v1.5 responsive navigation implementation — use `MediaQuery.sizeOf()` instead of `MediaQuery.of()`, add hysteresis to breakpoint checks, use `const` widgets where possible, test resize performance on web platform.

---

### Pitfall 6: Drawer State Lost on Navigation

**What goes wrong:**
User expands a section in NavigationDrawer (e.g., project list with expandable items), navigates to a screen, returns, and expansion state is lost. Drawer contents reset to collapsed state on every navigation. TreeView, ExpansionTile, or custom expand/collapse UI doesn't persist.

**Why it happens:**
Scaffold's drawer is disposed and recreated on navigation. Each route creates a new Scaffold instance with new drawer widget. Drawer state lives in widget tree, not in a state management solution. GoRouter's default behavior doesn't preserve drawer widget instances between routes.

**How to avoid:**
```dart
// ✅ CORRECT: Use StatefulShellRoute to preserve drawer state
final router = GoRouter(
  routes: [
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return ScaffoldWithNavigation(
          navigationShell: navigationShell,
        );
      },
      branches: [
        StatefulShellBranch(
          routes: [GoRoute(path: '/home', builder: /*...*/)],
        ),
        StatefulShellBranch(
          routes: [GoRoute(path: '/projects', builder: /*...*/)],
        ),
      ],
    ),
  ],
);

// Scaffold is created ONCE, navigation changes content only
class ScaffoldWithNavigation extends StatefulWidget {
  final StatefulNavigationShell navigationShell;

  const ScaffoldWithNavigation({required this.navigationShell});

  @override
  State<ScaffoldWithNavigation> createState() => _ScaffoldWithNavigationState();
}

class _ScaffoldWithNavigationState extends State<ScaffoldWithNavigation> {
  // Drawer state persists because widget is not disposed on navigation
  final _expandedProjects = <String>{};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: NavigationDrawer(
        children: _buildDrawerItems(),  // Uses _expandedProjects
      ),
      body: widget.navigationShell,  // Navigation changes here only
    );
  }
}

// ❌ WRONG: Each route creates new Scaffold
GoRouter(
  routes: [
    GoRoute(
      path: '/home',
      builder: (context, state) => Scaffold(
        drawer: NavigationDrawer(/*...*/),  // New instance
        body: HomeScreen(),
      ),
    ),
    GoRoute(
      path: '/projects',
      builder: (context, state) => Scaffold(
        drawer: NavigationDrawer(/*...*/),  // Different instance - state lost
        body: ProjectsScreen(),
      ),
    ),
  ],
);
```

**Warning signs:**
- Drawer expansion state resets on navigation
- Users complain about having to re-expand menus constantly
- Drawer animations replay when returning to screens
- Selected item highlighting resets incorrectly

**Phase to address:**
Beta v1.5 persistent navigation implementation — use `StatefulShellRoute` to wrap all main navigation routes, ensure single Scaffold instance persists across navigation, test drawer state preservation.

---

### Pitfall 7: Deletion Confirmation Race Conditions with Undo

**What goes wrong:**
User deletes project, sees snackbar with "UNDO" button, but if they tap "UNDO" while snackbar is animating out, the action is ignored. Or worse: deletion completes in database, but undo UI suggests it can still be undone. Multiple rapid deletions queue snackbars, user taps UNDO on wrong deletion.

**Why it happens:**
SnackBar with action buttons has known Flutter bug where auto-dismiss doesn't work reliably when action is set. Deletion happens immediately while snackbar displays, creating race condition between database transaction and user tapping UNDO. SnackBar queue allows multiple deletions before first one is undoable.

**How to avoid:**
```dart
// ✅ CORRECT: Defer deletion until snackbar dismissed
Future<void> deleteProjectWithUndo(String projectId) async {
  // Store deletion intent, don't execute yet
  final deletionIntent = DeletionIntent(projectId: projectId);

  final controller = ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text('Project deleted'),
      action: SnackBarAction(
        label: 'UNDO',
        onPressed: () {
          deletionIntent.cancel();  // Mark as cancelled
        },
      ),
      duration: Duration(seconds: 5),
    ),
  );

  // Wait for snackbar to close before executing deletion
  final reason = await controller.closed;

  if (!mounted) return;

  if (reason != SnackBarClosedReason.action && !deletionIntent.cancelled) {
    // User didn't tap UNDO and snackbar finished - now delete
    await apiService.deleteProject(projectId);
    if (!mounted) return;

    setState(() {
      // Remove from UI
    });
  }
}

// Alternative: Soft delete pattern
class Project {
  final String id;
  final DateTime? deletedAt;  // null = active, non-null = deleted
}

Future<void> softDeleteProject(String projectId) async {
  // Mark as deleted immediately
  await apiService.softDeleteProject(projectId);

  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text('Project deleted'),
      action: SnackBarAction(
        label: 'UNDO',
        onPressed: () async {
          await apiService.restoreProject(projectId);
          if (mounted) setState(() {});
        },
      ),
    ),
  );
}

// ❌ WRONG: Delete immediately, then show undo
Future<void> deleteProject(String projectId) async {
  await apiService.deleteProject(projectId);  // Already deleted!

  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text('Project deleted'),
      action: SnackBarAction(
        label: 'UNDO',
        onPressed: () {
          // Can't undo - data already gone from database
          apiService.restoreProject(projectId);  // Will fail
        },
      ),
    ),
  );
}
```

**Warning signs:**
- UNDO button sometimes doesn't work
- Multiple snackbars stack on rapid deletions
- Data already gone when user taps UNDO
- Snackbar doesn't auto-dismiss with action button (Flutter bug #126756)
- Race condition exceptions in database layer

**Phase to address:**
Beta v1.5 deletion implementation — implement soft delete pattern for all entity types, defer hard deletes until after snackbar dismissed, limit snackbar queue to prevent confusion, add integration tests for undo timing.

---

### Pitfall 8: Empty State Detection with Race Conditions

**What goes wrong:**
User deletes last project, but empty state doesn't appear. Or empty state flickers during loading, then shows list. Or both empty state AND list appear simultaneously. Especially bad when deletion + refetch race each other.

**Why it happens:**
State updates happen asynchronously: deletion request sent → UI optimistically updates → server confirms → list refetches → race condition if refetch completes before state settles. `ListView.builder` with `itemCount: 0` shows nothing, developer assumes conditional check elsewhere will handle empty state, but both widgets render.

**How to avoid:**
```dart
// ✅ CORRECT: Single source of truth with explicit states
class ProjectListState extends ChangeNotifier {
  LoadingState _loadingState = LoadingState.loading;
  List<Project> _projects = [];

  bool get isEmpty => _loadingState == LoadingState.loaded && _projects.isEmpty;
  bool get isLoading => _loadingState == LoadingState.loading;
  bool get hasData => _loadingState == LoadingState.loaded && _projects.isNotEmpty;

  Future<void> deleteProject(String id) async {
    // Optimistic update
    final index = _projects.indexWhere((p) => p.id == id);
    if (index != -1) {
      final removed = _projects.removeAt(index);
      notifyListeners();  // Update UI immediately

      try {
        await apiService.deleteProject(id);
      } catch (e) {
        // Rollback on error
        _projects.insert(index, removed);
        notifyListeners();
        rethrow;
      }
    }
  }
}

// Widget uses explicit state checks
class ProjectListView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<ProjectListState>(
      builder: (context, state, child) {
        if (state.isLoading) {
          return LoadingIndicator();
        }

        if (state.isEmpty) {
          return EmptyStateWidget(
            title: 'No projects yet',
            message: 'Create your first project to get started',
            action: ElevatedButton(
              onPressed: () => context.go('/new-project'),
              child: Text('Create Project'),
            ),
          );
        }

        return ListView.builder(
          itemCount: state.projects.length,
          itemBuilder: (context, index) => ProjectCard(state.projects[index]),
        );
      },
    );
  }
}

// ❌ WRONG: Multiple conditions, race conditions
class ProjectListView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<ProjectListState>(
      builder: (context, state, child) {
        return Column(
          children: [
            if (state.projects.isEmpty)  // Could be true during loading
              EmptyStateWidget(),

            if (state.isLoading)  // Could be true while projects exist
              LoadingIndicator(),

            ListView.builder(  // Always builds, even when empty
              itemCount: state.projects.length,
              itemBuilder: (context, index) => ProjectCard(state.projects[index]),
            ),
          ],
        );
      },
    );
  }
}
```

**Warning signs:**
- Empty state and list both visible
- Empty state flickers during transitions
- Loading indicator persists after data loads
- Deleting last item doesn't show empty state
- RefreshIndicator + empty state both visible

**Phase to address:**
Beta v1.5 empty states implementation — create explicit loading/empty/hasData states in all list view models, use mutually exclusive conditionals in widgets, add integration tests verifying state transitions.

---

### Pitfall 9: Deep Link State Sync with Breadcrumbs

**What goes wrong:**
User opens deep link to `/projects/abc/threads/xyz`, breadcrumb shows "Home > ???" because navigation stack wasn't built. Or breadcrumb shows correct path, but clicking "Projects" navigates to wrong state. Back button behavior inconsistent between deep link entry and normal navigation.

**Why it happens:**
GoRouter handles deep links by jumping directly to route, skipping intermediate routes. Breadcrumb components assume navigation stack was built linearly. StatefulShellRoute preserves state per branch, but deep link may land in different branch than breadcrumb expects. iOS deep link routing hits "/" before expected path on cold start.

**How to avoid:**
```dart
// ✅ CORRECT: Build breadcrumbs from route path, not navigation stack
class BreadcrumbBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    final segments = _buildBreadcrumbSegments(location);

    return Row(
      children: [
        for (var i = 0; i < segments.length; i++) ...[
          TextButton(
            onPressed: () => context.go(segments[i].path),
            child: Text(segments[i].label),
          ),
          if (i < segments.length - 1) Icon(Icons.chevron_right),
        ],
      ],
    );
  }

  List<BreadcrumbSegment> _buildBreadcrumbSegments(String location) {
    // Parse route path to build breadcrumbs
    final parts = location.split('/').where((s) => s.isNotEmpty).toList();
    final segments = <BreadcrumbSegment>[
      BreadcrumbSegment(label: 'Home', path: '/'),
    ];

    var currentPath = '';
    for (var i = 0; i < parts.length; i++) {
      currentPath += '/${parts[i]}';

      // Map path segments to labels
      if (parts[i] == 'projects') {
        if (i + 1 < parts.length) {
          // Fetch project name for /projects/:id
          final projectId = parts[i + 1];
          segments.add(BreadcrumbSegment(
            label: _getProjectName(projectId),
            path: '/projects/$projectId',
          ));
          i++;  // Skip the ID segment
        } else {
          segments.add(BreadcrumbSegment(label: 'Projects', path: currentPath));
        }
      }
    }

    return segments;
  }
}

// Handle iOS deep link "/" redirect
GoRouter(
  redirect: (context, state) {
    // iOS redirects to "/" before deep link - detect and allow
    if (state.matchedLocation == '/' && state.uri.toString() != '/') {
      return null;  // Allow deep link to proceed
    }
    return null;
  },
  routes: [/*...*/],
);

// ❌ WRONG: Build breadcrumbs from Navigator stack
class BreadcrumbBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final navigator = Navigator.of(context);
    // Navigator stack doesn't exist for deep links - breadcrumb breaks
    return Row(/*...*/);
  }
}
```

**Warning signs:**
- Breadcrumbs missing items when deep linking
- Back button doesn't go to expected previous screen
- Breadcrumb labels show IDs instead of names
- iOS deep link navigation flashes "/" screen
- Clicking breadcrumb item navigates to wrong state

**Phase to address:**
Beta v1.5 breadcrumb navigation implementation — parse breadcrumbs from route location not navigation stack, handle deep link initialization properly, test all deep link scenarios on iOS (cold start, background, already running).

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `setState` instead of state management (Riverpod/Bloc) | Faster initial development, no learning curve | State logic scattered across widgets, hard to test, rebuilds expensive, state loss on navigation | Only for truly local widget state (e.g., TextField focus, animation controllers) |
| Deleting without confirmation dialog | Simpler code, fewer widgets | Accidental deletions, user complaints, no undo path, lost data | Never - confirmation is table stakes UX |
| Hard-coding breakpoint values (e.g., 600px) across multiple widgets | Simple to implement | Inconsistent responsive behavior, hard to adjust, doesn't follow Material guidelines | Never - define constants or use Material window size classes |
| `MediaQuery.of(context)` instead of `MediaQuery.sizeOf(context)` | Habit, existing code examples | Unnecessary rebuilds on brightness/padding/orientation changes, performance issues | Never in modern Flutter (3.7+) - always use `sizeOf()` |
| Showing snackbar immediately after operation without checking `mounted` | Operation feels responsive | Crashes when user navigates away during operation | Never - always check `mounted` |
| Using `Navigator.pop(context)` in StatelessWidget without async gap check | Simple navigation code | Lint warnings, potential crashes | Only when no async gaps exist before pop() |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SQLite (sqflite) | Assuming `ON DELETE CASCADE` works without configuration | Execute `PRAGMA foreign_keys = ON` in `onCreate` and `onOpen` callbacks; verify with tests |
| SharedPreferences | Assuming writes persist immediately | Load theme before `runApp()`, await writes, verify successful write, consider SharedPreferencesAsync for critical data |
| GoRouter deep linking | Assuming navigation stack exists for deep links | Build breadcrumbs from route path, handle iOS "/" redirect, test cold start deep links |
| Material NavigationDrawer | Assuming drawer state persists across routes | Use `StatefulShellRoute` to preserve single Scaffold instance across navigation |
| SnackBar with actions | Assuming auto-dismiss works when action is set | Known Flutter bug (#126756) - manage dismissal manually or use soft delete pattern |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `MediaQuery.of(context)` instead of `MediaQuery.sizeOf(context)` | Dropped frames during resize, high rebuild count | Use `MediaQuery.sizeOf()` or `LayoutBuilder`, add `const` widgets, add hysteresis to breakpoints | Immediately noticeable on web during window resize |
| Rebuilding entire Scaffold on navigation | Drawer animations replay, state resets, janky transitions | Use `StatefulShellRoute`, preserve Scaffold instance, change body content only | >5 routes with complex drawer UI |
| No debouncing on responsive breakpoint transitions | Layout thrashes between states, high CPU during resize | Add hysteresis (e.g., 50px buffer), use `const` where possible | When user resizes window near breakpoint |
| Loading theme after MaterialApp builds | White flash on startup, poor UX in dark mode | Load theme in `main()` before `runApp()`, use `WidgetsFlutterBinding.ensureInitialized()` | Every app launch (immediately visible to users) |
| Expensive builds in ListView.builder without keys | Scroll stuttering, high rebuild cost | Use `const` widgets, provide keys, extract item builder to separate widget | >100 items or complex item widgets |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No confirmation before deletion | Accidental data loss, user frustration, support burden | Always show confirmation dialog, clearly state what will be deleted, explain cascade effects |
| Generic empty states ("No data") | User doesn't know what action to take | Context-specific empty states with clear CTAs: "No projects yet. Create your first project to get started." |
| Theme switch without persistence | User re-enables dark mode every session, frustration | Persist theme choice, load before UI builds, verify persistence works cross-platform |
| Undo snackbar disappears before user reads it | User misses undo opportunity, accidental deletions permanent | 5-7 second duration, defer deletion until snackbar dismissed, clear "UNDO" button |
| Drawer state resets on navigation | User re-expands menus constantly, tedious interaction | Preserve drawer state across navigation with `StatefulShellRoute` |
| Breadcrumbs show IDs instead of names | User can't understand location, navigation context lost | Fetch entity names for breadcrumbs, show "Loading..." during fetch, cache names |
| Responsive layout switches mid-interaction | User taps drawer, it switches to NavigationRail, target moves | Add hysteresis to prevent thrashing, avoid layout changes during active interactions |
| No loading states during deletion | User doesn't know if action worked, taps multiple times | Show loading indicator, disable delete button during operation, show success feedback |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Deletion feature:** Often missing cascade delete logic — verify orphaned data doesn't accumulate after deletes (run `SELECT * FROM threads WHERE project_id NOT IN (SELECT id FROM projects)`)
- [ ] **Theme switching:** Often missing persistence — verify theme survives app restart on all three platforms (web, Android, iOS)
- [ ] **Theme switching:** Often missing FOUC prevention — verify no white flash on app launch in dark mode
- [ ] **Deletion confirmation:** Often missing `context.mounted` checks — verify no crashes when user navigates away during deletion
- [ ] **SQLite cascade deletes:** Often missing `PRAGMA foreign_keys = ON` — verify foreign key constraint errors are thrown when expected
- [ ] **Responsive navigation:** Often missing hysteresis — verify layout doesn't thrash when resizing window near breakpoint
- [ ] **Undo deletion:** Often missing race condition handling — verify undo works even when tapped during snackbar animation
- [ ] **Empty states:** Often missing during loading — verify empty state doesn't appear while data is loading
- [ ] **Breadcrumbs:** Often missing deep link handling — verify breadcrumbs work when app is opened via deep link (cold start)
- [ ] **Navigation drawer:** Often missing state persistence — verify expansion state survives navigation to other screens

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Orphaned data from missing CASCADE | MEDIUM | Write migration script to clean orphans: `DELETE FROM threads WHERE project_id NOT IN (SELECT id FROM projects)`, add `PRAGMA foreign_keys = ON`, verify constraint works |
| Theme persistence failure | LOW | Add retry logic to SharedPreferences writes, fall back to system theme if load fails, add user-facing "Reset Settings" button |
| BuildContext after dispose crashes | LOW | Add `if (!mounted) return;` checks before all context operations after async gaps, enable `use_build_context_synchronously` lint |
| MediaQuery rebuild thrashing | LOW | Replace `MediaQuery.of()` with `MediaQuery.sizeOf()`, add const widgets, wrap responsive logic in `LayoutBuilder` |
| Drawer state loss on navigation | MEDIUM | Refactor routes to use `StatefulShellRoute`, wrap in single Scaffold, test state preservation |
| Deep link breadcrumb failure | MEDIUM | Refactor breadcrumbs to parse from route location, add entity name fetching, handle iOS "/" redirect |
| Undo race conditions | MEDIUM | Implement soft delete pattern, defer hard deletes until snackbar dismissed, add cancellation tokens |
| Empty state race conditions | LOW | Add explicit loading/empty/hasData states, use mutually exclusive conditionals, add state transition tests |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| BuildContext across async gaps | Beta v1.5 - All deletion features | Enable `use_build_context_synchronously` lint, code review all async operations, integration tests with navigation during operations |
| SQLite foreign keys disabled | Beta v1.5 - Deletion implementation | Add `PRAGMA foreign_keys = ON` in DB init, write test verifying cascade works, check for orphaned data in integration tests |
| SharedPreferences persistence | Beta v1.5 - Settings/Theme | Load theme in `main()` before `runApp()`, test persistence on all platforms, verify no FOUC in manual testing |
| Theme flash on startup | Beta v1.5 - Settings/Theme | Move theme load before MaterialApp, test on iOS/Android/web, manual verification in dark mode |
| MediaQuery rebuild thrashing | Beta v1.5 - Responsive navigation | Use `MediaQuery.sizeOf()`, add hysteresis, performance test window resize on web |
| Drawer state loss | Beta v1.5 - Persistent navigation | Implement `StatefulShellRoute`, test navigation preserves drawer state, verify expansion state persists |
| Deletion undo race conditions | Beta v1.5 - Deletion features | Implement soft delete, test undo during snackbar animation, verify undo works reliably |
| Empty state race conditions | Beta v1.5 - Empty states | Explicit state enums, mutually exclusive rendering, integration tests for loading→empty→data transitions |
| Deep link breadcrumb sync | Beta v1.5 - Breadcrumb navigation | Parse breadcrumbs from route, test cold start deep links on iOS, verify breadcrumb accuracy |

## Testing Strategy

**Unit Tests:**
- Theme persistence: verify save/load cycle works
- State management: verify deletion removes items from lists
- Breadcrumb parsing: verify correct segments from route paths

**Widget Tests:**
- Empty state rendering: verify mutually exclusive states (loading XOR empty XOR data)
- Responsive breakpoints: verify layout switches at correct widths
- Confirmation dialogs: verify shown before deletions

**Integration Tests:**
- Cascade deletes: verify deleting project removes threads/documents/messages
- Theme persistence: verify survives app restart on all platforms
- Undo timing: verify undo works when tapped at various times during snackbar display
- Deep linking: verify breadcrumbs correct on cold start deep links
- Navigation state: verify drawer expansion state survives navigation

**Manual Testing Checklist:**
- [ ] Theme: Enable dark mode, restart app, verify no white flash, verify stays dark
- [ ] Deletion: Delete project, verify confirmation shown, verify cascade to threads/docs, verify undo works
- [ ] Responsive: Resize browser window through breakpoint, verify no thrashing, verify smooth transition
- [ ] Deep link: Open `/projects/abc/threads/xyz` in new tab (cold start), verify breadcrumbs correct
- [ ] Drawer: Expand project list, navigate to thread, return, verify still expanded

## Sources

**Flutter Official Documentation:**
- [Adaptive design best practices](https://docs.flutter.dev/ui/adaptive-responsive/best-practices) - MediaQuery vs LayoutBuilder, breakpoint guidance
- [Deep linking](https://docs.flutter.dev/ui/navigation/deep-linking) - Deep link handling, platform differences
- [use_build_context_synchronously lint rule](https://dart.dev/tools/linter-rules/use_build_context_synchronously) - Async gap context safety

**State Management:**
- [Flutter State Management in 2026: Choosing the Right Approach](https://medium.com/@Sofia52/flutter-state-management-in-2026-choosing-the-right-approach-811b866d9b1b)
- [Best Flutter State Management Libraries 2026](https://foresightmobile.com/blog/best-flutter-state-management)

**Navigation & Routing:**
- [Flutter Drawer with State Management](https://dev.to/aaronksaunders/flutter-drawer-with-state-management-3g19)
- [GitHub Issue #146476: Keep state alive when opening/closing Scaffold's drawer](https://github.com/flutter/flutter/issues/146476)
- [GoRouter StatefulShellRoute for nested navigation](https://medium.com/@mohitarora7272/stateful-nested-navigation-in-flutter-using-gorouters-statefulshellroute-and-statefulshellbranch-8bb91443edad)

**Theme & Persistence:**
- [Flutter SharedPreferences not persistent issue #67925](https://github.com/flutter/flutter/issues/67925)
- [SharedPreferences data not persisting after page reload issue #156419](https://github.com/flutter/flutter/issues/156419)
- [Complete Flutter Guide: Dark Mode & Theme Switching](https://medium.com/@amazing_gs/complete-flutter-guide-how-to-implement-dark-mode-dynamic-theming-and-theme-switching-ddabaef48d5a)

**Async Context Issues:**
- [Do Not Use BuildContext in Async Gaps](https://medium.com/nerd-for-tech/do-not-use-buildcontext-in-async-gaps-why-and-how-to-handle-flutter-context-correctly-870b924eb42e)
- [How to Use BuildContext with Async Safely](https://csdcorp.com/blog/coding/how-to-use-buildcontext-with-async-safely/)
- [setState() called after dispose() - Causes and How to Fix](https://www.omi.me/blogs/flutter-errors/setstate-called-after-dispose-in-flutter-causes-and-how-to-fix)

**Deletion & Dialogs:**
- [Understanding Race Conditions in Flutter and Dart](https://medium.com/@dev.h.majid/understanding-race-conditions-in-flutter-and-dart-and-how-to-solve-them-d94976f6bd0a)
- [GitHub Issue #126756: SnackBar cannot auto dismiss when has action](https://github.com/flutter/flutter/issues/126756)
- [How to Make a Confirm Dialog in Flutter](https://www.kindacode.com/article/how-to-make-a-confirm-dialog-in-flutter)

**Database:**
- [SQLite Foreign Keys with Cascade Delete](https://www.techonthenet.com/sqlite/foreign_keys/foreign_delete.php)
- [GitHub Issue #319: sqflite cascade delete](https://github.com/tekartik/sqflite/issues/319)
- [SQLite Foreign Key Support official docs](https://sqlite.org/foreignkeys.html)

**Responsive Design:**
- [Building Beautiful Responsive UI in Flutter: Complete Guide for 2026](https://medium.com/@saadalidev/building-beautiful-responsive-ui-in-flutter-a-complete-guide-for-2026-ea43f6c49b85)
- [Mastering MediaQuery for Responsive Design](https://vibe-studio.ai/insights/mastering-mediaquery-for-responsive-design-in-flutter)
- [Responsive layouts: Split View and Drawer Navigation](https://codewithandrea.com/articles/flutter-responsive-layouts-split-view-drawer-navigation/)

**Deep Linking Issues:**
- [GitHub Issue #142988: Deep links route to "/" before expected path on iOS](https://github.com/flutter/flutter/issues/142988)
- [GitHub Issue #134373: Deep Linking conflicts with StatefulShellRoute](https://github.com/flutter/flutter/issues/134373)

---
*Pitfalls research for: Business Analyst Assistant Beta v1.5 - UI/UX Excellence*
*Researched: 2026-01-29*
*Confidence: HIGH - Based on official Flutter documentation, current 2025-2026 community resources, and documented GitHub issues*
