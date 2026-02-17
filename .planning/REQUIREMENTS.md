# Requirements: Assistant Foundation

**Defined:** 2026-02-17
**Core Value:** Separate Claude Code CLI into its own "Assistant" section with dedicated screens, clean of BA-specific logic — foundation for building a multi-purpose AI assistant.

## v3.0 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Data Model

- [ ] **DATA-01**: Thread model has `thread_type` field distinguishing BA Assistant vs Assistant threads
- [ ] **DATA-02**: Existing threads default to `ba_assistant` type via backward-compatible migration
- [ ] **DATA-03**: Documents can be associated with Assistant threads (project_id nullable for Assistant scope)

### Backend Logic

- [ ] **LOGIC-01**: AI service skips BA system prompt for Assistant threads (no BA tools, no BA instructions)
- [ ] **LOGIC-02**: MCP tools (search_documents, save_artifact) conditionally loaded only for BA threads
- [ ] **LOGIC-03**: Assistant threads always use `claude-code-cli` adapter regardless of settings

### API

- [ ] **API-01**: Thread creation accepts `thread_type` parameter
- [ ] **API-02**: Thread listing supports `thread_type` filter query parameter
- [ ] **API-03**: Assistant threads cannot have a project association (validation)

### Navigation

- [ ] **NAV-01**: "Assistant" appears as its own section in sidebar navigation
- [ ] **NAV-02**: Assistant section has dedicated routes (`/assistant`, `/assistant/:threadId`)
- [ ] **NAV-03**: Deep links to Assistant threads work correctly on page refresh

### UI

- [ ] **UI-01**: Assistant thread list screen shows only Assistant-type threads
- [ ] **UI-02**: User can create new Assistant thread (simplified dialog — no project, no mode selector)
- [ ] **UI-03**: Assistant conversation screen works end-to-end (send message, streaming response)
- [ ] **UI-04**: User can upload documents for context within Assistant threads
- [ ] **UI-05**: User can delete Assistant threads with standard undo behavior

## Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Search & Export

- **SRCH-01**: Thread search supports filtering by thread_type (FTS5 extension)
- **SRCH-02**: User can export Assistant conversation history as Markdown or PDF

### Customization

- **CUST-01**: User can define custom system prompts for Assistant mode
- **CUST-02**: User can select different providers in Assistant mode (not just CLI)

### Cross-Mode

- **XMOD-01**: User can reference BA project documents from Assistant threads
- **XMOD-02**: Shareable thread URLs work across BA and Assistant modes

## Out of Scope

| Feature | Reason |
|---------|--------|
| Universal thread list (mixed BA + Assistant) | Context confusion — users lose track of which mode a thread uses |
| Assistant switching mid-thread | System prompt contamination — BA context bleeds into general chat |
| Shared document pool across modes | Context pollution — BA docs appear in Assistant search results |
| Real-time sync between BA and Assistant | Privacy violation and context bloat |
| Conversation templates | Premature — validate basic Assistant first |
| Voice input | High complexity, defer to future |
| Multi-assistant workflows | Requires validated foundation first |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | TBD | Pending |
| DATA-02 | TBD | Pending |
| DATA-03 | TBD | Pending |
| LOGIC-01 | TBD | Pending |
| LOGIC-02 | TBD | Pending |
| LOGIC-03 | TBD | Pending |
| API-01 | TBD | Pending |
| API-02 | TBD | Pending |
| API-03 | TBD | Pending |
| NAV-01 | TBD | Pending |
| NAV-02 | TBD | Pending |
| NAV-03 | TBD | Pending |
| UI-01 | TBD | Pending |
| UI-02 | TBD | Pending |
| UI-03 | TBD | Pending |
| UI-04 | TBD | Pending |
| UI-05 | TBD | Pending |

**Coverage:**
- v3.0 requirements: 17 total
- Mapped to phases: 0
- Unmapped: 17

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-02-17 after initial definition*
