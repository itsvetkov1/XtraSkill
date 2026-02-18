# Requirements: BA Assistant — v3.1 Skill Discovery & Selection

**Defined:** 2026-02-18
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v3.1 Requirements

Requirements for v3.1 milestone. Each maps to roadmap phases.

### Skill Metadata

- [ ] **META-01**: Each skill has YAML frontmatter with name, description, and features list in its SKILL.md
- [ ] **META-02**: User-facing skill names are human-readable (e.g., "Business Analyst" not "business-analyst")
- [ ] **META-03**: Each skill description is a concise 1-2 sentence summary of what it does
- [ ] **META-04**: Each skill features list contains 3-5 key capabilities

### Skill API

- [ ] **API-01**: GET /api/skills returns name, description, and features for each skill parsed from SKILL.md frontmatter
- [ ] **API-02**: Skills without frontmatter fall back gracefully (name from directory, no description)

### Skill Browser

- [ ] **BROWSE-01**: User can open a skill browser dialog from the chat input skill button
- [ ] **BROWSE-02**: User can see all available skills in a grid/list layout with names and descriptions
- [ ] **BROWSE-03**: User can select a skill from the browser to use in their next message
- [ ] **BROWSE-04**: Skill browser closes after selection

### Selection Indicator

- [ ] **SEL-01**: Selected skill is shown as a chip/badge near the chat input
- [ ] **SEL-02**: User can tap the chip to deselect the skill
- [ ] **SEL-03**: Only one skill can be selected at a time

### Skill Info

- [ ] **INFO-01**: Each skill in the browser has an info button
- [ ] **INFO-02**: Info button opens a popup/balloon showing the skill's description and features
- [ ] **INFO-03**: User can dismiss the info popup and return to the skill browser

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Search & Navigation

- **SEARCH-01**: User can filter skills by typing in a search field
- **SEARCH-02**: User can open skill browser via keyboard shortcut (Ctrl+K / Cmd+K)

### Categories

- **CAT-01**: Skills grouped by category (analysis, coding, testing)
- **CAT-02**: Category badges shown on skill cards

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-skill selection | Current system is single-select per message; multi-skill adds complexity |
| Skill creation/editing UI | Skills are file-based (.claude/ directory); editing happens in IDE |
| Skill marketplace/sharing | Out of scope for solo developer tool |
| BA flow skill selector | Enhancement is Assistant section only; BA flow unchanged |
| Client-side SKILL.md parsing | Research says server-side parsing is safer and faster |
| Skill usage analytics | Deferred until need for "recent skills" sorting is validated |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| META-01 | — | Pending |
| META-02 | — | Pending |
| META-03 | — | Pending |
| META-04 | — | Pending |
| API-01 | — | Pending |
| API-02 | — | Pending |
| BROWSE-01 | — | Pending |
| BROWSE-02 | — | Pending |
| BROWSE-03 | — | Pending |
| BROWSE-04 | — | Pending |
| SEL-01 | — | Pending |
| SEL-02 | — | Pending |
| SEL-03 | — | Pending |
| INFO-01 | — | Pending |
| INFO-02 | — | Pending |
| INFO-03 | — | Pending |

**Coverage:**
- v3.1 requirements: 16 total
- Mapped to phases: 0
- Unmapped: 16

---
*Requirements defined: 2026-02-18*
*Last updated: 2026-02-18 after initial definition*
