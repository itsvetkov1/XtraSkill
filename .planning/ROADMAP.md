# Roadmap: Business Analyst Assistant

## Milestones

- ✅ **v1.0 MVP** - Phases 1-5 (shipped 2026-01-28)
- ✅ **v1.5 Beta** - Phases 6-10 (shipped 2026-01-30)
- ✅ **v1.6 UX Quick Wins** - Phases 11-14 (shipped 2026-01-30)
- ✅ **v1.7 URL & Deep Links** - Phases 15-18 (shipped 2026-01-31)
- ✅ **v1.8 LLM Provider Switching** - Phases 19-22 (shipped 2026-01-31)
- ✅ **v1.9 UX Improvements** - Phases 23-27 (shipped 2026-02-02)
- ✅ **v1.9.1 Unit Test Coverage** - Phases 28-33 (shipped 2026-02-02)
- ✅ **v1.9.2 Resilience & AI Transparency** - Phases 34-36 (shipped 2026-02-04)
- ✅ **v1.9.3 Document & Navigation Polish** - Phases 37-39 (shipped 2026-02-04)
- ✅ **v1.9.4 Artifact Deduplication** - Phases 40-42 (shipped 2026-02-05)
- ✅ **v1.9.5 Pilot Logging Infrastructure** - Phases 43-48 (shipped 2026-02-08)
- ✅ **v2.1 Rich Document Support** - Phases 54-56 (shipped 2026-02-12)
- ✅ **v0.1-claude-code: Claude Code as AI Backend** - Phases 57-61 (shipped 2026-02-17)
- ✅ **v3.0 Assistant Foundation** - Phases 62-64 (shipped 2026-02-18)
- 🚧 **v3.1 Skill Discovery & Selection** - Phases 65-67 (in progress)
- 🗄️ **v2.0 Security Audit & Deployment** - Phases 49-53 (backlogged)

## Phases

<details>
<summary>✅ v2.1 Rich Document Support (Phases 54-56) — SHIPPED 2026-02-12</summary>

- [x] Phase 54: Backend Foundation (3/3 plans) — completed 2026-02-12
- [x] Phase 55: Frontend Display & AI Context (3/3 plans) — completed 2026-02-12
- [x] Phase 56: Export Features (2/2 plans) — completed 2026-02-12

Full details: `.planning/milestones/v2.1-ROADMAP.md`

</details>

<details>
<summary>✅ v0.1-claude-code: Claude Code as AI Backend (Phases 57-61) — SHIPPED 2026-02-17</summary>

**Milestone Goal:** Determine if Claude Code's agent capabilities (via Python SDK or CLI subprocess) produce measurably better business analysis artifacts than the current direct API approach, and if so, build a production-viable adapter.

**Outcome:** Experiment successful — CLI adapter adopted. Formal quality comparison skipped; user decided to ship based on implementation experience and CLI BRD quality.

**Branch:** `feature/claude-code-backend` → merged to master

- [x] Phase 57: Foundation (2/2 plans) — completed 2026-02-13
- [x] Phase 58: Agent SDK Adapter (2/2 plans) — completed 2026-02-14
- [x] Phase 59: CLI Subprocess Adapter (2/2 plans) — completed 2026-02-14
- [x] Phase 60: Frontend Integration (2/2 plans) — completed 2026-02-15
- [x] Phase 61: Quality Comparison & Decision (3/4 plans, 1 skipped) — completed 2026-02-17

</details>

<details>
<summary>✅ v3.0 Assistant Foundation (Phases 62-64) — SHIPPED 2026-02-18</summary>

- [x] Phase 62: Backend Foundation (3/3 plans) — completed 2026-02-17
- [x] Phase 63: Navigation & Thread Management (2/2 plans) — completed 2026-02-17
- [x] Phase 64: Conversation & Documents (5/5 plans) — completed 2026-02-18

Full details: `.planning/milestones/v3.0-ROADMAP.md`

</details>

### 🚧 v3.1 Skill Discovery & Selection (In Progress)

**Milestone Goal:** Enhance the Assistant skill selector into a browsable list with descriptions, info popups, and transparent skill prepending.

- [x] **Phase 65: Backend Skill Metadata** - Parse SKILL.md frontmatter and enhance API (completed 2026-02-18)
- [x] **Phase 66: Skill Browser UI** - Browsable skill list with selection indicators (completed 2026-02-18)
- [ ] **Phase 67: Skill Info Popup** - Detailed skill information display

## Phase Details

### Phase 65: Backend Skill Metadata
**Goal**: Backend provides rich skill metadata parsed from SKILL.md frontmatter
**Depends on**: Phase 64 (v3.0 complete)
**Requirements**: META-01, META-02, META-03, META-04, API-01, API-02
**Success Criteria** (what must be TRUE):
  1. Each SKILL.md file has YAML frontmatter with name, description, and features
  2. GET /api/skills returns name, description, and features for all skills
  3. Skills without frontmatter fall back gracefully (name from directory, no description)
  4. Skill descriptions are concise 1-2 sentence summaries
  5. Each skill has 3-5 key capabilities listed as features
**Plans**: TBD

Plans:
- [ ] 65-01: TBD
- [ ] 65-02: TBD

### Phase 66: Skill Browser UI
**Goal**: Users can browse and select skills from a rich, browsable interface
**Depends on**: Phase 65
**Requirements**: BROWSE-01, BROWSE-02, BROWSE-03, BROWSE-04, SEL-01, SEL-02, SEL-03
**Success Criteria** (what must be TRUE):
  1. User can open skill browser dialog from chat input skill button
  2. User can see all available skills in grid/list with names and descriptions
  3. User can select a skill by tapping/clicking it
  4. Selected skill appears as removable chip/badge in chat input
  5. User can deselect skill by tapping chip close icon
  6. Only one skill can be selected at a time
  7. Skill browser closes after selection
**Plans**: 2 plans

Plans:
- [x] 66-01-PLAN.md — Foundation: Skill model features field, emoji helper, SkillCard widget
- [x] 66-02-PLAN.md — Browser sheet & integration: DraggableScrollableSheet grid, selector rewrite, chip style

### Phase 67: Skill Info Popup
**Goal**: Users can view detailed skill information before selecting
**Depends on**: Phase 66
**Requirements**: INFO-01, INFO-02, INFO-03
**Success Criteria** (what must be TRUE):
  1. Each skill card has an info icon/button
  2. Tapping info button shows popup with skill description and features
  3. User can dismiss popup and return to skill browser
  4. Info popup is readable on both mobile and desktop
**Plans**: TBD

Plans:
- [ ] 67-01: TBD

---

## Backlog

<details>
<summary>v2.0 Security Audit & Deployment (Backlogged 2026-02-13)</summary>

**Milestone Goal:** Harden the application for production and deploy to live environment with custom domain for pilot group.

**Status at time of backlog:**
- Phase 49-01 planned (code preparation) — plan exists but not executed
- Phase 49-02 planned (Railway deployment checkpoint) — plan exists but not executed
- Phases 50-53 not yet planned
- All plan files preserved in `.planning/phases/49-*`

**Requirements: 16 total (SEC-01..04, HOST-01..04, DOM-01..04, VER-01..04)**

| Phase | Name | Plans | Status |
|-------|------|-------|--------|
| 49 | Backend Deployment Foundation | 2 planned | Not executed |
| 50 | Security Hardening | TBD | Not started |
| 51 | Custom Domain & SSL | TBD | Not started |
| 52 | Frontend Deployment | TBD | Not started |
| 53 | Verification & Documentation | TBD | Not started |

**To resume:** Move back to active section and continue from Phase 49.

</details>

## Progress

**Execution Order:**
Phases execute in numeric order: 65 → 66 → 67

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 65. Backend Skill Metadata | v3.1 | 2/2 | Complete    | 2026-02-18 |
| 66. Skill Browser UI | v3.1 | Complete    | 2026-02-18 | - |
| 67. Skill Info Popup | v3.1 | 0/2 | Not started | - |

---
*Roadmap created: 2026-02-09*
*v2.1 archived: 2026-02-12 — 3 phases, 8 plans, 24/24 requirements shipped*
*v2.0 backlogged: 2026-02-13 — paused for Claude Code experiment*
*v0.1-claude-code activated: 2026-02-13 — 5 phases, research complete*
*v0.1-claude-code archived: 2026-02-17 — 5 phases, 11/12 plans shipped*
*v3.0 activated: 2026-02-17 — 3 phases, 17 requirements, Assistant Foundation*
*v3.0 archived: 2026-02-18 — 3 phases, 10 plans, 17/17 requirements shipped*
*v3.1 activated: 2026-02-18 — 3 phases, 16 requirements, Skill Discovery & Selection*
