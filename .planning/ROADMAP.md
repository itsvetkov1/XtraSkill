# Roadmap: BA Assistant v1.9.2

**Milestone:** v1.9.2 - Resilience & AI Transparency
**Created:** 2026-02-03
**Phases:** 3 (34-36)
**Requirements:** 24

## Overview

This milestone delivers error resilience, transparency indicators, and UX improvements. Phases are ordered by architectural dependencies: frontend-only changes first (no deployment coordination), then features surfacing existing data, then features requiring backend changes.

---

## Phase 34: Client-Side Resilience

**Goal:** Users experience graceful handling of network errors and upload validation without losing data

**Dependencies:** None (frontend-only)

**Plans:** 2 plans

Plans:
- [x] 34-01-PLAN.md - Network resilience: preserve partial content on stream error
- [x] 34-02-PLAN.md - File validation: client-side size check before upload

**Requirements:**
- NET-01: On network loss during SSE streaming, partial AI content is preserved (not cleared)
- NET-02: Error banner displays "Connection lost - response incomplete" when stream interrupted
- NET-03: Retry button available to regenerate interrupted response
- NET-04: Copy button remains functional for partial content in error state
- FILE-01: File size validated client-side before upload attempt
- FILE-02: Clear error message: "File too large. Maximum size is 1MB."
- FILE-03: Invalid file selection cleared, user can immediately try again

**Success Criteria:**
1. User sees partial AI response preserved when network drops mid-stream (not blank message)
2. User can tap Retry to regenerate response after network error
3. User can copy partial content from error-state message
4. User sees validation error immediately after selecting oversized file (before upload starts)
5. User can select a different file after validation failure without page reload

---

## Phase 35: Transparency Indicators

**Goal:** Users have visibility into budget status and conversation mode throughout their session

**Dependencies:** Phase 34 complete (establishes error handling patterns)

**Plans:** 3 plans

Plans:
- [x] 35-01-PLAN.md - Budget warning banners at 80%/95%/100% thresholds
- [x] 35-02-PLAN.md - Backend: add conversation_mode to Thread model
- [x] 35-03-PLAN.md - Mode badge in AppBar with tap-to-change

**Requirements:**
- BUD-01: Warning banner at 80% budget usage: "You've used 80% of your token budget"
- BUD-02: Warning banner at 95% usage: "Almost at limit - limited messages remaining"
- BUD-03: At 100%: Clear "Budget exhausted" state in ConversationScreen
- BUD-04: Exhausted state allows viewing history but blocks sending new messages
- BUD-05: Budget display shows percentage only (no monetary amounts)
- MODE-01: Current conversation mode shown as chip/badge in ConversationScreen AppBar
- MODE-02: Mode badge is tappable to open mode change menu
- MODE-03: Mode change shows warning about potential context shift
- MODE-04: Mode persists in database for that thread (survives app restart)

**Success Criteria:**
1. User sees warning banner when budget reaches 80% and 95% thresholds
2. User cannot send messages when budget exhausted but can still read history
3. User sees conversation mode (Meeting/Document Refinement) in AppBar after mode selection
4. User can tap mode badge to change mode with warning about context shift
5. User sees same mode after app restart for same thread

---

## Phase 36: AI Interaction Enhancement

**Goal:** Users can generate artifacts and see which documents informed AI responses

**Dependencies:** Phase 35 complete (backend patterns established)

**Requirements:**
- ART-01: "Generate Artifact" button visible in ConversationScreen
- ART-02: Artifact type picker with options: User Stories, Acceptance Criteria, BRD, Custom
- ART-03: Generated artifacts have inline export buttons (Markdown, PDF, Word)
- ART-04: Artifacts visually distinct from regular chat messages (card styling)
- SRC-01: AI responses show source document chips when documents were referenced
- SRC-02: Source chips display document names: "Sources: requirements.md, notes.txt"
- SRC-03: Clicking source chip opens Document Viewer for that document
- SRC-04: If no documents used in response, no source section shown

**Success Criteria:**
1. User can generate User Stories or BRD from conversation with type picker
2. User can export generated artifact as Markdown, PDF, or Word directly from card
3. User sees source document chips below AI response that used project documents
4. User can click source chip to view the referenced document
5. User sees artifact cards visually distinct from regular messages (card with border)

---

## Progress

| Phase | Name | Status | Requirements |
|-------|------|--------|--------------|
| 34 | Client-Side Resilience | Complete | 7/7 |
| 35 | Transparency Indicators | Complete | 9/9 |
| 36 | AI Interaction Enhancement | Not Started | 8 |

**Total:** 16/24 requirements complete

---

*Roadmap created: 2026-02-03*
*Last updated: 2026-02-03 (Phase 35 complete)*
