# BUG-019: History Filtering for Fulfilled Artifact Requests

**Priority:** Critical
**Status:** Done
**Component:** Backend / Conversation Service
**Parent:** BUG-016 (Artifact generation multiplies on repeated requests)
**Implementation Order:** 3 of 4 (implement after BUG-017 and BUG-018)
**Dependencies:** None (complements but does not depend on BUG-017/018)

---

## User Story

As a user having multiple conversations in the same thread,
I want fulfilled artifact requests to be marked in conversation history,
so that the AI structurally cannot re-trigger generation from prior requests.

---

## Problem

`build_conversation_context()` in `conversation_service.py:94-101` loads all messages
and passes them to the LLM without any indication of which artifact requests were
already fulfilled. The model sees raw request text and treats it as actionable.

BUG-017 and BUG-018 address this at the prompt level, but this story provides a
**structural guarantee** — the context itself is modified before reaching the model.

---

## Solution

### Detection Strategy: Response-Based

Scan **assistant messages** for the `ARTIFACT_CREATED` marker string that is already
returned by `execute_tool()` in `ai_service.py:726-735`. If an assistant message
contains this marker, the **preceding user message** was a fulfilled artifact request.

This approach:
- Detects what **actually happened**, not what we guess the user intended
- Zero false positives — if `save_artifact` was called, the request was fulfilled
- Works for preset button messages AND custom freeform prompts
- No trigger phrase list to maintain

### Changes Required

**File:** `backend/app/services/conversation_service.py`

**Modify:** `build_conversation_context()` function (lines 77-117)

**Logic:**

```python
async def build_conversation_context(
    db: AsyncSession,
    thread_id: str
) -> List[Dict[str, Any]]:
    # Fetch all messages in chronological order (existing code)
    stmt = (
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Convert to Claude message format with artifact deduplication
    conversation = []
    for i, msg in enumerate(messages):
        content = msg.content

        # Response-based detection: if an assistant message contains
        # ARTIFACT_CREATED marker, the preceding user message was fulfilled
        if msg.role == "assistant" and "ARTIFACT_CREATED:" in content:
            # Mark the preceding user message as fulfilled
            if conversation and conversation[-1]["role"] == "user":
                conversation[-1]["content"] = (
                    "[ALREADY PROCESSED - artifact was generated] "
                    + conversation[-1]["content"]
                )

        conversation.append({
            "role": msg.role,
            "content": content
        })

    # Existing truncation logic (unchanged)
    total_tokens = estimate_messages_tokens(conversation)
    if total_tokens > MAX_CONTEXT_TOKENS:
        conversation = truncate_conversation(conversation, MAX_CONTEXT_TOKENS)

    return conversation
```

### Edge Cases

1. **Assistant message without ARTIFACT_CREATED but tool was called** — The marker is
   embedded in the tool result by `execute_tool()`. If the marker is absent, the tool
   was not called, so no marking needed.

2. **Multiple artifact types in one response** — Still one user message, still one
   `[ALREADY PROCESSED]` prefix. Correct behavior.

3. **Failed generation (no marker in response)** — User message stays unmarked, allowing
   re-triggering. Correct behavior — user should be able to retry failed requests.

4. **Custom prompts** — Response-based detection works regardless of prompt content.
   No trigger phrase matching needed.

5. **ARTIFACT_CREATED appears in regular text** — Extremely unlikely as it's a structured
   marker format `ARTIFACT_CREATED:{json}|`. Could add stricter regex if needed, but
   the current string match is sufficient.

---

## Acceptance Criteria

- [ ] `build_conversation_context()` scans assistant messages for `ARTIFACT_CREATED:` marker
- [ ] Preceding user message is prefixed with `[ALREADY PROCESSED - artifact was generated]`
- [ ] Unfulfilled requests (no marker in following assistant message) are left untouched
- [ ] Failed generation attempts are NOT marked (user can retry)
- [ ] Custom freeform prompts are handled correctly (response-based, not input-based)
- [ ] Existing truncation logic is unaffected
- [ ] Unit test verifies marking behavior with mock message history

---

## Technical References

- `backend/app/services/conversation_service.py:77-117` — `build_conversation_context()`
- `backend/app/services/ai_service.py:726-735` — `ARTIFACT_CREATED` marker in tool result
- `backend/app/services/ai_service.py:846-847` — Where artifact_created event is emitted

---

## Testing

### Unit Tests

```python
def test_fulfilled_request_marked():
    """User message before ARTIFACT_CREATED response gets marked."""
    messages = [
        Message(role="user", content="Generate BRD from this conversation."),
        Message(role="assistant", content="ARTIFACT_CREATED:{...}| Done!"),
        Message(role="user", content="Can you explain section 3?"),
    ]
    result = build_context(messages)
    assert "[ALREADY PROCESSED" in result[0]["content"]
    assert "[ALREADY PROCESSED" not in result[2]["content"]

def test_failed_request_not_marked():
    """User message before non-artifact response stays clean."""
    messages = [
        Message(role="user", content="Generate BRD from this conversation."),
        Message(role="assistant", content="I need more info before generating."),
    ]
    result = build_context(messages)
    assert "[ALREADY PROCESSED" not in result[0]["content"]
```

### Manual Testing

1. Generate artifact in thread (should work normally)
2. Send another generation request in same thread
3. Verify only 1 new artifact is created (not 2)
4. Verify first request shows `[ALREADY PROCESSED]` in context (check logs after ENH-011)

---

*Created: 2026-02-04*
*Part of BUG-016 layered fix (Layer 3: Structural History Filtering)*
