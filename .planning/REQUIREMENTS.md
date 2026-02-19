# Requirements: BA Assistant — v3.1.1 Assistant Conversation Memory

**Defined:** 2026-02-19
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v3.1.1 Requirements

Requirements for v3.1.1 milestone. Each maps to roadmap phases.

### Conversation Memory

- [ ] **CONV-01**: CLI adapter sends full conversation history (all messages, not just last)
- [ ] **CONV-02**: Messages formatted with role labels (`[USER]`, `[ASSISTANT]`) matching BA flow pattern
- [ ] **CONV-03**: Role alternation validated before sending to CLI subprocess
- [ ] **CONV-04**: Multi-part content handled (text blocks, tool results)

### Token Management

- [ ] **TOKEN-01**: Assistant message filtering strips tool_use blocks to prevent document context duplication
- [ ] **TOKEN-02**: Token-aware truncation preserved for CLI adapter (existing 150K limit)
- [ ] **TOKEN-03**: Emergency truncation at 180K tokens with user-facing error message
- [ ] **TOKEN-04**: Linear token growth verified (not quadratic) across 20+ turn conversations with docs

### Performance

- [ ] **PERF-01**: Subprocess spawn latency measured and baselined
- [ ] **PERF-02**: Process pooling implemented for warm subprocess reuse
- [ ] **PERF-03**: Latency improvement documented (target: <200ms vs ~400ms cold start)

### Testing

- [ ] **TEST-01**: Backend unit tests for `_convert_messages_to_prompt()` with 1, 3, 10+ messages
- [ ] **TEST-02**: Backend unit tests for multi-part content handling (tool results)
- [ ] **TEST-03**: Backend regression tests verifying BA flow unchanged
- [ ] **TEST-04**: Frontend tests for AssistantConversationProvider message history handling
- [ ] **TEST-05**: Integration test: Assistant thread with 3+ turns preserves context

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Memory

- **MEM-01**: Conversation summarization for very long sessions (100+ turns)
- **MEM-02**: Memory across threads (cross-thread context recall)
- **MEM-03**: User-editable message history

### Conversation Features

- **FEAT-01**: Multiple conversation branches
- **FEAT-02**: Conversation search/indexing within thread

## Out of Scope

| Feature | Reason |
|---------|--------|
| Claude Agent SDK replacement | Out of scope — would require architectural rewrite, not a bug fix |
| Claude CLI session features (--continue, --session-id) | Active bugs in v2.1.31+, incompatible with --print mode |
| stream-json input format | Known duplication bug (Issue #5034), unnecessary complexity |
| BA flow changes | CLI adapter fix only; BA flow uses agent_service.py (unchanged) |
| Cross-thread memory | Each thread is independent context; cross-thread adds complexity |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONV-01 | TBD | Pending |
| CONV-02 | TBD | Pending |
| CONV-03 | TBD | Pending |
| CONV-04 | TBD | Pending |
| TOKEN-01 | TBD | Pending |
| TOKEN-02 | TBD | Pending |
| TOKEN-03 | TBD | Pending |
| TOKEN-04 | TBD | Pending |
| PERF-01 | TBD | Pending |
| PERF-02 | TBD | Pending |
| PERF-03 | TBD | Pending |
| TEST-01 | TBD | Pending |
| TEST-02 | TBD | Pending |
| TEST-03 | TBD | Pending |
| TEST-04 | TBD | Pending |
| TEST-05 | TBD | Pending |

**Coverage:**
- v3.1.1 requirements: 16 total
- Mapped to phases: 0
- Unmapped: 16 ⚠️

---
*Requirements defined: 2026-02-19*
*Last updated: 2026-02-19 after initial definition*
