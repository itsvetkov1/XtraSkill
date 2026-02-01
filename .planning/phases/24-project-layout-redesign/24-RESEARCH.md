# Phase 24: project-layout-redesign - Research

**Researched:** 2026-02-01
**Domain:** Flutter layout, collapsible panels, state management
**Confidence:** HIGH

## Summary

This phase transforms the project detail screen from a tab-based layout (Documents/Threads tabs) to a threads-first layout with documents in a collapsible side column. The current implementation uses `TabController` with `TabBarView` to switch between Documents and Threads views. The new layout will show threads directly (no tab switching) with documents accessible via a thin expandable strip on the left edge.

The codebase already has excellent patterns for this work: `NavigationProvider` demonstrates collapsible sidebar state management with SharedPreferences persistence, and `AnimatedSize`/`AnimatedContainer` from Flutter SDK provide smooth expand/collapse animations without package dependencies.

**Primary recommendation:** Build a custom `DocumentsColumn` widget using `AnimatedSize` for smooth width transitions, with a dedicated `DocumentColumnProvider` (following `NavigationProvider` pattern) for session-scoped state.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flutter/widgets | SDK | AnimatedSize, AnimatedContainer | Built-in, no dependencies, works everywhere |
| provider | ^6.x | State management | Already used throughout codebase |
| shared_preferences | ^2.x | Persistent storage | Already integrated for theme/nav |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| go_router | ^14.x | Navigation | Already integrated, used for document viewer |
| skeletonizer | ^1.x | Loading states | Already used in document/thread lists |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AnimatedSize | flutter_resizable_container | Overkill - user draggable resize not needed |
| AnimatedSize | collapsible_sidebar package | External dependency for simple use case |
| Custom column | ExpansionPanel | Wrong use case - designed for list items, not layout columns |

**Installation:**
No new dependencies required. All tools already in project.

## Architecture Patterns

### Recommended Project Structure
```
lib/
├── providers/
│   └── document_column_provider.dart    # NEW: Column expanded/collapsed state
├── screens/projects/
│   └── project_detail_screen.dart       # MODIFIED: Remove tabs, add column layout
└── widgets/
    └── documents_column.dart            # NEW: Collapsible documents column widget
```

### Pattern 1: Collapsible Column with AnimatedSize
**What:** A column that smoothly transitions between collapsed (narrow strip with icon) and expanded (full document list) states.
**When to use:** Side panels that toggle between states without user drag-resize.
**Example:**
```dart
// Source: Flutter SDK AnimatedSize documentation
class DocumentsColumn extends StatelessWidget {
  final bool isExpanded;
  final VoidCallback onToggle;
  final String projectId;

  const DocumentsColumn({
    required this.isExpanded,
    required this.onToggle,
    required this.projectId,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedSize(
      duration: const Duration(milliseconds: 200),
      curve: Curves.easeInOut,
      alignment: Alignment.centerLeft,  // Expand from left edge
      child: SizedBox(
        width: isExpanded ? 280 : 48,   // 48px for icon strip, 280px expanded
        child: isExpanded
            ? _ExpandedContent(projectId: projectId, onCollapse: onToggle)
            : _CollapsedStrip(onExpand: onToggle),
      ),
    );
  }
}
```

### Pattern 2: Session-Scoped Provider (Not Persistent)
**What:** State that persists within app session but not across restarts.
**When to use:** Column state (requirement says "within session", not across restarts).
**Example:**
```dart
// Simpler than NavigationProvider - no SharedPreferences needed
class DocumentColumnProvider extends ChangeNotifier {
  bool _isExpanded = false;  // Default: collapsed (LAYOUT-03)

  bool get isExpanded => _isExpanded;

  void toggle() {
    _isExpanded = !_isExpanded;
    notifyListeners();
  }

  void expand() {
    if (!_isExpanded) {
      _isExpanded = true;
      notifyListeners();
    }
  }

  void collapse() {
    if (_isExpanded) {
      _isExpanded = false;
      notifyListeners();
    }
  }
}
```

### Pattern 3: Row-Based Layout Replacing TabBarView
**What:** Replace tab-based content switching with horizontal Row layout.
**When to use:** When showing multiple content areas simultaneously.
**Example:**
```dart
// Current: TabBarView switches between Documents and Threads
// New: Row shows both simultaneously
Widget build(BuildContext context) {
  return Column(
    children: [
      // Project header (keep existing)
      _ProjectHeader(project: project),

      // Main content area: Documents column + Threads list
      Expanded(
        child: Row(
          children: [
            // Collapsible documents column
            Consumer<DocumentColumnProvider>(
              builder: (context, columnProvider, _) {
                return DocumentsColumn(
                  isExpanded: columnProvider.isExpanded,
                  onToggle: columnProvider.toggle,
                  projectId: projectId,
                );
              },
            ),

            // Vertical divider
            const VerticalDivider(width: 1, thickness: 1),

            // Threads list (always visible, primary content)
            Expanded(
              child: ThreadListScreen(projectId: projectId),
            ),
          ],
        ),
      ),
    ],
  );
}
```

### Anti-Patterns to Avoid
- **Using Navigator.push for documents from column:** Current document viewer uses Navigator.push which leaves the column context. Consider inline viewing or go_router navigation that preserves layout.
- **Persisting column state across app restarts:** Requirement says "within session" - don't add SharedPreferences for this.
- **Making column resizable by dragging:** Requirement is click-to-expand, not drag-to-resize. Don't overcomplicate.
- **Animating with explicit AnimationController:** Use implicit animations (AnimatedSize, AnimatedContainer) for simpler code.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Smooth width animation | Manual AnimationController | AnimatedSize | Handles curve, duration, rebuild automatically |
| State management | Custom setState callbacks | Provider + ChangeNotifier | Already used, consistent pattern |
| Document list display | Custom ListView | Existing _DocumentsTab pattern | Reuse with minimal modification |
| Loading skeletons | Custom shimmer effect | Skeletonizer | Already integrated, consistent UX |

**Key insight:** The hardest part of this phase is layout surgery (removing TabBar, restructuring widgets) not new widget development. Most building blocks exist.

## Common Pitfalls

### Pitfall 1: TabController Disposal Order
**What goes wrong:** Removing TabController without proper cleanup causes disposed controller errors.
**Why it happens:** TabController is tied to TickerProviderStateMixin, disposal order matters.
**How to avoid:** Remove `with SingleTickerProviderStateMixin` when removing TabController. Clean removal order: dispose controller in dispose(), then remove mixin.
**Warning signs:** "A TabController was used after being disposed" errors.

### Pitfall 2: Nested Scaffold Conflicts
**What goes wrong:** Current ThreadListScreen has its own Scaffold with FAB. Nesting may cause multiple FABs.
**Why it happens:** Each Scaffold manages its own FAB position independently.
**How to avoid:** Either lift FAB to parent, or ensure only one Scaffold in the view hierarchy. Current ThreadListScreen FAB is appropriate for threads - may need to add upload FAB handling for documents column.
**Warning signs:** FABs overlapping, FAB in wrong position.

### Pitfall 3: DocumentProvider vs ProjectProvider Documents
**What goes wrong:** Project detail shows documents from ProjectProvider.selectedProject.documents, but DocumentListScreen uses DocumentProvider.
**Why it happens:** Two different data sources for the same data.
**How to avoid:** Decide which provider owns document state in this context. Currently `_DocumentsTab` uses `ProjectProvider`, so new column should too for consistency. May need to call `DocumentProvider.loadDocuments()` if CRUD operations needed.
**Warning signs:** Stale document list after upload, documents not appearing after navigation.

### Pitfall 4: Column Width on Different Screen Sizes
**What goes wrong:** Fixed 280px expanded width looks wrong on mobile.
**Why it happens:** Not considering responsive breakpoints.
**How to avoid:** This feature may only make sense on desktop/tablet. On mobile, could either: (a) hide column entirely and use drawer, or (b) expand to full width modal. Check `ResponsiveHelper.isMobile(context)`.
**Warning signs:** Column takes too much space on small screens, unusable on phones.

### Pitfall 5: Document Viewer Navigation
**What goes wrong:** Clicking a document in the column navigates away from project view entirely.
**Why it happens:** Current implementation uses `Navigator.push(DocumentViewerScreen)`.
**How to avoid:** Options: (a) Keep push behavior (user can back-navigate), (b) Use go_router path like `/projects/:id/documents/:docId`, (c) Show document in inline panel. Option (a) is simplest for MVP.
**Warning signs:** User confusion about where they are after viewing document.

## Code Examples

Verified patterns from existing codebase:

### NavigationProvider Pattern (Session State)
```dart
// Source: lib/providers/navigation_provider.dart
// Existing pattern for sidebar toggle - adapt for document column
class NavigationProvider extends ChangeNotifier {
  bool _isSidebarExpanded;

  bool get isSidebarExpanded => _isSidebarExpanded;

  Future<void> toggleSidebar() async {
    _isSidebarExpanded = !_isSidebarExpanded;
    // Persistence logic...
    notifyListeners();
  }
}
```

### ResponsiveScaffold Row Layout
```dart
// Source: lib/widgets/responsive_scaffold.dart lines 141-203
// Existing pattern for sidebar + main content layout
Scaffold(
  body: Row(
    children: [
      NavigationRail(...),  // Side content
      const VerticalDivider(thickness: 1, width: 1),
      Expanded(
        child: Column(
          children: [
            _DesktopHeaderBar(),  // Header
            Expanded(child: child),  // Main content
          ],
        ),
      ),
    ],
  ),
);
```

### Current Tab Implementation (To Be Replaced)
```dart
// Source: lib/screens/projects/project_detail_screen.dart lines 172-196
// Current implementation - understand before replacing
TabBar(
  controller: _tabController,
  tabs: const [
    Tab(text: 'Documents', icon: Icon(Icons.description)),
    Tab(text: 'Threads', icon: Icon(Icons.chat)),
  ],
),
Expanded(
  child: TabBarView(
    controller: _tabController,
    children: [
      _DocumentsTab(projectId: widget.projectId),
      ThreadListScreen(projectId: widget.projectId),
    ],
  ),
),
```

### Document List Pattern (Reuse)
```dart
// Source: lib/screens/projects/project_detail_screen.dart lines 338-353
// Existing document list - reuse for column content
ListView.builder(
  padding: const EdgeInsets.all(16),
  itemCount: project.documents!.length,
  itemBuilder: (context, index) {
    final doc = project.documents![index];
    return ListTile(
      leading: const Icon(Icons.description),
      title: Text(doc['filename'] ?? 'Unknown'),
      subtitle: Text('Uploaded: ${doc['created_at'] ?? ''}'),
    );
  },
);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TabBar for context switching | Row layout with always-visible content | This phase | Reduces clicks, faster workflow |
| Navigator.push for modals | go_router for declarative navigation | Flutter 2.0+ era | Better deep linking, consistent with codebase |
| Manual AnimationController | Implicit animations (AnimatedSize) | Long established | Simpler code, fewer bugs |

**Deprecated/outdated:**
- ExpansionPanelList: Still works but designed for list items, not layout panels
- Drawer-based document access: Would hide documents behind hamburger menu, slower access

## Open Questions

Things that couldn't be fully resolved:

1. **Mobile Layout Strategy**
   - What we know: Column-based layout works well on desktop/tablet (>=600px)
   - What's unclear: Should mobile show column, use drawer, or hide entirely?
   - Recommendation: Keep column on tablet+, hide on mobile (documents accessible via different route)

2. **Document Upload from Column**
   - What we know: Current upload uses Navigator.push to DocumentUploadScreen
   - What's unclear: Should upload button be in column header, FAB, or both?
   - Recommendation: Add upload IconButton in column header when expanded, consistent with current pattern

3. **Document Delete from Column**
   - What we know: DocumentListScreen has PopupMenu with delete option
   - What's unclear: Should column support inline delete or require full screen?
   - Recommendation: Support delete from column - reuse existing DeleteConfirmationDialog and DocumentProvider.deleteDocument patterns

## Sources

### Primary (HIGH confidence)
- **Codebase Analysis:**
  - `lib/screens/projects/project_detail_screen.dart` - Current tab implementation
  - `lib/providers/navigation_provider.dart` - Collapsible sidebar pattern with persistence
  - `lib/widgets/responsive_scaffold.dart` - Row-based layout with sidebar
  - `lib/screens/documents/document_list_screen.dart` - Full document list features
  - `lib/screens/threads/thread_list_screen.dart` - Threads list implementation
- **Flutter SDK Documentation:**
  - [AnimatedSize class](https://api.flutter.dev/flutter/widgets/AnimatedSize-class.html) - Official widget docs
  - [AnimatedContainer class](https://api.flutter.dev/flutter/widgets/AnimatedContainer-class.html) - Official widget docs

### Secondary (MEDIUM confidence)
- [Animated Responsive Collapsible Menus in Flutter](https://medium.com/flutter-community/animated-responsive-collapsible-menus-in-flutter-ea17e99d1ac3) - Pattern validation
- [Flutter Gems - Sidebar packages](https://fluttergems.dev/drawer/) - Alternative packages (not recommended)

### Tertiary (LOW confidence)
- None - all findings verified with primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools already in codebase
- Architecture: HIGH - Patterns extracted from existing code
- Pitfalls: HIGH - Based on actual codebase analysis

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (stable patterns, low change risk)
