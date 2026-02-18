# Stack Research: Skill Discovery & Enhanced UI

**Domain:** Skill discovery UI enhancement (list, parse, display)
**Researched:** 2026-02-18
**Confidence:** HIGH

## Executive Summary

This milestone adds **enhanced skill list UI, SKILL.md parsing, and interactive skill cards** to the existing Flutter/FastAPI stack. The existing `/api/skills` endpoint already scans `.claude/` directories; backend needs frontmatter parsing, frontend needs UI components for chips, badges, tooltips, and responsive grid layouts.

**Key Decision:** Use built-in Flutter Material 3 widgets (`Chip`, `Badge`, `Tooltip`) over third-party packages to minimize dependencies and ensure Material Design compliance.

**Critical Finding:** `cosmic_frontmatter` package shown in search results is for Dart/Flutter, but more robust options exist. For backend Python parsing, use `python-frontmatter` (industry standard). For frontend Flutter parsing (if needed for local files), use `front_matter_ml`.

---

## Recommended Stack

### Backend Additions (Python/FastAPI)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `python-frontmatter` | `^1.1.0` | YAML frontmatter parser for SKILL.md | Industry standard for Python frontmatter parsing. Supports YAML/TOML/JSON. Used by static site generators, AI agent tooling, and documentation systems. More robust than manual regex parsing. [Source](https://github.com/eyeseast/python-frontmatter) |

**Installation:**
```bash
cd backend
source venv/bin/activate
pip install python-frontmatter
pip freeze > requirements.txt
```

**No other backend dependencies needed** — FastAPI routes already exist, SQLite models unchanged.

---

### Frontend Additions (Flutter)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `front_matter_ml` | `^1.2.0` | Parse YAML frontmatter in Dart | If skill files are ever read client-side (unlikely, but enables offline skill browsing). Optional for this milestone. [Source](https://pub.dev/packages/front_matter_ml) |
| `yaml` | `^3.1.2` | Low-level YAML parsing | Dependency of `front_matter_ml`, may be useful for custom parsing logic. [Source](https://pub.dev/packages/yaml) |

**Installation:**
```bash
cd frontend
flutter pub add front_matter_ml  # Optional, only if client-side parsing needed
```

**Material 3 Built-in Widgets (No Installation Required):**

| Widget | Purpose | Already Available |
|--------|---------|------------------|
| `Chip` / `ChoiceChip` | Display selected skills as chips | Material 3 built-in [Source](https://api.flutter.dev/flutter/material/Chip-class.html) |
| `Badge` | Show skill feature counts (e.g., "5 features") | Material 3 built-in [Source](https://api.flutter.dev/flutter/material/Badge-class.html) |
| `Tooltip` | Show skill descriptions on hover/long-press | Material 3 built-in [Source](https://api.flutter.dev/flutter/material/Tooltip-class.html) |
| `GridView.builder` | Responsive skill card grid | Flutter core widget [Source](https://api.flutter.dev/flutter/widgets/GridView-class.html) |
| `Dialog` / `AlertDialog` | Skill info popup with full details | Material 3 built-in [Source](https://api.flutter.dev/flutter/material/Dialog-class.html) |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Third-party dialog packages (`awesome_dialog`, `flutter_dialogs`) | Unnecessary complexity, Material 3 Dialog is feature-complete | Built-in `Dialog` / `AlertDialog` with custom content |
| Third-party chip packages (`chips_choice`, `flutter_tags`) | Material 3 `Chip` and `ChoiceChip` handle all use cases | Built-in `Chip` widgets |
| `badges` package (third-party) | Material 3 `Badge` is official and feature-complete | Built-in `Badge` widget |
| `super_tooltip` (third-party) | Material 3 `Tooltip` supports rich content via `richMessage` parameter | Built-in `Tooltip` with `richMessage` |
| `responsive_grid_list` package | Adds abstraction layer over `ListView.builder` — unnecessary for skill cards | Built-in `GridView.builder` with `SliverGridDelegateWithMaxCrossAxisExtent` |
| Markdown rendering packages (`flutter_markdown`) | Skills use structured frontmatter, not full markdown rendering | Parse frontmatter, display structured data |

**Rationale:** Material 3 (default in Flutter 3.24+) provides all needed UI components. Third-party packages add maintenance burden, version conflicts, and unnecessary abstraction. Built-in widgets are actively maintained, performant, and guarantee cross-platform consistency.

---

## Stack Patterns by Feature

### Feature: Parse SKILL.md Frontmatter (Backend)

**Pattern:**
```python
import frontmatter

# Load skill file
with open(skill_path, 'r', encoding='utf-8') as f:
    post = frontmatter.load(f)

# Access frontmatter fields
name = post.get('name', skill_dir.name)  # Fallback to directory name
description = post.get('description', 'No description')
features = post.get('features', [])  # List of features
tags = post.get('tags', [])  # Optional tags

# Access markdown content (body)
content = post.content
```

**Why:** `python-frontmatter` handles edge cases (multi-line YAML values, escaped quotes, TOML/JSON variants). Manual parsing with regex breaks on complex YAML.

**Current Implementation:** Backend's `_extract_description_from_skill()` manually parses first non-header line. Replace with `python-frontmatter` for structured data access.

---

### Feature: Responsive Skill Grid (Frontend)

**Pattern:**
```dart
GridView.builder(
  gridDelegate: SliverGridDelegateWithMaxCrossAxisExtent(
    maxCrossAxisExtent: 300,  // Max width of each card
    childAspectRatio: 1.2,    // Width/height ratio
    crossAxisSpacing: 16,
    mainAxisSpacing: 16,
  ),
  itemCount: skills.length,
  itemBuilder: (context, index) {
    return SkillCard(skill: skills[index]);
  },
)
```

**Why:** `SliverGridDelegateWithMaxCrossAxisExtent` auto-adjusts columns based on screen width (mobile: 1-2 columns, tablet: 3-4, desktop: 5+). No manual breakpoint logic needed. [Source](https://medium.com/@saadalidev/building-beautiful-responsive-ui-in-flutter-a-complete-guide-for-2026-ea43f6c49b85)

**Alternative:** `SliverGridDelegateWithFixedCrossAxisCount` if you want explicit column counts per breakpoint:
```dart
LayoutBuilder(
  builder: (context, constraints) {
    int columns = constraints.maxWidth > 1200 ? 4
                : constraints.maxWidth > 800 ? 3
                : 2;
    return GridView.builder(
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: columns,
        // ...
      ),
      // ...
    );
  },
)
```

---

### Feature: Skill Info Popup (Frontend)

**Pattern:**
```dart
void _showSkillInfo(BuildContext context, Skill skill) {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(skill.displayName),
      content: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(skill.description),
            SizedBox(height: 16),
            if (skill.features.isNotEmpty) ...[
              Text('Features:', style: TextStyle(fontWeight: FontWeight.bold)),
              ...skill.features.map((f) => Text('• $f')),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text('Close')),
        FilledButton(onPressed: () {
          Navigator.pop(context);
          onSkillSelected(skill);
        }, child: Text('Use Skill')),
      ],
    ),
  );
}
```

**Why:** Material 3 `AlertDialog` handles scrolling, responsive sizing, and theming automatically. No custom dialog package needed. [Source](https://api.flutter.dev/flutter/material/AlertDialog-class.html)

**Material 3 auto-applies:** Max width constraint (560dp on large screens), elevation, theme colors, accessibility labels.

---

### Feature: Selected Skills as Chips (Frontend)

**Pattern:**
```dart
Wrap(
  spacing: 8,
  children: selectedSkills.map((skill) =>
    Chip(
      label: Text(skill.displayName),
      avatar: Badge(
        label: Text('${skill.features.length}'),
        child: Icon(Icons.star, size: 16),
      ),
      onDeleted: () => _removeSkill(skill),
      deleteIcon: Icon(Icons.close, size: 18),
    )
  ).toList(),
)
```

**Why:** `Chip` with `onDeleted` provides Material 3 dismissible UI. `Badge` on avatar shows feature count. `Wrap` auto-wraps chips to next line on narrow screens. [Source](https://www.dhiwise.com/post/mastering-interactive-ui-design-with-flutter-chip)

**Accessibility:** Chips have minimum 48x48px touch targets (Material 3 spec). `Semantics` labels auto-generated for screen readers. [Source](https://medium.com/@expertappdevs/how-to-build-modern-ui-in-flutter-design-patterns-64615b5815fb)

---

### Feature: Skill Card with Tooltip (Frontend)

**Pattern:**
```dart
class SkillCard extends StatelessWidget {
  final Skill skill;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: skill.description,
      preferBelow: false,  // Show above on mobile
      child: Card(
        child: InkWell(
          onTap: () => _showSkillInfo(context, skill),
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.extension, color: Theme.of(context).colorScheme.primary),
                    SizedBox(width: 8),
                    Expanded(child: Text(skill.displayName, style: TextStyle(fontWeight: FontWeight.bold))),
                  ],
                ),
                SizedBox(height: 8),
                Text(skill.description, maxLines: 2, overflow: TextOverflow.ellipsis),
                Spacer(),
                if (skill.features.isNotEmpty)
                  Badge.count(
                    count: skill.features.length,
                    child: Icon(Icons.check_circle_outline),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

**Why:** `Tooltip` shows on hover (desktop/web) and long-press (mobile). `Badge.count` constructor simplifies numeric labels. `InkWell` provides Material ripple effect. [Source](https://api.flutter.dev/flutter/material/Tooltip-class.html)

---

## Version Compatibility

| Frontend Package | Compatible With | Notes |
|------------------|-----------------|-------|
| Flutter SDK 3.9.2+ | Material 3 widgets | `useMaterial3: true` already set in theme |
| `front_matter_ml: ^1.2.0` | `yaml: ^3.1.2` | Depends on `yaml` package internally |

| Backend Package | Compatible With | Notes |
|-----------------|-----------------|-------|
| `python-frontmatter: ^1.1.0` | Python 3.12 | Compatible with existing `PyYAML` in stack |
| | FastAPI 0.115+ | No conflicts with existing dependencies |

**Critical:** `python-frontmatter` uses `PyYAML` internally. Current backend doesn't explicitly list `PyYAML` in requirements.txt, but it's likely installed as a transitive dependency. No version conflicts expected.

---

## Migration Path from Current Implementation

### Backend Changes:

**Current (lines 41-73 in `/backend/app/routes/skills.py`):**
```python
def _extract_description_from_skill(skill_path: Path) -> str:
    # Manual parsing of first non-header line
    # Doesn't extract structured frontmatter
```

**New:**
```python
import frontmatter

def _parse_skill_metadata(skill_path: Path) -> dict:
    """Extract structured metadata from SKILL.md frontmatter."""
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        return {
            'name': post.get('name', ''),
            'description': post.get('description', 'No description'),
            'features': post.get('features', []),
            'tags': post.get('tags', []),
            'content': post.content  # Markdown body (for future use)
        }
    except Exception as e:
        logger.error(f"Failed to parse {skill_path}: {e}")
        return {
            'name': '',
            'description': 'No description',
            'features': [],
            'tags': [],
            'content': ''
        }
```

**API Response Schema Change:**
```python
# OLD: {"name": str, "description": str, "skill_path": str}
# NEW: {"name": str, "description": str, "skill_path": str, "features": list[str], "tags": list[str]}
```

**Migration Note:** Frontend's `Skill` model must be updated to accept new fields. Backward compatible (extra fields ignored by old clients).

---

### Frontend Changes:

**Current `Skill` model (lines 5-46 in `/frontend/lib/models/skill.dart`):**
```dart
class Skill {
  final String name;
  final String description;
  final String skillPath;
}
```

**New:**
```dart
class Skill {
  final String name;
  final String description;
  final String skillPath;
  final List<String> features;
  final List<String> tags;

  Skill({
    required this.name,
    required this.description,
    required this.skillPath,
    this.features = const [],
    this.tags = const [],
  });

  factory Skill.fromJson(Map<String, dynamic> json) {
    return Skill(
      name: json['name'] as String,
      description: json['description'] as String,
      skillPath: json['skill_path'] as String,
      features: (json['features'] as List<dynamic>?)?.map((e) => e as String).toList() ?? [],
      tags: (json['tags'] as List<dynamic>?)?.map((e) => e as String).toList() ?? [],
    );
  }
}
```

**Current `SkillSelector` (lines 10-122 in `/frontend/lib/screens/assistant/widgets/skill_selector.dart`):**
- PopupMenuButton with simple text items
- No feature display, no info popup

**New:**
- Replace `PopupMenuButton` with custom skill grid dialog
- Show feature counts as badges
- Add info button for skill details popup

---

## Performance Considerations

### Backend:

**Concern:** Parsing SKILL.md on every `/api/skills` request could be slow with many skills.

**Mitigation:**
1. **Cache parsed skills:** Use `@lru_cache` decorator on `_parse_skill_metadata()` with file path + mtime as cache key.
2. **Lazy loading:** Only parse frontmatter when skill is accessed (not needed for list view).
3. **Background refresh:** Parse all skills at startup, refresh on file change detection.

**Benchmark (expected):** `python-frontmatter` parses ~1MB/s. Typical SKILL.md is <10KB → <10ms per file. With 10 skills, total parse time <100ms (acceptable for API response).

---

### Frontend:

**Concern:** GridView with many skills could lag on low-end devices.

**Mitigation:**
1. **Use `GridView.builder`:** Lazy rendering (only visible cards built).
2. **Avoid heavy widgets in cards:** Keep card content lightweight (no images, no complex layouts).
3. **Cache skill list:** `SkillService` already caches skills after first fetch.

**Benchmark (expected):** GridView.builder can handle 1000+ items smoothly on modern devices. With <50 skills, performance is not a concern.

---

## Testing Requirements

### Backend Tests:

1. **Frontmatter parsing edge cases:**
   - Multi-line YAML values (descriptions with newlines)
   - Lists in frontmatter (features, tags)
   - Missing frontmatter (fallback to defaults)
   - Invalid YAML (error handling)

2. **API response validation:**
   - Verify new `features` and `tags` fields in JSON response
   - Backward compatibility with old frontend (extra fields ignored)

**Test File:** `/backend/tests/test_skill_integration.py` (already exists)

---

### Frontend Tests:

1. **Model deserialization:**
   - Skill.fromJson with new fields
   - Skill.fromJson with missing fields (defaults applied)

2. **UI widget tests:**
   - SkillCard renders with features badge
   - Tooltip shows on hover/long-press
   - Dialog opens on card tap
   - Chip displays selected skills

**Test Files:**
- `/frontend/test/models/skill_test.dart`
- `/frontend/test/widgets/skill_card_test.dart`

---

## Sources

**Backend:**
- [python-frontmatter GitHub](https://github.com/eyeseast/python-frontmatter) — Industry standard for Python YAML frontmatter parsing
- [python-frontmatter PyPI](https://pypi.org/project/frontmatter/) — Package documentation and version info
- [Python YAML Frontmatter Guide](https://safjan.com/python-packages-yaml-front-matter-markdown/) — Comparison of Python frontmatter libraries

**Frontend (Flutter):**
- [Flutter Material Chip API](https://api.flutter.dev/flutter/material/Chip-class.html) — Official Chip widget documentation
- [Flutter Material Badge API](https://api.flutter.dev/flutter/material/Badge-class.html) — Official Badge widget documentation
- [Flutter Material Tooltip API](https://api.flutter.dev/flutter/material/Tooltip-class.html) — Official Tooltip widget documentation
- [Flutter Dialog API](https://api.flutter.dev/flutter/material/Dialog-class.html) — Official Dialog widget documentation
- [Flutter GridView API](https://api.flutter.dev/flutter/widgets/GridView-class.html) — Official GridView widget documentation
- [Flutter Responsive Grid Best Practices](https://medium.com/@saadalidev/building-beautiful-responsive-ui-in-flutter-a-complete-guide-for-2026-ea43f6c49b85) — 2026 responsive layout guide
- [Flutter Chip Best Practices](https://www.dhiwise.com/post/mastering-interactive-ui-design-with-flutter-chip) — Interactive UI design with chips
- [Material 3 Updates 2025-2026](https://dcm.dev/blog/2025/12/23/top-flutter-features-2025) — Material 3 chip/badge/tooltip enhancements
- [front_matter_ml pub.dev](https://pub.dev/packages/front_matter_ml) — Dart YAML frontmatter parser (optional for Flutter)

---

*Stack research for: Skill Discovery UI Enhancement*
*Researched: 2026-02-18*
*Overall Confidence: HIGH (verified with official docs + 2026 sources)*
