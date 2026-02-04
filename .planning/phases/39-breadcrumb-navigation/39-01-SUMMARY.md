---
phase: 39-breadcrumb-navigation
plan: 01
subsystem: frontend-navigation
tags: [breadcrumbs, go-router, navigation, document-viewer, thread-navigation]

dependency-graph:
  requires:
    - Phase 15 Route Architecture (established GoRouter patterns)
    - Phase 38 Document Preview (document viewing patterns)
  provides:
    - Extended breadcrumb navigation for threads and documents
    - Document Viewer URL routing
    - Browser back button support for document viewer
  affects:
    - Future navigation features build on these patterns

tech-stack:
  added: []
  patterns:
    - Nested GoRoute under project route for documents
    - context.push for browser history preservation
    - Provider read in breadcrumb for dynamic labels

key-files:
  created: []
  modified:
    - frontend/lib/main.dart
    - frontend/lib/widgets/breadcrumb_bar.dart
    - frontend/lib/widgets/documents_column.dart
    - frontend/lib/screens/documents/document_list_screen.dart

decisions:
  - id: DOCUMENT-ROUTE-PATTERN
    choice: Nested route /projects/:id/documents/:docId
    reason: Consistent with threads pattern; enables breadcrumb context
  - id: PUSH-VS-GO
    choice: context.push for document navigation
    reason: Preserves browser history; back button returns to project
  - id: INTERMEDIATE-SEGMENT-LINKS
    choice: "Threads" and "Documents" segments link to project detail
    reason: No separate routes for tabs; user clicks tab after landing on project

metrics:
  duration: ~8 minutes
  completed: 2026-02-04
---

# Phase 39 Plan 01: Breadcrumb Navigation Summary

**One-liner:** Full breadcrumb hierarchy for threads (Projects > Project > Threads > Thread) and documents with proper GoRouter URL routing for Document Viewer

## What Was Built

### Task 1: Document Route in Router
Added nested document route in `frontend/lib/main.dart`:
- New route: `documents/:docId` under `/projects/:id`
- Full path: `/projects/:id/documents/:docId`
- Resolves to DocumentViewerScreen with documentId parameter
- Added import for DocumentViewerScreen

### Task 2: Extended Breadcrumb Building
Enhanced `_buildBreadcrumbs` method in `frontend/lib/widgets/breadcrumb_bar.dart`:
- **NAV-01:** Thread breadcrumb now shows: Projects > {Project Name} > Threads > {Thread Title}
- **NAV-02:** Project-less thread shows: Chats > {Thread Title}
- **NAV-03:** Document breadcrumb shows: Projects > {Project Name} > Documents > {Document Name}
- Added DocumentProvider import for document name lookup
- Intermediate segments ("Threads", "Documents") link to project detail (user clicks tab)

### Task 3: GoRouter Document Navigation
Updated document viewing to use GoRouter in both files:

**documents_column.dart:**
- Added go_router import
- Changed `_onView` from Navigator.push to `context.push('/projects/$projectId/documents/$documentId')`
- Removed unused DocumentViewerScreen import

**document_list_screen.dart:**
- Added go_router import
- Updated popup menu "view" action to use context.push
- Updated ListTile onTap to use context.push
- Removed unused DocumentViewerScreen import

## Key Technical Details

### Breadcrumb Route Pattern Order
The order of route checks in _buildBreadcrumbs is critical:
1. Home/root
2. Settings
3. Chats (project-less threads)
4. Projects (with internal order: documents check, threads check, simple project check)
5. Fallback

### Push vs Go for Navigation
```dart
// Push - adds to history stack (back button works)
context.push('/projects/$projectId/documents/$documentId');

// Go - replaces current location (back button goes further back)
context.go('/projects/$projectId');
```

Document viewing uses `push` so browser back returns to project. Breadcrumb clicks use `go` for direct navigation.

## Requirements Verified

| Requirement | Status | Verification |
|-------------|--------|--------------|
| NAV-01 | Done | Thread breadcrumb shows "Projects > {Name} > Threads > {Title}" |
| NAV-02 | Done | Project-less thread shows "Chats > {Title}" |
| NAV-03 | Done | Document breadcrumb shows "Projects > {Name} > Documents > {Filename}" |
| NAV-04 | Done | All segments except current page are clickable |
| NAV-05 | Done | Mobile truncation already supported via maxVisible parameter |
| NAV-06 | Done | Document viewer URL is /projects/{id}/documents/{docId} |

## Commits

| Hash | Description |
|------|-------------|
| TBD | feat(39-01): complete breadcrumb navigation and document routing |

## Deviations from Plan

None - plan executed exactly as written.

## Files Changed

- `frontend/lib/main.dart`
  - Added DocumentViewerScreen import
  - Added documents/:docId nested route under projects/:id

- `frontend/lib/widgets/breadcrumb_bar.dart`
  - Added DocumentProvider import
  - Restructured _buildBreadcrumbs for all route patterns
  - Added chats route handling
  - Added documents route handling
  - Added "Threads" intermediate segment

- `frontend/lib/widgets/documents_column.dart`
  - Added go_router import
  - Changed _onView to use context.push
  - Removed document_viewer_screen import

- `frontend/lib/screens/documents/document_list_screen.dart`
  - Added go_router import
  - Changed 2 Navigator.push calls to context.push
  - Removed document_viewer_screen import

## Next Phase Readiness

Phase 39 is complete with 1 plan (this one). Milestone v1.9.3 (Document & Navigation Polish) is complete.
