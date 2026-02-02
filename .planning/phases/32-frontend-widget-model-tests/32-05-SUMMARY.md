---
phase: 32-frontend-widget-model-tests
plan: 05
subsystem: frontend-testing
tags: [flutter, widget-tests, gap-closure, conditional-import, dart-html]

dependency_graph:
  requires:
    - 32-04-PLAN (widget tests complete)
    - 32-03-PLAN (DocumentListScreen tests created)
  provides:
    - Fixed DocumentListScreen test assertions
    - Conditional import for UrlStorageService (web/stub)
    - 103 passing widget tests
  affects:
    - 33-PLAN (Phase 32 verification now complete)

tech_stack:
  added: []
  patterns:
    - Conditional export for platform-specific code
    - Stub implementation pattern for web-only APIs

key_files:
  created:
    - frontend/lib/services/url_storage_service_web.dart (dart:html impl)
    - frontend/lib/services/url_storage_service_stub.dart (no-op stub)
  modified:
    - frontend/lib/services/url_storage_service.dart (conditional export)
    - frontend/test/widget/document_list_screen_test.dart (assertions fixed)

decisions:
  - id: D-32-05-01
    decision: Use conditional export pattern for dart:html dependency
    rationale: Flutter test environment cannot compile dart:html; stub provides no-op for tests
  - id: D-32-05-02
    decision: Use textContaining for date assertions
    rationale: DateFormatter.format() returns relative dates with variable text ("about X hours ago")
  - id: D-32-05-03
    decision: Use recent date in date format test
    rationale: Old dates (>7 days) return absolute format; relative dates are more test-stable

metrics:
  duration: ~2 minutes
  completed: 2026-02-02
---

# Phase 32 Plan 05: Gap Closure Summary

Fixed verification failures in DocumentListScreen tests and LoginScreen compilation.

## One-liner

Conditional import pattern for UrlStorageService resolves dart:html compilation; fixed EmptyState text assertions match current UI.

## Tasks Completed

| Task | Name | Commit | Result |
|------|------|--------|--------|
| 1 | Fix DocumentListScreen test assertions | c5c07c4 | 7/7 tests pass |
| 2 | Create conditional import for UrlStorageService | 07032d5 | 5/5 LoginScreen tests pass |
| 3 | Run full widget test suite | (verification) | 103/103 tests pass |

## Changes Made

### frontend/test/widget/document_list_screen_test.dart (Modified)
- Fixed empty state text: `'No documents yet'` (was `'No documents uploaded'`)
- Fixed empty state message: `'Upload documents to provide context...'` (was `'Tap the + button...'`)
- Fixed empty state icon: `Icons.description_outlined` (was `Icons.folder_open`)
- Fixed date assertion: `textContaining('Uploaded ')` without colon
- Changed testDate to `DateTime.now().subtract(Duration(hours: 2))` for stable relative format

### frontend/lib/services/url_storage_service.dart (Modified)
- Converted from implementation to conditional export
- Routes to web or stub based on `dart.library.html` availability

### frontend/lib/services/url_storage_service_web.dart (Created)
- Original implementation moved here
- Uses `dart:html` sessionStorage for browser environment

### frontend/lib/services/url_storage_service_stub.dart (Created)
- No-op implementation for tests and native platforms
- `storeReturnUrl()` - no-op
- `getReturnUrl()` - returns null
- `clearReturnUrl()` - no-op

## Verification Results

- DocumentListScreen tests: 7/7 pass
- LoginScreen tests: 5/5 pass (no dart:html compilation error)
- Full widget test suite: 103/103 pass

## Key Patterns Applied

### 1. Conditional Export Pattern
```dart
// url_storage_service.dart
export 'url_storage_service_stub.dart'
    if (dart.library.html) 'url_storage_service_web.dart';
```

### 2. Stub Implementation
```dart
// No-op methods for non-web platforms
class UrlStorageService {
  void storeReturnUrl(String url) {} // No-op
  String? getReturnUrl() => null;    // Always null
  void clearReturnUrl() {}           // No-op
}
```

## Deviations from Plan

None - plan executed exactly as written.

## Success Criteria Status

| Criterion | Status |
|-----------|--------|
| document_list_screen_test.dart assertions match current UI | PASS |
| url_storage_service.dart uses conditional export pattern | PASS |
| url_storage_service_stub.dart provides no-op implementation | PASS |
| url_storage_service_web.dart contains original dart:html impl | PASS |
| login_screen_test.dart compiles without dart:html error | PASS |
| All 7 DocumentListScreen tests pass | PASS |
| All 5 LoginScreen tests pass | PASS |
| Full widget test suite passes | PASS - 103 tests |

## Phase 32 Verification Status

With this gap closure plan complete:

| Requirement | Tests | Status |
|-------------|-------|--------|
| FMOD-01 | 27 model tests | PASS |
| FMOD-02 | Thread/TokenUsage tests | PASS |
| FWID-03 | 25 ConversationScreen tests | PASS |
| FWID-04 | 45 screen tests (document, project, thread, chats) | PASS |
| FWID-05 | 30 HomeScreen/SettingsScreen tests | PASS |
| FWID-06 | 12 LoginScreen tests | PASS |

**Phase 32 complete: 6/6 requirements covered**

## Next Phase Readiness

Phase 33 (test quality verification) can proceed. All Phase 32 widget and model tests are passing.
