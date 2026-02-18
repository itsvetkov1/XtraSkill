# Phase 62: Backend Foundation - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend fully supports thread_type discrimination — data model, service logic, and API endpoints all enforce clean separation between BA Assistant and Assistant threads. No frontend screens or navigation — only the minimal frontend fix to send thread_type on existing BA thread creation.

</domain>

<decisions>
## Implementation Decisions

### Assistant behavior
- No system prompt for Assistant threads — user messages go directly to the LLM with no instructions
- Hardcoded to claude-code-cli adapter — no override or provider selection possible for Assistant threads
- Full conversation history — all prior messages in the thread sent as context (same as BA threads)
- Include thinking/reasoning indicators during streaming — consistent with BA mode experience

### API defaults
- thread_type is **required** on thread creation — no default, all callers must be explicit
- Fix existing frontend BA thread creation to send `thread_type=ba_assistant` in this phase (prevents breakage)
- Listing threads without filter returns **all threads** regardless of type (backward compatible)
- thread_type field **always included** in all thread API responses (list, get, create)

### Document scope
- Documents in Assistant mode are **thread-scoped** — belong to a specific thread, only visible within that thread's conversation
- **Expanded file types** beyond BA mode: images (PNG, JPG, GIF) and spreadsheets (CSV, XLSX) in addition to existing types
- **Higher file size limit** for Assistant threads compared to BA mode (exact limit at Claude's discretion based on CLI adapter constraints)

### Error responses
- Invalid thread_type: HTTP 400 with message listing valid options ("Invalid thread_type. Must be 'ba_assistant' or 'assistant'")
- Assistant thread with project_id: **silently ignore** the project_id — create thread without project, no error
- Invalid thread_type enum: HTTP 400 with clear valid options
- AI generation errors: same error handling as BA mode — reuse existing patterns
- **Separate usage tracking** per thread_type for future analytics

### Claude's Discretion
- Exact file size limit for Assistant uploads (based on CLI adapter constraints)
- Migration implementation approach (Alembic vs manual SQL)
- Usage tracking implementation details (counters, storage)
- How to structure the thread_type enum in the codebase

</decisions>

<specifics>
## Specific Ideas

- thread_type pattern should match the existing model_provider field pattern (enum discriminator on the thread model)
- No service file duplication — conditional logic in ai_service.py based on thread_type, shared LLM adapters
- The "silently ignore project_id" behavior means the API is forgiving rather than strict — user experience over correctness

</specifics>

<deferred>
## Deferred Ideas

- Expanded file type support for BA mode — keep BA types unchanged, only Assistant gets new types
- Per-thread adapter override for Assistant mode — currently hardcoded to CLI, future flexibility deferred (CUST-02)
- Custom system prompts for Assistant mode — deferred to CUST-01

</deferred>

---

*Phase: 62-backend-foundation*
*Context gathered: 2026-02-17*
