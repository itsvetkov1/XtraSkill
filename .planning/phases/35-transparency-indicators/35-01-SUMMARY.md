---
phase: 35-transparency-indicators
plan: 01
subsystem: conversation
tags: [budget-tracking, token-usage, threshold-warnings, ui-feedback]

dependency-graph:
  requires: []
  provides:
    - budget-provider
    - budget-warning-banner
    - exhausted-state-blocking
  affects: [35-02]

tech-stack:
  added: []
  patterns:
    - "API-provided token counts per PITFALL-04 (no local estimates)"
    - "Percentage-only display per BUD-05 (no monetary amounts)"
    - "Consumer2 for multiple provider consumption"

key-files:
  created:
    - frontend/lib/providers/budget_provider.dart
    - frontend/lib/screens/conversation/widgets/budget_warning_banner.dart
  modified:
    - frontend/lib/main.dart
    - frontend/lib/screens/conversation/conversation_screen.dart

decisions:
  - id: DEC-3501-01
    decision: "Use API costPercentage from TokenUsage, not local calculation"
    rationale: "PITFALL-04 mandates API-provided counts to avoid estimation errors"
  - id: DEC-3501-02
    decision: "Show percentage only in banners, no dollar amounts"
    rationale: "BUD-05 requirement - budget is percentage-based display"
  - id: DEC-3501-03
    decision: "Exhausted banner cannot be dismissed"
    rationale: "Critical state should remain visible while viewing history"
  - id: DEC-3501-04
    decision: "Budget banner positioned above error banner"
    rationale: "Budget status is more important context for user actions"

metrics:
  duration: 12 minutes
  completed: 2026-02-03
---

# Phase 35 Plan 01: Budget Warning Banners Summary

**One-liner:** Token budget tracking with threshold-based warning banners (80%, 95%, 100%) using API-provided usage data and input blocking at exhaustion

## What Was Built

### BudgetProvider (New)
- BudgetStatus enum with four states: normal, warning, urgent, exhausted
- Fetches usage from /auth/usage API via AuthService.getUsage()
- Calculates percentage from TokenUsage.costPercentage (API-provided)
- Threshold detection: 80% warning, 95% urgent, 100% exhausted
- Auto-refreshes on construction
- Manual refresh() method for on-demand updates

### BudgetWarningBanner Widget (New)
- Stateful widget with dismissible state tracking
- Warning (80%): Yellow/tertiary banner - "You've used X% of your token budget"
- Urgent (95%): Orange banner - "Almost at limit - limited messages remaining"
- Exhausted (100%): Red/error banner - "Budget exhausted - unable to send messages"
- Dismiss action on warning/urgent only (exhausted stays visible)
- Resets dismissed state when status changes to higher severity

### ConversationScreen Updates
- Imports BudgetProvider and BudgetWarningBanner
- Uses Consumer2 for both ConversationProvider and BudgetProvider
- Refreshes budget on screen mount (initState)
- Shows BudgetWarningBanner above error banner
- ChatInput disabled when budget status is exhausted
- Refreshes budget after successful message send

### main.dart Updates
- Added BudgetProvider import
- Registered BudgetProvider in MultiProvider list after AuthProvider

## Commits

| Commit | Description |
|--------|-------------|
| e93c6ce | feat(35-01): create BudgetProvider with threshold detection |
| a2fef19 | feat(35-01): create BudgetWarningBanner widget |
| 50b685a | feat(35-01): integrate budget state into ConversationScreen |

## Verification Results

- [x] Static analysis passes: `flutter analyze` - no errors on modified files
- [x] BudgetProvider fetches from /auth/usage API via _authService.getUsage()
- [x] BudgetStatus enum has all four states (normal, warning, urgent, exhausted)
- [x] BudgetWarningBanner shows distinct messages for each threshold
- [x] ChatInput disabled when status is exhausted
- [x] No monetary amounts displayed anywhere (percentage only)

## Success Criteria Met

| Requirement | Status |
|-------------|--------|
| BUD-01: Warning banner at 80% shows percentage message | DONE |
| BUD-02: Warning banner at 95% shows "Almost at limit" | DONE |
| BUD-03: At 100%, clear "Budget exhausted" state visible | DONE |
| BUD-04: Exhausted state allows viewing but blocks sending | DONE |
| BUD-05: Budget display shows percentage only (no dollars) | DONE |

## Deviations from Plan

None - plan executed exactly as written.

## Testing Recommendations

To manually verify:
1. Start the app and navigate to a conversation
2. Check console/network to verify /auth/usage API is called on mount
3. Modify backend to return usage at 85% - verify yellow warning banner appears
4. Dismiss the banner - verify it hides
5. Modify backend to return usage at 97% - verify orange urgent banner appears
6. Dismiss the banner - verify it hides
7. Modify backend to return usage at 100% - verify:
   - Red "Budget exhausted" banner appears
   - Banner cannot be dismissed (no dismiss button)
   - Chat input is disabled (greyed out, cannot type)
   - Message history can still be scrolled
8. Modify backend to return usage at 50% - verify no banner shown

## Next Phase Readiness

Plan 35-02 (Mode Indicator) can proceed independently. No blockers.
