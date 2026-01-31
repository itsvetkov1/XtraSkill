# Phase 17: Screen URL Integration - Research

**Researched:** 2026-01-31
**Domain:** Flutter GoRouter URL parameter consumption, browser navigation, resource not-found states
**Confidence:** HIGH

## Summary

Phase 17 completes the deep linking implementation by ensuring screens correctly read URL parameters and handle cases where linked resources no longer exist. The codebase already has most of the foundation in place from Phase 15 and 16:

1. **ROUTE-02 (Browser back/forward)** - Largely working by design. GoRouter with nested routes maintains browser history correctly. Need to verify and potentially add `GoRouter.optionURLReflectsImperativeAPIs = true` for complete consistency.

2. **ROUTE-04 (ConversationScreen URL params)** - Already implemented in Phase 15. ConversationScreen accepts `projectId` and `threadId` from URL parameters.

3. **ERR-02/ERR-03 (Project/Thread not found)** - Need to implement distinct error states. Currently, providers catch 404 errors but don't distinguish between "error loading" and "resource not found". Screens need to display user-friendly "Project not found" or "Thread not found" states with navigation options.

**Primary recommendation:** Add `isNotFound` state flag to providers, create a reusable `ResourceNotFoundState` widget, and update screens to display appropriate not-found messages when API returns 404.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| go_router | ^17.0.1 | Declarative routing with URL params | Already in use, handles browser history |
| provider | ^6.1.5+1 | State management with error states | Already in use for all providers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dio | ^5.4.0 | HTTP client with status codes | Already in use, returns 404 status codes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Provider error flag | Sealed class states | Sealed classes more type-safe but more refactoring |
| Reusable widget | Inline error UI | Widget ensures consistency, less duplication |

**Installation:**
```bash
# No new packages needed - all already installed
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/
|-- widgets/
|   +-- resource_not_found_state.dart  # NEW: Reusable not-found UI
|-- providers/
|   |-- project_provider.dart          # MODIFY: Add isNotFound flag
|   +-- conversation_provider.dart     # MODIFY: Add isNotFound flag
+-- screens/
    |-- projects/
    |   +-- project_detail_screen.dart # MODIFY: Show not-found state
    +-- conversation/
        +-- conversation_screen.dart   # MODIFY: Show not-found state
```

### Pattern 1: Distinguishing "Not Found" from "Error"
**What:** Separate 404 responses from other API errors
**When to use:** When screens need to show different UI for "doesn't exist" vs "failed to load"
**Example:**
```dart
// In provider
class ProjectProvider extends ChangeNotifier {
  bool _isNotFound = false;
  String? _error;

  bool get isNotFound => _isNotFound;
  String? get error => _error;

  Future<void> selectProject(String id) async {
    _loading = true;
    _error = null;
    _isNotFound = false;
    notifyListeners();

    try {
      _selectedProject = await _projectService.getProject(id);
    } catch (e) {
      final errorMessage = e.toString();
      // Check if it's a 404 "not found" error
      if (errorMessage.contains('not found') ||
          errorMessage.contains('404')) {
        _isNotFound = true;
        _error = null; // Not a "real" error, just not found
      } else {
        _error = errorMessage;
        _isNotFound = false;
      }
      _selectedProject = null;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  void clearError() {
    _error = null;
    _isNotFound = false;
    notifyListeners();
  }
}
```

### Pattern 2: ResourceNotFoundState Widget
**What:** Reusable widget for "resource not found" UI state
**When to use:** When a valid route points to a deleted/non-existent resource
**Example:**
```dart
// Source: Adapted from existing EmptyState and NotFoundScreen patterns
class ResourceNotFoundState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String buttonLabel;
  final VoidCallback onPressed;

  const ResourceNotFoundState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    required this.buttonLabel,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 64,
              color: theme.colorScheme.error, // Error color vs primary
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style: theme.textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: onPressed,
              icon: const Icon(Icons.arrow_back),
              label: Text(buttonLabel),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Pattern 3: Screen with Not-Found Handling
**What:** Screen that shows appropriate state for not-found resources
**When to use:** Any screen that loads resources by URL parameter
**Example:**
```dart
// In project_detail_screen.dart
@override
Widget build(BuildContext context) {
  return Consumer<ProjectProvider>(
    builder: (context, provider, child) {
      // Show loading indicator
      if (provider.loading && provider.selectedProject == null) {
        return const Center(child: CircularProgressIndicator());
      }

      // Show not-found state (ERR-02)
      if (provider.isNotFound) {
        return ResourceNotFoundState(
          icon: Icons.folder_off_outlined,
          title: 'Project not found',
          message: 'This project may have been deleted or you may not have access to it.',
          buttonLabel: 'Back to Projects',
          onPressed: () => context.go('/projects'),
        );
      }

      // Show error state (network errors, etc.)
      if (provider.error != null) {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
              const SizedBox(height: 16),
              Text('Error loading project', style: theme.textTheme.titleLarge),
              const SizedBox(height: 8),
              SelectableText(provider.error!),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => provider.selectProject(widget.projectId),
                child: const Text('Retry'),
              ),
            ],
          ),
        );
      }

      // Normal project content...
    },
  );
}
```

### Pattern 4: Browser Back Navigation with GoRouter
**What:** Ensure browser back/forward buttons work correctly with nested routes
**When to use:** Always for web apps with deep linking
**Example:**
```dart
// In main.dart main() function
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Enable URL reflection for browser history consistency
  GoRouter.optionURLReflectsImperativeAPIs = true;

  usePathUrlStrategy();
  runApp(MyApp());
}
```

### Anti-Patterns to Avoid
- **Using generic error message for 404:** "Error loading project" doesn't tell user the resource is gone
- **No navigation option on not-found:** User gets stuck without a way to navigate away
- **Treating 404 as retryable error:** Retry button makes no sense for deleted resources
- **Not clearing not-found state:** Stale not-found state appears on subsequent navigations

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Not-found UI | Custom widget per screen | Shared ResourceNotFoundState | Consistency, maintainability |
| 404 detection | Regex on error messages | Service-level error types | Cleaner separation of concerns |
| Browser history | Manual history management | GoRouter nested routes | GoRouter handles this automatically |

**Key insight:** GoRouter's nested route structure (`/projects/:id/threads/:threadId`) automatically provides correct back navigation. The browser back button from thread goes to project detail because that's how nested routes work. No custom code needed.

## Common Pitfalls

### Pitfall 1: Confusing Not-Found with Error
**What goes wrong:** User sees "Error loading project. Retry?" for a deleted project
**Why it happens:** All API failures treated as generic errors
**How to avoid:** Parse error messages or status codes; set distinct `isNotFound` flag
**Warning signs:** Retry button appears for 404 errors

### Pitfall 2: Browser Back Button Reversed Order
**What goes wrong:** Back button navigates to unexpected pages
**Why it happens:** Known GoRouter issue with imperative navigation APIs
**How to avoid:** Add `GoRouter.optionURLReflectsImperativeAPIs = true` in main()
**Warning signs:** Back button goes to page 4 instead of page 2 after going 1->2->3->4

### Pitfall 3: Not-Found State Persists Across Navigation
**What goes wrong:** User navigates to valid project, still sees "not found" from previous navigation
**Why it happens:** Provider state not cleared when navigating away
**How to avoid:** Clear `isNotFound` flag at start of `selectProject()` call
**Warning signs:** Stale not-found message on valid resources

### Pitfall 4: No Way Out of Not-Found Screen
**What goes wrong:** User sees "Project not found" but has no obvious way to continue
**Why it happens:** Not-found state renders without navigation options
**How to avoid:** Always include "Back to [parent]" button in not-found state
**Warning signs:** Users stuck on not-found screen

### Pitfall 5: Thread Not-Found Without Project Context
**What goes wrong:** User sees "Thread not found" but doesn't know which project it was in
**Why it happens:** Thread screen doesn't have access to project info
**How to avoid:** ConversationScreen already has `projectId` from URL; use it for "Back to Project"
**Warning signs:** Generic "Back to Home" instead of "Back to Project"

## Code Examples

Verified patterns from existing codebase and official sources:

### Current Project Detail Error Handling (to modify)
```dart
// Current: project_detail_screen.dart lines 75-98
// Show error message
if (provider.error != null) {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.error_outline,
            size: 48, color: Theme.of(context).colorScheme.error),
        const SizedBox(height: 16),
        Text(
          'Error loading project',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        SelectableText(provider.error!),
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: () => provider.selectProject(widget.projectId),
          child: const Text('Retry'),
        ),
      ],
    ),
  );
}

final project = provider.selectedProject;
if (project == null) {
  return const Center(child: Text('Project not found'));  // Currently simple text
}
```

### Current ConversationScreen Error Banner (to extend)
```dart
// Current: conversation_screen.dart lines 152-167
// Error banner
if (provider.error != null)
  MaterialBanner(
    content: SelectableText(provider.error!),
    backgroundColor: Theme.of(context).colorScheme.errorContainer,
    actions: [
      TextButton(
        onPressed: provider.clearError,
        child: const Text('Dismiss'),
      ),
      if (provider.canRetry)
        TextButton(
          onPressed: provider.retryLastMessage,
          child: const Text('Retry'),
        ),
    ],
  ),
```

### Service 404 Detection (already exists)
```dart
// Current: project_service.dart lines 112-119
} on DioException catch (e) {
  if (e.response?.statusCode == 401) {
    throw Exception('Unauthorized - please login again');
  } else if (e.response?.statusCode == 404) {
    throw Exception('Project not found');  // Already throws specific message
  }
  throw Exception('Failed to load project: ${e.message}');
}

// Current: thread_service.dart lines 119-126
} on DioException catch (e) {
  if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
    throw Exception('Authentication required');
  } else if (e.response?.statusCode == 404) {
    throw Exception('Thread not found');  // Already throws specific message
  }
  throw Exception('Failed to load thread: ${e.message}');
}
```

### Nested Route Structure (already exists)
```dart
// Current: main.dart lines 253-270
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
  ],
),
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic error states | Distinct not-found states | Common pattern | Better UX for deleted resources |
| Custom back navigation | GoRouter nested routes | go_router 6.0+ | Automatic browser history management |

**Deprecated/outdated:**
- Manual `Navigator.pop()` for web back: Use GoRouter nested routes
- Single `error` flag for all failures: Distinguish 404 from other errors

## Open Questions

Things that couldn't be fully resolved:

1. **GoRouter.optionURLReflectsImperativeAPIs**
   - What we know: Setting this to `true` improves browser history consistency
   - What's unclear: Whether our current codebase needs this (uses `context.go()` not `push()`)
   - Recommendation: Add it defensively; test browser back/forward manually

2. **ConversationProvider rethrow behavior**
   - What we know: `loadThread()` calls `rethrow` after setting error state
   - What's unclear: Whether this could cause uncaught exception issues
   - Recommendation: Monitor during implementation; may need to remove rethrow

## Sources

### Primary (HIGH confidence)
- [GoRouter pub.dev](https://pub.dev/packages/go_router) - Version 17.0.1, nested routes
- [GoRouter Error handling docs](https://pub.dev/documentation/go_router/latest/topics/Error%20handling-topic.html) - errorBuilder patterns
- Existing codebase: `frontend/lib/main.dart`, `frontend/lib/providers/`, `frontend/lib/services/`

### Secondary (MEDIUM confidence)
- [Flutter GoRouter nested routes - CodeWithAndrea](https://codewithandrea.com/articles/flutter-bottom-navigation-bar-nested-routes-gorouter/) - StatefulShellRoute patterns
- [GitHub Issue #151941](https://github.com/flutter/flutter/issues/151941) - Browser back button order issue
- [GitHub Issue #162923](https://github.com/flutter/flutter/issues/162923) - Browser back/forward handling

### Tertiary (LOW confidence)
- [GoRouter dialog navigation fix](https://cleancodestack.com/flutter-gorouter-dialog-navigation/) - Router.neglect pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing packages, no additions
- Architecture: HIGH - Extending established provider patterns in codebase
- Pitfalls: HIGH - Verified via codebase review and GitHub issues

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (go_router stable, pattern-based implementation)

---

## Implementation Checklist (For Planner)

Phase 17 should implement:

### ROUTE-02: Browser Back/Forward Navigation
1. **Add `GoRouter.optionURLReflectsImperativeAPIs = true`** in main() for consistency
2. **Manual verification** of browser back/forward behavior on nested routes

### ROUTE-04: ConversationScreen URL Parameters
Already implemented in Phase 15 - no changes needed.

### ERR-02: Project Not Found State
1. **Add `isNotFound` flag to ProjectProvider** - Set when API returns 404
2. **Create ResourceNotFoundState widget** - Reusable not-found UI
3. **Update ProjectDetailScreen** - Show ResourceNotFoundState when `isNotFound` is true

### ERR-03: Thread Not Found State
1. **Add `isNotFound` flag to ConversationProvider** - Set when API returns 404
2. **Update ConversationScreen** - Show ResourceNotFoundState when `isNotFound` is true
3. **Use projectId for navigation** - "Back to Project" instead of "Back to Home"

**No package installations needed.**
**No backend changes needed.**
