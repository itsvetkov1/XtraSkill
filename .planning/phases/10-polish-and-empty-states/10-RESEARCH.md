# Phase 10: Polish & Empty States - Research

**Researched:** 2026-01-30
**Domain:** Flutter UI/UX - Empty States, Visual Polish, Date Formatting
**Confidence:** HIGH

## Summary

Phase 10 focuses on delivering professional empty states, home screen redesign, AI mode selection via ChoiceChips, and visual polish including consistent date formatting. The research confirms Flutter provides all necessary tools through Material 3 ChoiceChip widgets, the `intl` package for locale-aware date formatting, and the `timeago` package for relative time expressions.

Key findings:
- **Empty states**: Use consistent template (themed icon + encouraging message + filled CTA button) - no external packages needed
- **ChoiceChip for mode selection**: Flutter's built-in ChoiceChip supports Material 3 styling, works with Wrap widget for responsive layout
- **Date formatting**: Combine `intl` package (already in project) for absolute dates with `timeago` package for relative times
- **Message readability**: Adjust existing MessageBubble padding and font size - straightforward CSS-like changes
- **Thread preview text**: Standard `maxLines: 1` + `TextOverflow.ellipsis` pattern

**Primary recommendation:** Implement all features using Flutter's built-in Material 3 components plus `timeago` package (only new dependency). No architectural changes needed.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `flutter/material.dart` | SDK | ChoiceChip, Icons, Material 3 | Built-in, Material 3 compliant |
| `intl` | ^0.20.2 | Absolute date formatting (DateFormat.yMMMd) | Already in pubspec.yaml, ICU-compliant |
| `provider` | ^6.1.5+1 | State management for AuthProvider (display_name) | Already in project |

### Supporting (New)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `timeago` | ^3.7.1 | Relative time formatting ("5h ago", "yesterday") | POLISH-01 relative dates |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `timeago` | `get_time_ago` | timeago has more customization, larger community |
| `timeago` | `flutter_date_formatter` | timeago is simpler, more established |
| Custom relative time | Manual calculation | Error-prone, locale handling complex |

**Installation:**
```bash
cd frontend && flutter pub add timeago
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/
  utils/
    date_formatter.dart      # NEW: Centralized date formatting utilities
  widgets/
    empty_state.dart         # NEW: Reusable empty state widget
    mode_selector.dart       # NEW: ChoiceChip mode selector widget
  screens/
    home_screen.dart         # MODIFY: Redesign with user greeting + actions
    projects/
      project_list_screen.dart  # MODIFY: Update empty state to use widget
    threads/
      thread_list_screen.dart   # MODIFY: Add mode indicator, preview text
    conversation/
      conversation_screen.dart  # MODIFY: Add ChoiceChip mode selector
```

### Pattern 1: Centralized Date Formatting Utility
**What:** Single utility class handling both relative and absolute date formatting
**When to use:** Any date display in the app (threads, projects, messages)
**Example:**
```dart
// Source: intl package + timeago package
import 'package:intl/intl.dart';
import 'package:timeago/timeago.dart' as timeago;

class DateFormatter {
  /// Format date for display: relative for <7 days, absolute for older
  /// Implements POLISH-01 requirement
  static String format(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays < 7) {
      // Use timeago for relative: "2h ago", "4d ago", "Yesterday"
      return timeago.format(date);
    } else {
      // Use intl for absolute: "Jan 18, 2026"
      return DateFormat.yMMMd().format(date);
    }
  }

  /// Initialize timeago locales (call in main.dart)
  static void init() {
    // Default locale messages already loaded
    // Add more if needed: timeago.setLocaleMessages('fr', timeago.FrMessages());
  }
}
```

### Pattern 2: Reusable Empty State Widget
**What:** Consistent empty state template for all list screens
**When to use:** Projects list, threads list, documents list
**Example:**
```dart
// Source: Material Design empty state guidelines
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String buttonLabel;
  final VoidCallback onPressed;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    required this.buttonLabel,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            icon,
            size: 64,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            title,
            style: theme.textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: onPressed,
            icon: const Icon(Icons.add),
            label: Text(buttonLabel),
          ),
        ],
      ),
    );
  }
}
```

### Pattern 3: ChoiceChip Mode Selector with Wrap
**What:** Tappable mode selection replacing typed "A"/"B" responses
**When to use:** First message in conversation when AI asks for mode
**Example:**
```dart
// Source: Flutter ChoiceChip API + Wrap widget
class ModeSelector extends StatelessWidget {
  final String? selectedMode;
  final ValueChanged<String> onModeSelected;

  const ModeSelector({
    super.key,
    this.selectedMode,
    required this.onModeSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8.0,    // gap between adjacent chips
      runSpacing: 4.0, // gap between lines
      children: [
        ChoiceChip(
          label: const Text('Meeting Mode'),
          selected: selectedMode == 'meeting',
          onSelected: (_) => onModeSelected('Meeting Mode'),
          avatar: const Icon(Icons.groups, size: 18),
        ),
        ChoiceChip(
          label: const Text('Document Refinement'),
          selected: selectedMode == 'document',
          onSelected: (_) => onModeSelected('Document Refinement Mode'),
          avatar: const Icon(Icons.edit_document, size: 18),
        ),
      ],
    );
  }
}
```

### Anti-Patterns to Avoid
- **Hand-rolling relative time**: Don't calculate "5 days ago" manually - use timeago package
- **Hardcoded date strings**: Don't use "2026-01-30" format - use DateFormat for locale awareness
- **Inconsistent empty states**: Don't copy-paste empty state code - use reusable widget
- **Row for chips**: Don't use Row for ChoiceChips - use Wrap for responsive layout

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative time ("5h ago") | Manual Duration calculations | `timeago` package | Handles edge cases, localization, updates |
| Locale-aware dates | String interpolation | `DateFormat.yMMMd()` | ICU-compliant, handles locale differences |
| Text truncation | String.substring() | `maxLines` + `TextOverflow.ellipsis` | Responsive to container width |
| Mode selection UI | Custom toggle buttons | `ChoiceChip` widget | Material 3 compliant, accessible |
| Empty state layout | Custom Column each time | Reusable `EmptyState` widget | Consistency, maintenance |

**Key insight:** Flutter's Material 3 components and the intl ecosystem handle most UI polish requirements. Adding timeago is the only new dependency needed.

## Common Pitfalls

### Pitfall 1: Not Initializing Date Formatting Locales
**What goes wrong:** DateFormat throws "Locale not initialized" or shows wrong format
**Why it happens:** intl package requires async initialization for non-en_US locales
**How to avoid:** Call `initializeDateFormatting()` in main() before runApp()
**Warning signs:** Dates display incorrectly or app crashes on non-English devices

```dart
// main.dart
import 'package:intl/date_symbol_data_local.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting(); // Initialize all locales
  runApp(const MyApp());
}
```

### Pitfall 2: ChoiceChip Inside Row Overflows
**What goes wrong:** Chips overflow on narrow screens, causing RenderFlex error
**Why it happens:** Row doesn't wrap - it expects all children to fit
**How to avoid:** Always use Wrap widget for ChoiceChip collections
**Warning signs:** Yellow/black overflow stripes on small screens

### Pitfall 3: Empty State Not Showing After Delete
**What goes wrong:** User deletes last item but sees empty list, not empty state
**Why it happens:** Provider state check happens before list rebuild
**How to avoid:** Check `provider.items.isEmpty` in builder, not in initState
**Warning signs:** Empty list after delete operation, refresh shows empty state

### Pitfall 4: Home Screen Greeting Null Safety
**What goes wrong:** "Welcome back, null" displayed
**Why it happens:** AuthProvider.displayName can be null for users without display name
**How to avoid:** Use null coalescing: `displayName ?? email?.split('@').first ?? 'there'`
**Warning signs:** "null" text appearing in greeting

### Pitfall 5: Thread Mode Not Persisted
**What goes wrong:** Thread list can't show mode indicator because mode isn't stored
**Why it happens:** Thread model doesn't have mode field, mode is only in first message
**How to avoid:** Either add mode field to Thread model or parse from first AI message
**Warning signs:** Mode indicator can't be displayed without loading all messages

## Code Examples

Verified patterns from official sources:

### Date Formatting with intl Package
```dart
// Source: https://api.flutter.dev/flutter/package-intl_intl/DateFormat-class.html
import 'package:intl/intl.dart';

// Named constructor for locale-aware format
final formatted = DateFormat.yMMMd().format(DateTime.now()); // "Jan 30, 2026"

// With explicit locale
final formattedFr = DateFormat.yMMMd('fr').format(DateTime.now()); // "30 janv. 2026"

// Time formatting
final time = DateFormat.jm().format(DateTime.now()); // "5:08 PM"
```

### Relative Time with timeago Package
```dart
// Source: https://pub.dev/packages/timeago
import 'package:timeago/timeago.dart' as timeago;

final now = DateTime.now();
final fifteenAgo = now.subtract(const Duration(minutes: 15));
final twoHoursAgo = now.subtract(const Duration(hours: 2));
final threeDaysAgo = now.subtract(const Duration(days: 3));

print(timeago.format(fifteenAgo)); // "15 minutes ago"
print(timeago.format(twoHoursAgo)); // "about 2 hours ago"
print(timeago.format(threeDaysAgo)); // "3 days ago"

// Short format
print(timeago.format(twoHoursAgo, locale: 'en_short')); // "2h"
```

### ChoiceChip with Selection State
```dart
// Source: https://api.flutter.dev/flutter/material/ChoiceChip-class.html
int _selectedIndex = 0;

Wrap(
  spacing: 8.0,
  children: List<Widget>.generate(
    options.length,
    (int index) {
      return ChoiceChip(
        label: Text(options[index]),
        selected: _selectedIndex == index,
        onSelected: (bool selected) {
          setState(() {
            _selectedIndex = selected ? index : _selectedIndex;
          });
        },
      );
    },
  ).toList(),
)
```

### Text Truncation for Preview
```dart
// Source: Flutter Text widget documentation
Text(
  previewText,
  maxLines: 1,
  overflow: TextOverflow.ellipsis,
  style: theme.textTheme.bodySmall?.copyWith(
    color: theme.colorScheme.onSurfaceVariant,
  ),
)
```

### FilledButton for Empty State CTA
```dart
// Source: Material 3 Button styles
FilledButton.icon(
  onPressed: onCreatePressed,
  icon: const Icon(Icons.add),
  label: const Text('Create Project'),
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ElevatedButton | FilledButton | Flutter 3.0/Material 3 | Better visual hierarchy for CTAs |
| Manual Chip styling | ChoiceChip.elevated | Flutter 3.7 | Material 3 Filter chip compliance |
| Custom date formatting | DateFormat skeletons | intl 0.18+ | Automatic locale adaptation |
| Row for chips | Wrap widget | Always recommended | Responsive without overflow |

**Deprecated/outdated:**
- `RaisedButton`: Replaced by `ElevatedButton` (Flutter 2.0)
- `FlatButton`: Replaced by `TextButton` (Flutter 2.0)
- Custom chip implementations: Use Material 3 `ChoiceChip` instead

## Open Questions

Things that couldn't be fully resolved:

1. **Thread Mode Storage**
   - What we know: AI asks for mode in first message, user responds with "Meeting Mode" or "Document Refinement Mode"
   - What's unclear: Should we add a `mode` column to Thread model or parse from first user message?
   - Recommendation: Parse from messages for CONV-UI-03 (simpler, no migration). Consider mode column for future if needed.

2. **Message Preview Text Source**
   - What we know: POLISH-03 requires "first line of last message, truncated to 80 chars"
   - What's unclear: Should preview be last user message or last any message? How to handle multiline?
   - Recommendation: Use last message content, take first line only (split on newline), truncate at 80 chars with ellipsis

3. **Home Screen Recent Projects Count**
   - What we know: CONTEXT.md says "2-3 most recent projects as quick access cards"
   - What's unclear: Exactly 2, exactly 3, or responsive based on screen size?
   - Recommendation: Show up to 3, fewer on smaller screens via responsive layout

## Sources

### Primary (HIGH confidence)
- [Flutter ChoiceChip API](https://api.flutter.dev/flutter/material/ChoiceChip-class.html) - Widget documentation
- [Flutter DateFormat API](https://api.flutter.dev/flutter/package-intl_intl/DateFormat-class.html) - Date formatting documentation
- [timeago pub.dev](https://pub.dev/packages/timeago) - Package documentation
- [Flutter Wrap widget](https://api.flutter.dev/flutter/widgets/Wrap-class.html) - Layout documentation

### Secondary (MEDIUM confidence)
- [Flutter Material 3 Migration](https://docs.flutter.dev/release/breaking-changes/material-3-migration) - Migration guide
- [Empty State UX Examples](https://www.eleken.co/blog-posts/empty-state-ux) - Design patterns
- [Carbon Design System - Empty States](https://carbondesignsystem.com/patterns/empty-states-pattern/) - Enterprise patterns

### Tertiary (LOW confidence)
- Various Medium articles on Flutter best practices (patterns verified against official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing packages + one well-established addition (timeago)
- Architecture: HIGH - Patterns follow Flutter/Material 3 best practices
- Pitfalls: HIGH - Based on actual codebase review and documented issues
- Code examples: HIGH - Verified against official Flutter documentation

**Research date:** 2026-01-30
**Valid until:** 60 days (stable Flutter patterns, no breaking changes expected)
