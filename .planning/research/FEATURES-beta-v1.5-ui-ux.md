# Feature Landscape: Flutter Enterprise App UI/UX Patterns

**Domain:** Enterprise Flutter application UI/UX patterns for Beta v1.5
**Researched:** 2026-01-29
**Confidence:** MEDIUM-HIGH (verified with official Flutter/Material Design documentation + 2026 web sources)
**Context:** Beta v1.5 milestone focusing on UI/UX improvements for executive demos

## Executive Summary

This research examines UI/UX patterns specifically for enterprise Flutter applications targeting business analysts conducting executive demos. The focus is on seven critical UX areas identified from the current analysis: responsive navigation, empty states, deletion flows, settings organization, breadcrumb patterns, mode selection interfaces, and date/time display conventions.

**Key findings:**
- Material Design 3 is default in Flutter 3.16+, providing enhanced accessibility and large-screen support
- Navigation patterns must adapt dramatically by screen size (sidebar ≥600px, drawer <600px)
- Empty states require illustrations + messaging + CTAs to guide new users (not just blank screens)
- Deletion flows MUST use SnackBar undo patterns (Material 3 behavior changed in Flutter 3.38)
- Mode selection should use Material Design chips (ChoiceChip) rather than text commands
- Date/time formatting requires `intl` package with locale-aware skeletons for internationalization
- WCAG AA compliance (4.5:1 contrast, 48×48px targets) is table stakes for enterprise

## Table Stakes Features

Features users expect in enterprise applications. Missing these signals incomplete or unprofessional product.

| Feature | Why Expected | Complexity | Priority | Implementation Notes |
|---------|--------------|------------|----------|---------------------|
| **Persistent Navigation** | Users expect navigation available on every screen, not just home | Medium | P0 | NavigationRail for desktop (≥600px), Drawer for mobile (<600px); use `LayoutBuilder` for responsive switching |
| **Current Location Indicator** | Users must know where they are at all times | Low | P0 | Material 3 NavigationIndicator with `useIndicator: true`; selected state styling required |
| **Empty State Screens** | Blank screens signal broken functionality | Medium | P0 | Illustration/icon + heading + explanation + primary CTA button; different states per context |
| **Deletion Confirmation with Undo** | Users expect protection from accidental data loss | Medium | P1 | SnackBar with undo action (7-second window); Flutter 3.38+ requires explicit `duration` + `behavior: floating` |
| **Settings Page** | Users expect central location for preferences | Medium | P1 | Sectioned layout with ListTiles; profile at top, preferences grouped logically |
| **Consistent Date Formatting** | Inconsistent dates signal unfinished product | Low | P0 | Use `intl` package `DateFormat` skeletons; never hard-code date strings |
| **48×48px Touch Targets** | WCAG compliance; enterprise demos fail when controls hard to tap | Low | P0 | All interactive elements minimum 48×48 pixels (Material Design standard) |
| **4.5:1 Contrast Ratio** | WCAG AA requirement; enterprise buyers verify | Low | P0 | Material 3 default theme provides this; verify custom colors with contrast checker |
| **Undo for Important Actions** | Users expect to recover from mistakes | Medium | P1 | Critical for deletion; 7-second window standard, 10 seconds for bulk operations |
| **Responsive Breakpoints** | Seamless desktop ↔ tablet ↔ mobile experience | High | P0 | Material Design breakpoints: <600px phone, 600-839px tablet, 840px+ desktop |

## Differentiators

Features that elevate from "functional" to "polished enterprise-grade." Create positive impression in demos.

| Feature | Value Proposition | Complexity | Priority | Implementation Notes |
|---------|-------------------|------------|----------|---------------------|
| **Lottie Animated Empty States** | Engaging vs static; signals attention to detail | Medium | P2 | Use `lottie` package; LottieFiles/IconScout assets; lightweight vector format |
| **Bulk Selection with Visual Feedback** | Efficiency-first design; reduces repetitive actions | High | P2 | Multi-select checkboxes + floating action button + selection count indicator |
| **Responsive Breakpoint Transitions** | Signals cross-platform excellence | High | P2 | Animated transitions between NavigationRail ↔ Drawer at 600-840px breakpoints |
| **Smart Date/Time Formatting** | Relative dates ("2 hours ago") for recent, absolute for older | Medium | P3 | Use `timeago` package + `intl` fallback; 7-day threshold typical |
| **Material 3 Design** | Current design language (not legacy Material 2) | Low | P0 | Already default in Flutter 3.16+; ensure `useMaterial3: true` |
| **Mode Selection Chips** | Visual, tappable vs text commands | Low | P1 | `ChoiceChip` for exclusive selection; `Wrap` widget for responsive layout |
| **Contextual Empty States** | Different messages per context (new user vs filtered vs error) | Medium | P2 | More helpful than generic "No data" message |
| **Settings Search** | Reduces cognitive load for apps with many settings | Medium | P3 | Defer until settings page has 20+ options |
| **Skeleton Loading States** | Reduces perceived latency vs spinners | Medium | P2 | Pulsing shimmer effect; shows content structure while loading |
| **Floating Action Button (Mobile)** | Primary action immediately accessible | Low | P1 | Material Design standard for mobile; use for "New Conversation" action |

## Anti-Features

Features to explicitly avoid. Common mistakes in Flutter enterprise apps.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Breadcrumb Navigation on Mobile** | Horizontal-heavy; causes scrolling; redundant with back button | AppBar with back button + title; breadcrumbs only for desktop ≥1024px |
| **Destructive Actions Without Undo** | Creates anxiety; users fear mistakes | Always provide SnackBar with undo (7-10 seconds); longer for bulk operations |
| **"Are You Sure?" Dialogs for Everything** | Creates friction; users click through without reading | SnackBar undo for recoverable actions; dialogs ONLY for irreversible (account deletion) |
| **Text-Based Mode Commands** | Requires memorization; not discoverable; poor mobile UX | Visual ChoiceChips or SegmentedButton; always visible, self-documenting |
| **Inconsistent Navigation Patterns** | NavigationRail on some screens, hidden on others; confusing | Navigation persistent across ALL screens; NavigationRail (desktop) or Drawer (mobile) consistently |
| **Generic "No Data" Messages** | Unhelpful; users wonder if broken or what to do | Contextual empty states: illustration + explanation + CTA |
| **Hard-Coded Date Formats** | Breaks internationalization; unprofessional in non-US markets | Always use `intl` DateFormat with locale-aware skeletons |
| **Multiple Deletion Confirmation Steps** | "Delete" → "Are you sure?" → "Yes, delete" frustrates users | Single tap to delete → SnackBar with undo; fewer actions, same safety |
| **Settings as Flat List** | Cognitive overload when >10 items | Group into sections with headers (Profile, Preferences, Account, About) |
| **Non-Standard Icon Usage** | Confuses users; requires learning app-specific language | Use Material Icons standard: delete_outline, settings, account_circle, etc. |
| **Auto-Playing Animations** | Distracting; accessibility issue | Animations only on user interaction; respect `prefers-reduced-motion` |
| **Complex Gesture Requirements** | Discoverable on mobile ≠ obvious | Swipe-to-delete OK if also accessible via visible delete button |

## Feature Dependencies & Implementation Order

### Phase 1: Navigation Foundation (P0) — Week 1
**Why first:** Nothing else matters if users can't navigate.

```
Responsive Navigation System
├── NavigationRail for desktop (≥600px)
│   ├── selectedIndex tracks current location
│   └── useIndicator: true for visual feedback
├── Drawer for mobile (<600px)
│   ├── Same destinations as NavigationRail
│   └── Hamburger menu icon in AppBar
└── Consistent across all screens (persistent)
```

**Implementation:**
```dart
class ResponsiveScaffold extends StatelessWidget {
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 600) {
          // Desktop: NavigationRail
          return Row(
            children: [
              NavigationRail(
                selectedIndex: _selectedIndex,
                onDestinationSelected: _onDestinationSelected,
                useIndicator: true,
                destinations: _destinations,
              ),
              Expanded(child: _currentScreen),
            ],
          );
        } else {
          // Mobile: Drawer
          return Scaffold(
            appBar: AppBar(title: Text(_currentTitle)),
            drawer: Drawer(child: ListView(children: _drawerItems)),
            body: _currentScreen,
          );
        }
      },
    );
  }
}
```

**Testing checklist:**
- [ ] Navigation visible on every screen
- [ ] Current location indicated visually
- [ ] Transitions smooth at breakpoints (599px ↔ 600px)
- [ ] Touch targets ≥48×48px
- [ ] Screen reader announces current location

### Phase 2: Empty States (P0) — Week 2
**Why second:** New users immediately encounter empty states; must be welcoming.

```
Empty State Components
├── Illustration (SVG or Lottie animation)
│   ├── Size: 200px mobile, 300px desktop
│   └── Centered vertically and horizontally
├── Heading ("No conversations yet")
│   ├── Typography: headlineMedium
│   └── Max width: 400px for readability
├── Explanation ("Start a conversation to begin...")
│   ├── Typography: bodyLarge
│   └── 1-2 sentences maximum
└── Primary CTA (Button: "New Conversation")
    ├── FilledButton (Material 3)
    └── Minimum size: 48×48px
```

**Empty state contexts:**
1. **New User:** Welcoming, explains what to do first
   - "Welcome! Start your first conversation to begin requirements discovery."
   - CTA: "New Conversation"

2. **Filtered Results (No Matches):** Explains why empty, suggests action
   - "No conversations match your search."
   - CTA: "Clear Filters"

3. **Network Error:** Explains problem, suggests recovery
   - "Unable to load conversations. Check your connection."
   - CTA: "Retry"

**Implementation:**
```dart
class EmptyStateWidget extends StatelessWidget {
  final String title;
  final String message;
  final String ctaLabel;
  final VoidCallback onCtaPressed;
  final Widget? illustration; // SVG or Lottie

  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: 400),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (illustration != null)
              SizedBox(
                width: 200,
                height: 200,
                child: illustration,
              ),
            SizedBox(height: 24),
            Text(title, style: Theme.of(context).textTheme.headlineMedium),
            SizedBox(height: 16),
            Text(message, style: Theme.of(context).textTheme.bodyLarge, textAlign: TextAlign.center),
            SizedBox(height: 32),
            FilledButton(
              onPressed: onCtaPressed,
              child: Text(ctaLabel),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Phase 3: Deletion with Undo (P1) — Week 3
**Why third:** Users need to delete data safely.

```
Deletion Flow
1. User taps delete icon/action
2. Item removed from UI immediately (optimistic update)
3. SnackBar appears: "Conversation deleted" with "Undo" action
4. User has 7 seconds to undo (10 seconds for bulk)
5. If no undo, deletion finalized (API call if applicable)
```

**CRITICAL Flutter 3.38+ Breaking Change:**
Any SnackBar with an action is now persistent by default (doesn't auto-dismiss). MUST set `duration` AND `behavior: SnackBarBehavior.floating` to restore timed dismissal.

**Implementation:**
```dart
void deleteConversation(String id) {
  // Store reference for undo
  final conversation = _conversations.firstWhere((c) => c.id == id);

  // Optimistically remove from UI
  setState(() {
    _conversations.removeWhere((c) => c.id == id);
  });

  // Show SnackBar with undo
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text('Conversation deleted'),
      duration: Duration(seconds: 7), // REQUIRED in Flutter 3.38+
      behavior: SnackBarBehavior.floating, // REQUIRED for auto-dismiss
      action: SnackBarAction(
        label: 'Undo',
        onPressed: () {
          // Restore conversation
          setState(() {
            _conversations.add(conversation);
          });
        },
      ),
    ),
  );

  // Finalize deletion after duration
  Future.delayed(Duration(seconds: 7), () {
    if (!_conversations.contains(conversation)) {
      _conversationService.delete(id); // API call
    }
  });
}
```

**Bulk deletion:**
- Use 10-second window (longer for higher stakes)
- SnackBar message: "5 conversations deleted"
- Undo action restores all deleted items

### Phase 4: Settings Page (P1) — Week 4
**Why fourth:** Expected but not critical for core workflow.

```
Settings Organization
├── Profile Section (top)
│   ├── Avatar/name (ListTile with leading: CircleAvatar)
│   └── Account email (subtitle)
├── Preferences Section
│   ├── Theme (light/dark/system) — ListTile with trailing: DropdownButton
│   ├── Language — ListTile with trailing: current locale
│   └── Default mode (Mode A/B) — ListTile with trailing: SegmentedButton
├── Data & Privacy Section
│   ├── Export data — ListTile with onTap
│   ├── Delete account — ListTile with onTap (shows confirmation dialog)
│   └── Privacy policy link — ListTile with trailing: Icon(Icons.open_in_new)
└── About Section
    ├── Version number — ListTile (disabled, for display only)
    ├── Licenses — ListTile with onTap
    └── Help & feedback — ListTile with onTap
```

**Implementation:**
```dart
class SettingsPage extends StatelessWidget {
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Settings')),
      body: ListView(
        children: [
          // Profile Section
          ListTile(
            leading: CircleAvatar(child: Icon(Icons.account_circle)),
            title: Text('User Name'),
            subtitle: Text('user@example.com'),
          ),
          Divider(),

          // Preferences Section Header
          ListTile(
            title: Text('Preferences', style: Theme.of(context).textTheme.titleMedium),
            enabled: false,
          ),
          ListTile(
            leading: Icon(Icons.palette),
            title: Text('Theme'),
            trailing: DropdownButton<ThemeMode>(
              value: _currentTheme,
              onChanged: _setTheme,
              items: [
                DropdownMenuItem(value: ThemeMode.light, child: Text('Light')),
                DropdownMenuItem(value: ThemeMode.dark, child: Text('Dark')),
                DropdownMenuItem(value: ThemeMode.system, child: Text('System')),
              ],
            ),
          ),
          ListTile(
            leading: Icon(Icons.language),
            title: Text('Language'),
            trailing: Text('English'),
            onTap: () => _showLanguageDialog(),
          ),
          Divider(),

          // Data & Privacy Section Header
          ListTile(
            title: Text('Data & Privacy', style: Theme.of(context).textTheme.titleMedium),
            enabled: false,
          ),
          ListTile(
            leading: Icon(Icons.download),
            title: Text('Export data'),
            onTap: _exportData,
          ),
          ListTile(
            leading: Icon(Icons.delete_forever, color: Colors.red),
            title: Text('Delete account', style: TextStyle(color: Colors.red)),
            onTap: _showDeleteAccountDialog,
          ),
          Divider(),

          // About Section Header
          ListTile(
            title: Text('About', style: Theme.of(context).textTheme.titleMedium),
            enabled: false,
          ),
          ListTile(
            leading: Icon(Icons.info),
            title: Text('Version'),
            subtitle: Text('1.5.0 (Beta)'),
          ),
          ListTile(
            leading: Icon(Icons.article),
            title: Text('Licenses'),
            onTap: () => showLicensePage(context: context),
          ),
        ],
      ),
    );
  }
}
```

**Accessibility:**
- Section headers with `enabled: false` are semantic separators
- Leading icons improve scannability
- Trailing widgets show current values
- All ListTiles are 48px+ tall (Material default)

### Phase 5: Mode Selection Chips (P1) — Week 5
**Why fifth:** Improves discoverability, but existing text commands work.

```
Mode Selection UI
├── ChoiceChip for exclusive selection (Mode A OR Mode B)
├── Visual indicator of current mode (selected state)
├── Wrap widget for responsive layout (wraps on narrow screens)
└── Persistent across conversation (saved in thread metadata)
```

**Implementation:**
```dart
class ModeSelector extends StatefulWidget {
  final Mode currentMode;
  final Function(Mode) onModeChanged;

  State<ModeSelector> createState() => _ModeSelectorState();
}

class _ModeSelectorState extends State<ModeSelector> {
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8.0,
      runSpacing: 8.0,
      children: [
        ChoiceChip(
          label: Text('Mode A: Structured Requirements'),
          avatar: Icon(Icons.list_alt),
          selected: widget.currentMode == Mode.A,
          onSelected: (selected) {
            if (selected) widget.onModeChanged(Mode.A);
          },
        ),
        ChoiceChip(
          label: Text('Mode B: Open Discovery'),
          avatar: Icon(Icons.explore),
          selected: widget.currentMode == Mode.B,
          onSelected: (selected) {
            if (selected) widget.onModeChanged(Mode.B);
          },
        ),
      ],
    );
  }
}
```

**Material 3 ChoiceChip behavior:**
- Selected state: filled with secondary container color
- Checkmark icon appears when selected
- Haptic feedback on selection (mobile)
- 48px minimum touch target (automatically provided)

**Alternative:** SegmentedButton (Material 3)
For tighter layouts, SegmentedButton provides similar functionality:
```dart
SegmentedButton<Mode>(
  segments: [
    ButtonSegment(value: Mode.A, label: Text('Mode A'), icon: Icon(Icons.list_alt)),
    ButtonSegment(value: Mode.B, label: Text('Mode B'), icon: Icon(Icons.explore)),
  ],
  selected: {currentMode},
  onSelectionChanged: (Set<Mode> modes) {
    onModeChanged(modes.first);
  },
)
```

### Phase 6: Date/Time Formatting (P0) — Throughout
**Why throughout:** Implement as part of any date display work, not separate phase.

```
Date Formatting Rules
├── Recent items (<24 hours): Relative time ("2 hours ago")
├── This week (1-7 days): "Monday, 3:45 PM"
├── This year: "July 10, 3:45 PM"
└── Previous years: "July 10, 2025"
```

**Implementation:**
```dart
import 'package:intl/intl.dart';
import 'package:timeago/timeago.dart' as timeago;

String formatTimestamp(DateTime timestamp, {required Locale locale}) {
  final now = DateTime.now();
  final difference = now.difference(timestamp);

  if (difference.inHours < 24) {
    // Use timeago package: "2 hours ago"
    return timeago.format(timestamp, locale: locale.languageCode);
  } else if (difference.inDays < 7) {
    // "Monday, 3:45 PM"
    return DateFormat('EEEE, ').add_jm().format(timestamp);
  } else if (timestamp.year == now.year) {
    // "July 10, 3:45 PM"
    return DateFormat('MMMM d, ').add_jm().format(timestamp);
  } else {
    // "July 10, 2025"
    return DateFormat('MMMM d, y').format(timestamp);
  }
}
```

**Internationalization setup:**
```dart
import 'package:intl/date_symbol_data_local.dart';

void main() async {
  // Initialize date formatting for all locales
  await initializeDateFormatting();
  runApp(MyApp());
}
```

**Key principles:**
- **Always use skeletons** (`.yMMMd()`, `.jm()`) not pattern strings
- Skeletons adapt to locale conventions automatically
- 'j' skeleton uses 12h/24h based on locale
- Never hard-code date strings like "MM/DD/YYYY"

**Mobile vs Desktop:**
- **Mobile:** Compact format for space constraints
  ```dart
  DateFormat('MMMd').add_jm().format(timestamp) // "Jul 10, 3:45 PM"
  ```
- **Desktop:** Full format for clarity
  ```dart
  DateFormat('MMMMd').add_jm().format(timestamp) // "July 10, 3:45 PM"
  ```

## Accessibility Requirements (WCAG AA)

All features MUST meet these standards. Enterprise buyers verify compliance.

| Requirement | Standard | Verification Method | Implementation |
|-------------|----------|---------------------|----------------|
| **Touch Target Size** | Minimum 48×48 pixels | DevTools overlay; manual measurement | Material widgets provide this by default; verify custom widgets |
| **Contrast Ratio** | 4.5:1 normal text; 3:1 large text (≥18pt) | Contrast checker tool; automated testing | Material 3 default theme compliant; verify custom colors |
| **Screen Reader Support** | All interactive elements have semantic labels | TalkBack (Android), VoiceOver (iOS) | Use `Semantics` widget for custom elements; Material widgets auto-labeled |
| **Focus Management** | Logical focus order; visible focus indicators | Keyboard navigation test (web/desktop) | FocusNode widgets; Material 3 provides default focus indicators |
| **Color Independence** | Information not conveyed by color alone | Grayscale test; colorblindness simulators | Add icons + text labels; never rely on color alone |
| **Text Scaling** | UI remains usable at 200% text scale | System text size set to largest | Use flexible layouts; test with MediaQuery.textScaleFactor = 2.0 |
| **Error Messages** | Errors have sufficient contrast + clear text | Contrast checker; user testing | 4.5:1 contrast for error text; provide actionable messages |
| **Undo/Recovery** | Important actions are undoable | Feature testing | All deletion/destructive actions have undo mechanism |
| **Reduced Motion** | Respect prefers-reduced-motion | Test with system setting enabled | Check MediaQuery.disableAnimations; provide static alternatives |

**Flutter accessibility widgets:**
```dart
// Semantic labels for custom widgets
Semantics(
  label: 'Delete conversation',
  button: true,
  child: IconButton(
    icon: Icon(Icons.delete),
    onPressed: _deleteConversation,
  ),
)

// Merge semantics for complex widgets
MergeSemantics(
  child: Row(
    children: [
      Icon(Icons.star),
      Text('Favorite'),
    ],
  ),
)

// Exclude decorative elements
ExcludeSemantics(
  child: Container(
    decoration: BoxDecoration(...), // Decorative background
    child: actualContent,
  ),
)
```

**Known limitation:** Full keyboard accessibility on iOS is not possible due to Flutter framework limitations. Document this for enterprise buyers.

## Mobile vs Desktop Differences

| Feature | Mobile (<600px) | Desktop (≥600px) | Notes |
|---------|-----------------|------------------|-------|
| **Navigation** | Drawer (hamburger menu) | NavigationRail (persistent sidebar) | Breakpoint at 600px |
| **Mode Selection** | ChoiceChips (wrap to 2 rows) | ChoiceChips (single row) or SegmentedButton | Same component, responsive layout |
| **Deletion Confirmation** | SnackBar at bottom (floating) | SnackBar at bottom (floating) | Same pattern both platforms |
| **Settings** | Full-screen ListView | ListView in content area (sidebar remains) | Settings not in drawer on desktop |
| **Empty States** | Smaller illustration (200px) | Larger illustration (300px) | Scale based on available space |
| **Date Display** | Compact format ("7/10, 3:45 PM") | Full format ("July 10, 3:45 PM") | `DateFormat.MMMd()` vs `DateFormat.yMMMd()` |
| **Bulk Actions** | Floating Action Button | AppBar actions (icon buttons) | FAB for primary action on mobile |
| **Breadcrumbs** | Never use (redundant with back button) | Optional for complex hierarchies (≥1024px) | Back button sufficient for mobile |
| **Touch Targets** | 48×48px minimum | 48×48px minimum (same) | Consistent across platforms |
| **AppBar** | Always visible with title + actions | Optional (content may have own header) | Mobile needs orientation cues |

**Responsive breakpoints (Material Design standard):**
```dart
enum ScreenSize {
  phone,   // 0-599px: Drawer + bottom nav
  tablet,  // 600-839px: NavigationRail + adaptive layouts
  desktop, // 840px+: NavigationRail + multi-column layouts
}

ScreenSize getScreenSize(BoxConstraints constraints) {
  if (constraints.maxWidth < 600) return ScreenSize.phone;
  if (constraints.maxWidth < 840) return ScreenSize.tablet;
  return ScreenSize.desktop;
}
```

## Animation & Motion Guidelines

Animations should reduce cognitive load, not add distraction.

| Animation Type | Duration | Easing | When to Use | Implementation |
|----------------|----------|--------|-------------|----------------|
| **Navigation transitions** | 300ms | Decelerate | Screen changes, route transitions | `PageRouteBuilder` with `CurvedAnimation` |
| **Micro-interactions** | 100-200ms | Standard | Button presses, chip selection | `AnimatedContainer`, `AnimatedOpacity` |
| **Empty state entry** | 400ms | Decelerate | Fade in + slight scale | `FadeTransition` + `ScaleTransition` |
| **SnackBar entry/exit** | 250ms | Decelerate (in), Accelerate (out) | Built-in to Material SnackBar | Automatic |
| **Bulk selection mode** | 200ms | Standard | Checkboxes appear, FAB slides in | `AnimatedSwitcher` |
| **Skeleton loading** | 1.5s loop | Linear | Pulsing shimmer for loading states | `shimmer` package |

**Material Motion principles:**
- **Informative:** Animation clarifies relationships (e.g., navigation indicator slides to new position)
- **Focused:** Single element animates at a time; avoid simultaneous competing animations
- **Expressive:** Animations reflect brand personality (smooth, professional, not playful/bouncy for enterprise)

**Performance:** Animations MUST run at 60fps.
- Test on low-end devices
- Prefer `Transform` and `Opacity` (GPU-accelerated) over layout changes
- Use `RepaintBoundary` for complex animated widgets
- Avoid animating during heavy operations (API calls, data processing)

**Respect reduced motion:**
```dart
bool shouldAnimate(BuildContext context) {
  return !MediaQuery.of(context).disableAnimations;
}

Widget buildWithAnimation(BuildContext context) {
  if (shouldAnimate(context)) {
    return AnimatedOpacity(...);
  } else {
    return Container(...); // Static version
  }
}
```

## User Flow: New User First Experience

Critical flow showing how features work together for polished first impression.

```
1. Launch app
   └─> Empty state: "Welcome to Business Analyst Assistant"
       ├─> Lottie animation (optional: welcoming illustration)
       ├─> Explanation: "Start a conversation to begin requirements discovery"
       └─> CTA: [New Conversation] button (FilledButton, primary)

2. Tap [New Conversation]
   └─> Navigate to conversation screen
       ├─> Persistent navigation (Rail/Drawer) visible
       ├─> AppBar with title: "New Conversation"
       ├─> Mode selection chips visible at top (ChoiceChips)
       └─> Empty chat area with suggested prompt chips

3. Select mode (tap ChoiceChip)
   └─> Visual feedback: chip shows selected state
       ├─> Chip background changes to secondary container color
       ├─> Checkmark icon appears in chip
       ├─> Haptic feedback (mobile)
       └─> No confirmation dialog needed; mode set immediately

4. Send first message
   └─> Message appears in chat
       ├─> Timestamp formatted: "Just now" (relative, via timeago package)
       ├─> AI response streams in (SSE)
       └─> Mode indicator visible (chip at top remains selected)

5. Navigate to home (via sidebar/drawer)
   └─> Conversation appears in list
       ├─> Title: First line of first message (auto-generated)
       ├─> Timestamp: "5 minutes ago" (relative)
       └─> Mode indicator: Small chip showing "Mode A"

6. Swipe left or tap delete icon
   └─> SnackBar appears: "Conversation deleted [Undo]"
       ├─> Item removed from list immediately (optimistic)
       ├─> SnackBar floating at bottom
       ├─> 7-second window to undo
       └─> If no undo, deletion finalized after 7 seconds

7. Navigate to Settings (via sidebar/drawer)
   └─> Sectioned layout with profile at top
       ├─> Profile: Avatar + name + email
       ├─> Preferences: Theme, Language, Default mode
       ├─> Data & Privacy: Export, Delete account
       └─> About: Version, Licenses, Help
   └─> Navigation remains visible (desktop) or in drawer (mobile)
```

**Key UX principles demonstrated:**
- **No dead ends:** Navigation always available
- **Clear next actions:** CTAs in empty states
- **Immediate feedback:** Chip selection, message sending
- **Forgiving:** Undo for deletions
- **Contextual information:** Timestamps, mode indicators
- **Consistency:** Same patterns across screens

## Research Quality Assessment

| Area | Confidence | Reasoning | Sources |
|------|------------|-----------|---------|
| **Navigation Patterns** | HIGH | Official Flutter NavigationRail documentation verified; Material Design responsive breakpoints standard | Flutter docs, Material Design 3 |
| **Empty States** | MEDIUM | Strong community consensus and examples, but no official Material Design 3 empty state spec found | Medium articles (2025-2026), GitHub examples |
| **Deletion/Undo Flows** | HIGH | Official Flutter SnackBar documentation; Flutter 3.38 behavior change documented in release notes | Flutter API docs, breaking changes log |
| **Settings Organization** | MEDIUM | Community patterns and templates, but not formally specified in Material Design 3 | Flutter templates, Medium articles |
| **Breadcrumb Patterns** | MEDIUM | Material Design guidance exists but limited for mobile; Flutter implementation community-driven | Medium articles, UX design blogs |
| **Mode Selection Chips** | HIGH | Official Flutter ChoiceChip/ActionChip documentation; Material Design 3 chip specification | Flutter API docs, Material Design 3 |
| **Date/Time Formatting** | HIGH | Official `intl` package documentation; DateFormat class API reference | pub.dev, Flutter API docs |
| **Accessibility** | HIGH | Official Flutter accessibility documentation; WCAG 2 standards verified | Flutter docs, W3C WCAG |
| **Material 3 Adoption** | HIGH | Official Flutter documentation confirms Material 3 default since Flutter 3.16 | Flutter release notes |

## Open Questions & Gaps

Issues that may require phase-specific research or validation:

1. **Empty state illustration style:** Should illustrations be line art, flat color, or full color? Material Design 3 doesn't specify. **Decision needed** based on brand guidelines.

2. **Bulk deletion confirmation:** For bulk operations (deleting 10+ items), is 10-second undo window sufficient, or should there be a confirmation dialog first? **Research needed** on user expectations for bulk operations in enterprise contexts.

3. **Settings search implementation:** If settings page grows beyond 20 items, what's the best search pattern? Persistent search field at top, or search icon that expands? **Material Design doesn't specify** for settings-specific search.

4. **Breadcrumb truncation:** For deep hierarchies (5+ levels), how should breadcrumbs truncate on narrower desktop screens (840-1024px)? Show first + last 2 levels? Ellipsis menu? **Pattern testing needed.**

5. **Mode indicator in conversation list:** Should mode be shown as a chip (takes space) or as a colored dot (subtle but less clear)? **Testing needed** to determine what provides best at-a-glance scannability.

6. **Internationalization testing:** While `intl` package supports 50+ languages, BA Assistant currently only supports English. When should internationalization be prioritized, and which languages first? **Product decision needed.**

7. **Keyboard shortcuts:** Desktop users may expect keyboard shortcuts for common actions (Ctrl+N for new conversation, Ctrl+F for search). When should this be added, and what shortcuts map to which actions? **Defer to post-Beta** based on user feedback.

## Sources

### Official Flutter Documentation (HIGH confidence)
- [Material Design for Flutter](https://docs.flutter.dev/ui/design/material) - Material 3 default status confirmed
- [Flutter Accessibility](https://docs.flutter.dev/ui/accessibility-and-internationalization/accessibility) - WCAG compliance guidelines
- [NavigationRail class](https://api.flutter.dev/flutter/material/NavigationRail-class.html) - Usage patterns, responsive design
- [DateFormat class](https://api.flutter.dev/flutter/package-intl_intl/DateFormat-class.html) - Date formatting with locale support
- [SnackBar class](https://api.flutter.dev/flutter/material/SnackBar-class.html) - Undo pattern implementation
- [ChoiceChip class](https://api.flutter.dev/flutter/material/ChoiceChip-class.html) - Mode selection UI
- [InputChip class](https://api.flutter.dev/flutter/material/InputChip-class.html) - Interactive chip variants
- [ActionChip class](https://api.flutter.dev/flutter/material/ActionChip-class.html) - Action trigger chips

### Material Design 3 (HIGH confidence)
- [Material Design 3 for Flutter](https://m3.material.io/develop/flutter) - Official Material 3 Flutter implementation guide
- [Accessibility overview – Material Design 3](https://m3.material.io/foundations/overview) - Accessibility principles (page structure verified)

### Flutter Ecosystem Resources (MEDIUM confidence)
- [Modern Flutter UI in 2026: Design Patterns & Best Practices](https://medium.com/@expertappdevs/how-to-build-modern-ui-in-flutter-design-patterns-64615b5815fb) - Enterprise patterns, Material 3 adoption
- [Building Beautiful Responsive UI in Flutter: A Complete Guide for 2026](https://medium.com/@saadalidev/building-beautiful-responsive-ui-in-flutter-a-complete-guide-for-2026-ea43f6c49b85) - Responsive breakpoints
- [How to Create a Pixel-Perfect Material 3 UI in Flutter (Complete 2026 Guide)](https://medium.com/@saadalidev/how-to-create-a-pixel-perfect-material-3-ui-in-flutter-complete-2026-guide-233bb926f683) - Material 3 implementation
- [Responsive layouts in Flutter: Split View and Drawer Navigation](https://codewithandrea.com/articles/flutter-responsive-layouts-split-view-drawer-navigation/) - Responsive patterns

### Specific Feature Resources (MEDIUM confidence)
- [Mastering Empty States: The Power of Flutter Empty Widgets](https://www.dhiwise.com/post/mastering-the-flutter-empty-widget-enhancing-user-experience) - Empty state best practices
- [Design beautiful empty state screens (GitHub Gist)](https://gist.github.com/thepowerceo/9ccd6c6e00544e5242e96b80a11fe12e) - Empty state patterns (January 2026)
- [Deleting entry and undoing deletion in snackbar - WeightTracker 7](https://fidev.io/deleting-entry-with-undo/) - Undo pattern implementation
- [Flutter Settings Pages Templates](https://fluttertemplates.dev/widgets/must_haves/settings_page) - Settings organization patterns
- [Implementing breadcrumb in Flutter](https://amir-p.medium.com/implementing-breadcrumb-in-flutter-6ca9b8144206) - Breadcrumb patterns
- [Exploring breadcrumbs UI design: anatomy, UX tips, states & use cases](https://www.setproduct.com/blog/breadcrumbs-ui-design) - Breadcrumb UX guidelines
- [intl | Dart package](https://pub.dev/packages/intl) - Date/time internationalization (official)
- [Lottie Animations in Flutter: Creating Engaging User Experiences](https://dev.to/sayed_ali_alkamel/lottie-animations-in-flutter-creating-engaging-user-experiences-184n) - Lottie implementation
- [lottie | Flutter package](https://pub.dev/packages/lottie) - Official Lottie package

### Breaking Changes & Updates (HIGH confidence)
- [Flutter 3.38: New Features & Breaking Changes + Migration Guide](https://vagary.tech/blog/flutter-3-38-release-notes-breaking-changes-migration-guide) - SnackBar persistence behavior change
- [The ThemeData.useMaterial3 flag is true by default](https://docs.flutter.dev/release/breaking-changes/material-3-default) - Material 3 default since Flutter 3.16

### Accessibility Standards (HIGH confidence)
- [Improving Accessibility in Flutter Apps: A Comprehensive Guide](https://dev.to/adepto/improving-accessibility-in-flutter-apps-a-comprehensive-guide-1jod) - Flutter-specific accessibility
- [Exploring Accessibility and Digital Inclusion with Flutter](https://www.verygood.ventures/blog/exploring-accessibility-and-digital-inclusion-with-flutter) - WCAG compliance
- [Mobile App Accessibility: How to Make an App Inclusive?](https://blog.flutter.wtf/mobile-app-accessibility/) - Mobile accessibility patterns

### Multi-Select & Bulk Actions (MEDIUM confidence)
- [Selection - Patterns - Material Design](https://m1.material.io/patterns/selection.html) - Material Design selection patterns
- [MultiSelect Item of list in Flutter - Mobikul](https://mobikul.com/multiselect-item-of-list-in-flutter/) - Multi-select implementation
- [Explore Multi-Select Items In Flutter - Flutterexperts](https://flutterexperts.com/explore-multi-select-items-in-flutter/) - Multi-select patterns

### Bottom Sheets & Modals (MEDIUM confidence)
- [showModalBottomSheet function - material library](https://api.flutter.dev/flutter/material/showModalBottomSheet.html) - Official API documentation
- [Exploring Flutter Bottom Sheets: Persistent and Modal](https://www.dhiwise.com/post/exploring-different-types-of-flutter-bottom-sheets) - Usage patterns
- [Flutter modal bottom sheet tutorial with examples - LogRocket](https://blog.logrocket.com/flutter-modal-bottom-sheet-tutorial-with-examples/) - Implementation examples
