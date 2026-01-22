---
phase: 03-ai-powered-conversations
plan: 01
subsystem: api
tags: [claude, anthropic, sse, streaming, ai, tool-use]

# Dependency graph
requires:
  - phase: 02-data-foundation
    provides: Thread and Message models, document_search service
provides:
  - AIService class with Claude integration and tool use
  - Conversation service for message persistence
  - SSE streaming chat endpoint POST /threads/{thread_id}/chat
  - SYSTEM_PROMPT for proactive BA assistant behavior
  - DOCUMENT_SEARCH_TOOL for autonomous document search
affects: [03-02 frontend chat ui, 03-03 token tracking, artifact generation]

# Tech tracking
tech-stack:
  added: [sse-starlette]
  patterns: [SSE streaming, tool use loop, async generator for events]

key-files:
  created:
    - backend/app/services/ai_service.py
    - backend/app/services/conversation_service.py
    - backend/app/routes/conversations.py
  modified:
    - backend/requirements.txt
    - backend/main.py

key-decisions:
  - "Claude claude-sonnet-4-5-20250514 model for responses"
  - "150k token context window limit with 80% budget for messages"
  - "Token estimation: 1 token ~= 4 characters"
  - "Message truncation keeps recent messages, prepends system note"
  - "Tool results formatted with markdown bold for document names"

patterns-established:
  - "SSE event types: text_delta, tool_executing, message_complete, error"
  - "Tool execution loop: stream until tool_use stop_reason, execute, continue"
  - "validate_thread_access helper for ownership verification"
  - "Conversation context built from database, not passed from client"

# Metrics
duration: 18min
completed: 2026-01-22
---

# Phase 3 Plan 01: Backend AI Service Summary

**Claude integration with AsyncAnthropic client, SSE streaming chat endpoint, and autonomous document search tool**

## Performance

- **Duration:** 18 min
- **Started:** 2026-01-22T07:20:00Z
- **Completed:** 2026-01-22T07:38:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- AIService class with streaming chat and tool execution loop
- SYSTEM_PROMPT defining proactive BA assistant behavior
- DOCUMENT_SEARCH_TOOL enabling AI to autonomously search project documents
- Conversation service with message persistence and token-aware truncation
- POST /threads/{thread_id}/chat SSE endpoint with proper auth

## Task Commits

Each task was committed atomically:

1. **Task 1: Install sse-starlette and create AI service** - `bb686f0` (feat)
2. **Task 2: Create conversation service for message persistence** - `5569be7` (feat)
3. **Task 3: Create SSE streaming chat endpoint** - `e1217e5` (feat)

## Files Created/Modified
- `backend/requirements.txt` - Added sse-starlette>=2.0.0 dependency
- `backend/app/services/ai_service.py` - AIService class with Claude integration
- `backend/app/services/conversation_service.py` - Message persistence and context building
- `backend/app/routes/conversations.py` - SSE streaming chat endpoint
- `backend/main.py` - Registered conversations router

## Decisions Made
- **Model selection:** Using claude-sonnet-4-5-20250514 for balance of capability and cost
- **Token estimation:** Using 1 token ~= 4 characters heuristic for budget tracking
- **Context budget:** 150k tokens max with 80% for messages, 20% buffer for response
- **Truncation strategy:** Keep recent messages, prepend system note about truncated history
- **Tool result formatting:** Markdown bold for filenames, cleaned HTML markers from snippets

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed without issues.

## User Setup Required

**External services require manual configuration:**
- `ANTHROPIC_API_KEY` environment variable must be set for AI features
- Get API key from: Anthropic Console -> API Keys -> Create key

## Next Phase Readiness

**Ready for Plan 02 (Frontend Chat UI):**
- SSE endpoint returns text_delta events for streaming display
- message_complete event includes usage stats for token tracking
- Thread ownership validation prevents unauthorized access
- Messages persisted to database automatically

**Pending for Plan 02:**
- Token usage tracking (TODO in conversations.py)
- Thread title/summary generation (TODO in conversations.py)

---
*Phase: 03-ai-powered-conversations*
*Completed: 2026-01-22*
