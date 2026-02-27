# ENH-012: Evaluate Direct API vs CLI Subprocess for Assistant Threads

**Priority:** High
**Status:** Open
**Component:** Backend / LLM Adapters / Architecture
**Source:** ASSISTANT_FLOW_REVIEW.md — ISSUE-05

---

## User Story

As a user having a conversation in assistant mode,
I want fast response times,
So that conversations feel responsive without unnecessary overhead.

---

## Problem

Assistant threads are hardcoded to use the Claude CLI subprocess path even when no agent capabilities (tools, file access, multi-step reasoning) are needed. For a simple skill-enhanced conversation:

- CLI subprocess spawns a Node.js process: **120–400ms cold start overhead**
- The process pool (`POOL_SIZE = 2`) is documented as "sufficient for single-user dev"
- With 2 concurrent users, both hit cold spawns frequently
- The CLI provides no advantage when the assistant doesn't use tools (LOGIC-02 disables tools for assistant threads)

### The Trade-off

| Path | Latency | Tools | Multi-step | Complexity |
|------|---------|-------|------------|------------|
| CLI subprocess | 120-400ms + API time | Yes (full agent loop) | Yes | High (process mgmt) |
| Direct Anthropic API | API time only | Yes (manual tool loop) | Requires implementation | Medium |
| Claude Agent SDK | API time only | Yes (SDK tool loop) | Yes (built-in) | Low (SDK handles it) |

If skills don't need the agent loop, the direct API with the skill's system prompt is simpler and faster. If they do need agent capabilities, the Agent SDK (already used for BA assistant via `ClaudeAgentAdapter`) is a better choice than raw CLI subprocess.

---

## Acceptance Criteria

### Decision Phase
- [ ] Document which assistant thread use cases require agent capabilities (tool use, multi-step)
- [ ] Document which use cases are simple chat with a system prompt (no tools)
- [ ] Make an explicit architectural decision: CLI, Direct API, or Agent SDK for assistant threads

### Implementation (after decision)
- [ ] If Direct API: Route assistant threads through existing Anthropic adapter with skill system prompt
- [ ] If Agent SDK: Route assistant threads through ClaudeAgentAdapter with skill system prompt
- [ ] If CLI kept: Document the rationale and optimize the process pool for multi-user scenarios
- [ ] Response latency measurably improves for simple conversations (target: <200ms overhead removed)

---

## Technical References

- `backend/app/services/ai_service.py:931` — Thread type routing logic
- `backend/app/services/llm/claude_cli_adapter.py` — Current CLI subprocess path
- `backend/app/services/llm/claude_agent_adapter.py` — Agent SDK path (used by BA assistant)
- `backend/app/services/llm/anthropic_adapter.py` — Direct API path
- `POOL_SIZE = 2` in `claude_cli_adapter.py`

---

## Related

- SKILL-002: Inject skill system prompt (must work regardless of adapter choice)
- BUG-027: Process pool backoff (relevant if CLI is kept)

---

*Created: 2026-02-25*
*Source: Architecture review — assistant flow performance*
