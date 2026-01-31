# Phase 15: Route Architecture - Research

**Researched:** 2026-01-31
**Domain:** Flutter GoRouter nested routes, errorBuilder, 404 handling
**Confidence:** HIGH

## Summary

Phase 15 implements the foundational URL route architecture for deep linking. The existing codebase already uses GoRouter 17.0.1 with `StatefulShellRoute.indexedStack` and `usePathUrlStrategy()`. The work involves:

1. **Adding nested thread routes** - `/projects/:projectId/threads/:threadId` pattern
2. **Implementing errorBuilder** - Custom 404 page for invalid routes
3. **Updating ConversationScreen** - Accept both `projectId` and `threadId` from URL params

The current architecture is well-suited for this extension. No new packages needed.

**Primary recommendation:** Add thread routes as nested children of the existing project route, implement a simple NotFoundScreen with errorBuilder, and modify ConversationScreen to receive projectId as a required parameter alongside threadId.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| go_router | ^17.0.1 | Declarative routing with URL sync | Already in pubspec.yaml, official Flutter team package |
| flutter_web_plugins | SDK | Path URL strategy | Already configured with `usePathUrlStrategy()` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| provider | ^6.1.5+1 | State management | Already used for AuthProvider with `refreshListenable` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| go_router errorBuilder | go_router onException | onException supersedes errorBuilder; more complexity not needed for simple 404 |
| Nested routes | Flat routes with custom parsing | Nested routes match URL hierarchy naturally, better maintainability |

**Installation:**
```bash
# No new packages needed - all already installed
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/
├── main.dart                    # GoRouter configuration with errorBuilder
├── screens/
│   ├── not_found_screen.dart    # NEW: 404 error page
│   └── conversation/
│       └── conversation_screen.dart  # MODIFY: add projectId param
└── widgets/
    └── breadcrumb_bar.dart      # MODIFY: handle thread routes
```

### Pattern 1: Nested Routes for Thread URLs
**What:** Define thread routes as children of project detail route
**When to use:** When URL hierarchy should match navigation hierarchy
**Example:**
```dart
// Source: GoRouter official documentation + existing codebase pattern
StatefulShellBranch(
  routes: [
    GoRoute(
      path: '/projects',
      builder: (context, state) => const ProjectListScreen(),
      routes: [
        GoRoute(
          path: ':id',  // Using :id to match existing code
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return ProjectDetailScreen(projectId: id);
          },
          routes: [
            // NEW: Thread route as child of project
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
          ],
        ),
      ],
    ),
  ],
),
```

### Pattern 2: errorBuilder for 404 Pages
**What:** Custom error page shown when no route matches
**When to use:** GoRouter cannot find a matching route
**Example:**
```dart
// Source: GoRouter Error handling documentation
GoRouter(
  // ... existing configuration ...
  errorBuilder: (context, state) {
    return NotFoundScreen(
      attemptedPath: state.uri.path,
    );
  },
)
```

### Pattern 3: NotFoundScreen Widget
**What:** User-friendly 404 page with navigation options
**When to use:** errorBuilder callback
**Example:**
```dart
// Source: GoRouter examples repository
class NotFoundScreen extends StatelessWidget {
  final String attemptedPath;

  const NotFoundScreen({super.key, required this.attemptedPath});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Page Not Found')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              '404 - Page Not Found',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'The page "$attemptedPath" does not exist.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => context.go('/home'),
              icon: const Icon(Icons.home),
              label: const Text('Go to Home'),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Anti-Patterns to Avoid
- **Creating router inside build():** Router must be created once to preserve URL state on refresh
- **Using onException instead of errorBuilder:** More complex, not needed for simple 404
- **Using Navigator.push() for thread navigation:** Breaks URL sync; must use context.go()

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 404 page routing | Manual route checking in redirect | errorBuilder | GoRouter provides this API specifically for unknown routes |
| URL parameter extraction | Regex/string parsing | state.pathParameters | Type-safe, handles encoding automatically |
| Back navigation from nested route | Manual navigation stack | Nested route structure | GoRouter handles back navigation automatically for nested routes |

**Key insight:** GoRouter's nested route structure automatically provides correct back navigation. When user is at `/projects/abc/threads/xyz` and presses back, GoRouter navigates to `/projects/abc` because that's the parent route.

## Common Pitfalls

### Pitfall 1: Router Recreation Destroys URL on Refresh
**What goes wrong:** After refresh, URL briefly shows correct path then redirects to /home
**Why it happens:** Router created inside widget that rebuilds, losing URL state
**How to avoid:** Current code already handles this with `_isRouterInitialized` flag and `_routerInstance` stored in State
**Warning signs:** URL changes after 1-2 seconds on refresh; test F5 on nested routes

### Pitfall 2: StatefulShellRoute Back Navigation
**What goes wrong:** Back button from thread goes to wrong location
**Why it happens:** Deep links use `go()` semantics which replace stack
**How to avoid:** Nested routes within same branch handle this correctly; verify back navigation in testing
**Warning signs:** Back button goes to home instead of project detail

### Pitfall 3: Path Parameter Name Mismatch
**What goes wrong:** pathParameters['projectId'] returns null
**Why it happens:** Route uses `:id` but code expects `projectId`
**How to avoid:** Use consistent naming; current code uses `:id` for projects, continue that pattern
**Warning signs:** Null errors when extracting path parameters

### Pitfall 4: Missing Thread Route in Breadcrumbs
**What goes wrong:** Breadcrumbs don't show correct hierarchy for thread URLs
**Why it happens:** BreadcrumbBar only handles `/projects/:id`, not `/projects/:id/threads/:threadId`
**How to avoid:** Extend breadcrumb parsing logic for new route depth
**Warning signs:** Breadcrumbs show "Projects > Item" instead of proper thread name

## Code Examples

Verified patterns from official sources:

### Current Router Structure (main.dart:206-262)
```dart
// Existing StatefulShellRoute structure to extend
StatefulShellRoute.indexedStack(
  builder: (context, state, navigationShell) {
    // selectedIndex derived from path for proper highlighting
    final selectedIndex = _getSelectedIndex(state.uri.path);
    return ResponsiveScaffold(
      currentIndex: selectedIndex,
      onDestinationSelected: (index) => navigationShell.goBranch(index),
      child: navigationShell,
    );
  },
  branches: [
    // Branch 0: Home
    StatefulShellBranch(routes: [/* /home */]),
    // Branch 1: Projects - ADD THREAD ROUTES HERE
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
              // ADD: Thread route nested here
            ),
          ],
        ),
      ],
    ),
    // Branch 2: Settings
    StatefulShellBranch(routes: [/* /settings */]),
  ],
),
```

### Thread Navigation (from ThreadListScreen)
```dart
// Current: Uses Navigator.push (breaks URL sync)
// thread_list_screen.dart lines 47-54
void _onThreadTap(String threadId) {
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => ConversationScreen(threadId: threadId),
    ),
  );
}

// Updated: Use context.go for URL sync
void _onThreadTap(String threadId) {
  context.go('/projects/${widget.projectId}/threads/$threadId');
}
```

### ConversationScreen Update
```dart
// Current signature
class ConversationScreen extends StatefulWidget {
  final String threadId;
  const ConversationScreen({super.key, required this.threadId});
}

// Updated signature (add projectId)
class ConversationScreen extends StatefulWidget {
  final String projectId;
  final String threadId;
  const ConversationScreen({
    super.key,
    required this.projectId,
    required this.threadId,
  });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HashUrlStrategy | PathUrlStrategy | go_router 6.0+ | Clean URLs, SEO-friendly (already using PathUrlStrategy) |
| onException for errors | errorBuilder for 404 | go_router 10.0+ | Simpler API for common case |

**Deprecated/outdated:**
- `errorPageBuilder`: Use `errorBuilder` instead (simpler)
- Hash URLs (`/#/path`): Use path URLs for professional appearance

## Open Questions

Things that couldn't be fully resolved:

1. **Thread title in breadcrumbs**
   - What we know: ConversationProvider has thread title after load
   - What's unclear: How to access thread title in BreadcrumbBar before ConversationScreen loads
   - Recommendation: Show generic "Conversation" or fetch thread title in breadcrumb; decide during implementation

2. **Selected index for thread routes**
   - What we know: `_getSelectedIndex()` checks path.startsWith('/projects')
   - What's unclear: Does `/projects/abc/threads/xyz` correctly highlight Projects tab?
   - Recommendation: Test and verify; likely works since it starts with '/projects'

## Sources

### Primary (HIGH confidence)
- [go_router pub.dev](https://pub.dev/packages/go_router) - Version 17.0.1, nested routes, errorBuilder
- [GoRouter Error handling docs](https://pub.dev/documentation/go_router/latest/topics/Error%20handling-topic.html) - errorBuilder API
- Existing codebase: `frontend/lib/main.dart` lines 146-267 (current router config)

### Secondary (MEDIUM confidence)
- [GitHub Issue #172026](https://github.com/flutter/flutter/issues/172026) - Router recreation URL preservation
- [GoRouter Configuration docs](https://pub.dev/documentation/go_router/latest/topics/Configuration-topic.html) - Nested route patterns

### Tertiary (LOW confidence)
- [CodeWithAndrea nested routes guide](https://codewithandrea.com/articles/flutter-bottom-navigation-bar-nested-routes-gorouter/) - Pattern validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing packages, no additions
- Architecture: HIGH - Following established GoRouter patterns
- Pitfalls: HIGH - Verified via v1.7 research documents and GitHub issues

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (go_router is "feature-complete", stable API)

---

## Implementation Checklist (For Planner)

Phase 15 should implement:

1. **Add nested thread route** to existing project route in main.dart
2. **Create NotFoundScreen** widget at `screens/not_found_screen.dart`
3. **Add errorBuilder** to GoRouter constructor
4. **Update ConversationScreen** to accept projectId parameter
5. **Update ThreadListScreen** to use `context.go()` instead of `Navigator.push()`
6. **Update breadcrumb_bar.dart** to handle `/projects/:id/threads/:threadId` paths
7. **Update _getSelectedIndex()** if needed for thread route highlighting

**No package installations needed.**
**No backend changes needed.**
