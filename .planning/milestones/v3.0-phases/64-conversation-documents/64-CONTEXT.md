# Phase 64: Conversation & Documents - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

End-to-end chat and document upload for Assistant threads. Users can send messages, receive streaming responses (via claude-code-cli adapter), upload documents for AI context, and use Claude Code skills — completing the Assistant workflow started in Phases 62-63.

</domain>

<decisions>
## Implementation Decisions

### Chat screen design
- New dedicated AssistantChatScreen (not reusing BA ChatScreen)
- Clean chat view — no BA-specific buttons, no artifact viewer, no project context
- Attachment button for files
- Skills button — rugged-looking plus-in-a-square icon that opens a list of available Claude Code skills from .claude/
- When a skill is selected, it silently prepends to the prompt (user doesn't see "/skillname" in the chat — it behaves as if the prompt started with the skill context)
- Skills appear as a selectable element below the chat, not in the message stream

### Document upload flow
- Three upload methods: button in input area, drag-and-drop onto chat area, and paste image
- Broad file type support: documents (PDF, DOCX, TXT, MD), images (PNG, JPG, GIF), spreadsheets (CSV, XLSX), code files — anything Claude can process
- While composing: removable chip/pill above the text field showing filename
- After sending: inline card/thumbnail in the user's message bubble
- Documents persist for the entire thread — once uploaded, available as context for all future messages in that thread

### Streaming & indicators
- Thinking indicator with elapsed time — same pattern as existing BA chat
- Copy + retry controls on each AI response message
- Error handling: clear partial response on streaming error, show error message, auto-retry once
- Full markdown rendering — formatted output (like Ctrl+Shift+V in VS Code): headers, code blocks with syntax highlighting, tables, lists

### Input area controls
- Layout: attachment button on the left, skills button + send button grouped on the right
- Multi-line text input by default (3-4 lines tall)
- Enter sends the message, Shift+Enter for newline
- Skill indicator: small colored chip above the text field showing selected skill name, with X to remove

### Claude's Discretion
- Exact styling and spacing of the chat screen
- Skills list UI (popup menu, bottom sheet, etc.)
- Drag-and-drop visual feedback design
- Image paste detection implementation
- Auto-retry timing and backoff on streaming errors

</decisions>

<specifics>
## Specific Ideas

- Skills come from Claude Code skills in the .claude/ directory — same skills available in Claude Code CLI
- Markdown should be rendered formatted, not as raw markdown — "like Ctrl+Shift+V in VS Code" (paste without formatting shows rendered markdown)
- The skill selection should feel integrated, not like a command — user picks skill, sees chip, types their message naturally

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 64-conversation-documents*
*Context gathered: 2026-02-17*
