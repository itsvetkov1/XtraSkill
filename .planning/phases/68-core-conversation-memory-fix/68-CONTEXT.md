# Phase 68: Core Conversation Memory Fix - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the CLI adapter to send full conversation history instead of just the last message. Replace `_convert_messages_to_prompt()` in `claude_cli_adapter.py` with proper multi-turn formatting, then verify with backend and frontend tests. BA flow (agent_service.py) is unchanged.

</domain>

<decisions>
## Implementation Decisions

### Message Formatting
- Role labels: `Human:` / `Assistant:` (Anthropic's native conversation format)
- Delimiter between messages: `---` separator line between each turn
- Multi-part content: Keep text blocks, replace tool_use with annotated summary like `[searched documents]` or `[performed an action]`
- Thinking blocks: Exclude — only include final response text, not internal reasoning

### History Scope
- Include user and assistant messages only — exclude system messages and internal tool messages
- Reuse existing `ConversationService.build_conversation_context()` for history loading (shared logic, already handles truncation)
- Empty assistant messages (tool_use only, no text): Skip entirely — don't include in formatted history
- Document search results: Replace with brief reference annotations like `[referenced: filename.txt]` instead of full content

### Test Strategy
- Backend: Mocked subprocess for unit tests + one real integration test (spawns actual Claude CLI, costs API tokens)
- Integration test acceptance: Fact recall — casually mention a fact in turn 1 (e.g., "we're building a FastAPI app"), ask about it in turn 3. Do NOT explicitly say "remember this" to avoid triggering memory.md storage
- Thread type coverage: Assistant threads only — BA uses agent_service.py which is unmodified
- Frontend: Full AssistantConversationProvider test coverage — message list integrity, streaming state, error handling, retry with history

### Claude's Discretion
- Exact annotation text for tool_use summaries
- Error behavior when formatting fails (research suggests this is low-risk given proven pattern)
- Specific test fixture data and assertion style

</decisions>

<specifics>
## Specific Ideas

- Copy the proven formatting pattern from `agent_service.py` (lines 103-120) into `claude_cli_adapter.py`
- Research confirms Approach A (Full History via stdin) — single-file change, HIGH confidence
- Integration test must avoid explicit "remember this" phrasing — Claude Code stores explicitly requested memories in memory.md, which would make the test pass for wrong reasons

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 68-core-conversation-memory-fix*
*Context gathered: 2026-02-19*
