# Architecture Research

**Domain:** Assistant file generation and CLI permissions integration
**Researched:** 2026-02-23
**Confidence:** HIGH (all findings derived from reading the actual codebase)

---

## System Overview

```
+------------------------------------------------------------------+
|                         Flutter Frontend                          |
+----------------+-------------------------------+------------------+
|   BA Flow      |       Assistant Flow          |  Shared Widgets  |
| -------------- | ----------------------------  | ---------------  |
| Conversation   | AssistantChatScreen           | ArtifactCard     |
| Provider       | AssistantConversation         | ArtifactService  |
| generateArti   | Provider                      | (export: MD/PDF/ |
| fact()         | sendMessage()                 |  Word)           |
| (artifact_     |  [NEW] generateFile()         |                  |
|  generation    |  [NEW] GenerateFileDialog     |                  |
|  =true SSE)    |  [NEW] AssistantArtifactCard  |                  |
|                |                               |                  |
+----------------+-------------------------------+------------------+
|          AIService (frontend/lib/services/ai_service.dart)        |
|    streamChat(threadId, content, [artifactGeneration=false])       |
|    Parses SSE: TextDeltaEvent, ToolExecutingEvent,                 |
|    MessageCompleteEvent, ArtifactCreatedEvent, ErrorEvent          |
+------------------------------------------------------------------+
                              |  HTTP SSE
                              v
+------------------------------------------------------------------+
|                    FastAPI Backend (port 8000)                     |
+------------------------------------------------------------------+
|  POST /api/threads/{thread_id}/chat                               |
|       ChatRequest { content, artifact_generation: bool }          |
|       -> validates thread -> build_conversation_context()         |
|       -> AIService(provider, thread_type) -> stream_chat()        |
|       -> EventSourceResponse (SSE)                                |
+------------------------------------------------------------------+
|                      AIService (backend)                          |
|  thread_type == "assistant" -> forces provider = "claude-code-cli"|
|  thread_type == "ba_assistant" -> uses thread's model_provider    |
|  is_agent_provider == True -> _stream_agent_chat() (no man loop)  |
|  is_agent_provider == False -> manual tool loop (BA flow)         |
+------------------------------------------------------------------+
|                    ClaudeCLIAdapter                                |
|  ClaudeProcessPool (2 warm processes, asyncio.Queue)              |
|  _convert_messages_to_prompt() -> Human:/Assistant: format        |
|  stream_chat() -> acquire from pool -> write to stdin             |
|    -> parse stream-json stdout -> yield StreamChunk               |
|                                                                    |
|  [MISSING] --dangerously-skip-permissions flag in spawn args      |
|  [BLOCKED] Process pool spawns WITHOUT --dangerously-skip-perms   |
|  [BLOCKED] ClaudeProcessPool._spawn_warm_process() same issue     |
+------------------------------------------------------------------+
|              Artifacts (shared by both flows)                      |
|  models.py: Artifact, ArtifactType enum (user_stories,            |
|             acceptance_criteria, requirements_doc, brd)           |
|  routes/artifacts.py: GET /api/artifacts/{id}                     |
|                        GET /api/artifacts/{id}/export/{format}    |
|                        GET /api/threads/{id}/artifacts            |
+------------------------------------------------------------------+
                              |
                              v
             Claude Code CLI subprocess (--output-format stream-json)
```

---

## Component Boundaries

### Existing Components (Do Not Modify Substantially)

| Component | File | Responsibility | Touches v3.2? |
|-----------|------|----------------|---------------|
| ClaudeProcessPool | `backend/.../claude_cli_adapter.py` | Pre-warms 2 CLI processes | YES - add flag |
| ClaudeCLIAdapter.stream_chat() | `backend/.../claude_cli_adapter.py` | Spawns CLI, parses stream-json | YES - add flag |
| AIService._stream_agent_chat() | `backend/.../ai_service.py` | Routes agent events to SSE | YES - conditional system prompt |
| conversations.py chat endpoint | `backend/app/routes/conversations.py` | POST /threads/{id}/chat | NO - reused as-is |
| AssistantConversationProvider | `frontend/.../assistant_conversation_provider.dart` | Chat state, sendMessage() | YES - add generateFile() |
| AssistantChatScreen | `frontend/.../assistant_chat_screen.dart` | Chat UI | YES - render artifact cards |
| AssistantChatInput | `frontend/.../widgets/assistant_chat_input.dart` | Input bar | YES - add Generate File button |
| ArtifactCard | `frontend/.../conversation/widgets/artifact_card.dart` | Collapse/expand + export | REUSED as-is (BA widget) |
| ArtifactService | `frontend/.../services/artifact_service.dart` | Export MD/PDF/Word | REUSED as-is |
| Artifact model (frontend) | `frontend/.../models/artifact.dart` | ArtifactType, Artifact | REUSED as-is |
| Artifact model (backend) | `backend/app/models.py` | ArtifactType enum, DB table | NO - reused unchanged |
| mcp_tools.py save_artifact_tool | `backend/.../mcp_tools.py` | Saves artifact via ContextVar | NO - unchanged |

### New Components (Build for v3.2)

| Component | File | Responsibility |
|-----------|------|----------------|
| GenerateFileDialog | `frontend/.../assistant/widgets/generate_file_dialog.dart` | Free-text dialog for file description |
| AssistantArtifactCard | `frontend/.../assistant/widgets/assistant_artifact_card.dart` | Artifact card adapted for Assistant thread context |

---

## Data Flow: CLI Permissions Fix (Feature 1)

The problem is isolated. Claude CLI prompts interactively for permissions when it encounters tool use, causing the subprocess to hang. The fix is one flag added in three places.

### Current command (broken for non-interactive tool use):

```python
# ClaudeProcessPool._spawn_warm_process()
return await asyncio.create_subprocess_exec(
    self._cli_path,
    '-p',
    '--output-format', 'stream-json',
    '--verbose',
    '--model', self._model,
    ...
)
```

### Fixed command:

```python
return await asyncio.create_subprocess_exec(
    self._cli_path,
    '-p',
    '--output-format', 'stream-json',
    '--verbose',
    '--model', self._model,
    '--dangerously-skip-permissions',   # NEW
    ...
)
```

### Touch points (all three must be updated atomically):

1. `ClaudeProcessPool._spawn_warm_process()` — warm process spawn (line ~178)
2. `ClaudeProcessPool._cold_spawn()` — cold fallback spawn (line ~195)
3. `ClaudeCLIAdapter.stream_chat()` cold-spawn branch (line ~628) — when pool not initialized

All three use the same `asyncio.create_subprocess_exec(self.cli_path, '-p', ...)` pattern. Missing the flag in any one path causes intermittent hangs when that path executes.

**Confidence:** HIGH — `--dangerously-skip-permissions` is the established non-interactive flag for CLI subprocess use. The code already defines `_build_cli_env()` as a helper for environment — a similar `_build_cli_args()` helper would DRY the flag list across all three spawn locations.

---

## Data Flow: Assistant File Generation (Feature 2)

### Full request lifecycle:

```
User clicks "Generate File" button (new button in AssistantChatInput)
    |
    v
GenerateFileDialog.show() -> user types free-text description -> taps Generate
    |
    v
AssistantConversationProvider.generateFile(description)
    [NEW METHOD - mirrors BA's generateArtifact() pattern exactly]
    |
    v
AIService.streamChat(threadId, constructedPrompt, artifactGeneration=true)
    |  HTTP POST /api/threads/{thread_id}/chat
    v  { content: "Generate a document: <description>",
         artifact_generation: true }
    |
    v
conversations.py: artifact_generation=true path (EXISTING, unchanged)
    - Does NOT save user message to DB
    - Appends ephemeral silent-generation instruction to conversation
    - AIService(provider="claude-code-cli", thread_type="assistant")
    |
    v
_stream_agent_chat() [MODIFIED: inject save_artifact tool description in system prompt]
    -> ClaudeCLIAdapter.stream_chat() [MODIFIED: --dangerously-skip-permissions]
    |
    v
CLI subprocess executes save_artifact tool
    -> mcp_tools.save_artifact_tool() via ContextVar path
    -> saves Artifact to DB (thread_id from context, artifact_type chosen by model)
    -> returns ARTIFACT_CREATED:{...} marker
    |
    v
_stream_agent_chat() emits SSE events:
    - "artifact_created" { id, artifact_type, title }
    - "message_complete"
    |
    v
Frontend AIService parses ArtifactCreatedEvent
    |
    v
AssistantConversationProvider.generateFile():
    - on ArtifactCreatedEvent: add Artifact to _artifacts list, notifyListeners()
    - clears _isGeneratingFile state on MessageCompleteEvent or ErrorEvent
    |
    v
AssistantChatScreen renders AssistantArtifactCard for each artifact in _artifacts
```

### State additions to AssistantConversationProvider:

```dart
// NEW fields:
List<Artifact> _artifacts = [];          // accumulates generated artifacts
bool _isGeneratingFile = false;          // blocks concurrent generation
String? _generatingFileDescription;     // for UX display ("Generating...")
String? _lastFileDescription;           // for retry

// NEW methods:
Future<void> generateFile(String description) async
void retryLastFileGeneration()

// NEW getters:
List<Artifact> get artifacts => _artifacts;
bool get isGeneratingFile => _isGeneratingFile;
String? get generatingFileDescription => _generatingFileDescription;
bool get canRetryFileGeneration => _lastFileDescription != null && _error != null;
```

### Where artifacts are displayed:

The current `AssistantChatScreen._buildMessageList()` only renders messages. Artifact cards should render as a separate section below the message list. This matches BA flow behavior (artifact cards appear outside the message scroll area) and avoids interleaving complexity.

---

## The Missing Integration Point: save_artifact Tool in Assistant Mode

This is the most architecturally significant finding. The Assistant's normal chat uses `system_prompt = ""` (empty). For file generation to work, the CLI must know about the `save_artifact` tool. The tool description lives in the system prompt.

**Current state in `_stream_agent_chat()` (ai_service.py line 931):**
```python
# LOGIC-01: No system prompt for Assistant threads (per locked decision)
system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""
```

**Required change for file generation:**

The `artifact_generation` context must reach `_stream_agent_chat()`. There are two ways:

**Option A (recommended): Pass artifact_generation into AIService.stream_chat()**

```python
# conversations.py: pass artifact_generation to AIService.stream_chat()
raw_stream = ai_service.stream_chat(
    conversation,
    thread.project_id,
    thread_id,
    db,
    artifact_generation=body.artifact_generation  # NEW param
)
```

```python
# ai_service.py _stream_agent_chat(): conditional system prompt
if self.thread_type == "assistant" and artifact_generation:
    system_prompt = ASSISTANT_FILE_GENERATION_PROMPT  # NEW: minimal tool description
elif self.thread_type == "ba_assistant":
    system_prompt = SYSTEM_PROMPT
else:
    system_prompt = ""
```

```python
# New constant in ai_service.py:
ASSISTANT_FILE_GENERATION_PROMPT = """You are a file generation assistant.
The user wants you to generate a document or file. Use the save_artifact tool to save it.

save_artifact tool:
- artifact_type: one of user_stories, acceptance_criteria, requirements_doc, brd
- title: descriptive title for the file
- content_markdown: complete file content in markdown format

Generate the requested content and call save_artifact exactly once. Do not add conversational text."""
```

**Option B: Keep artifact_generation logic in conversations.py only**

The conversation route already appends a silent-generation instruction to the ephemeral message. The model could potentially figure out to call save_artifact without the system prompt describing the tool. However, this is unreliable — the model needs to know the tool signature exists to call it.

**Decision: Option A.** The `artifact_generation` boolean already flows through `ChatRequest` -> `event_generator()`. Extending it one level further into `AIService.stream_chat()` and `_stream_agent_chat()` is a minimal change.

---

## Reuse Analysis: Artifact Card

`ArtifactCard` at `frontend/lib/screens/conversation/widgets/artifact_card.dart` is implemented as a self-contained widget that:
- Accepts `Artifact artifact` and `String threadId`
- Calls `ArtifactService` for lazy content loading and export
- Has no dependency on `ConversationProvider`

The `Artifact` model already includes `artifact.threadId`, so `widget.threadId` in `ArtifactCard` is redundant but harmless.

**Decision: Create `AssistantArtifactCard` as a thin wrapper.** The difference from `ArtifactCard` is only the location in the widget tree (Assistant screen vs. BA ConversationScreen). Wrapping rather than copying avoids drift between the two. The wrapper passes `artifact.threadId` as the threadId parameter.

```dart
// frontend/lib/screens/assistant/widgets/assistant_artifact_card.dart
class AssistantArtifactCard extends StatelessWidget {
  final Artifact artifact;
  const AssistantArtifactCard({super.key, required this.artifact});

  @override
  Widget build(BuildContext context) {
    return ArtifactCard(
      artifact: artifact,
      threadId: artifact.threadId,
    );
  }
}
```

If `ArtifactCard` already handles `artifact.threadId` correctly (which it does — the threadId param is used for context only), this is a one-liner wrapper.

---

## Recommended Project Structure (New and Modified Files Only)

```
backend/app/services/llm/
  claude_cli_adapter.py         MODIFY: add --dangerously-skip-permissions to 3 spawn paths

backend/app/services/
  ai_service.py                 MODIFY: ASSISTANT_FILE_GENERATION_PROMPT constant,
                                        stream_chat() accepts artifact_generation param,
                                        _stream_agent_chat() uses conditional system prompt

frontend/lib/providers/
  assistant_conversation_provider.dart  MODIFY: add _artifacts list, generateFile(),
                                                retryLastFileGeneration(), getters

frontend/lib/screens/assistant/
  assistant_chat_screen.dart    MODIFY: render artifact cards section below messages

frontend/lib/screens/assistant/widgets/
  assistant_chat_input.dart     MODIFY: add Generate File IconButton
  generate_file_dialog.dart     NEW: free-text generation dialog
  assistant_artifact_card.dart  NEW: thin wrapper over ArtifactCard
```

No DB migrations required. No new routes required. No model changes required.

---

## Architectural Patterns

### Pattern 1: Silent Generation (Existing, Reuse Unchanged)

**What:** `artifact_generation=true` in `ChatRequest` suppresses user message save to DB, text_delta SSE events (filtered in event_generator), and assistant message save. Only `artifact_created` event reaches the frontend.

**When to use:** Any time file or artifact generation should happen without creating chat message bubbles. The BA flow established this pattern; Assistant file generation reuses it identically.

**Key invariant:** `generateFile()` must NOT call `sendMessage()` path. It must be a separate method that sets `_isGeneratingFile` (not `_isStreaming`) and does not touch `_messages`.

### Pattern 2: ContextVar Tool Execution (Existing, Unchanged)

**What:** `set_context(db, project_id, thread_id)` before `stream_chat()`. Tools read `thread_id` from ContextVars set by the adapter.

**Note:** Assistant threads have `project_id = None`. The `save_artifact_tool` in `mcp_tools.py` only needs `thread_id`, not `project_id`. The ContextVar path reads `_thread_id_context` independently. No change needed.

### Pattern 3: Pool Warm Processes (Existing, Fix Required)

**What:** All 3 spawn paths must receive identical CLI flags. Pre-warmed processes in the pool and cold-spawned fallbacks must behave identically.

**Fix:** Extract a `_base_cli_args()` helper method to ensure DRY flag list:

```python
def _base_cli_args(self) -> list:
    """Base CLI arguments used for all spawn paths."""
    return [
        self._cli_path,
        '-p',
        '--output-format', 'stream-json',
        '--verbose',
        '--model', self._model,
        '--dangerously-skip-permissions',  # Required for non-interactive tool use
    ]
```

Then all three spawn locations call `self._base_cli_args()` instead of repeating the flag list.

---

## Integration Points Summary

### Backend Integration Points

| Point | What Changes | File | Lines Affected |
|-------|-------------|------|----------------|
| `ClaudeProcessPool._spawn_warm_process()` | Add `--dangerously-skip-permissions` flag | `claude_cli_adapter.py` | ~178-193 |
| `ClaudeProcessPool._cold_spawn()` | Same flag | `claude_cli_adapter.py` | ~195-214 |
| Direct cold-spawn in `stream_chat()` | Same flag | `claude_cli_adapter.py` | ~628-635 |
| `AIService.stream_chat()` signature | Add `artifact_generation=False` param | `ai_service.py` | ~1039 |
| `AIService._stream_agent_chat()` | Add `artifact_generation` param + conditional system prompt | `ai_service.py` | ~864, ~931 |
| `ASSISTANT_FILE_GENERATION_PROMPT` | New constant with minimal save_artifact description | `ai_service.py` | New constant |

### Frontend Integration Points

| Point | What Changes | File |
|-------|-------------|------|
| `AssistantConversationProvider` | Add `_artifacts`, `_isGeneratingFile`, `generateFile()`, retry | `assistant_conversation_provider.dart` |
| `AssistantChatInput` | Add Generate File `IconButton` between SkillSelector and Send | `assistant_chat_input.dart` |
| `AssistantChatScreen._buildMessageList()` OR scaffold body | Add artifact cards section | `assistant_chat_screen.dart` |

### New Components

| Component | Depends On | Build Complexity |
|-----------|------------|-----------------|
| `GenerateFileDialog` | None (pure UI) | Low - simple dialog with TextField |
| `AssistantArtifactCard` | `Artifact` model, `ArtifactCard` widget | Trivial - thin wrapper |

---

## Build Order (Dependency-Driven)

The two features (CLI permissions fix and file generation) are independent. Do CLI fix first to unblock any tool-use testing.

**Phase 1 - CLI Permissions Fix (backend only, ~30 min):**
Add `--dangerously-skip-permissions` to all 3 spawn locations in `claude_cli_adapter.py`. Optionally extract `_base_cli_args()` helper. Verify with a test that invokes a tool.

**Phase 2 - Backend: save_artifact for Assistant (backend only, ~1-2 hr):**
Add `ASSISTANT_FILE_GENERATION_PROMPT` constant. Modify `AIService.stream_chat()` and `_stream_agent_chat()` to accept and use `artifact_generation` param for conditional system prompt injection. No DB changes. No route changes.

**Phase 3 - Frontend: Provider + Dialog (~2-3 hr):**
Add `generateFile()` method and artifact state to `AssistantConversationProvider`. Build `GenerateFileDialog` (TextField + Generate button). Build `AssistantArtifactCard` wrapper.

**Phase 4 - Frontend: UI Wire-up (~1-2 hr):**
Add Generate File button to `AssistantChatInput`. Wire `AssistantChatScreen` to render `AssistantArtifactCard` for each artifact in provider.

---

## Anti-Patterns

### Anti-Pattern 1: Mixing generateFile() into sendMessage()

**What people do:** Route file generation through `sendMessage()` with a special prefix or flag.

**Why it's wrong:** `sendMessage()` adds a user message bubble, sets `_isStreaming`, accumulates `_streamingText`, and adds an assistant message on complete. File generation must be silent — no chat history entries. This separation is established in PITFALL-06 of the decisions log.

**Do this instead:** Separate `generateFile()` method that only sets `_isGeneratingFile` (not `_isStreaming`) and never touches `_messages`.

### Anti-Pattern 2: Adding --dangerously-skip-permissions to only the warm-process spawn

**What people do:** Add the flag to `_spawn_warm_process()` only and forget `_cold_spawn()` and the inline cold-spawn in `stream_chat()`.

**Why it's wrong:** When the pool is exhausted (more than 2 concurrent requests, or during startup before warm processes are ready), the cold-spawn paths run without the flag. The CLI will block waiting for interactive input and hang the request indefinitely.

**Do this instead:** Extract `_base_cli_args()` helper and use it in all three spawn paths. Change it once, all paths updated.

### Anti-Pattern 3: Using the full BA SYSTEM_PROMPT for Assistant file generation

**What people do:** When `artifact_generation=True` for an Assistant thread, pass the full 7000-token `SYSTEM_PROMPT` (the BA business analyst prompt) to the CLI.

**Why it's wrong:** Injects BA-specific discovery behavior, mode detection ("Meeting Mode vs Document Refinement"), and consultative tone instructions into what should be clean, general-purpose file generation. Wastes tokens. May confuse the model with irrelevant BA constraints.

**Do this instead:** A minimal `ASSISTANT_FILE_GENERATION_PROMPT` that describes only the `save_artifact` tool and instructs the model to call it once with the generated content.

### Anti-Pattern 4: Adding a new ArtifactType enum value for Assistant files

**What people do:** Add `GENERATED_FILE` or `ASSISTANT_OUTPUT` to the `ArtifactType` enum.

**Why it's wrong:** Requires a DB migration (Enum column), backend enum change, frontend enum change. Unnecessary complexity for v3.2. The existing types (`user_stories`, `acceptance_criteria`, `requirements_doc`, `brd`) cover most generated content. The model can choose the most appropriate type from the description.

**Do this instead:** Let the CLI choose from existing artifact types based on the user's description. The frontend `ArtifactType.fromJson()` already has a safe fallback to `requirementsDoc` for unknown values.

---

## Scaling Considerations

Not relevant for v3.2 scope. Single-user, SQLite, 2-process pool.

| Concern | Current (v3.2) | Future |
|---------|---------------|--------|
| Process pool size | 2 is enough for 1 user | Scale with concurrent users |
| Artifact storage | SQLite, no limit at current scale | PostgreSQL migration path exists via SQLAlchemy ORM |
| File generation latency | CLI spawn overhead mitigated by pool | Pool size tuning if needed |

---

## Sources

All findings are HIGH confidence — derived from direct source code inspection:

- `/backend/app/services/llm/claude_cli_adapter.py` (ClaudeCLIAdapter, ClaudeProcessPool, all spawn paths)
- `/backend/app/services/ai_service.py` (AIService, _stream_agent_chat, system prompt logic at line 931)
- `/backend/app/routes/conversations.py` (ChatRequest, stream_chat endpoint, artifact_generation handling)
- `/backend/app/services/mcp_tools.py` (save_artifact_tool, ContextVar pattern, thread_id usage)
- `/backend/app/models.py` (ArtifactType enum, Artifact model, thread_id FK)
- `/frontend/lib/providers/assistant_conversation_provider.dart` (current state, generateFile gap)
- `/frontend/lib/providers/conversation_provider.dart` (generateArtifact() reference implementation)
- `/frontend/lib/screens/assistant/assistant_chat_screen.dart`
- `/frontend/lib/screens/assistant/widgets/assistant_chat_input.dart`
- `/frontend/lib/screens/conversation/widgets/artifact_card.dart` (reuse candidate)
- `/frontend/lib/services/artifact_service.dart` (reuse as-is)
- `/frontend/lib/models/artifact.dart` (reuse as-is)
- `/.planning/PROJECT.md` (v3.2 milestone requirements)

---

*Architecture research for: v3.2 Assistant File Generation and CLI Permissions*
*Researched: 2026-02-23*
