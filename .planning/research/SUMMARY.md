# Project Research Summary

**Project:** XtraSkill v3.0 — Assistant Foundation
**Domain:** Dual-mode AI chat application (BA Assistant + Claude Code CLI)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Executive Summary

This research addresses the architectural separation of an existing single-purpose BA Assistant into a dual-mode application supporting both BA-specific discovery workflows and a standalone Claude Code CLI assistant. The recommended approach treats thread type as a first-class discriminator—stored in the database, enforced at the service layer, and isolated through separate navigation branches. The core insight: this is **not** a feature addition requiring new infrastructure, but a **refactoring task** requiring architectural discipline to prevent context leakage between modes.

The critical risk is **implicit coupling** in the existing `ai_service.py`. The 600-line BA system prompt is currently hardcoded and applied to all conversations. Adding a second mode tempts developers to refactor this into conditional logic (`if thread_type == BA`), which creates five failure modes: (1) system prompt leakage between flows, (2) document search returning cross-mode results, (3) shared tool definitions bleeding BA-specific behavior into Assistant threads, (4) navigation context conflicts in GoRouter, and (5) CLI subprocess management blocking the async event loop. All five require **preventive architecture** in foundation phases—remediation after implementation is 10x more expensive.

The correct pattern is **service separation with shared utilities**: split `ai_service.py` into `ba_service.py` and `assistant_service.py` before implementing Assistant features. Each service owns its system prompt, tool definitions, and conversation formatting. Shared code (LLM adapters, token counting) moves to `ai/` utilities module. This modular monolith approach prevents conditional logic bugs while maintaining a single FastAPI application. The roadmap must enforce this separation in Phase 1 (Data Model & Service Foundation) before any UI work—skipping foundation to "ship faster" guarantees technical debt requiring rewrites.

## Key Findings

### Recommended Stack

The existing Flutter + FastAPI stack requires zero new dependencies. This is a refactoring project, not a greenfield build. The database needs a single new field (`thread_type` enum), the backend needs service-layer separation (code organization, not new libraries), and the frontend needs a fifth navigation branch in the existing StatefulShellRoute configuration.

**Core technologies (no changes):**
- **Flutter ^3.9.2** — Existing web/mobile frontend; GoRouter StatefulShellRoute pattern already validated for multi-section navigation
- **FastAPI >=0.129.0** — Python async backend; minor version update recommended for Python 3.14 support and Pydantic v2 improvements (current: 0.115.0)
- **SQLAlchemy >=2.0.46** — Async ORM; update for async session improvements (current: 2.0.35)
- **GoRouter ^17.0.1** — Already integrated; StatefulShellRoute.indexedStack perfect for BA vs Assistant separation
- **Provider ^6.1.5** — State management sufficient for thread filtering by type (Riverpod migration unjustified)

**Database changes (minimal):**
- **Alembic >=1.13.0** — Migration tool for adding `thread_type` enum field to existing Thread model
- **SQLite FTS5** — Full-text search already implemented; add `scope` discriminator to Document model for isolation

**Critical version notes:**
- FastAPI 0.129.0 (latest: 2026-02-12) adds Python 3.14 support with no breaking changes for this project
- SQLAlchemy 2.0.46 (latest: 2026-01-21) improves async session lifecycle management
- No new frontend dependencies—`go_router`, `provider`, `dio`, `flutter_client_sse` already cover all needs

**What NOT to add:**
- No separate AssistantService class duplication—use shared `ai/` utilities with separate service modules
- No Riverpod migration—Provider handles thread type filtering efficiently
- No GraphQL layer—REST endpoints with `thread_type` query parameter sufficient
- No separate AssistantThread model—single Thread table with enum discriminator cleaner
- No feature flag system—this is a permanent UX change, not an experiment

### Expected Features

The Assistant section mirrors the BA Assistant UX but strips away project-scoped complexity. Users expect feature parity for core chat functionality (thread creation, SSE streaming, markdown rendering, model provider selection) but explicitly do NOT expect BA-specific features (document search tools, artifact generation, conversation mode selection, project association).

**Must have (table stakes):**
- Thread creation with type=assistant (project-less, user-scoped)
- Message sending via existing conversation route (no changes to streaming infrastructure)
- SSE streaming responses (already implemented, reused for Assistant)
- Thread listing filtered by type=assistant (clone ChatsScreen UI with type filter)
- Thread deletion, renaming, markdown rendering (all existing features)
- Model provider selection (expose in UI, already implemented in backend)
- Token usage tracking (existing infrastructure, transparent across types)
- Deep linking to `/assistant/:id` routes (parallel to `/chats/:id`)

**Should have (differentiators):**
- No system prompt overhead—faster responses (600-line BA prompt removed)
- General knowledge access—not constrained to BA domain expertise
- Project-agnostic—works without creating projects first (onboarding simplification)
- Simpler UX—no conversation mode selector (Meeting/Refinement is BA-specific)
- Faster onboarding—new users can chat immediately without document upload prerequisite

**Defer (v2+):**
- Document upload for Assistant threads (needs document scope isolation architecture, deferred until post-MVP validation)
- Cross-project context (requires project association rethink, complex scoping)
- Artifact generation in Assistant (no clear non-BA use case identified yet)
- Advanced filtering (thread type + provider + date range—nice-to-have, not essential)
- Conversation templates (pre-built thread starters for common Assistant use cases)

**Anti-features (explicitly omit):**
- Document search tool in Assistant (no project context makes scope unclear)
- Artifact generation (save_artifact tool is BA-specific for BRDs/user stories)
- Conversation mode selector (Meeting vs Document Refinement is BA domain logic)
- Project association for Assistant threads (breaks clean separation, violates isolation architecture)
- MCP BA tools (search_documents and save_artifact conditionally disabled for Assistant threads)

### Architecture Approach

The architecture is **modular monolith with service-layer discrimination**. Single FastAPI application, single SQLite database, but strict module boundaries between `ba_assistant/` and `assistant/` service packages. Thread type is stored as a database enum field, enforced at API route validation, and routed to separate service implementations at the service layer. No conditional logic in services—each service is mode-aware only of its own type.

**Major components:**

1. **Thread Model Enhancement** — Add `thread_type` enum field (BA_ASSISTANT | ASSISTANT) with default=BA_ASSISTANT for backward compatibility. Indexed for filtering queries. Immutable after creation (threads don't change modes).

2. **Service Layer Separation** — Split existing `ai_service.py` into:
   - `ba_assistant/ba_service.py` — Owns BA system prompt, BA tools (search_documents, save_artifact), conversation formatting for BA context
   - `assistant/assistant_service.py` — Owns generic system prompt (minimal or none), no tools, pure Claude Code CLI integration
   - `ai/llm_factory.py` — Shared LLM adapter factory (Anthropic, Gemini, DeepSeek, CLI)
   - `ai/token_counter.py` — Shared token utilities
   - Services share ZERO logic except through explicit `ai/` imports. No `if thread_type` conditionals in service files.

3. **API Route Validation** — Separate routes enforce thread type:
   - `POST /api/projects/{id}/threads` — Creates BA threads (requires project_id, sets type=ba_assistant)
   - `POST /api/threads` — Creates Assistant threads (requires project_id=null, sets type=assistant)
   - `POST /api/threads/{id}/chat` — Validates thread.type matches expected service, returns 403 on mismatch
   - `GET /api/threads?thread_type=assistant` — Filters thread list by type

4. **Frontend Navigation (5-branch StatefulShellRoute)** — Add Assistant as fifth branch:
   - Branch 0: `/home` (existing)
   - Branch 1: `/assistant` (NEW—Assistant thread list screen)
   - Branch 2: `/chats` (existing BA threads, shifted from index 1→2)
   - Branch 3: `/projects` (existing, shifted from index 2→3)
   - Branch 4: `/settings` (existing, shifted from index 3→4)
   - Each branch gets separate navigator key to prevent stack pollution
   - Deep links: `/assistant/:id` routes to ConversationScreen with mode=ASSISTANT parameter

5. **System Prompt Injection Point** — AI service layer decides prompt based on thread type:
   ```python
   if thread.thread_type == BA_ASSISTANT:
       system_prompt = BA_SYSTEM_PROMPT  # 600-line BA discovery prompt
       tools = [search_documents, save_artifact]
   else:  # ASSISTANT
       system_prompt = ASSISTANT_SYSTEM_PROMPT  # Generic 5-line prompt or none
       tools = None
   ```
   Adapters remain pure LLM clients—never choose prompts.

6. **Document Isolation (if needed in Phase 2)** — Add `scope` enum to Document model (BA_PROJECT | ASSISTANT_THREAD) with `context_id` field (polymorphic FK to project_id or thread_id). Service-layer queries enforce scope: BA service queries `WHERE scope=BA_PROJECT`, Assistant service queries `WHERE scope=ASSISTANT_THREAD`. Prevents cross-contamination.

**Data flow (Assistant thread creation):**
```
User → "New Assistant Chat" → POST /api/threads {type: "assistant", project_id: null}
  ↓
Thread created with user_id, type=assistant, project_id=null
  ↓
User sends message → POST /api/threads/{id}/chat
  ↓
Route validates thread.type == assistant
  ↓
AssistantService.stream_chat(messages, thread_id)
  ↓
CLIAdapter.stream_chat(messages, ASSISTANT_SYSTEM_PROMPT, tools=None)
  ↓
SSE streaming to frontend (no BA tools, no project context)
```

**Integration points:**
- **Backend:** Thread model + Alembic migration, thread routes (add type param), AI service refactor, CLI adapter (conditional MCP config)
- **Frontend:** Thread model (add threadType field), thread creation dialog (type selector), Assistant screen (clone ChatsScreen), navigation config (add branch), conversation screen (pass mode parameter)

**Anti-patterns to avoid:**
- ❌ Global `SYSTEM_PROMPT` constant used everywhere—make it a function of thread type
- ❌ Thread type stored only in frontend state—must be database field for queries and persistence
- ❌ Duplicating AIService class for each type—use shared utilities with separate service modules
- ❌ Allowing Assistant threads to have project_id—enforce null at API validation layer
- ❌ Mixing Navigator and GoRouter calls—full GoRouter migration required for navigation consistency

### Critical Pitfalls

These five pitfalls cause rewrites if not addressed in foundation phases. All are preventable with proper architecture.

1. **System Prompt Injection via Shared AI Service** — BA's 600-line system prompt leaks into Assistant threads when refactoring to conditional logic. Developers add `if thread_type == BA` branches throughout `ai_service.py`, but one missed branch applies BA prompt to Assistant or vice versa. **Prevention:** Separate `ba_service.py` and `assistant_service.py` files before implementing Assistant. Each owns its own prompt. Zero `if` conditionals in services. **Detection:** Assistant asks BA discovery questions instead of answering general queries. **Phase:** Phase 1 (Service Layer Separation).

2. **Document Ownership Isolation Failure** — Customer A's uploaded requirements document appears in Customer B's BA search results, or BA project documents contaminate Assistant thread context. Occurs when developers create "shared documents pool" or "global project" (project_id=-1) as shortcut instead of explicit `scope` enum. **Prevention:** Add `scope` enum (BA_PROJECT | ASSISTANT_THREAD) and `context_id` field to Document model. Enforce at service layer: BA service queries `WHERE scope=BA_PROJECT`, Assistant queries `WHERE scope=ASSISTANT_THREAD`. Separate FTS5 indexes if needed. **Detection:** User sees documents they didn't upload. **Phase:** Phase 1 (Data Model Isolation).

3. **CLI Subprocess Blocking Event Loop** — Using synchronous `subprocess.run()` to spawn Claude CLI blocks FastAPI's async event loop, freezing all WebSocket connections for 30-60 seconds. All users' connections hang, no heartbeats, proxies timeout. **Prevention:** Use `asyncio.create_subprocess_exec()` with `stdout.readline()` streaming. Keep process reference to prevent GC from killing child. Set Windows ProactorEventLoop. Add `await websocket.drain()` after sends. Set 5-10 min timeout. **Detection:** All WebSockets hang during one Assistant message. CPU spike on single core. **Phase:** Phase 1 (Async Subprocess Infrastructure).

4. **GoRouter Navigation Context Conflicts** — User switches from BA to Assistant tab, app crashes with `currentConfiguration.isNotEmpty: You have popped the last page off of the stack`. Or deep link `/assistant/:id` opens in BA project context. Caused by mixing `Navigator.push()` (old code) with `GoRouter.go()` (new code), or simultaneous navigation events in StatefulShellRoute. **Prevention:** Remove ALL `Navigator` calls, use only `GoRouter`. Prefer `context.go()` over `context.push()`. Separate navigator keys per branch. Debounce tab changes (200ms). Add redirect validation for deep links. **Detection:** Navigation crashes, duplicate screens, URL doesn't match displayed screen. **Phase:** Phase 1 (Navigation Architecture).

5. **Shared Service State Leakage** — BA thread behavior leaks into Assistant threads (or reverse) because `ai_service.py` has shared tool definitions or message formatting logic with scattered conditionals. One missed `if` branch applies BA tools to Assistant. **Prevention:** Modular monolith—separate `ba_assistant/` and `assistant/` service modules. Each imports from shared `ai/` utilities but owns its own system prompt, tools, conversation formatting. API routes enforce mode: calling `/assistant/threads/{ba_thread_id}/chat` returns 403. **Detection:** Assistant threads call `save_artifact` tool. Logs show BA terminology in Assistant responses. **Phase:** Phase 1 (Service Extraction).

**Additional moderate pitfalls:**
- Forgetting to conditionally load MCP tools for CLI adapter (BA tools leak into Assistant)
- Not defaulting existing threads to `ba_assistant` in migration (null thread_type breaks enum parsing)
- Missing thread type in deep link routes (`/assistant/:id` not registered)
- Hardcoding thread type in creation dialog (can't create Assistant threads)
- No subprocess timeout on CLI calls (infinite hangs, resource exhaustion)

## Implications for Roadmap

The roadmap MUST enforce foundation-first architecture. Attempting to "ship faster" by building Assistant UI before service separation guarantees technical debt requiring rewrites. The critical path is: database schema → service separation → API validation → frontend UI.

### Suggested Phase Structure (6 Phases)

Based on research findings, recommend this phase order with explicit dependency enforcement:

### Phase 1: Foundation — Data Model & Service Separation
**Rationale:** Database schema and service architecture must exist before any Assistant features can be safely implemented. This phase prevents all five critical pitfalls by establishing clean boundaries.

**Delivers:**
- Thread model with `thread_type` enum field (BA_ASSISTANT | ASSISTANT)
- Alembic migration adding field with default=ba_assistant (backward compatible)
- Service layer split: `ai_service.py` → `ba_assistant/ba_service.py` + `assistant/assistant_service.py` + `ai/` shared utilities
- Document model with `scope` enum (BA_PROJECT | ASSISTANT_THREAD) and `context_id` field (if document upload in scope)
- Zero `if thread_type` conditionals in service files (verified via grep)

**Addresses (Features):**
- Foundation for thread type discrimination
- Prevents system prompt leakage
- Prevents document cross-contamination

**Avoids (Pitfalls):**
- Pitfall 1: System prompt injection (service separation prevents shared state)
- Pitfall 2: Document ownership isolation failure (scope enum enforced at schema level)
- Pitfall 5: Shared service state leakage (separate service files with no conditionals)

**Verification:**
- Migration applied to test database, existing threads have type=ba_assistant
- `grep -r "if.*thread.*type" backend/app/services/ba_assistant backend/app/services/assistant` returns zero hits
- BA service and Assistant service share no logic except through `ai/` imports

---

### Phase 2: Backend API — Thread Type Routing & Validation
**Rationale:** API layer must enforce thread type before frontend can safely create Assistant threads. Route validation prevents mode spoofing and ensures services receive correct thread types.

**Delivers:**
- Thread creation endpoints support `thread_type` parameter
- Thread listing endpoint supports `?thread_type=assistant` filter
- Conversation endpoint validates thread.type matches expected service (403 on mismatch)
- Conditional MCP tool loading in CLI adapter (no BA tools for Assistant)
- System prompt selection based on thread type in service layer

**Addresses (Features):**
- Thread creation with type=assistant
- Thread listing filtered by type
- API validation layer for mode enforcement

**Avoids (Pitfalls):**
- Pitfall 4 (partial): API validates thread type before service routing
- Moderate pitfall: Allowing project_id for Assistant threads (validation rejects)

**Verification:**
- Create BA thread, call `/api/threads/{id}/chat` → success
- Create Assistant thread with project_id → 400 error (validation rejects)
- Call `/api/threads?thread_type=assistant` → returns only Assistant threads

---

### Phase 3: Async Infrastructure — CLI Subprocess Management
**Rationale:** CLI subprocess must be implemented correctly before integrating into Assistant service. Blocking subprocess calls freeze the entire application—this cannot be retrofitted after launch.

**Delivers:**
- Async subprocess utility using `asyncio.create_subprocess_exec()`
- Streaming via `stdout.readline()` with backpressure handling
- Process lifecycle management (timeout after 5-10 min, cleanup on exit)
- Windows ProactorEventLoop configuration
- WebSocket integration with `drain()` calls
- Process pool limits (max 10 concurrent CLI processes via semaphore)

**Addresses (Features):**
- SSE streaming for Assistant responses
- CLI backend integration without event loop blocking

**Avoids (Pitfalls):**
- Pitfall 3: CLI subprocess blocking event loop (async implementation with safeguards)
- Moderate pitfall: No subprocess timeout (wrapped in `asyncio.wait_for()`)
- Moderate pitfall: Missing WebSocket drain (flush buffer after each send)

**Verification:**
- Stress test: 10 concurrent CLI calls, event loop never blocks >100ms
- Send Assistant message, verify heartbeats continue during 30s CLI processing
- Kill server mid-stream, verify no zombie `claude` processes (`ps aux | grep claude`)

---

### Phase 4: Frontend Navigation — GoRouter Architecture
**Rationale:** Navigation structure must be correct before building Assistant UI. GoRouter StatefulShellRoute conflicts are difficult to debug and impossible to fix after screens are built.

**Delivers:**
- 5-branch StatefulShellRoute configuration (add Assistant branch at index 1)
- Separate navigator keys for each branch (prevent stack pollution)
- Deep link routes for `/assistant/:id`
- Remove ALL `Navigator` calls, replace with `GoRouter`
- Debounced tab change handler (200ms)
- Redirect validation for deep links (check thread type matches route)

**Addresses (Features):**
- Assistant navigation entry point
- Deep linking to Assistant threads
- Navigation state preservation across mode switches

**Avoids (Pitfalls):**
- Pitfall 4: GoRouter navigation context conflicts (full GoRouter migration, no Navigator mixing)
- Minor pitfall: Missing thread type in deep link routes (registered in config)

**Verification:**
- `grep -r "Navigator\." frontend/lib` returns zero hits (only GoRouter calls)
- Deep link to `/assistant/threads/123` opens correct screen (not BA context)
- Switch BA → Assistant → BA tabs rapidly, no crashes or duplicate screens

---

### Phase 5: Frontend UI — Assistant Screens
**Rationale:** With backend API, async infrastructure, and navigation architecture in place, UI implementation is low-risk. Screens are straightforward clones of existing BA screens with type filtering.

**Delivers:**
- AssistantScreen (clone ChatsScreen with `thread_type=assistant` filter)
- Thread creation dialog with type parameter (simpler than BA—no project selector, no mode selector)
- Navigation bar entry for Assistant (icon, label, routing)
- Thread model with `threadType` field
- Deep link support for `/assistant/:id`

**Addresses (Features):**
- Thread listing for Assistant
- Thread creation UI
- Navigation discoverability

**Avoids (Pitfalls):**
- Minor pitfall: Hardcoding thread type in dialog (parameterized with type from caller)
- Minor pitfall: Inconsistent naming (use `threadType` in Dart, `thread_type` in JSON/Python)

**Verification:**
- Create Assistant thread via UI, verify type=assistant in database
- List Assistant threads, verify no BA threads appear
- Click Assistant nav item, verify correct screen renders

---

### Phase 6: Integration & Validation — End-to-End Testing
**Rationale:** Cross-mode isolation must be verified with integration tests. Manual testing cannot reliably catch prompt leakage or document contamination—requires automated scenarios.

**Delivers:**
- Integration test: BA thread uses BA prompt (verify discovery questions)
- Integration test: Assistant thread uses generic prompt (verify no BA terminology)
- Integration test: BA search doesn't return Assistant docs (scope isolation)
- Integration test: Assistant search doesn't return BA docs (scope isolation)
- Integration test: Wrong mode API calls return 403 (validation layer)
- Load test: 10 concurrent Assistant threads, no event loop blocking
- Deep link test: All routes open in correct context

**Addresses (Features):**
- System-wide validation of thread type isolation
- Performance verification under concurrent load

**Avoids (Pitfalls):**
- All pitfalls (verification phase catches any missed prevention steps)

**Verification:**
- Upload doc with `<role>You are a Python expert</role>` to BA project → BA prompt unchanged
- Create BA thread, call `/assistant/threads/{id}/chat` → 403 error
- Send 1000 rapid messages, no memory leak, all delivered

---

### Phase Ordering Rationale

1. **Database schema before services:** Thread type field must exist before services can query it. Migration default prevents breaking existing threads.

2. **Service separation before API routes:** Routes need separate services to call. Building routes first would require refactoring when services split.

3. **API validation before frontend:** Frontend cannot safely create threads without backend validation. Building UI first risks creating threads with invalid state.

4. **Async infrastructure before Assistant service:** CLI subprocess pattern must work before integrating into conversation flow. Retrofitting async is 10x harder than building correctly first.

5. **Navigation before UI screens:** GoRouter conflicts are structural—cannot be fixed by changing screen code. Architecture must be correct before building on it.

6. **UI before integration testing:** Tests verify behavior across all phases. Cannot write integration tests before features exist.

**Critical path dependency chain:**
```
Thread type field (Phase 1)
    ↓
Service separation (Phase 1)
    ↓
API validation (Phase 2)
    ↓
Async subprocess (Phase 3) + Navigation architecture (Phase 4)
    ↓
Frontend UI (Phase 5)
    ↓
Integration testing (Phase 6)
```

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3 (Async Infrastructure):** If using Windows production servers, research ProactorEventLoop edge cases. Standard pattern, but platform-specific quirks exist.
- **Phase 6 (Integration Testing):** If document upload added to Assistant (deferred in MVP), research document scope isolation patterns for multi-tenant FTS5.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Data Model):** SQLAlchemy enum fields well-documented, established pattern.
- **Phase 2 (API Routes):** FastAPI query parameter validation standard practice.
- **Phase 4 (Navigation):** GoRouter StatefulShellRoute documented, project already uses pattern.
- **Phase 5 (Frontend UI):** Cloning existing screens, no novel patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | No new dependencies required. FastAPI/SQLAlchemy version updates optional. Existing stack validated for dual-mode architecture. |
| Features | **HIGH** | Feature set derived from existing BA Assistant with clear anti-features identified. Table stakes vs differentiators well-defined. |
| Architecture | **HIGH** | Modular monolith with service separation is proven pattern. Thread type discrimination matches existing `model_provider` field pattern. Research synthesizes multi-tenant isolation, agent state management, and async subprocess patterns from 30+ authoritative sources. |
| Pitfalls | **HIGH** | All five critical pitfalls documented with prevention, detection, and recovery strategies. Synthesized from OWASP Gen AI Security, FastAPI WebSocket docs, Flutter GoRouter issues, and monolith refactoring guidance. Phase-to-pitfall mapping ensures roadmap addresses risks. |

**Overall confidence:** **HIGH**

This is not a greenfield project requiring novel solutions. It's a refactoring task applying established patterns (service separation, enum discriminators, async subprocess, GoRouter StatefulShellRoute) to existing infrastructure. The research identifies where shortcuts fail (shared service with conditionals, nullable project_id, blocking subprocess) and prescribes preventive architecture. High confidence in roadmap validity if foundation phases execute before UI work.

### Gaps to Address

**Minor gaps requiring validation during implementation:**

1. **Document upload for Assistant (deferred):** If added in Phase 2+, validate FTS5 scope isolation performance with 10k+ documents. Research recommends separate virtual tables (`documents_ba_fts`, `documents_assistant_fts`) but this adds infrastructure complexity. Test shared FTS with `scope` WHERE clause first; partition only if slow.

2. **CLI subprocess platform compatibility:** Research covers Linux/Mac (primary) and Windows (ProactorEventLoop), but doesn't address exotic platforms. If deploying to BSD or Android, validate `asyncio.create_subprocess_exec()` support during Phase 3.

3. **Token budget enforcement across modes:** BA threads have conversation context (messages + documents + system prompt). Assistant threads have lighter context (messages + minimal prompt). Research doesn't specify if token limits should differ by mode. Validate during Phase 6 load testing—may need per-mode token budgets.

4. **Deep link handling for deleted threads:** Research covers deep links for valid threads but doesn't specify 404 vs redirect behavior when thread deleted. Decision needed: show error page or redirect to Assistant thread list? Trivial gap, resolve during Phase 5 UI implementation.

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) — v0.129.0 (2026-02-12), Python 3.14 support
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) — Async session patterns
- [Python Asyncio Subprocess](https://docs.python.org/3/library/asyncio-subprocess.html) — Async subprocess management
- [GoRouter pub.dev](https://pub.dev/packages/go_router) — v17.0.1, StatefulShellRoute documentation
- [Provider pub.dev](https://pub.dev/packages/provider) — v6.1.5, state management patterns

**OWASP Security Guidance:**
- [LLM01:2025 Prompt Injection - OWASP Gen AI Security](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — System prompt isolation patterns
- [LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) — Context firewalls, untrusted input markers
- [Multi-Tenant Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html) — Row-level isolation strategies

**Microsoft Agent Framework:**
- [Agent Framework Workflows - State Isolation](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/state-isolation) — Agent state boundaries
- [Agent Framework Workflows - Shared States](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/shared-states) — Multi-agent architectures

### Secondary (MEDIUM confidence)

**Multi-Tenant Isolation Patterns:**
- [Multi-Tenant Deployment: 2026 Complete Guide](https://qrvey.com/blog/multi-tenant-deployment/) — Shared schema with discriminators
- [Tenant Isolation in Multi-Tenant Systems](https://workos.com/blog/tenant-isolation-in-multi-tenant-systems) — Data isolation best practices
- [FastAPI Multi-Tenancy Class Based Solution](https://sayanc20002.medium.com/fastapi-multi-tenancy-bf7c387d07b0) — Row-level isolation with shared tables

**Flutter Navigation:**
- [Flutter Bottom Navigation with GoRouter](https://codewithandrea.com/articles/flutter-bottom-navigation-bar-nested-routes-gorouter/) — StatefulShellRoute patterns
- [Flutter Navigation: Go vs Push](https://codewithandrea.com/articles/flutter-navigation-gorouter-go-vs-push/) — Best practices for programmatic navigation
- GitHub Flutter Issues: #142678 (Navigator.pop stack corruption), #160504 (simultaneous navigation), #154759 (context.push duplication), #134373 (deep linking conflicts)

**Python Async WebSocket:**
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) — Official WebSocket documentation
- [Getting Started with FastAPI WebSockets](https://betterstack.com/community/guides/scaling-python/fastapi-websockets/) — Backpressure handling
- [Python WebSocket Real-Time Communication Patterns](https://dasroot.net/posts/2026/02/python-websocket-servers-real-time-communication-patterns/) — Production patterns

**Monolith Refactoring:**
- [Refactoring Monoliths to Microservices](https://microservices.io/refactoring/) — Martin Fowler strangler fig pattern
- [How to Break a Monolith into Microservices](https://martinfowler.com/articles/break-monolith-into-microservices.html) — Service extraction strategies
- [AWS Decomposing Monoliths](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/) — Modular monolith approach

### Tertiary (LOW confidence)

**AI UX Patterns:**
- [AI UI Patterns](https://www.patterns.dev/react/ai-ui-patterns/) — Multi-mode switching, agent cards
- [AI UX Patterns 2026](https://nurxmedov.substack.com/p/ai-ux-patterns-in-2026-from-assistants) — Agentic design trends
- [Conversational UI Best Practices](https://research.aimultiple.com/conversational-ui/) — Separation of work vs personal contexts

**Community Resources:**
- [SQLAlchemy Enum Best Practices 2026](https://copyprogramming.com/howto/access-enum-value-from-a-database-record-in-python-sqlalchemy) — Enum filtering patterns
- [Flutter State Management in 2026](https://foresightmobile.com/blog/best-flutter-state-management) — Provider vs Riverpod trade-offs
- [Best AI Coding CLI 2026](https://www.xugj520.cn/en/archives/best-ai-coding-cli-2026-guide.html) — CLI chat interface patterns

---

*Research completed: 2026-02-17*
*Ready for roadmap: YES*
*Next step: Requirements definition with phase-specific task breakdown*
