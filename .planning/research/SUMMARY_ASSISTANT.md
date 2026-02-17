# Research Summary: Assistant Integration

**Domain:** Dual-mode chat application (BA Assistant vs General Assistant)
**Researched:** 2026-02-17
**Overall confidence:** HIGH

## Executive Summary

Adding a standalone "Assistant" section to the existing BA Assistant app requires minimal architectural changes. The core insight is to introduce a `thread_type` discriminator field in the Thread model that controls system prompt and tool availability at the AI service layer.

The existing architecture is well-suited for this extension: the Thread model already uses a provider field (`model_provider`) and supports project-less threads (`project_id` nullable, `user_id` for direct ownership). The AI service already has conditional logic for agent vs direct API providers. This pattern extends cleanly to thread types.

**Key architectural decision:** Use the "Shared Database, Shared Schema" multi-tenancy pattern with a discriminator field, not separate tables or services. BA threads and Assistant threads coexist in the same `threads` table, differentiated by `thread_type` enum. The AI service routes to different system prompts and tool sets based on this field.

**Impact assessment:** LOW risk to existing BA functionality (backward compatible migration, no changes to BA prompt/tools). MEDIUM risk to AI service (core streaming logic modified, but well-isolated). Implementation is additive - existing components remain functional.

## Key Findings

**Stack:** No new dependencies required. Existing FastAPI + SQLAlchemy + Flutter stack supports this pattern natively. Alembic migration for schema change, Pydantic models for validation.

**Architecture:** Thread type discrimination at service layer. Single `AIService` with conditional prompt/tool selection. CLI adapter conditionally loads MCP servers. Project association determines document access.

**Critical pitfall:** Avoid global system prompt constant anti-pattern. System prompt must be selected at runtime based on thread type, not hardcoded in ai_service.py.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Backend Data Model (1-2 days)
   - **Addresses:** Database schema, thread type enum
   - **Avoids:** Pitfall #2 (storing type only in frontend state)
   - **Tasks:**
     1. Add `ThreadType` enum to models.py
     2. Add `thread_type` field to Thread model (default: `ba_assistant`)
     3. Create Alembic migration
     4. Run migration (backfills existing threads to `ba_assistant`)

### Phase 2: Backend AI Service Logic (2-3 days)
   - **Addresses:** System prompt selection, tool availability
   - **Avoids:** Pitfall #1 (global system prompt), Pitfall #3 (service duplication)
   - **Tasks:**
     1. Extract BA system prompt to named constant
     2. Create minimal Assistant system prompt
     3. Add `thread_type` parameter to `stream_chat()`
     4. Add conditional prompt selection logic
     5. Add conditional tool selection (BA tools vs none)
     6. Update CLI adapter for conditional MCP config

### Phase 3: Backend API Routes (1 day)
   - **Addresses:** Thread creation with type, type filtering
   - **Avoids:** Cross-contamination of thread types
   - **Tasks:**
     1. Accept `thread_type` in thread creation routes
     2. Add validation (BA threads need project, Assistant threads are project-less)
     3. Pass thread type from conversation route to AI service
     4. Add thread filtering by type in list endpoints

### Phase 4: Frontend Data Model (1 day)
   - **Addresses:** Thread type representation, serialization
   - **Avoids:** Type information loss on refresh
   - **Tasks:**
     1. Add `threadType` field to Thread model
     2. Update Thread.fromJson() to parse thread_type
     3. Add backward compatibility (default to 'ba_assistant' if missing)

### Phase 5: Frontend UI - Assistant Screen (2-3 days)
   - **Addresses:** Assistant thread list, creation, navigation
   - **Avoids:** UI duplication with ChatsScreen
   - **Tasks:**
     1. Create AssistantScreen (clone ChatsScreen structure)
     2. Filter threads by thread_type=assistant
     3. Update thread creation dialog with type selector
     4. Add Assistant nav item to ResponsiveScaffold
     5. Wire navigation routes

### Phase 6: Testing & Validation (2 days)
   - **Addresses:** Regression, integration, type isolation
   - **Avoids:** BA prompt leaking into Assistant threads
   - **Tasks:**
     1. Regression test: BA thread creation and chat
     2. New flow test: Assistant thread creation and chat
     3. Isolation test: Verify no BA prompts in Assistant responses
     4. Tool test: Verify no document search in Assistant threads
     5. Migration test: Verify existing threads work after upgrade

**Phase ordering rationale:**
- Data model first (backend schema must exist before APIs use it)
- AI service logic second (core behavior implementation)
- API routes third (expose new behavior to frontend)
- Frontend model fourth (consume new API fields)
- Frontend UI fifth (user-facing features)
- Testing last (validate integration)

**Research flags for phases:**
- **Phase 2 (AI Service):** Likely needs deeper research - CLI adapter MCP configuration is complex
- **Phase 5 (Frontend UI):** Unlikely to need research - cloning existing patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies, existing tools sufficient |
| Features | MEDIUM | Assistant feature set clear, but UX details need design |
| Architecture | HIGH | Thread type pattern well-established in similar systems |
| Pitfalls | HIGH | Anti-patterns identified from codebase analysis |

## Gaps to Address

**Areas where research was inconclusive:**
- Thread title generation: Should Assistant threads auto-title like BA threads?
- Provider selection: Should Assistant threads allow provider switching?
- Message retention: Should Assistant threads follow same artifact correlation logic?

**Topics needing phase-specific research later:**
- Phase 2: CLI adapter MCP configuration file format (currently in-memory)
- Phase 5: Conversation mode UI for Assistant threads (Meeting vs Document Refinement makes no sense)
- Phase 6: Token budget handling for Assistant threads (same budget pool as BA?)

---
*Research Summary for: Assistant Integration*
*Researched: 2026-02-17*
*Estimated effort: 9-13 days across 6 phases*
