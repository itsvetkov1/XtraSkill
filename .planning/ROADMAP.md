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
- 🚧 **v3.1.1 Assistant Conversation Memory** - Phases 68-70 (in progress)
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

### 🚧 v3.1.1 Assistant Conversation Memory (In Progress)

**Milestone Goal:** Fix the critical bug where the Assistant loses conversation context after 2-3 messages, add token optimization to prevent context window overflow, and baseline subprocess performance.

- [x] **Phase 68: Core Conversation Memory Fix** - Replace single-message prompting with full history formatting, validate with tests (completed 2026-02-19)
- [ ] **Phase 69: Token Optimization** - Filter tool_use blocks and ensure linear token growth across long conversations
- [ ] **Phase 70: Performance Tuning** - Measure subprocess latency and implement process pooling for warm reuse

## Phase Details

### Phase 68: Core Conversation Memory Fix
**Goal**: Assistant conversations preserve full context across all turns
**Depends on**: Phase 67 (v3.1 complete)
**Requirements**: CONV-01, CONV-02, CONV-03, CONV-04, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05
**Success Criteria** (what must be TRUE):
  1. User can have a 5+ turn conversation in Assistant mode where the AI correctly references information from earlier turns
  2. Each message sent to the CLI subprocess includes the full conversation history with clear role labels
  3. BA Assistant flow continues to work identically (no regression from CLI adapter changes)
  4. Backend and frontend test suites pass with new conversation memory tests
**Plans**: 2 plans

Plans:
- [ ] 68-01-PLAN.md — Backend fix: replace single-message prompt with multi-turn formatter + unit tests + integration test
- [ ] 68-02-PLAN.md — Frontend tests: AssistantConversationProvider unit test coverage

### Phase 69: Token Optimization
**Goal**: Long Assistant conversations with document context stay within token limits without degrading quality
**Depends on**: Phase 68
**Requirements**: TOKEN-01, TOKEN-02, TOKEN-03, TOKEN-04
**Success Criteria** (what must be TRUE):
  1. A 20+ turn conversation with document searches shows linear (not quadratic) token growth
  2. Assistant messages sent to CLI have tool_use blocks stripped, keeping only human-readable text
  3. Conversations exceeding 180K tokens show a clear error message instead of a silent failure
  4. Existing 150K truncation limit continues to function correctly for the CLI adapter
**Plans**: TBD

Plans:
- [ ] 69-01: TBD

### Phase 70: Performance Tuning
**Goal**: Subprocess spawn overhead is measured, documented, and reduced through process pooling
**Depends on**: Phase 68
**Requirements**: PERF-01, PERF-02, PERF-03
**Success Criteria** (what must be TRUE):
  1. Subprocess spawn latency is measured and recorded as a baseline (expected ~400ms)
  2. Process pooling reuses warm subprocesses instead of cold-starting each message
  3. Measured latency improvement is documented (target: under 200ms with warm pool)
**Plans**: TBD

Plans:
- [ ] 70-01: TBD

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
Phases execute in numeric order: 68 → 69 → 70

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 68. Core Conversation Memory Fix | 2/2 | Complete   | 2026-02-19 | - |
| 69. Token Optimization | v3.1.1 | 0/TBD | Not started | - |
| 70. Performance Tuning | v3.1.1 | 0/TBD | Not started | - |

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
