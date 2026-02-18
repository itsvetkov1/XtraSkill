# Phase 67: Skill Info Popup - Research

**Researched:** 2026-02-18
**Domain:** Flutter Material Design 3 dialog patterns, card interaction, and event handling
**Confidence:** HIGH

## Summary

Phase 67 adds an info button to each skill card that displays detailed skill information in a popup. The phase requires integrating an info button into the existing `SkillCard` widget without interfering with card selection, showing skill metadata in a readable dialog, and ensuring responsive layout across mobile and desktop.

The standard Flutter Material Design 3 pattern for this use case is: **IconButton with info_outline icon → showDialog → AlertDialog**. This provides built-in Material 3 theming, accessibility via tooltips, and responsive layout handling. The key technical challenge is event handling — preventing the info button tap from triggering the card's onTap selection callback.

**Primary recommendation:** Add `IconButton(icon: Icons.info_outline)` to SkillCard, use `showDialog()` to display skill details in `AlertDialog`, and prevent tap propagation using a wrapping `GestureDetector` with an empty `onTap` on the info button.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFO-01 | Each skill in the browser has an info button | IconButton widget with Icons.info_outline positioned in card header |
| INFO-02 | Info button opens a popup/balloon showing the skill's description and features | showDialog() with AlertDialog containing full description and feature list |
| INFO-03 | User can dismiss the info popup and return to the skill browser | AlertDialog with action button and barrierDismissible: true (tap outside to dismiss) |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flutter/material.dart | 3.9.2 (SDK) | AlertDialog, showDialog, IconButton | Built-in Material Design 3 implementation with automatic theming |
| Icons.info_outline | Material Icons | Info button icon | Material Design standard for "additional information" affordance |

### Supporting

No additional packages required — all functionality available in Flutter SDK.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AlertDialog | Custom Dialog | AlertDialog provides M3 theming out-of-box; custom requires manual styling |
| Tooltip | MenuAnchor/PopupMenuButton | Tooltips are for passive hints, not actionable rich content |
| AlertDialog | BottomSheet | BottomSheet is better for mobile-first actions; dialog works universally |

**Installation:**
No dependencies to add.

## Architecture Patterns

### Pattern 1: Info Button in Card Without Selection Conflict

**What:** Add an interactive IconButton inside an InkWell-wrapped Card without the button triggering the card's onTap.

**When to use:** When a card has a primary tap action (selection) and a secondary action (info).

**Example:**
```dart
// Source: https://api.flutter.dev/flutter/material/InkWell-class.html
Card(
  child: InkWell(
    onTap: onSelectCard,
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Row(
        children: [
          Text('Card Title'),
          Spacer(),
          // Wrap IconButton to prevent tap propagation
          GestureDetector(
            onTap: () {
              // Info button action - stops propagation
            },
            child: IconButton(
              icon: Icon(Icons.info_outline),
              onPressed: () {
                showDialog(context: context, builder: ...);
              },
            ),
          ),
        ],
      ),
    ),
  ),
)
```

**Better approach (Material 3 2026):**
```dart
// Position IconButton outside InkWell's gesture area using Stack
// OR use a wrapping widget that absorbs the tap
IconButton(
  icon: Icon(Icons.info_outline),
  tooltip: 'More information',
  onPressed: () {
    // This prevents propagation naturally
    showDialog(...);
  },
)
```

### Pattern 2: AlertDialog with Scrollable Content

**What:** Display skill description and feature list in a dialog with automatic overflow handling.

**When to use:** When content length is variable and may exceed screen height.

**Example:**
```dart
// Source: https://api.flutter.dev/flutter/material/AlertDialog-class.html
showDialog(
  context: context,
  builder: (BuildContext context) {
    return AlertDialog(
      icon: Icon(Icons.info, color: Theme.of(context).colorScheme.primary),
      title: Text(skill.name),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(skill.description),
            SizedBox(height: 16),
            Text('Features:', style: TextStyle(fontWeight: FontWeight.bold)),
            ...skill.features.map((f) => Padding(
              padding: EdgeInsets.only(top: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('• '),
                  Expanded(child: Text(f)),
                ],
              ),
            )),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text('Close'),
        ),
      ],
    );
  },
);
```

### Pattern 3: Responsive Dialog Width

**What:** Adjust dialog width based on screen size for optimal readability.

**When to use:** When dialog content benefits from wider layout on desktop but compact on mobile.

**Example:**
```dart
// Source: Project's ResponsiveLayout pattern
AlertDialog(
  content: SizedBox(
    width: context.isDesktop ? 500 : 400,
    child: // ... content
  ),
)
```

### Anti-Patterns to Avoid

- **Tooltip for rich content:** Tooltips are designed for passive, brief text hints. Using them for multiple lines or interactive content creates accessibility issues (disappears on hover away).
- **Nested InkWells:** Placing InkWell inside InkWell causes unpredictable ripple behavior. Use a single InkWell for the card and separate gesture handling for buttons.
- **Missing scrollable wrapper:** AlertDialog content can overflow on small screens if not wrapped in SingleChildScrollView.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Custom info popup | Custom positioned overlay with Stack | AlertDialog | Handles backdrop, focus trap, animations, accessibility, responsive positioning |
| Tap event isolation | Manual event coordinate checking | GestureDetector or separate widget tree | Flutter's gesture system handles hit testing correctly |
| Dialog dismiss logic | Custom state management | Navigator.pop() with barrierDismissible | Built-in, accessible, respects platform conventions |

**Key insight:** Flutter's dialog system handles all edge cases (keyboard shortcuts, screen reader navigation, back button on Android, escape key on desktop) that custom overlays would need to reimplement.

## Common Pitfalls

### Pitfall 1: Info Button Triggers Card Selection

**What goes wrong:** Tapping the info IconButton also triggers the card's InkWell onTap, causing both the dialog to open AND the skill to be selected.

**Why it happens:** InkWell captures taps on its entire child tree. IconButton's onPressed doesn't stop propagation by default.

**How to avoid:**
1. **Simplest:** IconButton naturally consumes taps — ensure IconButton is a direct child with its own Material ancestor (Card provides this)
2. **If still propagating:** Wrap IconButton in a widget that explicitly stops propagation

**Warning signs:** Selecting a skill immediately after viewing its info popup.

### Pitfall 2: Dialog Overflow on Mobile

**What goes wrong:** Dialog content (description + features list) overflows viewport on mobile devices, making some content unreachable.

**Why it happens:** AlertDialog doesn't automatically scroll content.

**How to avoid:** Wrap content in `SingleChildScrollView` or use `AlertDialog(scrollable: true)`.

**Warning signs:** Truncated feature list, inability to reach "Close" button on small screens.

### Pitfall 3: Missing Accessibility Labels

**What goes wrong:** Screen reader users can't identify the info button's purpose.

**Why it happens:** IconButton without `tooltip` parameter has no semantic label.

**How to avoid:** Always include `tooltip: 'More information'` (or similar) on IconButton.

**Warning signs:** Screen reader announces "button" without context.

### Pitfall 4: Dialog Width Too Narrow on Desktop

**What goes wrong:** Dialog appears as a narrow column on wide desktop screens, wasting space and reducing readability.

**Why it happens:** AlertDialog defaults to a compact width suitable for mobile.

**How to avoid:** Use responsive width via `SizedBox(width: context.isDesktop ? 500 : 400)` around content.

**Warning signs:** Awkwardly narrow dialog on desktop with excessive line wrapping.

## Code Examples

Verified patterns from official sources and project codebase:

### Info Button in Card Header

```dart
// Pattern: Add info button to SkillCard header row
// Source: Existing SkillCard structure + Material IconButton docs
Row(
  children: [
    Text(
      getSkillEmoji(skill.name),
      style: const TextStyle(fontSize: 28),
    ),
    const SizedBox(width: 12),
    Expanded(
      child: Text(
        skill.name,
        style: theme.textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.bold,
        ),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
    ),
    // NEW: Info button
    IconButton(
      icon: const Icon(Icons.info_outline, size: 20),
      tooltip: 'More information',
      padding: const EdgeInsets.all(4),
      constraints: const BoxConstraints(),
      onPressed: () {
        // Show info dialog
      },
    ),
  ],
)
```

### Skill Info Dialog

```dart
// Pattern: AlertDialog with scrollable skill details
// Source: Project's document_preview_dialog.dart + AlertDialog docs
void _showSkillInfo(BuildContext context, Skill skill) {
  showDialog(
    context: context,
    builder: (BuildContext dialogContext) {
      return AlertDialog(
        icon: Icon(
          Icons.info,
          color: Theme.of(context).colorScheme.primary,
        ),
        title: Row(
          children: [
            Text(getSkillEmoji(skill.name), style: TextStyle(fontSize: 24)),
            SizedBox(width: 12),
            Expanded(child: Text(skill.name)),
          ],
        ),
        content: SizedBox(
          width: 450, // Responsive width can be added
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Description
                Text(
                  skill.description,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),

                // Features section
                if (skill.features.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Divider(),
                  const SizedBox(height: 12),
                  Text(
                    'Features',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...skill.features.map((feature) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('• ', style: TextStyle(fontSize: 14)),
                          Expanded(
                            child: Text(
                              feature,
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ],
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Close'),
          ),
        ],
      );
    },
  );
}
```

### Responsive Dialog Width

```dart
// Pattern: Adjust dialog width based on screen size
// Source: Project's ResponsiveLayout extension
import '../../../widgets/responsive_layout.dart';

AlertDialog(
  content: SizedBox(
    width: context.isDesktop ? 500 : (context.isTablet ? 450 : 400),
    child: // ... scrollable content
  ),
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom overlay with Stack | AlertDialog with M3 theming | Flutter 3.0+ (2022) | Automatic Material 3 styling, accessibility |
| WillPopScope for dismiss | PopScope + barrierDismissible | Flutter 3.24 (2025) | Better back navigation handling |
| Manual tooltip positioning | IconButton.tooltip parameter | Flutter 2.0+ (2021) | Automatic positioning and accessibility |

**Deprecated/outdated:**
- `WillPopScope`: Use `PopScope` in Flutter 3.24+ for handling back navigation in dialogs
- Manual ripple handling: InkWell with Material automatically provides M3-compliant ripples

## Open Questions

1. **Should info button prevent card selection entirely?**
   - What we know: Info button opens dialog, card has onTap for selection
   - What's unclear: UX expectation — should tapping info area still select, or only explicitly prevent it?
   - Recommendation: Prevent selection when tapping info button. Users expect info actions to be non-committal "peek" behavior, not selection.

2. **Feature list length limits?**
   - What we know: API returns 3-5 features per skill, SkillCard shows first 3
   - What's unclear: Should dialog show all features or apply same truncation?
   - Recommendation: Show ALL features in dialog — dialog is "full details" view, card is "preview".

## Sources

### Primary (HIGH confidence)

- [AlertDialog - Material library - Flutter API](https://api.flutter.dev/flutter/material/AlertDialog-class.html)
- [IconButton - Material library - Flutter API](https://api.flutter.dev/flutter/material/IconButton-class.html)
- [InkWell - Material library - Flutter API](https://api.flutter.dev/flutter/material/InkWell-class.html)
- [Material Design 3 - Dialogs Specs](https://m3.material.io/components/dialogs/specs)
- Project file: `frontend/lib/widgets/document_preview_dialog.dart` (dialog pattern reference)
- Project file: `frontend/lib/screens/assistant/widgets/skill_card.dart` (existing card structure)
- Project file: `frontend/lib/widgets/responsive_layout.dart` (responsive breakpoints)

### Secondary (MEDIUM confidence)

- [Flutter Material Design 3 in Flutter 2026](https://medium.com/hireflutterdev/material-design-3-in-flutter-d891ee2ff967) - M3 theming defaults
- [Customizing Flutter's PopupMenuButton 2026](https://copyprogramming.com/howto/flutter-popupmenubutton-customizing-the-3-dots-in-menu) - Alternative patterns considered
- [Flutter Tooltip Essentials](https://www.dhiwise.com/post/crafting-interactive-ui-a-succinct-guide-to-flutter-tooltip) - Tooltip vs dialog usage guidelines

### Tertiary (LOW confidence)

- WebSearch results for best practices (2026 updates) — verified against official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components are built-in Material widgets with stable APIs
- Architecture: HIGH - Patterns verified in existing project codebase and official documentation
- Pitfalls: HIGH - Common issues documented in Flutter community and Material guidelines

**Research date:** 2026-02-18
**Valid until:** March 2026 (stable - Material 3 is mature, no breaking changes expected)
