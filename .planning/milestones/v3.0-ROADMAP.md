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
- 🚧 **v3.0 Assistant Foundation** - Phases 62-64 (in progress)
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

### v3.0 Assistant Foundation (In Progress)

**Milestone Goal:** Separate Claude Code CLI into its own "Assistant" section with dedicated screens, clean of BA-specific logic — foundation for building a multi-purpose AI assistant.

**Branch:** `feature/claude-code-backend`

- [x] **Phase 62: Backend Foundation** - Data model, service logic, and API endpoints for thread_type discrimination (completed 2026-02-17)
- [x] **Phase 63: Navigation & Thread Management** - Assistant sidebar section, routes, thread list, create, and delete (completed 2026-02-17)
- [x] **Phase 64: Conversation & Documents** - End-to-end chat and document upload for Assistant threads (completed 2026-02-17)

## Phase Details

### Phase 62: Backend Foundation
**Goal**: Backend fully supports thread_type discrimination — data model, service logic, and API endpoints all enforce clean separation between BA Assistant and Assistant threads
**Depends on**: Phase 61 (CLI adapter exists and works)
**Requirements**: DATA-01, DATA-02, DATA-03, LOGIC-01, LOGIC-02, LOGIC-03, API-01, API-02, API-03
**Success Criteria** (what must be TRUE):
  1. Creating a thread via API with `thread_type=assistant` stores the type in the database and returns it in the response
  2. Listing threads with `?thread_type=assistant` returns only Assistant threads; omitting the filter returns all threads (backward compatible)
  3. Sending a message in an Assistant thread produces a response with no BA system prompt content and no BA tool calls (search_documents, save_artifact)
  4. Attempting to create an Assistant thread with a project_id returns a validation error
  5. Existing threads in the database have `thread_type=ba_assistant` after migration (no null values)
**Plans**: 3 plans
- [ ] 62-01-PLAN.md — Data model: ThreadType enum, thread_type field on Thread, thread_id on Document, migration with backfill
- [ ] 62-02-PLAN.md — API layer: thread_type on create/list/get endpoints, response models, frontend fix
- [ ] 62-03-PLAN.md — Service logic: AIService conditional routing, file validator limits, usage tracking

### Phase 63: Navigation & Thread Management
**Goal**: Users can navigate to a dedicated Assistant section and manage threads (create, view list, delete) independently of BA Assistant
**Depends on**: Phase 62 (API supports thread_type filtering and creation)
**Requirements**: NAV-01, NAV-02, NAV-03, UI-01, UI-02, UI-05
**Success Criteria** (what must be TRUE):
  1. Sidebar shows an "Assistant" entry that navigates to the Assistant thread list screen
  2. Assistant thread list shows only Assistant-type threads (no BA threads appear)
  3. User can create a new Assistant thread via a simplified dialog (no project selector, no mode selector) and it appears in the list
  4. User can delete an Assistant thread with the standard undo behavior (10-second window)
  5. Navigating directly to `/assistant` or `/assistant/:threadId` in the browser loads the correct screen, including on page refresh
**Plans**: 2 plans
- [ ] 63-01-PLAN.md — Navigation infrastructure + sidebar + AssistantListScreen with API-filtered thread list
- [ ] 63-02-PLAN.md — Thread creation dialog + deletion with undo and navigate-away

### Phase 64: Conversation & Documents
**Goal**: Users can have full conversations in Assistant threads and upload documents for context, completing the end-to-end Assistant workflow
**Depends on**: Phase 63 (Assistant screens exist and navigation works)
**Requirements**: UI-03, UI-04
**Success Criteria** (what must be TRUE):
  1. User can send a message in an Assistant thread and receive a streaming response with no BA-specific content
  2. Streaming works end-to-end: text appears progressively, thinking indicators display, and the response completes cleanly
  3. User can upload a document within an Assistant thread and the AI can reference its content in subsequent responses
  4. Assistant conversations use the claude-code-cli adapter regardless of the user's default provider setting
**Plans**: 5 plans
- [ ] 64-01-PLAN.md — Backend: Skills discovery API + thread-scoped document upload/listing endpoints
- [ ] 64-02-PLAN.md — Frontend foundation: AssistantConversationProvider + MarkdownMessage widget with syntax highlighting
- [ ] 64-03-PLAN.md — AssistantChatScreen with message list, streaming display, copy/retry controls
- [ ] 64-04-PLAN.md — AssistantChatInput with file attachment, skill selector, and send controls
- [ ] 64-05-PLAN.md — Document upload: drag-and-drop, paste, backend integration, message attachment display

## Coverage

### v3.0 Assistant Foundation

**Requirements mapped: 17/17**

| Requirement | Phase | Description |
|-------------|-------|-------------|
| DATA-01 | 62 | Thread model has thread_type field | Complete    | 2026-02-17 | 62 | Existing threads default to ba_assistant via migration |
| DATA-03 | 62 | Documents with nullable project_id for Assistant scope |
| LOGIC-01 | 62 | AI service skips BA system prompt for Assistant threads |
| LOGIC-02 | 62 | MCP tools conditionally loaded only for BA threads |
| LOGIC-03 | 62 | Assistant threads always use claude-code-cli adapter |
| API-01 | 62 | Thread creation accepts thread_type parameter |
| API-02 | 62 | Thread listing supports thread_type filter |
| API-03 | 62 | Assistant threads cannot have project association |
| NAV-01 | 63 | Assistant appears as own section in sidebar | Complete    | 2026-02-17 | 63 | Dedicated routes /assistant and /assistant/:threadId |
| NAV-03 | 63 | Deep links work correctly on page refresh |
| UI-01 | 63 | Assistant thread list shows only Assistant threads |
| UI-02 | 63 | Simplified thread creation dialog |
| UI-05 | 63 | Thread deletion with standard undo behavior |
| UI-03 | 64 | Conversation screen works end-to-end | Complete    | 2026-02-17 | 64 | Document upload within Assistant threads |

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

**Execution Order:** 62 → 63 → 64

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 57. Foundation | v0.1-claude-code | 2/2 | Complete | 2026-02-13 |
| 58. Agent SDK Adapter | v0.1-claude-code | 2/2 | Complete | 2026-02-14 |
| 59. CLI Subprocess Adapter | v0.1-claude-code | 2/2 | Complete | 2026-02-14 |
| 60. Frontend Integration | v0.1-claude-code | 2/2 | Complete | 2026-02-15 |
| 61. Quality Comparison & Decision | v0.1-claude-code | 3/4 (1 skipped) | Complete | 2026-02-17 |
| 62. Backend Foundation | v3.0 | 0/3 | Planned | - |
| 63. Navigation & Thread Management | v3.0 | 0/2 | Planned | - |
| 64. Conversation & Documents | v3.0 | 0/TBD | Not started | - |

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
