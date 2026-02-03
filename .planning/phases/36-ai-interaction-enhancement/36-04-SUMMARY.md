---
phase: 36-ai-interaction-enhancement
plan: 04
subsystem: frontend
tags: [source-attribution, chips, document-navigation, ui]
dependency_graph:
  requires: [36-01, 36-02]
  provides: ["SourceChips widget", "Message.documentsUsed", "source attribution UI"]
  affects: []
tech_stack:
  added: []
  patterns: ["collapsible UI sections", "Wrap widget for overflow"]
key_files:
  created:
    - frontend/lib/screens/conversation/widgets/source_chips.dart
  modified:
    - frontend/lib/models/message.dart
    - frontend/lib/providers/conversation_provider.dart
    - frontend/lib/screens/conversation/widgets/message_bubble.dart
    - frontend/lib/screens/conversation/conversation_screen.dart
decisions:
  - id: D-36-04-01
    decision: Bottom sheet preview for project-less threads
    rationale: Cannot navigate to /projects/:id/documents/:docId without project context
metrics:
  duration: 3 minutes
  completed: 2026-02-03
---

# Phase 36 Plan 04: Source Attribution UI Summary

**One-liner:** Collapsible SourceChips widget showing documents used in AI responses, with navigation to Document Viewer on tap

## What Was Built

### Task 1: SourceChips widget
- Created `frontend/lib/screens/conversation/widgets/source_chips.dart` with:
  - Collapsible header showing "X sources used" count
  - Expanded state reveals ActionChip for each document
  - Wrap layout handles overflow per PITFALL-13
  - Truncated filenames (25 chars) with full tooltip
  - Empty widget when no sources (SRC-04)

### Task 2: Message model and ConversationProvider updates
- Updated `frontend/lib/models/message.dart`:
  - Added `documentsUsed` field (List<DocumentSource>)
  - Default empty list preserves SRC-04 behavior
- Updated `frontend/lib/providers/conversation_provider.dart`:
  - Captures `event.documentsUsed` from MessageCompleteEvent
  - Sources flow from backend SSE to Message model

### Task 3: MessageBubble and ConversationScreen integration
- Updated `frontend/lib/screens/conversation/widgets/message_bubble.dart`:
  - Shows SourceChips for assistant messages when documentsUsed is non-empty
  - Added `projectId` parameter for navigation context
  - `_openDocument()` navigates to Document Viewer via GoRouter
  - `_showDocumentPreview()` shows bottom sheet for project-less threads
- Updated `frontend/lib/screens/conversation/conversation_screen.dart`:
  - Passes `widget.projectId` to MessageBubble

## Verification Results

| Check | Result |
|-------|--------|
| flutter analyze source_chips.dart | No issues |
| flutter analyze message.dart | No issues |
| flutter analyze conversation_provider.dart | No issues |
| flutter analyze message_bubble.dart | No issues |
| flutter analyze conversation_screen.dart | No issues |

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Message |
|------|---------|
| 56efadb | feat(36-04): create SourceChips widget for source attribution |
| 9a63d60 | feat(36-04): add documentsUsed to Message model and ConversationProvider |
| 31f9f4a | feat(36-04): display source chips and wire document navigation |

## Success Criteria Met

- [x] AI responses show source chips when documents were referenced (SRC-01)
- [x] Source chips display document names (SRC-02)
- [x] Clicking source chip opens Document Viewer (SRC-03)
- [x] No sources section shown if no documents used (SRC-04)
- [x] Wrap widget handles overflow (PITFALL-13)

## Next Phase Readiness

**Ready for human verification checkpoint**
- Source attribution complete from backend to UI
- Manual testing required to verify end-to-end flow
