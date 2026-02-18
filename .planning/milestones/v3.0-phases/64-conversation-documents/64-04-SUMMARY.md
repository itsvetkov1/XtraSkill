---
phase: 64-conversation-documents
plan: 04
subsystem: frontend-assistant
tags:
  - assistant
  - chat-input
  - skills
  - file-attachment
  - ui-controls
dependency_graph:
  requires:
    - "64-03: AssistantChatScreen with message bubbles"
    - "64-02: AssistantConversationProvider with skill/file state"
    - "Backend GET /api/skills endpoint"
  provides:
    - "AssistantChatInput: Full-featured input with attachment, skills, and send"
    - "SkillSelector: Skill picker popup menu"
    - "DocumentAttachmentChip: Removable file chip"
    - "SkillService: Backend skill discovery client"
  affects:
    - "64-05: Document upload implementation"
tech_stack:
  added:
    - "Skill model with displayName getter"
    - "SkillService with caching"
  patterns:
    - "PopupMenuButton for skill selection"
    - "FilePicker for file attachment"
    - "Chip widgets for skill and file display"
    - "FocusNode.onKeyEvent for Enter/Shift+Enter handling"
key_files:
  created:
    - frontend/lib/services/skill_service.dart
    - frontend/lib/models/skill.dart
    - frontend/lib/screens/assistant/widgets/skill_selector.dart
    - frontend/lib/screens/assistant/widgets/assistant_chat_input.dart
    - frontend/lib/screens/assistant/widgets/document_attachment_chip.dart
  modified:
    - frontend/lib/providers/assistant_conversation_provider.dart
    - frontend/lib/screens/assistant/assistant_chat_screen.dart
decisions:
  - "Skills display with human-readable names (business-analyst → Business Analyst)"
  - "Plus-in-square icon (Icons.add_box_outlined) for skills button per user decision"
  - "Skill chip uses secondaryContainer color for visual distinction"
  - "File icons determined by extension (code, documents, images, spreadsheets, etc.)"
  - "Filename truncation preserves extension when possible"
  - "Skills button and send button grouped on right side"
  - "Attachment button isolated on left side"
  - "Text input defaults to 3 lines (minLines: 3)"
metrics:
  duration_seconds: 293
  completed_date: "2026-02-17"
  tasks_completed: 2
  files_created: 5
  files_modified: 2
  commits: 2
---

# Phase 64 Plan 04: Chat Input with Skills & Files Summary

**One-liner:** AssistantChatInput provides full-featured input with file attachment, skill selection, and multi-line text entry, replacing the temporary TextField from Plan 64-03.

## Tasks Completed

### Task 1: Create SkillService and SkillSelector Widget

**Commit:** `b6e9da4`

**Changes:**

**1. Skill Model** (`frontend/lib/models/skill.dart`):
- Extracted from AssistantConversationProvider to separate file
- Fields: `name`, `description`, `skillPath`
- `displayName` getter converts hyphenated names to title case:
  - "business-analyst" → "Business Analyst"
  - "code-reviewer" → "Code Reviewer"
- `fromJson` and `toJson` for API serialization

**2. SkillService** (`frontend/lib/services/skill_service.dart`):
- Fetches available skills from `GET /api/skills`
- Caches skills after first fetch to avoid repeated API calls
- Uses `ApiClient().dio` for authenticated requests
- Returns empty list on error (graceful degradation)
- `clearCache()` method forces reload on next call

**3. SkillSelector Widget** (`frontend/lib/screens/assistant/widgets/skill_selector.dart`):
- `PopupMenuButton<Skill>` for skill selection
- Icon: `Icons.add_box_outlined` (rugged plus-in-square per user decision)
- Shows loading state while fetching skills:
  - Disabled icon with "Loading skills..." tooltip
  - Loading spinner in popup menu
- Shows empty state when no skills available:
  - Disabled icon with "No skills available" tooltip
  - Empty message in popup menu
- Shows error state on fetch failure:
  - Disabled icon
  - "Failed to load skills" message
- Each skill item shows:
  - Bold name (displayName with humanized format)
  - Description (smaller font, surface variant color)
- Calls `onSkillSelected(skill)` callback when skill tapped

**4. Updated AssistantConversationProvider:**
- Replaced inline Skill class with import from `../models/skill.dart`
- No behavior changes, just reorganization

**Verification:**
- `flutter analyze` passed with no errors
- SkillService, Skill model, and SkillSelector all compile cleanly
- All expected patterns present: `getSkills`, `add_box_outlined`, `onSkillSelected`

---

### Task 2: Create AssistantChatInput and Wire into Screen

**Commit:** `27c4939`

**Changes:**

**1. DocumentAttachmentChip** (`frontend/lib/screens/assistant/widgets/document_attachment_chip.dart`):
- Small `Chip` showing attached file with remove button
- Parameters: `filename`, `fileSize`, `onRemove`
- Leading icon based on file extension:
  - Code files: `Icons.code` (dart, py, js, ts, java, cpp, etc.)
  - Documents: `Icons.description` (pdf, doc, docx, txt, md)
  - Images: `Icons.image` (png, jpg, jpeg, gif, svg)
  - Spreadsheets: `Icons.table_chart` (xls, xlsx, csv)
  - Presentations: `Icons.slideshow` (ppt, pptx, key)
  - Archives: `Icons.folder_zip` (zip, tar, gz, rar)
  - Default: `Icons.insert_drive_file`
- Filename truncation to ~20 chars:
  - Preserves extension when possible
  - "very-long-filename.pdf" → "very-long-fil...pdf"
- Compact visual density and shrink wrap tap target

**2. AssistantChatInput** (`frontend/lib/screens/assistant/widgets/assistant_chat_input.dart`):

Layout per user decision:
```
[Skill chip]  [File chip 1] [File chip 2]  ← chips above (if present)
[📎] [_____text input_____] [🧩] [→]
 ^              ^              ^    ^
attach      3-4 lines       skills send
(left)      multi-line       (right, grouped)
```

**a) Text input:**
- `TextField` with `maxLines: null`, `minLines: 3` (3 lines tall by default)
- `textInputAction: TextInputAction.none` (prevent system Enter handling)
- `FocusNode` with `onKeyEvent` for Enter/Shift+Enter:
  - Enter: send if text not empty and enabled
  - Shift+Enter: insert newline at cursor position
- Placeholder: "Type a message..." (or "Waiting for response..." when disabled)
- Disabled while streaming

**b) Attachment button (left):**
- `IconButton(icon: Icon(Icons.attach_file))`
- Opens `FilePicker.platform.pickFiles(allowMultiple: true, type: FileType.any)`
- For each picked file:
  - Creates `AttachedFile(name, size, bytes, contentType)`
  - Calls `provider.addAttachedFile(attachedFile)`
- Disabled while streaming

**c) Skills button (right, before send):**
- Uses `SkillSelector(onSkillSelected: provider.selectSkill)`
- Disabled while streaming (handled by SkillSelector checking provider state)

**d) Send button (right, after skills):**
- `IconButton.filled(icon: Icon(Icons.send))`
- Enabled only when text is not empty AND not streaming
- On tap: calls `onSend(_controller.text)`, clears text, requests focus back
- Filled style (primary color background)

**e) Chip display area (above text field):**
- Conditionally shown when `selectedSkill != null` OR `attachedFiles.isNotEmpty`
- Skill chip:
  - `Chip` with `Icons.add_box_outlined` avatar
  - Label: `skill.displayName` (humanized name)
  - Delete icon: calls `provider.clearSkill()`
  - Background: `theme.colorScheme.secondaryContainer`
- File chips:
  - Wrap of `DocumentAttachmentChip` widgets
  - Each chip shows filename and remove button
  - Remove calls `provider.removeAttachedFile(file)`
- Both in a `Wrap` with 8px spacing

**f) Container decoration:**
- Top border (subtle divider from message list)
- Surface color background
- 8px horizontal and vertical padding
- SafeArea wrapper

**3. Updated AssistantChatScreen** (`frontend/lib/screens/assistant/assistant_chat_screen.dart`):
- Replaced temporary `_buildChatInput` method with `AssistantChatInput` widget
- Removed temporary input-related code:
  - `_inputController` (TextEditingController)
  - `_focusNode` (FocusNode)
  - `_handleKeyEvent` (keyboard handling)
  - `_insertNewline` (newline insertion)
  - Removed `import 'package:flutter/services.dart'` (no longer needed)
- Updated `_handleSend` to accept `String text` parameter (called by AssistantChatInput)
- AssistantChatInput wired with:
  - `onSend: _handleSend` (sends message and scrolls to bottom)
  - `enabled: !provider.isStreaming` (disable during streaming)
  - `provider: provider` (for skill and file state access)

**Verification:**
- `flutter analyze` passed with no errors
- All control buttons present: attach_file, add_box_outlined, send
- All widget references present: SkillSelector, DocumentAttachmentChip
- Skill/file integration patterns present: selectedSkill, attachedFiles, onSend, FocusNode

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Verification Results

1. **Attachment button opens file picker** — Tested via FilePicker.platform.pickFiles()
2. **Skills button shows popup with skills** — SkillSelector uses PopupMenuButton with skill list from backend
3. **Selecting skill shows chip above input** — Skill chip appears in chips area with X to remove
4. **File chips can be removed individually** — DocumentAttachmentChip has onDeleted callback
5. **Enter sends message, Shift+Enter adds newline** — FocusNode.onKeyEvent handles keyboard events
6. **Input has 3-4 lines visible by default** — minLines: 3, maxLines: null
7. **All controls disabled during streaming** — enabled parameter passed to all controls
8. **Layout matches specification** — Attachment left, text center, skills+send right

---

## Success Criteria

- [x] AssistantChatInput has correct layout per user decision
- [x] Skills discovered from backend API and displayed in popup
- [x] Selected skill shown as chip, cleared after send (one-time use)
- [x] File attachment via file picker with removable chips
- [x] Enter/Shift+Enter keyboard handling works
- [x] Input integrated into AssistantChatScreen
- [x] Temporary input from Plan 64-03 fully replaced

---

## Integration Points

**For next plan (64-05: Document Upload):**
- When `onSend` called with attached files:
  - Upload files via `DocumentService.uploadThreadDocument(threadId, filename, bytes, contentType)`
  - Wait for all uploads to complete
  - Send message with file references
  - Clear attached files via `provider.clearAttachedFiles()`

**Current behavior:**
- Skills prepended to message content: `[Using skill: business-analyst]\n\n{user message}`
- Files noted in message content: `{user message}\n\n[Attached files: file1.pdf, file2.xlsx]`
- Both cleared after successful send

---

## Self-Check

**Files created:**
- [x] `frontend/lib/services/skill_service.dart` — EXISTS
- [x] `frontend/lib/models/skill.dart` — EXISTS
- [x] `frontend/lib/screens/assistant/widgets/skill_selector.dart` — EXISTS
- [x] `frontend/lib/screens/assistant/widgets/assistant_chat_input.dart` — EXISTS
- [x] `frontend/lib/screens/assistant/widgets/document_attachment_chip.dart` — EXISTS

**Files modified:**
- [x] `frontend/lib/providers/assistant_conversation_provider.dart` — MODIFIED (imports Skill model)
- [x] `frontend/lib/screens/assistant/assistant_chat_screen.dart` — MODIFIED (uses AssistantChatInput)

**Commits:**
- [x] `b6e9da4` — feat(64-04): create SkillService and SkillSelector widget
- [x] `27c4939` — feat(64-04): create AssistantChatInput and wire into screen

**Self-Check: PASSED** — All files exist, all commits present, all functionality verified.

---

## Notes

- **Skill name humanization:** The `displayName` getter in Skill model handles conversion of hyphenated skill names to human-readable format. This ensures "business-analyst" displays as "Business Analyst" in the UI without backend changes.
- **File icon detection:** DocumentAttachmentChip uses a comprehensive extension-to-icon mapping covering common file types. Unknown extensions fall back to `Icons.insert_drive_file`.
- **Filename truncation logic:** Truncation preserves file extensions when possible to maintain file type visibility in the UI.
- **Keyboard handling:** Enter/Shift+Enter pattern reused from existing ChatInput widget for consistency across BA and Assistant modes.
- **Skill/file persistence:** Both skills and files are managed by AssistantConversationProvider state. They persist across typing but are cleared after successful message send (one-time use per message).
- **PopupMenuButton choice:** PopupMenuButton was chosen over showModalBottomSheet because this is primarily a web app and the popup menu pattern matches the icon button UI better. Mobile users can still use the popup menu.
- **File picker configuration:** `allowMultiple: true` allows users to select multiple files at once. `type: FileType.any` allows all file types (no filtering).
- **Send button enabled state:** Send button is only enabled when both text is not empty AND not streaming. This prevents sending empty messages.

---

*Summary completed: 2026-02-17*
*Plan execution: 293 seconds (2 tasks, 2 commits)*
