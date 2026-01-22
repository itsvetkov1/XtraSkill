---
phase: 03-ai-powered-conversations
plan: 02
subsystem: api
tags: [token-tracking, cost-monitoring, summarization, budget-enforcement]

# Dependency graph
requires:
  - phase: 03-ai-powered-conversations
    plan: 01
    provides: conversations.py with SSE chat endpoint, ai_service.py with MODEL constant
provides:
  - Token tracking service with cost calculation and budget enforcement
  - Thread summarization service with AI-generated titles
  - Chat endpoint with budget check and token tracking integration
affects: [03-03 frontend chat UI, cost monitoring dashboard, usage analytics]

# Tech tracking
tech-stack:
  added: []
  patterns: [monthly budget aggregation, interval-based summarization, pricing configuration]

key-files:
  created:
    - backend/app/services/token_tracking.py
    - backend/app/services/summarization_service.py
  modified:
    - backend/app/routes/conversations.py

key-decisions:
  - "Claude pricing: $3/1M input, $15/1M output tokens"
  - "Default monthly budget: $50 per user"
  - "Summary interval: every 5 messages"
  - "Max title length: 100 characters"
  - "Budget enforcement via 429 Too Many Requests"

patterns-established:
  - "calculate_cost function for token-to-dollar conversion"
  - "get_monthly_usage aggregates current month spending"
  - "maybe_update_summary triggers at modulo intervals (5, 10, 15...)"
  - "Summarization uses same Claude model for simplicity"

# Metrics
duration: 3min
completed: 2026-01-22
---

# Phase 3 Plan 02: Token Tracking and Summarization Summary

**Token usage tracking with cost calculation, monthly budget enforcement, and AI-generated thread titles every 5 messages**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-22T05:29:44Z
- **Completed:** 2026-01-22T05:32:06Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Token tracking service with Claude pricing ($3/1M input, $15/1M output)
- Monthly budget enforcement with $50 default limit
- Thread summarization service generating titles every 5 messages
- Chat endpoint now checks budget and tracks usage automatically

## Task Commits

Each task was committed atomically:

1. **Task 1: Create token tracking service** - `0d69615` (feat)
2. **Task 2: Create thread summarization service** - `9916871` (feat)
3. **Task 3: Wire token tracking and summarization into chat endpoint** - `780ba7b` (feat)

## Files Created/Modified
- `backend/app/services/token_tracking.py` - Token usage tracking and budget enforcement
- `backend/app/services/summarization_service.py` - AI-generated thread titles
- `backend/app/routes/conversations.py` - Integrated budget check, token tracking, and summarization

## Decisions Made
- **Claude pricing model:** Using official Jan 2026 pricing ($3/1M input, $15/1M output)
- **Budget enforcement:** $50/month default, checked before each chat request
- **Summary trigger:** Every 5 messages (at 5, 10, 15...) to balance cost vs freshness
- **Title length:** Max 100 characters for UI compatibility
- **Error handling:** Summarization failures logged but don't fail the main request

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed without issues.

## Technical Details

### Token Tracking Service
- `calculate_cost(model, input_tokens, output_tokens)` - Convert tokens to USD
- `track_token_usage(db, user_id, model, input, output, endpoint)` - Persist to TokenUsage table
- `get_monthly_usage(db, user_id)` - Aggregate current month's spend
- `check_user_budget(db, user_id)` - Returns True if within budget

### Summarization Service
- `format_messages_for_summary(messages)` - Truncate messages for prompt
- `generate_thread_summary(client, messages, current_title)` - Get new title from Claude
- `maybe_update_summary(db, thread_id, user_id)` - Conditional update at intervals

### Chat Endpoint Integration
- Budget check at request start (returns 429 if exceeded)
- Token tracking after successful response
- Summary update triggered after message save

## Requirements Delivered
- **AI-07 (partial):** Token usage is recorded after each AI response
- **CONV-06 (partial):** Thread title updates automatically after 5 messages

## Next Phase Readiness

**Ready for Plan 03 (Frontend Chat UI):**
- Token usage tracked in database
- Thread titles auto-update
- Budget enforcement prevents cost explosion

**Frontend considerations:**
- Handle 429 response for budget exceeded
- Show updated thread title after API refresh
- Display token usage stats from message_complete event

---
*Phase: 03-ai-powered-conversations*
*Completed: 2026-01-22*
