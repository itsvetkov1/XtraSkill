# Phase 27: thread-search-filter - Research

**Researched:** 2026-02-02
**Domain:** Flutter client-side filtering, Material 3 SearchBar
**Confidence:** HIGH

## Summary

Phase 27 implements search and sort functionality for thread lists. This is a client-side filtering feature that operates on already-loaded thread data, requiring no backend changes. The codebase uses the Provider pattern (ChangeNotifier) for state management, and threads are displayed in two locations: `ChatsScreen` (global chats) and `ThreadListScreen` (project threads).

The implementation will add local filter/sort state to the existing providers, use Flutter's Material 3 `SearchBar` widget for the search UI, and implement `SegmentedButton` or `DropdownButton` for sort options. The pattern follows standard Flutter list filtering: maintain a separate filtered list derived from the source list, update on search/sort changes.

**Primary recommendation:** Add search/sort state to `ChatsProvider` with computed `filteredThreads` getter; use Material 3 `SearchBar` with `TextField` semantics and `SegmentedButton` for sort options.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flutter Material | 3.x | SearchBar, SegmentedButton widgets | Built-in M3 components |
| Provider | (existing) | State management | Already used throughout app |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| collection | (Dart stdlib) | List sorting with `sort()` | Sorting by multiple criteria |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SearchBar | TextField with decoration | SearchBar has built-in M3 styling, better accessibility |
| SegmentedButton | DropdownButton | SegmentedButton shows all options at once, better for 3 options |
| SegmentedButton | ChoiceChips | SegmentedButton is more compact, standard for exclusive selection |

**Installation:**
No new dependencies required - all components available in Flutter Material.

## Architecture Patterns

### Recommended Approach

The filter/sort logic should be added to existing providers with computed filtered lists:

```
lib/
├── providers/
│   ├── chats_provider.dart     # Add: searchQuery, sortOption, filteredThreads
│   └── thread_provider.dart    # Add: searchQuery, sortOption, filteredThreads
├── screens/
│   ├── chats_screen.dart       # Add: SearchBar header, sort selector
│   └── threads/
│       └── thread_list_screen.dart  # Add: SearchBar, sort selector
└── models/
    └── thread_sort.dart        # NEW: SortOption enum
```

### Pattern 1: Filter State in Provider

**What:** Add search/sort state to provider, compute filtered list on-the-fly
**When to use:** Client-side filtering of small-medium lists (<1000 items)
**Example:**
```dart
// In ChatsProvider
class ChatsProvider extends ChangeNotifier {
  List<Thread> _threads = [];
  String _searchQuery = '';
  ThreadSortOption _sortOption = ThreadSortOption.newest;

  String get searchQuery => _searchQuery;
  ThreadSortOption get sortOption => _sortOption;

  /// Filtered and sorted threads based on current search/sort state
  List<Thread> get filteredThreads {
    var result = _threads.where((thread) {
      if (_searchQuery.isEmpty) return true;
      final title = thread.title?.toLowerCase() ?? '';
      return title.contains(_searchQuery.toLowerCase());
    }).toList();

    switch (_sortOption) {
      case ThreadSortOption.newest:
        result.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      case ThreadSortOption.oldest:
        result.sort((a, b) => a.updatedAt.compareTo(b.updatedAt));
      case ThreadSortOption.alphabetical:
        result.sort((a, b) =>
          (a.title ?? '').toLowerCase().compareTo((b.title ?? '').toLowerCase()));
    }
    return result;
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  void setSortOption(ThreadSortOption option) {
    _sortOption = option;
    notifyListeners();
  }

  void clearSearch() {
    _searchQuery = '';
    notifyListeners();
  }
}
```

### Pattern 2: Sort Option Enum

**What:** Type-safe enum for sort options with display labels
**When to use:** When you have a fixed set of sort options
**Example:**
```dart
// lib/models/thread_sort.dart
enum ThreadSortOption {
  newest('Newest'),
  oldest('Oldest'),
  alphabetical('A-Z');

  final String label;
  const ThreadSortOption(this.label);
}
```

### Pattern 3: Material 3 SearchBar in Header

**What:** SearchBar widget with clear button and leading icon
**When to use:** List screens needing inline search
**Example:**
```dart
// In screen build method
SearchBar(
  hintText: 'Search chats...',
  controller: _searchController,
  leading: const Icon(Icons.search),
  trailing: [
    if (_searchController.text.isNotEmpty)
      IconButton(
        icon: const Icon(Icons.clear),
        onPressed: () {
          _searchController.clear();
          provider.clearSearch();
        },
      ),
  ],
  onChanged: (value) => provider.setSearchQuery(value),
),
```

### Pattern 4: SegmentedButton for Sort

**What:** Material 3 segmented button for exclusive sort selection
**When to use:** 2-4 sort options that fit horizontally
**Example:**
```dart
SegmentedButton<ThreadSortOption>(
  segments: ThreadSortOption.values.map((option) =>
    ButtonSegment(
      value: option,
      label: Text(option.label),
    ),
  ).toList(),
  selected: {provider.sortOption},
  onSelectionChanged: (selected) {
    provider.setSortOption(selected.first);
  },
),
```

### Anti-Patterns to Avoid
- **Filtering in UI layer:** Don't filter in `build()` - do it in provider for testability
- **Creating new lists on every build:** Use computed getter, but don't store filtered list separately unless caching is needed
- **Ignoring case sensitivity:** Always use `.toLowerCase()` for search comparison
- **Forgetting null titles:** Threads can have `title: null`, must handle with `?? ''`

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Search input UI | Custom TextField | Material `SearchBar` | Built-in M3 styling, accessibility, clear button support |
| Exclusive option selection | Custom radio buttons | `SegmentedButton` | Standard M3 component, consistent styling |
| Case-insensitive search | Manual normalization | `toLowerCase()` | Dart standard, handles Unicode correctly |

**Key insight:** Flutter's Material 3 components handle accessibility, theming, and interaction states automatically. Custom implementations miss edge cases.

## Common Pitfalls

### Pitfall 1: Search Persists After Navigation
**What goes wrong:** User searches, navigates away, returns - search state is lost
**Why it happens:** Search state is in widget state, not provider
**How to avoid:** Store search query in provider, not local `TextEditingController`
**Warning signs:** Search clears when switching tabs

### Pitfall 2: Null Title Handling
**What goes wrong:** App crashes or shows wrong results when thread.title is null
**Why it happens:** Threads can be created without titles ("New Chat")
**How to avoid:** Always use `thread.title ?? ''` or `thread.title ?? 'New Chat'` for comparisons
**Warning signs:** Null pointer exceptions in filter logic

### Pitfall 3: Sort Not Respecting Current Sort on Load
**What goes wrong:** Newly loaded data ignores user's selected sort
**Why it happens:** Backend returns newest-first, UI shows newest-first even if user selected "Oldest"
**How to avoid:** Always apply sort in `filteredThreads` getter, not just on user action
**Warning signs:** Data jumps around after refresh

### Pitfall 4: Empty State Not Updated
**What goes wrong:** Empty state says "No chats yet" when there ARE chats but none match search
**Why it happens:** Using original empty state for both "no data" and "no matches"
**How to avoid:** Check both conditions: `threads.isEmpty` vs `filteredThreads.isEmpty && searchQuery.isNotEmpty`
**Warning signs:** Confusing "Create new" prompt when searching

### Pitfall 5: Performance with Large Lists
**What goes wrong:** UI stutters when typing in search
**Why it happens:** Filtering runs on every keystroke
**How to avoid:** For large lists (>500), consider debouncing search input
**Warning signs:** Lag between typing and results appearing

## Code Examples

Verified patterns from official sources and codebase conventions:

### Empty State for No Search Results
```dart
// Based on existing EmptyState widget pattern
if (provider.filteredThreads.isEmpty) {
  if (provider.searchQuery.isNotEmpty) {
    // Search returned no results
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off, size: 64,
               color: Theme.of(context).colorScheme.outline),
          const SizedBox(height: 16),
          Text(
            "No threads matching '${provider.searchQuery}'",
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => provider.clearSearch(),
            child: const Text('Clear search'),
          ),
        ],
      ),
    );
  } else {
    // Actually no threads
    return EmptyState(
      icon: Icons.chat_bubble_outline,
      title: 'No chats yet',
      message: 'Start a new conversation',
      buttonLabel: 'New Chat',
      onPressed: _createNewChat,
    );
  }
}
```

### Search Header Row Layout
```dart
// Consistent with app's Padding(16) pattern
Padding(
  padding: const EdgeInsets.all(16.0),
  child: Column(
    children: [
      // Title row with New Chat button
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text('Chats', style: Theme.of(context).textTheme.headlineMedium),
          FilledButton.icon(
            onPressed: _createNewChat,
            icon: const Icon(Icons.add),
            label: const Text('New Chat'),
          ),
        ],
      ),
      const SizedBox(height: 12),
      // Search bar
      SearchBar(
        hintText: 'Search chats...',
        controller: _searchController,
        leading: const Icon(Icons.search),
        trailing: [
          if (_searchController.text.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear),
              onPressed: _clearSearch,
            ),
        ],
        onChanged: (value) => context.read<ChatsProvider>().setSearchQuery(value),
      ),
      const SizedBox(height: 8),
      // Sort selector
      SegmentedButton<ThreadSortOption>(
        segments: ThreadSortOption.values.map((option) =>
          ButtonSegment(value: option, label: Text(option.label)),
        ).toList(),
        selected: {provider.sortOption},
        onSelectionChanged: (selected) {
          context.read<ChatsProvider>().setSortOption(selected.first);
        },
      ),
    ],
  ),
),
```

### Syncing TextEditingController with Provider
```dart
class _ChatsScreenState extends State<ChatsScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Restore search query from provider on init
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final query = context.read<ChatsProvider>().searchQuery;
      if (query.isNotEmpty) {
        _searchController.text = query;
      }
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _clearSearch() {
    _searchController.clear();
    context.read<ChatsProvider>().clearSearch();
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TextField with InputDecoration.search | Material 3 SearchBar | Flutter 3.7 | Built-in M3 styling |
| RadioListTile for options | SegmentedButton | Flutter 3.0 | More compact, M3 native |
| Manual filter/sort in widget | Computed getter in Provider | Always best practice | Testability, performance |

**Deprecated/outdated:**
- `SearchDelegate`: Old pattern requiring `showSearch()` navigation, replaced by `SearchAnchor` for full-page search or inline `SearchBar` for embedded search

## Open Questions

Things that couldn't be fully resolved:

1. **ThreadListScreen vs ChatsScreen consistency**
   - What we know: Both screens display threads, both need search/filter
   - What's unclear: Should they share a single widget or have separate implementations?
   - Recommendation: Implement in ChatsScreen first, then mirror pattern in ThreadListScreen

2. **Sort persistence across sessions**
   - What we know: Requirements say "search persists until cleared" (SEARCH-03)
   - What's unclear: Should sort preference also persist? (not mentioned in requirements)
   - Recommendation: Keep sort in memory only (not persisted), default to Newest

## Codebase Analysis

### Existing Thread Display Locations

1. **ChatsScreen** (`lib/screens/chats_screen.dart`)
   - Uses `ChatsProvider` for state
   - Displays all user threads (global listing)
   - Has header with "New Chat" button
   - Uses `RefreshIndicator` and `ListView.builder`
   - This is the PRIMARY target for search/filter

2. **ThreadListScreen** (`lib/screens/threads/thread_list_screen.dart`)
   - Uses `ThreadProvider` for state
   - Displays threads within a specific project
   - Has FAB for "New Conversation"
   - Uses `Skeletonizer` for loading states
   - SECONDARY target (same pattern, different provider)

### Thread Model Structure
```dart
class Thread {
  final String id;
  final String? projectId;
  final String? projectName;
  final String? title;        // Nullable - used for search
  final DateTime createdAt;
  final DateTime updatedAt;   // Used for sorting
  final DateTime? lastActivityAt;
  final int? messageCount;
  // ...
}
```

Fields available for filtering/sorting:
- `title` - Search target (nullable, use `?? ''`)
- `updatedAt` - Primary sort field for Newest/Oldest
- `createdAt` - Could use, but `updatedAt` better reflects activity
- `title` - Alphabetical sort (nullable handling required)

### Provider Pattern
Both `ChatsProvider` and `ThreadProvider` extend `ChangeNotifier` and follow the same patterns:
- `List<Thread> _threads` - source data
- `bool _isLoading` - loading state
- `String? _error` - error state
- `notifyListeners()` - trigger rebuilds

## Files to Modify

| File | Changes |
|------|---------|
| `lib/models/thread_sort.dart` | **NEW** - ThreadSortOption enum |
| `lib/providers/chats_provider.dart` | Add searchQuery, sortOption, filteredThreads getter, setters |
| `lib/screens/chats_screen.dart` | Add SearchBar, SegmentedButton, update to use filteredThreads |
| `lib/providers/thread_provider.dart` | Add searchQuery, sortOption, filteredThreads getter, setters |
| `lib/screens/threads/thread_list_screen.dart` | Add SearchBar, SegmentedButton, update to use filteredThreads |

## Risks/Considerations

1. **UI Real Estate:** Adding search bar + sort selector takes vertical space. On small screens, consider collapsible search.

2. **Provider Sync:** TextEditingController needs to stay in sync with provider state (for persistence across navigation).

3. **Empty State Differentiation:** Must distinguish "no threads at all" from "no threads match search" to show appropriate message per SEARCH-04.

4. **Testing:** Filter/sort logic in provider makes it unit-testable without widget tests.

## Sources

### Primary (HIGH confidence)
- Flutter Material SearchBar API: https://api.flutter.dev/flutter/material/SearchBar-class.html
- Codebase files: `chats_provider.dart`, `chats_screen.dart`, `thread_provider.dart`, `thread_list_screen.dart`, `thread.dart`

### Secondary (MEDIUM confidence)
- Flutter Material 3 SearchBar patterns: https://maneesha-erandi.medium.com/flutter-ui-essentials-material-3-searchbar-6c1acc540a2
- Flutter list filtering: https://www.kindacode.com/article/how-to-create-a-filter-search-listview-in-flutter

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using Flutter built-in Material 3 widgets
- Architecture: HIGH - Follows existing Provider patterns in codebase
- Pitfalls: HIGH - Common Flutter patterns, verified against codebase

**Research date:** 2026-02-02
**Valid until:** 60 days (stable Flutter patterns, no fast-moving dependencies)
