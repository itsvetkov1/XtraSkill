# Architecture Research: Skill Discovery & Selection Integration

**Domain:** Skill selector enhancement for Assistant chat
**Researched:** 2026-02-18
**Confidence:** HIGH

## Current Architecture (Baseline)

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Flutter)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ AssistantChat    │  │ SkillSelector    │                 │
│  │ Screen           │  │ Widget           │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                            │
│           ├─────────────────────┤                            │
│           │                                                  │
│  ┌────────▼─────────────────────────────────────┐           │
│  │ AssistantConversationProvider                │           │
│  │  - selectedSkill: Skill?                     │           │
│  │  - selectSkill(Skill)                        │           │
│  │  - clearSkill()                              │           │
│  │  - sendMessage(text) → prepends skill        │           │
│  └────────┬─────────────────────────────────────┘           │
│           │                                                  │
│  ┌────────▼────────┐                                        │
│  │ SkillService    │                                        │
│  │ (cached fetch)  │                                        │
│  └────────┬────────┘                                        │
│           │ HTTP GET /api/skills                            │
├───────────┴─────────────────────────────────────────────────┤
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐               │
│  │ GET /api/skills                          │               │
│  │  - Scans .claude/ directories            │               │
│  │  - Extracts description from SKILL.md    │               │
│  │  - Returns: name, description, path      │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Current Data Model

**Backend (Python):**
```python
# Returned from GET /api/skills (inferred from routes/skills.py)
{
    "name": str,              # e.g., "business-analyst"
    "description": str,       # First non-header line from SKILL.md
    "skill_path": str         # e.g., ".claude/business-analyst/SKILL.md"
}
```

**Frontend (Dart):**
```dart
class Skill {
  final String name;        // e.g., "business-analyst"
  final String description; // Short one-liner
  final String skillPath;   // Relative path

  String get displayName;   // e.g., "Business Analyst"
}
```

### Current Skill Flow

```
User clicks skill button
    ↓
SkillSelector shows PopupMenuButton
    ↓
FutureBuilder → SkillService.getSkills() → GET /api/skills
    ↓
PopupMenuButton renders skill list (name + description)
    ↓
User selects skill → onSkillSelected(skill)
    ↓
AssistantConversationProvider.selectSkill(skill)
    ↓
Skill shown as chip in input area
    ↓
User types message → sendMessage(content)
    ↓
Provider prepends: "[Using skill: business-analyst]\n\n{content}"
    ↓
Backend receives full message with skill context
```

## Enhanced Architecture (v3.1)

### New Components

| Component | Type | Purpose | Integration Point |
|-----------|------|---------|-------------------|
| **SkillBrowserDialog** | Widget (new) | Full-screen browsable skill list with search | Opened from AssistantChatInput |
| **SkillDetailPanel** | Widget (new) | Info popup showing full SKILL.md content | Triggered by info icon on skill cards |
| **EnhancedSkill** | Model (enhanced) | Extended skill model with full metadata | Replaces current Skill model |
| **SkillMetadataExtractor** | Backend utility (new) | Parses SKILL.md frontmatter + content | Used by GET /api/skills |

### Enhanced System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Flutter)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │ AssistantChatInput                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ Old: Skill   │  │ New: Browse  │                 │   │
│  │  │ PopupMenu    │  │ Skills Btn   │                 │   │
│  │  └──────┬───────┘  └──────┬───────┘                 │   │
│  └─────────┼──────────────────┼──────────────────────────┘   │
│            │                  │                              │
│            │        ┌─────────▼────────────┐                 │
│            │        │ SkillBrowserDialog   │                 │
│            │        │  - Search bar        │                 │
│            │        │  - Skill grid/list   │                 │
│            │        │  - Category filter   │                 │
│            │        └─────────┬────────────┘                 │
│            │                  │                              │
│            │        ┌─────────▼────────────┐                 │
│            │        │ SkillCard            │                 │
│            │        │  - Name              │                 │
│            │        │  - Description       │                 │
│            │        │  - Info icon (i)     │                 │
│            │        └─────────┬────────────┘                 │
│            │                  │                              │
│            │        ┌─────────▼────────────┐                 │
│            │        │ SkillDetailPanel     │                 │
│            │        │  - Full content      │                 │
│            │        │  - Features list     │                 │
│            │        │  - Quick reference   │                 │
│            │        └──────────────────────┘                 │
│            │                                                 │
│  ┌─────────▼─────────────────────────────────────┐          │
│  │ AssistantConversationProvider                 │          │
│  │  - selectedSkill: EnhancedSkill?              │          │
│  │  - selectSkill(EnhancedSkill)                 │          │
│  │  - sendMessage() → prepends "/skill-name"     │          │
│  └─────────┬─────────────────────────────────────┘          │
│            │                                                 │
│  ┌─────────▼─────────┐                                      │
│  │ SkillService      │                                      │
│  │  - getSkills()    │ (enhanced return type)               │
│  │  - getSkillDetail(name) → full SKILL.md                  │
│  └─────────┬─────────┘                                      │
│            │                                                 │
├────────────┴─────────────────────────────────────────────────┤
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐               │
│  │ GET /api/skills (enhanced)               │               │
│  │  - SkillMetadataExtractor                │               │
│  │  - Parses frontmatter (YAML)             │               │
│  │  - Extracts Quick Reference section      │               │
│  │  - Returns enhanced metadata             │               │
│  └──────────────────────────────────────────┘               │
│  ┌──────────────────────────────────────────┐               │
│  │ GET /api/skills/{name}/content (new)     │               │
│  │  - Returns full SKILL.md markdown        │               │
│  │  - For detail panel display              │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## Enhanced Data Model

### Backend Response (Enhanced GET /api/skills)

```python
# Enhanced response from GET /api/skills
{
    "name": str,                    # e.g., "business-analyst"
    "display_name": str,            # e.g., "Business Analyst"
    "description": str,             # Short one-liner (from frontmatter or first line)
    "purpose": str,                 # From "Quick Reference > Purpose" section
    "output": str,                  # From "Quick Reference > Output" section
    "skill_path": str,              # Relative path
    "category": str,                # Inferred or from frontmatter (e.g., "requirements", "design")
    "icon_hint": str,               # Optional: suggest icon (e.g., "description", "code")
}
```

### Frontend Model (Enhanced Skill)

```dart
class EnhancedSkill {
  final String name;
  final String displayName;
  final String description;
  final String? purpose;          // Optional: for detail view
  final String? output;            // Optional: for detail view
  final String skillPath;
  final String? category;
  final String? iconHint;

  String get displayName;          // Already exists
  IconData get icon;               // New: icon based on category/iconHint
}
```

### SKILL.md Structure (Standard)

```markdown
---
name: business-analyst
description: Short one-liner describing what the skill does
category: requirements
icon_hint: description
---

# Skill Name

Long-form description paragraph.

## Quick Reference

**Purpose**: [What this skill enables]

**Output**: [What it produces]

**Critical Rules**:
- Rule 1
- Rule 2

**Boundary**: [What this skill does NOT do]

## [Rest of skill content...]
```

## Architectural Patterns

### Pattern 1: Dual Selection Modes

**What:** Provide both quick selection (existing PopupMenu) and browsable mode (new Dialog).

**When to use:** When users need both quick access (for known skills) and discovery (for exploring).

**Trade-offs:**
- **Pro:** Caters to both expert and novice users
- **Pro:** Progressive disclosure — simple by default, powerful when needed
- **Con:** Two code paths to maintain
- **Con:** Slight UI complexity (two buttons or toggle)

**Implementation:**
```dart
// AssistantChatInput widget
Row(
  children: [
    // Quick selector (existing)
    SkillSelector(onSkillSelected: provider.selectSkill),

    // OR

    // Browse mode button
    IconButton(
      icon: Icon(Icons.apps),
      tooltip: 'Browse all skills',
      onPressed: () => showDialog(
        context: context,
        builder: (_) => SkillBrowserDialog(
          onSkillSelected: (skill) {
            provider.selectSkill(skill);
            Navigator.pop(context);
          },
        ),
      ),
    ),
  ],
)
```

**Recommendation:** Replace PopupMenu with single "Browse Skills" button. PopupMenu pattern is limiting for rich content.

---

### Pattern 2: Progressive Content Loading

**What:** Load skill list immediately, fetch full content only when user clicks info icon.

**When to use:** When detail content is large and not always needed.

**Trade-offs:**
- **Pro:** Fast initial load
- **Pro:** Reduces API payload size
- **Con:** Extra API call for details
- **Con:** Loading state for detail panel

**Implementation:**
```dart
// SkillCard widget
class SkillCard extends StatelessWidget {
  final EnhancedSkill skill;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          ListTile(
            title: Text(skill.displayName),
            subtitle: Text(skill.description),
            trailing: IconButton(
              icon: Icon(Icons.info_outline),
              onPressed: () => _showDetailPanel(context),
            ),
            onTap: () => widget.onSkillSelected(skill),
          ),
        ],
      ),
    );
  }

  void _showDetailPanel(BuildContext context) async {
    // Fetch full content on demand
    final content = await SkillService().getSkillContent(skill.name);
    showDialog(
      context: context,
      builder: (_) => SkillDetailPanel(skill: skill, content: content),
    );
  }
}
```

**Alternative:** Embed full content in initial GET /api/skills response.
- **Pro:** No additional API call
- **Con:** Larger payload (may be 10-50KB per skill with full markdown)

**Recommendation:** Use progressive loading (separate endpoint) if SKILL.md files exceed 5KB. Otherwise, embed in initial response.

---

### Pattern 3: Transparent Skill Prepending

**What:** Prepend skill context invisibly to backend, show clean UI to user.

**When to use:** When skill activation should be transparent and non-intrusive.

**Trade-offs:**
- **Pro:** Clean user experience (no manual "/skill-name" typing)
- **Pro:** User can copy/share messages without skill prefix clutter
- **Con:** User may not understand skill is active (mitigate with visible chip)
- **Con:** Backend receives modified message (document this clearly)

**Current Implementation:**
```dart
// AssistantConversationProvider.sendMessage()
String messageContent = content;
if (_selectedSkill != null) {
  messageContent = '[Using skill: ${_selectedSkill!.name}]\n\n$content';
}
// Send messageContent to backend

// Display in UI: original content (not modified)
final userMessage = Message(
  role: MessageRole.user,
  content: content,  // Original, not modified
);
```

**Enhancement for v3.1:**
```dart
// Change prepending format from "[Using skill: X]" to "/skill-name"
if (_selectedSkill != null) {
  messageContent = '/${_selectedSkill!.name}\n\n$content';
}
```

**Why slash prefix:**
- Industry standard (ChatGPT plugins, Slack commands, Discord bots)
- More concise than `[Using skill: X]`
- Easier to parse on backend if needed
- Source: [Chatbot UI Best Practices 2026](https://vynta.ai/blog/chatbot-ui/)

---

### Pattern 4: Skill Chip Visibility

**What:** Show selected skill as a removable chip above the input field.

**When to use:** Always — provides feedback that skill is active.

**Trade-offs:**
- **Pro:** Clear visual feedback
- **Pro:** Easy to remove before sending
- **Con:** Takes vertical space (minimal)

**Current Implementation:** Already exists in AssistantChatInput (skill chip with delete icon).

**Enhancement:** Add tooltip on hover showing "This skill will be applied to your next message".

---

## Data Flow

### Enhanced Skill Selection Flow

```
User opens chat
    ↓
Clicks "Browse Skills" button
    ↓
SkillBrowserDialog opens
    ↓
[Initial Load] → SkillService.getSkills() → GET /api/skills
    ↓
Renders skill grid with cards (name, description, info icon)
    ↓
[User searches/filters] → Local filtering on cached list
    ↓
User clicks skill card → onSkillSelected(skill) → Provider.selectSkill()
    ↓
Dialog closes, chip appears in input area
    ↓
User types message → sendMessage(content)
    ↓
Provider prepends: "/{skill-name}\n\n{content}"
    ↓
Backend receives modified message
```

### Skill Detail Panel Flow

```
User browsing skills in SkillBrowserDialog
    ↓
Clicks info icon on skill card
    ↓
[Option A: Progressive Loading]
  → SkillService.getSkillContent(name) → GET /api/skills/{name}/content
  → Returns full SKILL.md markdown

[Option B: Embedded Content]
  → Content already in EnhancedSkill model from initial load
    ↓
SkillDetailPanel shows as modal overlay
    ↓
Renders markdown content with sections:
  - Quick Reference
  - Core Workflow
  - Key Features
    ↓
"Use This Skill" button → onSkillSelected(skill) → closes both dialogs
```

## Component Responsibilities

### New Components

| Component | Responsibility | Files to Create |
|-----------|----------------|-----------------|
| **SkillBrowserDialog** | Full-screen skill browsing UI | `frontend/lib/screens/assistant/widgets/skill_browser_dialog.dart` |
| **SkillCard** | Individual skill card in browser | `frontend/lib/screens/assistant/widgets/skill_card.dart` |
| **SkillDetailPanel** | Info popup with full SKILL.md | `frontend/lib/screens/assistant/widgets/skill_detail_panel.dart` |
| **EnhancedSkill** | Extended skill model | Modify `frontend/lib/models/skill.dart` |
| **SkillMetadataExtractor** | Parse SKILL.md frontmatter + sections | `backend/app/services/skill_metadata_extractor.py` |

### Modified Components

| Component | Changes Required | Impact |
|-----------|------------------|--------|
| **SkillSelector** | Replace PopupMenu with Dialog launcher OR keep as quick-select option | Medium (UI change) |
| **AssistantChatInput** | Add "Browse Skills" button OR replace existing button | Low (button swap) |
| **SkillService** | Add `getSkillContent(name)` method for detail fetching | Low (new method) |
| **AssistantConversationProvider** | Change skill prepending from `[Using skill: X]` to `/skill-name` | Low (string change) |
| **GET /api/skills** | Return enhanced metadata (purpose, output, category, icon_hint) | Medium (parse more fields) |

## Integration Points

### Backend API Changes

| Endpoint | Type | Purpose | Response |
|----------|------|---------|----------|
| **GET /api/skills** | Enhanced | Return enhanced metadata | `List[EnhancedSkillDict]` |
| **GET /api/skills/{name}/content** | New (optional) | Return full SKILL.md markdown | `{"content": str, "metadata": dict}` |

**Decision Point:** Embed full content in GET /api/skills vs. separate endpoint?

**Recommendation:**
- If average SKILL.md < 5KB → embed in initial response
- If average SKILL.md > 5KB → use separate endpoint

**Current:** business-analyst SKILL.md is ~8KB → use separate endpoint.

---

### Frontend-Backend Contract

**Current:**
```json
// GET /api/skills
[
  {
    "name": "business-analyst",
    "description": "Short one-liner",
    "skill_path": ".claude/business-analyst/SKILL.md"
  }
]
```

**Enhanced:**
```json
// GET /api/skills
[
  {
    "name": "business-analyst",
    "display_name": "Business Analyst",
    "description": "Enables sales teams to systematically gather requirements...",
    "purpose": "Enable sales teams to capture complete business requirements",
    "output": "Single comprehensive BRD",
    "category": "requirements",
    "icon_hint": "description",
    "skill_path": ".claude/business-analyst/SKILL.md"
  }
]
```

**New Endpoint (Optional):**
```json
// GET /api/skills/business-analyst/content
{
  "name": "business-analyst",
  "content": "# Business Analyst\n\nSpecialized assistant for...",
  "metadata": {
    "name": "business-analyst",
    "description": "...",
    "category": "requirements"
  }
}
```

---

## Recommended Build Order

### Phase 1: Backend Enhancement (Foundation)
**Goal:** Enhance API to return richer skill metadata

1. Create `SkillMetadataExtractor` utility
   - Parse YAML frontmatter
   - Extract Quick Reference section
   - Return enhanced metadata dict
2. Modify GET /api/skills to use extractor
3. Create EnhancedSkill response model (Pydantic)
4. Test with existing SKILL.md files

**Why first:** Frontend needs enhanced data model before building UI.

**Estimated effort:** 4-6 hours

---

### Phase 2: Frontend Model Update
**Goal:** Update Skill model to support enhanced fields

1. Add optional fields to `Skill` class (purpose, output, category, iconHint)
2. Update `fromJson` constructor
3. Add `icon` getter (maps category/iconHint to IconData)
4. Backward compatibility: ensure existing code works with optional fields

**Why second:** UI widgets need updated model.

**Estimated effort:** 2-3 hours

---

### Phase 3: Skill Browser UI
**Goal:** Build browsable skill list interface

1. Create `SkillBrowserDialog` widget
   - Search bar at top
   - GridView or ListView of skills
   - Category filter (optional)
2. Create `SkillCard` widget
   - Name, description, icon
   - Info button (opens detail panel)
   - Tap to select
3. Integrate with AssistantChatInput
   - Add "Browse Skills" button
   - Open dialog on tap
   - Pass onSkillSelected callback

**Why third:** Core browsing experience.

**Estimated effort:** 8-10 hours

---

### Phase 4: Skill Detail Panel
**Goal:** Show full skill information in popup

**Option A: Embedded Content (simpler, no new API)**
1. Create `SkillDetailPanel` widget
2. Render full markdown (use `flutter_markdown` package)
3. Show Quick Reference section prominently
4. "Use This Skill" button at bottom

**Option B: Progressive Loading (lighter initial load)**
1. Add GET /api/skills/{name}/content endpoint
2. Create `SkillDetailPanel` with FutureBuilder
3. Fetch content on demand
4. Show loading state while fetching

**Recommendation:** Start with Option A (simpler). If payload becomes issue, refactor to Option B.

**Why fourth:** Detail view is nice-to-have after core browsing works.

**Estimated effort:** 6-8 hours

---

### Phase 5: Skill Prepending Enhancement
**Goal:** Change from `[Using skill: X]` to `/skill-name`

1. Update `AssistantConversationProvider.sendMessage()`
2. Change prepending format
3. Update backend parsing if needed (currently backend treats it as opaque text)
4. Update tests

**Why fifth:** Independent of UI changes, can be done anytime.

**Estimated effort:** 1-2 hours

---

### Phase 6: Polish & Refinements
**Goal:** UX improvements and edge cases

1. Add tooltips on skill chips ("Skill will be applied to next message")
2. Search functionality in SkillBrowserDialog (filter by name/description)
3. Category badges on skill cards
4. Empty state ("No skills available")
5. Error handling (API failures, missing SKILL.md)
6. Keyboard shortcuts (Escape to close dialog)

**Estimated effort:** 4-6 hours

---

**Total estimated effort:** 25-35 hours (3-4 full workdays or 5-7 half-days)

---

## Scaling Considerations

| Scale | Considerations |
|-------|----------------|
| **1-5 skills** | Current architecture fine. Simple list works. |
| **5-20 skills** | Grid view recommended. Search becomes useful. |
| **20+ skills** | Category filtering essential. Consider skill tags. |
| **50+ skills** | Fuzzy search. Lazy loading. Virtualized lists. |

**Current state:** 1 skill (business-analyst)

**v3.1 target:** Support 5-10 skills comfortably

**Recommendation:** Build for 5-20 skill range. Grid view + search covers this scale well.

---

## Anti-Patterns

### Anti-Pattern 1: Overloading PopupMenuButton

**What people do:** Try to cram rich content (descriptions, icons, categories) into PopupMenuButton.

**Why it's wrong:**
- PopupMenuButton is designed for simple text lists
- Adding multi-line descriptions makes it cluttered
- Limited styling flexibility
- Poor UX on mobile (small tap targets)

**Do this instead:** Use a full Dialog or BottomSheet for browsable lists with rich content. PopupMenuButton is fine for <5 simple items only.

**Source:** [Flutter Material Component Best Practices](https://docs.flutter.dev/ui/widgets/material)

---

### Anti-Pattern 2: Parsing Markdown on Every Render

**What people do:** Re-parse SKILL.md content in widget build() method.

**Why it's wrong:**
- Markdown parsing is CPU-intensive
- Causes jank on every rebuild
- Especially bad with Flutter's frequent rebuilds

**Do this instead:**
- Parse markdown once when fetching skill content
- Store parsed result in widget state
- Use `const` constructors where possible
- Cache parsed HTML/widget tree

**Example:**
```dart
// BAD
@override
Widget build(BuildContext context) {
  final parsed = markdown.parse(skill.content); // ❌ Parses on every build
  return MarkdownBody(data: parsed);
}

// GOOD
class SkillDetailPanel extends StatefulWidget {
  final String content;

  @override
  _SkillDetailPanelState createState() => _SkillDetailPanelState();
}

class _SkillDetailPanelState extends State<SkillDetailPanel> {
  late final String _parsedContent;

  @override
  void initState() {
    super.initState();
    _parsedContent = widget.content; // ✅ Parse once
  }

  @override
  Widget build(BuildContext context) {
    return MarkdownBody(data: _parsedContent);
  }
}
```

---

### Anti-Pattern 3: Invisible Skill Activation Without Feedback

**What people do:** Prepend skill to message without showing user it's active.

**Why it's wrong:**
- User doesn't know skill is being applied
- Leads to confusion ("Why is AI responding this way?")
- Violates transparency principle in AI UX
- Source: [AI Transparency in UX 2026](https://www.theknowledgeacademy.com/blog/ui-designer-skills/)

**Do this instead:**
- Show skill chip when selected
- Add badge or indicator in chat input
- Include tooltip explaining skill will be applied
- Allow user to remove skill before sending

**Current implementation:** ✅ Already follows best practice (skill chip visible in input area).

---

### Anti-Pattern 4: Hardcoding Skill Metadata in Frontend

**What people do:** Define skill icons, categories, descriptions in frontend constants.

**Why it's wrong:**
- Source of truth should be SKILL.md files
- Adding new skills requires frontend code changes
- Inconsistent with discovery-based architecture

**Do this instead:**
- Parse all metadata from SKILL.md (frontmatter + content)
- Backend extracts and returns metadata
- Frontend renders dynamically
- New skills work automatically when SKILL.md added to `.claude/`

**Current implementation:** ✅ Already follows best practice (backend scans `.claude/` directory).

---

## Sources

**Architecture Patterns:**
- [Where should AI sit in your UI?](https://uxdesign.cc/where-should-ai-sit-in-your-ui-1710a258390e) — AI UI layout patterns 2026
- [Frontend Design Patterns That Actually Work in 2026](https://www.netguru.com/blog/frontend-design-patterns) — Component-driven architecture, state management
- [Creating dialogs in Flutter - LogRocket Blog](https://blog.logrocket.com/creating-dialogs-flutter/) — Dialog widget patterns
- [ExpansionPanel in Flutter: A guide with examples](https://blog.logrocket.com/expansionpanel-flutter-guide-with-examples/) — Expandable content patterns

**UI/UX Best Practices:**
- [Best Practices for Designing Selection Controls](https://app.uxcel.com/courses/ui-components-n-patterns/selection-controls-best-practices-324) — Selection interface design
- [Chatbot UI Best Practices for 2026](https://vynta.ai/blog/chatbot-ui/) — Transparent AI disclosure, skill prepending patterns
- [10 UX Best Practices to Follow in 2026](https://uxpilot.ai/blogs/ux-best-practices) — Error prevention, cognitive load reduction

**AI Assistant Patterns:**
- [AI Assistant UI Guide | Adobe Experience Cloud](https://experienceleague.adobe.com/en/docs/experience-cloud-ai/experience-cloud-ai/ai-assistant/ai-assistant-ui) — Skill discovery, browsable capabilities
- [Conversational Interfaces: the Good, the Ugly & the Billion-Dollar Opportunity](https://lg.substack.com/p/conversational-interfaces-the-good) — Delegative UI, context injection

**Flutter Documentation:**
- [Material component widgets](https://docs.flutter.dev/ui/widgets/material) — Official widget catalog
- [Dialog class - material library](https://api.flutter.dev/flutter/material/Dialog-class.html) — Dialog widget API
- [SimpleDialog class](https://api.flutter.dev/flutter/material/SimpleDialog-class.html) — SimpleDialog patterns

---

*Architecture research for: Skill Discovery & Selection Integration*
*Researched: 2026-02-18*
*Confidence: HIGH — Based on existing codebase analysis, official Flutter docs, and 2026 AI UX patterns*
