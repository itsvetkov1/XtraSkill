# Phase 39: Breadcrumb Navigation - Research

**Researched:** 2026-02-04
**Domain:** Flutter Navigation / go_router / Breadcrumb UX
**Confidence:** HIGH

## Summary

This phase enhances breadcrumb navigation to show full context including thread titles and document names, and converts the Document Viewer from a modal push to a proper GoRouter route. Research confirms this is achievable with the existing stack (go_router 17.0.1) using established patterns already present in the codebase.

The codebase already has a working `BreadcrumbBar` widget that uses `GoRouterState.of(context)` to parse the current path and build breadcrumbs. The current implementation handles `/projects`, `/projects/:id`, and `/projects/:id/threads/:threadId` routes. This phase extends that pattern to:
1. Add "Threads" intermediate segment for thread breadcrumbs
2. Add "Chats" route handling for project-less threads
3. Add document route (`/projects/:id/documents/:docId`) and breadcrumb handling
4. Convert Document Viewer from `Navigator.push` to `context.go`

**Primary recommendation:** Extend the existing `_buildBreadcrumbs` method in `breadcrumb_bar.dart` with new route cases, add document route to `main.dart`, and update navigation calls from `Navigator.push` to `context.go`.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| go_router | 17.0.1 | Declarative routing | Already in use; handles nested routes, path params, deep linking |
| provider | 6.1.5 | State for name resolution | Already in use; provides project/thread/document names |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| GoRouterState | (part of go_router) | Route state access | Use `GoRouterState.of(context)` to get current path |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| GoRouterState.of(context) | NavigatorObserver | NavigatorObserver misses `context.go()` calls; current approach is correct |
| Manual path parsing | Named routes | Named routes add complexity for simple hierarchy display |

**Installation:** No new dependencies needed.

## Architecture Patterns

### Current Project Structure (Relevant Files)
```
frontend/lib/
├── main.dart                              # Router configuration
├── widgets/
│   └── breadcrumb_bar.dart               # Breadcrumb display logic
├── screens/
│   └── documents/
│       ├── document_viewer_screen.dart   # Needs route conversion
│       └── document_list_screen.dart     # Calls Navigator.push
└── providers/
    ├── project_provider.dart             # selectedProject.name
    ├── conversation_provider.dart        # thread.title
    └── document_provider.dart            # selectedDocument.filename
```

### Pattern 1: Path-Based Breadcrumb Building
**What:** Parse URL path segments and map to display labels
**When to use:** Always - this is the established pattern in the codebase
**Example:**
```dart
// Source: Existing breadcrumb_bar.dart pattern
List<Breadcrumb> _buildBreadcrumbs(BuildContext context, String path) {
  final segments = path.split('/').where((s) => s.isNotEmpty).toList();

  // Route: /projects/:id/threads/:threadId
  if (segments.length >= 4 && segments[2] == 'threads') {
    final projectId = segments[1];
    final projectName = context.read<ProjectProvider>().selectedProject?.name ?? 'Project';
    final threadTitle = context.read<ConversationProvider>().thread?.title ?? 'Thread';

    return [
      Breadcrumb('Projects', '/projects'),
      Breadcrumb(projectName, '/projects/$projectId'),
      Breadcrumb('Threads', '/projects/$projectId'),  // NEW: intermediate segment
      Breadcrumb(threadTitle),  // Current page, no route
    ];
  }
}
```

### Pattern 2: Route Definition for Documents
**What:** Add nested route under projects for document viewing
**When to use:** For NAV-06 (Document Viewer with proper URL)
**Example:**
```dart
// Source: go_router nested routes pattern
GoRoute(
  path: ':id',
  builder: (context, state) => ProjectDetailScreen(projectId: state.pathParameters['id']!),
  routes: [
    GoRoute(
      path: 'threads/:threadId',
      builder: (context, state) => ConversationScreen(
        projectId: state.pathParameters['id']!,
        threadId: state.pathParameters['threadId']!,
      ),
    ),
    // NEW: Document viewer route
    GoRoute(
      path: 'documents/:docId',
      builder: (context, state) => DocumentViewerScreen(
        documentId: state.pathParameters['docId']!,
      ),
    ),
  ],
),
```

### Pattern 3: Navigation Update (push to go)
**What:** Replace Navigator.push with context.go for URL-reflected navigation
**When to use:** When document viewer needs URL-based routing
**Example:**
```dart
// Before (documents_column.dart line 220)
Navigator.of(context).push(
  MaterialPageRoute(
    builder: (context) => DocumentViewerScreen(documentId: documentId),
  ),
);

// After
context.go('/projects/$projectId/documents/$documentId');
```

### Anti-Patterns to Avoid
- **NavigatorObserver for breadcrumbs:** Misses `context.go()` calls per PITFALL-03; use GoRouterState instead
- **History-based breadcrumbs:** Shows back path, not hierarchy; confusing per UX research
- **Extra parameter for document data:** Lost on browser back; pass ID in path and load from provider

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Route state access | Custom route observer | `GoRouterState.of(context)` | Observer misses go() calls |
| Name resolution timing | Async name fetching in breadcrumb | Provider sync access | Provider already loaded when screen mounts |
| Mobile truncation | Custom text truncation | `maxVisible` parameter (existing) | Already implemented in BreadcrumbBar |

**Key insight:** The codebase already has the correct architecture. This phase extends existing patterns rather than introducing new ones.

## Common Pitfalls

### Pitfall 1: Project ID Not Available in Document Route
**What goes wrong:** DocumentViewerScreen currently only receives `documentId`, but breadcrumbs need `projectId` to show full path
**Why it happens:** Navigator.push doesn't preserve context; route parameters must be explicit
**How to avoid:** Include `projectId` in the route path (`/projects/:id/documents/:docId`)
**Warning signs:** Breadcrumb shows "Projects > Project" without project name

### Pitfall 2: Provider Not Loaded on Deep Link
**What goes wrong:** User deep-links to `/projects/abc/documents/xyz`, but `ProjectProvider.selectedProject` is null
**Why it happens:** Provider only loads when ProjectDetailScreen mounts
**How to avoid:** DocumentViewerScreen should trigger project load if selectedProject is null, or accept graceful degradation showing "Project" instead of name
**Warning signs:** Breadcrumb shows "Project" instead of actual name on page refresh

### Pitfall 3: Threads Tab Not Linkable
**What goes wrong:** "Threads" breadcrumb segment clicks but goes to project detail (Overview tab)
**Why it happens:** No separate route for Threads tab; it's a tab within ProjectDetailScreen
**How to avoid:** Link "Threads" segment to `/projects/:id` (same as project name) - user can click tab; OR use query param `?tab=threads`
**Warning signs:** User expects "Threads" to go to threads list but sees Overview

### Pitfall 4: Browser Back Button Unexpected Behavior
**What goes wrong:** Pressing back from document viewer goes to unexpected location
**Why it happens:** `context.go()` replaces history vs `context.push()` adds to it
**How to avoid:** Use `context.push('/projects/$projectId/documents/$docId')` for document viewer since user expects back to return to project
**Warning signs:** Back button skips project detail screen

### Pitfall 5: Document Name Flicker
**What goes wrong:** Breadcrumb shows "Document" briefly, then changes to filename
**Why it happens:** DocumentProvider.selectedDocument is null until async load completes
**How to avoid:** Accept brief "Document" display, or show skeleton; this matches existing thread behavior
**Warning signs:** Visual flicker on document view navigation

## Code Examples

Verified patterns from official sources and existing codebase:

### Example 1: Extended Breadcrumb Building for All Routes
```dart
// Source: Extension of existing breadcrumb_bar.dart pattern
List<Breadcrumb> _buildBreadcrumbs(BuildContext context, String path) {
  final breadcrumbs = <Breadcrumb>[];
  final segments = path.split('/').where((s) => s.isNotEmpty).toList();

  // /chats/:threadId -> Chats > {Thread Title}
  if (segments.isNotEmpty && segments[0] == 'chats') {
    if (segments.length == 1) {
      return [const Breadcrumb('Chats')];
    }
    if (segments.length >= 2) {
      final conversationProvider = context.read<ConversationProvider>();
      final threadTitle = conversationProvider.thread?.title ?? 'Conversation';
      return [
        const Breadcrumb('Chats', '/chats'),
        Breadcrumb(threadTitle),
      ];
    }
  }

  // /projects/:id/threads/:threadId -> Projects > {Project} > Threads > {Thread}
  if (segments.length >= 4 && segments[0] == 'projects' && segments[2] == 'threads') {
    final projectId = segments[1];
    final projectProvider = context.read<ProjectProvider>();
    final projectName = projectProvider.selectedProject?.name ?? 'Project';
    final conversationProvider = context.read<ConversationProvider>();
    final threadTitle = conversationProvider.thread?.title ?? 'Conversation';

    return [
      const Breadcrumb('Projects', '/projects'),
      Breadcrumb(projectName, '/projects/$projectId'),
      Breadcrumb('Threads', '/projects/$projectId'),  // Links to project (user clicks tab)
      Breadcrumb(threadTitle),
    ];
  }

  // /projects/:id/documents/:docId -> Projects > {Project} > Documents > {Document}
  if (segments.length >= 4 && segments[0] == 'projects' && segments[2] == 'documents') {
    final projectId = segments[1];
    final projectProvider = context.read<ProjectProvider>();
    final projectName = projectProvider.selectedProject?.name ?? 'Project';
    final documentProvider = context.read<DocumentProvider>();
    final documentName = documentProvider.selectedDocument?.filename ?? 'Document';

    return [
      const Breadcrumb('Projects', '/projects'),
      Breadcrumb(projectName, '/projects/$projectId'),
      Breadcrumb('Documents', '/projects/$projectId'),  // Links to project (user clicks tab)
      Breadcrumb(documentName),
    ];
  }

  // ... existing handlers for /projects, /projects/:id, etc.
}
```

### Example 2: Document Route Definition
```dart
// Source: go_router documentation + existing main.dart pattern
// Add to StatefulShellBranch for Projects, under :id routes
GoRoute(
  path: ':id',
  builder: (context, state) {
    final id = state.pathParameters['id']!;
    return ProjectDetailScreen(projectId: id);
  },
  routes: [
    // Existing thread route
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
    // NEW: Document viewer route
    GoRoute(
      path: 'documents/:docId',
      builder: (context, state) {
        final docId = state.pathParameters['docId']!;
        return DocumentViewerScreen(documentId: docId);
      },
    ),
  ],
),
```

### Example 3: Updated Document Navigation
```dart
// Source: go_router context.push pattern
// In documents_column.dart _onView method
void _onView(BuildContext context, String documentId) {
  // Use push to add to history (back button returns to project)
  context.push('/projects/$projectId/documents/$documentId');
}

// In document_list_screen.dart ListTile onTap
onTap: () {
  context.push('/projects/${widget.projectId}/documents/${doc.id}');
},
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Navigator.push for modals | GoRouter routes with paths | go_router 6.0+ | Enables deep linking, URL reflection |
| NavigatorObserver | GoRouterState.of(context) | go_router adoption | Correctly captures go() calls |
| Path-only breadcrumbs | Name-resolved breadcrumbs | Custom implementation | Better UX with readable names |

**Deprecated/outdated:**
- `state.queryParams` deprecated in favor of `state.uri.queryParameters` (go_router 10.0+)
- `state.params` deprecated in favor of `state.pathParameters` (go_router 10.0+)

## Open Questions

Things that couldn't be fully resolved:

1. **"Threads" and "Documents" intermediate segment navigation**
   - What we know: No separate route exists for project tabs
   - What's unclear: Should these link to project with tab query param, or just to project?
   - Recommendation: Link to `/projects/:id` - user can then click the appropriate tab. Adding `?tab=threads` would require ProjectDetailScreen changes.

2. **Project load on document deep link**
   - What we know: DocumentViewerScreen loads document via DocumentProvider
   - What's unclear: Should it also trigger ProjectProvider.selectProject for breadcrumb name?
   - Recommendation: Accept graceful degradation ("Project" shown briefly). Alternative: add projectId to DocumentViewerScreen and load project in initState.

## Sources

### Primary (HIGH confidence)
- [go_router pub.dev](https://pub.dev/packages/go_router) - v17.1.0 documentation, nested routes, path parameters
- [GoRouterState class](https://pub.dev/documentation/go_router/latest/go_router/GoRouterState-class.html) - uri, pathParameters, of() method
- Existing codebase: `breadcrumb_bar.dart`, `main.dart`, `document_viewer_screen.dart`

### Secondary (MEDIUM confidence)
- [go_router breadcrumb GitHub issue](https://github.com/flutter/flutter/issues/99118) - Confirms GoRouterState approach is standard
- [Flutter go_router guide (Medium)](https://medium.com/@vimehraa29/flutter-go-router-the-crucial-guide-41dc615045bb) - Nested routes pattern

### Research Summary (HIGH confidence)
- `.planning/research/SUMMARY_v1.9.3.md` - Confirms architecture approach, pitfalls already documented

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - go_router 17.0.1 already in use, patterns verified
- Architecture: HIGH - Extending existing `_buildBreadcrumbs` method, same pattern
- Pitfalls: HIGH - Based on existing codebase analysis and documented v1.9.3 research

**Research date:** 2026-02-04
**Valid until:** 30 days (stable stack, no expected breaking changes)
