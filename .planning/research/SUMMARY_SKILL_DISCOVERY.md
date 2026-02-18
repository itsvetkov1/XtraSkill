# Skill Discovery & Selection Research Summary

**Project:** v3.1 Skill Discovery & Selection
**Domain:** Chat UI enhancement - browsable skill list with rich metadata
**Researched:** 2026-02-18
**Confidence:** HIGH

## Executive Summary

This milestone enhances the existing skill selector from a simple PopupMenuButton to a rich browsable interface with skill metadata, info popups, and visual selection indicators. Research confirms that the existing architecture (Flutter Material 3 + FastAPI backend with `.claude/` directory scanning) is well-suited for this enhancement. The recommended approach is to parse SKILL.md frontmatter on the backend using `python-frontmatter`, return enhanced metadata via the existing `/api/skills` endpoint, and use Material 3's built-in widgets (Chip, Tooltip, Dialog) on the frontend—avoiding unnecessary third-party packages.

The core pattern follows industry standards: browsable skill list in a modal (BottomSheet or Dialog), info popups with detailed descriptions, and visual selection feedback via chips. Critical risks include breaking the existing transparent skill prepend mechanism and causing unnecessary widget rebuilds from state management changes. These are mitigated by preserving the existing prepend logic, using scoped Provider rebuilds, and extensive integration testing before refactoring.

The research is based on official Flutter/Material 3 documentation, verified 2026 sources, and existing codebase analysis (current `SkillSelector`, `AssistantConversationProvider`, and `/api/skills` endpoint). Confidence is HIGH across all areas—stack choices use standard libraries, feature expectations align with established UI patterns (VS Code command palette, Slack slash commands), and architecture builds incrementally on existing foundation without major restructuring.

## Key Findings

### Recommended Stack

**Backend:** Add `python-frontmatter` (v1.1.0) for YAML frontmatter parsing in SKILL.md files. This is the industry standard used by static site generators and documentation systems, far more robust than manual regex parsing. No other backend dependencies needed—FastAPI routes and SQLite models remain unchanged.

**Frontend:** Use Material 3 built-in widgets exclusively. No third-party packages required for this milestone. Optional: Add `front_matter_ml` (v1.2.0) only if client-side skill file parsing is needed in the future (unlikely).

**Core technologies:**
- `python-frontmatter` (backend): Parse SKILL.md YAML frontmatter — industry standard, handles edge cases (multi-line values, TOML/JSON variants)
- Material 3 `Chip` (frontend): Display selected skills as removable chips — built-in, accessible, consistent styling
- Material 3 `Dialog/BottomSheet` (frontend): Browsable skill list modal — native mobile pattern, swipe-to-dismiss
- Material 3 `Tooltip` (frontend): Skill descriptions on hover/long-press — built-in rich content support via `richMessage`
- Material 3 `Badge` (frontend): Feature count indicators — official widget, no third-party package needed
- `GridView.builder` (frontend): Responsive skill card grid — lazy rendering, auto-adjusts columns based on screen width

**What NOT to add:**
- Third-party dialog packages (`awesome_dialog`, `flutter_dialogs`) — Material 3 Dialog is feature-complete
- Third-party chip packages (`chips_choice`, `flutter_tags`) — Material 3 Chip handles all use cases
- `badges` package — Material 3 Badge is official
- `super_tooltip` — Material 3 Tooltip supports rich content
- `responsive_grid_list` — GridView.builder with `SliverGridDelegateWithMaxCrossAxisExtent` handles responsive layouts
- Markdown rendering packages (`flutter_markdown`) — not needed for structured frontmatter display (defer to v2+ if full markdown rendering required)

### Expected Features

**Must have (table stakes) — This Milestone:**
- Browsable skill list (modal interface replacing PopupMenuButton)
- Skill descriptions displayed inline in list
- Visual selection indicator (chip showing selected skill)
- Keyboard-friendly navigation (arrow keys + Enter work by default in ListView)
- Touch-friendly selection (tap-to-select on mobile/tablet)
- Loading/error/empty states (already implemented, port from PopupMenuButton)
- Skill name display (human-readable via `displayName` getter)
- Modal dismissal (tap-outside, back button, swipe gesture)

**Should have (competitive) — Add After Validation (v1.x):**
- Inline skill help/info (info icon opens detailed description modal)
- Skill search/filter (TextFormField with live filtering, trigger when 10+ skills installed)
- Keyboard shortcut to open picker (Cmd+K / Ctrl+K, add when power users request)
- Skill preview/quick look (tooltip on hover/long-press)

**Defer (v2+) — Future Consideration:**
- Skill categorization (group by type: analysis, coding, testing; needs API schema change)
- Recent skills first (usage tracking + local storage; trigger when analytics show repeated usage)
- Skill usage hints (example prompts per skill; trigger when users request "how do I use this?")

**Anti-features (don't build):**
- Multi-skill selection — prepend format supports only one skill per message
- Skill favorites/pinning — use auto-detected recent skills instead
- Custom skill creation from UI — violates single source of truth (.claude/ directory)
- Always-visible skill bar — clutters chat input, especially on mobile
- Skill auto-suggestion — adds latency and complexity, let users decide when to activate

### Architecture Approach

The enhancement builds incrementally on the existing architecture: backend scans `.claude/` directories and returns skill metadata via `/api/skills`, frontend caches skills in `SkillService` and manages selection state in `AssistantConversationProvider`. The core change is backend parsing of SKILL.md frontmatter (extracting `features`, `tags`, `category`, etc.) and frontend UI upgrade from PopupMenuButton to a browsable modal with rich content display.

**Major components:**

1. **SkillMetadataExtractor (backend, new)** — Parse SKILL.md frontmatter + Quick Reference section; return enhanced metadata dict with fallbacks for missing fields. Handles YAML/TOML/JSON variants gracefully.

2. **Enhanced GET /api/skills (backend, modified)** — Return structured metadata: `name`, `display_name`, `description`, `purpose`, `output`, `category`, `icon_hint`, `features[]`, `tags[]`, `skill_path`. Backward compatible (extra fields ignored by old clients).

3. **EnhancedSkill Model (frontend, modified)** — Extend existing `Skill` class with optional fields: `features`, `tags`, `category`, `iconHint`, `purpose`, `output`. Add `icon` getter mapping category to IconData.

4. **SkillBrowserDialog (frontend, new)** — Full-screen browsable skill list with optional search bar, GridView or ListView of SkillCard widgets, category filter (optional, defer if <10 skills).

5. **SkillCard (frontend, new)** — Individual skill display: icon, name, description (truncated), feature count badge, info button. Tap to select, info button opens detail panel.

6. **SkillDetailPanel (frontend, new, P2)** — Modal showing full skill information: Quick Reference prominently, feature list, "Use This Skill" button. Uses either embedded content (if <5KB per skill) or progressive loading (separate API endpoint).

**Key architectural patterns:**
- **Transparent skill prepending** — Preserve existing `[Using skill: X]` or change to `/skill-name` format; prepend invisibly to backend, show clean UI with chip indicator
- **Progressive content loading** — Load skill list immediately, fetch full content only when user clicks info icon (if SKILL.md files >5KB)
- **Dual selection modes (optional)** — Provide both quick PopupMenu (for known skills) and browsable Dialog (for discovery); OR replace PopupMenu entirely with single "Browse Skills" button
- **State scoping** — Use `context.select()` to rebuild only widgets depending on `selectedSkill`, avoiding unnecessary rebuilds of message list and input field

### Critical Pitfalls

1. **Parsing SKILL.md on frontend instead of backend** — Causes 100-300ms latency on mobile, increases memory overhead, duplicates parsing logic. **Prevention:** Parse on backend with `python-frontmatter`, return structured data. Frontend only renders pre-parsed JSON.

2. **Breaking existing skill prepend mechanism** — Adding UI enhancements inadvertently changes prepend format or duplicates skill in message. **Prevention:** Preserve exact prepend logic in isolated function, write integration tests before refactoring, ensure UI components only set state without implementing prepend.

3. **State management refactor without testing** — Adding skill selection to Provider triggers unintended rebuilds (input loses focus, scroll resets). **Prevention:** Use `context.select()` for scoped rebuilds, separate skill state from conversation state if needed, profile with Flutter DevTools.

4. **Tooltip/popup overflow on mobile screens** — Info popups render off-screen or clipped on narrow devices, especially near screen edges or above keyboard. **Prevention:** Use overflow-aware tooltip packages OR Material 3 Dialog/BottomSheet (handles overflow automatically), test on 320px width (iPhone SE), ensure minimum 8px margin from edges.

5. **Inconsistent skill deselection UX** — User can select skill but can't easily clear it, or deselection methods vary (chip close vs. re-tap in selector). **Prevention:** Support both chip close AND re-tapping selected skill to deselect, show visual feedback (checkmark) for selected skill in browser.

6. **Bottom sheet performance with large skill lists** — Opening sheet with 10+ skills causes lag, animation jank on low-end devices. **Prevention:** Use `ListView.builder` (lazy loading), set `isScrollControlled: true`, preload skill data before showing sheet (avoid FutureBuilder inside sheet).

7. **SKILL.md structure assumptions** — Parser assumes all files have YAML frontmatter with specific fields, crashes or excludes skills when structure varies. **Prevention:** Defensive parsing with fallbacks (use filename if front matter missing), support YAML/TOML/JSON variants, extract description from markdown body if frontmatter absent.

## Implications for Roadmap

Based on research, suggested phase structure for incremental enhancement:

### Phase 1: Backend Metadata Enhancement
**Rationale:** Frontend needs richer skill data before building new UI. Parse SKILL.md frontmatter on backend first to unlock enhanced display capabilities.

**Delivers:** Enhanced `/api/skills` endpoint returning structured metadata (`features`, `tags`, `category`, `purpose`, `output`, etc.).

**Addresses:**
- Table stakes: Skill descriptions inline in list (needs full metadata from backend)
- Pitfall 1: Parse on backend, not frontend (prevents performance issues)
- Pitfall 7: SKILL.md structure assumptions (defensive parsing with fallbacks)

**Avoids:** Pitfall 1 (frontend parsing), Pitfall 7 (structure assumptions)

**Stack elements:** `python-frontmatter` library, enhanced Pydantic response model

**Estimated effort:** 4-6 hours

### Phase 2: Frontend Model Update
**Rationale:** Update `Skill` model to accept enhanced metadata from backend. Required before building new UI components.

**Delivers:** `EnhancedSkill` model with `features[]`, `tags[]`, `category`, `iconHint`, `purpose`, `output` fields. Backward compatible (optional fields).

**Addresses:**
- Table stakes: Foundation for all UI enhancements
- Architecture: Single source of truth (backend metadata, frontend renders dynamically)

**Avoids:** Hardcoding skill metadata in frontend constants

**Estimated effort:** 2-3 hours

### Phase 3: Browsable Skill List UI
**Rationale:** Core user-facing enhancement—replace PopupMenuButton with rich browsable interface. Delivers immediate value.

**Delivers:** `SkillBrowserDialog` (modal with skill grid/list), `SkillCard` widget (name, description, icon, feature count badge), "Browse Skills" button in chat input.

**Addresses:**
- Table stakes: Browsable list, inline descriptions, touch-friendly selection, modal dismissal
- Competitive: Skill preview tooltips (if using rich tooltips on cards)
- Pitfall 6: Bottom sheet performance (use ListView.builder)
- Pitfall 12: Breaking existing layout (preserve input row structure)

**Avoids:** Pitfall 2 (breaking prepend mechanism—don't modify message send logic yet), Pitfall 3 (state management issues—use scoped rebuilds)

**Stack elements:** Material 3 Dialog/BottomSheet, GridView.builder, Material 3 Chip

**Estimated effort:** 8-10 hours

### Phase 4: Visual Selection Indicators
**Rationale:** Provide clear feedback when skill is selected. Builds on Phase 3's selection logic.

**Delivers:** Enhanced skill chip display (feature count badge, distinct styling vs. file chips), tooltip on chip hover ("Skill will be applied to next message").

**Addresses:**
- Table stakes: Visual selection indicator
- Pitfall 5: Inconsistent deselection UX (multiple clear paths)
- Pitfall 7: Chip visual confusion (distinct colors/icons)
- Pitfall 11: Close icon too small (accessible touch targets)

**Avoids:** Pitfall 3 (state rebuilds—chip area uses `context.select()`)

**Stack elements:** Material 3 Chip with `deleteIcon`, Material 3 Badge

**Estimated effort:** 3-4 hours

### Phase 5: Skill Prepend Enhancement (Optional)
**Rationale:** Independent of UI changes. Change prepend format from `[Using skill: X]` to `/skill-name` (industry standard).

**Delivers:** Updated prepend logic in `AssistantConversationProvider.sendMessage()`, integration tests verifying prepend behavior.

**Addresses:**
- Architecture: Transparent skill prepending pattern (align with ChatGPT plugins, Slack commands)
- Pitfall 2: Preserve existing prepend mechanism (test before changing)

**Avoids:** Breaking existing threads, double prepend issues

**Estimated effort:** 1-2 hours

### Phase 6: Skill Info Popup (P2 Feature)
**Rationale:** Nice-to-have after core browsing works. Defer until users request detailed skill information.

**Delivers:** `SkillDetailPanel` widget, info icon on skill cards, full SKILL.md content display with Quick Reference section.

**Addresses:**
- Competitive: Inline skill help/info
- Pitfall 4: Tooltip overflow (use Dialog/BottomSheet instead of Tooltip for long content)
- Pitfall 9: Content too long (truncate to top 3-5 features in preview, full details in panel)

**Implementation decision:** Embed full content in initial `/api/skills` response if average SKILL.md <5KB, otherwise create `GET /api/skills/{name}/content` endpoint for progressive loading.

**Stack elements:** Material 3 Dialog, optional markdown rendering package (if showing full markdown content)

**Estimated effort:** 6-8 hours

### Phase 7: Search & Polish (P2 Features)
**Rationale:** Add when skill count grows or users request. Not essential for initial launch.

**Delivers:** Search/filter TextField in SkillBrowserDialog, keyboard shortcut (Cmd+K / Ctrl+K), category badges, pull-to-refresh, cache invalidation.

**Addresses:**
- Competitive: Skill search/filter, keyboard shortcut
- Pitfall 10: Cache invalidation (time-based expiration, pull-to-refresh)

**Trigger:** Add search when 10+ skills installed, keyboard shortcut when power users request.

**Estimated effort:** 4-6 hours

### Phase Ordering Rationale

- **Backend first (Phase 1):** Frontend UI depends on enhanced metadata; no point building cards without feature counts, categories, etc.
- **Model update second (Phase 2):** Minimal effort, unblocks all frontend work, ensures type safety.
- **Core browsing third (Phase 3):** Highest user value—transforms skill selection experience. Must work before adding polish.
- **Selection feedback fourth (Phase 4):** Builds on Phase 3's selection logic. Clean separation allows testing core browsing independently.
- **Prepend enhancement fifth (Phase 5):** Independent of UI; can be done in parallel or deferred. Low risk since it's a simple string format change.
- **Info popup sixth (Phase 6):** Deferred until users request detailed skill info. Core browsing is usable without it.
- **Search/polish seventh (Phase 7):** Added when needed (10+ skills, power user requests). Avoid premature optimization.

**Dependency chain:**
```
Phase 1 (Backend) → Phase 2 (Model) → Phase 3 (Browsing UI)
                                            ↓
                                       Phase 4 (Selection Chips)
                                            ↓
                                       Phase 6 (Info Popup)
                                            ↓
                                       Phase 7 (Search/Polish)

Phase 5 (Prepend) ← Independent, can run in parallel
```

### Research Flags

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Backend Metadata):** Well-documented, `python-frontmatter` is standard library with excellent docs
- **Phase 2 (Model Update):** Dart model extension, straightforward pattern
- **Phase 3 (Browsing UI):** Material 3 widgets (Dialog, BottomSheet, GridView) have official examples and extensive documentation
- **Phase 4 (Selection Chips):** Material 3 Chip widget, established pattern
- **Phase 7 (Search/Polish):** TextField filtering is standard Flutter pattern

**Phases likely needing validation during execution:**
- **Phase 5 (Prepend Enhancement):** Simple change but requires testing with existing threads/messages to ensure no breakage
- **Phase 6 (Info Popup):** Decision point: embedded content vs. progressive loading. Test with actual SKILL.md file sizes before implementing.

**No phases require deep research** — all patterns are established, libraries are mature, and existing codebase provides foundation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | `python-frontmatter` is industry standard (verified PyPI, GitHub); Material 3 widgets are official Flutter components (API docs verified); no experimental packages |
| Features | HIGH | Feature expectations drawn from established UI patterns (VS Code command palette, Slack slash commands) and UX research articles (verified 2026 sources); existing codebase already implements core flow |
| Architecture | HIGH | Based on existing codebase analysis (SkillSelector, AssistantConversationProvider, /api/skills endpoint verified in repo); incremental enhancement approach validated by official Flutter migration guides |
| Pitfalls | HIGH | Pitfalls verified from official Flutter docs (state management, widget lifecycle), backend performance articles (FastAPI caching), and community consensus (bottom sheet performance, tooltip overflow) |

**Overall confidence:** HIGH

Research is grounded in official documentation (Flutter API, FastAPI, Material 3), verified 2026 sources, and existing codebase structure. No speculative or unverified patterns. All recommended technologies are mature with stable APIs.

### Gaps to Address

**Skill count unknown:** Current environment has 1 skill (`business-analyst`). Design targets 5-20 skill range. If user installs 20+ skills, may need to add categorization (Phase 7 feature). **Mitigation:** Design with categorization in mind (backend returns `category` field even if frontend doesn't display it yet); easy to add filter UI later.

**SKILL.md format consistency:** Research assumes SKILL.md files follow frontmatter convention. If user's skills lack frontmatter, parser must gracefully fall back to extracting description from markdown body. **Mitigation:** Defensive parsing implemented in Phase 1 (Pitfall 7 prevention); test with both frontmatter and plain markdown files.

**Mobile vs. desktop UX:** Design prioritizes mobile (BottomSheet, touch-friendly), but desktop users may expect keyboard shortcuts. **Mitigation:** Material 3 widgets support keyboard navigation by default (arrow keys, Enter); defer Cmd+K shortcut to Phase 7 when requested.

**Info popup implementation decision (Phase 6):** Embed full SKILL.md content in initial API response vs. progressive loading. **Resolution:** Test average SKILL.md file size during Phase 1; if <5KB, embed; if >5KB, create separate endpoint. Document decision in phase plan.

## Sources

### Primary (HIGH confidence)

**Backend (Python/FastAPI):**
- [python-frontmatter GitHub](https://github.com/eyeseast/python-frontmatter) — Library docs, version compatibility
- [python-frontmatter PyPI](https://pypi.org/project/frontmatter/) — Package installation, API reference
- [Python YAML Frontmatter Guide](https://safjan.com/python-packages-yaml-front-matter-markdown/) — Comparison of frontmatter libraries

**Frontend (Flutter/Material 3):**
- [Flutter Material Chip API](https://api.flutter.dev/flutter/material/Chip-class.html) — Official Chip widget documentation
- [Flutter Material Badge API](https://api.flutter.dev/flutter/material/Badge-class.html) — Official Badge widget documentation
- [Flutter Material Tooltip API](https://api.flutter.dev/flutter/material/Tooltip-class.html) — Official Tooltip widget documentation
- [Flutter Dialog API](https://api.flutter.dev/flutter/material/Dialog-class.html) — Official Dialog widget documentation
- [Flutter GridView API](https://api.flutter.dev/flutter/widgets/GridView-class.html) — Official GridView widget documentation
- [Flutter showModalBottomSheet API](https://api.flutter.dev/flutter/material/showModalBottomSheet.html) — Bottom sheet modal pattern

**Existing Codebase:**
- `/backend/app/routes/skills.py` (lines 41-73) — Current skill parsing logic
- `/frontend/lib/models/skill.dart` (lines 5-46) — Current Skill model
- `/frontend/lib/screens/assistant/widgets/skill_selector.dart` (lines 10-122) — Current SkillSelector widget

### Secondary (MEDIUM confidence)

**Design Patterns:**
- [Chat UI Design Patterns 2026](https://muz.li/inspiration/chat-ui/) — Command palette patterns
- [Command Palette UX Patterns](https://medium.com/design-bootcamp/command-palette-ux-patterns-1-d6b6e68f30c1) — VS Code-style browsing
- [Badges vs Chips/Tags Guide](https://medium.com/design-bootcamp/ux-blueprint-03-badges-vs-chips-tags-a-friendly-guide-e38ab2217be3) — Visual indicator patterns
- [Popups, Dialogs, Tooltips UX Patterns](https://medium.com/design-bootcamp/popups-dialogs-tooltips-and-popovers-ux-patterns-2-939da7a1ddcd) — Info popup best practices
- [Tooltip Best Practices 2026](https://userguiding.com/blog/website-tooltips) — Overflow handling, positioning

**Flutter Best Practices:**
- [Flutter Responsive Grid Best Practices](https://medium.com/@saadalidev/building-beautiful-responsive-ui-in-flutter-a-complete-guide-for-2026-ea43f6c49b85) — 2026 responsive layout guide
- [Flutter Chip Best Practices](https://www.dhiwise.com/post/mastering-interactive-ui-design-with-flutter-chip) — Interactive chip design
- [Material 3 Updates 2025-2026](https://dcm.dev/blog/2025/12/23/top-flutter-features-2025) — Chip/badge/tooltip enhancements
- [Flutter Bottom Sheet Tutorial](https://blog.logrocket.com/flutter-modal-bottom-sheet-tutorial-with-examples/) — Modal bottom sheet patterns

**Performance & Pitfalls:**
- [Top 5 Common BottomSheet Mistakes](https://medium.com/easy-flutter/top-5-common-bottomsheet-mistakes-flutter-developers-make-and-how-to-avoid-them-447a6b991e52) — Performance pitfalls
- [Flutter State Management in 2026](https://medium.com/@Sofia52/flutter-state-management-in-2026-choosing-the-right-approach-811b866d9b1b) — Provider scoping patterns
- [FastAPI Performance Tuning & Caching](https://blog.greeden.me/en/2026/02/03/fastapi-performance-tuning-caching-strategy-101-a-practical-recipe-for-growing-a-slow-api-into-a-lightweight-fast-api/) — Backend caching strategies

### Tertiary (MEDIUM confidence - competitive analysis)

- [VS Code Command Palette](https://code.visualstudio.com/api/ux-guidelines/command-palette) — Keyboard-first browsing pattern
- [Slack Slash Commands](https://docs.slack.dev/interactivity/implementing-slash-commands/) — Inline autocomplete pattern
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) — Agent skill metadata structure
- [Where should AI sit in your UI?](https://uxdesign.cc/where-should-ai-sit-in-your-ui-1710a258390e) — AI UI layout patterns 2026
- [Chatbot UI Best Practices 2026](https://vynta.ai/blog/chatbot-ui/) — Transparent skill disclosure, slash prefix patterns

---
*Research completed: 2026-02-18*
*Ready for roadmap: yes*
*Total estimated effort: 25-35 hours (Phases 1-7)*
