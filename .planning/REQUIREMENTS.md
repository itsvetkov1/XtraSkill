# Requirements: v1.9 UX Improvements

**Defined:** 2026-02-01
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v1.9 Requirements

Requirements for UX improvements. Each maps to roadmap phases.

### Chat Input (UX-001, THREAD-010)

- [x] **INPUT-01**: Enter key sends message when input is not empty
- [x] **INPUT-02**: Enter key does nothing when input is empty (no error, no empty send)
- [x] **INPUT-03**: Shift+Enter inserts new line in message
- [x] **INPUT-04**: Send button remains functional as alternative to Enter
- [x] **INPUT-05**: Chat input expands to 8-10 visible lines (scrollable beyond)

### Project Layout (UX-002)

- [x] **LAYOUT-01**: Threads view is default when opening a project (not Documents tab)
- [x] **LAYOUT-02**: Documents appear in collapsible column between menu and thread list
- [x] **LAYOUT-03**: Documents column is minimized by default (thin strip with icon)
- [x] **LAYOUT-04**: Clicking minimized column expands to show document list
- [x] **LAYOUT-05**: Expanded column can be collapsed back to minimized state
- [x] **LAYOUT-06**: Document operations (upload, view, delete) accessible from column

### Global Chats (UX-003)

- [x] **CHATS-01**: "Chats" section appears in left navigation menu
- [x] **CHATS-02**: Chats section shows all user's chats (with and without projects)
- [x] **CHATS-03**: Each chat shows title with project name in brackets (or "[No Project]")
- [x] **CHATS-04**: Chats sorted by most recent activity
- [x] **CHATS-05**: "New Chat" button in Chats section creates project-less chat
- [x] **CHATS-06**: "New Chat" button on Home page creates project-less chat
- [x] **CHATS-07**: New chat takes user directly to conversation view
- [ ] **CHATS-08**: Chat detail shows project name (clickable) or "No Project" with add button
- [ ] **CHATS-09**: "Add to Project" button in chat header for project-less chats
- [ ] **CHATS-10**: "Add to Project" option in chat options menu for project-less chats
- [ ] **CHATS-11**: Project selection modal shows all user's projects
- [ ] **CHATS-12**: After adding to project, chat appears in project's thread list
- [ ] **CHATS-13**: Association is permanent (no remove option)

### Thread Search (THREAD-006)

- [ ] **SEARCH-01**: Search bar in thread list filters by title (real-time)
- [ ] **SEARCH-02**: Sort options available: Newest, Oldest, Alphabetical
- [ ] **SEARCH-03**: Search persists until explicitly cleared
- [ ] **SEARCH-04**: Empty result shows "No threads matching '{query}'"

## v2.0 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Thread Enhancements

- **THREAD-PREVIEW**: Thread list items show preview of last message
- **THREAD-MODE**: Thread list items display mode indicator badge

### Search Expansion

- **GLOBAL-SEARCH**: Search across all projects and threads
- **SEARCH-CONTENT**: Search within message content (not just titles)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Mid-conversation project switching | Complexity; add once, never remove is simpler |
| Thread drag-and-drop between projects | Over-engineering; add-to-project modal sufficient |
| Column resize by dragging | Complexity; expand/collapse binary state is simpler |
| Keyboard shortcuts beyond Enter/Shift+Enter | Defer to v2.0 based on user demand |
| Multi-select chats for bulk operations | Defer to v2.0 |
| Chat archiving | Defer to v2.0 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INPUT-01 | Phase 23 | Complete |
| INPUT-02 | Phase 23 | Complete |
| INPUT-03 | Phase 23 | Complete |
| INPUT-04 | Phase 23 | Complete |
| INPUT-05 | Phase 23 | Complete |
| LAYOUT-01 | Phase 24 | Complete |
| LAYOUT-02 | Phase 24 | Complete |
| LAYOUT-03 | Phase 24 | Complete |
| LAYOUT-04 | Phase 24 | Complete |
| LAYOUT-05 | Phase 24 | Complete |
| LAYOUT-06 | Phase 24 | Complete |
| CHATS-01 | Phase 25 | Complete |
| CHATS-02 | Phase 25 | Complete |
| CHATS-03 | Phase 25 | Complete |
| CHATS-04 | Phase 25 | Complete |
| CHATS-05 | Phase 25 | Complete |
| CHATS-06 | Phase 25 | Complete |
| CHATS-07 | Phase 25 | Complete |
| CHATS-08 | Phase 26 | Pending |
| CHATS-09 | Phase 26 | Pending |
| CHATS-10 | Phase 26 | Pending |
| CHATS-11 | Phase 26 | Pending |
| CHATS-12 | Phase 26 | Pending |
| CHATS-13 | Phase 26 | Pending |
| SEARCH-01 | Phase 27 | Pending |
| SEARCH-02 | Phase 27 | Pending |
| SEARCH-03 | Phase 27 | Pending |
| SEARCH-04 | Phase 27 | Pending |

**Coverage:**
- v1.9 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---
*Requirements defined: 2026-02-01*
