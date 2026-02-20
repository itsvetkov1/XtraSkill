# Requirements: BA Assistant — v3.1.1 Assistant Conversation Memory

**Defined:** 2026-02-19
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v3.1.1 Requirements

Requirements for v3.1.1 milestone. Each maps to roadmap phases.

### Conversation Memory

- [x] **CONV-01**: CLI adapter sends full conversation history (all messages, not just last)
- [x] **CONV-02**: Messages formatted with role labels (`[USER]`, `[ASSISTANT]`) matching BA flow pattern
- [x] **CONV-03**: Role alternation validated before sending to CLI subprocess
- [x] **CONV-04**: Multi-part content handled (text blocks, tool results)

### Token Management

- [x] **TOKEN-01**: Assistant message filtering strips tool_use blocks to prevent document context duplication
- [x] **TOKEN-02**: Token-aware truncation preserved for CLI adapter (existing 150K limit)
- [x] **TOKEN-03**: Emergency truncation at 180K tokens with user-facing error message
- [x] **TOKEN-04**: Linear token growth verified (not quadratic) across 20+ turn conversations with docs

### Performance

- [ ] **PERF-01**: Subprocess spawn latency measured and baselined
- [ ] **PERF-02**: Process pooling implemented for warm subprocess reuse
- [ ] **PERF-03**: Latency improvement documented (target: <200ms vs ~400ms cold start)

### Testing

- [x] **TEST-01**: Backend unit tests for `_convert_messages_to_prompt()` with 1, 3, 10+ messages
- [x] **TEST-02**: Backend unit tests for multi-part content handling (tool results)
- [x] **TEST-03**: Backend regression tests verifying BA flow unchanged
- [x] **TEST-04**: Frontend tests for AssistantConversationProvider message history handling
- [x] **TEST-05**: Integration test: Assistant thread with 3+ turns preserves context

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
| CONV-01 | Phase 68 | Complete |
| CONV-02 | Phase 68 | Complete |
| CONV-03 | Phase 68 | Complete |
| CONV-04 | Phase 68 | Complete |
| TOKEN-01 | Phase 69 | Complete |
| TOKEN-02 | Phase 69 | Complete |
| TOKEN-03 | Phase 69 | Complete |
| TOKEN-04 | Phase 69 | Complete |
| PERF-01 | Phase 70 | Pending |
| PERF-02 | Phase 70 | Pending |
| PERF-03 | Phase 70 | Pending |
| TEST-01 | Phase 68 | Complete |
| TEST-02 | Phase 68 | Complete |
| TEST-03 | Phase 68 | Complete |
| TEST-04 | Phase 68 | Complete |
| TEST-05 | Phase 68 | Complete |

**Coverage:**
- v3.1.1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-02-19*
*Last updated: 2026-02-19 after roadmap creation — all 16 requirements mapped*
