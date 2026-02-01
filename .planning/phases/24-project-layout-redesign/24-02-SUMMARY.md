---
phase: 24-project-layout-redesign
plan: 02
subsystem: frontend-ui
tags: [flutter, layout, threads-first, tabs-removal]

dependency-graph:
  requires:
    - "24-01 (DocumentColumnProvider and DocumentsColumn widget)"
  provides:
    - "Threads-first project detail layout"
    - "Integrated collapsible documents column"
  affects:
    - "UX-002 user story (threads primary, documents column)"

tech-stack:
  added: []
  patterns:
    - "Row-based layout (column + expanded content)"
    - "Vertical divider between sections"
    - "Immediate thread loading in initState"

file-tracking:
  key-files:
    created: []
    modified:
      - frontend/lib/screens/projects/project_detail_screen.dart

decisions:
  - id: TABS-REMOVAL
    choice: "Complete removal of TabController/TabBar/TabBarView"
    reason: "Threads-first layout eliminates need for tab navigation"
  - id: LAYOUT-STRUCTURE
    choice: "Column(header, Expanded(Row(docs, divider, threads)))"
    reason: "Clean separation of header and content areas with horizontal split"

metrics:
  duration: "~3 minutes"
  completed: "2026-02-01"
---

# Phase 24 Plan 02: Integrate Column into Project Detail Summary

Replaced tab-based navigation with threads-first Row layout integrating DocumentsColumn.

## What Was Built

### Project Detail Screen Refactoring

**Removed:**
- `SingleTickerProviderStateMixin` mixin
- `TabController` initialization and disposal
- `TabBar` with Documents/Threads tabs
- `TabBarView` with tab content switching
- `_DocumentsTab` private class (no longer needed)
- `document_upload_screen.dart` import (now handled by DocumentsColumn)

**Added:**
- `documents_column.dart` import
- Row-based layout in Expanded widget
- Immediate thread loading in initState

### Final Layout Structure

```dart
Column(
  children: [
    // Project info header (name, description, edit/delete buttons)
    Container(...),

    // Main content area
    Expanded(
      child: Row(
        children: [
          DocumentsColumn(projectId: widget.projectId),  // 48px/280px
          VerticalDivider(width: 1, thickness: 1),
          Expanded(
            child: ThreadListScreen(projectId: widget.projectId),
          ),
        ],
      ),
    ),
  ],
)
```

### Behavior Changes

1. **Threads visible immediately** - No more tab switching to see threads
2. **Documents in side column** - Accessible via collapsible strip on left
3. **Simplified state** - No TabController lifecycle management
4. **Thread loading** - Now happens in initState (was on tab switch)

## Commits

| Hash | Message |
|------|---------|
| e7f439d | feat(24-02): replace tabs with threads-first layout and documents column |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All LAYOUT requirements verified:

1. LAYOUT-01: Threads list shows immediately when opening project
2. LAYOUT-02: Documents column appears on left side
3. LAYOUT-03: Column minimized (48px strip) by default
4. LAYOUT-04: Clicking strip expands column to 280px
5. LAYOUT-05: Clicking collapse button minimizes column
6. LAYOUT-06: Document operations (upload, view, delete) work from column
7. Session persistence: Column state preserved when navigating away and back

## Next Phase Readiness

**Phase 24 complete.** The project layout redesign is fully implemented:
- DocumentColumnProvider manages collapse/expand state
- DocumentsColumn widget provides the collapsible sidebar
- ProjectDetailScreen uses threads-first Row layout

**User story UX-002 addressed:**
- Threads are now the primary view (no tab switching)
- Documents accessible via collapsible side column
- State persists within session
