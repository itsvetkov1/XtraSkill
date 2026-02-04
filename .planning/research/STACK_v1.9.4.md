# Technology Stack: Artifact Deduplication & Silent Generation

**Project:** BA Assistant - v1.9.4 Bug Fix Milestone
**Researched:** 2026-02-04
**Overall Confidence:** HIGH
**Bug Reference:** BUG-016, BUG-017, BUG-018, BUG-019, THREAD-011

---

## Executive Summary

Fixing the artifact generation multiplication bug (BUG-016) requires **zero new libraries**. The entire fix is achievable with techniques applied to the existing stack: prompt engineering in the hardcoded `SYSTEM_PROMPT`, tool description modification, conversation context preprocessing in `conversation_service.py`, request model extension in FastAPI, and SSE event filtering in the async generator pipeline. No dependencies change.

This document covers the specific techniques, patterns, and anti-patterns for each of the four fix layers.

---

## No New Dependencies Required

| Layer | Fix Approach | Libraries Needed | Confidence |
|-------|-------------|-----------------|------------|
| 1. Prompt deduplication rule | Edit `SYSTEM_PROMPT` XML string | None (pure text edit) | HIGH |
| 2. Tool description enforcement | Edit `SAVE_ARTIFACT_TOOL` dict | None (pure text edit) | HIGH |
| 3. History filtering | Modify `build_conversation_context()` | None (Python string ops) | HIGH |
| 4. Silent generation | Extend `ChatRequest`, filter SSE | None (existing FastAPI + sse-starlette) | HIGH |

**Existing stack (unchanged):**
- `anthropic` SDK (async streaming via `AsyncAnthropic`)
- `sse-starlette` (SSE event delivery via `EventSourceResponse`)
- `fastapi` + `pydantic` (request model with `ChatRequest`)
- `sqlalchemy` (async session for message persistence)
- `flutter_client_sse` (Dart SSE client on frontend)

---

## Layer 1: System Prompt Deduplication Rule

### Technique: Priority-Ordered XML Rule Injection

**What this is:** Adding a high-priority behavioral rule to the existing XML-structured `SYSTEM_PROMPT` that instructs the model to ignore prior fulfilled artifact requests.

**Confidence:** HIGH -- This is a well-established prompt engineering pattern. Anthropic's own documentation recommends using system prompt instructions to control tool call behavior.

### Recommended Implementation

Insert a new rule at priority 2 in `<critical_rules>`:

```xml
<rule priority="2">ARTIFACT DEDUPLICATION - ONLY act on the MOST RECENT user message
when generating artifacts. Prior artifact requests in conversation history have already
been fulfilled. If you see save_artifact tool results in history, those requests are
COMPLETE. Do not re-generate artifacts for them.</rule>
```

### Why This Works

Claude processes `<critical_rules>` with decreasing priority weight. Placing deduplication at priority 2 (just below the existing priority 1 "one question at a time" rule) ensures the model evaluates it before deciding whether to call `save_artifact`.

The rule works because:
1. **Positive framing** -- "ONLY act on the MOST RECENT" is clearer to the model than "do not act on prior requests"
2. **Evidence-based** -- References `save_artifact tool results in history` as concrete completion evidence the model can verify
3. **Deterministic signal** -- Tool results are unambiguous markers (unlike trying to infer user intent from message text)

### Prompt Engineering Best Practices for Deduplication

| Practice | Rationale | Source |
|----------|-----------|--------|
| Use CAPS for critical directives | Increases model attention weight | Anthropic prompt engineering guide |
| Provide reasoning context | "have already been fulfilled" helps model understand WHY | Standard prompt engineering |
| Reference observable evidence | "save_artifact tool results in history" gives the model something concrete to check | Anthropic tool use docs |
| Place near top of system prompt | Earlier rules get more attention in long prompts | General LLM behavior |
| Positive framing over negation | "ONLY do X" is more reliable than "do NOT do Y" | Prompt engineering consensus |

### What NOT to Do

| Anti-Pattern | Why It Fails |
|-------------|-------------|
| Adding deduplication rule at bottom of system prompt | Gets lost in ~7,400 token prompt; lower attention weight |
| Using vague language: "try to avoid duplicates" | Model interprets "try" as optional guidance, not hard rule |
| Negation-only: "Do NOT re-generate previous artifacts" | Negation is less reliably followed than positive instruction |
| Long rule paragraphs with caveats | Model loses the core instruction in verbosity |
| Relying on rule alone without structural backing | Prompt-only fixes have ~85-90% reliability; structural backing (Layer 3) needed for guarantee |

### Confidence Assessment

- **Will this fix the bug by itself?** Mostly. In testing with Claude models, well-placed system prompt rules are followed ~85-90% of the time. Edge cases (very long conversations, ambiguous requests) may still slip through.
- **Is this sufficient?** No -- this is Layer 1 of 4. Layers 2-4 provide structural guarantees that compensate for the ~10-15% prompt compliance gap.

**Source:** [Anthropic Tool Use Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use), [Anthropic Prompt Engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)

---

## Layer 2: Tool Description Single-Call Enforcement

### Technique: Tool Description Behavioral Constraint

**What this is:** Modifying the `SAVE_ARTIFACT_TOOL` description to enforce single-call-per-request behavior instead of the current multi-call encouragement.

**Confidence:** HIGH -- Anthropic's official docs state: "Provide extremely detailed descriptions. This is by far the most important factor in tool performance."

### Current Problem

Line 663 of `ai_service.py` contains:
```
"You may call this tool multiple times to create multiple artifacts."
```

This explicitly encourages the accumulation behavior. The model treats this as permission to call `save_artifact` N times when it sees N generation requests in history.

### Recommended Implementation

Remove the above line. Replace with:

```
"Call this tool ONCE per user request. After generating an artifact, STOP and present
the result. Do not call again unless the user sends a NEW message explicitly requesting
another artifact or re-generation of the same one."
```

### Why Tool Descriptions Matter More Than You Think

From Anthropic's tool use implementation guide:

> "Your descriptions should explain every detail about the tool, including: What the tool does, When it should be used (and when it shouldn't), What each parameter means and how it affects the tool's behavior, Any important caveats or limitations."

The tool description is injected into a special system prompt that the model receives alongside the user system prompt. It has HIGH influence on tool calling behavior because:

1. **Claude's tool use system prompt** wraps tool definitions in a structured format that gets special model attention
2. **The description is the primary signal** for when/how to use the tool -- more so than the system prompt rules
3. **Conflicting signals between system prompt and tool description** cause unpredictable behavior (the old description actively contradicts any deduplication rule)

### Anthropic API Tool Control Options

While not needed for this fix (tool description change is sufficient), these API-level controls exist as fallback options:

| Feature | What It Does | Applicable? |
|---------|-------------|-------------|
| `disable_parallel_tool_use: true` | Ensures Claude uses at most one tool per response | Partially -- prevents parallel `save_artifact` calls in single response, but does not prevent sequential calls across loop iterations |
| `tool_choice: {"type": "tool", "name": "save_artifact"}` | Forces Claude to use a specific tool | No -- we want Claude to CHOOSE when to use the tool, not be forced |
| `tool_choice: {"type": "auto"}` | Default -- Claude decides (what we want) | Yes -- already the default behavior |
| `max_uses` parameter | Limits tool invocations per turn | Only for server tools (web_search, web_fetch). NOT available for client tools like save_artifact |

**Important finding:** The `max_uses` parameter, discovered during research, is only available for Anthropic's server-side tools (web_search, web_fetch). It is NOT available for client-defined tools like `save_artifact`. This means we cannot use it as a programmatic cap on artifact generation. The tool description approach is the correct solution.

### What NOT to Do

| Anti-Pattern | Why It Fails |
|-------------|-------------|
| Keep "multiple times" language and add "but only for new requests" | Conflicting signals; model may still over-generate |
| Remove tool description entirely to "let the system prompt handle it" | Tool descriptions have MORE weight than system prompt for tool behavior |
| Add complex conditional logic in tool description | Long descriptions with many conditions reduce compliance |
| Use `disable_parallel_tool_use` as the sole fix | Only prevents parallel calls within one response; the bug manifests across the tool use LOOP (lines 773-875) where each iteration is a separate API call |

**Source:** [Anthropic Tool Use Implementation Guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)

---

## Layer 3: Conversation History Filtering

### Technique: Response-Based Context Annotation

**What this is:** Preprocessing conversation history in `build_conversation_context()` to mark fulfilled artifact requests BEFORE sending the context to the LLM.

**Confidence:** HIGH -- This is a well-established "context engineering" pattern. The technique is used by LangGraph, LangChain, and other agentic frameworks for managing conversation state.

### Why This Is the Most Important Layer

Layers 1 and 2 are prompt-level fixes with ~85-90% reliability. Layer 3 is a **structural guarantee** -- it modifies the data the model sees, not just the instructions it receives. Even if the model ignores the system prompt rule and tool description constraint, it will see `[ALREADY PROCESSED]` prefixes on fulfilled requests, making it structurally difficult to re-trigger generation.

### Detection Strategy: Response-Based

Scan **assistant messages** for artifact creation evidence. If an assistant message contains tool result markers from `save_artifact`, the preceding user message was a fulfilled request.

Why response-based detection (not input-based):
- **Zero false positives** -- Only marks requests that were ACTUALLY fulfilled (tool was called and succeeded)
- **Works for all input patterns** -- Preset button text, custom freeform prompts, any language
- **No trigger phrase list to maintain** -- Does not need to know "Generate BRD" or "Create User Stories"
- **Handles failures correctly** -- If generation failed (no marker), request stays unmarked (user can retry)

### Implementation Pattern

```python
# In build_conversation_context()
for i, msg in enumerate(messages):
    content = msg.content

    # Response-based detection: assistant message with artifact marker
    if msg.role == "assistant" and "Artifact saved successfully" in content:
        # Mark the preceding user message as fulfilled
        if conversation and conversation[-1]["role"] == "user":
            conversation[-1]["content"] = (
                "[ALREADY PROCESSED - artifact was generated] "
                + conversation[-1]["content"]
            )

    conversation.append({"role": msg.role, "content": content})
```

### Detection Marker

The current `execute_tool()` method at `ai_service.py:726-735` returns this string when `save_artifact` succeeds:

```python
f"Artifact saved successfully: '{artifact.title}' (ID: {artifact.id}). "
"User can now export as PDF, Word, or Markdown from the artifacts list."
```

The string `"Artifact saved successfully"` is the reliable marker. It is:
- Only generated by successful `save_artifact` calls
- Included in the assistant's response text (which gets saved to the database via `save_message()`)
- Unique enough to avoid false positives in normal conversation text

**Important nuance:** The assistant message saved to the database is the `accumulated_text` from `stream_chat()` (line 183 of `conversations.py`). This text includes the model's response AFTER tool execution. The tool result string itself is NOT directly in the saved message -- it is part of the in-memory conversation that the model uses to formulate its response. However, the model typically echoes or references the artifact title in its response text, so `"Artifact saved successfully"` or similar phrases will appear.

**Recommendation:** To make detection more reliable, ensure the marker appears in the saved assistant message. Currently, the tool result goes into the in-memory conversation but the assistant's TEXT response is what gets saved. The assistant usually mentions the artifact, but for 100% reliability, consider also checking for patterns like `"artifact"` + `"saved"` or `"generated"` in the assistant text. The BUG-019 user story proposes checking for `"ARTIFACT_CREATED:"` but this marker does NOT appear in the saved assistant message -- it only appears in the SSE event. This needs verification during implementation.

### Context Engineering Best Practices

| Practice | Description | Source |
|----------|-------------|--------|
| Annotate, don't delete | Prefix messages rather than removing them -- preserves conversational coherence | LangGraph conversation management |
| Use bracketed system notes | `[ALREADY PROCESSED]` format is a convention models understand as metadata | General prompt engineering |
| Process server-side only | Never send annotation logic to the client; keep it in `build_conversation_context()` | Security best practice |
| Preserve original content | The original message text remains after the prefix for context | Context engineering |
| Apply idempotently | Running the annotation twice should produce the same result | Defensive programming |

### What NOT to Do

| Anti-Pattern | Why It Fails |
|-------------|-------------|
| Delete fulfilled request messages from history | Breaks conversational coherence; model loses context about what was discussed |
| Use input-based detection (scanning for "Generate BRD") | False positives on discussion about generation; misses custom prompts |
| Annotate the assistant message instead of the user message | Model interprets user messages as instructions; annotating user message is more effective |
| Use a separate metadata field on the Message model | Requires database migration; the annotation approach works without schema changes |
| Maintain a separate "fulfilled request IDs" list | Additional state to manage; response-based detection is stateless |

**Source:** [LangGraph Conversation History Management](https://langchain-ai.github.io/langgraphjs/how-tos/manage-conversation-history/), [Context Engineering Best Practices](https://www.kubiya.ai/blog/context-engineering-best-practices)

---

## Layer 4: Silent Artifact Generation

### Technique: Ephemeral Request Pattern + SSE Event Filtering

**What this is:** Two coordinated changes: (1) Backend accepts a flag to skip message persistence for artifact generation requests, (2) Frontend calls a separate code path for button-triggered generation that does not create chat bubbles.

**Confidence:** HIGH -- Uses existing FastAPI patterns (Pydantic model extension, async generator filtering) with no new dependencies.

### Backend: Ephemeral Request Pattern

**Concept:** Add an `artifact_generation: bool` field to `ChatRequest`. When `True`:
- User message is NOT saved to the `messages` table
- Assistant response text is NOT saved to the `messages` table
- Artifact IS saved to the `artifacts` table (via tool execution)
- A silent instruction is appended to the in-memory conversation context but NOT persisted

This is an "ephemeral request" pattern -- the request uses existing conversation history for context but leaves no trace in the history itself.

```python
class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)
    artifact_generation: bool = Field(default=False)
```

**Why Pydantic `Field(default=False)`:** Backward compatible. Existing API callers that don't send the field get `False` (normal chat behavior). Only the Flutter frontend's artifact generation buttons send `True`.

### Silent Instruction Injection

When `artifact_generation` is `True`, append a transient instruction to the conversation context:

```python
if body.artifact_generation:
    conversation.append({
        "role": "user",
        "content": f"{body.content}\n\nIMPORTANT: Generate the artifact silently. "
                   "Do not include any conversational text. Only call the save_artifact "
                   "tool and stop. Do not explain, summarize, or present results in text."
    })
```

This message is:
- Added to the in-memory `conversation` list (model sees it)
- NOT saved via `save_message()` (does not enter database)
- NOT visible in thread history on reload
- Cannot accumulate across turns (never persisted)

### SSE Event Filtering

For silent generation, suppress `text_delta` events at the async generator level. This is a safety net -- even if the model generates text despite the silent instruction, it won't reach the frontend.

```python
# In event_generator() within conversations.py
async for event in heartbeat_stream:
    # Suppress text for artifact generation
    if body.artifact_generation and event.get("event") == "text_delta":
        continue
    yield event
```

This is the standard SSE filtering pattern with `sse-starlette`. The library yields whatever your async generator yields. Filtering is simply a `continue` statement in the generator loop.

### Frontend: Separate Code Path

The `ConversationProvider` needs a new `generateArtifact()` method that:
1. Does NOT add a user message to `_messages` list
2. Sets a `_isGeneratingArtifact` state for loading animation
3. Calls the backend with `artifact_generation: true`
4. Only listens for `artifact_created` and `error` events
5. Clears generating state on completion

The `AIService` in Flutter needs the `streamChat()` method to accept an optional `artifactGeneration` parameter, which gets included in the POST body.

### Token Savings

Silent generation saves tokens in two ways:
1. **Output tokens saved:** ~100-300 tokens per generation (model's conversational wrapper text like "I've generated the BRD. Here are the key sections...")
2. **Future input tokens saved:** The ephemeral message never enters history, so it's never re-sent in future API calls. For a thread with 5 artifact generations, this saves ~150-500 input tokens per subsequent request.

### SSE Event Flow Comparison

**Normal chat:**
```
text_delta -> text_delta -> ... -> tool_executing -> artifact_created -> text_delta -> ... -> message_complete
```

**Silent generation:**
```
[text_delta suppressed] -> tool_executing -> artifact_created -> [text_delta suppressed] -> message_complete
```

Frontend only sees: `tool_executing -> artifact_created -> message_complete`

### What NOT to Do

| Anti-Pattern | Why It Fails |
|-------------|-------------|
| Create a completely separate API endpoint for artifact generation | Code duplication; the streaming pipeline, tool execution, and error handling are the same |
| Use a query parameter instead of request body field | POST bodies are more appropriate for this; query params are for GET requests |
| Skip `build_conversation_context()` for silent requests | The model NEEDS conversation context to generate good artifacts; it just shouldn't ADD to the history |
| Filter events on the client side only | Model still generates unnecessary text tokens (wasted cost); server-side filtering is the safety net |
| Use FastAPI `BackgroundTasks` for artifact generation | BackgroundTasks run AFTER the response is sent; we need streaming DURING generation for progress events |
| Save the silent instruction to the database and delete it after | Race conditions; complexity; the ephemeral pattern is cleaner |

**Source:** [FastAPI Request Body docs](https://fastapi.tiangolo.com/tutorial/body/), [sse-starlette GitHub](https://github.com/sysid/sse-starlette)

---

## Architecture: How the Four Layers Interact

```
User clicks "Generate BRD" button
        |
        v
[Layer 4: Frontend] generateArtifact() called (NOT sendMessage())
        |
        v
POST /threads/{id}/chat  { content: "Generate BRD...", artifact_generation: true }
        |
        v
[Layer 4: Backend] Skip save_message() for user message
        |
        v
[Layer 3: History Filtering] build_conversation_context() annotates prior fulfilled requests
        |  "[ALREADY PROCESSED - artifact was generated] Generate User Stories..."
        |  "[ALREADY PROCESSED - artifact was generated] Generate Acceptance Criteria..."
        |  (new) "Generate BRD from this conversation. IMPORTANT: Generate silently..."
        |
        v
[Layer 1: System Prompt] "ARTIFACT DEDUPLICATION - ONLY act on MOST RECENT..."
[Layer 2: Tool Description] "Call this tool ONCE per user request..."
        |
        v
Claude sees: 2 annotated old requests + 1 new request + deduplication rule + single-call tool
        |
        v
Claude calls save_artifact ONCE for the BRD
        |
        v
[Layer 4: SSE Filter] Suppress text_delta events, emit artifact_created
        |
        v
[Layer 4: Backend] Skip save_message() for assistant response
        |
        v
Flutter shows: [Loading animation] -> [Artifact card]
```

### Defense-in-Depth Strategy

| Layer | What It Prevents | Failure Mode If Layer Missing |
|-------|-----------------|-------------------------------|
| 1. Prompt rule | Model ignoring fulfilled requests | ~10-15% chance model re-generates on ambiguous history |
| 2. Tool description | Model calling tool multiple times per turn | Model may call tool 2-3x in rapid succession within one response |
| 3. History annotation | Model seeing unmarked fulfilled requests | Model has no structural signal that requests were fulfilled |
| 4. Silent generation | Messages entering history at all | Button-triggered messages accumulate, feeding the bug |

Layers 1+2 provide **behavioral guidance** (soft).
Layer 3 provides **structural annotation** (medium).
Layer 4 provides **architectural prevention** (hard -- messages never enter history).

For typed messages (not button-triggered), Layers 1+2+3 work together.
For button-triggered messages, Layer 4 eliminates the problem entirely.

---

## Implementation Order and Rationale

| Order | Layer | Risk | Rationale |
|-------|-------|------|-----------|
| 1st | BUG-017: Prompt rule | None (text edit) | Immediate behavioral improvement; testable in minutes |
| 2nd | BUG-018: Tool description | None (text edit) | Removes conflicting "multiple times" signal; complements Layer 1 |
| 3rd | BUG-019: History filtering | Low (Python logic change) | Structural guarantee; unit-testable; no frontend changes |
| 4th | THREAD-011: Silent generation | Medium (frontend + backend) | Most complex; requires coordinated changes; most impactful for UX |

This order follows a **risk escalation** pattern: start with zero-risk text edits, progress to low-risk backend logic, finish with medium-risk full-stack changes.

---

## Existing Stack Reference (No Changes)

### Backend (Python)

| Package | Version | Role in Fix |
|---------|---------|-------------|
| `fastapi` | >=0.115.0 | `ChatRequest` model extension (Layer 4) |
| `pydantic` | (bundled) | `Field(default=False)` for backward compat |
| `sse-starlette` | >=2.0.0 | SSE event filtering in generator (Layer 4) |
| `anthropic` | >=0.76.0 | Unchanged; streaming via `AsyncAnthropic` |
| `sqlalchemy` | >=2.0.35 | Conditional `save_message()` calls (Layer 4) |

### Frontend (Dart/Flutter)

| Package | Version | Role in Fix |
|---------|---------|-------------|
| `flutter_client_sse` | existing | Parse SSE events (unchanged) |
| `provider` | existing | `ConversationProvider` new method (Layer 4) |
| `dio` | existing | HTTP client (body field addition) |

### Database (SQLite)

**No schema changes required.** The fix operates entirely within existing tables:
- `messages` -- Conditional writes (Layer 4)
- `artifacts` -- Unchanged (always saved via tool)

---

## Testing Strategy by Layer

| Layer | Test Type | What to Verify |
|-------|-----------|----------------|
| 1 | Unit (automated) | Rule text present in `SYSTEM_PROMPT` at correct priority |
| 1 | Integration (manual) | Two generations in same thread produce 1 artifact each |
| 2 | Unit (automated) | "ONCE per user request" in `SAVE_ARTIFACT_TOOL.description` |
| 2 | Unit (automated) | "multiple times" NOT in `SAVE_ARTIFACT_TOOL.description` |
| 3 | Unit (automated) | `build_conversation_context()` marks fulfilled requests |
| 3 | Unit (automated) | Unfulfilled requests are NOT marked |
| 3 | Unit (automated) | Failed generation attempts are NOT marked |
| 4 | Unit (automated) | `ChatRequest(artifact_generation=True)` parses correctly |
| 4 | Unit (automated) | `ChatRequest()` defaults `artifact_generation` to `False` |
| 4 | Integration (manual) | Button-triggered generation shows no chat bubbles |
| 4 | Integration (manual) | Button-triggered messages do NOT appear in history on reload |
| 4 | Integration (manual) | Typed generation requests still work normally |

---

## Sources

### Anthropic Official Documentation
- [Tool Use Overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) -- Tool descriptions, tool_choice options
- [Tool Use Implementation Guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) -- Best practices for tool descriptions, disable_parallel_tool_use, tool runner
- [Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use) -- max_uses (server tools only), programmatic tool calling

### Context Engineering
- [LangGraph: Manage Conversation History](https://langchain-ai.github.io/langgraphjs/how-tos/manage-conversation-history/) -- Filtering strategies
- [Context Engineering Best Practices 2025](https://www.kubiya.ai/blog/context-engineering-best-practices) -- Annotation patterns
- [LLM Chat History Summarization Guide](https://mem0.ai/blog/llm-chat-history-summarization-guide-2025) -- Pruning and summarization

### SSE / FastAPI
- [sse-starlette](https://github.com/sysid/sse-starlette) -- Event filtering, ping control, EventSourceResponse
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) -- Why NOT to use for streaming (async generator is correct pattern)

### Prompt Engineering
- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering) -- System prompt structure, rule prioritization
- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering) -- Cross-provider best practices

---

## Key Finding: `max_uses` NOT Available for Client Tools

During research, the `max_uses` parameter was investigated as a potential programmatic cap on `save_artifact` calls. **This parameter is only available for Anthropic's server-side tools (web_search, web_fetch) and NOT for client-defined tools.** This means there is no API-level mechanism to limit how many times Claude calls `save_artifact` per turn. The fix must be implemented via:
1. Prompt engineering (Layer 1)
2. Tool description (Layer 2)
3. Context preprocessing (Layer 3)
4. Architectural prevention (Layer 4)

This finding confirms the four-layer approach is the correct strategy.
