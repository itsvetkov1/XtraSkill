# Roadmap: v1.6 UX Quick Wins

**Milestone:** v1.6 UX Quick Wins
**Created:** 2026-01-30
**Phases:** 4 (Phases 11-14)
**Depth:** Quick

## Overview

This milestone delivers four friction-reduction features for the conversation workflow: copy AI responses, retry failed messages, display auth provider, and rename threads. All features use existing Flutter SDK capabilities with zero new dependencies. Frontend-only features execute first (Copy, Retry, Auth), followed by the full-stack feature (Thread Rename).

## Phases

### Phase 11: Copy AI Response

**Goal:** Users can copy AI-generated content to clipboard with one tap.

**Dependencies:** None

**Requirements:**
- COPY-01: Copy icon button visible on all assistant messages
- COPY-02: Copy action copies full message content to clipboard
- COPY-03: Snackbar confirms "Copied to clipboard"
- COPY-04: Copy works cross-platform (web, Android, iOS) with error handling

**Success Criteria:**
1. User sees copy icon on every assistant message bubble
2. Tapping copy icon places full message text on system clipboard
3. "Copied to clipboard" snackbar appears after successful copy
4. Copy fails gracefully on all platforms with error feedback

**Effort Estimate:** 1-2 hours

**Plans:** 1 plan
Plans:
- [x] 11-01-PLAN.md - Add copy button to assistant messages with clipboard integration

---

### Phase 12: Retry Failed Message

**Goal:** Users can recover from AI request failures without retyping.

**Dependencies:** None (can run parallel with Phase 11)

**Requirements:**
- RETRY-01: Error banner shows "Dismiss | Retry" actions when AI request fails
- RETRY-02: Retry resends the last user message without retyping
- RETRY-03: Failed message state tracked in ConversationProvider
- RETRY-04: Works for both network errors and API errors

**Success Criteria:**
1. When AI request fails, error banner appears with "Dismiss" and "Retry" buttons
2. Tapping "Retry" resends the original user message automatically
3. User does not need to retype or remember their failed message
4. Retry works identically for network timeouts and API errors (500s, etc.)

**Effort Estimate:** 2-3 hours

**Plans:** 1 plan
Plans:
- [x] 12-01-PLAN.md - Add retry state to provider and retry button to error banner

---

### Phase 13: Auth Provider Display

**Goal:** Users can identify which OAuth provider they authenticated with.

**Dependencies:** None (can run parallel with Phases 11-12)

**Requirements:**
- SETTINGS-01: Auth provider indicator shown in Settings profile section
- SETTINGS-02: Display format: "Signed in with Google" or "Signed in with Microsoft"

**Success Criteria:**
1. Settings page profile section shows authentication method
2. Display reads "Signed in with Google" or "Signed in with Microsoft" based on login method
3. No authentication required to view (uses cached auth state)

**Effort Estimate:** 30 minutes - 1 hour

**Plans:** 1 plan
Plans:
- [x] 13-01-PLAN.md - Add authProvider field to provider and display in settings profile

---

### Phase 14: Thread Rename

**Goal:** Users can rename conversation threads after creation.

**Dependencies:** Phases 11-13 (execute last as full-stack feature)

**Requirements:**
- THREAD-01: Edit icon in ConversationScreen AppBar opens rename dialog
- THREAD-02: "Rename" option in Thread List PopupMenu
- THREAD-03: Dialog pre-fills current thread title
- THREAD-04: Backend PATCH endpoint for thread rename

**Success Criteria:**
1. User can tap edit icon in conversation AppBar to open rename dialog
2. User can select "Rename" from thread list popup menu to open rename dialog
3. Rename dialog shows current thread title, ready for editing
4. Saving updates thread title immediately (optimistic UI with rollback on failure)
5. Backend validates and persists new title

**Effort Estimate:** 3-4 hours (1hr backend, 2-3hr frontend)

**Plans:** 2 plans
Plans:
- [ ] 14-01-PLAN.md - Backend PATCH endpoint for thread rename
- [ ] 14-02-PLAN.md - Frontend service, provider, dialog, and UI integration

---

## Progress

| Phase | Name | Requirements | Status | Verified |
|-------|------|--------------|--------|----------|
| 11 | Copy AI Response | 4 | Complete | 2026-01-30 |
| 12 | Retry Failed Message | 4 | Complete | 2026-01-30 |
| 13 | Auth Provider Display | 2 | Complete | 2026-01-30 |
| 14 | Thread Rename | 4 | Planned | - |

**Total:** 14 requirements across 4 phases

## Execution Order

Phases 11-13 are independent (frontend-only) and can execute in any order or parallel.
Phase 14 requires backend work first, so executes last.

Recommended order: 11 -> 12 -> 13 -> 14

---

*Roadmap created: 2026-01-30*
*Last updated: 2026-01-30 (Phase 14 planned)*
