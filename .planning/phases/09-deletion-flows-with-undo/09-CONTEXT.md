# Phase 9: Deletion Flows with Undo - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can delete projects, threads, documents, and messages with confirmation dialogs and undo capability. Deletion includes optimistic UI updates with rollback on error. Backend performs cascade deletes maintaining referential integrity.

</domain>

<decisions>
## Implementation Decisions

### Confirmation Dialogs
- Summary cascade info only ("This will delete all threads and messages") — no exact counts
- Neutral visual style — standard dialog colors, no red/warning treatment
- Generic item references ("Delete this project?") — no item names in dialog text
- Button labels: "Delete" / "Cancel"

### Claude's Discretion
- Undo SnackBar timing and visual treatment (10-second window per requirements)
- Delete button placement (swipe, context menu, detail screen icons)
- Post-delete navigation routing (parent screen vs stay in place)
- Optimistic UI animation/transition style
- Error state handling when backend delete fails

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for undo behavior, delete triggers, and navigation.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-deletion-flows-with-undo*
*Context gathered: 2026-01-30*
