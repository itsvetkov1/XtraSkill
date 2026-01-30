# Phase 10: Polish & Empty States - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Professional empty states with clear guidance + visual consistency improvements across all screens. This phase delivers:
1. Empty states for projects, threads, and documents lists
2. Home screen redesign with welcome message and action buttons
3. AI mode selection via ChoiceChips instead of typed responses
4. Visual polish: consistent dates, message readability, metadata badges, header consolidation

</domain>

<decisions>
## Implementation Decisions

### Home Screen Layout
- Personal greeting with user's display name: "Welcome back, [Name]"
- Primary + secondary button arrangement: "Start Conversation" large/prominent, "Browse Projects" smaller/secondary
- Show 2-3 most recent projects as quick access cards below the action buttons
- When no projects exist: show empty hint "No projects yet — create your first one!" instead of hiding the section

### Empty State Design
- Simple icon style: large themed icon (folder, chat bubble, document) — minimal, not illustrated
- Encouraging tone: "No projects yet — create your first one to get started!"
- Filled button for CTAs: primary color filled button for high visibility
- Consistent template: same layout everywhere (icon + message + button), only icon and message text vary per context

### Mode Selection UI
- ChoiceChip buttons for Meeting Mode / Document Refinement Mode
- Replace current typed "A"/"B" response with tappable chips

### Claude's Discretion
- Exact icon choices for each empty state
- ChoiceChip placement and styling details
- Date formatting implementation (POLISH-01 through POLISH-05)
- Message pill padding and font size adjustments (CONV-UI-02)
- Thread list preview text truncation (POLISH-03)
- Project card metadata badge styling (POLISH-04)
- Header consolidation approach (POLISH-02)

</decisions>

<specifics>
## Specific Ideas

No specific references — open to standard Material Design patterns for ChoiceChips, empty states, and home screen layouts.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-polish-and-empty-states*
*Context gathered: 2026-01-30*
