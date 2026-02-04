# THREAD-011: Silent Artifact Generation from Buttons

**Priority:** High
**Status:** Open
**Component:** Frontend + Backend / Artifact Generation
**Related:** BUG-016 (also eliminates accumulation for button-triggered requests)
**Implementation Order:** 4 of 4 (implement after BUG-017, BUG-018, BUG-019)

---

## User Story

As a user clicking an artifact generation button,
I want to see a loading animation followed by the artifact card directly,
so that the chat stays clean without unnecessary user/assistant messages.

---

## Problem

Currently, clicking a preset artifact button (User Stories, Acceptance Criteria,
Requirements Doc, BRD) sends a visible message like `"Generate BRD from this conversation."`
into the chat. The AI then responds with text + artifact. This creates two chat bubbles
(user message + assistant response) that clutter the conversation and contribute to the
accumulation bug (BUG-016) since these messages enter the history.

---

## Solution

### Behavioral Change

**Before:**
```
[User bubble] "Generate BRD from this conversation."
[Assistant bubble] "Done! I've created Business Requirements Document..."
[Artifact card]
```

**After:**
```
[Loading animation]
[Artifact card]
```

No user message. No assistant text. Only the artifact card appears.

### Backend Changes

**File:** `backend/app/routes/conversations.py`

**1. Extend request model:**

```python
class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)
    artifact_generation: bool = Field(default=False)
```

**2. Modify `stream_chat` endpoint:**

When `artifact_generation` is `True`:
- Do NOT call `save_message()` for the user message
- Do NOT call `save_message()` for the assistant response after streaming
- DO still call `build_conversation_context()` (existing history needed for generation)
- DO still execute `save_artifact` tool (artifact saved to artifacts table)
- DO still stream SSE events (`tool_executing`, `artifact_created`)
- Do NOT stream `text_delta` events (suppress AI conversational text)

**3. Append silent-generation instruction:**

When `artifact_generation` is `True`, append to the conversation context:

```python
# After building conversation context
if body.artifact_generation:
    conversation.append({
        "role": "user",
        "content": f"{body.content}\n\nIMPORTANT: Generate the artifact silently. "
                   "Do not include any conversational text. Only call the save_artifact "
                   "tool and stop. Do not explain, summarize, or present results in text."
    })
```

This message is appended to context but NOT saved to database, so it:
- Never enters conversation history
- Cannot accumulate across turns
- Instructs the model to skip text generation (saves tokens)

**File:** `backend/app/services/ai_service.py`

**4. Filter text_delta events for silent mode:**

Add a parameter to `stream_chat()` or handle at the route level — when in artifact
generation mode, suppress `text_delta` SSE events before yielding. This is a safety net
in case the model generates text despite the instruction.

```python
# In event_generator() within conversations.py
async for event in heartbeat_stream:
    # Suppress text for artifact generation
    if body.artifact_generation and event.get("event") == "text_delta":
        continue
    yield event
```

### Frontend Changes

**File:** `frontend/lib/screens/conversation/conversation_screen.dart`

**5. Update `_showArtifactTypePicker` handler (lines 198-216):**

When a preset or custom artifact is selected:
- Send request with `artifact_generation: true` flag
- Do NOT add user message to local chat list
- Show a loading/generating animation in the chat area

**File:** `frontend/lib/providers/conversation_provider.dart`

**6. Add `generateArtifact()` method (separate from `sendMessage()`):**

```dart
Future<void> generateArtifact(String prompt) async {
  // Set generating state (triggers loading animation)
  _isGeneratingArtifact = true;
  notifyListeners();

  // Call backend with artifact_generation: true
  await _apiService.streamChat(
    threadId: threadId,
    content: prompt,
    artifactGeneration: true,
  );

  // On artifact_created event: update artifact list
  // On complete: clear generating state
  _isGeneratingArtifact = false;
  notifyListeners();
}
```

**File:** `frontend/lib/screens/conversation/widgets/chat_input.dart`

**7. No changes needed** — button already calls `onGenerateArtifact` callback.

**File:** `frontend/lib/services/api_service.dart` (or equivalent)

**8. Update API call to include flag:**

Add `artifact_generation` parameter to the chat stream request.

### Loading Animation

**Location:** Inline in the chat message list area, at the bottom.

**Behavior:**
- Appears when `_isGeneratingArtifact` is true
- Shows a subtle animation (shimmer or pulsing dot) with text like "Generating..."
- Disappears when `artifact_created` event is received
- Replaced by the artifact card widget

---

## Acceptance Criteria

### Backend
- [ ] `ChatRequest` model accepts optional `artifact_generation` boolean
- [ ] When `artifact_generation: true`, user message is NOT saved to database
- [ ] When `artifact_generation: true`, assistant response is NOT saved to database
- [ ] Artifact IS saved to artifacts table (via `save_artifact` tool)
- [ ] Silent instruction is appended to context but NOT persisted
- [ ] `text_delta` SSE events are suppressed when `artifact_generation: true`
- [ ] `artifact_created` SSE event is still emitted
- [ ] `message_complete` SSE event is still emitted (for cleanup)
- [ ] Regular chat (without flag) is completely unaffected

### Frontend
- [ ] Clicking preset artifact button sends `artifact_generation: true`
- [ ] Clicking custom artifact submit sends `artifact_generation: true`
- [ ] No user message bubble appears in chat for button-triggered generation
- [ ] No assistant text bubble appears for button-triggered generation
- [ ] Loading animation shows during generation
- [ ] Artifact card appears after `artifact_created` event
- [ ] Loading animation disappears after artifact card appears
- [ ] Typed messages (not via button) still work normally — full chat flow

### Edge Cases
- [ ] If generation fails (error event), loading animation clears and error is shown
- [ ] If user disconnects mid-generation, no orphaned messages in database
- [ ] Token tracking still works for artifact generation requests
- [ ] Thread summary update skipped for silent requests (no new messages to summarize)

---

## Technical References

**Backend:**
- `backend/app/routes/conversations.py:34-36` — ChatRequest model
- `backend/app/routes/conversations.py:85-211` — stream_chat endpoint
- `backend/app/services/ai_service.py:755-882` — AIService.stream_chat()

**Frontend:**
- `frontend/lib/screens/conversation/conversation_screen.dart:198-216` — artifact picker handler
- `frontend/lib/screens/conversation/widgets/chat_input.dart:141-146` — sparkle button
- `frontend/lib/screens/conversation/widgets/artifact_type_picker.dart` — type picker modal
- `frontend/lib/providers/conversation_provider.dart` — message sending logic

---

## Architecture Notes

**Why this also helps BUG-016:**
Button-triggered messages never enter the message history. This eliminates the
accumulation problem at the source for all button-triggered requests. Combined with
BUG-017/018/019 which handle typed requests, all artifact generation paths are covered.

**Token savings:**
Suppressing AI text response for artifact generation saves ~100-300 output tokens per
generation request. The silent instruction adds ~30 input tokens. Net positive.

---

*Created: 2026-02-04*
*Part of BUG-016 layered fix (Layer 4: UX - Silent Generation)*
