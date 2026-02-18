# Domain Pitfalls

**Domain:** Skill Discovery UI Enhancement for Flutter Chat Application
**Researched:** 2026-02-18

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

---

### Pitfall 1: Parsing SKILL.md on Frontend Instead of Backend

**What goes wrong:** Developers parse markdown front matter on the Flutter frontend for every skill popup/info display, causing performance degradation and increased complexity.

**Why it happens:** It seems simple to parse markdown client-side since Flutter packages exist (`front_matter_ml`, `cosmic_frontmatter`). However, this creates unnecessary computation on the user's device.

**Consequences:**
- **Performance:** Parsing markdown (especially with YAML front matter) on each info popup can introduce 100-300ms latency on mobile devices
- **Inconsistent structure handling:** SKILL.md files may have varying markdown structures, requiring defensive parsing logic duplicated across frontend
- **Memory overhead:** Loading and parsing multiple SKILL.md files client-side increases memory footprint
- **Cache invalidation complexity:** Frontend must track when skill files change to invalidate parsed data

**Prevention:**
- **Backend responsibility:** Parse SKILL.md files on the backend when the `/api/skills` endpoint is called
- **Enhanced API response:** Return structured data with `name`, `description`, `features` (array), and `skillPath` fields
- **Single source of truth:** Backend validates markdown structure using consistent parser (Python's `python-frontmatter` library)
- **Frontend simplicity:** Flutter only renders pre-parsed data from API

**Detection:**
- Warning signs: Multiple markdown parsing packages in `pubspec.yaml`
- Frontend code contains YAML or front matter parsing logic
- Performance profiling shows skill info popups taking >200ms to render

**Implementation guidance:**
```python
# Backend: app/api/skills.py
from pathlib import Path
import frontmatter

def parse_skill_metadata(skill_path: Path) -> dict:
    """Parse SKILL.md front matter and extract features."""
    with open(skill_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    return {
        'name': post.get('name', skill_path.parent.name),
        'description': post.get('description', ''),
        'features': extract_features(post.content),  # Parse markdown body
        'skill_path': str(skill_path.relative_to(project_root))
    }
```

---

### Pitfall 2: Breaking Existing Skill Prepend Mechanism

**What goes wrong:** Adding UI enhancements (browsable list, info popups, chips) inadvertently changes how skills are prepended to messages, causing the prepend logic to break or duplicate.

**Why it happens:** The existing transparent `/skill-name` prepend works correctly. When adding new UI components (bottom sheet, chips, selection indicators), developers refactor the message-sending logic without preserving the exact prepend behavior.

**Consequences:**
- **Broken skill invocation:** Skills no longer activate because prepend format changes (e.g., `/business-analyst` becomes `skill:business-analyst`)
- **Double prepend:** Skill appears twice in message (once from chip state, once from old logic)
- **Lost transparency:** User sees skill name in their message history instead of transparent background prepend
- **Regression in existing threads:** Conversations that worked before enhancement fail after upgrade

**Prevention:**
- **Test existing prepend first:** Write integration tests capturing current behavior before making any changes
- **Preserve prepend layer separation:** Keep prepend logic in a single, isolated function that UI components call
- **UI is presentation only:** Chips, badges, and popups DISPLAY skill selection state but don't implement prepend logic
- **Add, don't replace:** New UI components should be additive—existing `SkillSelector` PopupMenu keeps working

**Detection:**
- Warning signs: Message send logic modified in multiple places
- `onSend` callback in `AssistantChatInput` changed to handle skills differently
- Provider's skill state used directly in message string concatenation instead of dedicated prepend function

**Implementation guidance:**
```dart
// CORRECT: Single prepend function, UI just sets state
void _handleSend() {
  final text = _controller.text.trim();
  final messageWithSkill = _prependSkillIfSelected(text, provider.selectedSkill);
  widget.onSend(messageWithSkill);  // Same callback signature
}

String _prependSkillIfSelected(String message, Skill? skill) {
  if (skill == null) return message;
  return '/${skill.name} $message';  // Preserve exact format
}

// WRONG: UI directly manipulates message
void _handleSend() {
  final text = _controller.text.trim();
  final prefix = provider.selectedSkill != null
      ? 'Use skill ${provider.selectedSkill!.name}: '
      : '';
  widget.onSend('$prefix$text');  // Changed prepend format!
}
```

---

### Pitfall 3: State Management Refactor Without Testing

**What goes wrong:** Adding skill selection state to `AssistantConversationProvider` triggers unintended widget rebuilds across the entire chat UI, causing performance issues or lost scroll position.

**Why it happens:** Flutter's `ChangeNotifier` pattern calls `notifyListeners()` on every state change. Adding skill selection state can trigger rebuilds of message list, input field, and other unrelated widgets if not properly scoped.

**Consequences:**
- **Input field loses focus:** User selects a skill from bottom sheet, input field rebuilds and loses cursor position
- **Message list scrolls to top:** Selecting a skill triggers provider update, message list rebuilds and resets scroll
- **Excessive rebuilds:** Every skill selection causes entire conversation screen to rebuild (60+ widgets)
- **Animation jank:** Bottom sheet animations stutter because parent widget is rebuilding

**Prevention:**
- **Use `select()` or `Consumer` with child:** Rebuild only widgets that depend on specific provider properties
- **Separate providers for UI state:** Keep skill selection state in a dedicated `SkillProvider` or local widget state
- **Test scroll preservation:** Automated tests should verify message list scroll position survives skill selection
- **Profile rebuilds:** Use Flutter DevTools to verify only affected widgets rebuild on skill selection

**Detection:**
- Warning signs: Input field loses focus when opening skill selector
- Scroll position jumps when selecting a skill
- DevTools shows 50+ widget rebuilds on skill selection
- Frame rendering time spikes during skill selection

**Implementation guidance:**
```dart
// CORRECT: Scoped rebuilds using select()
class AssistantChatInput extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // Only rebuild chip area when skill changes
    final selectedSkill = context.select<AssistantConversationProvider, Skill?>(
      (provider) => provider.selectedSkill,
    );

    return Column(
      children: [
        if (selectedSkill != null) _SkillChip(skill: selectedSkill),
        _InputField(),  // Doesn't rebuild when skill changes
      ],
    );
  }
}

// WRONG: Entire input rebuilds on any provider change
class AssistantChatInput extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AssistantConversationProvider>();
    // Everything rebuilds whenever provider.notifyListeners() is called
    return Column(
      children: [
        if (provider.selectedSkill != null) Chip(...),
        TextField(...),
      ],
    );
  }
}
```

---

### Pitfall 4: Tooltip/Popup Overflow on Mobile Screens

**What goes wrong:** Info popups/tooltips for skill descriptions render off-screen or get clipped on mobile devices, making skill features unreadable.

**Why it happens:** Flutter's built-in `Tooltip` widget has limited overflow handling. When a skill info popup is triggered near screen edges, it may not auto-flip or clamp to viewport bounds.

**Consequences:**
- **Unusable on mobile:** Skill info button is tappable, but tooltip content is hidden above screen top or below keyboard
- **Inconsistent UX:** Tooltips work on desktop (wide viewport) but fail on mobile (narrow viewport)
- **User confusion:** Users think the info button is broken because they can't see the tooltip
- **Platform-specific bugs:** iOS keyboard covers tooltip, Android tooltip renders behind system UI

**Prevention:**
- **Use overlay-aware packages:** Prefer `super_tooltip`, `just_tooltip`, or `df_tooltip` over built-in `Tooltip`
- **Test on smallest screen:** Verify tooltips on 320px wide screen (iPhone SE) with keyboard open
- **Auto-flip positioning:** Configure tooltips to flip from top to bottom when near screen edges
- **Screen margin safety:** Set minimum distance from viewport edges (e.g., `screenMargin: 8`)
- **Dismiss on scroll:** Auto-close tooltips when skill list scrolls to prevent orphaned popups

**Detection:**
- Warning signs: Tooltip renders partially off-screen on narrow devices
- Tooltip doesn't appear when tapped on mobile (actually off-screen above)
- Tooltip position is hardcoded (e.g., `preferBelow: true` with no fallback)

**Implementation guidance:**
```dart
// CORRECT: Overflow-aware tooltip with auto-flip
SuperTooltip(
  content: Text(skill.features.join('\n')),
  popupDirection: TooltipDirection.up,  // Prefers up, but auto-flips
  arrowTipDistance: 10,
  minimumOutsideMargin: 8,  // Minimum 8px from screen edges
  hasShadow: true,
  showCloseButton: ShowCloseButton.inside,
  onDismiss: () => _closeTooltip(),
  child: IconButton(
    icon: Icon(Icons.info_outline),
    onPressed: () => _showTooltip(),
  ),
);

// WRONG: Built-in tooltip with no overflow handling
Tooltip(
  message: skill.features.join('\n'),  // Can be very long
  preferBelow: true,  // No fallback if below doesn't fit
  child: IconButton(
    icon: Icon(Icons.info_outline),
    onPressed: () {},
  ),
);
```

---

## Moderate Pitfalls

Issues causing user confusion or requiring workarounds.

---

### Pitfall 5: Inconsistent Skill Deselection UX

**What goes wrong:** Users can select a skill but have no clear way to deselect it, or deselection behavior is inconsistent (chip close vs. selector re-tap).

**Why it happens:** Developers focus on "select skill" flow but don't define "clear skill" interaction patterns consistently across chip, bottom sheet, and popup menu.

**Consequences:**
- **Trapped selection:** User selects wrong skill, can't easily clear it without selecting another
- **Confusing chip behavior:** Chip shows "X" close icon, but tapping skill selector again doesn't toggle
- **Inconsistent patterns:** Chip close removes skill, but re-tapping skill in selector doesn't deselect
- **Accessibility issue:** Screen reader users can't discover deselection method

**Prevention:**
- **Multiple deselection paths:** Support both chip close AND re-tapping selected skill in selector
- **Visual feedback:** Selected skill in bottom sheet shows checkmark or different background
- **Clear affordance:** Chip close icon is always visible and interactive
- **Consistent terminology:** Use "Clear" or "Remove" consistently in UI and code

**Implementation guidance:**
```dart
// Bottom sheet skill list item
ListTile(
  leading: Icon(
    isSelected ? Icons.check_circle : Icons.circle_outlined,
  ),
  title: Text(skill.displayName),
  selected: isSelected,
  onTap: () {
    if (isSelected) {
      provider.clearSkill();  // Deselect by re-tapping
    } else {
      provider.selectSkill(skill);
    }
    Navigator.pop(context);
  },
);

// Chip with consistent close behavior
Chip(
  label: Text(skill.displayName),
  deleteIcon: Icon(Icons.close),
  onDeleted: provider.clearSkill,  // Same method
);
```

---

### Pitfall 6: Bottom Sheet Performance with Large Skill Lists

**What goes wrong:** Opening a bottom sheet with 10+ skills causes lag, animation jank, or slow rendering on lower-end devices.

**Why it happens:** Bottom sheet builder is called repeatedly during animation, and each rebuild constructs all skill list items (even those not visible).

**Consequences:**
- **Laggy open animation:** Bottom sheet takes 500ms+ to open instead of smooth 300ms animation
- **Frame drops:** Rendering drops below 60fps during bottom sheet drag gestures
- **Poor UX on budget devices:** Skill selector feels broken on older Android phones
- **Memory spikes:** All skill widgets constructed upfront, even if only 3 are visible

**Prevention:**
- **Use `ListView.builder`:** Lazy-load skill list items, only build visible items
- **Set `isScrollControlled: true`:** Required for bottom sheets with scrollable content
- **Avoid deep nesting:** Flatten widget tree in bottom sheet content
- **Preload skill data:** Fetch and cache skills before showing bottom sheet (avoid FutureBuilder inside sheet)

**Implementation guidance:**
```dart
// CORRECT: Lazy-loading bottom sheet
showModalBottomSheet(
  context: context,
  isScrollControlled: true,
  builder: (context) {
    final skills = context.read<SkillProvider>().skills;  // Already loaded
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      builder: (context, scrollController) {
        return ListView.builder(  // Lazy build
          controller: scrollController,
          itemCount: skills.length,
          itemBuilder: (context, index) => _SkillListItem(skills[index]),
        );
      },
    );
  },
);

// WRONG: Builds all items upfront
showModalBottomSheet(
  context: context,
  builder: (context) {
    return FutureBuilder<List<Skill>>(  // Rebuilds during animation
      future: skillService.getSkills(),
      builder: (context, snapshot) {
        return Column(  // All children built immediately
          children: snapshot.data?.map((s) => ListTile(...)).toList() ?? [],
        );
      },
    );
  },
);
```

---

### Pitfall 7: Skill Chip Visual Confusion with File Chips

**What goes wrong:** Skill chips and file attachment chips look too similar, causing users to confuse them or accidentally delete the wrong chip.

**Why it happens:** Both use `Chip` widget with similar styling, and developers don't differentiate with color, icon, or label styling.

**Consequences:**
- **User deletes wrong chip:** Tries to remove file attachment, removes skill instead
- **Visual clutter:** Two chip types with identical styling create noisy UI
- **Accessibility issue:** Screen reader announces both as "Chip" with no distinguishing information
- **Scaling issue:** When 3+ files + skill are selected, chip area becomes unreadable

**Prevention:**
- **Different background colors:** Skill chip uses `secondaryContainer`, file chips use `tertiaryContainer`
- **Different icons:** Skill uses `add_box_outlined`, file uses `description` or `attach_file`
- **Visual hierarchy:** Skill chip appears first (left), file chips follow
- **Semantic labels:** Chip labels include type prefix for screen readers

**Implementation guidance:**
```dart
// Skill chip (distinct styling)
Chip(
  avatar: Icon(Icons.add_box_outlined, size: 18),  // Unique icon
  label: Text(skill.displayName, style: TextStyle(fontSize: 13)),
  deleteIcon: Icon(Icons.close, size: 18),
  onDeleted: provider.clearSkill,
  backgroundColor: theme.colorScheme.secondaryContainer,  // Distinct color
  semanticLabel: 'Skill: ${skill.displayName}',  // Screen reader
);

// File chip (different styling)
Chip(
  avatar: Icon(Icons.description, size: 18),  // Different icon
  label: Text(file.name, style: TextStyle(fontSize: 13)),
  deleteIcon: Icon(Icons.close, size: 18),
  onDeleted: () => provider.removeFile(file),
  backgroundColor: theme.colorScheme.tertiaryContainer,  // Different color
  semanticLabel: 'Attached file: ${file.name}',  // Screen reader
);
```

---

### Pitfall 8: SKILL.md Structure Assumptions

**What goes wrong:** Backend parser assumes all SKILL.md files have front matter with specific fields, causing parsing failures or missing data when skill files vary.

**Why it happens:** Developer writes parser based on one example skill file (e.g., `business-analyst/SKILL.md`) without testing against all skill files or handling edge cases.

**Consequences:**
- **Missing skills in list:** Skills without front matter are excluded from `/api/skills` response
- **Parse errors logged:** Backend logs errors for skills with TOML or JSON front matter (not YAML)
- **Graceful degradation failure:** Parser crashes instead of returning partial data
- **Incomplete descriptions:** Parser expects front matter `description` but skill has it in markdown body

**Prevention:**
- **Defensive parsing:** Handle missing front matter gracefully (use filename as name fallback)
- **Support multiple formats:** YAML, TOML, and JSON front matter should all work
- **Fallback to markdown body:** If front matter missing, extract description from first paragraph
- **Schema validation:** Define expected fields but don't require all (use defaults)
- **Test with all skill files:** Integration test parsing every `.claude/*/SKILL.md` file

**Implementation guidance:**
```python
# CORRECT: Defensive parsing with fallbacks
def parse_skill(skill_path: Path) -> dict:
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
    except Exception as e:
        logger.warning(f"Failed to parse {skill_path}: {e}")
        post = frontmatter.loads('')  # Empty front matter

    # Fallbacks for missing fields
    name = post.get('name') or skill_path.parent.name
    description = post.get('description') or extract_first_paragraph(post.content)

    return {
        'name': name,
        'description': description[:200],  # Truncate long descriptions
        'features': extract_features(post.content) or [],
        'skill_path': str(skill_path.relative_to(project_root))
    }

# WRONG: Assumes all fields exist
def parse_skill(skill_path: Path) -> dict:
    post = frontmatter.load(open(skill_path))  # Can crash
    return {
        'name': post['name'],  # KeyError if missing
        'description': post['description'],  # KeyError if missing
    }
```

---

## Minor Pitfalls

Issues causing minor annoyances or edge case failures.

---

### Pitfall 9: Skill Info Popup Content Too Long

**What goes wrong:** Skill feature lists are very long (10+ bullets), causing info popup to overflow screen or require awkward scrolling.

**Why it happens:** Developer displays all features from SKILL.md without truncating or paginating, assuming content will be short.

**Consequences:**
- **Unreadable on mobile:** Popup shows 3 features, rest cut off with no scroll affordance
- **Tooltip dismissed accidentally:** User tries to scroll, gesture triggers tooltip close instead
- **Information overload:** User wants quick overview, sees wall of text

**Prevention:**
- **Truncate to top 3-5 features:** Show most important features, add "View full description" link
- **Use modal for full info:** Info icon opens bottom sheet with scrollable full content
- **Progressive disclosure:** Show summary in tooltip, full details in dedicated screen
- **Character limits:** Cap feature descriptions at 100 characters each

**Implementation guidance:**
```dart
// Show top 3 features in tooltip
final topFeatures = skill.features.take(3).toList();
final hasMore = skill.features.length > 3;

SuperTooltip(
  content: Column(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(skill.description, style: TextStyle(fontWeight: FontWeight.bold)),
      SizedBox(height: 8),
      ...topFeatures.map((f) => Text('• $f')),
      if (hasMore)
        TextButton(
          child: Text('View ${skill.features.length - 3} more...'),
          onPressed: () => _showFullSkillInfo(skill),
        ),
    ],
  ),
  child: IconButton(icon: Icon(Icons.info_outline)),
);
```

---

### Pitfall 10: Skill Selector Cache Invalidation

**What goes wrong:** User adds a new skill file to `.claude/` directory, but skill selector doesn't show it until app restart.

**Why it happens:** `SkillService` caches skills after first load and never refreshes, assuming skills are static.

**Consequences:**
- **Stale skill list:** Newly added skills invisible until cache cleared
- **Developer confusion:** Added skill file but can't select it in UI
- **Manual workaround required:** User must restart app to see new skills

**Prevention:**
- **Add refresh method:** `SkillService.refreshSkills()` clears cache and reloads
- **Pull-to-refresh on skill list:** Bottom sheet supports pull-to-refresh gesture
- **Time-based expiration:** Cache skills for 5 minutes, auto-refresh after expiry
- **Watch for file changes:** Advanced—use file watcher to invalidate cache when `.claude/` changes

**Implementation guidance:**
```dart
class SkillService {
  List<Skill>? _cachedSkills;
  DateTime? _cacheTimestamp;
  static const _cacheDuration = Duration(minutes: 5);

  Future<List<Skill>> getSkills({bool forceRefresh = false}) async {
    final now = DateTime.now();
    final isCacheValid = _cacheTimestamp != null &&
        now.difference(_cacheTimestamp!) < _cacheDuration;

    if (!forceRefresh && isCacheValid && _cachedSkills != null) {
      return _cachedSkills!;
    }

    try {
      final response = await _dio.get('/api/skills');
      _cachedSkills = (response.data as List)
          .map((json) => Skill.fromJson(json))
          .toList();
      _cacheTimestamp = now;
      return _cachedSkills!;
    } catch (e) {
      debugPrint('Failed to load skills: $e');
      return _cachedSkills ?? [];  // Return stale cache on error
    }
  }

  void clearCache() {
    _cachedSkills = null;
    _cacheTimestamp = null;
  }
}
```

---

### Pitfall 11: Chip Close Icon Too Small on Mobile

**What goes wrong:** Skill chip close "X" icon is only 18px, making it hard to tap accurately on mobile touchscreens.

**Why it happens:** Material Design default chip sizing prioritizes density over touch target size.

**Consequences:**
- **Frustrating UX:** User taps close icon 2-3 times before successfully removing chip
- **Accidental whole-chip taps:** Trying to tap close icon triggers chip tap instead
- **Accessibility violation:** Touch target smaller than recommended 44x44px minimum

**Prevention:**
- **Material guidelines:** Minimum 48x48dp touch target for interactive elements
- **Increase icon size:** Use `deleteIconSize: 20` or larger
- **Add padding around icon:** Use `visualDensity: VisualDensity.comfortable`
- **Increase minimum tap area:** Wrap close icon in `InkWell` with explicit constraints

**Implementation guidance:**
```dart
// CORRECT: Accessible close icon
Chip(
  label: Text(skill.displayName),
  deleteIcon: Icon(Icons.close, size: 20),  // Slightly larger
  onDeleted: provider.clearSkill,
  materialTapTargetSize: MaterialTapTargetSize.padded,  // Minimum tap size
  visualDensity: VisualDensity.comfortable,  // More padding
);
```

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **SKILL.md Parsing** | Pitfall 1 (frontend parsing), Pitfall 8 (structure assumptions) | Parse on backend, defensive parsing with fallbacks |
| **Browsable Skill List** | Pitfall 6 (bottom sheet performance) | Use `ListView.builder`, `isScrollControlled: true` |
| **Info Popups** | Pitfall 4 (overflow), Pitfall 9 (content too long) | Use overflow-aware tooltip package, truncate to top 3-5 features |
| **Selection Chips** | Pitfall 7 (visual confusion), Pitfall 11 (close icon too small) | Distinct colors/icons, larger touch targets |
| **State Management** | Pitfall 3 (refactor without testing) | Use `select()`, separate providers, profile rebuilds |
| **Integration** | Pitfall 2 (breaking existing prepend) | Preserve existing prepend logic, integration tests |
| **UX Consistency** | Pitfall 5 (deselection UX) | Multiple deselection paths, visual feedback |
| **Caching** | Pitfall 10 (cache invalidation) | Time-based expiration, pull-to-refresh |

---

## Integration Pitfalls (Existing System)

### Pitfall 12: Breaking Existing AssistantChatInput Layout

**What goes wrong:** Adding new skill UI elements (browsable list button, info icons) breaks the existing layout balance between attachment, text input, skills, and send buttons.

**Why it happens:** Current layout uses `Row` with `Expanded` text field and fixed-width buttons. Adding more buttons or replacing `SkillSelector` causes overflow or cramped input.

**Consequences:**
- **Horizontal overflow:** Too many buttons in input row cause layout exception on narrow screens
- **Input field too narrow:** Text field shrinks to unusable width when buttons added
- **Button grouping broken:** Send and skills buttons no longer visually grouped on right

**Prevention:**
- **Preserve existing button positions:** Keep attachment left, skills+send grouped right
- **Modal for browsable list:** Don't add inline button—open bottom sheet from existing skills button
- **Chip area above input:** Skill chip already appears above input row, don't modify row layout
- **Responsive button sizing:** Use `IconButton` (48x48) on mobile, can show labels on desktop

**Implementation guidance:**
```dart
// CORRECT: Preserve existing layout, extend skills button functionality
Row(
  crossAxisAlignment: CrossAxisAlignment.end,
  children: [
    // Attachment (left) - unchanged
    IconButton(icon: Icon(Icons.attach_file), onPressed: _handleAttach),

    // Text input - unchanged
    Expanded(child: TextField(...)),

    // Skills button (right, grouped with send) - enhanced to open bottom sheet
    SkillSelector(
      onSkillSelected: provider.selectSkill,
      showBrowsableList: true,  // New feature, same button
    ),

    // Send button (right) - unchanged
    IconButton.filled(icon: Icon(Icons.send), onPressed: _handleSend),
  ],
);

// WRONG: Adds new buttons causing overflow
Row(
  children: [
    IconButton(icon: Icon(Icons.attach_file)),
    IconButton(icon: Icon(Icons.list)),  // Browse skills button - NEW
    Expanded(child: TextField(...)),
    IconButton(icon: Icon(Icons.add_box)),  // Skills popup - existing
    IconButton(icon: Icon(Icons.info)),  // Info button - NEW (overflow!)
    IconButton.filled(icon: Icon(Icons.send)),
  ],
);
```

---

### Pitfall 13: ChangeNotifier Leak in SkillSelector

**What goes wrong:** `SkillSelector` widget creates `SkillService` instance in widget build method, causing memory leaks or unnecessary API calls.

**Why it happens:** Current implementation creates `SkillService()` directly in widget without proper lifecycle management.

**Consequences:**
- **Multiple service instances:** Each rebuild creates new `SkillService`, cache doesn't work
- **Memory leak:** Service instances never disposed, accumulate in memory
- **Redundant API calls:** Cache scoped to widget instance, rebuilds trigger new API calls

**Prevention:**
- **Singleton pattern:** Make `SkillService` a singleton accessible via `SkillService.instance`
- **Provider pattern:** Inject `SkillService` via Provider at app level
- **StatefulWidget:** Create service in `initState()`, dispose in `dispose()`

**Implementation guidance:**
```dart
// CORRECT: Singleton service
class SkillService {
  static final SkillService _instance = SkillService._internal();
  factory SkillService() => _instance;
  SkillService._internal();

  List<Skill>? _cachedSkills;
  // ... rest of implementation
}

// OR: Provider injection
void main() {
  runApp(
    MultiProvider(
      providers: [
        Provider<SkillService>(create: (_) => SkillService()),
        // ... other providers
      ],
      child: MyApp(),
    ),
  );
}

class SkillSelector extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final skillService = context.read<SkillService>();  // Injected
    // ... rest of implementation
  }
}
```

---

### Pitfall 14: Flutter 3.38+ Breaking Changes with Overlays

**What goes wrong:** Using deprecated `OverlayPortal.targetsRootOverlay` for skill info popups causes runtime warnings or breaks in future Flutter versions.

**Why it happens:** Flutter 3.38 deprecated this constructor in favor of new overlay architecture, but existing tutorials still reference it.

**Consequences:**
- **Deprecation warnings:** Console fills with warnings during development
- **Future breakage:** May stop working in Flutter 4.0 when deprecated APIs removed
- **Migration effort:** Need to refactor overlay logic later when it breaks

**Prevention:**
- **Use non-deprecated APIs:** Check Flutter 3.38+ migration guide before implementing overlays
- **Modern packages:** Use `super_tooltip`, `just_tooltip`, or `df_tooltip` (updated for 3.38+)
- **Test on latest Flutter:** Run on Flutter 3.41+ to catch deprecations early

**Implementation guidance:**
```dart
// CORRECT: Use modern overlay approach (Flutter 3.38+)
OverlayPortal(
  controller: _overlayController,
  overlayChildBuilder: (context) {
    return CompositedTransformFollower(
      link: _layerLink,
      targetAnchor: Alignment.topCenter,
      followerAnchor: Alignment.bottomCenter,
      child: SkillInfoCard(skill: skill),
    );
  },
  child: CompositedTransformTarget(
    link: _layerLink,
    child: IconButton(
      icon: Icon(Icons.info_outline),
      onPressed: () => _overlayController.toggle(),
    ),
  ),
);

// WRONG: Deprecated API (Flutter 3.38+)
OverlayPortal.targetsRootOverlay(  // DEPRECATED
  controller: _overlayController,
  overlayChildBuilder: (context) => SkillInfoCard(skill: skill),
  child: IconButton(icon: Icon(Icons.info_outline)),
);
```

---

## Sources

### Markdown Parsing & Front Matter
- [Decoding Agent Skills Markdown](https://atlassc.net/2026/01/19/decoding-agent-skills-markdown)
- [front_matter_ml Dart Package](https://pub.dev/packages/front_matter_ml)
- [Markdown Parsing in Dart – Corner Software](https://csdcorp.com/blog/coding/markdown-parsing-in-dart/)

### Flutter Bottom Sheet Performance
- [Top 5 Common BottomSheet Mistakes Flutter Developers Make](https://medium.com/easy-flutter/top-5-common-bottomsheet-mistakes-flutter-developers-make-and-how-to-avoid-them-447a6b991e52)
- [Concerns regarding performance of modal bottom sheets in Flutter](https://copyprogramming.com/howto/flutter-modal-bottom-sheet-performance-issue)

### State Management
- [Flutter State Management in 2026: Choosing the Right Approach](https://medium.com/@Sofia52/flutter-state-management-in-2026-choosing-the-right-approach-811b866d9b1b)
- [The Ultimate Guide to Flutter State Management in 2026](https://medium.com/@satishparmarparmar486/the-ultimate-guide-to-flutter-state-management-in-2026-from-setstate-to-bloc-riverpod-561192c31e1c)

### Tooltip & Popup Positioning
- [super_tooltip Flutter Package](https://pub.dev/packages/super_tooltip)
- [just_tooltip Flutter Package](https://pub.dev/packages/just_tooltip)
- [df_tooltip Flutter Package](https://pub.dev/packages/df_tooltip)
- [flutter/dart popup tooltips poorly positioned](https://github.com/flutter/flutter/issues/22912)

### FastAPI Performance
- [FastAPI Performance Tuning & Caching Strategy 101](https://blog.greeden.me/en/2026/02/03/fastapi-performance-tuning-caching-strategy-101-a-practical-recipe-for-growing-a-slow-api-into-a-lightweight-fast-api/)
- [How to optimize API response time in a Flutter application with heavy JSON parsing?](https://github.com/orgs/community/discussions/174980)

### Flutter Breaking Changes
- [Flutter 3.38: New Features & Breaking Changes + Migration Guide](https://vagary.tech/blog/flutter-3-38-release-notes-breaking-changes-migration-guide)
- [What's new in Flutter 3.41](https://blog.flutter.dev/whats-new-in-flutter-3-41-302ec140e632)

---

*Research completed: 2026-02-18*
*Confidence: HIGH (verified with official docs, current packages, existing codebase)*
