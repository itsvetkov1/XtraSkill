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
- ✅ **v3.1 Skill Discovery & Selection** - Phases 65-67 (shipped 2026-02-18)
- ✅ **v3.1.1 Assistant Conversation Memory** - Phases 68-70 (shipped 2026-02-20)
- 🚧 **v3.2 Assistant File Generation & CLI Permissions** - Phases 71-73 (in progress)
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

<details>
<summary>✅ v3.1 Skill Discovery & Selection (Phases 65-67) — SHIPPED 2026-02-18</summary>

**Milestone Goal:** Enhance the Assistant skill selector into a browsable list with descriptions, info popups, and transparent skill prepending.

- [x] Phase 65: Backend Skill Metadata (2/2 plans) — completed 2026-02-18
- [x] Phase 66: Skill Browser UI (2/2 plans) — completed 2026-02-18
- [x] Phase 67: Skill Info Popup (1/1 plans) — completed 2026-02-18

Full details: `.planning/milestones/v3.1-ROADMAP.md`

</details>

<details>
<summary>✅ v3.1.1 Assistant Conversation Memory (Phases 68-70) — SHIPPED 2026-02-20</summary>

- [x] Phase 68: Core Conversation Memory Fix (2/2 plans) — completed 2026-02-19
- [x] Phase 69: Token Optimization (1/1 plans) — completed 2026-02-20
- [x] Phase 70: Performance Tuning (1/1 plans) — completed 2026-02-20

Full details: `.planning/milestones/v3.1.1-ROADMAP.md`

</details>

---

### v3.2 Assistant File Generation & CLI Permissions (In Progress)

**Milestone Goal:** Enable the Assistant to generate arbitrary files on demand via a dialog-driven workflow with export cards, and fix CLI subprocess to run non-interactively without blocking on permission prompts.

## Phases (v3.2)

- [x] **Phase 71: CLI Permissions Fix** - Add `--dangerously-skip-permissions` to all three CLI spawn paths (completed 2026-02-23)
- [x] **Phase 72: Backend File Generation** - Wire save_artifact tool and system prompt for Assistant file generation (completed 2026-02-24)
- [ ] **Phase 73: Frontend File Generation** - Provider state, generate dialog, artifact card rendering, and UI wire-up

## Phase Details

### Phase 71: CLI Permissions Fix
**Goal**: The Claude CLI subprocess runs non-interactively without blocking on any permission prompt in all spawn paths
**Depends on**: Nothing (first phase of milestone)
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05
**Success Criteria** (what must be TRUE):
  1. Running `ps aux | grep claude` shows 2 pre-warmed pool processes each carrying `--dangerously-skip-permissions`
  2. Sending a message in the Assistant chat completes without any permission prompt blocking the response
  3. A cold-spawn fallback (when pool is exhausted) also produces a response without blocking
**Plans**: 1 plan

Plans:
- [ ] 71-01-PLAN.md -- Add skip-permissions flag to all 3 spawn sites + test assertions

### Phase 72: Backend File Generation
**Goal**: The backend generates and persists a file artifact for Assistant threads when `artifact_generation=True` is sent via the existing chat endpoint
**Depends on**: Phase 71
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04
**Success Criteria** (what must be TRUE):
  1. A `curl` POST to `/api/threads/{assistant_thread_id}/chat` with `artifact_generation=true` returns an `artifact_created` SSE event with a valid artifact ID
  2. The artifact is retrievable via GET `/api/artifacts/{id}` with `artifact_type` of `generated_file`
  3. No BA system prompt content appears in the CLI invocation for Assistant threads (verified via process arguments or debug logging)
  4. The `generated_file` ArtifactType value exists in the backend enum and Alembic migration has been applied
**Plans**: 2 plans

Plans:
- [ ] 72-01-PLAN.md -- ArtifactType enum + Alembic migration + FastMCP server + mount
- [ ] 72-02-PLAN.md -- CLI adapter flags + ARTIFACT_CREATED detection + parameter threading + system prompt

### Phase 73: Frontend File Generation
**Goal**: Users can tap a "Generate File" button, describe what to generate in a dialog, and see the result as a collapsible artifact card with export options in the Assistant chat
**Depends on**: Phase 72
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, UI-09
**Success Criteria** (what must be TRUE):
  1. A "Generate File" icon button is visible in the Assistant chat input bar next to the send button
  2. Tapping the button opens a bottom sheet dialog with a free-text field; tapping Confirm closes the dialog immediately and starts generation
  3. While generation is in progress the chat area shows a loading indicator (not a blank message bubble)
  4. When generation completes an artifact card appears in the message list that can be collapsed and expanded
  5. The artifact card has functional export buttons for Markdown, PDF, and Word that download the generated content
**Plans**: TBD

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
Phases execute in numeric order: 71 → 72 → 73

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 68. Core Conversation Memory Fix | v3.1.1 | 2/2 | Complete | 2026-02-19 |
| 69. Token Optimization | v3.1.1 | 1/1 | Complete | 2026-02-20 |
| 70. Performance Tuning | v3.1.1 | 1/1 | Complete | 2026-02-20 |
| 71. CLI Permissions Fix | 1/1 | Complete    | 2026-02-23 | - |
| 72. Backend File Generation | 2/2 | Complete    | 2026-02-24 | - |
| 73. Frontend File Generation | v3.2 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-09*
*v2.1 archived: 2026-02-12 — 3 phases, 8 plans, 24/24 requirements shipped*
*v2.0 backlogged: 2026-02-13 — paused for Claude Code experiment*
*v0.1-claude-code activated: 2026-02-13 — 5 phases, research complete*
*v0.1-claude-code archived: 2026-02-17 — 5 phases, 11/12 plans shipped*
*v3.0 activated: 2026-02-17 — 3 phases, 17 requirements, Assistant Foundation*
*v3.0 archived: 2026-02-18 — 3 phases, 10 plans, 17/17 requirements shipped*
*v3.1 activated: 2026-02-18 — 3 phases, 16 requirements, Skill Discovery & Selection*
*v3.1 archived: 2026-02-18 — 3 phases, 5 plans, 16/16 requirements shipped*
*v3.1.1 activated: 2026-02-19 — 3 phases, 16 requirements, Assistant Conversation Memory*
*v3.1.1 archived: 2026-02-20 — 3 phases, 3 plans, 16/16 requirements shipped*
*v3.2 activated: 2026-02-23 — 3 phases, 18 requirements, Assistant File Generation & CLI Permissions*
