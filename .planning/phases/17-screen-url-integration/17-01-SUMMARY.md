---
phase: 17-screen-url-integration
plan: 01
subsystem: frontend-ui
tags: [flutter, error-handling, navigation, widgets]

dependency-graph:
  requires:
    - 15-route-architecture (URL routing)
    - 16-auth-url-preservation (sessionStorage for returnUrl)
  provides:
    - ResourceNotFoundState reusable widget
    - ProjectProvider.isNotFound 404 detection
    - ProjectDetailScreen not-found UI
  affects:
    - 17-02 (ThreadDetailScreen not-found state)

tech-stack:
  added: []
  patterns:
    - Error state differentiation (not-found vs generic error)
    - Reusable error state widgets

key-files:
  created:
    - frontend/lib/widgets/resource_not_found_state.dart
  modified:
    - frontend/lib/providers/project_provider.dart
    - frontend/lib/screens/projects/project_detail_screen.dart

decisions:
  DEC-17-01-01: "Check isNotFound BEFORE error != null (distinct UI states)"
  DEC-17-01-02: "Set error=null when isNotFound=true (mutually exclusive states)"
  DEC-17-01-03: "Use folder_off_outlined icon for deleted project (visual distinction)"

metrics:
  duration: ~4 minutes
  completed: 2026-01-31
---

# Phase 17 Plan 01: Project Not-Found State Summary

**One-liner:** Reusable ResourceNotFoundState widget with error styling, ProjectProvider.isNotFound flag for 404 detection, and ProjectDetailScreen integration showing "Back to Projects" navigation.

## What Was Built

### 1. ResourceNotFoundState Widget
Created `frontend/lib/widgets/resource_not_found_state.dart`:
- Mirrors EmptyState structure but with error-specific styling
- Icon uses `theme.colorScheme.error` (not primary)
- Button shows `Icons.arrow_back` (navigation away, not creation)
- No optional buttonIcon - always shows back arrow

### 2. ProjectProvider isNotFound Flag
Updated `frontend/lib/providers/project_provider.dart`:
- Added `_isNotFound` private field and `isNotFound` getter
- `selectProject()` detects 404 from error message ("not found" or "404")
- Sets `isNotFound=true` and `error=null` for 404 (mutually exclusive)
- `clearError()` also clears `isNotFound`

### 3. ProjectDetailScreen Not-Found UI
Updated `frontend/lib/screens/projects/project_detail_screen.dart`:
- Checks `isNotFound` BEFORE `error != null` (distinct handling)
- Shows ResourceNotFoundState with:
  - Icon: `Icons.folder_off_outlined`
  - Title: "Project not found"
  - Message: "This project may have been deleted or you may not have access to it."
  - Button: "Back to Projects" navigating to `/projects`

## Implementation Decisions

| Decision | Rationale |
|----------|-----------|
| Check isNotFound BEFORE error | These are distinct UI states - 404 is "not found" (back button), other errors are retryable (retry button) |
| Set error=null when isNotFound=true | Makes states mutually exclusive - simplifies UI logic |
| Use folder_off_outlined icon | Visual distinction from generic error (error_outline) |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 33697e5 | feat | Create ResourceNotFoundState widget |
| a550430 | feat | Add isNotFound flag to ProjectProvider |
| e1feb43 | feat | Add not-found state to ProjectDetailScreen |

## Deviations from Plan

None - plan executed exactly as written.

## Verification

All verification criteria met:
- [x] `flutter analyze frontend/lib/widgets/` - No issues
- [x] `flutter analyze frontend/lib/providers/project_provider.dart` - No issues
- [x] `flutter analyze frontend/lib/screens/projects/project_detail_screen.dart` - No issues
- [x] `flutter build web --no-tree-shake-icons` - Build succeeds

## Next Phase Readiness

Plan 17-02 can proceed immediately:
- ResourceNotFoundState widget ready for reuse
- Pattern established: isNotFound flag, check before error, error=null for 404
- ThreadDetailScreen will follow identical pattern with ThreadProvider
