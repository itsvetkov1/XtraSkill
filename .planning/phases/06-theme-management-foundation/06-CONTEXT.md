# Phase 6: Theme Management Foundation - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can switch between light and dark themes with persistent preferences that load instantly on app startup. This phase establishes theme infrastructure and Settings page integration. Custom color schemes, per-project themes, and advanced theme customization are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Visual Design - Overall Feel
- Professional/corporate aesthetic prioritizing readability and credibility
- High contrast approach suitable for enterprise SaaS usage
- Focus on clarity over playfulness

### Visual Design - Dark Mode
- Dark gray background (#121212 - #1E1E1E range, Material Design 3 approach)
- NOT true black (#000000) to reduce eye strain during long sessions
- Softer visual experience compared to stark black backgrounds

### Visual Design - Color Palette
- Blue accent color for interactive elements (classic professional: #1976D2 range)
- Traditional corporate blue for buttons, links, highlights
- Universally recognized as clickable/interactive

### Visual Design - Surface Elevation
- Subtle shadows only (no borders)
- Light mode: soft drop shadows for depth
- Dark mode: lighter surface colors using Material 3 elevation tint approach
- Clean, layered visual hierarchy without border clutter

### UI Placement - Toggle Location
- Settings page only (no quick-access in app bar or sidebar)
- Theme switching requires navigation to Settings screen
- Avoids UI clutter, keeps interface clean

### UI Placement - Control Type
- Standard switch toggle (Light ↔ Dark)
- Familiar binary on/off pattern common in mobile settings
- Professional, unambiguous interaction

### UI Placement - Label Format
- Simple label: "Dark Mode" with switch
- Light theme = switch off, Dark theme = switch on
- No icons, no verbose descriptions, straightforward presentation

### UI Placement - Visual Feedback
- Instant theme switch with no animation
- No fade transitions, no confirmation SnackBars
- Maximum responsiveness, no visual distractions

### Default Behavior - First Launch
- Always default to light theme for new users
- Predictable, consistent starting experience
- Users must manually switch to dark if preferred
- Does NOT follow system preference initially

### Default Behavior - System Preference Changes
- Ignore OS theme changes after app launch
- User's explicit choice takes precedence over system settings
- Once user opens app, theme stays as chosen regardless of OS changes
- Respects user autonomy and intentional selections

### Default Behavior - Persistence Timing
- Save theme preference immediately on toggle
- Write to SharedPreferences the instant user flips switch
- No delays, no debouncing, guaranteed immediate persistence

### Default Behavior - Startup Loading Strategy
- Assume last-used theme and render immediately
- Cache/assume theme to eliminate wait time during startup
- Correct theme if assumption wrong (rare edge case, brief flicker acceptable)
- Optimizes for common case: prevents white flash on dark mode (SET-06)

### Claude's Discretion
- Exact shade selection within color ranges (e.g., precise hex for dark gray #121212 vs #1E1E1E)
- Typography scaling and font weights for light vs dark themes
- Shadow opacity and blur radius for elevation effects
- Text color contrast ratios (as long as they meet WCAG AA standards)
- Error state handling during SharedPreferences failures

</decisions>

<specifics>
## Specific Ideas

- Material Design 3 elevation approach for dark mode surface tinting
- SharedPreferences for cross-platform persistence (Flutter standard)
- Requirement SET-06 explicitly mentions preventing white flash on dark mode startup

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. No requests for custom themes, per-project theming, or advanced color customization emerged.

</deferred>

---

*Phase: 06-theme-management-foundation*
*Context gathered: 2026-01-29*
