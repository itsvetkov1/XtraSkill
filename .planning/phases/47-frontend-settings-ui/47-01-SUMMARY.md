---
phase: 47-frontend-settings-ui
plan: 01
subsystem: frontend-logging
tags: [flutter, provider, settings-ui, logging, privacy, persistence]

requires:
  - phase: 45
    provides: LoggingService singleton with buffer and monitoring
  - phase: 46
    provides: LoggingService.logApi() for HTTP request logging

provides:
  - LoggingProvider for toggle state management
  - Settings screen UI for logging control
  - Persistent logging preference across app restarts
  - Privacy protection via buffer clear on disable

affects:
  - phase: 48
    note: Flush mechanism will check isEnabled before sending logs

tech-stack:
  added:
    - LoggingProvider (ChangeNotifier pattern)
  patterns:
    - Persist-before-notify pattern from ThemeProvider
    - Early return guard in service layer
    - Privacy-first design (clear buffer on disable)

key-files:
  created:
    - frontend/lib/providers/logging_provider.dart
  modified:
    - frontend/lib/services/logging_service.dart
    - frontend/lib/main.dart
    - frontend/lib/screens/settings_screen.dart
    - frontend/test/widget/settings_screen_test.dart
    - frontend/test/widget_test.dart

decisions:
  - id: LOG-024
    decision: Default logging enabled for pilot phase
    rationale: Maximize diagnostic data collection during pilot
    impact: Users start with logging ON, can disable if privacy-conscious
  - id: LOG-025
    decision: Clearing buffer when logging disabled
    rationale: Privacy protection - don't retain logs user disabled
    impact: Toggling off immediately clears in-memory buffer
  - id: LOG-026
    decision: Early return in _log() method
    rationale: Performance - avoid all logging overhead when disabled
    impact: Zero performance cost when logging disabled

metrics:
  duration: 7 minutes
  completed: 2026-02-08
---

# Phase 47 Plan 01: Settings UI with Logging Toggle Summary

**One-liner:** Logging toggle in Settings screen with SharedPreferences persistence and privacy-first buffer clearing on disable

## What Was Built

Added user-facing control for detailed logging via Settings screen toggle with persistent state management.

**LoggingProvider:**
- Follows ThemeProvider pattern exactly (persist-before-notify)
- Loads preference from SharedPreferences on app startup
- Defaults to enabled (true) for pilot phase data collection
- toggleLogging() persists state before updating UI
- Updates LoggingService.isEnabled on toggle

**LoggingService enhancements:**
- Added private `_isEnabled` field (default: true)
- Public setter `isEnabled` updates state and clears buffer when disabled
- Early return in `_log()` method prevents all logging when disabled
- Buffer clear ensures privacy protection

**Settings screen UI:**
- "Detailed Logging" SwitchListTile in Preferences section
- Subtitle: "Capture diagnostic logs for troubleshooting"
- Consumer<LoggingProvider> pattern for reactive UI
- Positioned after AI Provider dropdown, before divider

**Testing:**
- Added MockLoggingProvider to settings_screen_test.dart
- New test group "Logging Section" with 2 tests
- Fixed existing dark mode tests (now 2 SwitchListTiles)
- Updated widget_test.dart smoke test
- All 20 settings screen tests pass
- 617 total frontend tests pass

## Task Commits

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Create LoggingProvider and add isEnabled to LoggingService | d490ed4 | logging_provider.dart, logging_service.dart |
| 2 | Wire LoggingProvider in main.dart and add toggle to Settings | 75a4d0a | main.dart, settings_screen.dart, tests |

## Decisions Made

**LOG-024: Default logging enabled**
- Context: Pilot phase needs maximum diagnostic data
- Decision: Initialize with `isLoggingEnabled = true`
- Alternative considered: Default disabled (privacy-first)
- Chosen because: Pilot prioritizes data collection, users can disable
- Impact: More users contribute logs during pilot, better issue detection

**LOG-025: Clear buffer when disabled**
- Context: User disables logging for privacy
- Decision: Call `clearBuffer()` in isEnabled setter when disabled
- Alternative considered: Retain buffer until next flush
- Chosen because: Privacy-first design, immediate effect expected by user
- Impact: Toggle OFF immediately destroys in-memory logs

**LOG-026: Early return in _log()**
- Context: Performance when logging disabled
- Decision: Add `if (!_isEnabled) return;` as first line in _log()
- Alternative considered: Check in each public log method
- Chosen because: Single point of control, zero overhead when disabled
- Impact: No performance cost when logging disabled

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

**Persist-before-notify pattern:**
```dart
Future<void> toggleLogging() async {
  _isLoggingEnabled = !_isLoggingEnabled;

  // PERSIST FIRST (survives crash after toggle)
  await _prefs.setBool(_loggingKey, _isLoggingEnabled);

  // THEN update service
  LoggingService().isEnabled = _isLoggingEnabled;

  // FINALLY notify UI
  notifyListeners();
}
```

**Early return guard:**
```dart
void _log({...}) {
  if (!_isEnabled) return;  // <-- Prevents all logging overhead

  // Console logging
  _logger.log(logLevel, message);

  // Buffer management
  _buffer.add(entry);
}
```

**Privacy protection:**
```dart
set isEnabled(bool enabled) {
  _isEnabled = enabled;
  if (!enabled) {
    clearBuffer();  // <-- Immediate privacy protection
  }
}
```

## Testing Results

**Widget tests:** All 20 settings screen tests pass
- Section headers (with scroll to Actions)
- Account section (7 tests)
- Appearance section (3 tests, updated for 2 switches)
- Preferences section (2 tests)
- Usage section (2 tests)
- Logging section (2 tests - NEW)
- Actions section (3 tests)

**Integration:** Smoke test passes with loggingProvider
**Analysis:** No errors, 39 existing warnings (unrelated)

## Next Phase Readiness

**Phase 48 (Flush logs to backend) can proceed:**
- LoggingProvider state management ready
- LoggingService.isEnabled check available
- Buffer clearing on disable ensures privacy
- Settings UI allows user control

**Recommendation:** Phase 48 flush logic should check `LoggingService()._isEnabled` before transmitting logs.

## Files Modified

**Created:**
- `frontend/lib/providers/logging_provider.dart` (77 lines)

**Modified:**
- `frontend/lib/services/logging_service.dart` (+16 lines: isEnabled setter, early return)
- `frontend/lib/main.dart` (+5 lines: load and wire LoggingProvider)
- `frontend/lib/screens/settings_screen.dart` (+12 lines: SwitchListTile for logging)
- `frontend/test/widget/settings_screen_test.dart` (+24 lines: logging tests, fix dark mode tests)
- `frontend/test/widget_test.dart` (+2 lines: loggingProvider in smoke test)

## Self-Check: PASSED

All created files exist:
- frontend/lib/providers/logging_provider.dart ✓

All commits exist:
- d490ed4 ✓
- 75a4d0a ✓
