# Phase 63: Navigation & Thread Management - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Dedicated Assistant section in the app with sidebar navigation, routes, thread list, thread creation, and thread deletion — all independent of BA Assistant. Users can navigate to `/assistant` and `/assistant/:threadId`, manage threads, and deep links work on refresh.

</domain>

<decisions>
## Implementation Decisions

### Sidebar Placement
- Assistant section appears **above** the BA Assistant section in the sidebar
- Both sections have expandable thread lists — clicking the section header expands to show recent threads inline
- Section headers with labels ("Assistant" and "BA Assistant") plus a horizontal divider separating the two sections
- Assistant icon: a bold "level up" plus icon (RPG stat-upgrade style) — ties to XtraSkill branding. Use `Icons.add_circle` or similar bold plus from Material Icons as closest match

### Thread List Layout
- Each thread shows **title + last activity timestamp** — minimal, no previews or message counts
- Sorted by **most recent activity first** (last activity timestamp, newest at top)
- Same compact list style in both the sidebar expansion and the main `/assistant` content area — no card layout
- Empty state: friendly illustration with "Start your first conversation" call-to-action button

### Thread Creation Flow
- **Button + dialog** approach — a "New Thread" button opens a small dialog
- Dialog fields: **title** (required, empty field with placeholder hint) + **description** (optional)
- No project selector, no mode selector (simplified vs BA creation)
- After creation: **navigate immediately** into the new thread's conversation screen

### Delete Behavior
- Delete triggered via a **visible trash/delete icon** on each thread item (always visible, not hover-only)
- Undo via **bottom snackbar** with "Undo" action and 10-second countdown
- If deleting the currently-viewed thread: navigate back to `/assistant` thread list
- Thread is soft-deleted during undo window, hard-deleted after timeout

### Claude's Discretion
- Exact animation/transition for sidebar expansion
- Specific illustration choice for empty state
- Thread item spacing and typography details
- Exact placeholder text for creation dialog fields

</decisions>

<specifics>
## Specific Ideas

- The "plus" icon for Assistant is a recurring theme — it's the XtraSkill brand icon (like an RPG level-up/stat increase icon). Use this consistently across Assistant-related UI.
- Sidebar should feel like two distinct but visually cohesive sections, not a cluttered single list

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 63-navigation-thread-management*
*Context gathered: 2026-02-17*
