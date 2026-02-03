# Phase 36: AI Interaction Enhancement - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can generate artifacts from conversations and see which project documents informed AI responses. Artifact types include User Stories, Acceptance Criteria, BRD, and Custom. Source attribution shows document chips that link to Document Viewer.

</domain>

<decisions>
## Implementation Decisions

### Artifact Generation Flow
- Generate Artifact button in chat input area (next to send button or in input toolbar)
- Bottom sheet type picker slides up with tappable cards
- Each type card shows icon + name + description for full context
- Custom type shows predefined templates (recent custom prompts) plus free-form input field

### Artifact Card Styling
- Colored left border + subtle background tint to distinguish from regular messages
- Use theme accent color for border/background (consistent with brand)
- Collapsed by default to keep chat tidy
- Collapsed state shows: type icon + title + "Tap to expand"

### Export Functionality
- Inline icon buttons (MD, PDF, Word) in a row at bottom of card
- Export icons visible even when card is collapsed for quick access
- File naming: type + timestamp (e.g., "user_stories_2026-02-03.md")
- SnackBar feedback with 'Open' action after successful export

### Source Attribution Display
- Collapsible section at bottom of AI message ("View sources" link)
- Collapsed state shows: document icon + "X sources used"
- Expanded state shows outlined chips with document icon + filename
- Tapping chip opens Document Viewer in bottom sheet preview (with option to go full screen)

### Claude's Discretion
- Exact placement of Generate Artifact button within input area
- Icons for each artifact type
- Bottom sheet preview height for Document Viewer
- Loading states during artifact generation
- Error handling for export failures

</decisions>

<specifics>
## Specific Ideas

- Per PITFALL-05: Verify citations match actual documents (no hallucination)
- Per PITFALL-08: Collapsed artifact cards with lazy render for performance
- Export should work offline if content already generated
- Source chips only appear when documents were actually referenced (SRC-04)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 36-ai-interaction-enhancement*
*Context gathered: 2026-02-03*
