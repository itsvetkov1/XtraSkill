# Phase 42: Silent Artifact Generation - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Button-triggered artifact generation produces an artifact card with a loading indicator and no chat message bubbles, completely bypassing conversation history accumulation. This is Layer 4 of the deduplication defense-in-depth strategy. The frontend needs a new `generateArtifact()` code path separate from `sendMessage()`, and the backend needs an endpoint that creates artifacts WITHOUT saving messages.

</domain>

<decisions>
## Implementation Decisions

### Loading experience
- Progress bar replaces the preset button area during generation (buttons disappear, progress bar takes their place)
- Indeterminate horizontal progress bar with label below
- Label shows specific artifact type: "Generating User Stories..." (matches the button clicked)
- After ~15 seconds, add reassurance text below: "This may take a moment..."
- Progress bar and label remain until generation completes or fails

### Error experience
- On failure, the progress bar area transforms into an error state (same location)
- Error message is friendly and generic: "Something went wrong. Please try again."
- No technical details shown to user (no "Network timeout" or "API rate limit")
- Two action buttons: "Retry" (re-triggers same artifact generation) and "Dismiss" (returns to normal preset buttons)
- Unlimited retries allowed — no cap on retry attempts

### Button interaction
- Chat input field is DISABLED during silent generation (user cannot send typed messages while waiting)
- Cancel button shown alongside progress bar — user can abort in-progress generation
- Cancel returns to normal state (preset buttons + active chat input)
- On success: preset buttons return immediately (no success confirmation animation)
- Artifact card appears at bottom of chat message list (natural scroll position, no auto-scroll if user scrolled up)

### Claude's Discretion
- Progress bar animation style and color
- Exact timing for reassurance text threshold
- Cancel implementation (abort HTTP request vs ignore response)
- How disabled chat input is visually communicated (grayed out, placeholder text, etc.)
- Artifact card appearance animation (fade in, slide in, or instant)

</decisions>

<specifics>
## Specific Ideas

- The button area transformation should feel like a state swap — buttons out, progress in, buttons back — not a layout shift
- "Generating User Stories..." label should match the exact button text the user clicked
- Error state lives in the same physical space as the progress bar — no jumping around

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 42-silent-artifact-generation*
*Context gathered: 2026-02-05*
