# Architecture: Artifact Deduplication & Silent Generation (v1.9.4)

**Domain:** Bug fix — Artifact generation multiplies on repeated requests
**Researched:** 2026-02-04
**Confidence:** HIGH (based on direct codebase analysis of all affected files)

---

## Executive Summary

The artifact multiplication bug (BUG-016) is caused by an architectural gap: conversation
history is loaded unfiltered, and the LLM has no prompt-level or structural signal to
distinguish fulfilled requests from new ones. The fix is a 4-layer defense-in-depth strategy
that modifies 6 existing files across backend and frontend. No new files are needed for
layers 1-3. Layer 4 (silent generation) adds frontend state and a loading widget.

**Critical finding during research:** BUG-019 references an `ARTIFACT_CREATED:{json}|`
marker that exists ONLY in the dead code path (`agent_service.py:174`). The active code
path (`ai_service.py:733`) uses `"Artifact saved successfully: '{title}' (ID: {id})"` as
the tool result string. The detection strategy in `build_conversation_context()` must use
the correct marker from the active code path, or query the artifacts table directly.

---

## Current Architecture (Pre-Fix)

### System Overview

```
+-------------------+    HTTP/SSE     +---------------------+    Anthropic API    +-----------+
|   Flutter App     | -------------> |   FastAPI Backend    | -----------------> | Claude    |
|                   | <------------- |                      | <----------------- | Sonnet    |
|                   |   SSE events   |                      |   Streaming        |           |
+-------------------+                +---------------------+                    +-----------+
        |                                     |
        |                                     v
        |                            +------------------+
        |                            |     SQLite       |
        |                            |  - messages      |
        |                            |  - artifacts     |
        |                            |  - threads       |
        |                            +------------------+
        |
        v
  [User sees chat bubbles
   + artifact cards]
```

### Current Data Flow: Artifact Generation

```
Step 1: User clicks "Generate User Stories" button
        |
        v
Step 2: conversation_screen.dart:_showArtifactTypePicker()
        Returns ArtifactTypeSelection
        |
        v
Step 3: conversation_screen.dart:214
        provider.sendMessage("Generate User Stories from this conversation.")
        |
        v
Step 4: conversation_provider.dart:sendMessage()
        - Adds optimistic user message to _messages list
        - Sets _isStreaming = true
        - Calls _aiService.streamChat(threadId, content)
        |
        v
Step 5: Frontend ai_service.dart:streamChat()
        POST /api/threads/{id}/chat  body: {"content": "Generate User Stories..."}
        SSE connection opened
        |
        v
Step 6: Backend conversations.py:stream_chat()
        - save_message(db, thread_id, "user", body.content)  <-- SAVED TO DB
        - build_conversation_context(db, thread_id)           <-- LOADS ALL MESSAGES
        - AIService(provider).stream_chat(conversation, ...)
        |
        v
Step 7: Backend conversation_service.py:build_conversation_context()
        - SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at
        - Converts to [{role: "user", content: "..."}, {role: "assistant", content: "..."}]
        - NO filtering of fulfilled artifact requests
        |
        v
Step 8: Backend ai_service.py:stream_chat()
        - Sends SYSTEM_PROMPT + conversation + tools to Claude
        - Claude sees ALL prior "Generate X" messages in history
        - Claude calls save_artifact for EACH one it deems actionable
        - Tool loop continues until no more tool_use blocks
        |
        v
Step 9: Backend conversations.py:event_generator()
        - Accumulates text_delta events
        - Yields tool_executing, artifact_created, text_delta events
        - save_message(db, thread_id, "assistant", accumulated_text)  <-- SAVED TO DB
        |
        v
Step 10: Frontend conversation_provider.dart:sendMessage()
         - Processes TextDeltaEvent, ToolExecutingEvent, ArtifactCreatedEvent, MessageCompleteEvent
         - Adds assistant message to _messages
         - Adds artifact to _artifacts
```

### The Bug: Why N Requests Create N Artifacts

```
Turn 1: User sends "Generate User Stories"
        History: [user: "Generate User Stories"]
        Claude sees 1 generation request -> generates 1 artifact

Turn 2: User sends "Generate BRD"
        History: [user: "Generate User Stories",
                  assistant: "Done! I've created User Stories...",
                  user: "Generate BRD"]
        Claude sees 2 generation-related messages -> generates 1 or 2 artifacts

Turn 3: User sends "Generate Requirements Doc"
        History: [user: "Generate User Stories",
                  assistant: "Done! ...",
                  user: "Generate BRD",
                  assistant: "Done! ...",
                  user: "Generate Requirements Doc"]
        Claude sees 3 generation requests -> generates up to 3 artifacts
```

The root cause is the combination of:
1. No prompt rule saying "only act on latest request"
2. Tool description saying "You may call this tool multiple times"
3. No structural marking of fulfilled requests in history
4. Every generation request entering the permanent message history

---

## Fix Architecture: 4-Layer Defense in Depth

### Layer Diagram

```
+------------------------------------------------------------------+
|                      Layer 1: Prompt Engineering                  |
|  File: ai_service.py SYSTEM_PROMPT                               |
|  What: Add ARTIFACT DEDUPLICATION critical rule (priority 2)     |
|  Effect: Model instructed to only act on MOST RECENT request     |
+------------------------------------------------------------------+
                              |
+------------------------------------------------------------------+
|                      Layer 2: Tool Definition                    |
|  File: ai_service.py SAVE_ARTIFACT_TOOL                         |
|  What: Replace "may call multiple times" with single-call rule   |
|  Effect: Model instructed to call tool ONCE per user request     |
+------------------------------------------------------------------+
                              |
+------------------------------------------------------------------+
|                      Layer 3: Structural History Filtering       |
|  File: conversation_service.py build_conversation_context()      |
|  What: Annotate fulfilled artifact requests with prefix          |
|  Effect: Context itself signals which requests are complete      |
+------------------------------------------------------------------+
                              |
+------------------------------------------------------------------+
|                      Layer 4: UX (Silent Generation)             |
|  Files: conversations.py, conversation_provider.dart,            |
|         conversation_screen.dart, ai_service.dart                |
|  What: Button-triggered artifacts skip message history entirely  |
|  Effect: Zero accumulation for button-triggered requests         |
+------------------------------------------------------------------+
```

### Why 4 Layers (Defense in Depth)

Each layer addresses a different failure mode:

| Layer | What It Prevents | Failure Mode If Only Layer |
|-------|------------------|---------------------------|
| 1. Prompt rule | Model re-triggering old requests | Model may ignore prompt in long contexts |
| 2. Tool description | Multiple tool calls per turn | Doesn't prevent across-turn accumulation |
| 3. History annotation | Structural ambiguity in context | Model may not interpret annotation correctly |
| 4. Silent generation | Messages entering history at all | Only covers button-triggered, not typed requests |

Layers 1+2+3 together handle **typed** artifact requests (user types "generate BRD").
Layer 4 handles **button-triggered** artifact requests (user clicks sparkle button).
All 4 together provide complete coverage.

---

## Component Boundaries and Responsibilities

### Files to Modify (No New Files for Layers 1-3)

| # | File | Layer | Change Type | Scope |
|---|------|-------|-------------|-------|
| 1 | `backend/app/services/ai_service.py` | 1+2 | Modify constants | SYSTEM_PROMPT XML, SAVE_ARTIFACT_TOOL dict |
| 2 | `backend/app/services/conversation_service.py` | 3 | Modify function | build_conversation_context() |
| 3 | `backend/app/routes/conversations.py` | 4 | Modify model + endpoint | ChatRequest, stream_chat(), event_generator() |
| 4 | `frontend/lib/services/ai_service.dart` | 4 | Modify method | streamChat() signature and body payload |
| 5 | `frontend/lib/providers/conversation_provider.dart` | 4 | Add method + state | generateArtifact(), _isGeneratingArtifact |
| 6 | `frontend/lib/screens/conversation/conversation_screen.dart` | 4 | Modify handler | _showArtifactTypePicker() |

### New Widgets (Layer 4 only)

| Widget | Purpose | Location |
|--------|---------|----------|
| GeneratingIndicator | Inline loading animation during silent generation | `frontend/lib/screens/conversation/widgets/generating_indicator.dart` |

---

## Detailed Data Flow Per Layer

### Layer 1: System Prompt Deduplication Rule

**Change location:** `ai_service.py` lines ~120-126, inside `<critical_rules>` XML block

**Data flow (no change to flow, change to content):**

```
SYSTEM_PROMPT string constant
    |
    v
ai_service.py:stream_chat() -> self.adapter.stream_chat(system_prompt=SYSTEM_PROMPT)
    |
    v
Anthropic API receives system prompt with new rule at priority 2
```

**What changes:** The SYSTEM_PROMPT XML gets a new `<rule priority="2">` inserted and
existing rules 2-5 renumbered to 3-6. This is a string constant modification only.

**No runtime flow changes.** The system prompt is already passed on every request.

### Layer 2: Tool Description Single-Call

**Change location:** `ai_service.py` lines ~649-683, SAVE_ARTIFACT_TOOL dict

**Data flow (no change to flow, change to content):**

```
SAVE_ARTIFACT_TOOL dict constant
    |
    v
AIService.__init__() -> self.tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]
    |
    v
ai_service.py:stream_chat() -> self.adapter.stream_chat(tools=self.tools)
    |
    v
Anthropic API receives tool definition with updated description
```

**What changes:** Line 663's `"You may call this tool multiple times to create multiple
artifacts."` is replaced with single-call enforcement text. This is a dict constant
modification only.

**No runtime flow changes.** Tools are already passed on every request.

### Layer 3: History Annotation in build_conversation_context()

**Change location:** `conversation_service.py` lines 77-117

**Current data flow:**

```
DB: messages table
    |  SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at
    v
[msg1, msg2, msg3, msg4, msg5, ...]
    |  Convert each to {role, content}
    v
[{role:"user", content:"..."}, {role:"assistant", content:"..."}, ...]
    |  (optional truncation)
    v
Returned to caller (conversations.py:stream_chat)
```

**New data flow:**

```
DB: messages table
    |  SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at
    v
[msg1, msg2, msg3, msg4, msg5, ...]
    |  Convert each to {role, content}
    |
    |  NEW: For each assistant message, check if it contains
    |       "Artifact saved successfully" (the marker from ai_service.py:733)
    |       If yes, prefix the PRECEDING user message with
    |       "[ALREADY FULFILLED - artifact was generated] "
    v
[{role:"user", content:"[ALREADY FULFILLED...] Generate User Stories..."},
 {role:"assistant", content:"Done! I've created..."},
 {role:"user", content:"Generate BRD from this conversation."}]
    |  (optional truncation)
    v
Returned to caller
```

**CRITICAL CORRECTION from BUG-019:** The user story references `ARTIFACT_CREATED:`
marker from dead code (`agent_service.py:174`). The actual marker in the active code path
is the string `"Artifact saved successfully"` at `ai_service.py:733`. However, this
string is the tool RESULT returned to Claude during the tool loop -- it is NOT saved
to the database as the assistant message.

What IS saved to the database is `accumulated_text` (conversations.py:183), which is the
model's TEXT output only (not tool results). The model typically responds with something
like `"Done! I've created Business Requirements Document..."` after receiving the tool
result.

**Detection strategies (ranked by reliability):**

1. **Best: Query artifacts table** -- Check if there are artifacts in the thread that
   were created between consecutive messages. This is a structural guarantee with zero
   false positives.

2. **Good: Check for artifact_created SSE event pattern** -- Not available in stored
   messages.

3. **Acceptable: Heuristic on assistant text** -- Look for phrases like
   "I've created", "saved successfully", "artifact", "generated". Fragile, depends on
   model's exact phrasing.

4. **Alternative: Store a metadata flag on messages** -- Add an `artifact_fulfilled`
   boolean column to the messages table. Set it when `save_message()` is called for
   assistant messages after an artifact was created. Most reliable but requires a schema
   migration.

**Recommendation:** Use option 1 (query artifacts table) as primary detection, falling
back to heuristic text matching. The artifacts table has `created_at` timestamps that can
be correlated with message timestamps.

Simplified implementation:

```python
# After loading messages, load artifact creation timestamps for the thread
artifact_stmt = select(Artifact.created_at).where(Artifact.thread_id == thread_id)
artifact_result = await db.execute(artifact_stmt)
artifact_times = [r[0] for r in artifact_result.all()]

# For each user message, check if an artifact was created AFTER it
# (meaning the request was fulfilled)
for i, msg in enumerate(messages):
    if msg.role == "user":
        # Check if any artifact was created between this message and the next user message
        msg_time = msg.created_at
        next_user_time = find_next_user_time(messages, i)
        if any(msg_time <= at <= next_user_time for at in artifact_times):
            # This user message triggered an artifact generation
            conversation[i]["content"] = "[ALREADY FULFILLED] " + conversation[i]["content"]
```

However, the simpler heuristic from BUG-019 (checking the assistant message text) is also
viable if the detection string is corrected. The assistant text will contain phrases like
"created", "generated", "saved" when artifacts were produced. This may have false positives
for conversations about artifacts without actually generating them, but in practice the
system prompt is highly structured.

**Recommended approach for v1.9.4:** Use the assistant text heuristic with the corrected
marker string, as it avoids schema changes and extra DB queries. The text to detect should
be `"Artifact saved successfully"` OR phrases like tool result confirmation patterns.

Actually, there is an even simpler and more reliable approach: **Check if the assistant
message content block in the Anthropic API format includes a `tool_use` block with
`name: "save_artifact"`.** But this information is lost -- the assistant message is saved
as plain text (only `accumulated_text`), not as structured content blocks.

**Final recommendation:** The simplest reliable approach is to search assistant messages
for the confirmation phrase the model produces after calling `save_artifact`. The model
consistently says something about creating/generating the artifact in its follow-up text.
But since we cannot guarantee exact phrasing, the **artifacts table query** (option 1) is
the most robust.

### Layer 4: Silent Generation (New Frontend/Backend Flow)

**Current flow (button click):**

```
User clicks sparkle -> ArtifactTypePicker -> "Generate User Stories"
    |
    v
conversation_provider.sendMessage("Generate User Stories from this conversation.")
    |
    v
[User bubble appears in chat]
    |
    v
POST /api/threads/{id}/chat  body: {"content": "Generate User Stories..."}
    |
    v
Backend: save_message(user) -> build_context -> stream_chat -> save_message(assistant)
    |
    v
[text_delta events -> streaming text in UI]
[artifact_created event -> artifact card in UI]
[message_complete -> assistant bubble in UI]
```

**New flow (button click with artifact_generation flag):**

```
User clicks sparkle -> ArtifactTypePicker -> "Generate User Stories"
    |
    v
conversation_provider.generateArtifact("Generate User Stories from this conversation.")
    |  (NEW method, separate from sendMessage)
    |
    v
[Loading indicator appears in chat area, NO user bubble]
    |
    v
POST /api/threads/{id}/chat  body: {"content": "Generate User Stories...",
                                     "artifact_generation": true}
    |
    v
Backend: NO save_message(user)
         build_context(db, thread_id) as before
         Append ephemeral instruction to context (NOT saved to DB):
           "Generate the artifact silently. Only call save_artifact and stop."
         stream_chat(conversation, ...) as before
    |
    v
SSE stream:
  - text_delta events: SUPPRESSED (not yielded to client)
  - tool_executing events: yielded normally
  - artifact_created events: yielded normally
  - message_complete events: yielded (for cleanup), BUT no save_message(assistant)
    |
    v
Frontend:
  - On artifact_created: add to _artifacts list, dismiss loading indicator
  - On message_complete: clear generating state
  - On error: clear generating state, show error
  - NO user message added to _messages
  - NO assistant message added to _messages
```

**Key architectural decisions for Layer 4:**

1. **Ephemeral context message:** The generation prompt is appended to the conversation
   context array sent to Claude but NOT saved to the messages table. This means it cannot
   accumulate across turns.

2. **Server-side text suppression:** The backend filters `text_delta` events when
   `artifact_generation=true`. This is a safety net -- even if Claude generates text
   despite the silent instruction, the frontend never receives it.

3. **Token tracking still works:** The `message_complete` event still carries `usage`
   data. Token tracking in `event_generator()` still fires. Only message persistence
   is skipped.

4. **Thread summary skipped:** Since no messages are saved, `maybe_update_summary()` can
   be skipped for silent requests (or called but will no-op since message count hasn't
   changed).

---

## Dependency Graph and Build Order

```
Layer 1 (Prompt Rule)  ----+
                            |
Layer 2 (Tool Desc)    ----+----> All backend prompt/tool changes
                            |     can be done in one commit
Layer 3 (History Filter)---+     (no interdependencies)

Layer 4 (Silent Gen)   --------> Depends on nothing above, but
                                  should be built last since it's
                                  the most complex (frontend + backend)
```

### Recommended Build Order

| Phase | Layer | Files | Rationale |
|-------|-------|-------|-----------|
| Phase 1 | Layers 1+2 | `ai_service.py` | Pure string constant changes. Zero risk. Immediate partial fix for typed requests. Can be tested together. |
| Phase 2 | Layer 3 | `conversation_service.py` | Single function modification. Unit-testable in isolation. Completes the typed-request fix. |
| Phase 3 | Layer 4 | `conversations.py`, `conversation_provider.dart`, `conversation_screen.dart`, `ai_service.dart`, new `generating_indicator.dart` | Most complex. Touches both frontend and backend. Should be built after layers 1-3 provide the safety net. |

**Why this order:**
- Layers 1+2 together provide immediate improvement for the most common case
- Layer 3 provides structural guarantee regardless of model behavior
- Layer 4 is an enhancement that eliminates the problem for button-triggered requests
  but is the highest-risk change (more files, new API contract, frontend state)
- If Layer 4 has issues, Layers 1+2+3 still prevent the bug for all paths

### Dependency Details

```
Phase 1 (Layers 1+2):
  ai_service.py SYSTEM_PROMPT  <- modify string constant (lines ~120-126)
  ai_service.py SAVE_ARTIFACT_TOOL <- modify dict constant (line ~663)
  Dependencies: NONE
  Risk: LOW (prompt-only changes)

Phase 2 (Layer 3):
  conversation_service.py build_conversation_context() <- modify function
  Dependencies: NONE (complements but does not depend on Phase 1)
  Risk: LOW-MEDIUM (need to choose correct detection strategy)

  NOTE: If using artifacts table query, needs:
    - Import Artifact model
    - Additional DB query in build_conversation_context()
    - Be aware of async session scope

Phase 3 (Layer 4):
  Backend:
    conversations.py ChatRequest <- add artifact_generation field
    conversations.py stream_chat() <- conditional save/suppress logic
    conversations.py event_generator() <- filter text_delta events
  Frontend:
    ai_service.dart streamChat() <- add artifactGeneration parameter
    conversation_provider.dart <- add generateArtifact() method, _isGeneratingArtifact state
    conversation_screen.dart <- modify _showArtifactTypePicker handler
    NEW: generating_indicator.dart <- loading animation widget
  Dependencies:
    - Backend changes must deploy before frontend changes (new API field)
    - Frontend ai_service.dart must send new field before provider uses it
  Risk: MEDIUM (API contract change, new frontend state, new widget)
```

---

## Integration Points and Risks

### Risk 1: Marker Detection in Layer 3

**Problem:** BUG-019 references `ARTIFACT_CREATED:` which is dead code. The active path
saves only the model's text response, which varies.

**Mitigation:** Use artifacts table query instead of text heuristic. The artifacts table
has reliable data about which artifacts exist and when they were created.

**Alternative mitigation:** Add a deterministic marker to the tool result that gets
reflected in the model's response. For example, change the tool result string in
`execute_tool()` to include a parseable tag:

```python
return (
    f"[ARTIFACT_SAVED] Artifact saved successfully: '{artifact.title}' (ID: {artifact.id}). "
    "User can now export as PDF, Word, or Markdown from the artifacts list.",
    event_data
)
```

Then the model's follow-up text will likely echo or reference `[ARTIFACT_SAVED]`. However,
this is still not guaranteed since the tool result goes to Claude (not saved to DB) and
Claude's text response is what gets saved.

**Best approach:** Query the artifacts table. It is the single source of truth.

### Risk 2: Backward Compatibility of ChatRequest

**Problem:** Adding `artifact_generation: bool = Field(default=False)` to ChatRequest.
Old frontend versions won't send this field.

**Mitigation:** Default value of `False` means old clients work exactly as before. This
is a non-breaking change. The `Field(default=False)` makes the field optional.

### Risk 3: Token Tracking for Silent Requests

**Problem:** When `artifact_generation=true`, the `accumulated_text` is empty (text_delta
suppressed). But `message_complete` still carries usage data.

**Mitigation:** Token tracking uses `usage_data` from `message_complete`, not
`accumulated_text`. It will work correctly. Verify that the `if usage_data:` block at
conversations.py:186-193 still fires for silent requests.

### Risk 4: Thread Summary for Silent Requests

**Problem:** `maybe_update_summary()` at conversations.py:197 is called after every chat.
For silent requests, no new messages were saved, so the summary update is wasted work.

**Mitigation:** Skip the call when `artifact_generation=true`:
```python
if not body.artifact_generation:
    await maybe_update_summary(db, thread_id, current_user["user_id"])
```

### Risk 5: Error Handling in Silent Mode

**Problem:** If artifact generation fails (Claude returns error, tool execution fails, or
network drops), the frontend needs to clear the loading state and show an error.

**Mitigation:** The `generateArtifact()` method in conversation_provider must handle:
- `ErrorEvent` -> set error, clear _isGeneratingArtifact
- Stream exception -> set error, clear _isGeneratingArtifact
- `message_complete` without preceding `artifact_created` -> this means Claude didn't
  call the tool. Should be treated as a soft failure with user-visible message.

### Risk 6: Multi-Provider Support

**Problem:** The system uses an LLM adapter pattern with Anthropic, Gemini, and DeepSeek
adapters. Prompt changes (Layers 1+2) go through the adapter's `stream_chat()` method.

**Mitigation:** The SYSTEM_PROMPT and tools are passed identically to all adapters. The
new rules are provider-agnostic natural language. All providers should respect them.
Layer 3 (history annotation) is provider-agnostic by design.

---

## Testing Strategy Per Layer

| Layer | Test Type | What to Test |
|-------|-----------|-------------|
| 1 | Unit | SYSTEM_PROMPT contains deduplication rule at priority 2 |
| 1 | Unit | Rule priorities renumbered correctly (1-6) |
| 2 | Unit | SAVE_ARTIFACT_TOOL description contains "ONCE per user request" |
| 2 | Unit | SAVE_ARTIFACT_TOOL description does NOT contain "multiple times" |
| 3 | Unit | build_conversation_context marks fulfilled requests |
| 3 | Unit | Unfulfilled requests are NOT marked |
| 3 | Unit | Failed generation attempts are NOT marked |
| 3 | Integration | Two sequential generation requests produce 1 artifact each |
| 4 | Unit | ChatRequest accepts artifact_generation field (defaults False) |
| 4 | Unit | text_delta events suppressed when artifact_generation=true |
| 4 | Unit | User message NOT saved when artifact_generation=true |
| 4 | Unit | Assistant message NOT saved when artifact_generation=true |
| 4 | Unit | artifact_created event still emitted in silent mode |
| 4 | Integration | Button-triggered generation shows only artifact card |
| 4 | E2E | Full flow: button -> loading -> artifact card, no chat bubbles |

---

## Summary of Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| 4 layers not 1 | Defense in depth; each layer catches what others miss |
| Prompt + structural fixes | Prompt alone is unreliable for long contexts |
| Silent generation as separate code path | Clean separation; existing sendMessage untouched |
| Artifacts table for detection (Layer 3) | Most reliable; single source of truth |
| Server-side text suppression | Safety net; model may ignore silent instruction |
| Optional API field with default | Backward-compatible; old clients unaffected |
| Ephemeral context message | Generation prompt never enters DB; cannot accumulate |

---

## Sources

All findings from direct codebase analysis:
- `backend/app/services/ai_service.py` (lines 114-882) -- SYSTEM_PROMPT, tools, stream_chat
- `backend/app/services/conversation_service.py` (lines 77-117) -- build_conversation_context
- `backend/app/routes/conversations.py` (lines 34-211) -- ChatRequest, stream_chat endpoint
- `frontend/lib/providers/conversation_provider.dart` (lines 134-209) -- sendMessage
- `frontend/lib/services/ai_service.dart` (lines 111-179) -- streamChat SSE handling
- `frontend/lib/screens/conversation/conversation_screen.dart` (lines 198-216) -- artifact picker
- `backend/app/services/agent_service.py` (dead code, for marker comparison only)
- `user_stories/BUG-016_artifact-generation-multiplies.md` -- Root cause analysis
- `user_stories/BUG-017_prompt-deduplication-rule.md` -- Layer 1 spec
- `user_stories/BUG-018_tool-description-single-call.md` -- Layer 2 spec
- `user_stories/BUG-019_history-filtering-fulfilled-requests.md` -- Layer 3 spec
- `user_stories/THREAD-011_silent-artifact-generation.md` -- Layer 4 spec
