---
phase: 07
plan: 02
subsystem: navigation
tags: [gorouter, statefulshellroute, responsive, navigation, flutter]

dependency-graph:
  requires: ["07-01"]
  provides: ["StatefulShellRoute-integration", "navigation-shell"]
  affects: ["07-03"]

tech-stack:
  added: []
  patterns: ["StatefulShellRoute.indexedStack", "path-based-index-derivation"]

key-files:
  created: []
  modified:
    - frontend/lib/main.dart

decisions:
  - name: "Path-based index derivation"
    choice: "Use state.uri.path instead of navigationShell.currentIndex"
    rationale: "Ensures nested routes (e.g., /projects/:id) highlight correct parent item"

metrics:
  duration: "3 minutes"
  completed: "2026-01-29"
---

# Phase 7 Plan 02: GoRouter Integration Summary

**One-liner:** StatefulShellRoute.indexedStack wraps authenticated routes with ResponsiveScaffold shell for persistent navigation.

## What Was Built

### Task 1: Add NavigationProvider to main.dart initialization
- Added import for `NavigationProvider`
- Load `NavigationProvider` alongside `ThemeProvider` in `main()` using async `load()` factory
- Updated `MyApp` constructor to accept `NavigationProvider` as required parameter
- Added `NavigationProvider` to `MultiProvider` using `ChangeNotifierProvider.value()` (same pattern as ThemeProvider to avoid recreation on rebuild)

**Commit:** c7e0a33

### Task 2: Refactor GoRouter to use StatefulShellRoute.indexedStack
- Added import for `ResponsiveScaffold` widget
- Created `_getSelectedIndex(String path)` helper function for path-based navigation highlighting
- Wrapped authenticated routes (`/home`, `/projects`, `/projects/:id`, `/settings`) in `StatefulShellRoute.indexedStack`
- Configured 3 branches:
  - Branch 0: Home (`/home`)
  - Branch 1: Projects (`/projects` with nested `:id` route)
  - Branch 2: Settings (`/settings`)
- Unauthenticated routes (`/splash`, `/login`, `/auth/callback`) remain outside shell
- Used `state.uri.path` (not `navigationShell.currentIndex`) for nested route highlighting

**Commit:** 43a3719

### Task 3: Diagnose nested Scaffold conflicts
- **Finding:** All three screens (HomeScreen, ProjectListScreen, SettingsScreen) have their own Scaffolds
- **Impact:** Mobile viewport will show double AppBars (ResponsiveScaffold + screen-level Scaffold)
- **Resolution:** Deferred to Plan 07-03 (Screen Refactoring) as planned

## Key Links Established

| From | To | Via | Pattern |
|------|-----|-----|---------|
| main.dart | ResponsiveScaffold | StatefulShellRoute builder | `ResponsiveScaffold(child: navigationShell)` |
| main.dart | NavigationProvider | MultiProvider | `ChangeNotifierProvider.value(value: navigationProvider)` |
| StatefulShellRoute | Branch navigation | goBranch callback | `navigationShell.goBranch(index)` |
| Navigation highlighting | Path | Helper function | `_getSelectedIndex(state.uri.path)` |

## Decisions Made

### 1. Path-based Index Derivation
**Decision:** Use `state.uri.path` with helper function instead of `navigationShell.currentIndex`

**Rationale:** The `navigationShell.currentIndex` only reflects the active branch index, not the actual route within that branch. When user navigates to `/projects/abc-123`, using `currentIndex` would show 1 (correct), but if we relied on branch index alone for more complex scenarios, we'd lose context. The path-based approach:
- Handles nested routes correctly (e.g., `/projects/:id` highlights Projects)
- Is explicit and testable
- Matches the pattern recommended in go_router documentation

**Alternatives considered:**
- Using only `navigationShell.currentIndex` - simpler but doesn't support future sub-navigation highlighting
- Using GoRouterState.of(context) in child widgets - adds coupling

## Deviations from Plan

None - plan executed exactly as written.

## Known Issues for Plan 03

### Nested Scaffold Conflicts (Expected)

**Issue:** All authenticated screens have their own Scaffolds, causing nested Scaffold structure:
```
ResponsiveScaffold (has Scaffold)
  -> HomeScreen/_MobileLayout (has Scaffold with AppBar)
```

**Visual Impact:**
- Mobile: Double AppBars visible
- Desktop: Nested Scaffolds (less visible but still redundant)

**Resolution:** Plan 07-03 will:
1. Refactor HomeScreen to export content-only widget
2. Remove Scaffold from ProjectListScreen
3. Remove Scaffold from SettingsScreen
4. Have all screens rely on ResponsiveScaffold for navigation chrome

## Verification Results

| Check | Status |
|-------|--------|
| `flutter analyze main.dart` | Pass (4 info-level warnings only) |
| main.dart >= 150 lines | Pass (262 lines) |
| NavigationProvider in MultiProvider | Pass |
| StatefulShellRoute wrapping authenticated routes | Pass |
| Unauthenticated routes outside shell | Pass |
| Auth redirect logic unchanged | Pass |

## Files Modified

### frontend/lib/main.dart (262 lines)
- **Lines 15:** Added NavigationProvider import
- **Lines 25:** Added ResponsiveScaffold import
- **Lines 30-33:** Load both ThemeProvider and NavigationProvider in main()
- **Lines 68-72:** Updated runApp to pass navigationProvider
- **Lines 75-83:** Updated MyApp constructor with navigationProvider parameter
- **Lines 97-98:** Added NavigationProvider to MultiProvider
- **Lines 130-138:** Added `_getSelectedIndex()` helper function
- **Lines 199-257:** StatefulShellRoute.indexedStack configuration with 3 branches

## Next Phase Readiness

### Ready for Plan 07-03
- StatefulShellRoute is integrated and working
- ResponsiveScaffold receives navigation events correctly
- Screens can be refactored to content-only widgets

### Blockers
None

### Concerns
- Nested Scaffold issue is visual-only, not functional
- User testing should wait until Plan 03 completes screen refactoring
