# Phase 41: Structural History Filtering - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Fulfilled artifact requests are structurally removed from the AI model's conversation context so the model never sees completed generation requests. Messages remain in the database and visible in the chat UI — filtering is purely an internal processing step before context is sent to the model.

</domain>

<decisions>
## Implementation Decisions

### Filtering strategy
- **Remove, don't annotate** — fulfilled artifact request pairs (user message + assistant response) are excluded from the conversation context sent to the model, rather than being marked with annotations
- The model never sees fulfilled requests, eliminating the possibility of re-execution entirely

### What gets filtered
- Both the user message that triggered artifact generation AND the assistant response that contained the generation are removed from context
- All fulfilled requests in the entire conversation history are filtered, not just recent ones

### When filtering happens
- Filtering is applied at **read time** (when building conversation context for the model), not at save time
- Original messages remain untouched in the database
- The chat UI displays the full conversation history normally — filtering is invisible to the user

### Detection of fulfilled requests
- Must determine which message pairs resulted in successful artifact generation
- CRITICAL: The `ARTIFACT_CREATED:` marker from BUG-019 is dead code — must use an alternative detection strategy (tool results or database artifact records)

### User visibility
- No visual indication in the UI that messages have been filtered from context
- Filtering is purely an internal optimization — completely invisible to the user

### Claude's Discretion
- Exact detection mechanism for identifying fulfilled artifact requests (tool results vs database lookup)
- How to handle edge cases (partial failures, retries)
- Implementation approach for the filtering logic within conversation_service.py

</decisions>

<specifics>
## Specific Ideas

- User explicitly wants fulfilled generation messages OUT of context, not just annotated — "it doesn't input any value and there is no reason to be kept [in context]"
- This is a stronger approach than the original annotation plan — complete removal vs. marking

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 41-structural-history-filtering*
*Context gathered: 2026-02-05*
