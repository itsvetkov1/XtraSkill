---
phase: 42-silent-artifact-generation
plan: 02
subsystem: frontend-state
tags: [flutter, provider, streaming, artifact-generation, state-management]

dependency-graph:
  requires:
    - phase-42-01 (backend artifact_generation flag and silent mode endpoint)
  provides:
    - AIService.streamChat artifactGeneration parameter
    - ConversationProvider.generateArtifact() separate code path
    - Generation-specific state (isGeneratingArtifact, generatingArtifactType)
    - Retry/cancel mechanism for failed generations
    - Error source distinction (lastOperationWasGeneration)
  affects:
    - 42-03 (UI buttons will call generateArtifact to trigger silent generation)

tech-stack:
  added: []
  patterns:
    - Separate state machine for artifact generation (no shared streaming state)
    - Collection-if for conditional request body fields
    - Error source tagging for UI differentiation

key-files:
  created: []
  modified:
    - frontend/lib/services/ai_service.dart
    - frontend/lib/providers/conversation_provider.dart
    - frontend/test/unit/providers/conversation_provider_test.mocks.dart

decisions:
  - id: PITFALL-06-enforcement
    description: "generateArtifact() uses completely separate state from sendMessage()"
    rationale: "Prevents blank message bubbles, streaming UI conflicts, and state machine interference"
  - id: state-clear-on-artifact-created
    description: "Generation state clears on ArtifactCreatedEvent, not MessageCompleteEvent"
    rationale: "PITFALL-05: artifact appears before stream ends; user sees result immediately"
  - id: error-source-tagging
    description: "_lastOperationWasGeneration distinguishes generation vs chat errors"
    rationale: "UI can show generation-specific retry button vs chat retry button"

metrics:
  duration: ~4 minutes
  completed: 2026-02-05
---

# Phase 42 Plan 02: Frontend generateArtifact Code Path Summary

**One-liner:** Separate generateArtifact() method on ConversationProvider with dedicated state machine, retry/cancel, and artifactGeneration flag on AIService.streamChat

## What Was Done

### Task 1: Add artifactGeneration parameter to AIService.streamChat
- Added `{bool artifactGeneration = false}` optional named parameter to `streamChat()`
- When true, includes `'artifact_generation': true` in the SSE POST request body
- Uses Dart collection-if syntax so the field is omitted when false (backward compatible)
- Event parsing unchanged -- backend suppresses text_delta events in silent mode, client handles gracefully

### Task 2: Add generateArtifact() method and generation state to ConversationProvider
- **5 new state variables:** `_isGeneratingArtifact`, `_generatingArtifactType`, `_lastGenerationPrompt`, `_lastGenerationArtifactType`, `_lastOperationWasGeneration`
- **4 new getters:** `isGeneratingArtifact`, `generatingArtifactType`, `canRetryGeneration`, `lastOperationWasGeneration`
- **generateArtifact(prompt, artifactType):** Completely separate code path from sendMessage()
  - Does NOT set `_isStreaming` (would trigger streaming UI)
  - Does NOT add to `_messages` (would create blank bubbles)
  - Does NOT accumulate `_streamingText` (not used in silent mode)
  - Sets `_isGeneratingArtifact` and `_generatingArtifactType` for dedicated loading UI
  - Clears state on `ArtifactCreatedEvent` (not `MessageCompleteEvent`)
  - Guard: `if (_isGeneratingArtifact || _isStreaming) return` prevents concurrent operations
- **retryLastGeneration():** Replays last failed generation prompt
- **cancelGeneration():** Clears all generation state cleanly
- **Updated clearConversation():** Resets all 5 new state variables
- **Updated clearError():** Resets generation error state
- **Updated sendMessage():** Sets `_lastOperationWasGeneration = false` at start
- **Updated MockAIService:** Added `artifactGeneration` parameter to match new signature

## Architecture Notes

The critical architectural constraint (PITFALL-06) is enforced: `generateArtifact()` shares ZERO mutable state with `sendMessage()`. The only shared state is `_error` (which is tagged by `_lastOperationWasGeneration` for disambiguation) and `_artifacts` (which both paths can add to).

State flow:
```
generateArtifact() called
  -> _isGeneratingArtifact = true
  -> streamChat(artifactGeneration: true)
  -> ArtifactCreatedEvent arrives
  -> _artifacts.add(artifact)
  -> _isGeneratingArtifact = false
  -> UI updates via notifyListeners()
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated MockAIService for test compilation**
- **Found during:** Task 2 verification
- **Issue:** Generated mock `conversation_provider_test.mocks.dart` had stale `streamChat` signature missing `artifactGeneration` parameter
- **Fix:** Updated mock to include `{bool? artifactGeneration = false}` and pass it in `Invocation.method`
- **Files modified:** `frontend/test/unit/providers/conversation_provider_test.mocks.dart`
- **Commit:** 58989a0

## Verification Results

| Check | Status |
|-------|--------|
| streamChat has artifactGeneration parameter | Pass |
| generateArtifact() separate from sendMessage() | Pass |
| Does NOT set _isStreaming, add messages, or accumulate text | Pass |
| isGeneratingArtifact getter works | Pass |
| generatingArtifactType getter works | Pass |
| canRetryGeneration works | Pass |
| cancelGeneration clears state | Pass |
| Existing tests pass (38/40) | Pass (2 pre-existing failures) |
| Flutter analyze | Pass - no issues |

**Note:** 2 pre-existing test failures exist in `conversation_provider_test.dart` (lines 351, 366) where tests expect `streamingText` to be empty after error, but the code intentionally preserves partial content per PITFALL-01. These failures predate this plan and are unrelated to our changes.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 81e0f0d | feat | Add artifactGeneration parameter to AIService.streamChat |
| 58989a0 | feat | Add generateArtifact method and generation state to ConversationProvider |

## Next Phase Readiness

Plan 42-02 provides the complete frontend code path for silent artifact generation. The next plan (42-03) can wire up UI buttons to call `provider.generateArtifact(prompt, type)` and display the `isGeneratingArtifact` / `generatingArtifactType` state in loading indicators.
