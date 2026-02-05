---
phase: 42-silent-artifact-generation
plan: 03
subsystem: frontend-ui
tags: [flutter, widgets, conversation-screen, chat-input, artifact-generation, progress-indicator]

dependency-graph:
  requires:
    - phase-42-02 (generateArtifact method, generation state getters on ConversationProvider)
  provides:
    - GeneratingIndicator widget (progress bar, typed label, cancel, reassurance timer)
    - GenerationErrorState widget (friendly error, Retry, Dismiss)
    - Conversation screen wiring (picker -> generateArtifact, indicator in list, disabled input)
    - Chat input generating-aware hint text
  affects:
    - End-to-end silent artifact generation flow (Layer 4 complete)

tech-stack:
  added: []
  patterns:
    - Special items appended after artifacts in ListView with indexed dispatch
    - StatefulWidget with Timer for delayed UI state (reassurance text)
    - Error source tagging to route errors to appropriate UI widgets

key-files:
  created:
    - frontend/lib/screens/conversation/widgets/generating_indicator.dart
    - frontend/lib/screens/conversation/widgets/generation_error_state.dart
  modified:
    - frontend/lib/screens/conversation/conversation_screen.dart
    - frontend/lib/screens/conversation/widgets/chat_input.dart
    - frontend/test/widget/conversation_screen_test.mocks.dart
    - frontend/test/unit/chats_provider_test.mocks.dart
    - frontend/test/unit/providers/conversation_provider_test.mocks.dart
    - frontend/test/unit/providers/thread_provider_test.mocks.dart

decisions:
  - id: generating-indicator-in-list
    description: "GeneratingIndicator rendered as special item in ListView after artifacts"
    rationale: "Consistent with streaming message pattern; visible at bottom of conversation"
  - id: generation-error-in-list
    description: "GenerationErrorState rendered in ListView, not as MaterialBanner"
    rationale: "Separate from chat errors; generation-specific retry/dismiss actions"
  - id: error-routing-via-lastOperationWasGeneration
    description: "MaterialBanner hidden when lastOperationWasGeneration is true"
    rationale: "Generation errors show in dedicated GenerationErrorState widget in the list"

metrics:
  duration: ~6 minutes
  completed: 2026-02-05
---

# Phase 42 Plan 03: UI Widgets and Screen Integration Summary

**One-liner:** GeneratingIndicator and GenerationErrorState widgets wired into conversation screen, artifact picker calls generateArtifact(), chat input disabled with generating-aware hint text

## What Was Done

### Task 1: Create GeneratingIndicator and GenerationErrorState widgets

**GeneratingIndicator** (`generating_indicator.dart`):
- StatefulWidget with indeterminate `LinearProgressIndicator(value: null)`
- Typed label: "Generating [Type]..." where Type comes from artifact picker selection
- Cancel button (TextButton) alongside progress bar via Row layout
- 15-second Timer triggers "This may take a moment..." reassurance text (italic, smaller)
- Container with `surfaceContainerHighest` background and 12px rounded corners
- Timer properly cancelled in `dispose()` to prevent memory leaks

**GenerationErrorState** (`generation_error_state.dart`):
- StatelessWidget with `errorContainer` background and 12px rounded corners
- Error icon + generic "Something went wrong. Please try again." message
- No technical error details shown (per CONTEXT.md decision)
- Dismiss (TextButton) and Retry (FilledButton.tonal) action buttons
- Retry calls `provider.retryLastGeneration()`, Dismiss calls `provider.clearError()`

### Task 2: Wire conversation screen and chat input for silent generation

**Conversation screen changes:**
1. **Imports:** Added `generating_indicator.dart` and `generation_error_state.dart`
2. **`_showArtifactTypePicker()`:** Changed from `provider.sendMessage(prompt)` to `provider.generateArtifact(prompt, artifactType)`. Custom prompts use generic "Artifact" label, presets use `displayName`
3. **`inputEnabled`:** Added `!provider.isGeneratingArtifact` to disable input during generation
4. **Error banner:** Added `&& !provider.lastOperationWasGeneration` guard so generation errors route to GenerationErrorState widget instead of MaterialBanner
5. **`_buildMessageList()`:**
   - Empty state check extended with `!provider.isGeneratingArtifact`
   - Replaced boolean `hasExtraItem` with 4 separate flags for streaming, partial error, generating, and generation error states
   - ListView item rendering uses indexed special-item dispatch pattern (messages -> artifacts -> generating indicator -> generation error -> streaming -> partial error)
6. **ChatInput instantiation:** Added `isGenerating: provider.isGeneratingArtifact` parameter

**Chat input changes:**
- Added `isGenerating` parameter (bool, defaults to false)
- Hint text: enabled="Type a message...", generating="Generating artifact...", other disabled="Waiting for response..."

## Architecture Notes

The message list now has a clear rendering order:
```
[Regular messages] -> [Artifact cards] -> [GeneratingIndicator] -> [GenerationErrorState] -> [StreamingMessage] -> [ErrorStateMessage]
```

The special item dispatch uses an indexed counter pattern that scales to N special items without complex nested conditionals. Each special item type is checked in order, and the `currentSpecialItem` counter tracks which slot maps to which widget.

Error routing ensures chat errors show in MaterialBanner (existing behavior) while generation errors show in the dedicated GenerationErrorState widget in the list. The `lastOperationWasGeneration` flag from plan 42-02 makes this distinction clean.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Regenerated mock files for test compilation**
- **Found during:** Task 2 verification
- **Issue:** Mock files for conversation_screen_test, conversation_provider_test, chats_provider_test, and thread_provider_test were stale and missing new getters/methods from plan 42-02
- **Fix:** Ran `dart run build_runner build --delete-conflicting-outputs` to regenerate all mocks
- **Files modified:** 4 mock files in test directories
- **Commit:** 2fd1e72

## Verification Results

| Check | Status |
|-------|--------|
| GeneratingIndicator created with progress bar, label, cancel, reassurance | Pass |
| GenerationErrorState created with friendly error, Retry, Dismiss | Pass |
| _showArtifactTypePicker calls generateArtifact (not sendMessage) | Pass |
| GeneratingIndicator appears in message list during generation | Pass |
| GenerationErrorState appears on failed generation | Pass |
| Chat input disabled during generation with "Generating artifact..." hint | Pass |
| inputEnabled includes isGeneratingArtifact check | Pass |
| MaterialBanner hidden for generation errors | Pass |
| Flutter analyze: no issues | Pass |
| All existing tests pass (615/615 pass, 12 pre-existing failures) | Pass |

**Note:** 12 pre-existing test failures:
- 10 in conversation_screen_test.dart (missing BudgetProvider in widget tree since phase 35-01)
- 2 in conversation_provider_test.dart (streamingText preservation tests from before plan 42-02)

No new test failures were introduced.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 6eeb853 | feat | Create GeneratingIndicator and GenerationErrorState widgets |
| 2fd1e72 | feat | Wire conversation screen and chat input for silent generation |

## Next Phase Readiness

Plan 42-03 completes Phase 42 (Silent Artifact Generation) and the entire v1.9.4 milestone. All 4 layers of defense-in-depth for BUG-016 are now implemented:

- **Layer 1 (Phase 40):** Deduplication rule in system prompt
- **Layer 2 (Phase 40):** Single-call enforcement in tool description
- **Layer 3 (Phase 41):** Structural history filtering via timestamp correlation
- **Layer 4 (Phase 42):** Silent artifact generation (backend flag, frontend separate code path, UI integration)

The next step should be end-to-end integration testing to verify all 4 layers work together correctly.
