# Requirements: Claude Code as AI Backend Experiment

**Defined:** 2026-02-13
**Core Value:** Determine if Claude Code's agent capabilities produce measurably better business analysis artifacts than the current direct API approach

## v1 Requirements

Requirements for this experiment. Each maps to roadmap phases.

### Foundation

- [ ] **FOUND-01**: Developer can install claude-agent-sdk and verify CLI bundled
- [ ] **FOUND-02**: MCP tools (search_documents, save_artifact) extracted to shared reusable module
- [ ] **FOUND-03**: New provider `claude-code-sdk` registered in LLMFactory
- [ ] **FOUND-04**: New provider `claude-code-cli` registered in LLMFactory

### Agent SDK Adapter

- [ ] **SDK-01**: ClaudeAgentAdapter implements LLMAdapter ABC with stream_chat()
- [ ] **SDK-02**: SDK events translated to StreamChunk format (text, thinking, tool_use, complete, error)
- [ ] **SDK-03**: MCP server integrates search_documents and save_artifact tools
- [ ] **SDK-04**: Streaming responses work via existing SSE endpoint
- [ ] **SDK-05**: Error handling maps SDK errors to StreamChunk error chunks

### CLI Subprocess Adapter

- [ ] **CLI-01**: ClaudeCLIAdapter implements LLMAdapter ABC with stream_chat()
- [ ] **CLI-02**: CLI subprocess spawned with JSON output mode and proper lifecycle management
- [ ] **CLI-03**: JSON stream parsed into StreamChunk format
- [ ] **CLI-04**: Tool integration via MCP server or prompt-based approach
- [ ] **CLI-05**: Subprocess cleanup prevents zombie processes and memory leaks

### Frontend Integration

- [ ] **UI-01**: "Claude Code (SDK)" appears in provider settings dropdown
- [ ] **UI-02**: "Claude Code (CLI)" appears in provider settings dropdown
- [ ] **UI-03**: New threads can be created with claude-code providers
- [ ] **UI-04**: Chat streaming works end-to-end with new providers

### Quality Comparison

- [ ] **QUAL-01**: 5+ BRDs generated with direct API baseline (control)
- [ ] **QUAL-02**: 5+ BRDs generated with Agent SDK adapter
- [ ] **QUAL-03**: 5+ BRDs generated with CLI subprocess adapter
- [ ] **QUAL-04**: Quality metrics defined and scored (completeness, AC quality, consistency, error coverage)
- [ ] **QUAL-05**: Comparison report with go/no-go recommendation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Production deployment | This is an experiment branch — deployment only if quality proven |
| Multi-pass direct API enhancement | Interesting alternative but separate experiment |
| Session resumption / multi-turn agent sessions | SDK supports it but unnecessary for document generation comparison |
| Docker sandboxing per user | Over-engineering for experiment; evaluate if approach adopted |
| Cost optimization | Track costs during comparison but don't optimize yet |
| Frontend provider-specific UI | Use existing provider dropdown pattern, no custom UI per provider |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 57 | Pending |
| FOUND-02 | Phase 57 | Pending |
| FOUND-03 | Phase 57 | Pending |
| FOUND-04 | Phase 57 | Pending |
| SDK-01 | Phase 58 | Pending |
| SDK-02 | Phase 58 | Pending |
| SDK-03 | Phase 58 | Pending |
| SDK-04 | Phase 58 | Pending |
| SDK-05 | Phase 58 | Pending |
| CLI-01 | Phase 59 | Pending |
| CLI-02 | Phase 59 | Pending |
| CLI-03 | Phase 59 | Pending |
| CLI-04 | Phase 59 | Pending |
| CLI-05 | Phase 59 | Pending |
| UI-01 | Phase 60 | Pending |
| UI-02 | Phase 60 | Pending |
| UI-03 | Phase 60 | Pending |
| UI-04 | Phase 60 | Pending |
| QUAL-01 | Phase 61 | Pending |
| QUAL-02 | Phase 61 | Pending |
| QUAL-03 | Phase 61 | Pending |
| QUAL-04 | Phase 61 | Pending |
| QUAL-05 | Phase 61 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-13*
*Last updated: 2026-02-13 after initial definition*
