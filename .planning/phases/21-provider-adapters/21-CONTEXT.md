# Phase 21: Provider Adapters - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement Gemini and DeepSeek adapters with provider-specific handling. Each adapter normalizes responses to StreamChunk format. Backend handles all provider differences — frontend treats all providers identically.

</domain>

<decisions>
## Implementation Decisions

### Error handling
- Show full error details to user: provider name + specific error code/message (e.g., "DeepSeek rate limit exceeded (429)")
- Authentication/API key errors get special handling — should prompt user to check settings or indicate provider is misconfigured
- Malformed or unexpected responses fail gracefully: show "Response could not be processed" and log details for debugging
- Streaming errors abort immediately — clear any partial content and show only the error message

### Thinking output
- Hide thinking/reasoning output from users for all providers (Gemini thinking, DeepSeek reasoning_content)
- Claude does not currently use extended thinking
- Skip thinking UI for v1.8 — basic multi-provider is the focus, thinking visibility is a future phase
- Claude's discretion on whether to store thinking content in database

### Model selection
- Gemini: `gemini-3-flash-preview` with heavy thinking mode
- DeepSeek: `deepseek-reasoner` (R1 reasoning model)
- Fixed model per provider — users choose provider, not specific model within provider
- Model names configurable via environment variables (GEMINI_MODEL, DEEPSEEK_MODEL) for deployment flexibility

### Retry behavior
- Simple retry strategy: 2 retries (3 total attempts) with fixed delay
- Same retry treatment for rate limits and server errors (no differentiation)
- No cross-provider fallback — each conversation stays bound to its provider
- User must create new conversation to use different provider if current one fails

### Claude's Discretion
- Fixed delay duration between retries
- Whether to store thinking content in database
- Specific error message formatting details
- Logging implementation for debugging

</decisions>

<specifics>
## Specific Ideas

- Errors should be informative: "DeepSeek rate limit exceeded (429)" not generic "service unavailable"
- Auth errors are special — they indicate configuration problems, not transient failures
- Keep it simple: no auto-fallback, no thinking UI, just working adapters

</specifics>

<deferred>
## Deferred Ideas

- Thinking/reasoning output visibility toggle — future phase after basic multi-provider works
- Model selection within providers (e.g., choosing between gemini models) — future enhancement
- Auto-fallback to another provider on failure — decided against for v1.8
- Extended thinking for Claude — not currently used, UI support deferred

</deferred>

---

*Phase: 21-provider-adapters*
*Context gathered: 2026-01-31*
