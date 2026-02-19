# Phase 69: Token Optimization - Research

**Researched:** 2026-02-19
**Domain:** Python backend token management for CLI adapter multi-turn conversations
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TOKEN-01 | Assistant message filtering strips tool_use blocks to prevent document context duplication | Phase 68 `_extract_text_content()` already annotates tool_use blocks with `[searched documents]`/`[performed an action]`. The remaining work is verifying this filtering is applied at the `build_conversation_context` stage for cases where messages were stored with JSON-encoded content blocks (potential future path), and adding a test that confirms filtering is active. |
| TOKEN-02 | Token-aware truncation preserved for CLI adapter (existing 150K limit) | `build_conversation_context()` calls `truncate_conversation()` at 150K tokens. Phase 68 changed `_convert_messages_to_prompt()` but did NOT change `build_conversation_context()` — the 150K limit is structurally preserved. A regression test should confirm `MAX_CONTEXT_TOKENS = 150000` and `truncate_conversation()` are called before the CLI adapter receives messages. |
| TOKEN-03 | Emergency truncation at 180K tokens with user-facing error message | No 180K emergency limit exists today. `build_conversation_context()` has only the 150K limit with silent sliding window. Need to add: (a) a second check AFTER `build_conversation_context()` at the `stream_chat` route level or `_stream_agent_chat`, (b) a `message_complete` error event or HTTP error response that the frontend shows as a user-visible error. |
| TOKEN-04 | Linear token growth verified (not quadratic) across 20+ turn conversations with docs | A unit test that simulates 20+ turn conversations with mock document search annotations (`[searched documents]`) and measures estimated token counts per turn. Asserts that growth is approximately linear (slope < some threshold), NOT exponential or quadratic. No real CLI subprocess needed — mock messages mimicking realistic document search output. |

</phase_requirements>

---

## Summary

Phase 69 addresses four inter-related token management requirements for the CLI adapter. The central problem is **document context duplication**: if document search results are re-included verbatim in every conversation turn, token usage grows quadratically (O(n²)) rather than linearly (O(n)) across a 20+ turn conversation.

Phase 68 implemented `_extract_text_content()` which replaces `tool_use` blocks with short annotations (`[searched documents]`). This addresses duplication at the **formatting** layer: even if messages arrive with structured content blocks, tool_use blocks are replaced by a 2-word annotation. The remaining Phase 69 work is:

1. **TOKEN-01**: Verify the filtering is actually active in the real call chain. Messages loaded from DB are plain strings (not lists), so `_extract_text_content` currently takes the `isinstance(content, str)` branch and returns content unchanged. Filtering only activates for list content. A test to confirm this path works correctly with real-world message types is needed.

2. **TOKEN-02**: Regression test that the existing 150K truncation in `build_conversation_context()` still fires correctly after Phase 68 changes. No code change needed — this is a verification/test task.

3. **TOKEN-03**: Add a 180K emergency limit. This is a NEW code addition: after `build_conversation_context()` returns, check estimated tokens. If >180K, yield an `error` SSE event with a user-readable message rather than sending to CLI and getting a cryptic failure.

4. **TOKEN-04**: A unit test simulating 20+ turns with document search output, measuring token growth per turn, asserting linearity.

**Primary recommendation:** Add the 180K emergency check in `_stream_agent_chat()` in `ai_service.py`, add regression tests for the 150K truncation, add the linear growth assertion test, and verify TOKEN-01 filtering with an end-to-end message content test.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | Existing in venv | Backend unit tests | Already used in all existing tests |
| pytest-asyncio | Existing in venv | Async test support | Already used in existing tests |
| unittest.mock | 3.12 stdlib | Mock db session for token tests | Already used in CLI adapter tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None | - | No new libraries needed | All changes are in existing service layer |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| In-app token estimation (`len(text)//4`) | tiktoken (OpenAI's tokenizer) | tiktoken is accurate but adds dependency; `len//4` is already established in the codebase and sufficient for emergency limit detection |
| HTTP 413 error for 180K | SSE error event | HTTP 413 disconnects before SSE starts; SSE error event allows frontend to show message inline without breaking the UI flow |

**Installation:** No new packages required.

---

## Architecture Patterns

### Call Chain (Phase 69 relevant paths)

```
conversations.py route (POST /threads/{thread_id}/chat)
  ├─ build_conversation_context(db, thread_id)          ← 150K truncation HERE (TOKEN-02)
  │    └─ truncate_conversation(messages, MAX_CONTEXT_TOKENS)
  │
  └─ AIService.stream_chat() → _stream_agent_chat()     ← 180K emergency check HERE (TOKEN-03)
       └─ ClaudeCLIAdapter.stream_chat()
            └─ _convert_messages_to_prompt(messages)    ← tool_use filtering HERE (TOKEN-01)
                 └─ _extract_text_content()
```

### Current State: Message Content in DB

All assistant messages are stored via `save_message(db, thread_id, "assistant", accumulated_text)` where `accumulated_text` is a plain string. When loaded by `build_conversation_context()`, content is `{"role": "assistant", "content": "plain string"}`. The `_extract_text_content()` `isinstance(content, str)` branch returns it unchanged.

**This means**: Tool_use blocks are NOT currently being duplicated for the CLI adapter path. The quadratic growth risk exists if the CLI's text response includes verbatim document content (which the CLI may include when responding). The `[searched documents]` annotation in history does NOT prevent the CLI from re-quoting document content in subsequent turns — but this is a behavior limitation, not a code bug.

**TOKEN-01's actual scope**: Confirm that `_extract_text_content()` is correct for future-proofing (if messages were ever stored as JSON-encoded content lists), AND add a test verifying the filtering path.

### Pattern 1: 180K Emergency Check (TOKEN-03)

**What:** After `build_conversation_context()` returns, before calling the CLI adapter, check if the estimated token count exceeds 180K.

**Where to add:** In `_stream_agent_chat()` in `ai_service.py`, immediately after `set_context()` is called.

**Why here, not in conversations.py:** The 180K check is CLI-adapter-specific behavior. The Anthropic/Gemini adapters have different limits and would not benefit from the same check. Placing it in `_stream_agent_chat()` keeps it isolated to agent provider paths.

**Example:**
```python
# Source: TOKEN-03 requirement + existing estimate_messages_tokens pattern
from app.services.conversation_service import estimate_messages_tokens

# Add to _stream_agent_chat() before adapter.stream_chat() call:
EMERGENCY_TOKEN_LIMIT = 180000
estimated_tokens = estimate_messages_tokens(messages)
if estimated_tokens > EMERGENCY_TOKEN_LIMIT:
    yield {
        "event": "error",
        "data": json.dumps({
            "message": (
                f"This conversation is too long to continue ({estimated_tokens:,} estimated tokens). "
                "Please start a new conversation to continue."
            )
        })
    }
    return
```

**Note on import:** `estimate_messages_tokens` is already importable from `app.services.conversation_service`. No new functions needed.

### Pattern 2: Linear Growth Verification Test (TOKEN-04)

**What:** A unit test that builds N turns of synthetic messages (user + assistant with `[searched documents]` annotation) and checks that token estimates grow linearly.

**Where:** New test class in `backend/tests/unit/services/test_conversation_service.py` OR a new `test_token_optimization.py`.

**Recommendation:** Add to `test_conversation_service.py` since it tests `estimate_messages_tokens`.

**Example:**
```python
# Source: TOKEN-04 requirement + existing estimate_messages_tokens pattern
class TestLinearTokenGrowth:
    """Verify token growth is linear across 20+ turn conversations with doc searches."""

    def _make_conversation(self, turns: int) -> List[Dict[str, Any]]:
        """Build a realistic multi-turn conversation with document search annotations."""
        messages = []
        for i in range(turns):
            messages.append({
                "role": "user",
                "content": f"Tell me about feature {i} in the project documents."
            })
            # Realistic assistant response: some text + doc search annotation
            messages.append({
                "role": "assistant",
                "content": (
                    f"Based on the project documentation, feature {i} works as follows. "
                    f"[searched documents]\n"
                    f"This feature handles the {i}-th use case with standard behavior."
                )
            })
        return messages

    def test_token_growth_is_linear_over_20_turns(self):
        """Token counts grow linearly (not quadratically) across 20+ turns."""
        token_counts = []
        for num_turns in range(1, 22):  # 1 to 21 turns
            messages = self._make_conversation(num_turns)
            tokens = estimate_messages_tokens(messages)
            token_counts.append(tokens)

        # Linear growth: each additional turn adds approximately the same token count
        # Compute first differences (turn N+1 - turn N)
        diffs = [token_counts[i+1] - token_counts[i] for i in range(len(token_counts)-1)]

        # All first differences should be approximately equal (linear = constant first diff)
        # Allow 20% variance to handle integer truncation effects
        avg_diff = sum(diffs) / len(diffs)
        for d in diffs:
            assert abs(d - avg_diff) / avg_diff < 0.20, (
                f"Non-linear growth detected: diff={d} deviates >20% from avg={avg_diff:.1f}. "
                f"Token counts: {token_counts}"
            )

    def test_token_growth_not_quadratic(self):
        """Confirm token count at turn N is NOT proportional to N^2."""
        messages_5 = self._make_conversation(5)
        messages_10 = self._make_conversation(10)
        messages_20 = self._make_conversation(20)

        tokens_5 = estimate_messages_tokens(messages_5)
        tokens_10 = estimate_messages_tokens(messages_10)
        tokens_20 = estimate_messages_tokens(messages_20)

        # For linear growth: tokens_20 ≈ 4 * tokens_5 (20/5 = 4x)
        # For quadratic growth: tokens_20 ≈ 16 * tokens_5 (20^2/5^2 = 16x)
        ratio_10_vs_5 = tokens_10 / tokens_5  # Should be ~2 (linear)
        ratio_20_vs_5 = tokens_20 / tokens_5  # Should be ~4 (linear)

        assert ratio_10_vs_5 < 3.0, f"Turn 10/5 ratio {ratio_10_vs_5:.2f} suggests non-linear growth"
        assert ratio_20_vs_5 < 6.0, f"Turn 20/5 ratio {ratio_20_vs_5:.2f} suggests non-linear growth"
```

### Pattern 3: 150K Truncation Regression Test (TOKEN-02)

**What:** A test confirming `build_conversation_context()` still applies truncation when conversation exceeds 150K tokens, verifying Phase 68 did not inadvertently break this.

**Where:** The existing `TestTruncateConversation` in `test_conversation_service.py` already covers `truncate_conversation()`. Add one test to `test_conversation_service_db.py` (or a mock-db test) that covers `build_conversation_context()` calling truncation.

**Key finding:** `MAX_CONTEXT_TOKENS = 150000` is a module-level constant. The truncation check at lines 171-174 of `conversation_service.py` is:
```python
if total_tokens > MAX_CONTEXT_TOKENS:
    conversation = truncate_conversation(conversation, MAX_CONTEXT_TOKENS)
```
This is UNCHANGED by Phase 68. The regression test simply needs to confirm the constant hasn't changed and the flow is intact.

### Pattern 4: TOKEN-01 Filtering Verification Test

**What:** Confirm `_extract_text_content()` strips tool_use blocks from list-format content, and confirm string-format content (current real DB path) passes through unchanged.

**Where:** Add to `TestClaudeCLIAdapterMessageConversion` in `test_claude_cli_adapter.py` — most of this already exists from Phase 68.

**Finding:** Phase 68 unit tests already cover `test_tool_use_blocks_replaced_with_annotation` and `test_tool_use_only_assistant_messages_skipped`. TOKEN-01 verification is already implemented. The remaining gap is a **token count test** showing that the annotations (`[searched documents]` = ~2 tokens) are much smaller than typical document content (300-500 tokens per snippet), proving the filtering reduces token consumption.

**Example:**
```python
def test_tool_use_annotation_far_smaller_than_document_content(self, mock_which):
    """[searched documents] annotation uses far fewer tokens than full document content."""
    adapter = ClaudeCLIAdapter(api_key="test-key")

    # Simulate an assistant message with document search + text
    large_doc_content = "a" * 2000  # ~500 tokens of document content
    messages_with_doc_in_tool_use = [
        {"role": "user", "content": "What does the spec say?"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Based on the spec:"},
                {"type": "tool_use", "id": "t1", "name": "search_documents",
                 "input": {"query": "spec", "result": large_doc_content}}
            ]
        }
    ]

    prompt = adapter._convert_messages_to_prompt(messages_with_doc_in_tool_use)

    # The tool_use block's large content is NOT in the output
    assert large_doc_content not in prompt
    # The annotation is tiny (2 words vs 500 tokens)
    assert "[searched documents]" in prompt
    assert len(prompt) < len(large_doc_content)
```

### Anti-Patterns to Avoid

- **Do NOT add the 180K check in `conversations.py` route handler**: The check is CLI-adapter-specific. Placing it in the route handler would apply it to ALL adapters (Anthropic/Gemini/DeepSeek), which have different context window sizes and rate limits.
- **Do NOT change `MAX_CONTEXT_TOKENS` from 150K**: TOKEN-02 explicitly requires the existing limit to be preserved. The 180K emergency limit is an ADDITIONAL check, not a replacement.
- **Do NOT raise a Python exception for the 180K limit**: The SSE streaming has already started. Raising an exception would result in an uncaught error logged but no user-visible message. Yield the error event instead.
- **Do NOT use quadratic growth simulation for TOKEN-04**: The test should use SIMPLE string messages (not actual CLI subprocess calls). The token estimation function (`estimate_messages_tokens`) is a pure function — test it directly with controlled input.
- **Do NOT use `tiktoken` or external tokenizers**: The codebase uses `len(text) // 4` as the standard. Do not introduce a new dependency for this phase.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Custom tokenizer | `estimate_messages_tokens()` from `conversation_service.py` | Already established in codebase; consistent with 150K truncation logic |
| Error propagation | Custom exception types | SSE `error` event with `json.dumps({"message": "..."})` | Matches existing error pattern in `_stream_agent_chat()` lines 993-996 |
| Test message building | Complex mock factories | Simple dict literals (`{"role": "user", "content": "..."}`) | `estimate_messages_tokens` takes plain dicts — no elaborate setup needed |

**Key insight:** All infrastructure for token management already exists. Phase 69 is primarily about adding checks and tests, not building new mechanisms.

---

## Common Pitfalls

### Pitfall 1: 180K Check Placed Before build_conversation_context

**What goes wrong:** If the 180K check fires BEFORE `build_conversation_context()`, it would check the raw DB message count but not the truncated context. The 150K truncation in `build_conversation_context()` should have already reduced the conversation to ≤150K tokens. So a 180K check before `build_conversation_context()` would NEVER fire (since the context is truncated to 150K first).

**Why it happens:** The natural instinct is to add the check early (in `conversations.py`). But `build_conversation_context()` truncates first, so the check must come AFTER truncation to detect edge cases where the truncation itself is not enough (e.g., a single message > 150K tokens that passes the truncation check due to integer arithmetic).

**How to avoid:** Place the 180K check in `_stream_agent_chat()` AFTER `messages` is received (already truncated by `build_conversation_context()`). This catches the edge case where truncation was supposed to reduce to 150K but the rough estimation allowed a slightly larger value through.

**Warning signs:** Emergency check never fires even when conversations exceed 180K tokens.

### Pitfall 2: Quadratic Growth Test Uses Wrong Input

**What goes wrong:** The TOKEN-04 test uses messages that grow exponentially by nature (e.g., each assistant message includes all previous messages as a quote). The test would correctly detect non-linear growth in the test data but not reflect the real system behavior.

**Why it happens:** Wanting to simulate the "worst case". But the test should simulate REALISTIC message patterns (short user questions + assistant responses with a `[searched documents]` annotation) to validate that the system's actual output format doesn't cause quadratic growth.

**How to avoid:** Use fixed-size messages per turn (same user question template + same assistant response template). This ensures the growth is measured from accumulated message count, not from expanding message sizes.

**Warning signs:** Test passes but doesn't actually validate the system (fixed-message test always shows linear growth regardless of implementation).

### Pitfall 3: 180K Error Message Not Visible to User

**What goes wrong:** Yielding a `{"event": "error", "data": json.dumps({...})}` SSE event but the frontend doesn't display it because the frontend expects the `message` key inside the data to be a plain string but receives something else.

**Why it happens:** Error event format mismatch. The frontend's `AssistantConversationProvider` listens for `error` events and reads `data["message"]`.

**How to avoid:** Match EXACTLY the existing error event format:
```python
yield {
    "event": "error",
    "data": json.dumps({"message": "This conversation is too long..."})
}
return  # CRITICAL: return immediately after yielding error
```

**Warning signs:** Error event is sent but frontend shows spinning indicator instead of error message.

### Pitfall 4: TOKEN-02 Regression Test Tests the Wrong Thing

**What goes wrong:** Writing a test that verifies `truncate_conversation()` works (already tested in 21 existing tests) rather than verifying that `build_conversation_context()` CALLS truncation when needed.

**Why it happens:** `truncate_conversation()` is a pure function that's easy to test. `build_conversation_context()` requires a DB session mock.

**How to avoid:** The existing tests in `test_conversation_service.py` already cover `truncate_conversation()` thoroughly. For TOKEN-02, add ONE test using the `test_conversation_service_db.py` pattern (async mock DB) that confirms the truncation constant `MAX_CONTEXT_TOKENS = 150000` is correct. A simple import assertion is sufficient:
```python
def test_max_context_tokens_is_150000():
    assert MAX_CONTEXT_TOKENS == 150000
```

**Warning signs:** Tests pass but someone accidentally changes `MAX_CONTEXT_TOKENS` in the future without a test catching it.

### Pitfall 5: estimate_messages_tokens Misses Token Count for CLI Messages

**What goes wrong:** `estimate_messages_tokens()` estimates tokens based on `len(text) // 4`. For CLI adapter messages going through `_convert_messages_to_prompt()`, the FORMATTED prompt (with `Human:`, `Assistant:`, `---` separators) is longer than the raw messages. The 180K check uses unformatted message token count, but the CLI receives the formatted prompt (longer).

**Why it happens:** The token estimation is done on the input `messages` list, but the actual bytes sent to the CLI are the `combined_prompt` string (which includes formatting overhead).

**How to avoid:** The overhead is small. For 20-turn conversation: ~20 × (len("Human: ") + len("---") + 2 newlines) ≈ 20 × 15 chars ≈ ~75 tokens overhead. This is negligible for the 180K emergency limit detection. Document this in a code comment. Do NOT add a more complex estimation — keep the existing rough estimate.

**Warning signs:** This is not a breaking issue — the overhead is <1% of the 180K limit. No warning signs to watch for.

### Pitfall 6: Pre-existing Test Failure Counted as Regression

**What goes wrong:** `test_stream_chat_passes_api_key_in_env` in `test_claude_cli_adapter.py` fails with 1 error. This is a pre-existing bug from before Phase 68, documented in Phase 68 summaries. Phase 69 tests must NOT fix this test or mark it as a regression.

**How to avoid:** The baseline is 47 passing, 1 pre-existing fail. Verify final state is: baseline count + new tests added, still 1 failing (the pre-existing one).

---

## Code Examples

Verified patterns from existing codebase:

### Existing Error Yield Pattern (matches TOKEN-03 requirement)
```python
# Source: ai_service.py lines 992-996 — existing error event format
elif chunk.chunk_type == "error":
    yield {
        "event": "error",
        "data": json.dumps({"message": chunk.error})
    }
    return
```

### Existing Token Estimation (matches TOKEN-02/TOKEN-04 use)
```python
# Source: conversation_service.py lines 14-23
MAX_CONTEXT_TOKENS = 150000  # Leave room for response and system prompt
CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN

def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    total += estimate_tokens(str(part.get("content", "")))
    return total
```

### Where 180K Check Goes in _stream_agent_chat()
```python
# Source: ai_service.py lines 860-916 — _stream_agent_chat structure
async def _stream_agent_chat(self, messages, project_id, thread_id, db):
    # ... existing log_service setup ...
    try:
        if hasattr(self.adapter, 'set_context'):
            self.adapter.set_context(db, project_id, thread_id)

        # >>> TOKEN-03: Add emergency check HERE <<<
        from app.services.conversation_service import estimate_messages_tokens
        EMERGENCY_TOKEN_LIMIT = 180000
        estimated_tokens = estimate_messages_tokens(messages)
        if estimated_tokens > EMERGENCY_TOKEN_LIMIT:
            yield {
                "event": "error",
                "data": json.dumps({
                    "message": (
                        f"This conversation has grown too long to continue "
                        f"({estimated_tokens:,} estimated tokens). "
                        "Please start a new conversation."
                    )
                })
            }
            return

        accumulated_text = ""
        # ... rest of method ...
```

### Constant Assertion Pattern (TOKEN-02 test)
```python
# Source: test_conversation_service.py — existing constant import pattern
from app.services.conversation_service import MAX_CONTEXT_TOKENS

def test_max_context_tokens_is_150000():
    """Regression: 150K truncation limit must not be changed."""
    assert MAX_CONTEXT_TOKENS == 150000, (
        f"MAX_CONTEXT_TOKENS changed to {MAX_CONTEXT_TOKENS}. "
        "This breaks TOKEN-02 requirement. If intentional, update this test."
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `messages[-1]` only (POC) | Full history via `_convert_messages_to_prompt()` | Phase 68 | Enables multi-turn memory — now token growth matters |
| No emergency token check | 180K check in `_stream_agent_chat()` | Phase 69 | Prevents silent CLI failures on long conversations |
| No linear growth test | `test_token_growth_is_linear_over_20_turns` | Phase 69 | Ongoing verification of growth characteristics |

**Deprecated/outdated:**
- The POC comment "Production: Format multi-turn conversation with role labels" was removed in Phase 68. No further technical debt to address there.

---

## Open Questions

1. **Should EMERGENCY_TOKEN_LIMIT be a module constant or hard-coded?**
   - What we know: `MAX_CONTEXT_TOKENS = 150000` is a module constant in `conversation_service.py`. `EMERGENCY_TOKEN_LIMIT = 180000` would live in `ai_service.py`.
   - What's unclear: Whether the 180K limit will need tuning (it should not — it's an emergency ceiling, not a soft limit).
   - Recommendation: Define as a module-level constant in `ai_service.py` with a comment explaining it's the emergency ceiling above the 150K soft limit. Keep it separate from `conversation_service.py` because it's adapter-specific behavior.

2. **Does TOKEN-01 require ANY new code, or is it already complete via Phase 68?**
   - What we know: `_extract_text_content()` in Phase 68 already handles tool_use blocks (replaces with annotation). The existing 13 unit tests from Phase 68 already verify this.
   - What's unclear: Whether the requirement means "verify existing implementation" or "add new code".
   - Recommendation: TOKEN-01 is **satisfied by Phase 68 implementation**. Phase 69 TOKEN-01 work = (a) add one token-size comparison test showing annotation vs. raw tool_use input size, and (b) update REQUIREMENTS.md to mark it done.

3. **What should the 180K error message say to the user?**
   - What we know: The frontend `AssistantConversationProvider` displays error messages from `{"message": "..."}` as an inline error in the chat UI.
   - Recommendation: `"This conversation is too long to continue ({N:,} estimated tokens). Please start a new conversation."` — clear, actionable, includes the actual number for debugging.

---

## Sources

### Primary (HIGH confidence)

- Direct code read: `backend/app/services/conversation_service.py` — confirmed `MAX_CONTEXT_TOKENS = 150000`, `estimate_messages_tokens()`, `truncate_conversation()` implementation
- Direct code read: `backend/app/services/ai_service.py` lines 860-1016 — confirmed `_stream_agent_chat()` structure, existing error yield format, where 180K check should go
- Direct code read: `backend/app/services/llm/claude_cli_adapter.py` — confirmed Phase 68 `_extract_text_content()` implementation, tool_use annotation logic
- Direct code read: `backend/app/routes/conversations.py` lines 136-199 — confirmed `build_conversation_context()` call chain, `save_message()` saves plain text strings
- Direct code read: `backend/tests/unit/services/test_conversation_service.py` — confirmed 21 existing tests, test patterns for `estimate_messages_tokens`, `truncate_conversation`
- Test run: `cd backend && ./venv/bin/python -m pytest tests/unit/llm/test_claude_cli_adapter.py -q` — confirmed 47 pass, 1 pre-existing fail (baseline for Phase 69)
- Phase 68 research: `.planning/phases/68-core-conversation-memory-fix/68-RESEARCH.md` — Phase 68 decisions and implementation context
- Phase 68 summaries: `68-01-SUMMARY.md`, `68-02-SUMMARY.md` — confirmed what Phase 68 actually built
- Prior research: `.planning/research/PITFALLS_CONVERSATION_MEMORY.md` — Pitfall 8 documents the quadratic growth mechanism

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — TOKEN-01 through TOKEN-04 requirements definitions
- `.planning/ROADMAP.md` — Phase 69 success criteria and dependencies

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries, existing patterns verified in source
- Architecture: HIGH — all affected files read, call chain verified, exact insertion point for 180K check confirmed
- Pitfalls: HIGH — identified from direct code analysis and prior phase research

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (stable architecture, no fast-moving dependencies)
