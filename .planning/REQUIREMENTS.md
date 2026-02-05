# Requirements: BA Assistant v1.9.4

**Defined:** 2026-02-05
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations.

## v1 Requirements

Requirements for v1.9.4 Artifact Generation Deduplication. Each maps to roadmap phases.

### Prompt Engineering

- [x] **PROMPT-01**: System prompt includes artifact deduplication rule at priority 2 in `<critical_rules>` section
- [x] **PROMPT-02**: Deduplication rule uses positive framing: "ONLY act on the MOST RECENT user message"
- [x] **PROMPT-03**: Deduplication rule includes re-generation escape hatch (user explicitly asking to regenerate/revise is honored as a new request)
- [x] **PROMPT-04**: Deduplication rule references save_artifact tool results as completion evidence
- [x] **PROMPT-05**: Existing critical rules renumbered correctly (priorities shifted by +1)
- [x] **PROMPT-06**: save_artifact tool description enforces single-call: "Call this tool ONCE per user request"
- [x] **PROMPT-07**: "You may call this tool multiple times" line is removed from tool description
- [x] **PROMPT-08**: Tool description allows explicit re-generation via new user message

### History Filtering

- [x] **HIST-01**: `build_conversation_context()` detects fulfilled artifact requests in conversation history
- [x] **HIST-02**: Detection uses response-based strategy (what actually happened, not input guessing)
- [x] **HIST-03**: Fulfilled message pairs completely removed from context (user decision: removal, not annotation)
- [x] **HIST-04**: Unfulfilled requests (failed generation, no artifact created) are left untouched for retry
- [x] **HIST-05**: Custom freeform prompts handled correctly (response-based detection works for all prompt types)
- [x] **HIST-06**: Existing truncation logic in `build_conversation_context()` is unaffected

### Silent Generation

- [ ] **SILENT-01**: `ChatRequest` model accepts optional `artifact_generation` boolean flag
- [ ] **SILENT-02**: When `artifact_generation: true`, user message is NOT saved to database
- [ ] **SILENT-03**: When `artifact_generation: true`, assistant response is NOT saved to database
- [ ] **SILENT-04**: Artifact IS saved to artifacts table via save_artifact tool (core functionality preserved)
- [ ] **SILENT-05**: Silent instruction appended to in-memory conversation context but NOT persisted to database
- [ ] **SILENT-06**: `text_delta` SSE events suppressed when `artifact_generation: true`
- [ ] **SILENT-07**: `artifact_created` SSE event still emitted in silent mode
- [ ] **SILENT-08**: `message_complete` SSE event still emitted for stream-end signaling
- [ ] **SILENT-09**: Regular chat (without flag) is completely unaffected by silent generation changes
- [ ] **SILENT-10**: Frontend clicking preset artifact button sends `artifact_generation: true`
- [ ] **SILENT-11**: Frontend clicking custom artifact submit sends `artifact_generation: true`
- [ ] **SILENT-12**: No user message bubble appears in chat for button-triggered generation
- [ ] **SILENT-13**: No assistant text bubble appears for button-triggered generation
- [ ] **SILENT-14**: `generateArtifact()` is a separate code path from `sendMessage()` (not reused with flag)
- [ ] **SILENT-15**: Loading animation shows during generation with artifact type: "Generating [Type]..."
- [ ] **SILENT-16**: Artifact card appears after `artifact_created` event
- [ ] **SILENT-17**: Loading animation disappears after artifact card appears

### Error Handling

- [ ] **ERR-01**: If generation fails (error event), loading animation clears and error message shown
- [ ] **ERR-02**: Silent generation failures logged to backend for debugging
- [ ] **ERR-03**: Thread summary update skipped for silent requests (no new messages to summarize)
- [ ] **ERR-04**: Token tracking still works for artifact generation requests

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Context Management

- **CTX-01**: Context compaction for long threads (compress old tool interactions)
- **CTX-02**: Conversation summarization replacing old turns with LLM-generated summaries
- **CTX-03**: Observation masking for verbose tool results

### Tool Execution

- **TOOL-01**: Idempotent tool execution with dedup keys (artifact title + thread_id)
- **TOOL-02**: Step count limiting in tool loop (max iterations cap)
- **TOOL-03**: Cancel/stop button for generation in progress

### Artifact Management

- **ART-01**: Artifact version history (each regeneration creates new version)
- **ART-02**: Retry button on failed generation (inline, not requiring button re-click)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Trigger phrase detection system | Fragile regex/keyword matching; response-based detection is superior (zero false positives) |
| Removing old messages from history | Breaks conversation coherence; prefix annotation preserves reference-ability |
| Global `parallel_tool_calls: false` | Bug is specific to save_artifact, not parallel calling in general; global restriction causes collateral damage |
| Tool call deduplication middleware | Over-engineering; fix root cause instead of building infrastructure around symptom |
| Hidden message flag in database | Schema change not needed; ephemeral pattern (don't save) is simpler |
| Post-hoc duplicate deletion | Symptom treatment not prevention; user would see artifacts appear then disappear |
| Token accumulation bug fix | Pre-existing bug (ai_service.py line 776); out of scope for v1.9.4, track separately |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROMPT-01 | Phase 40 | Complete |
| PROMPT-02 | Phase 40 | Complete |
| PROMPT-03 | Phase 40 | Complete |
| PROMPT-04 | Phase 40 | Complete |
| PROMPT-05 | Phase 40 | Complete |
| PROMPT-06 | Phase 40 | Complete |
| PROMPT-07 | Phase 40 | Complete |
| PROMPT-08 | Phase 40 | Complete |
| HIST-01 | Phase 41 | Complete |
| HIST-02 | Phase 41 | Complete |
| HIST-03 | Phase 41 | Complete |
| HIST-04 | Phase 41 | Complete |
| HIST-05 | Phase 41 | Complete |
| HIST-06 | Phase 41 | Complete |
| SILENT-01 | Phase 42 | Pending |
| SILENT-02 | Phase 42 | Pending |
| SILENT-03 | Phase 42 | Pending |
| SILENT-04 | Phase 42 | Pending |
| SILENT-05 | Phase 42 | Pending |
| SILENT-06 | Phase 42 | Pending |
| SILENT-07 | Phase 42 | Pending |
| SILENT-08 | Phase 42 | Pending |
| SILENT-09 | Phase 42 | Pending |
| SILENT-10 | Phase 42 | Pending |
| SILENT-11 | Phase 42 | Pending |
| SILENT-12 | Phase 42 | Pending |
| SILENT-13 | Phase 42 | Pending |
| SILENT-14 | Phase 42 | Pending |
| SILENT-15 | Phase 42 | Pending |
| SILENT-16 | Phase 42 | Pending |
| SILENT-17 | Phase 42 | Pending |
| ERR-01 | Phase 42 | Pending |
| ERR-02 | Phase 42 | Pending |
| ERR-03 | Phase 42 | Pending |
| ERR-04 | Phase 42 | Pending |

**Coverage:**
- v1 requirements: 35 total
- Mapped to phases: 35
- Unmapped: 0

---
*Requirements defined: 2026-02-05*
*Last updated: 2026-02-05 (Phase 41 complete — HIST requirements marked done)*
