# Phase 20: database-api - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Thread model stores provider information and backend handles extended thinking timeouts. Adding `model_provider` column to threads and implementing SSE heartbeats to prevent connection drops during long thinking periods.

</domain>

<decisions>
## Implementation Decisions

### Heartbeat behavior
- Use SSE comment format (`: heartbeat\n\n`) — invisible to clients, just keeps connection alive
- Send heartbeats every 15 seconds during silence
- Only send heartbeats when no data sent for threshold period — not continuously throughout streaming

### Timeout thresholds
- Heartbeats start after 5 seconds of silence (first heartbeat at 5s, then every 15s)
- Maximum total wait time: 10 minutes (allows DeepSeek reasoning which can take 5+ min)
- Timeout resets when any partial data arrives — 10-min is for silence only
- On timeout: send SSE error event with timeout message (consistent with other errors)

### Claude's Discretion
- Provider storage column type and default value
- Thread creation API changes for provider parameter
- Migration strategy for existing threads (default to 'anthropic')
- Validation and error responses for invalid providers

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for database migration and API changes.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 20-database-api*
*Context gathered: 2026-01-31*
