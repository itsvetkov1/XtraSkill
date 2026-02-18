---
phase: 64-conversation-documents
plan: 02
subsystem: frontend-assistant
tags:
  - assistant
  - conversation
  - streaming
  - markdown
  - syntax-highlighting
dependency_graph:
  requires:
    - "62-01: Backend thread API with thread_type discriminator"
    - "62-03: Backend chat endpoint routing based on thread_type"
    - "63-01: Assistant navigation and routing"
  provides:
    - "AssistantConversationProvider: SSE streaming chat state for Assistant threads"
    - "MarkdownMessage: Formatted AI response rendering with syntax highlighting"
    - "Skill selection: Prepend context to messages transparently"
    - "File attachment tracking: Ready for document upload integration"
  affects:
    - "64-03: Chat UI will use AssistantConversationProvider and MarkdownMessage"
tech_stack:
  added:
    - flutter_markdown: "Markdown rendering"
    - flutter_highlight: "Syntax highlighting for code blocks"
    - markdown: "Custom markdown element builders"
  patterns:
    - "Provider-based state management with ChangeNotifier"
    - "SSE streaming with AIService.streamChat()"
    - "Auto-retry on first error with 2-second delay"
    - "Theme-aware code highlighting (github/vs2015)"
key_files:
  created:
    - frontend/lib/providers/assistant_conversation_provider.dart
    - frontend/lib/screens/assistant/widgets/markdown_message.dart
  modified:
    - frontend/pubspec.yaml
decisions:
  - "Skill selection is one-time per message (clears after send)"
  - "File attachments append to message content as references (not actual upload yet)"
  - "Auto-retry once on streaming error after 2-second delay"
  - "Thinking timer tracks elapsed time from stream start to first text delta"
  - "MarkdownMessage uses HighlightView for code blocks (not Text with background)"
  - "Code blocks get positioned copy button (Stack with Positioned widget)"
metrics:
  duration_seconds: 172
  completed_date: "2026-02-17"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
  commits: 2
---

# Phase 64 Plan 02: Assistant Conversation Provider & Markdown Rendering Summary

**One-liner:** AssistantConversationProvider manages SSE streaming chat state for Assistant threads with skill prepending, while MarkdownMessage renders AI responses with syntax-highlighted code blocks.

## Tasks Completed

### Task 1: Add Dependencies and Create AssistantConversationProvider

**Commit:** `eb83d2e`

**Changes:**
- Added `flutter_markdown` and `flutter_highlight` dependencies to pubspec.yaml
- Created `AssistantConversationProvider` class — simplified version of BA `ConversationProvider`
- Included SSE streaming via `AIService.streamChat()`
- Implemented skill selection with transparent prepending to user messages
- Added file attachment tracking (list of `AttachedFile` objects)
- Implemented auto-retry on first streaming error with 2-second delay
- Added thinking timer (`_thinkingStartTime`) for elapsed time display
- Stripped all BA-specific logic: no artifacts, budget checking, mode selection, document attribution

**State fields:**
- `Thread? _thread` — current thread
- `List<Message> _messages` — conversation messages
- `String _streamingText` — accumulated during streaming
- `String? _statusMessage` — e.g., "Thinking..."
- `bool _isStreaming` — streaming state
- `bool _loading` — initial load
- `String? _error` — error message
- `bool _isNotFound` — 404 state
- `String? _lastFailedMessage` — for retry
- `bool _hasPartialContent` — partial content from interrupted stream
- `Skill? _selectedSkill` — skill to prepend (one-time use)
- `List<AttachedFile> _attachedFiles` — pending files
- `DateTime? _thinkingStartTime` — thinking indicator start
- `bool _hasAutoRetried` — auto-retry flag

**Core methods:**
- `loadThread(String threadId)` — loads thread and messages via ThreadService
- `sendMessage(String content)` — sends with SSE streaming, prepends skill context if selected, clears skill/files after send
- `retryLastMessage()` — retry last failed message
- `clearConversation()` — reset all state
- `clearError()` — clear error state
- `selectSkill(Skill skill)` / `clearSkill()` — manage skill selection
- `addAttachedFile()` / `removeAttachedFile()` / `clearAttachedFiles()` — manage file attachments

**Model classes:**
- `Skill` — name, description, skillPath fields with `fromJson`
- `AttachedFile` — name, size, bytes (Uint8List?), contentType fields

**Auto-retry pattern:**
- On streaming error: if `!_hasAutoRetried`, wait 2 seconds, retry if still in error state
- Reset `_hasAutoRetried` on successful send

**Verification:**
- `flutter analyze` passed with no issues
- No BA-specific references (artifacts, budget, mode selector)
- All core methods present

---

### Task 2: Create MarkdownMessage Widget with Syntax Highlighting

**Commit:** `458636d`

**Changes:**
- Created `MarkdownMessage` widget for rendering AI responses as formatted markdown
- Used `MarkdownBody` from `flutter_markdown` with `selectable: true`
- Created custom `CodeElementBuilder` extending `MarkdownElementBuilder` for syntax highlighting
- Used `HighlightView` from `flutter_highlight` for code blocks
- Theme-aware highlighting: `githubTheme` for light mode, `vs2015Theme` for dark mode
- Added "Copy code" button (IconButton) positioned in top-right of each code block
- Configured `MarkdownStyleSheet` from theme for headers, tables, lists, blockquotes
- Handled links via `url_launcher` (already in pubspec)
- Handled edge cases: empty content returns `SizedBox.shrink()`, streaming partial markdown renders gracefully
- Added `markdown` package as explicit dependency (required for custom builder)

**Widget structure:**
```dart
class MarkdownMessage extends StatelessWidget {
  final String content;
  final bool isStreaming;

  // Returns MarkdownBody with:
  // - Custom CodeElementBuilder for syntax highlighting
  // - Theme-based StyleSheet
  // - Link tap handler
}

class CodeElementBuilder extends MarkdownElementBuilder {
  // Returns Stack with:
  // - HighlightView (syntax-highlighted code)
  // - Positioned copy button
}
```

**Styling:**
- Paragraphs: bodyLarge with fontSize 15, height 1.4
- Headings: h1/h2/h3 with appropriate sizes
- Code: monospace font with surfaceContainerHighest background
- Code blocks: rounded container (8px) with 12px padding
- Blockquotes: left border with primary color
- Tables: bordered with outlineVariant

**Verification:**
- `flutter analyze` passed with no issues
- All key imports present (MarkdownBody, HighlightView, github/vs2015 themes)
- Copy-code functionality with SnackBar confirmation

---

## Deviations from Plan

**None.** Plan executed exactly as written. All requirements met without modifications.

---

## Verification Results

1. **flutter analyze** — Passed for all new files with no errors
2. **AssistantConversationProvider methods** — All required methods present (sendMessage, loadThread, retryLastMessage, selectSkill, addAttachedFile)
3. **MarkdownMessage rendering** — Uses flutter_markdown with syntax highlighting via flutter_highlight
4. **No BA-specific logic** — Confirmed no artifacts, budget, or mode selection in AssistantConversationProvider
5. **Dependencies installed** — flutter_markdown, flutter_highlight, and markdown in pubspec.yaml

---

## Success Criteria

- [x] AssistantConversationProvider manages streaming chat state cleanly (no BA logic)
- [x] Skill selection prepends to prompt transparently and clears after send
- [x] MarkdownMessage renders headers, code blocks, tables, lists with proper formatting
- [x] Code blocks have syntax highlighting with theme-appropriate colors
- [x] Auto-retry on first streaming error after 2-second delay
- [x] Thinking indicator start time tracked for elapsed time display

---

## Integration Points

**For next plans (64-03: Chat UI):**
- Use `AssistantConversationProvider` in MultiProvider setup
- Use `MarkdownMessage` widget for assistant message bubbles (instead of Text widget)
- Display thinking indicator with elapsed time from `provider.thinkingStartTime`
- Show selected skill chip (if `provider.selectedSkill != null`)
- Show attached file chips (if `provider.attachedFiles.isNotEmpty`)
- Handle streaming state with `provider.isStreaming` and `provider.streamingText`

**Provider usage pattern:**
```dart
// In chat screen
final provider = context.watch<AssistantConversationProvider>();

// Load thread
await provider.loadThread(threadId);

// Send message
await provider.sendMessage(content);

// Render messages
for (var message in provider.messages) {
  if (message.role == MessageRole.assistant) {
    MarkdownMessage(content: message.content)
  }
}

// Render streaming text
if (provider.isStreaming) {
  MarkdownMessage(content: provider.streamingText, isStreaming: true)
}
```

---

## Self-Check

**Files created:**
- [x] `frontend/lib/providers/assistant_conversation_provider.dart` — EXISTS
- [x] `frontend/lib/screens/assistant/widgets/markdown_message.dart` — EXISTS

**Files modified:**
- [x] `frontend/pubspec.yaml` — MODIFIED (flutter_markdown, flutter_highlight, markdown added)

**Commits:**
- [x] `eb83d2e` — feat(64-02): add AssistantConversationProvider with streaming and skill support
- [x] `458636d` — feat(64-02): create MarkdownMessage widget with syntax highlighting

**Self-Check: PASSED** — All files exist, all commits present, all functionality verified.

---

## Notes

- **flutter_markdown discontinued warning:** Package is marked as discontinued in favor of flutter_markdown_plus, but current version (0.7.7+1) is stable and sufficient for our needs. Migration to flutter_markdown_plus can be deferred to future maintenance.
- **Skill prepending:** Skill context is prepended to the message content BEFORE sending to backend, but the user message bubble shows only the original user content (without skill annotation). This keeps the UI clean while providing context to the AI.
- **File attachment:** Current implementation tracks file metadata but doesn't upload yet. Full file upload integration will come in document-related plans.
- **Auto-retry once:** Balances resilience with avoiding infinite retry loops. User can manually retry after auto-retry if needed.
- **Thinking timer:** Starts when streaming begins, clears on first text delta. This allows UI to show "Thinking for 5 seconds..." before text appears.

---

*Summary completed: 2026-02-17*
*Plan execution: 172 seconds (2 tasks, 2 commits)*
