# Phase 6: Theme Management Foundation - Research

**Researched:** 2026-01-29
**Domain:** Flutter Material Design 3 theme management with persistent preferences
**Confidence:** HIGH

## Summary

Flutter's theme management in 2026 uses Material Design 3 with `ColorScheme.fromSeed()` for automatic color palette generation. The standard stack for theme persistence uses `shared_preferences` (version 2.5.4+) with ChangeNotifier-based state management. The critical challenge is preventing white flash on dark mode startup, solved by loading theme preferences in an async `main()` before `runApp()` initialization.

Material 3 defaults to dark gray (`#121212`) instead of pure black (`#000000`) for reduced eye strain, with surface tint colors replacing elevation shadows. The architecture uses a ThemeProvider with ChangeNotifier pattern, persisting theme mode immediately on toggle using SharedPreferences, and loading it synchronously before MaterialApp renders.

**Primary recommendation:** Use `shared_preferences` 2.5.4+ with async initialization in `main()`, Material 3's `ColorScheme.fromSeed()` with custom seed color, and ChangeNotifier pattern for reactive theme switching with zero flickering.

## Standard Stack

The established libraries/tools for Flutter theme management:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `shared_preferences` | 2.5.4+ | Persistent key-value storage | Flutter's official plugin for cross-platform local storage, wraps NSUserDefaults (iOS) and SharedPreferences (Android) |
| `provider` | 6.x | State management | Official Flutter recommendation for simple state management, created by Remi Rousselet, ideal for theme switching |
| Material 3 | Built-in (Flutter 3.16+) | Design system | Default since Flutter 3.16, `useMaterial3: true` by default |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `adaptive_theme` | 3.6.0+ | Theme management helper | Alternative to custom implementation, handles persistence and initialization automatically |
| `flex_color_scheme` | 7.x | Advanced theming | Only if custom color schemes beyond Material 3 seed colors needed (DEFERRED - out of scope) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `shared_preferences` | `flutter_secure_storage` | Secure storage is overkill for theme preference (adds encryption overhead, theme choice isn't sensitive) |
| Provider | Riverpod | Riverpod is "Provider 2.0" with better compile-time safety, but Provider is simpler for single-value theme state |
| Custom implementation | `adaptive_theme` package | Package provides built-in initialization and flickering prevention, but adds dependency and less control |

**Installation:**
```bash
flutter pub add shared_preferences
flutter pub add provider
```

## Architecture Patterns

### Recommended Project Structure
```
lib/
├── main.dart                    # Async initialization, load theme before runApp()
├── providers/
│   └── theme_provider.dart      # ChangeNotifier for theme state management
├── theme/
│   ├── app_theme.dart          # ThemeData definitions (light and dark)
│   └── theme_constants.dart    # Color constants, seed colors
└── screens/
    └── settings_screen.dart    # Settings page with theme toggle
```

### Pattern 1: Async Main Initialization
**What:** Load SharedPreferences before MaterialApp renders to prevent white flash
**When to use:** Always - required for SET-06 (prevent white flash on dark mode)
**Example:**
```dart
// Source: Flutter Official Docs - https://docs.flutter.dev/cookbook/persistence/key-value
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final isDarkMode = prefs.getBool('isDarkMode') ?? false; // Default to light

  runApp(
    ChangeNotifierProvider(
      create: (_) => ThemeProvider(isDarkMode),
      child: const MyApp(),
    ),
  );
}
```

### Pattern 2: ThemeProvider with ChangeNotifier
**What:** Reactive theme state management that notifies listeners on toggle
**When to use:** Always - standard pattern for theme switching
**Example:**
```dart
// Source: Material Design Docs + Flutter Provider best practices
class ThemeProvider extends ChangeNotifier {
  bool _isDarkMode;
  final SharedPreferences _prefs;

  ThemeProvider(this._isDarkMode, this._prefs);

  bool get isDarkMode => _isDarkMode;

  ThemeMode get themeMode => _isDarkMode ? ThemeMode.dark : ThemeMode.light;

  Future<void> toggleTheme() async {
    _isDarkMode = !_isDarkMode;
    await _prefs.setBool('isDarkMode', _isDarkMode); // Persist immediately
    notifyListeners(); // Trigger rebuild
  }
}
```

### Pattern 3: Material 3 ColorScheme.fromSeed
**What:** Generate harmonious color palette from single seed color
**When to use:** Always for Material 3 - replaces manual color definitions
**Example:**
```dart
// Source: https://api.flutter.dev/flutter/material/ColorScheme/ColorScheme.fromSeed.html
class AppTheme {
  static const Color seedColor = Color(0xFF1976D2); // Blue (#1976D2)

  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: seedColor,
      brightness: Brightness.light,
    ),
  );

  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: seedColor,
      brightness: Brightness.dark,
    ).copyWith(
      // Material 3 default is #121212 for dark surface (good - matches user decision)
      surface: const Color(0xFF121212), // Explicit for documentation
    ),
  );
}
```

### Pattern 4: MaterialApp Theme Configuration
**What:** Wire theme provider to MaterialApp with both light and dark themes
**When to use:** Always - standard MaterialApp setup
**Example:**
```dart
// Source: https://api.flutter.dev/flutter/material/MaterialApp/darkTheme.html
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);

    return MaterialApp(
      title: 'Business Analyst Assistant',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeProvider.themeMode, // Reactive to provider changes
      home: const HomeScreen(),
    );
  }
}
```

### Pattern 5: Settings Page Toggle
**What:** SwitchListTile for theme toggle in settings page
**When to use:** Always - user decision specifies Settings page placement
**Example:**
```dart
// Source: https://api.flutter.dev/flutter/material/SwitchListTile-class.html
class SettingsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          SwitchListTile(
            title: const Text('Dark Mode'),
            value: themeProvider.isDarkMode,
            onChanged: (_) => themeProvider.toggleTheme(), // Instant toggle
          ),
        ],
      ),
    );
  }
}
```

### Anti-Patterns to Avoid
- **Hardcoding theme colors in widgets:** Use `Theme.of(context).colorScheme.primary` instead of `Color(0xFF1976D2)` directly
- **Using `setState()` at root level:** Rebuilds entire tree unnecessarily; use Provider with Consumer for scoped rebuilds
- **Delaying SharedPreferences persistence:** Save immediately on toggle, not on app shutdown (app may crash)
- **Using deprecated `background` color:** Use `surface` instead (deprecated after Flutter 3.18.0)
- **Setting `useMaterial3: false`:** Material 3 is default since Flutter 3.16, reverting is deprecated and limits features

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Theme persistence | Custom file I/O or database storage | `shared_preferences` package | Cross-platform abstraction (NSUserDefaults, Android SharedPreferences, localStorage), platform-specific optimizations, automatic key prefixing on web |
| Color palette generation | Manually defining all 40+ Material colors | `ColorScheme.fromSeed()` | Generates accessible, harmonious palettes per Material 3 spec, ensures WCAG contrast ratios |
| Theme state management | Global variables or singletons | Provider with ChangeNotifier | Reactive updates, widget tree integration, testable with mocks |
| Preventing startup flicker | Splash screen delays or loading indicators | Async `main()` with early preference load | Loads correct theme before first frame, zero visual artifacts |
| Surface elevation in dark mode | Manual shadow calculations | Material 3 surface tint | Automatic elevation indication via surface tint color (replaces shadows in Material 3) |

**Key insight:** Flutter's theme system is deeply integrated with the widget tree and rendering pipeline. Custom solutions miss platform-specific optimizations (like web localStorage key prefixing, iOS plist caching, Android XML parsing) and fail to handle edge cases (isolate communication, configuration changes, hot reload).

## Common Pitfalls

### Pitfall 1: White Flash on Dark Mode Startup
**What goes wrong:** App renders with light theme briefly, then switches to dark theme, causing jarring white flash
**Why it happens:** SharedPreferences loads asynchronously after MaterialApp renders default theme
**How to avoid:**
- Make `main()` async
- Call `WidgetsFlutterBinding.ensureInitialized()` before async operations
- Load theme preference with `await SharedPreferences.getInstance()` before `runApp()`
- Pass loaded preference to ThemeProvider constructor
**Warning signs:** Users report "white flash when opening app in dark mode"

**Source:** [Adaptive Theme Package Documentation](https://pub.dev/packages/adaptive_theme), [Flutter Theme Persistence Repository](https://github.com/khalilify/flutter-theme-persistence)

### Pitfall 2: Not Persisting Immediately on Toggle
**What goes wrong:** User toggles theme, app crashes or is force-closed, theme preference lost
**Why it happens:** Delaying `prefs.setBool()` until app shutdown or using debouncing
**How to avoid:** Call `await prefs.setBool('isDarkMode', value)` immediately in toggle method before `notifyListeners()`
**Warning signs:** Theme resets to default after app force-close or crash

**Source:** User decision in 06-CONTEXT.md (Persistence Timing: "Save theme preference immediately on toggle")

### Pitfall 3: Ignoring System Preference After User Choice
**What goes wrong:** User selects dark mode in app, OS switches to light mode, app switches too (overriding user's explicit choice)
**Why it happens:** Using `ThemeMode.system` without tracking user's explicit preference
**How to avoid:**
- Store user's explicit choice in SharedPreferences
- Only use `ThemeMode.system` if no stored preference exists (first launch)
- After user toggles once, ignore OS changes
**Warning signs:** Users complain "app theme changes when I don't want it to"

**Source:** User decision in 06-CONTEXT.md (System Preference Changes: "Ignore OS theme changes after app launch")

### Pitfall 4: Using Pure Black (#000000) for Dark Mode
**What goes wrong:** Dark theme causes eye strain during long sessions, looks harsh
**Why it happens:** Assuming darker = better, or copying iOS defaults
**How to avoid:** Use Material 3 default `#121212` (dark gray) for surface color
**Warning signs:** Users report eye strain, request "less harsh dark mode"

**Source:** [Material Design Dark Theme Guidelines](https://m2.material.io/design/color/dark-theme.html), [In the Spotlight – Dark UI Design Principles](https://www.toptal.com/designers/ui/dark-ui-design)

**Material Design rationale:** Dark gray reduces contrast for bright imagery/animations, allows shadows/elevation to be visible, reduces eye strain vs. pure black

### Pitfall 5: Hardcoding Theme Data Throughout Widget Tree
**What goes wrong:** Changing colors requires updating hundreds of files, inconsistencies emerge
**Why it happens:** Using `Color(0xFF1976D2)` directly in widgets instead of theme system
**How to avoid:**
- Define colors in `AppTheme` class only
- Access via `Theme.of(context).colorScheme.primary`
- Use theme properties: `primaryColor`, `onPrimary`, `surface`, etc.
**Warning signs:** "Find in files" shows color hex codes scattered across project

**Source:** [Best Practices for Flutter Theme Data](https://vocal.media/journal/best-practices-for-flutter-theme-data)

### Pitfall 6: Over-calling notifyListeners()
**What goes wrong:** Sluggish performance, unnecessary rebuilds, janky animations
**Why it happens:** Calling `notifyListeners()` multiple times in quick succession or for every intermediate state
**How to avoid:**
- Call once per logical state change (after persistence completes)
- Use conditional checks: only notify if value actually changed
- Place Consumer widgets deep in tree to limit rebuild scope
**Warning signs:** Frame drops when toggling theme, profiler shows excessive rebuilds

**Source:** [Flutter ChangeNotifier Performance Optimization](https://www.dhiwise.com/post/fluidstate-management-with-flutter-changenotifier)

### Pitfall 7: Not Handling SharedPreferences Failures
**What goes wrong:** App crashes when disk full, permissions denied, or storage corrupted
**Why it happens:** Assuming `SharedPreferences.getInstance()` and `setBool()` always succeed
**How to avoid:**
- Wrap SharedPreferences calls in try-catch
- Provide fallback: default to light theme if load fails
- Log errors for debugging
- Consider retry logic for save failures
**Warning signs:** Crash reports with "PlatformException" from shared_preferences

**Source:** [Flutter SharedPreferences Complete Guide](https://medium.com/easy-flutter/shared-preferences-in-flutter-a-complete-guide-ed70e34d37b6)

### Pitfall 8: Web-Specific localStorage Visibility
**What goes wrong:** Security-conscious users/enterprises reject app seeing theme preference in browser DevTools
**Why it happens:** Flutter web uses browser localStorage, visible in F12 Developer Tools
**How to avoid:**
- Awareness: theme preference is NOT sensitive data (not a real security issue)
- Document this behavior if enterprises raise concerns
- Never store sensitive data in SharedPreferences (use `flutter_secure_storage` for secrets)
**Warning signs:** Enterprise users flag "can see app data in browser"

**Source:** [Flutter SharedPreferences: The Simple Guide to Local Storage on Web](https://medium.com/@BolgerCarol/flutters-shared-preferences-the-simple-guide-to-local-storage-on-mobile-and-web-21a5c5dc08b4)

## Code Examples

Verified patterns from official sources:

### Complete ThemeProvider Implementation
```dart
// Source: Provider pattern from https://docs.flutter.dev/data-and-backend/state-mgmt/simple
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeProvider extends ChangeNotifier {
  static const String _themeKey = 'isDarkMode';

  bool _isDarkMode;
  final SharedPreferences _prefs;

  ThemeProvider(this._prefs, {bool? initialDarkMode})
      : _isDarkMode = initialDarkMode ?? false;

  bool get isDarkMode => _isDarkMode;

  ThemeMode get themeMode => _isDarkMode ? ThemeMode.dark : ThemeMode.light;

  /// Toggle theme and persist immediately (SET-04, user decision: immediate persistence)
  Future<void> toggleTheme() async {
    _isDarkMode = !_isDarkMode;

    try {
      await _prefs.setBool(_themeKey, _isDarkMode);
    } catch (e) {
      // Log error but don't block UI (user sees toggle, background save failed)
      debugPrint('Failed to persist theme preference: $e');
      // Could show SnackBar here if desired, but user decision: no visual feedback
    }

    notifyListeners();
  }

  /// Load theme preference from SharedPreferences
  static Future<ThemeProvider> load(SharedPreferences prefs) async {
    final isDarkMode = prefs.getBool(_themeKey) ?? false; // Default to light (user decision)
    return ThemeProvider(prefs, initialDarkMode: isDarkMode);
  }
}
```

### Async Main with Theme Loading
```dart
// Source: https://docs.flutter.dev/cookbook/persistence/key-value
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() async {
  // Required for plugin initialization before runApp()
  WidgetsFlutterBinding.ensureInitialized();

  // Load SharedPreferences (prevents white flash - SET-06)
  final prefs = await SharedPreferences.getInstance();
  final themeProvider = await ThemeProvider.load(prefs);

  runApp(
    ChangeNotifierProvider.value(
      value: themeProvider,
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<ThemeProvider>(
      builder: (context, themeProvider, child) {
        return MaterialApp(
          title: 'Business Analyst Assistant',
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: themeProvider.themeMode, // Reactive to provider
          home: const HomeScreen(),
        );
      },
    );
  }
}
```

### Material 3 Theme Definition
```dart
// Source: https://api.flutter.dev/flutter/material/ColorScheme/ColorScheme.fromSeed.html
import 'package:flutter/material.dart';

class AppTheme {
  // User decision: Blue accent (#1976D2 range)
  static const Color seedColor = Color(0xFF1976D2);

  static ThemeData get lightTheme {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: seedColor,
      brightness: Brightness.light,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,

      // User decision: subtle shadows only (no borders)
      cardTheme: CardTheme(
        elevation: 2, // Soft drop shadow
        shadowColor: Colors.black.withOpacity(0.1),
        surfaceTintColor: Colors.transparent, // Disable tint if desired
      ),
    );
  }

  static ThemeData get darkTheme {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: seedColor,
      brightness: Brightness.dark,
    ).copyWith(
      // Material 3 default is already #121212, but explicit for clarity
      // User decision: Dark gray (#121212-#1E1E1E range), NOT pure black
      surface: const Color(0xFF121212),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,

      // User decision: subtle surface elevation using Material 3 tint approach
      // Material 3 automatically applies surface tint for elevation
      cardTheme: const CardTheme(
        elevation: 2, // Lighter surface via tint, not shadow
        // surfaceTint automatically applied by Material 3
      ),
    );
  }
}
```

### Settings Page with Theme Toggle
```dart
// Source: https://api.flutter.dev/flutter/material/SwitchListTile-class.html
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        children: [
          // User decision: Simple label "Dark Mode" with switch, no icons
          Consumer<ThemeProvider>(
            builder: (context, themeProvider, child) {
              return SwitchListTile(
                title: const Text('Dark Mode'),
                value: themeProvider.isDarkMode,
                // User decision: Instant theme switch, no animation
                onChanged: (_) => themeProvider.toggleTheme(),
              );
            },
          ),
          // Other settings...
        ],
      ),
    );
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `ThemeData` color definitions | `ColorScheme.fromSeed()` | Flutter 3.0 (2022), default since 3.16 (2023) | Automatic accessible palettes, reduces 200+ lines of theme code to ~10 |
| Elevation shadows in dark mode | Surface tint colors | Material 3 (Flutter 3.0+) | Better visual hierarchy without harsh shadows, power savings on OLED |
| `background` color role | `surface` color role | Deprecated Flutter 3.18.0 (2024) | Simplified color system, `surface` replaces both `background` and `canvas` |
| `applyElevationOverlayColor` | `surfaceTintColor` | Material 3 migration | Explicit control over elevation indication, aligns with Material 3 spec |
| `SharedPreferences` (legacy API) | `SharedPreferencesAsync` | Version 2.3.0 (2024) | Eliminates initialization delay, direct platform calls, better isolate safety |
| Riverpod/BLoC for simple theme | Provider + ChangeNotifier | Always valid | Riverpod is "Provider 2.0" but Provider remains simpler for single-value state (theme toggle) |

**Deprecated/outdated:**
- **`ThemeData.background` and `ThemeData.onBackground`**: Deprecated after v3.18.0, use `surface` and `onSurface` instead
- **`applyElevationOverlayColor` in Material 3**: Ignored when `useMaterial3: true`, replaced by `surfaceTintColor`
- **`ThemeMode.system` as default without user override**: Modern pattern: respect system on first launch, then honor user's explicit choice

## Open Questions

Things that couldn't be fully resolved:

1. **SharedPreferencesAsync vs. Legacy API**
   - What we know: `SharedPreferencesAsync` is newer (2.3.0+), eliminates initialization, recommended for new projects
   - What's unclear: Migration path if starting with legacy API, performance differences in practice, testing support maturity
   - Recommendation: Start with legacy `SharedPreferences.getInstance()` (proven, well-documented), migrate to async API if initialization delay becomes measurable issue

2. **Surface Tint Intensity Control**
   - What we know: Material 3 automatically applies surface tint for elevation, can disable with `Colors.transparent`
   - What's unclear: Fine-grained control over tint opacity per elevation level
   - Recommendation: Use default Material 3 behavior (user decision: "Material Design 3 elevation approach"), disable tint entirely if too pronounced (`surfaceTintColor: Colors.transparent`)

3. **Web-Specific localStorage Limits**
   - What we know: Web uses browser localStorage (5-10MB typical limit), single key-value (theme) is negligible (~10 bytes)
   - What's unclear: Browser-specific quota enforcement behavior, what happens if localStorage is disabled (privacy mode)
   - Recommendation: Handle `SharedPreferences.getInstance()` failure gracefully (default to light theme), acceptable edge case

4. **Testing setMockInitialValues Limitations**
   - What we know: `SharedPreferences.setMockInitialValues()` can only be called once per test suite
   - What's unclear: Best practices for multi-test scenarios requiring different initial values
   - Recommendation: Use test groups with single `setUpAll()`, or mock SharedPreferences with mockito/mocktail for complex scenarios

## Sources

### Primary (HIGH confidence)
- [Flutter Official Docs: SharedPreferences Cookbook](https://docs.flutter.dev/cookbook/persistence/key-value) - Key-value persistence patterns
- [Flutter API: MaterialApp.darkTheme](https://api.flutter.dev/flutter/material/MaterialApp/darkTheme.html) - Theme configuration
- [Flutter API: ColorScheme.fromSeed](https://api.flutter.dev/flutter/material/ColorScheme/ColorScheme.fromSeed.html) - Material 3 color generation
- [Flutter API: ColorScheme.dark](https://api.flutter.dev/flutter/material/ColorScheme/ColorScheme.dark.html) - Default dark color values
- [Flutter Docs: Material 3 Migration](https://docs.flutter.dev/release/breaking-changes/material-3-migration) - Surface tint, elevation changes
- [Flutter Docs: Simple State Management](https://docs.flutter.dev/data-and-backend/state-mgmt/simple) - Provider + ChangeNotifier pattern
- [pub.dev: shared_preferences 2.5.4](https://pub.dev/packages/shared_preferences) - Current version, API changes
- [pub.dev: adaptive_theme](https://pub.dev/packages/adaptive_theme) - Flickering prevention patterns

### Secondary (MEDIUM confidence)
- [Material Design: Dark Theme Guidelines](https://m2.material.io/design/color/dark-theme.html) - #121212 rationale, design principles (verified across multiple sources)
- [Mastering Material Design 3: Complete Guide to Theming in Flutter](https://www.christianfindlay.com/blog/flutter-mastering-material-design3) - Comprehensive Material 3 theming overview
- [Complete Flutter Guide: Dark Mode Implementation](https://medium.com/@amazing_gs/complete-flutter-guide-how-to-implement-dark-mode-dynamic-theming-and-theme-switching-ddabaef48d5a) - Theme switching patterns
- [DHiWise: Flutter SharedPreferences Guide](https://www.dhiwise.com/post/optimize-app-development-using-flutter-sharedpreferences) - Best practices, singleton pattern
- [Flutter Provider State Management for Optimal Performance](https://www.dhiwise.com/post/achieving-optimal-performance-with-flutter-provider-state-management) - Consumer optimization, notifyListeners best practices
- [Mocking SharedPreferences in Flutter Unit Tests](https://blog.victoreronmosele.com/mocking-shared-preferences-flutter) - Testing patterns

### Tertiary (LOW confidence - community guidance)
- [Best Practices for Flutter Theme Data](https://vocal.media/journal/best-practices-for-flutter-theme-data) - Hardcoding pitfalls (general advice, not Flutter-specific source)
- [The Ultimate Guide to Flutter State Management in 2026](https://medium.com/@satishparmarparmar486/the-ultimate-guide-to-flutter-state-management-in-2026-from-setstate-to-bloc-riverpod-561192c31e1c) - Riverpod vs Provider landscape (opinion piece)
- [In the Spotlight: Dark UI Design Principles](https://www.toptal.com/designers/ui/dark-ui-design) - General dark mode UX guidance (not Flutter-specific)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Flutter packages with stable APIs, Material 3 is built-in default
- Architecture: HIGH - Patterns verified from official Flutter docs and API references
- Pitfalls: MEDIUM to HIGH - White flash and persistence pitfalls verified from multiple sources, localStorage visibility is web platform fact, performance guidance from Flutter team

**Research date:** 2026-01-29
**Valid until:** ~60 days (stable domain - Material 3 and shared_preferences are mature, slow-moving APIs)
