# Phase 66: Skill Browser UI - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Browsable dialog where users see all available skills with names, descriptions, and features, and select one to use in their next message. Selection shows as a removable chip in the chat input area. Single-skill selection only.

</domain>

<decisions>
## Implementation Decisions

### Skill Card Layout
- Grid of cards layout (not list/timeline)
- Each card shows: emoji icon, skill name, 1-2 line description, and 2-3 feature bullets
- Each skill gets a relevant emoji icon (e.g. business analyst, QA, prompt enhancer)
- Responsive grid: 3 columns on desktop, 2 on tablet, 1 on mobile

### Browser Dialog Style
- Bottom sheet that slides up from bottom
- Draggable: starts at ~50% screen height, user can drag up to ~90% or down to dismiss
- Header: drag handle + "Choose a Skill" title
- Stays as bottom sheet on all screen sizes (no adaptation to centered dialog on desktop)

### Selection Chip Design
- Chip appears above the text field (in a row above the message input area)
- Chip displays: emoji + full skill name + X dismiss button (e.g. "📊 Business Analyst ×")
- Filled chip style: solid accent color background with white text — prominent
- Tapping chip body does nothing — only X button is interactive for dismissal
- Single-select: selecting a new skill replaces the current one

### States & Transitions
- Loading state: skeleton cards shimmer in the grid shape while skills load
- Error/empty state: friendly message "Couldn't load skills" with a retry button
- Open/close animation: custom spring animation (bouncy, playful feel)
- Selection feedback: card briefly highlights/scales on tap, then sheet slides down (~300ms delay)

### Claude's Discretion
- Exact skeleton card shimmer implementation
- Spring animation parameters (stiffness, damping)
- Card corner radius, shadows, and spacing values
- Exact responsive breakpoints for column count changes
- How emoji icons map to specific skills

</decisions>

<specifics>
## Specific Ideas

- Cards should show enough info to distinguish skills without needing to open info popup (name + description + features)
- The bottom sheet should feel natural on mobile — drag handle for muscle memory
- Selection should feel immediate — brief highlight then close, not a multi-step process

</specifics>

<deferred>
## Deferred Ideas

- Multi-skill selection for complex workflows — user expressed interest in selecting multiple skills at once, deferred to future phase (changes SEL-03 single-select requirement)

</deferred>

---

*Phase: 66-skill-browser-ui*
*Context gathered: 2026-02-18*
