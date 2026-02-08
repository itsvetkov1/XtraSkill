# Phase 47: Frontend Settings UI - Research

**Researched:** 2026-02-08
**Domain:** Flutter UI state management with SharedPreferences persistence
**Confidence:** HIGH

## Summary

This phase adds a logging toggle to the existing Settings screen, following the established patterns in the codebase. The research examined existing settings implementations (ThemeProvider, ProviderProvider) and the LoggingService to understand how to integrate an enable/disable mechanism.

The standard approach uses a ChangeNotifier provider with immediate SharedPreferences persistence (the "persist-before-notify" pattern). The LoggingService already exists as a singleton with buffering and console output, so the implementation requires adding an enabled/disabled state that conditionally stops logging operations.

This is a straightforward UI integration task with well-established patterns in the codebase. All required dependencies are already present (shared_preferences, provider, logger).

**Primary recommendation:** Create LoggingProvider following ThemeProvider pattern with immediate persistence, add isEnabled check to LoggingService._log() method, and add SwitchListTile to Settings screen.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| provider | ^6.1.5+1 | State management | Project standard, used for all providers (AuthProvider, ThemeProvider, ProviderProvider) |
| shared_preferences | ^2.5.4 | Persistent key-value storage | Already used for theme and provider preferences, cross-platform |
| logger | ^2.5.0 | Console logging | Already integrated in LoggingService with ProductionFilter |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| flutter_test | SDK | Widget testing | Test toggle behavior and persistence |
| mockito | ^5.6.3 | Mock generation | Mock LoggingProvider in existing settings_screen_test.dart |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| provider + ChangeNotifier | Riverpod | Riverpod offers better testability and compile-time safety, but project uses provider pattern throughout (phase context states "Riverpod for state management" but codebase shows provider package in use) |
| shared_preferences | Hive/SQLite | Overkill for simple boolean flag, SharedPreferences is proven in codebase |

**Installation:**
```bash
# No new dependencies needed - all already present in pubspec.yaml
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/
├── providers/
│   └── logging_provider.dart      # NEW: ChangeNotifier for logging state
├── services/
│   └── logging_service.dart       # MODIFY: Add isEnabled check
├── screens/
│   └── settings_screen.dart       # MODIFY: Add logging toggle
└── main.dart                      # MODIFY: Load LoggingProvider on startup
```

### Pattern 1: Provider with Immediate Persistence (Persist-Before-Notify)
**What:** ChangeNotifier that saves state to SharedPreferences BEFORE calling notifyListeners()
**When to use:** For user preferences that must survive app crashes (theme, provider selection, logging toggle)
**Example:**
```dart
// Source: frontend/lib/providers/theme_provider.dart (lines 60-74)
class ThemeProvider extends ChangeNotifier {
  final SharedPreferences _prefs;
  bool _isDarkMode;
  static const String _themeKey = 'isDarkMode';

  Future<void> toggleTheme() async {
    _isDarkMode = !_isDarkMode;
    try {
      // CRITICAL: Persist BEFORE notifyListeners
      await _prefs.setBool(_themeKey, _isDarkMode);
    } catch (e) {
      debugPrint('Failed to persist theme preference: $e');
      // Don't block UI - continue with notifyListeners
    }
    notifyListeners();
  }
}
```

**Why this matters:** Ensures preference survives if app crashes after toggle but before shutdown.

### Pattern 2: Async Factory Load Method
**What:** Static factory method that loads saved preference before constructing provider
**When to use:** Prevent flash of wrong state on app startup
**Example:**
```dart
// Source: frontend/lib/providers/theme_provider.dart (lines 33-43)
static Future<ThemeProvider> load(SharedPreferences prefs) async {
  try {
    final isDarkMode = prefs.getBool(_themeKey) ?? false;
    return ThemeProvider(prefs, initialDarkMode: isDarkMode);
  } catch (e) {
    debugPrint('Failed to load theme preference: $e');
    return ThemeProvider(prefs, initialDarkMode: false);
  }
}
```

**Why this matters:** Provider is initialized with correct state before MaterialApp renders.

### Pattern 3: Singleton Service with Conditional Logging
**What:** Singleton service checks enabled flag before performing operations
**When to use:** Central service that needs enable/disable capability
**Example:**
```dart
// Existing pattern from LoggingService (lines 152-179)
class LoggingService {
  static final LoggingService _instance = LoggingService._internal();
  factory LoggingService() => _instance;

  void _log({
    required String level,
    required String message,
    required String category,
    Map<String, dynamic>? metadata,
  }) {
    // ADD CHECK HERE: if (!_isEnabled) return;
    _logger.log(logLevel, message);
    _buffer.add(entry);
    // ...
  }
}
```

**Why this matters:** Single point of control - all logging methods funnel through _log().

### Pattern 4: Settings Screen Section Structure
**What:** Grouped settings with section headers, using SwitchListTile for toggles
**When to use:** Any settings screen with multiple categories
**Example:**
```dart
// Source: frontend/lib/screens/settings_screen.dart (lines 80-92)
_buildSectionHeader(context, 'Appearance'),
Consumer<ThemeProvider>(
  builder: (context, themeProvider, _) {
    return SwitchListTile(
      title: const Text('Dark Mode'),
      subtitle: const Text('Use dark theme'),
      value: themeProvider.isDarkMode,
      onChanged: (_) => themeProvider.toggleTheme(),
    );
  },
),
const Divider(),
```

**Why this matters:** Consistent UI pattern across all settings categories.

### Anti-Patterns to Avoid
- **Checking enabled state in each log method:** Don't add `if (isEnabled)` to logNavigation(), logAction(), etc. Centralize check in _log() method.
- **Not persisting before notifying:** Async operations can be interrupted - always persist BEFORE notifyListeners().
- **Forgetting to wire global error handlers:** FlutterError.onError and PlatformDispatcher.onError must be conditionally disabled when logging is off (lines 56-68 in main.dart).

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Key-value persistence | Custom file-based storage | shared_preferences | Cross-platform, handles platform differences (NSUserDefaults on iOS, SharedPreferences on Android, localStorage on web) |
| State change notifications | Manual setState() management | provider + ChangeNotifier | Scoped rebuilds, testable, established in codebase |
| Loading saved preferences | Synchronous read in build() | Async factory load in main() | Prevents flash of wrong state, ensures correct initial render |

**Key insight:** SharedPreferences is not just "simple storage" - it handles platform-specific storage APIs, async persistence, and failure modes. The provider package eliminates manual state management boilerplate.

## Common Pitfalls

### Pitfall 1: Forgetting to Load Provider on Startup
**What goes wrong:** LoggingProvider not loaded in main(), causing null errors or missing persistence
**Why it happens:** Pattern requires async factory call before MaterialApp renders
**How to avoid:** Follow established pattern in main.dart (lines 46-49) where ThemeProvider and ProviderProvider are loaded
**Warning signs:** "Null check operator used on null value" errors on LoggingProvider access

### Pitfall 2: Not Checking Enabled State for Global Error Handlers
**What goes wrong:** Global error handlers (FlutterError.onError, PlatformDispatcher.onError) continue logging when toggle is disabled
**Why it happens:** Error handlers wired directly to LoggingService, not through provider
**How to avoid:** Add enabled check before calling loggingService.logError() in error handlers, or pass LoggingProvider to handlers
**Warning signs:** Logs still appearing in console/buffer after toggle disabled

### Pitfall 3: Race Condition Between Provider Toggle and Service State
**What goes wrong:** User toggles off, but logs still captured briefly before service reads new state
**Why it happens:** LoggingService singleton doesn't automatically know about provider state changes
**How to avoid:** Pass enabled state to LoggingService on provider change, or have service read from provider
**Warning signs:** Test failures showing logs captured after toggle disabled

### Pitfall 4: Incomplete Test Coverage
**What goes wrong:** Widget tests don't verify persistence, only toggle behavior
**Why it happens:** SharedPreferences requires mocking in tests
**How to avoid:** Use MockLoggingProvider in settings_screen_test.dart (existing pattern at lines 16-40), verify toggle() method called
**Warning signs:** Tests pass but persistence doesn't work in real app

### Pitfall 5: Not Clearing Buffer When Disabling Logging
**What goes wrong:** User disables logging expecting privacy, but buffer still contains historical logs
**Why it happens:** Disable only stops new logs, doesn't flush existing buffer
**How to avoid:** Call loggingService.clearBuffer() when logging disabled to respect privacy intent
**Warning signs:** User reports privacy concern - toggled off but logs still visible/transmitted

## Code Examples

Verified patterns from existing codebase:

### Loading Provider on Startup (main.dart pattern)
```dart
// Source: frontend/lib/main.dart (lines 46-49)
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final prefs = await SharedPreferences.getInstance();
  final themeProvider = await ThemeProvider.load(prefs);
  final navigationProvider = await NavigationProvider.load(prefs);
  final providerProvider = await ProviderProvider.load(prefs);
  // ADD: final loggingProvider = await LoggingProvider.load(prefs);

  runApp(MyApp(
    themeProvider: themeProvider,
    // ADD: loggingProvider: loggingProvider,
  ));
}
```

### Provider Factory Constructor Pattern
```dart
// Source: frontend/lib/providers/provider_provider.dart (lines 40-54)
class LoggingProvider extends ChangeNotifier {
  final SharedPreferences _prefs;
  bool _isLoggingEnabled;
  static const String _loggingKey = 'isLoggingEnabled';

  LoggingProvider(this._prefs, {bool? initialEnabled})
      : _isLoggingEnabled = initialEnabled ?? true; // Default enabled

  static Future<LoggingProvider> load(SharedPreferences prefs) async {
    try {
      final isEnabled = prefs.getBool(_loggingKey) ?? true;
      return LoggingProvider(prefs, initialEnabled: isEnabled);
    } catch (e) {
      debugPrint('Failed to load logging preference: $e');
      return LoggingProvider(prefs, initialEnabled: true);
    }
  }
}
```

### Toggle with Immediate Persistence
```dart
// Source: frontend/lib/providers/theme_provider.dart (lines 60-74)
Future<void> toggleLogging() async {
  _isLoggingEnabled = !_isLoggingEnabled;

  try {
    // CRITICAL: Persist BEFORE notifyListeners
    await _prefs.setBool(_loggingKey, _isLoggingEnabled);
  } catch (e) {
    debugPrint('Failed to persist logging preference: $e');
  }

  notifyListeners();

  // PRIVACY: Clear buffer when disabling to respect user intent
  if (!_isLoggingEnabled) {
    LoggingService().clearBuffer();
  }
}
```

### SwitchListTile in Settings
```dart
// Source: frontend/lib/screens/settings_screen.dart (lines 80-92)
// Add to "Preferences" section after provider dropdown
Consumer<LoggingProvider>(
  builder: (context, loggingProvider, _) {
    return SwitchListTile(
      title: const Text('Detailed Logging'),
      subtitle: const Text('Capture diagnostic logs for troubleshooting'),
      value: loggingProvider.isLoggingEnabled,
      onChanged: (_) => loggingProvider.toggleLogging(),
    );
  },
),
```

### Conditional Logging in Service
```dart
// Source: frontend/lib/services/logging_service.dart (lines 152-179)
class LoggingService {
  bool _isEnabled = true; // Public setter for provider to update

  set isEnabled(bool enabled) {
    _isEnabled = enabled;
    if (!enabled) {
      clearBuffer(); // Privacy: clear on disable
    }
  }

  void _log({
    required String level,
    required String message,
    required String category,
    Map<String, dynamic>? metadata,
  }) {
    // CRITICAL: Check enabled state first
    if (!_isEnabled) return;

    final logLevel = Level.values.byName(level.toLowerCase());
    _logger.log(logLevel, message);
    // ... rest of logging logic
  }
}
```

### Widget Test Pattern
```dart
// Source: frontend/test/widget/settings_screen_test.dart (lines 147-150)
group('Logging Section', () {
  testWidgets('shows logging toggle', (tester) async {
    await tester.pumpWidget(buildTestWidget());
    await tester.pump();

    expect(find.text('Detailed Logging'), findsOneWidget);
    expect(find.byType(SwitchListTile), findsNWidgets(2)); // Dark mode + Logging
  });

  testWidgets('toggles logging state', (tester) async {
    when(mockLoggingProvider.isLoggingEnabled).thenReturn(true);

    await tester.pumpWidget(buildTestWidget());
    await tester.pump();

    // Tap the switch
    await tester.tap(find.byType(SwitchListTile).last);

    // Verify toggle method called
    verify(mockLoggingProvider.toggleLogging()).called(1);
  });
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| StatefulWidget setState() | provider + ChangeNotifier | Established in codebase | Cleaner separation, testable state |
| Synchronous preference reads | Async factory load | Phase 6 (ThemeProvider) | Eliminates flash of wrong state |
| Service-owned state | Provider-owned state | Standard in project | Single source of truth, UI-driven |
| Logger only | logger + buffer | Phase 45 | Console output + backend transmission |

**Deprecated/outdated:**
- Direct SharedPreferences reads in build() methods (causes async errors, state flash)
- Multiple storage keys for related settings (use provider pattern)

## Open Questions

Things that couldn't be fully resolved:

1. **Should global error handlers respect logging toggle?**
   - What we know: FlutterError.onError and PlatformDispatcher.onError currently always log
   - What's unclear: Is error logging considered "opt-out-able" or always-on for debugging?
   - Recommendation: Respect toggle for consistency and user expectation of "no logging". Wrap error handler calls with enabled check.

2. **Should LoggingService maintain enabled state or query provider?**
   - What we know: Two options: (A) Provider updates service via setter, (B) Service queries provider
   - What's unclear: Which maintains better separation of concerns?
   - Recommendation: Option A (setter) - simpler, no circular dependency, service doesn't need context

3. **Default logging state: enabled or disabled?**
   - What we know: User hasn't opted in to diagnostics yet
   - What's unclear: Privacy vs. debugging value
   - Recommendation: Default ENABLED for pilot phase (LOG-05 says "user can toggle", implies logging is default). Can change to opt-in for production.

## Sources

### Primary (HIGH confidence)
- frontend/lib/providers/theme_provider.dart - Established persist-before-notify pattern
- frontend/lib/providers/provider_provider.dart - Established async factory load pattern
- frontend/lib/services/logging_service.dart - Existing singleton service structure
- frontend/lib/screens/settings_screen.dart - Existing UI patterns (SwitchListTile, Consumer, section structure)
- frontend/lib/main.dart - Provider initialization pattern on startup
- frontend/test/widget/settings_screen_test.dart - Existing widget test patterns
- frontend/pubspec.yaml - Confirmed all dependencies present (provider ^6.1.5+1, shared_preferences ^2.5.4, logger ^2.5.0)

### Secondary (MEDIUM confidence)
- .planning/STATE.md - Phase 45 established LoggingService singleton, Phase 46 established HTTP integration
- .planning/REQUIREMENTS.md - LOG-05: toggle in settings, SLOG-01: persist state
- .planning/ROADMAP.md - Success criteria: toggle appears, state persists, disabling stops capture

### Tertiary (LOW confidence)
- None - all findings from codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries present in pubspec.yaml, versions verified
- Architecture: HIGH - Patterns observed directly in codebase (ThemeProvider, ProviderProvider, SettingsScreen)
- Pitfalls: HIGH - Common issues documented in existing provider implementations

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days - stable patterns)
