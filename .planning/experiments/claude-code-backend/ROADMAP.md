# Roadmap: Claude Code as AI Backend Experiment

## Overview

This experimental milestone investigates whether Claude Code's agent capabilities (via Python SDK or CLI subprocess) produce measurably better business analysis artifacts than the current direct API approach. The roadmap progresses through foundation setup, parallel SDK and CLI adapter implementations, frontend integration for comparison testing, and quality measurement with go/no-go decision. Success depends on demonstrating >20% quality improvement that justifies 30-50% cost overhead and integration complexity.

## Phases

**Phase Numbering:**
- Integer phases (57-61): Continuing from v2.1 (ended at phase 56)
- Decimal phases (e.g., 57.1): Urgent insertions if needed

**Experiment Phases:**
- [ ] **Phase 57: Foundation** - Shared infrastructure for both adapters
- [ ] **Phase 58: Agent SDK Adapter** - Primary integration via Python SDK
- [ ] **Phase 59: CLI Subprocess Adapter** - Experimental CLI subprocess integration
- [ ] **Phase 60: Frontend Integration** - Provider selection and streaming UI
- [ ] **Phase 61: Quality Comparison & Decision** - Measure quality and decide go/no-go

## Phase Details

### Phase 57: Foundation
**Goal**: Shared infrastructure ready for both SDK and CLI adapter implementations
**Depends on**: Nothing (experiment start)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04
**Success Criteria** (what must be TRUE):
  1. Developer can verify claude-agent-sdk v0.1.35+ installed with bundled CLI
  2. MCP tools (search_documents, save_artifact) extracted to shared reusable module
  3. LLMFactory recognizes "claude-code-sdk" provider and can route to adapter stub
  4. LLMFactory recognizes "claude-code-cli" provider and can route to adapter stub
**Plans**: TBD

Plans:
- [ ] 57-01: TBD

### Phase 58: Agent SDK Adapter
**Goal**: Claude Agent SDK integrated as production-viable provider via LLMAdapter pattern
**Depends on**: Phase 57 (shared tools and factory registration)
**Requirements**: SDK-01, SDK-02, SDK-03, SDK-04, SDK-05
**Success Criteria** (what must be TRUE):
  1. ClaudeAgentAdapter implements LLMAdapter.stream_chat() and yields StreamChunk events
  2. SDK agent loop events translate to StreamChunk format without data loss (text, thinking, tool_use, complete, error)
  3. MCP server integrates search_documents and save_artifact tools with proper context propagation
  4. User can create thread with claude-code-sdk provider and receive streaming responses via existing SSE endpoint
  5. SDK errors map to StreamChunk error chunks with user-friendly messages
**Plans**: TBD

Plans:
- [ ] 58-01: TBD

### Phase 59: CLI Subprocess Adapter
**Goal**: Claude Code CLI integrated as experimental provider for quality comparison
**Depends on**: Phase 57 (shared tools and factory registration)
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05
**Success Criteria** (what must be TRUE):
  1. ClaudeCLIAdapter implements LLMAdapter.stream_chat() and spawns CLI subprocess per request
  2. CLI subprocess lifecycle managed properly (spawn with flags, cleanup prevents zombies, timeout handling)
  3. JSON stream from CLI stdout parsed into StreamChunk events with proper event boundaries
  4. Tools work via MCP server or prompt-based approach (document search and artifact save functional)
  5. Subprocess cleanup prevents memory leaks and orphaned processes in async FastAPI context
**Plans**: TBD

Plans:
- [ ] 59-01: TBD

### Phase 60: Frontend Integration
**Goal**: Users can select Claude Code providers and use them for conversations
**Depends on**: Phase 58 (SDK adapter) and Phase 59 (CLI adapter)
**Requirements**: UI-01, UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):
  1. Settings page provider dropdown shows "Claude Code (SDK)" option
  2. Settings page provider dropdown shows "Claude Code (CLI)" option
  3. User can create new thread with claude-code-sdk or claude-code-cli provider
  4. Chat streaming works end-to-end with new providers (messages sent, AI responses stream, thinking displays, tools execute)
**Plans**: TBD

Plans:
- [ ] 60-01: TBD

### Phase 61: Quality Comparison & Decision
**Goal**: Measurable quality comparison with clear go/no-go recommendation
**Depends on**: Phase 60 (both adapters functional in UI)
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05
**Success Criteria** (what must be TRUE):
  1. 5+ BRDs generated with direct API (anthropic provider baseline) with quality metrics recorded
  2. 5+ BRDs generated with Agent SDK adapter (claude-code-sdk) with quality metrics recorded
  3. 5+ BRDs generated with CLI subprocess adapter (claude-code-cli) with quality metrics recorded
  4. Quality metrics defined and scored across all samples (completeness, AC quality, consistency, error coverage)
  5. Comparison report written with recommendation (adopt SDK, adopt CLI, stay with direct API, or enhance direct API with multi-pass)
**Plans**: TBD

Plans:
- [ ] 61-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 57 → 58 → 59 → 60 → 61

**Note:** This is an experiment on feature branch `feature/claude-code-backend`. Phase 61 decision gates any merge to master.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 57. Foundation | 0/TBD | Not started | - |
| 58. Agent SDK Adapter | 0/TBD | Not started | - |
| 59. CLI Subprocess Adapter | 0/TBD | Not started | - |
| 60. Frontend Integration | 0/TBD | Not started | - |
| 61. Quality Comparison & Decision | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-13*
*Experiment milestone: v0.1-claude-code*
*Phase range: 57-61 (5 phases)*
