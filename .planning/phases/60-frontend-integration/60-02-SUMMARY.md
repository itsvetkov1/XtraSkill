---
phase: 60-frontend-integration
plan: 02
subsystem: conversation-ui-provider-display
tags: [thread-info, provider-display, experimental-ui]
dependency_graph:
  requires:
    - phase-60-01-provider-registration
  provides:
    - thread-info-bottom-sheet
    - provider-indicator-model-display
  affects:
    - conversation-screen
    - provider-indicator-widget
tech_stack:
  added: []
  patterns:
    - modal-bottom-sheet
    - conditional-ui-rendering
    - two-line-text-layout
key_files:
  created: []
  modified:
    - frontend/lib/screens/conversation/conversation_screen.dart
    - frontend/lib/screens/conversation/widgets/provider_indicator.dart
decisions:
  - title: "Thread Info Access via Info Button"
    rationale: "Placed info button before edit button in AppBar for easy access to thread metadata including provider information"
  - title: "Model Name Display in Provider Indicator"
    rationale: "Show model name as second line in provider indicator for Claude Code providers while maintaining single-line layout for existing providers"
  - title: "Date Format in Thread Info"
    rationale: "Use ISO-like format (YYYY-MM-DD HH:MM) for consistency with backend timestamp formatting"
metrics:
  duration: 109
  tasks_completed: 2
  files_modified: 2
  commits: 2
  completed_at: 2026-02-15
---

# Phase 60 Plan 02: Thread Info UI with Provider Display Summary

**Add thread info panel showing provider details in conversation screen, enabling users to identify which provider was used for each thread.**

## Objective Achieved

Users can now see which provider was used for a thread via an info button in the conversation AppBar. The thread info bottom sheet displays provider name with experimental badge for Claude Code providers, model name, mode, and created date. The provider indicator below chat input now shows model name as a second line for Claude Code providers.

## Tasks Completed

### Task 1: Add Thread Info Bottom Sheet with Provider Display
**Commit:** `986d87e`

**Changes (conversation_screen.dart):**
- Added import for `constants.dart` to access ProviderConfigs
- Added info icon button (Icons.info_outline) to AppBar actions before the edit button
- Implemented `_showThreadInfo()` method that displays modal bottom sheet with:
  - Thread title
  - Provider name with colored icon
  - Experimental badge for Claude Code providers (secondaryContainer styling)
  - Model name (conditional, only shown for providers with modelName)
  - Mode with icon and display name
  - Created date formatted as YYYY-MM-DD HH:MM
- Implemented `_formatDate()` helper method for date formatting
- Material 3 styling with ListTile components for consistent UI

**Bottom Sheet Structure:**
- SafeArea wrapper for device compatibility
- Column layout with CrossAxisAlignment.start
- Header with "Thread Info" title (titleMedium, fontWeight 600)
- ListTile for each metadata field (title, provider, model, mode, created)
- Experimental badge uses secondaryContainer/onSecondaryContainer colors
- Dense ListTile layout for compact display

**Files Modified:**
- `frontend/lib/screens/conversation/conversation_screen.dart`

### Task 2: Update Provider Indicator to Show Model Name
**Commit:** `598cfaf`

**Changes (provider_indicator.dart):**
- Changed text layout from single Text widget to Column
- Column properties: `crossAxisAlignment: CrossAxisAlignment.start`, `mainAxisSize: MainAxisSize.min`
- Display name shown in bodySmall style (existing behavior)
- Model name conditionally shown when `config.modelName != null`
- Model name uses labelSmall style with outline color for visual hierarchy
- Existing providers (Claude, Gemini, DeepSeek) with null modelName render identically to before (single line)
- Claude Code providers show two lines: provider name + model name

**Visual Result:**
- Claude Code (SDK): Line 1 "Claude Code (SDK)", Line 2 "Claude Sonnet 4.5"
- Claude Code (CLI): Line 1 "Claude Code (CLI)", Line 2 "Claude Sonnet 4.5"
- Existing providers: Single line with provider name only (no regression)

**Files Modified:**
- `frontend/lib/screens/conversation/widgets/provider_indicator.dart`

## Verification Results

**conversation_screen.dart Verification:**
- ✅ Import for constants.dart exists
- ✅ Info icon button in AppBar actions (before edit button)
- ✅ `_showThreadInfo()` method with bottom sheet implementation
- ✅ `_formatDate()` helper method exists
- ✅ No provider-specific streaming logic added (no `if (provider == 'claude-code-sdk')` checks)
- ✅ `flutter analyze` passes cleanly

**provider_indicator.dart Verification:**
- ✅ Uses Column for text layout (supports optional second line)
- ✅ Conditionally shows modelName only when non-null
- ✅ Existing providers with null modelName render identically to before (single line)
- ✅ `flutter analyze` passes cleanly

**Provider-Agnostic Streaming Verification:**
- ✅ No provider checks in _buildMessageList() method
- ✅ StreamingMessage, MessageBubble, and error widgets remain provider-agnostic
- ✅ All streaming display logic works identically for all 5 providers

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

**Thread Info Flow:**
1. User taps info button (info_outline icon) in conversation AppBar
2. `_showThreadInfo()` retrieves thread from ConversationProvider
3. `ProviderConfigs.getConfig(thread.modelProvider)` resolves provider config
4. Modal bottom sheet displays with SafeArea and Material 3 styling
5. Experimental badge conditionally rendered for Claude Code providers
6. Model name conditionally rendered when available
7. Created date formatted with `_formatDate()` helper

**Provider Indicator Update:**
1. `ProviderConfigs.getConfig(provider)` resolves config (existing behavior)
2. Column layout replaces single Text widget
3. Display name shown on first line (bodySmall style)
4. Model name shown on second line if available (labelSmall style, outline color)
5. For existing providers (modelName: null), only first line renders (no visual change)
6. For Claude Code providers (modelName: "Claude Sonnet 4.5"), both lines render

**Why No Provider-Specific Streaming Logic:**
- Phase 58/59 adapters already normalize all provider events to ChatEvent format
- Existing UI components (MessageBubble, StreamingMessage, ThinkingIndicator) consume ChatEvent types
- Adding providers to registration + thread info UI enables full functionality without streaming changes
- Provider indicator automatically works with new providers via ProviderConfigs.getConfig()

**Material 3 Styling Patterns:**
- Experimental badge: secondaryContainer background, onSecondaryContainer text
- Thread info header: titleMedium font, fontWeight 600
- ListTile dense layout for compact vertical spacing
- Consistent icon-title-subtitle pattern across all metadata fields

## Next Steps

**Manual E2E Testing (add to TESTING-QUEUE.md):**
- TC-60-07: Tap info button in conversation with Claude Code (SDK) thread, verify experimental badge shows
- TC-60-08: Tap info button in conversation with Claude Code (CLI) thread, verify experimental badge shows
- TC-60-09: Tap info button in conversation with existing provider (Claude/Gemini/DeepSeek), verify no experimental badge
- TC-60-10: Verify provider indicator shows two lines for Claude Code providers (name + model)
- TC-60-11: Verify provider indicator shows single line for existing providers (name only)
- TC-60-12: Verify thread info displays mode and created date correctly

**Phase 61 - Quality Evaluation:**
- Use thread info to track which provider was used per thread
- Compare quality metrics across providers
- Experimental badge provides visual indicator for users during evaluation

## Self-Check: PASSED

**Created Files:**
- ✅ `.planning/phases/60-frontend-integration/60-02-SUMMARY.md` (this file)

**Modified Files:**
- ✅ `frontend/lib/screens/conversation/conversation_screen.dart` exists
  - Contains import for constants.dart
  - Contains info icon button in AppBar
  - Contains `_showThreadInfo()` method with showModalBottomSheet
  - Contains `_formatDate()` helper method
  - No provider-specific streaming checks

- ✅ `frontend/lib/screens/conversation/widgets/provider_indicator.dart` exists
  - Contains Column layout for text
  - Contains conditional modelName rendering
  - No visual regression for existing providers

**Commits:**
- ✅ `986d87e` exists: feat(60-02): add thread info bottom sheet with provider display
- ✅ `598cfaf` exists: feat(60-02): update provider indicator to show model name

All claims verified. Self-check passed.
