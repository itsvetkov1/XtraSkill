# Phase 22: Frontend Provider UI - Research

**Researched:** 2026-01-31
**Domain:** Flutter provider selection and persistence, UI state management
**Confidence:** HIGH

## Summary

This phase adds LLM provider selection to the existing Flutter codebase. The work involves creating a new provider selector dropdown in Settings, persisting the selection with SharedPreferences (already used for theme), updating Thread model/service to handle `model_provider`, and adding a provider indicator widget in the conversation screen.

The codebase has established patterns for everything needed:
- **ThemeProvider pattern:** Load from SharedPreferences at startup, persist immediately on change, notify listeners
- **Settings screen structure:** Section headers with ListTile/SwitchListTile widgets
- **Thread model:** Already has JSON parsing, but needs `model_provider` field added
- **Conversation screen layout:** Column with error banner, messages, and ChatInput

**Primary recommendation:** Follow existing codebase patterns exactly. Create ProviderProvider modeled on ThemeProvider. Add dropdown in Settings using DropdownButtonFormField. Add indicator widget between message list and ChatInput.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shared_preferences | 2.5.4 | Persist provider setting | Already used for theme, proven pattern |
| provider | 6.1.5+1 | State management | Already used across entire app |
| flutter/material | SDK | UI components | DropdownButtonFormField, Row, Icon |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dio | 5.9.0 | HTTP client | Thread service API calls (already used) |

### No New Dependencies Needed

All functionality is achievable with existing dependencies. No additional packages required.

## Architecture Patterns

### Recommended Project Structure
```
lib/
├── providers/
│   ├── theme_provider.dart      # Reference pattern for persistence
│   └── provider_provider.dart   # NEW: LLM provider selection
├── models/
│   └── thread.dart              # UPDATE: Add modelProvider field
├── services/
│   └── thread_service.dart      # UPDATE: Pass model_provider on create
├── screens/
│   ├── settings_screen.dart     # UPDATE: Add provider dropdown
│   └── conversation/
│       ├── conversation_screen.dart  # UPDATE: Add indicator widget
│       └── widgets/
│           └── provider_indicator.dart  # NEW: Model indicator widget
└── core/
    └── constants.dart           # NEW or UPDATE: Provider colors/names
```

### Pattern 1: Provider State Management (from ThemeProvider)
**What:** ChangeNotifier with SharedPreferences persistence
**When to use:** Any user preference that survives app restart
**Example:**
```dart
// Source: frontend/lib/providers/theme_provider.dart
class ProviderProvider extends ChangeNotifier {
  final SharedPreferences _prefs;
  String _selectedProvider;

  static const String _providerKey = 'defaultLlmProvider';

  ProviderProvider(this._prefs, {String? initialProvider})
      : _selectedProvider = initialProvider ?? 'anthropic';

  static Future<ProviderProvider> load(SharedPreferences prefs) async {
    final savedProvider = prefs.getString(_providerKey) ?? 'anthropic';
    return ProviderProvider(prefs, initialProvider: savedProvider);
  }

  String get selectedProvider => _selectedProvider;

  Future<void> setProvider(String provider) async {
    _selectedProvider = provider;
    await _prefs.setString(_providerKey, provider);
    notifyListeners();
  }
}
```

### Pattern 2: Settings Section Layout (from SettingsScreen)
**What:** Section header + ListTile/SwitchListTile pattern
**When to use:** All settings items
**Example:**
```dart
// Source: frontend/lib/screens/settings_screen.dart
_buildSectionHeader(context, 'Preferences'),  // Existing pattern
ListTile(
  title: const Text('Default AI Provider'),
  subtitle: Consumer<ProviderProvider>(
    builder: (context, provider, _) {
      return DropdownButtonFormField<String>(
        value: provider.selectedProvider,
        decoration: const InputDecoration(border: InputBorder.none),
        items: [
          DropdownMenuItem(value: 'anthropic', child: Text('Claude')),
          DropdownMenuItem(value: 'google', child: Text('Gemini')),
          DropdownMenuItem(value: 'deepseek', child: Text('DeepSeek')),
        ],
        onChanged: (value) => provider.setProvider(value!),
      );
    },
  ),
),
```

### Pattern 3: Model Field Addition (from Thread)
**What:** Add optional field with JSON parsing
**When to use:** Extending existing models
**Example:**
```dart
// Source: frontend/lib/models/thread.dart pattern
class Thread {
  // ... existing fields
  final String? modelProvider;  // NEW field

  factory Thread.fromJson(Map<String, dynamic> json) {
    return Thread(
      // ... existing parsing
      modelProvider: json['model_provider'] as String?,  // NEW
    );
  }
}
```

### Pattern 4: Provider Indicator Widget
**What:** Compact row with icon + text, positioned above input
**When to use:** Model indicator below messages, above input
**Example:**
```dart
// NEW widget following codebase widget patterns
class ProviderIndicator extends StatelessWidget {
  final String provider;

  const ProviderIndicator({super.key, required this.provider});

  @override
  Widget build(BuildContext context) {
    final config = _getProviderConfig(provider);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(config.icon, size: 16, color: config.color),
          const SizedBox(width: 8),
          Text(config.displayName, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
```

### Anti-Patterns to Avoid
- **Hardcoded provider logic scattered everywhere:** Centralize in ProviderProvider and constants
- **Not using existing SharedPreferences instance:** Reuse the instance created in main()
- **Silent failures on persistence:** ThemeProvider pattern handles errors gracefully
- **Breaking existing Thread model consumers:** Model change must be backward-compatible

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Provider persistence | Custom file storage | SharedPreferences | Already in project, proven pattern |
| Dropdown UI | Custom selector | DropdownButtonFormField | Material standard, handles touch/keyboard |
| State propagation | Manual callback chains | ChangeNotifier + Consumer | Existing app architecture |
| Main initialization | Conditional provider init | ThemeProvider.load() pattern | Avoids state flash on startup |

**Key insight:** The codebase already solves every architectural problem. This phase is about applying existing patterns to a new domain.

## Common Pitfalls

### Pitfall 1: Not Loading Provider at App Startup
**What goes wrong:** Flash of default provider or race condition
**Why it happens:** Provider loaded after widgets build
**How to avoid:** Load in main() before runApp(), pass to MultiProvider like ThemeProvider
**Warning signs:** Provider resets on hot restart, brief "Claude" flash when user selected DeepSeek

### Pitfall 2: Thread Model Breaking Existing Code
**What goes wrong:** Existing thread list/detail screens crash
**Why it happens:** Adding required field or breaking fromJson
**How to avoid:** Add field as nullable, provide default in backend response parsing
**Warning signs:** "NoSuchMethodError" or "type null is not a subtype" errors

### Pitfall 3: Forgetting to Pass model_provider on Thread Create
**What goes wrong:** New threads always use "anthropic" regardless of setting
**Why it happens:** Thread creation API call doesn't include model_provider parameter
**How to avoid:** Thread service createThread() must accept and pass provider
**Warning signs:** New threads ignore user's default provider selection

### Pitfall 4: Indicator Not Updating on Thread Load
**What goes wrong:** Indicator shows wrong provider or is stale
**Why it happens:** Not reading from thread.modelProvider, using global default
**How to avoid:** Conversation screen gets provider from thread object, not ProviderProvider
**Warning signs:** Opening old thread shows current default instead of bound provider

### Pitfall 5: Dark Mode Color Contrast
**What goes wrong:** Provider colors illegible in dark theme
**Why it happens:** Using exact same colors for light and dark
**How to avoid:** Define separate dark mode variants or adjust saturation/brightness
**Warning signs:** Low contrast ratio, colors look washed out or too bright

## Code Examples

Verified patterns from existing codebase:

### SharedPreferences Initialization (main.dart pattern)
```dart
// Source: frontend/lib/main.dart lines 38-41
final prefs = await SharedPreferences.getInstance();
final themeProvider = await ThemeProvider.load(prefs);
final providerProvider = await ProviderProvider.load(prefs);  // ADD
```

### MultiProvider Registration (main.dart pattern)
```dart
// Source: frontend/lib/main.dart lines 107-116
MultiProvider(
  providers: [
    ChangeNotifierProvider.value(value: widget.themeProvider),
    ChangeNotifierProvider.value(value: widget.providerProvider),  // ADD
    // ... existing providers
  ],
  // ...
)
```

### Settings Section Pattern (settings_screen.dart)
```dart
// Source: frontend/lib/screens/settings_screen.dart lines 79-88
// Appearance Section
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
```

### Thread Creation with Provider (thread_service.dart update)
```dart
// Source: frontend/lib/services/thread_service.dart createThread pattern
Future<Thread> createThread(String projectId, String? title, String? provider) async {
  // ...
  final response = await _dio.post(
    '$_baseUrl/api/projects/$projectId/threads',
    options: Options(headers: headers),
    data: {
      if (title != null && title.isNotEmpty) 'title': title,
      if (provider != null) 'model_provider': provider,  // ADD
    },
  );
  // ...
}
```

### Conversation Screen Column Structure (conversation_screen.dart)
```dart
// Source: frontend/lib/screens/conversation/conversation_screen.dart lines 173-204
body: Column(
  children: [
    // Error banner
    if (provider.error != null)
      MaterialBanner(...),

    // Message list
    Expanded(
      child: _buildMessageList(provider),
    ),

    // NEW: Provider indicator - insert here
    ProviderIndicator(provider: provider.thread?.modelProvider ?? 'anthropic'),

    // Chat input
    ChatInput(...),
  ],
),
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A - new feature | ChangeNotifier + SharedPreferences | Established | Use existing patterns |

**Current best practices in this codebase:**
- ThemeProvider pattern for persisted user preferences
- Consumer widgets for reactive updates
- Immediate persistence before notifyListeners()
- Error-resilient preference loading with defaults

## Open Questions

Things that couldn't be fully resolved:

1. **Provider Icons**
   - What we know: User wants icon + text, icon should be provider-specific
   - What's unclear: Whether to use MaterialIcons, custom SVGs, or text abbreviations
   - Recommendation: Use MaterialIcons for MVP (Icons.smart_toy for Claude, Icons.auto_awesome for Gemini, Icons.psychology for DeepSeek), can upgrade to brand assets later

2. **Thread List Display**
   - What we know: Thread model will have modelProvider field
   - What's unclear: Whether to show provider indicator in thread list items
   - Recommendation: Not in scope per requirements (UI-01 is "below chat window" only), can add later if desired

## Sources

### Primary (HIGH confidence)
- `frontend/lib/providers/theme_provider.dart` - Reference implementation for SharedPreferences pattern
- `frontend/lib/screens/settings_screen.dart` - Settings section structure and Consumer usage
- `frontend/lib/models/thread.dart` - Thread model structure
- `frontend/lib/services/thread_service.dart` - API call patterns
- `frontend/lib/screens/conversation/conversation_screen.dart` - Conversation UI structure
- `frontend/lib/main.dart` - App initialization and provider registration

### Secondary (MEDIUM confidence)
- `backend/app/routes/threads.py` - Backend API contract (model_provider field, valid values)
- Flutter Material Components documentation - DropdownButtonFormField standard usage

### Tertiary (LOW confidence)
- None - all findings verified against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using only existing dependencies
- Architecture: HIGH - Following established codebase patterns exactly
- Pitfalls: HIGH - Based on code review of existing implementations

**Research date:** 2026-01-31
**Valid until:** Indefinite - based on stable codebase patterns, not external libraries

---

## Provider Configuration Reference

From CONTEXT.md user decisions:

| Provider | Display Name | Color (Light) | Backend Value |
|----------|--------------|---------------|---------------|
| Claude | Claude | #D97706 (Anthropic orange) | anthropic |
| Gemini | Gemini | #4285F4 (Google blue) | google |
| DeepSeek | DeepSeek | #00B8D4 (Teal/cyan) | deepseek |

**Color application:** Icon tint only, text stays neutral (per user decision)
