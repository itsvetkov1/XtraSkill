---
phase: 07
plan: 03
subsystem: navigation
tags: [breadcrumbs, back-button, refactoring, responsive, navigation, flutter]

dependency-graph:
  requires: ["07-02"]
  provides: ["breadcrumb-navigation", "contextual-back", "screen-refactoring"]
  affects: ["08"]

tech-stack:
  added: []
  patterns: ["content-only-screens", "shell-provided-navigation"]

key-files:
  created:
    - frontend/lib/widgets/breadcrumb_bar.dart
    - frontend/lib/widgets/contextual_back_button.dart
  modified:
    - frontend/lib/widgets/responsive_scaffold.dart
    - frontend/lib/screens/home_screen.dart
    - frontend/lib/screens/settings_screen.dart
    - frontend/lib/screens/projects/project_list_screen.dart
    - frontend/lib/screens/projects/project_detail_screen.dart
    - frontend/test/widget_test.dart

decisions:
  - name: "Shell-provided navigation"
    choice: "All screens are content-only, ResponsiveScaffold provides all navigation UI"
    rationale: "Single source of truth for AppBar, breadcrumbs, back buttons prevents duplication"
  - name: "Mobile breadcrumb truncation"
    choice: "maxVisible: 2 for mobile, show last 2 segments with '...' prefix"
    rationale: "Mobile screens have limited horizontal space"

metrics:
  duration: "8 minutes"
  completed: "2026-01-29"
---

# Phase 7 Plan 03: Breadcrumb Navigation & Screen Refactoring Summary

**One-liner:** BreadcrumbBar and ContextualBackButton widgets plus content-only screen refactoring eliminates nested Scaffolds and provides consistent navigation UX.

## What Was Built

### Task 1: Create BreadcrumbBar widget
Created `frontend/lib/widgets/breadcrumb_bar.dart` (181 lines):

- **Breadcrumb data class:** Holds label and optional route (null = current page, not clickable)
- **BreadcrumbBar StatelessWidget:** Parses current route from `GoRouterState.of(context).uri.path`
- **Path parsing logic:**
  - `/home` -> "Home"
  - `/projects` -> "Projects"
  - `/projects/:id` -> "Projects > {Project Name}" (name from ProjectProvider)
  - `/settings` -> "Settings"
- **Truncation support:** `maxVisible` parameter for mobile (shows "..." + last N segments)
- **Clickable parent segments:** Navigate via `context.go(route)`
- **Current page styling:** Bold, non-clickable

**Commit:** a889b6d

### Task 2: Create ContextualBackButton widget
Created `frontend/lib/widgets/contextual_back_button.dart` (119 lines):

- **Contextual labels:**
  - `/projects/:id` -> "Projects"
  - `/projects/:id/threads/:tid` -> "{Project Name}"
  - Root pages -> no back button (SizedBox.shrink)
- **canPop check:** Only show if navigation can pop
- **iconOnly mode:** For mobile AppBar leading (just icon with tooltip)
- **Full mode:** Icon + label TextButton for desktop header

**Commit:** 6288bdf

### Task 3: Refactor screens and update ResponsiveScaffold

**ResponsiveScaffold updates:**
- Added imports for `breadcrumb_bar.dart` and `contextual_back_button.dart`
- Created `_DesktopHeaderBar` widget with:
  - ContextualBackButton (shows only on nested routes)
  - BreadcrumbBar (route-based navigation context)
- Desktop layout: Header bar above content area
- Tablet layout: Same header bar (reuses `_DesktopHeaderBar`)
- Mobile layout:
  - AppBar leading: ContextualBackButton (iconOnly) when canPop, hamburger menu otherwise
  - AppBar title: BreadcrumbBar with maxVisible: 2

**Screen refactoring:**
- **HomeScreen:** Removed ResponsiveLayout, _MobileLayout, _DesktopLayout, _NavigationDrawer, _NavigationSidebar - now content-only (127 lines from 387)
- **SettingsScreen:** Removed Scaffold and AppBar - now content-only ListView (56 lines from 59)
- **ProjectListScreen:** Kept minimal Scaffold for FAB positioning (no AppBar) - body content only (302 lines from 302)
- **ProjectDetailScreen:** Removed AppBar, kept TabBar + content (335 lines from 333) - Column with header, TabBar, TabBarView

**Test fix (deviation):**
- Updated `frontend/test/widget_test.dart` to provide required themeProvider and navigationProvider to MyApp

**Commits:** 2865e5f, 6edbaaa

## Key Links Established

| From | To | Via | Pattern |
|------|-----|-----|---------|
| BreadcrumbBar | GoRouterState | GoRouterState.of(context) | `state.uri.path` |
| BreadcrumbBar | ProjectProvider | context.read | Project name resolution |
| ContextualBackButton | GoRouter | context.pop() | Navigation action |
| ResponsiveScaffold | BreadcrumbBar | Widget composition | AppBar title / header |
| ResponsiveScaffold | ContextualBackButton | Widget composition | Leading action |

## Decisions Made

### 1. Shell-Provided Navigation
**Decision:** All authenticated screens provide content only; ResponsiveScaffold provides all navigation UI (AppBar, sidebar, drawer, breadcrumbs, back buttons).

**Rationale:**
- Single source of truth for navigation chrome
- Eliminates nested Scaffold issues
- Consistent UX across all screens
- Easier to maintain and update navigation behavior

**Alternatives considered:**
- Keep screen-level Scaffolds with `primary: false` - still causes nested Scaffold warnings
- Custom shell widget per screen - violates DRY principle

### 2. Mobile Breadcrumb Truncation
**Decision:** Use `maxVisible: 2` for mobile breadcrumbs, showing "..." prefix when truncated.

**Rationale:**
- Mobile screens have ~300-400px horizontal space
- Full breadcrumb trail overflows on deep routes
- "... > Parent > Current" is sufficient context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Widget test required provider updates**
- **Found during:** Task 3 verification (flutter analyze)
- **Issue:** MyApp now requires themeProvider and navigationProvider parameters
- **Fix:** Updated test to set up mock SharedPreferences and create required providers
- **Files modified:** frontend/test/widget_test.dart
- **Commit:** 6edbaaa

## Verification Results

| Check | Status |
|-------|--------|
| `flutter analyze breadcrumb_bar.dart` | Pass |
| `flutter analyze contextual_back_button.dart` | Pass |
| `flutter analyze responsive_scaffold.dart` | Pass |
| `flutter analyze home_screen.dart` | Pass |
| `flutter analyze settings_screen.dart` | Pass |
| `flutter analyze project_list_screen.dart` | Pass |
| `flutter analyze project_detail_screen.dart` | Pass |
| `flutter analyze` (full) | Pass (29 info/warning, no errors) |
| BreadcrumbBar >= 60 lines | Pass (181 lines) |
| ContextualBackButton >= 30 lines | Pass (119 lines) |

## NAV Requirements Satisfied

| ID | Requirement | Plan | Status |
|----|-------------|------|--------|
| NAV-01 | Persistent sidebar | 01, 02 | Complete |
| NAV-02 | Breadcrumb navigation | 03 | Complete |
| NAV-03 | Back arrows with destination context | 03 | Complete |
| NAV-04 | Navigation highlighting | 02 | Complete |
| NAV-05 | Sidebar state persistence | 01 | Complete |

All 5 NAV requirements from Phase 7 are now satisfied.

## Files Created

### frontend/lib/widgets/breadcrumb_bar.dart (181 lines)
- Breadcrumb data class
- BreadcrumbBar widget
- Path parsing logic
- Truncation support
- Clickable/non-clickable segment rendering

### frontend/lib/widgets/contextual_back_button.dart (119 lines)
- ContextualBackButton widget
- Parent label detection
- iconOnly mode support
- canPop integration

## Files Modified

### frontend/lib/widgets/responsive_scaffold.dart (480 lines, +68)
- Added go_router import
- Added breadcrumb_bar.dart import
- Added contextual_back_button.dart import
- Added _DesktopHeaderBar widget
- Updated _DesktopLayout with header bar
- Updated _TabletLayout with header bar
- Updated _MobileLayout AppBar with breadcrumbs and contextual back

### frontend/lib/screens/home_screen.dart (127 lines, -260)
- Removed ResponsiveLayout, _MobileLayout, _DesktopLayout
- Removed _NavigationDrawer, _NavigationSidebar
- Removed logout button (handled by Settings)
- Content-only widget

### frontend/lib/screens/settings_screen.dart (56 lines, -3)
- Removed Scaffold and AppBar
- Content-only ListView

### frontend/lib/screens/projects/project_list_screen.dart (302 lines, 0)
- Removed AppBar
- Kept Scaffold for FAB positioning
- Body content only

### frontend/lib/screens/projects/project_detail_screen.dart (335 lines, +2)
- Removed AppBar
- Kept TabBar structure
- Added edit button to project header
- Column with header, TabBar, TabBarView

### frontend/test/widget_test.dart (29 lines, +14)
- Added SharedPreferences mock setup
- Added ThemeProvider and NavigationProvider creation
- Updated MyApp instantiation with required providers

## Next Phase Readiness

### Ready for Phase 8
- All navigation infrastructure complete
- Screens are content-only and shell-managed
- No nested Scaffold issues
- Consistent UX across mobile/tablet/desktop

### Blockers
None

### Concerns
None - Phase 7 objectives fully achieved
