# Feature Research: Skill Discovery & Selection UI

**Domain:** Chat application skill picker / command palette
**Researched:** 2026-02-18
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Browsable skill list | Users need to see what's available without memorizing commands | LOW | Already have API returning skills; need UI component |
| Skill descriptions | Users need to know what each skill does before selecting | LOW | Already returned by API; display in UI |
| Visual selection indicator | Users need confirmation of which skill they've selected | LOW | Chip/badge pattern standard in modern UIs |
| Keyboard-friendly navigation | Power users expect arrow keys + Enter in list interfaces | MEDIUM | Flutter ListTile supports focus navigation by default |
| Touch-friendly selection | Mobile/tablet users expect tap-to-select | LOW | Flutter bottom sheet + ListTile handles this natively |
| Loading states | Users expect feedback while skills load from API | LOW | Already implemented in current PopupMenuButton |
| Error states | Users expect graceful degradation when API fails | LOW | Already implemented in current PopupMenuButton |
| Empty states | Users expect clear messaging when no skills available | LOW | Already implemented in current PopupMenuButton |
| Skill name display | Users expect human-readable names (not file names) | LOW | Already implemented via `displayName` getter |
| Modal dismissal | Users expect tap-outside or back button to cancel | LOW | Flutter bottom sheet provides this by default |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Inline skill help/info | View detailed skill info without leaving selection flow | MEDIUM | Info icon next to each skill opens detailed description modal |
| Skill categorization | Organize skills by type (analysis, coding, testing, etc.) | MEDIUM | Requires API changes to add category metadata |
| Skill search/filter | Find skills faster when list grows beyond ~10 items | MEDIUM | TextFormField at top of bottom sheet with live filtering |
| Recent skills first | Surface frequently-used skills for faster access | MEDIUM | Requires usage tracking and local storage |
| Skill usage hints | Show example prompts or use cases | MEDIUM | Requires extended metadata from SKILL.md files |
| Keyboard shortcut to open picker | Power user efficiency (e.g., Cmd+K or Ctrl+K) | LOW | Flutter keyboard shortcuts straightforward |
| Skill preview/quick look | Hover/long-press shows tooltip with brief description | LOW | Use rich tooltip on skill list items |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multi-skill selection | Users want to combine skills | Skills prepend `/skill-name` to message - multiple would conflict | Single skill per message; users can switch skills mid-conversation |
| Skill favorites/pinning | Users want quick access to top skills | Adds UI complexity and settings management overhead | Recent skills (auto-detected) + search when list grows |
| Custom skill creation from UI | Users want to add skills without files | Violates single-source-of-truth (.claude/ directory); sync nightmare | Document how to create .claude/skill-name/SKILL.md |
| Always-visible skill bar | Users want skills visible without clicking | Clutters chat input area; mobile space constrained | Button trigger + full-screen browsable list |
| Skill auto-suggestion based on message | AI suggests relevant skill for typed message | Adds latency and complexity; may annoy users with wrong suggestions | Clear skill button always available; user decides when needed |

## Feature Dependencies

```
Browsable Skill List
    └──requires──> GET /api/skills (EXISTS)
    └──requires──> Skill model (EXISTS)

Visual Selection Indicator (Chip)
    └──requires──> Browsable Skill List

Skill Info Popup
    └──requires──> Browsable Skill List
    └──enhances──> Skill descriptions

Skill Search/Filter
    └──requires──> Browsable Skill List
    └──enhances──> Large skill counts (10+ skills)

Keyboard Shortcut to Open
    └──requires──> Browsable Skill List
    └──enhances──> Power user workflow
```

### Dependency Notes

- **Browsable Skill List requires GET /api/skills:** API already exists and returns name, description, skill_path
- **Visual Selection Indicator requires Browsable Skill List:** Can't show selection before user can browse/select
- **Skill Info Popup enhances Skill descriptions:** Provides expanded view of existing description field
- **Skill Search enhances Large skill counts:** Only valuable when users have 10+ skills installed

## MVP Definition

### Launch With (This Milestone)

Minimum viable enhancement to existing skill selector.

- [x] **GET /api/skills endpoint** — Already exists, returns skill metadata
- [x] **Skill model with displayName** — Already exists in frontend
- [x] **SkillService with caching** — Already exists
- [ ] **Bottom sheet modal** — Replace PopupMenuButton with showModalBottomSheet
- [ ] **Scrollable skill list** — ListView.builder with all available skills
- [ ] **Skill descriptions inline** — Show description under each skill name
- [ ] **Visual selection (chip)** — Show selected skill as removable chip in input area
- [ ] **Tap-to-select interaction** — ListTile onTap selects skill and closes sheet
- [ ] **Loading/error/empty states** — Port existing states from PopupMenuButton

### Add After Validation (v1.x)

Features to add once core browsing works and user feedback is gathered.

- [ ] **Skill info popup** — Info icon next to each skill; tap opens detailed modal with full SKILL.md content
- [ ] **Skill search/filter** — TextField at top of bottom sheet for live filtering (trigger: 10+ skills installed)
- [ ] **Keyboard shortcut** — Cmd+K or Ctrl+K to open skill picker (trigger: power user request)
- [ ] **Skill preview tooltips** — Long-press or hover shows quick description (trigger: mobile usability testing)

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Skill categorization** — Group skills by type (trigger: 20+ skills installed, needs API schema change)
- [ ] **Recent skills first** — Sort by usage frequency (trigger: analytics show repeated skill usage)
- [ ] **Skill usage hints** — Example prompts per skill (trigger: user requests for "how do I use this skill?")

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Bottom sheet modal | HIGH | LOW | P1 |
| Scrollable skill list | HIGH | LOW | P1 |
| Inline descriptions | HIGH | LOW | P1 |
| Visual selection chip | HIGH | LOW | P1 |
| Loading/error states | HIGH | LOW | P1 |
| Skill info popup | MEDIUM | MEDIUM | P2 |
| Skill search/filter | MEDIUM | MEDIUM | P2 |
| Keyboard shortcut | MEDIUM | LOW | P2 |
| Skill preview tooltips | LOW | LOW | P2 |
| Skill categorization | MEDIUM | HIGH | P3 |
| Recent skills first | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for milestone completion (table stakes)
- P2: Should have, add when requested or when list grows
- P3: Nice to have, defer until proven need

## Competitor Feature Analysis

| Feature | VS Code Command Palette | Slack Slash Commands | Our Approach |
|---------|------------------------|---------------------|--------------|
| Trigger | Ctrl+Shift+P keyboard shortcut | Type `/` in message field | Tap skill button in chat input |
| Display | Modal centered on screen, fuzzy search | Dropdown above message field | Bottom sheet modal (mobile-friendly) |
| Filtering | Live fuzzy search as you type | Live prefix filtering | Scrollable list; search optional (P2) |
| Selection | Arrow keys + Enter or click | Arrow keys + Enter or click | Tap or keyboard navigation |
| Info display | Command name + category + shortcut | Command name + usage hint | Skill name + description + info icon (P2) |
| Persistence | None (ephemeral, re-opens empty) | Recent commands shown first | Selected skill shown as chip until removed |

### Key Insights from Competitors

**VS Code Command Palette:**
- Keyboard-first design (Ctrl+Shift+P universal trigger)
- Fuzzy search essential for hundreds of commands
- Command names show default keyboard shortcuts alongside
- Can drag to reposition palette
- *Takeaway:* Keyboard shortcut valuable for power users; defer search until skill count > 10

**Slack Slash Commands:**
- Autocomplete menu appears inline above message field
- Real-time prefix filtering as you type `/rem` → shows `/remind`
- Usage hints shown in menu (e.g., `/remind [who] [what] [when]`)
- Works identically on mobile and desktop
- *Takeaway:* Inline descriptions critical; mobile parity important

**Flutter Bottom Sheet (Platform Pattern):**
- Native mobile pattern for browsable option lists
- Swipe-to-dismiss standard gesture
- DraggableScrollableSheet supports partial → full-screen expansion
- *Takeaway:* Use platform conventions; bottom sheet ideal for touch interfaces

## Implementation Pattern Recommendations

Based on research, the recommended implementation follows these patterns:

### 1. Bottom Sheet Modal (vs. Popup Menu)

**Why:**
- Flutter best practice for browsable lists on mobile
- Native swipe-to-dismiss gesture
- More screen space for descriptions
- Scrollable for unlimited skill count

**Implementation:**
```dart
showModalBottomSheet(
  context: context,
  isScrollControlled: true,
  shape: RoundedRectangleBorder(
    borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
  ),
  builder: (context) => SkillPickerSheet(),
);
```

### 2. Selection Indicator (Chip/Badge Pattern)

**Why:**
- Standard UI pattern for selected items in input contexts
- Clearly shows active skill
- Removable (tap X to deselect)
- Doesn't obscure input field

**Implementation:**
- Use Material `Chip` widget with `onDeleted` callback
- Position before text input field in Row/Wrap
- Use accent color for selected state

**Examples from research:**
- Chat apps (Slack emoji react chip)
- Email clients (recipient chips)
- Tag selectors

### 3. Info Popup (Tooltip vs. Modal)

**Why:**
- Users need skill details without leaving selection flow
- Tooltips too small for SKILL.md content
- Modal allows scrollable full content

**Implementation (P2 feature):**
- Info icon (IconButton with `Icons.info_outline`) next to skill name
- Tap opens full-screen dialog with SKILL.md markdown rendered
- Allow copy-to-clipboard for skill path

**Accessibility:**
- Use `role="tooltip"` equivalent (Semantics widget)
- 4.5:1 contrast ratio minimum
- Dismissible with back button or tap-outside

### 4. Skill List Display

**Why:**
- Users need to scan available skills quickly
- Descriptions provide context without opening info popup
- Visual hierarchy: name bold, description subtle

**Implementation:**
```dart
ListView.builder(
  itemCount: skills.length,
  itemBuilder: (context, index) {
    final skill = skills[index];
    return ListTile(
      title: Text(skill.displayName, style: TextStyle(fontWeight: FontWeight.bold)),
      subtitle: Text(skill.description, style: TextStyle(fontSize: 12)),
      trailing: IconButton(icon: Icon(Icons.info_outline), onTap: () => _showSkillInfo(skill)),
      onTap: () => _selectSkill(skill),
    );
  },
);
```

## Sources

### Design Patterns & Best Practices
- [Chat UI Design Patterns 2026](https://muz.li/inspiration/chat-ui/)
- [Command Palette UX Patterns](https://medium.com/design-bootcamp/command-palette-ux-patterns-1-d6b6e68f30c1)
- [Badges vs Chips/Tags Guide](https://medium.com/design-bootcamp/ux-blueprint-03-badges-vs-chips-tags-a-friendly-guide-e38ab2217be3)
- [Popups, Dialogs, Tooltips UX Patterns](https://medium.com/design-bootcamp/popups-dialogs-tooltips-and-popovers-ux-patterns-2-939da7a1ddcd)
- [Tooltip Best Practices 2026](https://userguiding.com/blog/website-tooltips)

### Platform-Specific Implementation
- [VS Code Command Palette](https://code.visualstudio.com/api/ux-guidelines/command-palette)
- [Slack Slash Commands](https://docs.slack.dev/interactivity/implementing-slash-commands/)
- [Flutter Bottom Sheet Tutorial](https://blog.logrocket.com/flutter-modal-bottom-sheet-tutorial-with-examples/)
- [Flutter showModalBottomSheet API](https://api.flutter.dev/flutter/material/showModalBottomSheet.html)
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills)

### UI Component References
- [Chat Support Skills Best Practices](https://www.sprinklr.com/blog/chat-support-skills/)
- [Selection Controls Best Practices](https://app.uxcel.com/courses/ui-components-n-patterns/selection-controls-best-practices-324)
- [Modal UI Examples from SaaS Apps](https://userpilot.com/blog/ui-modal-examples/)
- [Badge vs Pills vs Chips vs Tags](https://smart-interface-design-patterns.com/articles/badges-chips-tags-pills/)

---
*Feature research for: Skill Discovery & Selection UI*
*Researched: 2026-02-18*
*Context: Subsequent milestone enhancing existing skill selector with browsable list, info popups, and visual selection indicators*
