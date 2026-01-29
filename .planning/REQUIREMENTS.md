# Requirements

**Project:** Business Analyst Assistant
**Version:** Beta v1.5 - UI/UX Excellence
**Last Updated:** 2026-01-29

## Overview

This document defines functional requirements for Beta v1.5, focusing on UI/UX improvements to prepare the application for executive demos and wider user testing. Requirements transform the MVP into a polished, intuitive experience through navigation enhancements, professional empty states, deletion capabilities, and visual consistency improvements.

## Beta v1.5 Requirements

### Navigation & Layout (NAV)

| REQ-ID | Requirement | Priority | Complexity |
|--------|-------------|----------|------------|
| **NAV-01** | Persistent sidebar navigation visible on all screens with responsive behavior (desktop always-visible ≥900px, mobile hamburger <600px) | CRITICAL | High |
| **NAV-02** | Breadcrumb navigation displays current location path (e.g., "Projects > Project Name > Thread Name") | HIGH | Medium |
| **NAV-03** | Back arrows show destination context (e.g., "← Projects" or "← Project Name") | MEDIUM | Low |
| **NAV-04** | Navigation highlights current screen location in sidebar | HIGH | Low |
| **NAV-05** | Sidebar state persists across navigation (expanded/collapsed preference on desktop) | MEDIUM | Medium |

**Category Rationale:** Navigation is the critical foundation - users reported getting lost without persistent sidebar. Fixes the #1 critical UX issue from analysis.

---

### User Guidance & Onboarding (ONBOARD)

| REQ-ID | Requirement | Priority | Complexity |
|--------|-------------|----------|------------|
| **ONBOARD-01** | Projects list displays empty state when user has no projects (illustration + message + "Create Project" CTA) | CRITICAL | Low |
| **ONBOARD-02** | Threads list displays empty state when project has no threads (message + "Start Conversation" CTA) | CRITICAL | Low |
| **ONBOARD-03** | Documents list displays empty state when project has no documents (message + "Upload Document" CTA) | CRITICAL | Low |
| **ONBOARD-04** | Home screen displays primary action buttons ("Start Conversation", "Browse Projects") after authentication | CRITICAL | Low |
| **ONBOARD-05** | Home screen removes development phase information ("Next Steps") and displays user-oriented welcome | CRITICAL | Low |

**Category Rationale:** Empty states prevent "blank screen" confusion for new users during executive demos. Fixes critical first-impression issues.

---

### Data Management - Deletion (DEL)

| REQ-ID | Requirement | Priority | Complexity |
|--------|-------------|----------|------------|
| **DEL-01** | User can delete projects with confirmation dialog showing cascade impact ("This will delete X threads and Y documents") | HIGH | High |
| **DEL-02** | User can delete threads with confirmation dialog showing impact ("This will delete X messages") | HIGH | Medium |
| **DEL-03** | User can delete documents from project (confirmation dialog) | HIGH | Low |
| **DEL-04** | User can delete individual messages from thread (confirmation dialog) | MEDIUM | Medium |
| **DEL-05** | Backend performs cascade deletes maintaining referential integrity (threads→messages, projects→threads→messages) | CRITICAL | High |
| **DEL-06** | Deleted items show SnackBar with undo action (10-second window) | HIGH | High |
| **DEL-07** | Deletion uses optimistic UI updates (immediate removal from list, rollback on error) | MEDIUM | Medium |

**Category Rationale:** Deletion was deferred from MVP. Research shows undo pattern (SnackBar) is table stakes for Flutter apps. Bringing forward from original Beta scope.

---

### Settings & Preferences (SET)

| REQ-ID | Requirement | Priority | Complexity |
|--------|-------------|----------|------------|
| **SET-01** | Settings page displays user profile information (email, name from OAuth provider) | HIGH | Low |
| **SET-02** | Settings page provides logout button with confirmation | HIGH | Low |
| **SET-03** | Settings page includes light/dark theme toggle switch | HIGH | Medium |
| **SET-04** | Theme preference persists across app restarts (SharedPreferences) | CRITICAL | Medium |
| **SET-05** | Settings page displays current month token budget usage (used/limit with percentage) | MEDIUM | Medium |
| **SET-06** | Theme loads before MaterialApp initialization (prevent white flash on dark mode) | CRITICAL | Low |
| **SET-07** | Theme respects system preference on first launch (iOS/Android/web) | MEDIUM | Low |

**Category Rationale:** Settings page was referenced in sidebar but didn't exist. Theme toggle and token budget display add transparency and user control.

---

### Conversation UI Enhancements (CONV-UI)

| REQ-ID | Requirement | Priority | Complexity |
|--------|-------------|----------|------------|
| **CONV-UI-01** | AI mode selection presents as clickable ChoiceChip buttons (Meeting Mode, Document Refinement Mode) instead of typed "A"/"B" responses | HIGH | Medium |
| **CONV-UI-02** | Message pills have improved readability (increased padding, font size 15-16px) | MEDIUM | Low |
| **CONV-UI-03** | Thread list items display mode indicator (chip or colored dot showing which mode was used) | LOW | Low |

**Category Rationale:** Mode selection via typing "A" or "B" creates friction and feels dated. ChoiceChips are standard Material 3 pattern for exclusive selection.

---

### Visual Polish & Consistency (POLISH)

| REQ-ID | Requirement | Priority | Complexity |
|--------|-------------|----------|------------|
| **POLISH-01** | Date/time formatting is consistent: relative for recent (<7 days: "4d ago", "Yesterday"), absolute for older (>7 days: "Jan 18, 2026") | HIGH | Low |
| **POLISH-02** | Project detail headers are consolidated to reduce vertical space waste (single line name + metadata, not duplicate) | MEDIUM | Low |
| **POLISH-03** | Thread list items show preview text (first line of last message, truncated to 80 chars) | MEDIUM | Low |
| **POLISH-04** | Project cards display metadata badges (thread count, document count) | LOW | Low |
| **POLISH-05** | All dates use `intl` package with locale-aware formatting (not hard-coded strings) | MEDIUM | Low |

**Category Rationale:** Visual consistency improvements caught by UX analysis. Date formatting inconsistency ("4d ago" vs "2026-01-19") was flagged as unprofessional.

---

## v2.0 Requirements (Deferred to Next Milestone)

### Search & Discovery (SEARCH)

| REQ-ID | Requirement | Rationale for Deferral |
|--------|-------------|------------------------|
| **SEARCH-01** | User can search across all projects by name or description | Beta v1.5 focuses on navigation and polish; search deferred to v2.0 per original plan |
| **SEARCH-02** | User can search within project across threads | Same as SEARCH-01 |
| **SEARCH-03** | User can filter projects by date or activity | Same as SEARCH-01 |

### Advanced Features (ADVANCED)

| REQ-ID | Requirement | Rationale for Deferral |
|--------|-------------|------------------------|
| **ADVANCED-01** | Keyboard shortcuts for desktop power users (Cmd+N for new conversation, etc.) | Nice-to-have; defer until post-Beta user feedback validates need |
| **ADVANCED-02** | Contextual empty state illustrations (different images per scenario) | Single generic illustration sufficient for Beta; A/B test later |
| **ADVANCED-03** | Bulk deletion (multi-select) | Single-item deletion sufficient; bulk adds UI complexity |
| **ADVANCED-04** | Thread archiving and starring | Organization features defer to v2.0 |
| **ADVANCED-05** | Message editing (not just deletion) | Editing introduces conversation coherence complexity |

---

## Out of Scope (V2.0+)

### Collaboration & Sharing (COLLAB)

| Feature | Rationale |
|---------|-----------|
| Multi-user project sharing | Single-user per account validates core value first; team features add massive complexity |
| Real-time collaboration (simultaneous editing) | Requires WebSockets, CRDTs, conflict resolution; deferred until strong user demand |
| Comments on artifacts | Low ROI for single-user; defer to team collaboration phase |

### Integrations (INTEGR)

| Feature | Rationale |
|---------|-----------|
| JIRA integration (import/export) | CRITICAL for v2.0 enterprise adoption; defer until MVP validates core value |
| Azure DevOps integration | Similar to JIRA; high enterprise value but defer to v2.0 |
| Confluence export | Lower priority than JIRA; v2.0+ |

### Advanced UX (UX-ADVANCED)

| Feature | Rationale |
|---------|-----------|
| Offline mode with sync | Complex sync engine; validate need through usage data first |
| Voice input for messages | HIGH VALUE for meetings; consider for v2.0 if mobile adoption strong |
| Customizable themes (beyond light/dark) | Light/dark sufficient; custom themes add complexity without clear ROI |
| Accessibility features beyond WCAG AA | WCAG AA is table stakes (48×48px touch targets, 4.5:1 contrast); enhanced features (screen reader optimizations, high contrast mode) defer to v2.0 based on user requests |

---

## Requirement Traceability

This section maps requirements to roadmap phases. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| NAV-01 | Phase 7 | Pending |
| NAV-02 | Phase 7 | Pending |
| NAV-03 | Phase 7 | Pending |
| NAV-04 | Phase 7 | Pending |
| NAV-05 | Phase 7 | Pending |
| ONBOARD-01 | Phase 10 | Pending |
| ONBOARD-02 | Phase 10 | Pending |
| ONBOARD-03 | Phase 10 | Pending |
| ONBOARD-04 | Phase 10 | Pending |
| ONBOARD-05 | Phase 10 | Pending |
| DEL-01 | Phase 9 | Pending |
| DEL-02 | Phase 9 | Pending |
| DEL-03 | Phase 9 | Pending |
| DEL-04 | Phase 9 | Pending |
| DEL-05 | Phase 9 | Pending |
| DEL-06 | Phase 9 | Pending |
| DEL-07 | Phase 9 | Pending |
| SET-01 | Phase 8 | Pending |
| SET-02 | Phase 8 | Pending |
| SET-03 | Phase 6 | Complete |
| SET-04 | Phase 6 | Complete |
| SET-05 | Phase 8 | Pending |
| SET-06 | Phase 6 | Complete |
| SET-07 | Phase 6 | Complete |
| CONV-UI-01 | Phase 10 | Pending |
| CONV-UI-02 | Phase 10 | Pending |
| CONV-UI-03 | Phase 10 | Pending |
| POLISH-01 | Phase 10 | Pending |
| POLISH-02 | Phase 10 | Pending |
| POLISH-03 | Phase 10 | Pending |
| POLISH-04 | Phase 10 | Pending |
| POLISH-05 | Phase 10 | Pending |

**Coverage:**
- Beta v1.5 requirements: 32/32 mapped (100%)
- Phase 6 (Theme Management): 4 requirements
- Phase 7 (Navigation Infrastructure): 5 requirements
- Phase 8 (Settings Page): 3 requirements
- Phase 9 (Deletion Flows): 7 requirements
- Phase 10 (Polish & Empty States): 13 requirements
- v2.0 requirements: 9 deferred
- Out of scope: 8+ features

---

## Acceptance Criteria Guidelines

Each requirement will have detailed acceptance criteria defined during phase planning. Criteria must be:

- **Specific and testable:** Clear pass/fail conditions
- **User-centric:** Defined from user perspective (not technical implementation)
- **Observable:** Can be verified through UI or API interaction
- **Complete:** Covers happy path, edge cases, and error conditions

Example format:
```
**Given** user has zero projects
**When** user navigates to Projects screen
**Then** empty state displays with illustration
**And** message reads "No projects yet"
**And** "Create Project" button is prominently visible
**And** tapping button opens create project dialog
```

---

## Success Metrics

Beta v1.5 success will be measured by:

1. **Executive Demo Readiness:**
   - Zero navigation confusion (user can move between any two screens without backtracking)
   - Professional first impression (no blank screens, consistent polish)
   - All destructive actions have confirmation + undo (no fear of data loss)

2. **User Engagement:**
   - Empty state CTAs increase feature discovery (track clicks)
   - Home screen CTAs reduce time-to-first-conversation
   - Theme toggle used by 30%+ of users

3. **Technical Quality:**
   - Zero BuildContext async crashes (lint rule enforced)
   - Theme persistence 100% reliable (no white flash, survives restart)
   - Cascade deletes never orphan data (integration tests verify)

4. **UX Consistency:**
   - Date formatting consistent across all screens
   - Navigation state preserved (sidebar expansion, breadcrumbs accurate)
   - Deletion undo works 100% of time within 10-second window

---

*Requirements baseline established: 2026-01-29*
*Total Beta v1.5 requirements: 32*
*Total v2.0 requirements: 9*
*Out of scope: 8+*
*Traceability updated: 2026-01-29*
