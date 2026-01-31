# Phase 22: Frontend Provider UI - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Add provider selection to Settings and display which provider a conversation uses in the chat UI. New conversations use the user's default provider; existing conversations use their stored provider. This phase covers UI only — backend provider support is complete from Phase 21.

</domain>

<decisions>
## Implementation Decisions

### Settings Layout
- Dropdown selector (compact, tap to expand)
- Placed under "Preferences" section in Settings
- Options show provider name only (Claude, Gemini, DeepSeek) — no model details
- Silent save on change — no snackbar or confirmation

### Model Indicator Design
- Position: Above the input field (between message list and input box)
- Style: Icon + text (provider logo/icon alongside name)
- Alignment: Left aligned
- Interaction: Not tappable — purely informational

### Provider Colors
- Claude: Anthropic orange/coral (~#D97706)
- Gemini: Google blue (~#4285F4)
- DeepSeek: Teal/cyan (~#00B8D4)
- Color application: Icon tint only — text stays neutral

### Claude's Discretion
- Exact icon assets or icon representation approach
- Spacing and typography details
- Dark mode color adjustments if needed
- State transitions (skipped in discussion)

</decisions>

<specifics>
## Specific Ideas

No specific product references mentioned — open to standard Material/Flutter patterns for dropdown and indicator components.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 22-frontend-provider-ui*
*Context gathered: 2026-01-31*
