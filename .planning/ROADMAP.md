# Roadmap: v1.9 UX Improvements

**Milestone:** v1.9
**Created:** 2026-02-01
**Status:** In Progress

---

## Overview

Reduce friction in daily chat workflow with standard chat UX patterns, improved project layout prioritizing conversations, and flexible chat organization that doesn't require project selection upfront.

---

## Phases

### Phase 23: chat-input-ux

**Goal:** Standard chat input behavior with Enter to send and expanded input area.

**Dependencies:** None (standalone frontend change)

**Requirements:**
- INPUT-01: Enter key sends message when input is not empty
- INPUT-02: Enter key does nothing when input is empty
- INPUT-03: Shift+Enter inserts new line
- INPUT-04: Send button remains functional
- INPUT-05: Chat input expands to 8-10 visible lines

**Success Criteria:**
1. User can type message and press Enter to send immediately
2. User can compose multi-line message using Shift+Enter
3. Long messages display in expanded input area (scrollable)
4. Empty Enter does not trigger error or send

**Plans:** 1 plan

Plans:
- [x] 23-01-PLAN.md - Enter/Shift+Enter keyboard handling and expanded input

---

### Phase 24: project-layout-redesign

**Goal:** Threads become primary view with documents in collapsible side column.

**Dependencies:** None (standalone frontend change)

**Requirements:**
- LAYOUT-01: Threads view is default when opening project
- LAYOUT-02: Documents in collapsible column
- LAYOUT-03: Column minimized by default
- LAYOUT-04: Click to expand column
- LAYOUT-05: Click to collapse column
- LAYOUT-06: Document operations accessible from column

**Success Criteria:**
1. Opening project shows threads list immediately (not documents tab)
2. User can access documents via side column without leaving threads view
3. Column state (expanded/collapsed) persists within session
4. All document functionality works from column (upload, view, delete)

**Plans:** 2 plans

Plans:
- [ ] 24-01-PLAN.md - DocumentColumnProvider and DocumentsColumn widget foundation
- [ ] 24-02-PLAN.md - Refactor ProjectDetailScreen to Row layout

---

### Phase 25: global-chats-backend

**Goal:** Backend support for project-less threads and global chats listing.

**Dependencies:** None (backend foundation)

**Requirements:**
- CHATS-01: Chats section in navigation (frontend shows section)
- CHATS-02: API returns all user's chats
- CHATS-03: Response includes project name or null
- CHATS-04: Sorted by most recent activity
- CHATS-05: New Chat in Chats section
- CHATS-06: New Chat on Home page
- CHATS-07: Direct to conversation view

**Success Criteria:**
1. API endpoint returns all threads for user (with and without projects)
2. Creating thread without project_id succeeds
3. Thread response includes project info (or null for project-less)
4. Frontend Chats section displays all threads with project context

**Plans:** TBD

---

### Phase 26: chat-project-association

**Goal:** Add project-less chats to projects with UI for association.

**Dependencies:** Phase 25 (global chats must exist)

**Requirements:**
- CHATS-08: Chat detail shows project or "No Project" with add button
- CHATS-09: Add to Project button in header
- CHATS-10: Add to Project in options menu
- CHATS-11: Project selection modal
- CHATS-12: After association, chat in project's list
- CHATS-13: Association is permanent

**Success Criteria:**
1. Project-less chat shows "Add to Project" button in header
2. Clicking Add opens modal with project list
3. Selecting project associates chat permanently
4. Associated chat appears in both Chats menu and project's thread list

**Plans:** TBD

---

### Phase 27: thread-search-filter

**Goal:** Search and sort functionality for thread lists.

**Dependencies:** None (standalone frontend feature)

**Requirements:**
- SEARCH-01: Search bar filters by title
- SEARCH-02: Sort options (Newest, Oldest, Alphabetical)
- SEARCH-03: Search persists until cleared
- SEARCH-04: Empty result message

**Success Criteria:**
1. User can type in search bar to filter threads instantly
2. User can change sort order via dropdown/selector
3. Search term remains visible and active until cleared
4. "No threads matching 'X'" shown when no results

**Plans:** TBD

---

## Progress

| Phase | Name | Requirements | Status |
|-------|------|--------------|--------|
| 23 | chat-input-ux | INPUT-01 to INPUT-05 | Complete |
| 24 | project-layout-redesign | LAYOUT-01 to LAYOUT-06 | Planned |
| 25 | global-chats-backend | CHATS-01 to CHATS-07 | Pending |
| 26 | chat-project-association | CHATS-08 to CHATS-13 | Pending |
| 27 | thread-search-filter | SEARCH-01 to SEARCH-04 | Pending |

**Coverage:** 27/27 requirements mapped

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Enter behavior | Enter sends, Shift+Enter newline | Industry standard (Slack, Discord, Teams) |
| Documents column | Collapsible, minimized default | Prioritizes conversation workflow without hiding documents |
| Project association | One-way (add only) | Simpler than bidirectional; prevents accidental orphaning |
| Thread search | Client-side filtering | Sufficient for expected thread counts; no backend change needed |

---

*Roadmap created: 2026-02-01*
