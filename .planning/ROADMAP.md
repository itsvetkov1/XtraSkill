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

---

*Roadmap created: 2026-02-09*
*v2.1 archived: 2026-02-12 — 3 phases, 8 plans, 24/24 requirements shipped*
*v2.0 backlogged: 2026-02-13 — paused for Claude Code experiment*
*v0.1-claude-code activated: 2026-02-13 — 5 phases, research complete*
*v0.1-claude-code archived: 2026-02-17 — 5 phases, 11/12 plans shipped*
*v3.0 activated: 2026-02-17 — 3 phases, 17 requirements, Assistant Foundation*
*v3.0 archived: 2026-02-18 — 3 phases, 10 plans, 17/17 requirements shipped*
