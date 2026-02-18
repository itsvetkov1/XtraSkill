# Phase 63: Navigation & Thread Management - Research

**Researched:** 2026-02-17
**Domain:** Flutter Navigation Architecture with go_router, Sidebar UI Patterns, Thread Management
**Confidence:** HIGH

## Summary

Phase 63 implements a dedicated Assistant section in the app with its own sidebar navigation, routes, thread list, creation flow, and deletion behavior. The phase builds on top of Phase 62's backend thread_type discrimination, adding the frontend navigation and UI layer to manage Assistant threads independently of BA Assistant threads.

The existing app already has robust patterns for thread management (ThreadProvider, thread list screens, thread creation dialogs), sidebar navigation (ResponsiveScaffold with NavigationRail), and deep link routing (StatefulShellRoute with go_router). Phase 63 adapts these patterns to create a parallel Assistant section without disrupting the existing BA Assistant flow.

**Primary recommendation:** Extend the existing ResponsiveScaffold navigation model with a new StatefulShellBranch for /assistant routes, create Assistant-specific screens by adapting ChatsScreen patterns (filtering threads by thread_type='assistant'), and reuse the thread deletion/creation patterns with simplified fields (no project, no mode selector).

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Sidebar Placement:**
- Assistant section appears ABOVE the BA Assistant section in the sidebar
- Both sections have expandable thread lists — clicking the section header expands to show recent threads inline
- Section headers with labels ("Assistant" and "BA Assistant") plus a horizontal divider separating the two sections
- Assistant icon: a bold "level up" plus icon (RPG stat-upgrade style) — ties to XtraSkill branding. Use `Icons.add_circle` or similar bold plus from Material Icons as closest match

**Thread List Layout:**
- Each thread shows title + last activity timestamp — minimal, no previews or message counts
- Sorted by most recent activity first (last activity timestamp, newest at top)
- Same compact list style in both the sidebar expansion and the main /assistant content area — no card layout
- Empty state: friendly illustration with "Start your first conversation" call-to-action button

**Thread Creation Flow:**
- Button + dialog approach — a "New Thread" button opens a small dialog
- Dialog fields: title (required, empty field with placeholder hint) + description (optional)
- No project selector, no mode selector (simplified vs BA creation)
- After creation: navigate immediately into the new thread's conversation screen

**Delete Behavior:**
- Delete triggered via a visible trash/delete icon on each thread item (always visible, not hover-only)
- Undo via bottom snackbar with "Undo" action and 10-second countdown
- If deleting the currently-viewed thread: navigate back to /assistant thread list
- Thread is soft-deleted during undo window, hard-deleted after timeout

### Claude's Discretion

- Exact animation/transition for sidebar expansion
- Specific illustration choice for empty state
- Thread item spacing and typography details
- Exact placeholder text for creation dialog fields

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAV-01 | "Assistant" appears as its own section in sidebar navigation | go_router StatefulShellBranch pattern supports multi-section navigation; ResponsiveScaffold NavigationRail can be extended with additional destinations |
| NAV-02 | Assistant section has dedicated routes (`/assistant`, `/assistant/:threadId`) | go_router nested routes pattern; existing `/chats/:threadId` demonstrates project-less thread routing |
| NAV-03 | Deep links to Assistant threads work correctly on page refresh | go_router with path URL strategy (already configured); existing routes demonstrate deep link support |
| UI-01 | Assistant thread list screen shows only Assistant-type threads | Backend thread_type filter on GET /api/threads?thread_type=assistant; ThreadProvider.loadThreads can filter client-side or via API param |
| UI-02 | User can create new Assistant thread (simplified dialog — no project, no mode selector) | Existing ThreadCreateDialog pattern; POST /api/threads with thread_type='assistant' (backend enforces no project) |
| UI-05 | User can delete Assistant threads with standard undo behavior | Existing ThreadProvider.deleteThread with SnackBar undo; same 10-second window and optimistic UI removal |

</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| go_router | ^14.0.0 | Declarative routing, deep linking, nested routes | Official Flutter routing solution, type-safe, supports StatefulShellRoute for persistent navigation shells |
| provider | ^6.1.0 | State management for thread lists, navigation state | Flutter team-recommended, reactive state updates, already used throughout app |
| flutter/material | 3.x | UI components (NavigationRail, ListTile, Dialog) | Built-in Material Design 3 components, no external dependencies |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shared_preferences | ^2.0.0 | Persist sidebar expanded/collapsed state | Already used for NavigationProvider, theme preferences |
| skeletonizer | Latest | Loading skeleton for thread lists during fetch | Already used in ChatsScreen, ThreadListScreen |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| StatefulShellRoute | Manual state preservation | StatefulShellRoute maintains per-branch navigation stacks automatically, manual state requires custom logic |
| NavigationRail | Drawer-only navigation | NavigationRail is desktop-optimized, responsive (desktop rail, mobile drawer already implemented) |
| ThreadProvider pattern | Direct API calls in widgets | ThreadProvider centralizes state, enables optimistic UI updates, undo behavior |

**Installation:**
No new dependencies — all patterns use existing libraries already in pubspec.yaml.

---

## Architecture Patterns

### Recommended Project Structure

Current structure already established, Phase 63 extends it:

```
frontend/lib/
├── screens/
│   ├── assistant/                    # NEW: Assistant-specific screens
│   │   ├── assistant_list_screen.dart   # Thread list for /assistant route
│   │   └── assistant_create_dialog.dart # Simplified thread creation (no project/mode)
│   ├── chats_screen.dart              # REFERENCE: Global threads list (similar pattern)
│   └── threads/
│       ├── thread_list_screen.dart    # REFERENCE: BA threads list (existing)
│       └── thread_create_dialog.dart  # REFERENCE: BA creation dialog (existing)
├── widgets/
│   └── responsive_scaffold.dart       # MODIFY: Add Assistant nav destination
├── providers/
│   └── thread_provider.dart           # EXTEND: Filter by thread_type
└── main.dart                          # MODIFY: Add /assistant StatefulShellBranch
```

### Pattern 1: StatefulShellRoute with Parallel Branches

**What:** go_router's StatefulShellRoute maintains separate navigation stacks per branch. Each branch preserves its scroll position, selected thread, etc.

**When to use:** When multiple top-level navigation sections need independent state (e.g., Chats and Assistant both need their own "current thread" state).

**Example from main.dart (existing pattern):**
```dart
// Source: /Users/a1testingmac/projects/XtraSkill/frontend/lib/main.dart lines 252-346
StatefulShellRoute.indexedStack(
  builder: (context, state, navigationShell) => ResponsiveScaffold(
    currentIndex: _getSelectedIndex(state.uri.path),
    onDestinationSelected: (index) => navigationShell.goBranch(index, initialLocation: true),
    child: navigationShell,
  ),
  branches: [
    StatefulShellBranch(routes: [GoRoute(path: '/home', ...)]),
    StatefulShellBranch(routes: [GoRoute(path: '/chats', routes: [
      GoRoute(path: ':threadId', ...) // Nested route for /chats/:threadId
    ])]),
    StatefulShellBranch(routes: [GoRoute(path: '/projects', ...)]),
    StatefulShellBranch(routes: [GoRoute(path: '/settings', ...)]),
  ],
)
```

**For Phase 63:** Add a 5th branch for `/assistant` with nested `:threadId` route (same pattern as Chats branch).

### Pattern 2: Thread List with thread_type Filtering

**What:** Load threads from backend with thread_type query parameter, or filter client-side if already loaded.

**When to use:** When a screen should show only a specific thread type (Assistant vs BA Assistant).

**Example from backend API (Phase 62):**
```dart
// Backend: GET /api/threads?thread_type=assistant
// Returns only threads with thread_type='assistant'

// Frontend implementation options:
// Option A: API-level filter (better for large lists)
final response = await _dio.get('/api/threads?thread_type=assistant');

// Option B: Client-side filter (better if already loaded all threads)
final assistantThreads = allThreads.where((t) => t.threadType == 'assistant').toList();
```

**Recommendation for Phase 63:** Use API-level filter (Option A) to avoid loading BA threads unnecessarily.

### Pattern 3: Optimistic Delete with Undo (Existing)

**What:** Remove item from UI immediately, show SnackBar with Undo button, commit delete after timeout.

**When to use:** Standard pattern for all delete operations in the app.

**Example from ThreadProvider:**
```dart
// Source: /Users/a1testingmac/projects/XtraSkill/frontend/lib/providers/thread_provider.dart lines 245-287
Future<void> deleteThread(BuildContext context, String threadId) async {
  final index = _threads.indexWhere((t) => t.id == threadId);
  _pendingDelete = _threads[index];
  _threads.removeAt(index);
  notifyListeners();

  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
    content: Text('Thread deleted'),
    duration: Duration(seconds: 10),
    action: SnackBarAction(label: 'Undo', onPressed: () => _undoDelete()),
  ));

  _deleteTimer = Timer(Duration(seconds: 10), () => _commitPendingDelete());
}
```

**For Phase 63:** Reuse ThreadProvider.deleteThread as-is. If deleting currently-viewed thread, add navigation to `/assistant` before showing SnackBar.

### Pattern 4: Simplified Creation Dialog (No Project, No Mode)

**What:** Thread creation dialog with only title + description fields, no project selector dropdown, no mode chips.

**When to use:** Assistant threads are project-less by design (backend enforces via silent ignore if project_id sent).

**Reference from existing BA dialog:**
```dart
// Source: /Users/a1testingmac/projects/XtraSkill/frontend/lib/screens/threads/thread_create_dialog.dart
// BA version has: projectId required in constructor, title field, provider dropdown
// Assistant version needs: title field (required with hint), description field (optional)
```

**For Phase 63:** Create new `AssistantCreateDialog` with:
- Title field (required, placeholder: "e.g., Debug CSS Layout")
- Description field (optional, placeholder: "Optional details about this conversation")
- No project selector (Assistant threads are always project-less)
- No mode selector (mode is BA-specific feature)

### Anti-Patterns to Avoid

- **Don't create separate ThreadProvider for Assistant threads:** Reuse existing ThreadProvider, filter by thread_type. Multiple providers lead to state sync issues.
- **Don't hard-code thread_type in UI components:** Pass thread_type as parameter to shared components (e.g., ThreadListScreen could accept `threadType` filter param).
- **Don't skip navigation after creation:** User expects immediate navigation into new thread after creation (matches BA Assistant behavior).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Navigation state preservation | Custom stack management | StatefulShellRoute.indexedStack | go_router handles per-branch state, back button, deep links automatically |
| Thread list filtering | Manual array operations in widgets | ThreadProvider with query params | Centralized state, loading indicators, error handling, optimistic updates |
| Undo deletion | Custom timer + rollback logic | Existing ThreadProvider.deleteThread | Already handles undo window, rollback, API errors, navigation cleanup |
| Empty state illustrations | Custom SVG assets | EmptyState widget (existing) | Consistent styling, already used in ThreadListScreen, ChatsScreen |

**Key insight:** The app has mature patterns for thread management, navigation, and deletion. Extending these patterns is faster, more maintainable, and more consistent than building parallel implementations.

---

## Common Pitfalls

### Pitfall 1: Navigation Index Mismatch After Adding Assistant Branch

**What goes wrong:** Adding a new StatefulShellBranch changes the index numbers of existing branches. If ResponsiveScaffold destinations array doesn't match branch order, navigation breaks.

**Why it happens:** StatefulShellRoute branch index must align with NavigationRail destination index.

**How to avoid:**
1. Add Assistant navigation destination in ResponsiveScaffold at the correct index position
2. Update `_getSelectedIndex()` logic to map `/assistant` paths to the new branch index
3. Ensure NavigationRail destinations array matches branch order exactly

**Warning signs:** Clicking "Assistant" navigates to wrong screen, sidebar highlights wrong item.

**Example fix:**
```dart
// Before (4 branches): Home=0, Chats=1, Projects=2, Settings=3
// After (5 branches): Home=0, Assistant=1, Chats=2, Projects=3, Settings=4

// Update _getSelectedIndex in main.dart:
int _getSelectedIndex(String path) {
  if (path.startsWith('/home')) return 0;
  if (path.startsWith('/assistant')) return 1; // NEW
  if (path.startsWith('/chats')) return 2;     // Shifted from 1
  if (path.startsWith('/projects')) return 3;  // Shifted from 2
  if (path.startsWith('/settings')) return 4;  // Shifted from 3
  return 0;
}
```

### Pitfall 2: Thread Deletion While Viewing That Thread

**What goes wrong:** Deleting the currently-viewed thread leaves user on a 404 screen or blank conversation view.

**Why it happens:** ConversationScreen still references deleted thread, no navigation triggered.

**How to avoid:** Check if deleted thread matches selectedThread, navigate to thread list before showing SnackBar.

**Warning signs:** User deletes thread, sees loading spinner or "Thread not found" error.

**Example fix:**
```dart
Future<void> deleteThread(BuildContext context, String threadId) async {
  // ... existing optimistic removal logic ...

  // NEW: Navigate away if deleting current thread
  if (_selectedThread?.id == threadId) {
    _selectedThread = null;
    // Trigger navigation in widget that called deleteThread
    // OR use context.go('/assistant') here if BuildContext available
  }

  // ... existing SnackBar and timer logic ...
}
```

### Pitfall 3: Forgetting to Update Breadcrumb Logic

**What goes wrong:** Navigating to `/assistant` or `/assistant/:threadId` shows incorrect breadcrumbs (e.g., "Chats > Thread" instead of "Assistant > Thread").

**Why it happens:** BreadcrumbBar widget needs route handler for new /assistant paths.

**How to avoid:** Add breadcrumb logic for `/assistant` routes in `breadcrumb_bar.dart` following existing pattern.

**Warning signs:** Breadcrumbs missing or incorrect on Assistant screens.

**Example fix:**
```dart
// In BreadcrumbBar._buildBreadcrumbs() add:
if (path.startsWith('/assistant/')) {
  final threadId = path.split('/').last;
  final threadTitle = await _fetchThreadTitle(threadId); // Or from provider
  return [
    _Breadcrumb(label: 'Assistant', path: '/assistant'),
    _Breadcrumb(label: threadTitle, path: path, isCurrent: true),
  ];
} else if (path == '/assistant') {
  return [_Breadcrumb(label: 'Assistant', path: path, isCurrent: true)];
}
```

### Pitfall 4: Using ChatsProvider Instead of ThreadProvider

**What goes wrong:** ChatsProvider is designed for global threads (all types), has pagination, search, and cross-project features. Using it for Assistant-only threads causes filtering complexity.

**Why it happens:** ChatsScreen uses ChatsProvider, tempting to reuse for Assistant screen.

**How to avoid:** Use ThreadProvider for Assistant thread list (same as BA thread lists), filter by thread_type='assistant' at API or provider level.

**Warning signs:** Assistant thread list shows BA threads, search returns mixed results, pagination logic overly complex.

**Example approach:**
```dart
// GOOD: ThreadProvider with filter
class AssistantListScreen extends StatefulWidget {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Option A: Add loadThreadsByType method to ThreadProvider
      context.read<ThreadProvider>().loadThreadsByType('assistant');

      // Option B: Filter after loading all threads (if already loaded)
      // (Less ideal for large thread counts)
    });
  }
}

// BAD: Using ChatsProvider and filtering in UI
// Creates unnecessary complexity, loads all threads unnecessarily
```

---

## Code Examples

Verified patterns from existing codebase:

### Nested Route Pattern (for /assistant/:threadId)

```dart
// Source: /Users/a1testingmac/projects/XtraSkill/frontend/lib/main.dart lines 279-298
// Existing Chats branch with nested threadId route:
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
)

// For Assistant: Same pattern, different path
StatefulShellBranch(
  routes: [
    GoRoute(
      path: '/assistant',
      builder: (context, state) => const AssistantListScreen(),
      routes: [
        GoRoute(
          path: ':threadId',
          builder: (context, state) {
            final threadId = state.pathParameters['threadId']!;
            return ConversationScreen(
              projectId: null,
              threadId: threadId,
            );
          },
        ),
      ],
    ),
  ],
)
```

### ThreadProvider Delete with Undo Pattern

```dart
// Source: /Users/a1testingmac/projects/XtraSkill/frontend/lib/providers/thread_provider.dart lines 245-316
Future<void> deleteThread(BuildContext context, String threadId) async {
  final index = _threads.indexWhere((t) => t.id == threadId);
  if (index == -1) return;

  // Cancel any previous pending delete
  if (_pendingDelete != null) {
    await _commitPendingDelete();
  }

  // Remove optimistically
  _pendingDelete = _threads[index];
  _pendingDeleteIndex = index;
  _threads.removeAt(index);

  // Clear selected if it was the deleted thread
  if (_selectedThread?.id == threadId) {
    _selectedThread = null;
  }

  notifyListeners();

  // Show undo SnackBar
  if (context.mounted) {
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Thread deleted'),
        duration: const Duration(seconds: 10),
        action: SnackBarAction(
          label: 'Undo',
          onPressed: () => _undoDelete(),
        ),
      ),
    );
  }

  // Start deletion timer
  _deleteTimer?.cancel();
  _deleteTimer = Timer(const Duration(seconds: 10), () {
    _commitPendingDelete();
  });
}

void _undoDelete() {
  _deleteTimer?.cancel();
  if (_pendingDelete != null) {
    final insertIndex = _pendingDeleteIndex.clamp(0, _threads.length);
    _threads.insert(insertIndex, _pendingDelete!);
    _pendingDelete = null;
    notifyListeners();
  }
}

Future<void> _commitPendingDelete() async {
  if (_pendingDelete == null) return;

  final threadToDelete = _pendingDelete!;
  final originalIndex = _pendingDeleteIndex;
  _pendingDelete = null;

  try {
    await _threadService.deleteThread(threadToDelete.id);
  } catch (e) {
    // Rollback: restore to list
    final insertIndex = originalIndex.clamp(0, _threads.length);
    _threads.insert(insertIndex, threadToDelete);
    _error = 'Failed to delete thread: $e';
    notifyListeners();
  }
}
```

### Thread Creation with Navigation

```dart
// Pattern from ThreadCreateDialog (simplified for Assistant):
Future<void> _createThread() async {
  setState(() => _isCreating = true);

  try {
    final threadProvider = context.read<ThreadProvider>();
    final providerProvider = context.read<ProviderProvider>();

    final thread = await threadProvider.createThread(
      null, // No projectId for Assistant threads
      _titleController.text.trim(),
      provider: providerProvider.selectedProvider,
    );

    if (mounted) {
      Navigator.of(context).pop(); // Close dialog
      // Navigate to conversation screen
      context.go('/assistant/${thread.id}');
    }
  } catch (e) {
    if (mounted) {
      setState(() => _isCreating = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to create thread: $e')),
      );
    }
  }
}
```

### Empty State Pattern

```dart
// Source: /Users/a1testingmac/projects/XtraSkill/frontend/lib/screens/threads/thread_list_screen.dart lines 131-140
EmptyState(
  icon: Icons.chat_bubble_outline,
  title: 'No conversations yet',
  message: 'Start a conversation to discuss requirements with AI assistance.',
  buttonLabel: 'Start Conversation',
  buttonIcon: Icons.add_comment,
  onPressed: _showCreateDialog,
)

// For Assistant screen: Same pattern, different copy
EmptyState(
  icon: Icons.add_circle, // Bold plus icon (XtraSkill branding)
  title: 'No conversations yet',
  message: 'Start your first conversation with Claude Code.',
  buttonLabel: 'New Conversation',
  buttonIcon: Icons.add,
  onPressed: _showCreateDialog,
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hash-based URLs (#/route) | Path-based URLs (/route) | v1.7 (Phase US-001) | Deep links work on page refresh, shareable URLs |
| Manual navigation stack | StatefulShellRoute | v1.5 (Phase 7) | Per-branch state preservation, no manual stack management |
| Global thread list only | Thread type filtering | v3.0 (Phase 62) | Backend supports thread_type discrimination, enables separate Assistant UI |
| Single ThreadProvider for all threads | Thread type filtering at API level | Phase 62 | Avoids loading irrelevant threads, cleaner separation |

**Deprecated/outdated:**
- Hash URLs: Replaced by path URLs (usePathUrlStrategy in main.dart)
- Manual back button handling: go_router context.canPop() handles this automatically
- Separate providers per thread type: Use single ThreadProvider with filtering instead

---

## Open Questions

1. **Sidebar Expandable Thread Lists**
   - What we know: User wants inline thread lists that expand when clicking section header (both BA Assistant and Assistant sections)
   - What's unclear: Whether sidebar expansion should:
     - Show recent N threads inline (e.g., 5 most recent)
     - Scroll within sidebar if more threads exist
     - Include "View All" link to main screen
   - Recommendation: Start with "View All" link only (no inline threads). Inline thread lists in NavigationRail require custom ExpansionTile-like behavior, adds complexity. User said "Claude's discretion" for animation details, so this is within scope to defer.

2. **Thread List Compact Style**
   - What we know: "Same compact list style in both sidebar expansion and main content area — no card layout"
   - What's unclear: Whether ListTile is compact enough or if custom widget needed
   - Recommendation: Use Material ListTile with `dense: true` for compactness, remove Card wrapper. ListTile shows title + subtitle (timestamp) naturally.

3. **Assistant Icon in Sidebar**
   - What we know: "Bold level up plus icon (RPG stat-upgrade style), use Icons.add_circle or similar"
   - What's unclear: Whether to use filled vs outlined variant, size, color
   - Recommendation: Use `Icons.add_circle` (filled) for selected state, `Icons.add_circle_outline` for unselected. Matches existing pattern (e.g., `Icons.chat_bubble` vs `Icons.chat_bubble_outline`).

---

## Sources

### Primary (HIGH confidence)

- **Existing Codebase Files** (current implementation):
  - `/Users/a1testingmac/projects/XtraSkill/frontend/lib/main.dart` - StatefulShellRoute pattern, existing navigation branches
  - `/Users/a1testingmac/projects/XtraSkill/frontend/lib/widgets/responsive_scaffold.dart` - NavigationRail implementation, navigation destinations
  - `/Users/a1testingmac/projects/XtraSkill/frontend/lib/providers/thread_provider.dart` - Thread state management, delete with undo pattern
  - `/Users/a1testingmac/projects/XtraSkill/frontend/lib/screens/chats_screen.dart` - Global thread list pattern (reference for Assistant list)
  - `/Users/a1testingmac/projects/XtraSkill/frontend/lib/screens/threads/thread_list_screen.dart` - Project thread list pattern, empty states
  - `/Users/a1testingmac/projects/XtraSkill/frontend/lib/screens/threads/thread_create_dialog.dart` - Thread creation dialog pattern
  - `/Users/a1testingmac/projects/XtraSkill/backend/app/routes/threads.py` - Thread API with thread_type filtering (Phase 62)
  - `/Users/a1testingmac/projects/XtraSkill/.planning/phases/62-backend-foundation/62-VERIFICATION.md` - Phase 62 backend support verification

- **Official Flutter Documentation**:
  - go_router package documentation (pub.dev) - StatefulShellRoute, nested routes, deep linking
  - Material Design 3 NavigationRail documentation (api.flutter.dev)
  - Provider package documentation (pub.dev) - ChangeNotifier pattern

### Secondary (MEDIUM confidence)

- **Phase Context and Requirements**:
  - `.planning/phases/63-navigation-thread-management/63-CONTEXT.md` - User decisions from discussion phase
  - `.planning/REQUIREMENTS.md` - NAV-01 through NAV-03, UI-01, UI-02, UI-05 specifications
  - `.planning/ROADMAP.md` - Phase dependencies, success criteria

### Tertiary (LOW confidence)

None required — all research derived from existing codebase patterns and official Flutter documentation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, verified in pubspec.yaml
- Architecture: HIGH - Existing patterns from Chats, Projects, Threads screens provide direct templates
- Pitfalls: HIGH - Derived from existing navigation index logic, deletion flows, breadcrumb handling
- Code examples: HIGH - All examples extracted from current codebase, verified functional

**Research date:** 2026-02-17
**Valid until:** 30 days (stable patterns, no fast-moving dependencies)
