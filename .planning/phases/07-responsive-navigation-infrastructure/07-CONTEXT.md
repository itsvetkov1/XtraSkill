# Phase 7: Responsive Navigation Infrastructure - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Persistent sidebar navigation visible on all screens with responsive behavior (desktop ≥900px always-visible, mobile <600px hamburger). Includes breadcrumb navigation, contextual back arrows, current location highlighting, and sidebar state persistence.

</domain>

<decisions>
## Implementation Decisions

### Navigation state memory
- Sidebar collapsed/expanded state persists across browser sessions (SharedPreferences)
- Expandable sidebar sections (e.g., Projects list) persist their expanded/collapsed states
- App does NOT restore last navigation location — always starts at home screen
- Scroll positions in lists do NOT persist — lists start at top when navigated to

### Claude's Discretion
- Sidebar visual design (width, icons vs text, collapse animation, section grouping)
- Tablet breakpoint behavior (900px to 600px gap handling)
- Breadcrumb interaction details (click behavior, truncation, mobile treatment)
- Exact animation timing and easing curves
- Implementation of state persistence storage format

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for sidebar, breadcrumbs, and back navigation. User focused on state persistence behavior:
- Sidebar state = remember
- Section states = remember
- Last page location = don't remember
- Scroll positions = don't remember

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-responsive-navigation-infrastructure*
*Context gathered: 2026-01-29*
