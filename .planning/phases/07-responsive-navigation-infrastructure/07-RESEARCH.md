# Phase 7: Responsive Navigation Infrastructure - Research

**Researched:** 2026-01-29
**Domain:** Flutter responsive navigation with GoRouter
**Confidence:** HIGH

## Summary

This research investigates how to implement persistent sidebar navigation with responsive behavior across mobile and desktop breakpoints, including breadcrumb navigation, contextual back arrows, and sidebar state persistence.

The current codebase uses GoRouter with simple routes (no ShellRoute), and each screen implements its own navigation structure independently. The Home screen has both mobile (drawer) and desktop (sidebar) layouts using `ResponsiveLayout`, but these are duplicated patterns not shared across screens. Other screens (Projects, Settings) have no persistent navigation.

**Key findings:**
1. **StatefulShellRoute.indexedStack** is the standard GoRouter pattern for persistent navigation shells with state preservation per branch
2. **LayoutBuilder-based responsive switching** between NavigationRail (desktop) and Drawer (mobile) at breakpoint thresholds
3. **Breadcrumbs require custom implementation** - GoRouter does not provide built-in breadcrumb support, but `GoRouterState.of(context).uri.path` enables location tracking
4. **SharedPreferences immediate-persist pattern** (established in Phase 6) directly applies to sidebar state

**Primary recommendation:** Use StatefulShellRoute with a responsive shell builder that switches between NavigationRail (>=900px) and hamburger drawer (<600px), with custom breadcrumb widget tracking route segments.

## Current Architecture Analysis

### Existing Navigation Structure

**main.dart (lines 118-197):**
- GoRouter with flat route structure (no ShellRoute)
- Routes: `/splash`, `/login`, `/auth/callback`, `/home`, `/projects`, `/projects/:id`, `/settings`
- Auth redirect logic handles splash/login/callback transitions
- Router cached in StatefulWidget to prevent recreation bug

**home_screen.dart:**
- ResponsiveLayout switches mobile/desktop
- Mobile: Scaffold with AppBar + Drawer
- Desktop: Row with NavigationRail + content
- Sidebar is private to home screen - not shared
- Hardcoded selectedIndex: 0

**project_list_screen.dart, settings_screen.dart:**
- Simple Scaffold with AppBar
- No sidebar navigation
- No breadcrumbs

**responsive_layout.dart:**
- Breakpoints: mobile < 600, tablet >= 600 < 900, desktop >= 900
- Uses LayoutBuilder for responsive switching
- Defined in `core/config.dart`: `Breakpoints.mobile = 600`, `Breakpoints.tablet = 900`

### Current Breakpoint Values

From `config.dart`:
```dart
class Breakpoints {
  static const double mobile = 600;
  static const double tablet = 900;
  static const double desktop = 1200;
}
```

**NAV-01 requirements map to:**
- Desktop always-visible >= 900px
- Mobile hamburger < 600px
- Tablet (600-899px) is Claude's discretion

### Problems to Solve

1. **No persistent navigation:** Sidebar only exists on home screen
2. **State loss on navigation:** Navigating to /projects loses sidebar context
3. **No breadcrumbs:** Current location not shown
4. **No back arrow context:** Default AppBar back button shows generic arrow
5. **No sidebar state persistence:** collapsed/expanded not remembered

## Responsive Navigation Patterns

### Pattern 1: StatefulShellRoute with Responsive Builder

The recommended approach uses StatefulShellRoute.indexedStack wrapping all authenticated routes with a responsive shell that switches between NavigationRail and Drawer based on screen width.

**Source:** [Code with Andrea - Flutter Bottom Navigation Bar with StatefulShellRoute](https://codewithandrea.com/articles/flutter-bottom-navigation-bar-nested-routes-gorouter/)

**Architecture:**
```
GoRouter
├── /splash (outside shell)
├── /login (outside shell)
├── /auth/callback (outside shell)
└── StatefulShellRoute (authenticated routes)
    ├── builder: ResponsiveScaffold (switches NavigationRail/Drawer)
    ├── Branch: Home (/home)
    ├── Branch: Projects (/projects, /projects/:id)
    ├── Branch: Conversations (/conversations) [future]
    └── Branch: Settings (/settings)
```

**Key benefits:**
- Each branch maintains its own navigation stack
- Sidebar persists across all screen transitions
- State preserved when switching between sections
- Deep linking works correctly

### Pattern 2: LayoutBuilder for Responsive Switching

**Source:** [Code with Andrea - Responsive Layouts Split View](https://codewithandrea.com/articles/flutter-responsive-layouts-split-view-drawer-navigation/)

Use LayoutBuilder to detect available width and render appropriate navigation:

```dart
LayoutBuilder(builder: (context, constraints) {
  if (constraints.maxWidth >= 900) {
    return ScaffoldWithNavigationRail(...);
  } else if (constraints.maxWidth >= 600) {
    return ScaffoldWithCollapsedRail(...); // Tablet: collapsed rail or drawer
  } else {
    return ScaffoldWithDrawer(...);
  }
});
```

**Breakpoint recommendations (from NAV-01):**
- >= 900px: NavigationRail always visible (extended or collapsed)
- 600-899px: Claude's discretion - recommend collapsed NavigationRail
- < 600px: Hamburger menu opening Drawer

### Pattern 3: NavigationRail Extended/Collapsed Toggle

**Source:** [Flutter API - NavigationRail](https://api.flutter.dev/flutter/material/NavigationRail-class.html)

NavigationRail has built-in animation for extended/collapsed states:
- `extended`: Boolean controlling state
- `minExtendedWidth`: Width when extended (default 256)
- Built-in animation transitions between states
- `labelType: NavigationRailLabelType.none` required when extended

**Usage pattern:**
```dart
NavigationRail(
  extended: isExpanded,  // Controlled by provider
  minExtendedWidth: 250,
  selectedIndex: currentIndex,
  onDestinationSelected: (index) => goBranch(index),
  destinations: [...]
)
```

## GoRouter StatefulShellRoute

### API Overview (go_router v17.0.1)

**Source:** [pub.dev/packages/go_router](https://pub.dev/packages/go_router)

StatefulShellRoute.indexedStack creates:
- Separate Navigator per branch
- IndexedStack-like behavior preserving all branch states
- `navigationShell.currentIndex` for active branch detection
- `navigationShell.goBranch(index)` for programmatic navigation

### Configuration Pattern

```dart
final GoRouter _router = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/home',
  routes: [
    // Auth routes outside shell
    GoRoute(path: '/splash', ...),
    GoRoute(path: '/login', ...),
    GoRoute(path: '/auth/callback', ...),

    // Authenticated routes inside shell
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return ResponsiveScaffold(
          navigationShell: navigationShell,
          currentIndex: navigationShell.currentIndex,
        );
      },
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/home',
              builder: (context, state) => HomeScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/projects',
              builder: (context, state) => ProjectListScreen(),
              routes: [
                GoRoute(
                  path: ':id',
                  builder: (context, state) => ProjectDetailScreen(
                    projectId: state.pathParameters['id']!,
                  ),
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/settings',
              builder: (context, state) => SettingsScreen(),
            ),
          ],
        ),
      ],
    ),
  ],
);
```

### Current Location Detection

**Source:** [GitHub Issue #161090](https://github.com/flutter/flutter/issues/161090)

```dart
// Get current path
final location = GoRouterState.of(context).uri.path;

// Check if route is active (including nested routes)
bool isRouteActive(String route) {
  return location.startsWith(route);
}
```

This enables sidebar highlighting:
```dart
destinations: [
  NavigationRailDestination(
    icon: Icon(Icons.home_outlined),
    selectedIcon: Icon(Icons.home),
    label: Text('Home'),
  ),
  // ...
],
selectedIndex: _getSelectedIndex(GoRouterState.of(context).uri.path),
```

## Breadcrumb Implementation

### GoRouter Limitation

GoRouter does not provide built-in breadcrumb support. [GitHub Issue #99118](https://github.com/flutter/flutter/issues/99118) requests access to the route stack for breadcrumbs but remains open.

### Recommended Approach: Route-Based Breadcrumbs

Since the app has a predictable route hierarchy, breadcrumbs can be derived from the current URI path:

**Route hierarchy:**
```
/home                           -> Home
/projects                       -> Projects
/projects/:id                   -> Projects > {Project Name}
/projects/:id/threads/:tid      -> Projects > {Project Name} > {Thread Name}
```

**Implementation pattern:**

1. **Create BreadcrumbProvider** that parses `GoRouterState.of(context).uri.path`
2. **Resolve names asynchronously** using ProjectProvider/ThreadProvider
3. **Render as clickable segments** with `context.go()` navigation

```dart
class Breadcrumb {
  final String label;
  final String? route; // null = current (not clickable)

  Breadcrumb(this.label, [this.route]);
}

List<Breadcrumb> buildBreadcrumbs(String path, {Project? project, Thread? thread}) {
  final segments = path.split('/').where((s) => s.isNotEmpty).toList();
  final breadcrumbs = <Breadcrumb>[];

  if (segments.contains('projects')) {
    breadcrumbs.add(Breadcrumb('Projects', '/projects'));

    // If on project detail
    final projectIndex = segments.indexOf('projects');
    if (projectIndex + 1 < segments.length) {
      final projectId = segments[projectIndex + 1];
      breadcrumbs.add(Breadcrumb(
        project?.name ?? 'Project',
        '/projects/$projectId',
      ));
    }
  }

  // Mark last breadcrumb as current (no route)
  if (breadcrumbs.isNotEmpty) {
    breadcrumbs.last = Breadcrumb(breadcrumbs.last.label, null);
  }

  return breadcrumbs;
}
```

### Breadcrumb Widget

```dart
class BreadcrumbBar extends StatelessWidget {
  final List<Breadcrumb> breadcrumbs;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: breadcrumbs.expand((crumb) => [
        if (crumb != breadcrumbs.first)
          Text(' > ', style: TextStyle(color: Colors.grey)),
        crumb.route != null
          ? TextButton(
              onPressed: () => context.go(crumb.route!),
              child: Text(crumb.label),
            )
          : Text(crumb.label, style: TextStyle(fontWeight: FontWeight.bold)),
      ]).toList(),
    );
  }
}
```

## Sidebar State Persistence

### Established Pattern (Phase 6)

ThemeProvider demonstrates the immediate-persist pattern:
1. Change state
2. Persist to SharedPreferences immediately (before notifyListeners)
3. Notify listeners

**Source:** `frontend/lib/providers/theme_provider.dart`

### NavigationProvider Design

```dart
class NavigationProvider extends ChangeNotifier {
  final SharedPreferences _prefs;
  bool _isSidebarExpanded;
  Map<String, bool> _sectionStates; // e.g., {"projects": true, "settings": false}

  static const String _sidebarExpandedKey = 'sidebarExpanded';
  static const String _sectionStatesKey = 'sectionStates';

  NavigationProvider(this._prefs, {
    bool? initialExpanded,
    Map<String, bool>? initialSections,
  }) : _isSidebarExpanded = initialExpanded ?? true,
       _sectionStates = initialSections ?? {};

  static Future<NavigationProvider> load(SharedPreferences prefs) async {
    final expanded = prefs.getBool(_sidebarExpandedKey) ?? true;
    final sectionsJson = prefs.getString(_sectionStatesKey);
    final sections = sectionsJson != null
        ? Map<String, bool>.from(jsonDecode(sectionsJson))
        : <String, bool>{};
    return NavigationProvider(prefs,
        initialExpanded: expanded, initialSections: sections);
  }

  bool get isSidebarExpanded => _isSidebarExpanded;

  Future<void> toggleSidebar() async {
    _isSidebarExpanded = !_isSidebarExpanded;
    await _prefs.setBool(_sidebarExpandedKey, _isSidebarExpanded);
    notifyListeners();
  }

  bool isSectionExpanded(String section) => _sectionStates[section] ?? false;

  Future<void> toggleSection(String section) async {
    _sectionStates[section] = !(_sectionStates[section] ?? false);
    await _prefs.setString(_sectionStatesKey, jsonEncode(_sectionStates));
    notifyListeners();
  }
}
```

### What NOT to Persist (Per CONTEXT.md)

- Last navigation location (always start at home)
- Scroll positions in lists

## Current Location Highlighting

### Implementation with StatefulShellRoute

StatefulNavigationShell provides `currentIndex` for branch-level highlighting:

```dart
// In shell builder
NavigationRail(
  selectedIndex: navigationShell.currentIndex,
  onDestinationSelected: (index) {
    navigationShell.goBranch(
      index,
      initialLocation: index == navigationShell.currentIndex,
    );
  },
  // ...
)
```

### Nested Route Highlighting

For highlighting within a branch (e.g., highlighting "Projects" when on /projects/:id):

```dart
int _getSelectedIndex(String path) {
  if (path.startsWith('/home')) return 0;
  if (path.startsWith('/projects')) return 1;
  if (path.startsWith('/conversations')) return 2;
  if (path.startsWith('/settings')) return 3;
  return 0;
}
```

## Back Arrow Context (NAV-03)

### Standard Approach

AppBar automatically shows back button when there's navigation history. For contextual text (e.g., "Back to Projects"):

**Option 1: Custom leading widget**
```dart
AppBar(
  leading: TextButton.icon(
    icon: Icon(Icons.arrow_back),
    label: Text(parentRouteName), // e.g., "Projects"
    onPressed: () => context.pop(),
  ),
  // ...
)
```

**Option 2: Route-aware back button**
```dart
class ContextualBackButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final parentLabel = _getParentLabel(GoRouterState.of(context).uri.path);

    return parentLabel != null
        ? TextButton.icon(
            icon: Icon(Icons.arrow_back),
            label: Text(parentLabel),
            onPressed: () => context.pop(),
          )
        : BackButton();
  }

  String? _getParentLabel(String path) {
    if (path.startsWith('/projects/') && path != '/projects') {
      return 'Projects';
    }
    // Add more cases as needed
    return null;
  }
}
```

## Don't Hand-Roll

Problems with existing solutions that should NOT be custom-built:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Persistent navigation shell | Custom Navigator wrapper | StatefulShellRoute | Handles state preservation, deep linking, back button |
| Responsive breakpoint detection | Manual MediaQuery checks everywhere | ResponsiveLayout widget (exists) or LayoutBuilder | Centralized, consistent, testable |
| NavigationRail animation | Custom animation controller | NavigationRail.extended property | Built-in smooth animation |
| Route state synchronization | Manual state tracking | GoRouterState.of(context) | Always in sync with actual route |

**Key insight:** GoRouter's StatefulShellRoute eliminates the need for custom navigation state management. Breadcrumbs are the only truly custom component needed.

## Common Pitfalls

### Pitfall 1: Router Recreation on Rebuild
**What goes wrong:** GoRouter recreated on every rebuild, losing navigation state
**Why it happens:** Router created in build() method
**How to avoid:** Phase 6 already solved this - router cached in StatefulWidget state
**Warning signs:** Back button doesn't work, navigation jumps unexpectedly

### Pitfall 2: NavigationRail labelType with Extended
**What goes wrong:** Assertion error or visual glitch
**Why it happens:** Setting labelType when extended = true
**How to avoid:** Set `labelType: NavigationRailLabelType.none` when using extended mode
**Warning signs:** Widget tree exception mentioning NavigationRail

### Pitfall 3: Nested Scaffolds with Drawer
**What goes wrong:** Can't access drawer from inner scaffold
**Why it happens:** Scaffold.of(context) finds wrong scaffold
**How to avoid:** Use Scaffold.maybeOf(context) or GlobalKey<ScaffoldState>
**Warning signs:** "no Scaffold ancestor found" error

### Pitfall 4: Branch Index vs Route Path Mismatch
**What goes wrong:** Wrong sidebar item highlighted
**Why it happens:** Using branch index when on nested route
**How to avoid:** Derive index from path, not from StatefulNavigationShell alone
**Warning signs:** Sidebar shows wrong selection after deep navigation

### Pitfall 5: SharedPreferences Web Inconsistency
**What goes wrong:** Sidebar state not persisting after page reload in production
**Why it happens:** Known Flutter web SharedPreferences issue
**How to avoid:** Test in production environment, consider fallback defaults
**Warning signs:** Works in dev, fails in prod deployment

## Code Examples

### ResponsiveScaffold Shell

```dart
// Source: Pattern from Code with Andrea, adapted for this project
class ResponsiveScaffold extends StatelessWidget {
  final StatefulNavigationShell navigationShell;
  final int currentIndex;

  const ResponsiveScaffold({
    required this.navigationShell,
    required this.currentIndex,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= Breakpoints.tablet) {
          // Desktop: NavigationRail + content
          return _DesktopLayout(
            navigationShell: navigationShell,
            currentIndex: currentIndex,
          );
        } else {
          // Mobile: Drawer + content
          return _MobileLayout(
            navigationShell: navigationShell,
            currentIndex: currentIndex,
          );
        }
      },
    );
  }
}
```

### StatefulShellRoute Configuration

```dart
// Source: go_router documentation pattern
StatefulShellRoute.indexedStack(
  builder: (context, state, navigationShell) => ResponsiveScaffold(
    navigationShell: navigationShell,
    currentIndex: navigationShell.currentIndex,
  ),
  branches: [
    StatefulShellBranch(
      routes: [
        GoRoute(path: '/home', builder: (_, __) => const HomeContent()),
      ],
    ),
    StatefulShellBranch(
      routes: [
        GoRoute(
          path: '/projects',
          builder: (_, __) => const ProjectListScreen(),
          routes: [
            GoRoute(
              path: ':id',
              builder: (context, state) => ProjectDetailScreen(
                projectId: state.pathParameters['id']!,
              ),
            ),
          ],
        ),
      ],
    ),
    StatefulShellBranch(
      routes: [
        GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
      ],
    ),
  ],
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ShellRoute | StatefulShellRoute | go_router 6.0 (2023) | Per-branch state preservation |
| Manual IndexedStack | StatefulShellRoute.indexedStack | go_router 7.0 | Simplified API |
| router.location | GoRouterState.of(context).uri | go_router 9.0 | Context-required location access |
| Custom responsive widgets | LayoutBuilder + NavigationRail | Flutter 3.0+ | Built-in Material 3 support |

**Deprecated/outdated:**
- `router.location` getter - removed in go_router 9.0, use `GoRouterState.of(context).uri.path`
- Manually managing nested Navigators - StatefulShellRoute handles this

## Recommended Approach

### Architecture

1. **Create NavigationProvider** - Manages sidebar expanded/collapsed state with SharedPreferences persistence
2. **Refactor GoRouter** - Wrap authenticated routes in StatefulShellRoute.indexedStack
3. **Create ResponsiveScaffold** - Shell widget switching between NavigationRail (desktop) and Drawer (mobile)
4. **Create BreadcrumbBar** - Widget parsing current route and displaying clickable breadcrumbs
5. **Create ContextualBackButton** - Widget showing "Back to {Parent}" instead of generic back arrow
6. **Update individual screens** - Remove per-screen navigation, rely on shell

### Implementation Order

1. NavigationProvider (foundation)
2. ResponsiveScaffold shell widget
3. StatefulShellRoute configuration
4. Sidebar highlighting (currentIndex)
5. BreadcrumbBar widget
6. ContextualBackButton
7. Screen refactoring (remove redundant navigation)

### Tablet Breakpoint (600-899px)

Recommendation: Use collapsed NavigationRail (icons only, no labels) with tooltip on hover. This provides:
- More content space than extended rail
- Persistent navigation visibility (unlike drawer)
- Consistent UX across resize

## Open Questions

1. **Expandable sections in sidebar**
   - What we know: CONTEXT.md mentions expandable section states should persist
   - What's unclear: Whether this means nested menu items (like "Projects > Project List") or just collapsible category headers
   - Recommendation: Implement simple category headers (Home, Projects, Settings) first, add expandable project list in future phase if needed

2. **Breadcrumb mobile treatment**
   - What we know: NAV-02 requires breadcrumb navigation
   - What's unclear: How to display breadcrumbs on mobile with limited width
   - Recommendation: Truncate middle segments with "..." or hide on mobile (back button serves similar purpose)

## Sources

### Primary (HIGH confidence)
- [Code with Andrea - Flutter Bottom Navigation Bar with StatefulShellRoute](https://codewithandrea.com/articles/flutter-bottom-navigation-bar-nested-routes-gorouter/) - StatefulShellRoute patterns
- [Flutter API - NavigationRail](https://api.flutter.dev/flutter/material/NavigationRail-class.html) - Extended/collapsed API
- [pub.dev/packages/go_router](https://pub.dev/packages/go_router) - Current version (17.0.1)
- Existing codebase: `theme_provider.dart` - Persistence pattern

### Secondary (MEDIUM confidence)
- [Code with Andrea - Responsive Layouts](https://codewithandrea.com/articles/flutter-responsive-layouts-split-view-drawer-navigation/) - Split view pattern
- [Apparence Kit - Sidebar with GoRouter](https://apparencekit.dev/blog/how-to-build-flutter-sidebar-menu/) - StatefulShellRoute sidebar implementation
- [GitHub Issue #161090](https://github.com/flutter/flutter/issues/161090) - GoRouter path access patterns

### Tertiary (LOW confidence)
- [GitHub Issue #99118](https://github.com/flutter/flutter/issues/99118) - Breadcrumb feature request (unresolved)
- Various Medium articles on StatefulShellRoute patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - GoRouter StatefulShellRoute is well-documented official pattern
- Architecture: HIGH - Multiple authoritative sources confirm responsive shell approach
- Pitfalls: MEDIUM - Based on known issues and community reports
- Breadcrumbs: MEDIUM - Custom implementation required, no standard solution

**Research date:** 2026-01-29
**Valid until:** 2026-03-01 (60 days - go_router is stable, patterns well-established)
