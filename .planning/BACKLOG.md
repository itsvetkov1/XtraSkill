# Product Backlog

**Project:** Business Analyst Assistant
**Created:** 2026-01-30
**Source:** APP-FEATURES-AND-FLOWS.md critique analysis

---

## How to Use This Backlog

- **Status:** `Open` | `In Progress` | `Done` | `Wont Do`
- **Priority:** `Critical` | `High` | `Medium` | `Low`
- Pick tickets by priority, update status as you work

---

## Critical Priority

### THREAD-001: Add retry mechanism for failed AI messages
**Status:** Open
**Component:** Conversation Screen

**User Story:**
As a user, I want to retry a failed AI request without retyping my message, so that network issues don't waste my effort.

**Problem:**
Error banner only shows "Dismiss" - no way to retry. User must retype their message if AI response fails.

**Acceptance Criteria:**
- [ ] Error banner shows "Dismiss | Retry" actions
- [ ] Retry resends the last user message
- [ ] ConversationProvider stores last sent message for retry
- [ ] Works for both network errors and API errors

**References:** `conversation_screen.dart`, lines 580-586 in spec

---

### THREAD-002: Add copy functionality for AI responses
**Status:** Open
**Component:** Message Bubble

**User Story:**
As a user, I want to easily copy AI-generated content, so that I can paste artifacts into other tools.

**Problem:**
Message Bubble has "Selectable text" but no explicit copy button. Mobile users struggle to select/copy long responses.

**Acceptance Criteria:**
- [ ] Copy icon button visible on all assistant messages
- [ ] Long-press menu includes "Copy" option (alongside Delete)
- [ ] Copy action copies full message to clipboard
- [ ] Snackbar confirms "Copied to clipboard"

**References:** `message_bubble.dart`, lines 714-720 in spec

---

### THREAD-003: Add ability to rename thread after creation
**Status:** Open
**Component:** Conversation Screen, Thread List

**User Story:**
As a user, I want to rename a conversation thread after starting it, so that I can give it a meaningful name once the topic becomes clear.

**Problem:**
Thread title can only be set at creation. Users end up with many "Untitled" threads.

**Acceptance Criteria:**
- [ ] Edit icon in ConversationScreen AppBar opens rename dialog
- [ ] "Rename" option added to Thread List PopupMenu
- [ ] Pre-fills current title in text field
- [ ] Empty title defaults to "Untitled"

**References:** `thread_create_dialog.dart`, `conversation_screen.dart`

---

### THREAD-004: Handle network interruption during streaming
**Status:** Open
**Component:** Streaming Message, Conversation Provider

**User Story:**
As a user, I want partial AI responses preserved if my connection drops, so that I don't lose valuable content.

**Problem:**
Document doesn't specify behavior on connection loss mid-stream. Partial responses may be discarded.

**Acceptance Criteria:**
- [ ] On network loss during streaming, partial content is preserved
- [ ] Error banner shows "Connection lost - response incomplete"
- [ ] Retry option attempts to continue/regenerate response
- [ ] User can copy partial content even in error state

**References:** `streaming_message.dart`, lines 726-730 in spec

---

## High Priority

### THREAD-005: Show current conversation mode persistently
**Status:** Open
**Component:** Conversation Screen

**User Story:**
As a user, I want to see which mode (Meeting/Document) my conversation is in, so that I understand the AI's behavior.

**Problem:**
Mode selector disappears after first message. User can't see or change active mode.

**Acceptance Criteria:**
- [ ] Current mode shown as chip/badge in AppBar after selection
- [ ] Tapping mode badge opens menu to change mode
- [ ] Mode change shows warning about potential context shift
- [ ] Mode persists across app restarts for that thread

**References:** Conversation Screen UI Elements, lines 564-572 in spec

---

### THREAD-006: Add search and filter for thread list
**Status:** Open
**Component:** Thread List Screen

**User Story:**
As a user, I want to search and sort my conversation threads, so that I can find specific discussions in large projects.

**Problem:**
Thread List only shows items with pull-to-refresh. No search or sort. Projects with many threads become unmanageable.

**Acceptance Criteria:**
- [ ] Search bar filters threads by title (real-time)
- [ ] Sort options: Newest, Oldest, Alphabetical
- [ ] Search persists until cleared
- [ ] Empty search result shows "No threads matching '{query}'"

**References:** `thread_list_screen.dart`, lines 512-537 in spec

---

### THREAD-007: Add dedicated artifact generation UI
**Status:** Open
**Component:** Conversation Screen

**User Story:**
As a user, I want a clear way to generate and manage artifacts, so that I don't have to remember specific prompts.

**Problem:**
Artifact generation requires typing specific phrases. No dedicated UI, no artifact management, export is unclear.

**Acceptance Criteria:**
- [ ] "Generate Artifact" button/FAB in ConversationScreen
- [ ] Artifact type picker: User Stories, Acceptance Criteria, BRD, Custom
- [ ] Generated artifacts visually distinct from chat (card/section)
- [ ] Each artifact has inline export buttons (Markdown, PDF, Word)
- [ ] Artifacts section/tab for viewing all generated artifacts

**References:** Flow 3 step 7, lines 173-177 in spec

---

### NAV-001: Extend breadcrumb to include thread context
**Status:** Open
**Component:** Breadcrumb Bar

**User Story:**
As a user, I want breadcrumbs to show my full location including the current thread, so that I can navigate back to any level.

**Problem:**
Breadcrumb stops at Project Detail. In ConversationScreen, user can't navigate directly to Threads tab.

**Acceptance Criteria:**
- [ ] Breadcrumb in ConversationScreen: "Projects > {Project} > Threads > {Thread}"
- [ ] Each segment is clickable and navigates to that route
- [ ] Truncation works gracefully on mobile

**References:** Flow 7, lines 264-269 in spec

---

### DOC-001: Add document preview before upload
**Status:** Open
**Component:** Document Upload Screen

**User Story:**
As a user, I want to preview a file before uploading, so that I can verify I selected the correct document.

**Problem:**
File selection immediately triggers upload. No confirmation or preview step.

**Acceptance Criteria:**
- [ ] After file selection, show preview: filename, size, first ~20 lines
- [ ] "Upload" button confirms and starts upload
- [ ] "Cancel" button clears selection
- [ ] Preview uses monospace font consistent with Document Viewer

**References:** `document_upload_screen.dart`, lines 460-487 in spec

---

### DELETE-001: Document undo behavior for threads and documents
**Status:** Open
**Component:** Thread List, Document List

**User Story:**
As a user, I want consistent undo behavior when deleting any resource, so that I can recover from mistakes.

**Problem:**
Project delete has 10-second undo (Flow 5). Thread/document delete behavior not documented - may not have undo.

**Acceptance Criteria:**
- [ ] Clarify: Do threads/documents have undo? Document the decision
- [ ] If yes: Implement 10-second undo matching project behavior
- [ ] If no: Document why (e.g., cascade complexity) and ensure confirmation dialog is clear
- [ ] Update spec with consistent delete behavior section

**References:** Flow 5, lines 199-222; Thread/Doc delete menus

---

### BUDGET-001: Design token budget exhaustion UX
**Status:** Open
**Component:** Settings Screen, Conversation Screen

**User Story:**
As a user, I want clear feedback when approaching or reaching my token budget limit, so that I'm not surprised by blocked functionality.

**Problem:**
Settings shows usage bar but no specification for what happens at limit. User may hit cryptic errors.

**Acceptance Criteria:**
- [ ] Warning banner at 80% usage: "You've used 80% of your budget"
- [ ] Warning banner at 95% usage: "Almost at limit - X messages remaining (estimate)"
- [ ] At 100%: Clear "Budget exhausted" state in ConversationScreen
- [ ] Exhausted state: Can view history, cannot send new messages
- [ ] Message explaining reset period or upgrade path
- [ ] Graceful API error handling (not generic error)

**References:** Settings Screen lines 614-619, missing from spec

---

## Medium Priority

### HOME-001: Differentiate home screen action buttons
**Status:** Open
**Component:** Home Screen

**User Story:**
As a user, I want the two home screen buttons to do different things, so that I understand which to click.

**Problem:**
"Start Conversation" and "Browse Projects" both navigate to `/projects`. Redundant and confusing.

**Acceptance Criteria:**
- [ ] "Start Conversation" → `/projects` with most recent project auto-selected, Threads tab active
- [ ] OR "Start Conversation" → opens project picker dialog, then navigates to Threads tab
- [ ] "Browse Projects" → `/projects` (current behavior)
- [ ] Button labels/icons clearly indicate different actions

**References:** Home Screen buttons, lines 351-356 in spec

---

### THREAD-008: Show which documents AI referenced
**Status:** Open
**Component:** Message Bubble, Conversation Screen

**User Story:**
As a user, I want to see which documents the AI used in its response, so that I can verify the source of information.

**Problem:**
AI shows "Searching documents..." status but response doesn't indicate which documents were referenced.

**Acceptance Criteria:**
- [ ] Assistant messages show source chips below content when documents were used
- [ ] Chips are clickable → open Document Viewer
- [ ] Format: "Sources: requirements.md, user-flows.txt"
- [ ] If no documents used, no chips shown

**References:** Flow 3 step 5, line 164 in spec

---

### SETTINGS-001: Show authentication provider
**Status:** Open
**Component:** Settings Screen

**User Story:**
As a user, I want to see which account (Google/Microsoft) I'm logged in with, so that I know which credentials to use.

**Problem:**
Settings shows email and name but not the OAuth provider used.

**Acceptance Criteria:**
- [ ] Provider icon (Google G / Microsoft logo) shown next to avatar
- [ ] OR subtitle text: "Signed in with Google" / "Signed in with Microsoft"

**References:** Settings Account section, lines 602-606 in spec

---

### PROJECT-001: Document tab state persistence
**Status:** Open
**Component:** Project Detail Screen

**User Story:**
As a user, I want the app to remember which tab I was viewing in a project, so that navigation feels consistent.

**Problem:**
Document doesn't specify tab persistence behavior when navigating away and back.

**Acceptance Criteria:**
- [ ] Document expected behavior in spec
- [ ] Implement: Remember last selected tab per project (stored in ProjectProvider or local)
- [ ] OR: Always default to Documents tab (simpler, document this choice)

**References:** Project Detail Screen, lines 396-430 in spec

---

### DOC-002: Add download option in Document Viewer
**Status:** Open
**Component:** Document Viewer Screen

**User Story:**
As a user, I want to download a document I previously uploaded, so that I can access my original file.

**Problem:**
Document Viewer shows content but no way to download/export the original file.

**Acceptance Criteria:**
- [ ] Download icon button in AppBar
- [ ] Downloads original file (not just displayed content)
- [ ] Uses original filename
- [ ] Shows snackbar: "Downloaded {filename}"

**References:** Document Viewer Screen, lines 490-509 in spec

---

### THREAD-009: Clarify message count definition
**Status:** Open
**Component:** Thread List Screen (Documentation)

**User Story:**
As a user, I want to understand what the message count means, so that I can gauge thread length.

**Problem:**
Thread list shows "message count" but spec doesn't define if it's total, user-only, or includes AI.

**Acceptance Criteria:**
- [ ] Update spec: "Message count includes both user and assistant messages"
- [ ] Format in UI: "12 messages" (total) or "6 exchanges" (pairs)
- [ ] Consistent with actual implementation

**References:** Thread List items, line 523 in spec

---

### DOC-003: Document OAuth token refresh behavior
**Status:** Open
**Component:** Authentication (Documentation)

**Description:**
Document that OAuth tokens auto-refresh silently in the background. Users should never be interrupted for re-authentication during normal use.

**Acceptance Criteria:**
- [ ] Add to spec under Authentication section or new "Session Management" section
- [ ] Text: "JWT tokens are automatically refreshed before expiration. Users remain authenticated without interruption."
- [ ] Document edge case: If refresh fails (revoked access), user sees friendly re-auth prompt

**References:** Authentication section, lines 37-39 in spec

---

### DOC-004: Document conversation export feature
**Status:** Open
**Component:** Conversation Screen (Documentation)

**User Story:**
As a user, I want to export an entire conversation thread, so that I can share or archive the full discussion.

**Problem:**
Feature Summary mentions "Export to Markdown, PDF, Word" but ConversationScreen doesn't show how to export full thread.

**Acceptance Criteria:**
- [ ] Clarify: Is this per-artifact or per-thread export?
- [ ] If per-thread: Add export button to ConversationScreen AppBar
- [ ] Document export flow in spec
- [ ] Export includes: all messages, timestamps, mode, artifacts

**References:** Feature Summary line 820, not in Conversation Screen buttons

---

### DOC-005: Document maximum file size enforcement
**Status:** Open
**Component:** Document Upload Screen

**User Story:**
As a user, I want clear feedback if my file is too large, so that I understand why upload failed.

**Problem:**
Spec mentions "1MB" limit but doesn't document the error state UX.

**Acceptance Criteria:**
- [ ] Document error state: "File too large. Maximum size is 1MB."
- [ ] Error shown before upload attempt (client-side validation)
- [ ] Snackbar or inline error message
- [ ] File selection cleared, user can try again

**References:** Document Upload instructions, line 471 in spec

---

## Low Priority

### RESPONSIVE-001: Review tablet breakpoint threshold
**Status:** Open
**Component:** Responsive Scaffold

**Description:**
600-899px shows collapsed NavigationRail (icons only). This is fairly wide for icon-only navigation.

**Acceptance Criteria:**
- [ ] Evaluate: Should labels show at 600px+?
- [ ] Consider: Collapsed 500-699px, Extended 700px+
- [ ] Or keep current - document rationale

**References:** Responsive Breakpoints table, lines 29-34 in spec

---

### AUTH-001: Document session duration
**Status:** Open
**Component:** Login Screen (Documentation)

**Description:**
Login screen doesn't indicate how long sessions last.

**Acceptance Criteria:**
- [ ] Document JWT session duration in spec
- [ ] If sessions are short (<24h), consider "Stay signed in" option
- [ ] Or document: "Sessions last 30 days unless user logs out"

**References:** Login Screen, lines 292-314 in spec

---

### THREAD-010: Increase chat input max lines
**Status:** Open
**Component:** Chat Input Widget

**User Story:**
As a user, I want more space for long inputs, so that I can paste requirements without cramped editing.

**Problem:**
Chat Input allows 1-5 lines. Users pasting long context are cramped.

**Acceptance Criteria:**
- [ ] Increase max to 8-10 lines
- [ ] OR add "expand" button that opens full-screen input modal
- [ ] Scrollable when exceeding max visible lines

**References:** Chat Input widget, line 710 in spec

---

### STATE-001: Document or add UsageProvider
**Status:** Open
**Component:** State Management (Documentation)

**Description:**
Settings shows token usage but no UsageProvider in State Management table.

**Acceptance Criteria:**
- [ ] Add UsageProvider to table with: purpose, key state (used, limit, percentage, isLoading, error)
- [ ] OR clarify usage data is fetched ad-hoc in Settings without dedicated provider

**References:** State Management section, lines 774-804 vs Settings lines 614-619

---

## Future Enhancements (Parking Lot)

These are enhancement ideas beyond current scope. Consider for future milestones.

| ID | Enhancement | Rationale |
|----|-------------|-----------|
| ENH-001 | Thread templates | Pre-fill mode + opening prompt for common scenarios |
| ENH-002 | Pin important threads | Keep frequently accessed threads at top |
| ENH-003 | Thread archiving | Hide completed threads without deleting |
| ENH-004 | Conversation bookmarks | Mark and find key moments in long threads |
| ENH-005 | AI response ratings | Thumbs up/down to track useful responses |
| ENH-006 | Quick artifact actions | Inline export buttons on detected artifact blocks |
| ENH-007 | Thread sharing | Generate read-only link for stakeholders |
| ENH-008 | Keyboard shortcuts | Desktop power-user efficiency |
| ENH-009 | Offline mode | View cached content without connection |
| ENH-010 | Accessibility audit | Screen reader support, focus order, ARIA |

---

*Backlog generated from APP-FEATURES-AND-FLOWS.md analysis*
*Last updated: 2026-01-30*
