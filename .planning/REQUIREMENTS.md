# Requirements: BA Assistant v1.9.2

**Defined:** 2026-02-02
**Core Value:** Business analysts reduce time on requirement documentation through AI-assisted discovery conversations

## v1.9.2 Requirements

Requirements for Resilience & AI Transparency milestone. Each maps to roadmap phases.

### Network Resilience

- [ ] **NET-01**: On network loss during SSE streaming, partial AI content is preserved (not cleared)
- [ ] **NET-02**: Error banner displays "Connection lost - response incomplete" when stream interrupted
- [ ] **NET-03**: Retry button available to regenerate interrupted response
- [ ] **NET-04**: Copy button remains functional for partial content in error state

### Token Budget UX

- [ ] **BUD-01**: Warning banner at 80% budget usage: "You've used 80% of your token budget"
- [ ] **BUD-02**: Warning banner at 95% usage: "Almost at limit - limited messages remaining"
- [ ] **BUD-03**: At 100%: Clear "Budget exhausted" state in ConversationScreen
- [ ] **BUD-04**: Exhausted state allows viewing history but blocks sending new messages
- [ ] **BUD-05**: Budget display shows percentage only (no monetary amounts)

### Mode Indicator

- [ ] **MODE-01**: Current conversation mode shown as chip/badge in ConversationScreen AppBar
- [ ] **MODE-02**: Mode badge is tappable to open mode change menu
- [ ] **MODE-03**: Mode change shows warning about potential context shift
- [ ] **MODE-04**: Mode persists in database for that thread (survives app restart)

### Artifact Generation UI

- [ ] **ART-01**: "Generate Artifact" button visible in ConversationScreen
- [ ] **ART-02**: Artifact type picker with options: User Stories, Acceptance Criteria, BRD, Custom
- [ ] **ART-03**: Generated artifacts have inline export buttons (Markdown, PDF, Word)
- [ ] **ART-04**: Artifacts visually distinct from regular chat messages (card styling)

### Document Sources

- [ ] **SRC-01**: AI responses show source document chips when documents were referenced
- [ ] **SRC-02**: Source chips display document names: "Sources: requirements.md, notes.txt"
- [ ] **SRC-03**: Clicking source chip opens Document Viewer for that document
- [ ] **SRC-04**: If no documents used in response, no source section shown

### File Validation

- [ ] **FILE-01**: File size validated client-side before upload attempt
- [ ] **FILE-02**: Clear error message: "File too large. Maximum size is 1MB."
- [ ] **FILE-03**: Invalid file selection cleared, user can immediately try again

## v2.0 Deferred

Features acknowledged but not in current milestone scope.

### Network Resilience Extras
- Auto-reconnect with exponential backoff (requires eventflux migration)
- Network state detection banner (requires connectivity_plus)

### Budget Extras
- Real-time budget display during conversation (not just Settings)
- Estimated messages remaining calculation

### Artifact Extras
- Dedicated Artifacts tab showing all generated artifacts
- Artifact editing before export

## Out of Scope

| Feature | Reason |
|---------|--------|
| Monetary budget display | User preference: percentages only |
| Full eventflux migration | Risk: web support experimental; keep current SSE for now |
| Artifact versioning | Complexity: defer to future milestone |
| Document source highlighting | Complexity: would require storing chunk positions |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NET-01 | Phase 34 | Pending |
| NET-02 | Phase 34 | Pending |
| NET-03 | Phase 34 | Pending |
| NET-04 | Phase 34 | Pending |
| FILE-01 | Phase 34 | Pending |
| FILE-02 | Phase 34 | Pending |
| FILE-03 | Phase 34 | Pending |
| BUD-01 | Phase 35 | Pending |
| BUD-02 | Phase 35 | Pending |
| BUD-03 | Phase 35 | Pending |
| BUD-04 | Phase 35 | Pending |
| BUD-05 | Phase 35 | Pending |
| MODE-01 | Phase 35 | Pending |
| MODE-02 | Phase 35 | Pending |
| MODE-03 | Phase 35 | Pending |
| MODE-04 | Phase 35 | Pending |
| ART-01 | Phase 36 | Pending |
| ART-02 | Phase 36 | Pending |
| ART-03 | Phase 36 | Pending |
| ART-04 | Phase 36 | Pending |
| SRC-01 | Phase 36 | Pending |
| SRC-02 | Phase 36 | Pending |
| SRC-03 | Phase 36 | Pending |
| SRC-04 | Phase 36 | Pending |

**Coverage:**
- v1.9.2 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-02*
*Last updated: 2026-02-02 after initial definition*
