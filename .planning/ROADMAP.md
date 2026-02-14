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
- 📋 **v0.1-claude-code: Claude Code as AI Backend** - Phases 57-61 (active)
- 🗄️ **v2.0 Security Audit & Deployment** - Phases 49-53 (backlogged)

## Phases

<details>
<summary>✅ v2.1 Rich Document Support (Phases 54-56) — SHIPPED 2026-02-12</summary>

- [x] Phase 54: Backend Foundation (3/3 plans) — completed 2026-02-12
- [x] Phase 55: Frontend Display & AI Context (3/3 plans) — completed 2026-02-12
- [x] Phase 56: Export Features (2/2 plans) — completed 2026-02-12

Full details: `.planning/milestones/v2.1-ROADMAP.md`

</details>

### 📋 v0.1-claude-code: Claude Code as AI Backend (Active)

**Milestone Goal:** Determine if Claude Code's agent capabilities (via Python SDK or CLI subprocess) produce measurably better business analysis artifacts than the current direct API approach, and if so, build a production-viable adapter.

**Branch:** `feature/claude-code-backend` (experiment isolated from master, Phase 61 gates merge)

- [x] **Phase 57: Foundation** - Shared infrastructure for both adapters (completed 2026-02-13)
- [x] **Phase 58: Agent SDK Adapter** - Primary integration via Python SDK (completed 2026-02-14)
- [x] **Phase 59: CLI Subprocess Adapter** - Experimental CLI subprocess integration (completed 2026-02-14)
- [ ] **Phase 60: Frontend Integration** - Provider selection and streaming UI
- [ ] **Phase 61: Quality Comparison & Decision** - Measure quality and decide go/no-go

#### Phase 57: Foundation
**Goal**: Shared infrastructure ready for both SDK and CLI adapter implementations
**Depends on**: Nothing (experiment start)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04
**Success Criteria** (what must be TRUE):
  1. Developer can verify claude-agent-sdk v0.1.35+ installed with bundled CLI
  2. MCP tools (search_documents, save_artifact) extracted to shared reusable module
  3. LLMFactory recognizes "claude-code-sdk" provider and can route to adapter stub
  4. LLMFactory recognizes "claude-code-cli" provider and can route to adapter stub
**Plans:** 2 plans

Plans:
- [x] 57-01-PLAN.md — Upgrade SDK to v0.1.35+ and extract MCP tools to shared module
- [x] 57-02-PLAN.md — Register claude-code-sdk and claude-code-cli providers in LLMFactory with adapter stubs

#### Phase 58: Agent SDK Adapter
**Goal**: Claude Agent SDK integrated as production-viable provider via LLMAdapter pattern
**Depends on**: Phase 57 (shared tools and factory registration)
**Requirements**: SDK-01, SDK-02, SDK-03, SDK-04, SDK-05
**Success Criteria** (what must be TRUE):
  1. ClaudeAgentAdapter implements LLMAdapter.stream_chat() and yields StreamChunk events
  2. SDK agent loop events translate to StreamChunk format without data loss (text, thinking, tool_use, complete, error)
  3. MCP server integrates search_documents and save_artifact tools with proper context propagation
  4. User can create thread with claude-code-sdk provider and receive streaming responses via existing SSE endpoint
  5. SDK errors map to StreamChunk error chunks with user-friendly messages
**Plans:** 2 plans

Plans:
- [x] 58-01-PLAN.md — Implement ClaudeAgentAdapter.stream_chat() with SDK event translation and AIService agent routing
- [x] 58-02-PLAN.md — Unit tests for adapter stream_chat and AIService agent provider routing

#### Phase 59: CLI Subprocess Adapter
**Goal**: Claude Code CLI integrated as experimental provider for quality comparison
**Depends on**: Phase 57 (shared tools and factory registration)
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05
**Success Criteria** (what must be TRUE):
  1. ClaudeCLIAdapter implements LLMAdapter.stream_chat() and spawns CLI subprocess per request
  2. CLI subprocess lifecycle managed properly (spawn with flags, cleanup prevents zombies, timeout handling)
  3. JSON stream from CLI stdout parsed into StreamChunk events with proper event boundaries
  4. Tools work via MCP server or prompt-based approach (document search and artifact save functional)
  5. Subprocess cleanup prevents memory leaks and orphaned processes in async FastAPI context
**Plans:** 2 plans

Plans:
- [x] 59-01-PLAN.md — Implement ClaudeCLIAdapter.stream_chat() with subprocess lifecycle and JSON event translation
- [x] 59-02-PLAN.md — Unit tests for ClaudeCLIAdapter (subprocess mocking, event translation, cleanup verification)

#### Phase 60: Frontend Integration
**Goal**: Users can select Claude Code providers and use them for conversations
**Depends on**: Phase 58 (SDK adapter) and Phase 59 (CLI adapter)
**Requirements**: UI-01, UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):
  1. Settings page provider dropdown shows "Claude Code (SDK)" option
  2. Settings page provider dropdown shows "Claude Code (CLI)" option
  3. User can create new thread with claude-code-sdk or claude-code-cli provider
  4. Chat streaming works end-to-end with new providers (messages sent, AI responses stream, thinking displays, tools execute)
**Plans**: TBD

Plans:
- [ ] 60-01: TBD

#### Phase 61: Quality Comparison & Decision
**Goal**: Measurable quality comparison with clear go/no-go recommendation
**Depends on**: Phase 60 (both adapters functional in UI)
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05
**Success Criteria** (what must be TRUE):
  1. 5+ BRDs generated with direct API (anthropic provider baseline) with quality metrics recorded
  2. 5+ BRDs generated with Agent SDK adapter (claude-code-sdk) with quality metrics recorded
  3. 5+ BRDs generated with CLI subprocess adapter (claude-code-cli) with quality metrics recorded
  4. Quality metrics defined and scored across all samples (completeness, AC quality, consistency, error coverage)
  5. Comparison report written with recommendation (adopt SDK, adopt CLI, stay with direct API, or enhance direct API with multi-pass)
**Plans**: TBD

Plans:
- [ ] 61-01: TBD

## Coverage

### v0.1-claude-code: Claude Code as AI Backend

**Requirements mapped: 19/19**

| Requirement | Phase | Description |
|-------------|-------|-------------|
| FOUND-01 | 57 | Install claude-agent-sdk with bundled CLI |
| FOUND-02 | 57 | Extract MCP tools to shared module |
| FOUND-03 | 57 | Register claude-code-sdk in LLMFactory |
| FOUND-04 | 57 | Register claude-code-cli in LLMFactory |
| SDK-01 | 58 | ClaudeAgentAdapter implements LLMAdapter |
| SDK-02 | 58 | Event translation to StreamChunk format |
| SDK-03 | 58 | MCP server with search/artifact tools |
| SDK-04 | 58 | SSE streaming via existing endpoint |
| SDK-05 | 58 | Error handling and mapping |
| CLI-01 | 59 | ClaudeCLIAdapter implements LLMAdapter |
| CLI-02 | 59 | Subprocess lifecycle management |
| CLI-03 | 59 | JSON stream parsing to StreamChunk |
| CLI-04 | 59 | Tool integration via MCP |
| CLI-05 | 59 | Subprocess cleanup and memory safety |
| UI-01 | 60 | SDK option in provider dropdown |
| UI-02 | 60 | CLI option in provider dropdown |
| UI-03 | 60 | Thread creation with new providers |
| UI-04 | 60 | End-to-end chat streaming |
| QUAL-01 | 61 | Baseline BRD generation |
| QUAL-02 | 61 | SDK BRD generation |
| QUAL-03 | 61 | CLI BRD generation |
| QUAL-04 | 61 | Quality metrics scoring |
| QUAL-05 | 61 | Comparison report with recommendation |

## Progress

**Execution Order:** 57 → 58 → 59 → 60 → 61

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 57. Foundation | v0.1-claude-code | 2/2 | Complete | 2026-02-13 |
| 58. Agent SDK Adapter | v0.1-claude-code | 2/2 | Complete | 2026-02-14 |
| 59. CLI Subprocess Adapter | v0.1-claude-code | 2/2 | Complete | 2026-02-14 |
| 60. Frontend Integration | v0.1-claude-code | 0/TBD | Not started | - |
| 61. Quality Comparison & Decision | v0.1-claude-code | 0/TBD | Not started | - |

---

## Backlog

<details>
<summary>🗄️ v2.0 Security Audit & Deployment (Backlogged 2026-02-13)</summary>

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
*Phase 57 planned: 2026-02-13 — 2 plans in 2 waves*
*Phase 57 completed: 2026-02-13 — SDK v0.1.35+, shared MCP tools, factory registration with adapter stubs*
