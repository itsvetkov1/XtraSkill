# Phase 58: Agent SDK Adapter - Context

**Gathered:** 2026-02-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement ClaudeAgentAdapter as a production-viable LLM provider using the Claude Agent SDK (Python). The adapter must integrate into the existing LLMAdapter pattern, translate SDK agent loop events into StreamChunk format for SSE streaming, and connect MCP tools (search_documents, save_artifact) with proper database/user context propagation. This is a backend-only phase — frontend integration is Phase 60.

</domain>

<decisions>
## Implementation Decisions

### Multi-turn streaming visibility
- Show tool activity indicators to user during agent execution (e.g., "Searching documents...")
- Show thinking indicator (not full thinking content) — match existing Claude thinking behavior
- Continuous stream across agent rounds — all text appends seamlessly into a single response, no visual segmentation between turns
- Source attribution chips must work identically to direct API — search_documents tool calls produce the same chip data

### Agent behavior & personality
- Use the current BA system prompt (identical to direct API adapter) for POC
- Deferred: Future goal is to leverage Claude Code skills (business-analyst skill) instead of system prompt
- SDK uses ANTHROPIC_API_KEY (API billing) — accepted for POC evaluation
- Both SDK and CLI adapters will be built as planned (SDK = API key, CLI = subscription)

### Timeout & failure policy
- No turn limit — POC is testing the frontier of agent capabilities, used only by controlled test group
- No request timeout — let the agent run as long as needed
- On failure: clean error only — discard partial output, show error with retry option
- Error messages include diagnostic info (which tool failed, which turn) — useful for POC debugging

### Tool context strategy
- Use proper HTTP-based MCP transport for context propagation — production-ready architecture, not shortcuts
- Tools enhanced for agent context — SDK tools can return richer results than direct API tools
- Proactive tool use allowed — agent decides when to search docs or save artifacts (this IS the agentic advantage being tested)
- Larger context windows for search results — give the agent more document context per search to test if more context = better output

### Claude's Discretion
- Exact MCP HTTP transport implementation approach (stdio vs SSE vs streamable HTTP)
- StreamChunk event vocabulary extensions needed for agent-specific events
- How to surface tool activity indicators through existing SSE format
- Enhanced search result format details (chunk sizes, metadata richness)

</decisions>

<specifics>
## Specific Ideas

- "The end goal is to make it use my skills (including business-analyst) but for now we want POC to see how this works in general"
- User wants to eventually use Claude subscription for Claude Code — CLI adapter (Phase 59) enables this, SDK must use API key
- POC is for controlled test group only — prioritize experimentation over production hardening
- Fair comparison matters but enhanced tools are fine — we're testing what the agent CAN do, not limiting it to match direct API

</specifics>

<deferred>
## Deferred Ideas

- Claude Code skills integration (business-analyst skill as system prompt replacement) — future phase after POC evaluation
- Subscription-based billing for SDK (if Anthropic adds subscription API access) — monitor
- Production hardening (turn limits, timeouts, rate limiting) — Phase 61 decision or post-experiment

</deferred>

---

*Phase: 58-agent-sdk-adapter*
*Context gathered: 2026-02-14*
