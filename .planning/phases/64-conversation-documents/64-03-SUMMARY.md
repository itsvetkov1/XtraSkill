---
phase: 64-conversation-documents
plan: 03
subsystem: frontend-assistant
tags:
  - assistant
  - chat-ui
  - message-bubbles
  - streaming
  - markdown
dependency_graph:
  requires:
    - "64-02: AssistantConversationProvider and MarkdownMessage"
    - "63-01: Assistant navigation and routing"
  provides:
    - "AssistantChatScreen: Main chat UI for Assistant threads"
    - "AssistantMessageBubble: Message bubble with markdown and copy/retry"
    - "AssistantStreamingMessage: Streaming with thinking timer"
  affects:
    - "64-04: Chat input will replace temporary TextField"
tech_stack:
  patterns:
    - "Consumer pattern for provider state"
    - "Auto-scroll on message updates with post-frame callback"
    - "Thinking timer with Timer.periodic for elapsed time display"
    - "Synchronous clipboard for Safari compatibility"
key_files:
  created:
    - frontend/lib/screens/assistant/assistant_chat_screen.dart
    - frontend/lib/screens/assistant/widgets/assistant_message_bubble.dart
    - frontend/lib/screens/assistant/widgets/assistant_streaming_message.dart
  modified:
    - frontend/lib/main.dart
decisions:
  - "Temporary chat input using TextField + IconButton (will be replaced in Plan 64-04)"
  - "File attachment chips removed (Message model has no metadata field yet)"
  - "Thinking timer updates every second via Timer.periodic"
  - "Auto-scroll uses post-frame callback to ensure layout is complete"
  - "Retry button only shows on last message when error is present"
metrics:
  duration_seconds: 229
  completed_date: "2026-02-17"
  tasks_completed: 2
  files_created: 3
  files_modified: 1
  commits: 2
---

# Phase 64 Plan 03: Assistant Chat UI Assembly Summary

**One-liner:** AssistantChatScreen provides dedicated chat UI for Assistant threads with markdown message bubbles, streaming with thinking timer, and temporary text input.

## Tasks Completed

### Task 1: Create AssistantChatScreen and Message Widgets

**Commit:** `4a0402d`

**Changes:**

**1. AssistantMessageBubble** (`frontend/lib/screens/assistant/widgets/assistant_message_bubble.dart`):
- User messages: Primary color bubble aligned right, plain text
- Assistant messages: Surface-colored bubble aligned left with:
  - MarkdownMessage widget for content rendering
  - Copy button (IconButton) with synchronous clipboard call (Safari-compatible)
  - Retry button (TextButton) shown only when `onRetry` callback provided
  - Controls row at bottom with copy + retry buttons
- Max width: 80% of screen width
- Bubble styling: rounded corners with flat corner on message side (same as BA MessageBubble)
- No metadata field support (Message model doesn't have metadata yet)

**2. AssistantStreamingMessage** (`frontend/lib/screens/assistant/widgets/assistant_streaming_message.dart`):
- StatefulWidget with Timer.periodic for elapsed time display
- Shows thinking indicator with elapsed time when `text` is empty and `statusMessage` is null:
  ```
  [spinner] Thinking... (5s)
  ```
- Elapsed time calculated from `thinkingStartTime` parameter, updates every second
- Shows status message when set (e.g., "Searching documents...")
- Renders accumulated text via MarkdownMessage when `text` is not empty
- Timer disposal in dispose()
- Timer restarts on `thinkingStartTime` change, stops when cleared

**3. AssistantChatScreen** (`frontend/lib/screens/assistant/assistant_chat_screen.dart`):
- Scaffold with AppBar (thread title) and Column layout
- On init: loads thread via `AssistantConversationProvider.loadThread(threadId)`
- Loading state: full-screen spinner
- Not-found state (404): ResourceNotFoundState with "Back to Assistant" button
- Error state (full-screen): error icon with retry button
- Error banner (with partial content): MaterialBanner above message list with dismiss + retry

**Message list:**
- ListView.builder with normal order (oldest at top, newest at bottom)
- Auto-scroll on new messages and streaming updates via post-frame callback
- SelectionArea wrapper enables text selection
- Empty state: centered icon + "Start a conversation" text
- For each message: renders AssistantMessageBubble
- After messages: renders AssistantStreamingMessage if streaming
- Retry button on last message if error present and message is assistant role

**Temporary chat input (will be replaced in 64-04):**
- Row with TextField + IconButton(Icons.send)
- Enter sends, Shift+Enter newline (reuses FocusNode.onKeyEvent pattern)
- Multi-line (maxLines: 4, minLines: 1)
- Disabled while streaming
- On send: calls `provider.sendMessage(text)`, clears input, focuses input, scrolls to bottom
- No artifact generation button, no file attachment button

**Auto-scroll:**
- Uses ScrollController.animateTo with post-frame callback
- Triggered on message changes and streaming updates
- 300ms animation with Curves.easeOut

**No BA-specific elements:**
- No AppBar mode badge
- No budget warning banner
- No artifact type picker
- No mode selector chips
- No provider indicator
- No "Add to Project" button
- No source chips

**Verification:**
- `flutter analyze` passed with no errors
- Zero BA-specific references confirmed
- All widget references present (MarkdownMessage, AssistantStreamingMessage, AssistantMessageBubble)

---

### Task 2: Wire AssistantChatScreen into Router and Provider Tree

**Commit:** `69bb80b`

**Changes:**

**1. Updated router** in `frontend/lib/main.dart`:
- Changed `/assistant/:threadId` route from `ConversationScreen` to `AssistantChatScreen`
- Before:
  ```dart
  return ConversationScreen(
    projectId: null,
    threadId: threadId,
  );
  ```
- After:
  ```dart
  return AssistantChatScreen(
    threadId: threadId,
  );
  ```

**2. Added AssistantConversationProvider to MultiProvider:**
- Added after ConversationProvider in provider list
- Created inline with `create: (_) => AssistantConversationProvider()`
- No constructor parameters needed (defaults to AIService() and ThreadService())

**3. Added imports:**
- `import 'providers/assistant_conversation_provider.dart';`
- `import 'screens/assistant/assistant_chat_screen.dart';`

**4. Preserved existing routing:**
- ConversationScreen still used for `/chats/:threadId` route (project-less threads)
- ConversationScreen still used for `/projects/:id/threads/:threadId` route (project threads)
- No changes to BA conversation routing

**Verification:**
- `flutter analyze` passed with no errors
- AssistantChatScreen and AssistantConversationProvider references present
- ConversationScreen still used for Chats and Projects (2 references)

---

## Deviations from Plan

**1. [Rule 1 - Bug] Removed file attachment chips**
- **Found during:** Task 1 implementation
- **Issue:** Plan specified showing attached files from `message.metadata['attached_files']`, but Message model has no metadata field
- **Fix:** Removed file attachment display logic from AssistantMessageBubble
- **Impact:** File chips can be added when Message model is extended with metadata field
- **Files modified:** `frontend/lib/screens/assistant/widgets/assistant_message_bubble.dart`
- **Decision:** Simplification — file attachments are a future enhancement, not blocking for v1 chat UI

---

## Verification Results

1. **flutter analyze** — Passed for all new files with no errors
2. **BA-specific elements check** — Zero occurrences confirmed (no artifacts, budget, mode selector, provider indicator, source chips, add-to-project)
3. **Widget references** — AssistantMessageBubble and AssistantStreamingMessage both present in AssistantChatScreen
4. **Routing** — AssistantChatScreen wired to /assistant/:threadId, ConversationScreen preserved for Chats and Projects
5. **Provider setup** — AssistantConversationProvider registered in MultiProvider

---

## Success Criteria

- [x] AssistantChatScreen is the screen for /assistant/:threadId (not ConversationScreen)
- [x] Messages render with markdown formatting via MarkdownMessage
- [x] Streaming shows thinking indicator with elapsed time
- [x] Copy and retry controls work on assistant messages
- [x] Clean UI — no BA artifacts, budget, mode, project elements
- [x] Existing BA routing is unchanged (Chats and Projects still use ConversationScreen)
- [x] Auto-scroll on new messages and streaming updates
- [x] Temporary chat input works for sending messages (will be replaced in 64-04)

---

## Integration Points

**For next plan (64-04: Chat Input with Skills & Files):**
- Replace temporary TextField input with AssistantChatInput widget
- Add skill selector dropdown/chips
- Add file attachment button with picker
- Remove temporary `_buildChatInput` method from AssistantChatScreen
- Use AssistantChatInput with callbacks for send, skill selection, file attachment

**Current temporary input behavior:**
- Enter sends, Shift+Enter newline
- Disabled while streaming
- No skill selection
- No file attachment
- Single IconButton.filled for send

---

## Self-Check

**Files created:**
- [x] `frontend/lib/screens/assistant/assistant_chat_screen.dart` — EXISTS
- [x] `frontend/lib/screens/assistant/widgets/assistant_message_bubble.dart` — EXISTS
- [x] `frontend/lib/screens/assistant/widgets/assistant_streaming_message.dart` — EXISTS

**Files modified:**
- [x] `frontend/lib/main.dart` — MODIFIED (AssistantChatScreen route, AssistantConversationProvider registered)

**Commits:**
- [x] `4a0402d` — feat(64-03): create AssistantChatScreen with message widgets
- [x] `69bb80b` — feat(64-03): wire AssistantChatScreen into router and provider tree

**Self-Check: PASSED** — All files exist, all commits present, all functionality verified.

---

## Notes

- **Thinking timer precision:** Timer updates every 1 second via Timer.periodic. This is sufficient granularity for user feedback without excessive re-renders.
- **Auto-scroll timing:** Uses post-frame callback to ensure Flutter layout is complete before calculating scroll position. This prevents scroll position from being stale.
- **Retry button placement:** Only shown on the last message when an error is present. This matches BA ConversationScreen pattern and avoids retry buttons on old messages.
- **Synchronous clipboard:** Copy button uses synchronous `Clipboard.setData()` call without async/await to maintain Safari compatibility (from Phase 11 decision).
- **Temporary input replacement:** Plan 64-04 will create AssistantChatInput widget with skill selection and file attachment, replacing the temporary TextField input in this plan.
- **Message metadata:** When Message model is extended with metadata field (for file attachments, thinking time, etc.), file chips can be added back to AssistantMessageBubble.

---

*Summary completed: 2026-02-17*
*Plan execution: 229 seconds (2 tasks, 2 commits)*
