# Feature Research

**Domain:** AI Assistant file generation + CLI subprocess permissions
**Researched:** 2026-02-23
**Confidence:** HIGH (codebase read directly; CLI behavior verified via official docs + GitHub issues)

---

## Context: What Already Exists

This is a subsequent milestone (v3.2). The following are already built and NOT in scope:

**Assistant section (v3.0-v3.1.1):**
- AssistantChatScreen with streaming, markdown rendering, copy/retry
- AssistantChatInput with attachment button (left), SkillSelector (right-of-text), send button (rightmost)
- AssistantConversationProvider: sendMessage(), skill prepend, file attach/upload
- ClaudeCLIAdapter: subprocess pool, stream-json parsing, conversation history

**BA section (v1.9.2-v1.9.4):**
- ArtifactCard widget: collapsible, lazy content load, MD/PDF/Word export buttons
- ArtifactTypePicker: bottom sheet with preset types + custom text input
- generateArtifact() on ConversationProvider: separate path from sendMessage()
- export_service.py: Markdown, PDF, docx generation and download
- Artifact model (DB + Dart): id, thread_id, artifact_type, title, content_markdown

**New v3.2 scope** (what this milestone adds):
1. `--dangerously-skip-permissions` flag in CLI subprocess command
2. "Generate File" button in AssistantChatInput (next to send)
3. Dialog: free-text description of what to generate
4. Artifact card in Assistant chat messages (reusing existing ArtifactCard)

---

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CLI runs without blocking on permission prompts | Without this, subprocess hangs when Claude attempts any tool — blocking all generation requests. Non-interactive subprocess cannot display or respond to a permission prompt. | LOW | Add `--dangerously-skip-permissions` to cmd args in `_spawn_warm_process()`, `_cold_spawn()`, and the cmd list in `stream_chat()`. Three identical single-line additions. |
| Generate File button visible in chat input bar | Users need a visible affordance for generation — not a hidden text command or buried menu | LOW | Add IconButton to the AssistantChatInput Row, between SkillSelector and send. The Row already has the pattern: attach (left), text, skill, send (right). |
| Dialog with free-text description field | Users describe arbitrary file content — no preset types are appropriate for a general assistant | LOW | showModalBottomSheet with a TextField. Pattern already exists in ArtifactTypePicker. New widget: GenerateFileDialog with static show() factory. |
| Generated content displayed as artifact card in chat | Users expect to see output in the conversation, not just a "done" status message | MEDIUM | Requires: (a) save_artifact tool fires in CLI flow, (b) artifact_created SSE event reaches frontend, (c) AssistantConversationProvider handles ArtifactCreatedEvent, (d) AssistantMessageBubble or conversation list renders ArtifactCard. |
| Collapse/expand behavior on artifact card | Standard for large content; already implemented in ArtifactCard | LOW | Reuse existing ArtifactCard widget directly — zero new code for this behavior. |
| MD/PDF/Word export from artifact card | Users expect to extract generated content to files; already shipped in BA section | LOW | Reuse existing ArtifactCard export buttons + export_service.py backend. No new backend code needed. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Free-text generation (not preset artifact types) | General assistant generates anything — code, plans, templates, scripts — not limited to BA document types | LOW | Dialog accepts arbitrary text; description becomes the generation instruction. Contrast with BA section which uses fixed ArtifactType enum (user_stories, brd, etc.). |
| Silent generation separate from chat flow | No empty message bubbles, no streaming conflicts, no state machine interference | LOW | Already established pattern in BA section (Phase 42 decision). Replicate: `generateFile()` method on provider, separate from `sendMessage()`. |
| Reuses existing export infrastructure | Users get MD/PDF/Word download immediately with no new backend work | LOW | ArtifactCard.export() calls ArtifactService which calls existing /api/artifacts/{id}/export endpoint. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Preset artifact type picker for Assistant (clone of BA ArtifactTypePicker) | Familiar UX from BA section | The Assistant section is general-purpose; forcing preset types (BRD, User Stories) is BA-specific and contextually wrong here | Free-text dialog only — user types exactly what they want, no category boxing |
| Streaming generation output (character by character) | Feels more responsive | ClaudeCLIAdapter does not support partial message streaming (documented in the adapter: "Partial message streaming not supported; only complete events are emitted") | Spinner during generation, complete artifact card rendered when done |
| Auto-detect what to generate from conversation | Reduce user friction | Requires heuristic that will misfire on ambiguous conversations; unpredictable behavior | Explicit button + dialog — user controls what gets generated |
| Edit generated content inline before export | Refine without exporting to disk | Complex state management: content sync, export from edited state, dirty state tracking | Export to MD/Word and edit externally; consistent with existing BA artifact behavior |
| `--allowedTools` flag instead of `--dangerously-skip-permissions` | Seems more targeted | CLI's agent loop has no fixed tool set — it uses tool descriptions from system prompt. Cannot enumerate tools upfront. `--allowedTools` would require hardcoding specific tool names that could vary. | `--dangerously-skip-permissions` is the correct flag for fully automated headless use per official docs |

---

## Feature Dependencies

```
[--dangerously-skip-permissions in CLI subprocess args]
    └──enables──> [Any file tool in Claude agent loop runs without hanging]
                      └──requires──> [save_artifact tool in CLI system prompt — already exists in mcp_tools.py]
                                         └──already exists──> [Artifact model in DB with content_markdown]

[Generate File button in AssistantChatInput]
    └──triggers──> [GenerateFileDialog (free-text)]
                      └──submits──> [generateFile(description) on AssistantConversationProvider]
                                        └──calls──> [POST /api/threads/{id}/chat with generation prompt]
                                        └──CLI loop invokes save_artifact tool]
                                        └──yields──> [artifact_created SSE event from ai_service.py]
                                                         └──AssistantConversationProvider adds to _artifacts list]
                                                         └──renders──> [ArtifactCard in conversation view]

[ArtifactCard in Assistant messages]
    └──reuses──> [existing ArtifactCard widget — no changes needed to the widget]
    └──reuses──> [existing export_service.py endpoints — no new backend]
    └──requires──> [AssistantConversationProvider._artifacts List<Artifact>]
    └──requires──> [AssistantChatScreen renders artifact cards in message list]
```

### Dependency Notes

- **`--dangerously-skip-permissions` is a hard prerequisite.** Without it, any generation request causing Claude to attempt file tools either blocks (subprocess waits on stdin for approval that never comes) or fails with "Claude requested permissions to use [tool], but you haven't granted it yet." Confirmed via GitHub issue #581 (non-interactive -p mode permission blocking) and official headless docs.

- **`generateFile()` must be separate from `sendMessage()`.** Established pattern from BA section Phase 42 decision. If generation uses sendMessage(), it creates blank user message bubbles, streaming UI conflicts, and state machine interference. The provider needs a parallel `generateFile()` method with its own `_isGenerating` flag.

- **artifact_created SSE event handling is the MEDIUM complexity item.** The ClaudeCLIAdapter already translates save_artifact tool_use blocks into StreamChunk events. The ai_service.py conversation route handles artifact creation and emits artifact_created SSE events. BUT: AssistantConversationProvider currently only handles TextDeltaEvent, ToolExecutingEvent, MessageCompleteEvent, ErrorEvent. It does not handle ArtifactCreatedEvent. This wiring is the main new code.

- **ArtifactCard reuse is safe and complete.** The existing ArtifactCard widget depends only on the Artifact model and ArtifactService. Both are thread-type-agnostic. The card can be dropped directly into AssistantChatScreen's message list rendering with zero changes to the widget itself.

---

## MVP Definition

### Launch With (v3.2)

All four features are required together — partial delivery leaves generation either blocked (no flag) or invisible (no card).

- [ ] `--dangerously-skip-permissions` in ClaudeCLIAdapter subprocess args — unblocks generation
- [ ] "Generate File" button in AssistantChatInput + GenerateFileDialog — entry point for users
- [ ] `generateFile()` on AssistantConversationProvider + artifact_created event handling — core logic
- [ ] ArtifactCard rendered in AssistantChatScreen conversation list — visible output

### Add After Validation (v3.x)

- [ ] Skill-aware generation: when user has a skill selected, prepend skill context to the generation prompt. Low complexity addition, not blocking for v3.2.
- [ ] Generation history panel: list all artifacts generated in a thread. Scope: v3.3+.

### Future Consideration (v2+)

- [ ] Bulk export of all artifacts from a thread
- [ ] In-app content editing before export

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `--dangerously-skip-permissions` flag | HIGH (nothing works without it) | LOW (1-line change, 3 locations) | P1 |
| Generate File button + GenerateFileDialog | HIGH (user entry point) | LOW (new button + simple dialog widget) | P1 |
| `generateFile()` on AssistantConversationProvider + event wiring | HIGH (core logic) | MEDIUM (new method, artifact event handling, state) | P1 |
| ArtifactCard in AssistantChatScreen | HIGH (visible output) | MEDIUM (plumb provider artifacts into list rendering) | P1 |
| Skill context in generation | MEDIUM (useful when skill selected) | LOW (prepend existing selectedSkill.name) | P2 |

**Priority key:**
- P1: Must have for v3.2 launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Implementation Notes by Feature

### Feature 1: `--dangerously-skip-permissions`

**File:** `backend/app/services/llm/claude_cli_adapter.py`

Three locations in the file require the same change:

1. `_spawn_warm_process()` — pool pre-warm subprocess args (line ~178)
2. `_cold_spawn()` — cold fallback subprocess args (line ~203)
3. `stream_chat()` `cmd` list — direct spawn path when pool is None (line ~604)

The flag goes after `-p`:
```python
self.cli_path,
"-p",
"--dangerously-skip-permissions",  # ADD HERE
"--output-format", "stream-json",
"--verbose",
"--model", self.model,
```

**Why `--dangerously-skip-permissions` and not `--allowedTools`:** The CLI agent loop uses tool descriptions from the system prompt (mcp_tools.py). The `--allowedTools` flag requires listing specific tool names upfront. Since the tool set is dynamic (determined by system prompt content), `--dangerously-skip-permissions` is the correct flag for automated headless use. This is what Anthropic recommends in their official headless/CI documentation.

**Security context:** The backend server already runs under user authentication. The subprocess inherits a restricted server environment. The flag is appropriate for this controlled server-side use case — the same scenario as Docker/CI usage.

### Feature 2: Generate File Button + Dialog

**File:** `frontend/lib/screens/assistant/widgets/assistant_chat_input.dart`

Add an `IconButton` (suggested icon: `Icons.auto_awesome` or `Icons.create_new_folder_outlined`) to the input Row, between SkillSelector and the send button.

**New widget:** `frontend/lib/screens/assistant/widgets/generate_file_dialog.dart`

Pattern: showModalBottomSheet (consistent with ArtifactTypePicker in BA section). Widget structure:
- Static `show(BuildContext context) -> Future<String?>` factory method
- Title: "Generate File"
- Subtitle: "Describe what to generate"
- TextField: multiline, autofocus, "Describe the file you want to create..."
- Submit button: returns the description text

Returns `null` if dismissed, returns description string if submitted.

### Feature 3: `generateFile()` on AssistantConversationProvider

**File:** `frontend/lib/providers/assistant_conversation_provider.dart`

**New state:**
```dart
List<Artifact> _artifacts = [];
bool _isGenerating = false;  // Separate from _isStreaming
```

**New method:**
```dart
Future<void> generateFile(String description) async {
  if (_thread == null || _isStreaming || _isGenerating) return;
  _isGenerating = true;
  notifyListeners();

  final prompt = 'Generate the following and save it as an artifact:\n\n$description';

  try {
    await for (final event in _aiService.streamChat(_thread!.id, prompt)) {
      if (event is ArtifactCreatedEvent) {
        _artifacts.add(event.artifact);
        notifyListeners();
      }
      // ignore TextDeltaEvent (generation is silent, no streaming display)
    }
  } finally {
    _isGenerating = false;
    notifyListeners();
  }
}
```

**ArtifactCreatedEvent handling:** AIService already emits ArtifactCreatedEvent (used in ConversationProvider for BA section). AssistantConversationProvider needs to add this event type to its stream handling — currently it ignores unknown events.

### Feature 4: ArtifactCard in AssistantChatScreen

**File:** `frontend/lib/screens/assistant/assistant_chat_screen.dart`

**Approach:** Render artifacts as a distinct section at the bottom of the conversation list, not attached to specific messages. This matches how BA ConversationProvider tracks `_currentArtifact` and how artifact cards appear independently in the message stream.

In `_buildMessageList()`, after rendering regular messages and streaming message, add:
```dart
// Artifact cards (generated files)
...provider.artifacts.map((artifact) => ArtifactCard(
  artifact: artifact,
  threadId: widget.threadId,
))
```

The ArtifactCard widget requires no changes — it already handles expand/collapse, lazy content loading, and MD/PDF/Word export.

**Provider getter:**
```dart
List<Artifact> get artifacts => _artifacts;
```

---

## Sources

- Codebase read directly:
  - `backend/app/services/llm/claude_cli_adapter.py`
  - `frontend/lib/screens/assistant/widgets/assistant_chat_input.dart`
  - `frontend/lib/screens/assistant/assistant_chat_screen.dart`
  - `frontend/lib/providers/assistant_conversation_provider.dart`
  - `frontend/lib/screens/conversation/widgets/artifact_card.dart`
  - `frontend/lib/screens/conversation/widgets/artifact_type_picker.dart`
  - `frontend/lib/models/artifact.dart`
  - `.planning/PROJECT.md`
- Official Claude Code CLI headless docs: [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)
- GitHub Issue #581: [Bug: Claude CLI non-interactive mode doesn't respect configured tool permissions](https://github.com/anthropics/claude-code/issues/581) — confirms permission blocking in -p mode
- GitHub Issue #25503: [[BUG] --dangerously-skip-permissions flag should bypass the permissions mode dialog](https://github.com/anthropics/claude-code/issues/25503)
- [What is --dangerously-skip-permissions in Claude Code?](https://docs.bswen.com/blog/2026-02-21-dangerously-skip-permissions-explained/) (2026-02-21)
- [claude --dangerously-skip-permissions](https://blog.promptlayer.com/claude-dangerously-skip-permissions/) — use case context

---

*Feature research for: BA Assistant v3.2 — Assistant File Generation & CLI Permissions*
*Researched: 2026-02-23*
*Confidence: HIGH — CLI behavior verified via official docs + GitHub issues; feature design based on direct codebase reading*
