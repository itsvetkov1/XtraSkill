# Requirements: BA Assistant — v3.2 Assistant File Generation & CLI Permissions

**Defined:** 2026-02-23
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v3.2 Requirements

Requirements for v3.2 milestone. Each maps to roadmap phases.

### CLI Permissions

- [ ] **CLI-01**: Claude CLI subprocess runs with `--dangerously-skip-permissions` flag in all spawn paths (warm pool, cold spawn, direct)
- [ ] **CLI-02**: `--dangerously-skip-permissions` flag added to `_spawn_warm_process()` in ClaudeProcessPool
- [ ] **CLI-03**: `--dangerously-skip-permissions` flag added to `_cold_spawn()` in ClaudeProcessPool
- [ ] **CLI-04**: `--dangerously-skip-permissions` flag added to direct subprocess spawn in `stream_chat()` fallback path
- [ ] **CLI-05**: Assistant chat works end-to-end without CLI permission prompts blocking

### File Generation Backend

- [ ] **GEN-01**: Assistant threads have a lightweight system prompt that instructs the CLI to use `save_artifact` tool for file generation requests
- [ ] **GEN-02**: `artifact_generation` parameter is threaded through to `_stream_agent_chat()` for conditional behavior
- [ ] **GEN-03**: `save_artifact` MCP tool is available and functional for Assistant thread file generation
- [ ] **GEN-04**: Generated file content is persisted via Artifact model and retrievable via existing artifact API

### File Generation Frontend

- [ ] **UI-01**: "Generate File" icon button appears next to the send button in Assistant chat input bar
- [ ] **UI-02**: Clicking "Generate File" opens a dialog with a free-text field for describing what to generate
- [ ] **UI-03**: Dialog has confirm/cancel buttons; confirm triggers generation
- [ ] **UI-04**: `generateFile()` is a separate method on AssistantConversationProvider (not reusing `sendMessage()`)
- [ ] **UI-05**: AssistantConversationProvider handles `ArtifactCreatedEvent` from SSE stream
- [ ] **UI-06**: Generated content displays as an artifact card in the Assistant chat message list
- [ ] **UI-07**: Artifact card supports collapse/expand interaction
- [ ] **UI-08**: Artifact card has export buttons for Markdown, PDF, and Word formats
- [ ] **UI-09**: Generation-in-progress state shows a loading indicator (not blank message bubble)

## Future Requirements

### Deferred

- Thread list items show preview of last message (from Beta v1.5)
- Thread list items display mode indicator (from Beta v1.5)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Predefined artifact types for Assistant | Assistant uses free-text description, not BA's preset BRD/AC/UserStory types |
| New API endpoints for generation | Reuses existing chat endpoint with artifact_generation flag |
| DB migration for new artifact type | Research conflict resolved: reuse existing artifact type infrastructure |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 71 | Pending |
| CLI-02 | Phase 71 | Pending |
| CLI-03 | Phase 71 | Pending |
| CLI-04 | Phase 71 | Pending |
| CLI-05 | Phase 71 | Pending |
| GEN-01 | Phase 72 | Pending |
| GEN-02 | Phase 72 | Pending |
| GEN-03 | Phase 72 | Pending |
| GEN-04 | Phase 72 | Pending |
| UI-01 | Phase 73 | Pending |
| UI-02 | Phase 73 | Pending |
| UI-03 | Phase 73 | Pending |
| UI-04 | Phase 73 | Pending |
| UI-05 | Phase 73 | Pending |
| UI-06 | Phase 73 | Pending |
| UI-07 | Phase 73 | Pending |
| UI-08 | Phase 73 | Pending |
| UI-09 | Phase 73 | Pending |

**Coverage:**
- v3.2 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 — traceability complete after roadmap creation*
