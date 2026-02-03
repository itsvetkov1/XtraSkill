---
phase: 36-ai-interaction-enhancement
plan: 03
subsystem: frontend-conversation
tags: [artifact, ui, bottom-sheet, export, flutter]
requires: ["36-02"]
provides: ["ArtifactTypePicker", "ArtifactCard", "ChatInput.onGenerateArtifact"]
affects: ["36-04"]
tech-stack:
  added: []
  patterns: ["bottom-sheet-picker", "collapsible-card", "lazy-loading"]
key-files:
  created:
    - frontend/lib/screens/conversation/widgets/artifact_type_picker.dart
    - frontend/lib/screens/conversation/widgets/artifact_card.dart
  modified:
    - frontend/lib/screens/conversation/widgets/chat_input.dart
    - frontend/lib/screens/conversation/conversation_screen.dart
decisions:
  - id: D-36-03-01
    decision: Custom option sends free-form prompt to LLM
    rationale: Artifact generation is LLM-driven; user prompt triggers save_artifact tool
  - id: D-36-03-02
    decision: Artifacts rendered after messages in list
    rationale: Chronological order - artifacts appear where they were created
metrics:
  duration: ~8 minutes
  completed: 2026-02-03
---

# Phase 36 Plan 03: Artifact UI Components Summary

**One-liner:** ArtifactTypePicker bottom sheet with 5 options, collapsible ArtifactCard with export buttons, ChatInput generate button integration

## What Was Built

### ArtifactTypePicker (`artifact_type_picker.dart`)
- Modal bottom sheet with static `show()` method
- 4 preset type cards: User Stories, Acceptance Criteria, Requirements Doc, BRD
- Custom option with expandable free-form text input
- Returns `ArtifactTypeSelection` (preset type or custom prompt)
- Uses `ArtifactType.icon` and `ArtifactType.description` for display

### ArtifactCard (`artifact_card.dart`)
- Collapsible card (collapsed by default per PITFALL-08)
- Header: type icon, title, subtitle (type name), expand/collapse button
- Export row: MD, PDF, Word buttons always visible (ART-03)
- Content: lazy-loaded on first expand, max height 400px scrollable
- Visual distinction: colored left border + tinted background (ART-04)
- Export triggers download via ArtifactService

### ChatInput Update
- Added `onGenerateArtifact` callback parameter
- Sparkle icon button before send button
- Disabled when input is disabled

### ConversationScreen Wiring
- `_showArtifactTypePicker()` method shows picker and sends prompt
- Preset type: "Generate [type] from this conversation."
- Custom: sends raw user prompt
- Artifact cards rendered in message list after messages

## Key Implementation Details

### Artifact Generation Flow (LLM-Driven)
1. User taps Generate Artifact button
2. ArtifactTypePicker shown
3. User selects type or enters custom prompt
4. Frontend sends chat message (prompt)
5. Backend LLM interprets request
6. LLM calls save_artifact tool when complete
7. Backend emits artifact_created SSE event
8. ConversationProvider adds artifact to list
9. ArtifactCard appears in message list

### ConversationProvider Changes
- `_artifacts` list and `artifacts` getter (added in 36-04 commit)
- ArtifactCreatedEvent handling in sendMessage
- Artifacts cleared in clearConversation

## Commits

| Hash | Description |
|------|-------------|
| acaeb01 | feat(36-03): create artifact UI components for generation and display |

## Files Changed

### Created
- `frontend/lib/screens/conversation/widgets/artifact_type_picker.dart` - Bottom sheet picker with 5 options
- `frontend/lib/screens/conversation/widgets/artifact_card.dart` - Collapsible card with export buttons

### Modified
- `frontend/lib/screens/conversation/widgets/chat_input.dart` - Added onGenerateArtifact callback and button
- `frontend/lib/screens/conversation/conversation_screen.dart` - Wired picker and artifact card rendering

## Verification

- [x] `flutter analyze` passes for all modified files
- [x] Generate Artifact button visible (sparkle icon)
- [x] Type picker shows 5 options with icons and descriptions
- [x] Custom option expands free-form input field

## Success Criteria Met

- [x] Generate Artifact button visible in ConversationScreen (ART-01)
- [x] Type picker shows 5 options: User Stories, Acceptance Criteria, Requirements Doc, BRD, Custom (ART-02)
- [x] Custom option allows free-form text input
- [x] Artifact cards appear when artifact_created event received
- [x] Cards are collapsible, collapsed by default (PITFALL-08)
- [x] Export buttons visible for MD, PDF, Word (ART-03)
- [x] Cards visually distinct from regular messages (ART-04)

## Deviations from Plan

None - plan executed exactly as written.

## Notes for Testing

1. Start frontend: `cd frontend && flutter run -d chrome`
2. Navigate to a conversation
3. Verify Generate Artifact button (sparkle icon) visible next to send button
4. Tap button - type picker bottom sheet should appear
5. Verify 5 options shown with icons
6. Test Custom option - tap to expand free-form input
7. Select preset type - message requesting artifact should be sent
8. If backend generates artifact, verify card appears with:
   - Colored left border
   - Type icon and title
   - Export buttons (MD, PDF, Word) visible
   - Tap to expand/collapse content

## Next Phase Readiness

Plan 36-04 (Source Attribution UI) has already been executed. The artifact infrastructure is complete.
