---
phase: 10-polish-and-empty-states
plan: 01
subsystem: frontend-utilities
tags: [date-formatting, empty-state, ui-components, timeago, intl]
dependency-graph:
  requires:
    - "Phase 9: Deletion flows (post-delete empty states)"
  provides:
    - "DateFormatter utility for consistent date display"
    - "EmptyState widget for all list screens"
  affects:
    - "10-02: Home Screen with empty state"
    - "10-03: Project List with empty state"
    - "10-04: Thread List with date formatting"
    - "All future screens using dates or empty states"
tech-stack:
  added:
    - "timeago: ^3.7.1"
  patterns:
    - "Centralized utility classes in lib/utils/"
    - "Relative/absolute date threshold (7 days)"
    - "Reusable empty state widget template"
key-files:
  created:
    - "frontend/lib/utils/date_formatter.dart"
    - "frontend/lib/widgets/empty_state.dart"
  modified:
    - "frontend/pubspec.yaml"
    - "frontend/lib/main.dart"
decisions:
  - id: "DATE-FMT-01"
    choice: "7-day threshold for relative vs absolute dates"
    reason: "Balance between recency feel and date precision per POLISH-01"
  - id: "EMPTY-STATE-01"
    choice: "FilledButton.icon for CTA"
    reason: "Material 3 primary action button per CONTEXT.md"
metrics:
  duration: "~2 minutes"
  completed: "2026-01-30"
---

# Phase 10 Plan 01: Foundation Infrastructure Summary

**One-liner:** DateFormatter utility with 7-day relative/absolute threshold using timeago package, plus reusable EmptyState widget with themed icon and FilledButton CTA.

## What Was Built

### DateFormatter Utility (`frontend/lib/utils/date_formatter.dart`)

Centralized date formatting utility implementing POLISH-01 requirement:

```dart
class DateFormatter {
  static void init() { /* Initialize timeago locales */ }

  static String format(DateTime date) {
    // <7 days: "about 2 hours ago", "3 days ago"
    // >=7 days: "Jan 18, 2026"
  }

  static String formatTime(DateTime date) { /* "5:08 PM" */ }
  static String formatDateTime(DateTime date) { /* "Jan 18, 2026 5:08 PM" */ }
}
```

Key implementation details:
- Uses `timeago` package for relative time ("about 2 hours ago")
- Uses `intl` DateFormat.yMMMd() for absolute dates ("Jan 18, 2026")
- 7-day threshold balances recency feel with precision
- Initialized in main.dart via `initializeDateFormatting()` and `DateFormatter.init()`

### EmptyState Widget (`frontend/lib/widgets/empty_state.dart`)

Reusable empty state template implementing ONBOARD-01 to ONBOARD-03:

```dart
EmptyState(
  icon: Icons.folder_outlined,      // 64px, primary color
  title: 'No projects yet',          // titleLarge
  message: 'Create your first...',   // bodyMedium, onSurfaceVariant
  buttonLabel: 'Create Project',     // FilledButton.icon
  onPressed: () => _createProject(),
  buttonIcon: Icons.add,             // Optional, defaults to add
)
```

Layout follows CONTEXT.md guidelines:
- Centered column with 32px padding
- Large themed icon (64px, primary color)
- Title with titleLarge style
- Message with bodyMedium and onSurfaceVariant color
- FilledButton.icon CTA (not ElevatedButton per Material 3)

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Add timeago package and create DateFormatter utility | c7632cc | pubspec.yaml, date_formatter.dart, main.dart |
| 2 | Create reusable EmptyState widget | b8eb940 | empty_state.dart |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

```
flutter analyze lib/utils/date_formatter.dart
> No issues found!

flutter analyze lib/widgets/empty_state.dart
> No issues found!

grep "DateFormatter.init" lib/main.dart
> Line 34: DateFormatter.init();

grep "timeago: ^3.7.1" pubspec.yaml
> Line 49: timeago: ^3.7.1
```

All success criteria met:
- [x] timeago ^3.7.1 added to pubspec.yaml
- [x] DateFormatter class with format(), formatTime(), init() methods
- [x] EmptyState widget with icon, title, message, buttonLabel, onPressed params
- [x] DateFormatter.init() called in main.dart before runApp
- [x] All code passes flutter analyze

## Usage Examples

### DateFormatter in Thread List
```dart
Text(
  DateFormatter.format(thread.updatedAt),
  style: theme.textTheme.bodySmall,
)
// Output: "about 2 hours ago" or "Jan 18, 2026"
```

### EmptyState in Project List
```dart
if (projects.isEmpty) {
  return EmptyState(
    icon: Icons.folder_outlined,
    title: 'No projects yet',
    message: 'Create your first project to start capturing requirements with AI-assisted discovery.',
    buttonLabel: 'Create Project',
    onPressed: () => _showCreateProjectDialog(context),
  );
}
```

## Next Phase Readiness

**Ready for 10-02:** Foundation utilities are in place. Next plans can:
- Import `DateFormatter` from `package:frontend/utils/date_formatter.dart`
- Import `EmptyState` from `package:frontend/widgets/empty_state.dart`
- Replace inline empty states with `EmptyState` widget
- Replace inline date formatting with `DateFormatter.format()`

**No blockers identified.**
