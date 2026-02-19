# Phase 68: Core Conversation Memory Fix - Research

**Researched:** 2026-02-19
**Domain:** Claude CLI adapter multi-turn conversation formatting (Python backend + Flutter frontend)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Message Formatting
- Role labels: `Human:` / `Assistant:` (Anthropic's native conversation format)
- Delimiter between messages: `---` separator line between each turn
- Multi-part content: Keep text blocks, replace tool_use with annotated summary like `[searched documents]` or `[performed an action]`
- Thinking blocks: Exclude — only include final response text, not internal reasoning

#### History Scope
- Include user and assistant messages only — exclude system messages and internal tool messages
- Reuse existing `ConversationService.build_conversation_context()` for history loading (shared logic, already handles truncation)
- Empty assistant messages (tool_use only, no text): Skip entirely — do not include in formatted history
- Document search results: Replace with brief reference annotations like `[referenced: filename.txt]` instead of full content

#### Test Strategy
- Backend: Mocked subprocess for unit tests + one real integration test (spawns actual Claude CLI, costs API tokens)
- Integration test acceptance: Fact recall — casually mention a fact in turn 1 (e.g., "we're building a FastAPI app"), ask about it in turn 3. Do NOT explicitly say "remember this" to avoid triggering memory.md storage
- Thread type coverage: Assistant threads only — BA uses agent_service.py which is unmodified
- Frontend: Full AssistantConversationProvider test coverage — message list integrity, streaming state, error handling, retry with history

### Claude's Discretion
- Exact annotation text for tool_use summaries
- Error behavior when formatting fails (research suggests this is low-risk given proven pattern)
- Specific test fixture data and assertion style

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONV-01 | CLI adapter sends full conversation history (all messages, not just last) | Replace `_convert_messages_to_prompt()` to iterate all messages, not just `messages[-1]` |
| CONV-02 | Messages formatted with role labels matching BA flow pattern | Use `Human:` / `Assistant:` labels with `---` separator (mirrors proven pattern in agent_service.py lines 103-120) |
| CONV-03 | Role alternation validated before sending to CLI subprocess | Iterate messages; detect consecutive same-role turns and log warning (no hard error per discretion area) |
| CONV-04 | Multi-part content handled (text blocks, tool results) | Extract text parts, replace tool_use blocks with `[performed an action]`, skip tool_result messages, handle thinking blocks by exclusion |
| TEST-01 | Backend unit tests for `_convert_messages_to_prompt()` with 1, 3, 10+ messages | Extend `TestClaudeCLIAdapterMessageConversion` class in existing test file — test multi-turn output format |
| TEST-02 | Backend unit tests for multi-part content handling (tool results) | Add fixture messages with tool_use and tool_result content types; verify annotation text in output |
| TEST-03 | Backend regression tests verifying BA flow unchanged | BA flow uses `agent_service.py` directly, not `claude_cli_adapter.py` — verify AIService routing still correct |
| TEST-04 | Frontend tests for AssistantConversationProvider message history handling | New test file: `assistant_conversation_provider_test.dart` — message list, streaming state, error handling, retry |
| TEST-05 | Integration test: Assistant thread with 3+ turns preserves context | One real subprocess test in `tests/integration/` — avoid "remember this" phrasing, use casual fact mention |
</phase_requirements>

---

## Summary

The bug is precisely located: `_convert_messages_to_prompt()` in `claude_cli_adapter.py` (lines 106-137) only extracts the last user message from the history list (`messages[-1]`). Every other turn is discarded before the prompt is assembled and sent to the CLI subprocess via stdin. The fix is a targeted replacement of this single method to iterate all messages and format them with role labels and separators.

The proven pattern already exists in `agent_service.py` (lines 102-120) where the same problem was solved for the BA Agent SDK flow. That implementation uses `[USER]:` and `[ASSISTANT]:` bracket labels. The locked decision for this phase selects `Human:` / `Assistant:` labels with `---` separators instead, which is Anthropic's canonical multi-turn conversation format that the Claude CLI natively understands.

The call chain is clean: `conversations.py` route calls `build_conversation_context()` (which loads and truncates all messages), then passes the full list to `AIService.stream_chat()`, which passes it to `ClaudeCLIAdapter.stream_chat()`, which calls `_convert_messages_to_prompt()` — and it is here that the context is thrown away. No changes are required anywhere else in the backend except this single method.

**Primary recommendation:** Replace `_convert_messages_to_prompt()` with a multi-turn formatter that iterates all messages, applies `Human:` / `Assistant:` labels with `---` separators, handles multi-part content by annotation, skips tool-only messages, and excludes thinking blocks.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python asyncio | 3.12 stdlib | Subprocess management | Already in use; no change |
| pytest + pytest-asyncio | Existing in venv | Backend unit + integration tests | Already used in all existing tests |
| unittest.mock | 3.12 stdlib | Mock subprocess for unit tests | Already used in `test_claude_cli_adapter.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mockito (Dart) | Existing in pubspec | Mock AIService/ThreadService for Flutter tests | Already used in conversation_provider_test.dart |
| flutter_test | Existing SDK | Flutter unit test runner | Standard for all frontend tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Human:` / `Assistant:` labels | `[USER]:` / `[ASSISTANT]:` (agent_service.py pattern) | Locked decision: Anthropic native format is cleaner for Claude CLI to parse |
| Annotation `[performed an action]` | Full tool_use JSON in prompt | Locked decision: annotations keep context without leaking tool internals |

---

## Architecture Patterns

### Call Chain (Unchanged by Fix)

```
conversations.py route
  └─ build_conversation_context(db, thread_id)  # loads ALL messages, truncates to 150k tokens
       └─ AIService.stream_chat(conversation, project_id, thread_id, db)
            └─ [routes to _stream_agent_chat because is_agent_provider=True]
                 └─ ClaudeCLIAdapter.stream_chat(messages, system_prompt)
                      └─ _convert_messages_to_prompt(messages)  ← FIX IS HERE
                           └─ combined_prompt → stdin of claude subprocess
```

### Pattern 1: Multi-Turn Prompt Formatting

**What:** Converts `List[Dict]` message history into a single string with role labels and separators for CLI stdin.

**When to use:** All Assistant thread requests (any message count ≥ 1).

**Current (broken) implementation:**
```python
# claude_cli_adapter.py lines 106-137 — only uses messages[-1]
def _convert_messages_to_prompt(self, messages):
    if not messages:
        return ""
    last_message = messages[-1]
    ...
```

**Replacement implementation (based on locked decisions):**
```python
def _convert_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
    """
    Convert full conversation history to multi-turn prompt string for CLI.

    Formats all user and assistant messages with role labels and separators
    so the CLI receives complete conversation context.

    Format: Human: / Assistant: labels with '---' separators between turns.
    Multi-part content: text blocks kept, tool_use replaced with annotation,
    tool_result messages skipped, thinking blocks excluded.

    Args:
        messages: Full conversation history in standard format

    Returns:
        str: Multi-turn prompt text for CLI stdin
    """
    if not messages:
        return ""

    parts = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Map role to Anthropic native label
        if role == "user":
            label = "Human"
        elif role == "assistant":
            label = "Assistant"
        else:
            # Skip system messages and any unknown roles
            continue

        # Extract text from content (string or list)
        text = self._extract_text_content(content)

        # Skip empty assistant messages (tool_use only, no text)
        if not text.strip():
            continue

        parts.append(f"{label}: {text}")

    return "\n\n---\n\n".join(parts)

def _extract_text_content(self, content) -> str:
    """Extract text from string or list content, handling multi-part blocks."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if not isinstance(part, dict):
                continue
            block_type = part.get("type", "")
            if block_type == "text":
                text_parts.append(part.get("text", ""))
            elif block_type == "thinking":
                # Exclude thinking blocks — only final response text
                pass
            elif block_type == "tool_use":
                tool_name = part.get("name", "")
                if "search_documents" in tool_name:
                    text_parts.append("[searched documents]")
                else:
                    text_parts.append("[performed an action]")
            elif block_type == "tool_result":
                # Tool result messages are skipped at the message level
                # (these are user messages containing tool results)
                pass
        return "\n".join(text_parts)

    return str(content)
```

**Note on tool_result messages:** The `tool_result` type appears as the role-"user" message content type in the Anthropic API format (after a tool_use). These messages have content like `[{"type": "tool_result", "tool_use_id": "...", "content": "..."}]`. When iterating messages, such a user message will have empty text after extraction (tool_result blocks produce no text), so the empty-text skip condition handles them correctly.

### Pattern 2: Existing Test Class Extension

**What:** Add new test methods to `TestClaudeCLIAdapterMessageConversion` in the existing test file.

**When to use:** All `_convert_messages_to_prompt()` tests.

**Existing class location:** `backend/tests/unit/llm/test_claude_cli_adapter.py` lines 832-875

**New test pattern:**
```python
@patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
def test_converts_multi_turn_with_role_labels(self, mock_which):
    """Multi-turn messages use Human:/Assistant: labels with --- separators."""
    adapter = ClaudeCLIAdapter(api_key="test-key")

    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"},
    ]

    prompt = adapter._convert_messages_to_prompt(messages)

    assert "Human: Hello" in prompt
    assert "Assistant: Hi there" in prompt
    assert "Human: How are you?" in prompt
    assert "---" in prompt
```

### Pattern 3: Integration Test Structure

**What:** One test that spawns an actual Claude CLI subprocess and verifies fact recall across turns.

**When to use:** TEST-05 only — real API cost incurred.

**File location:** `backend/tests/integration/test_cli_conversation_memory.py` (new file)

**Structure:**
```python
@pytest.mark.integration  # Mark for exclusion from regular CI
@pytest.mark.asyncio
async def test_assistant_remembers_fact_across_turns():
    """
    Verify CLI adapter preserves conversation context across 3+ turns.

    Turn 1: Casually mention a fact (e.g., "I'm building a FastAPI app")
    Turn 2: Ask general question (build up context naturally)
    Turn 3: Ask about turn 1 fact WITHOUT repeating it

    IMPORTANT: Do NOT use "remember this" phrasing. Claude Code stores
    explicitly requested memories in memory.md, which would make the test
    pass for the wrong reason.
    """
    ...
```

### Pattern 4: Flutter Test File

**What:** New test file mirroring `conversation_provider_test.dart` pattern for `AssistantConversationProvider`.

**File location:** `frontend/test/unit/providers/assistant_conversation_provider_test.dart`

**Mock file:** `frontend/test/unit/providers/assistant_conversation_provider_test.mocks.dart` (generated by `dart run build_runner build`)

**Pattern (from existing `conversation_provider_test.dart`):**
```dart
@GenerateNiceMocks([
  MockSpec<AIService>(),
  MockSpec<ThreadService>(),
  MockSpec<DocumentService>(),
])
void main() {
  group('AssistantConversationProvider Unit Tests', () {
    late MockAIService mockAIService;
    late MockThreadService mockThreadService;
    late MockDocumentService mockDocumentService;
    late AssistantConversationProvider provider;

    setUp(() {
      mockAIService = MockAIService();
      mockThreadService = MockThreadService();
      mockDocumentService = MockDocumentService();
      provider = AssistantConversationProvider(
        aiService: mockAIService,
        threadService: mockThreadService,
        documentService: mockDocumentService,
      );
    });
    ...
  });
}
```

### Anti-Patterns to Avoid

- **Do NOT change `agent_service.py`:** BA flow is completely separate and unchanged. The fix is in `claude_cli_adapter.py` only.
- **Do NOT modify the `combined_prompt` assembly in `stream_chat()`:** The `[SYSTEM]: ... \n\n [USER]: ...` wrapping at line 264 already works. The new `_convert_messages_to_prompt()` returns the full multi-turn history, and it gets prepended with the system prompt exactly as before.
- **Do NOT use `messages[-1]` anywhere:** The entire point of the fix is to use all messages.
- **Do NOT use "remember this" in integration test:** Claude Code intercepts this phrase and writes to memory.md — the test would pass for wrong reasons.
- **Do NOT include `tool_result` message text in prompt:** Tool results can be very long (full document content). Skip them entirely. The annotation on the `tool_use` block is sufficient context.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Message truncation | Custom token counter | `ConversationService.build_conversation_context()` | Already handles truncation to 150k tokens, fulfilled pair exclusion, and DB loading |
| Flutter mocking | Custom mock classes | `mockito` with `@GenerateNiceMocks` | Already established pattern in all existing Flutter tests; mock generation by `build_runner` |

**Key insight:** `build_conversation_context()` already does the hard work — it loads from DB, filters fulfilled pairs, and truncates. The CLI adapter only needs to format what it receives. The formatter is pure text manipulation with no edge cases that require special libraries.

---

## Common Pitfalls

### Pitfall 1: Existing Test Breaks on Stdin Content Assertion

**What goes wrong:** `test_stream_chat_spawns_subprocess_with_correct_args` (line 566) asserts `b"[USER]:"` in the stdin write. After the fix, the format changes to `Human:`, so this assertion will fail.

**Why it happens:** The test checks the exact bytes written to stdin, which encode the format string.

**How to avoid:** Update the existing assertion from `b"[USER]:"` to `b"Human:"`. Also update `b"[SYSTEM]:"` check to match the new combined_prompt format (which is unchanged — the system prompt wrapper in `stream_chat()` line 264 stays as-is).

**Warning signs:** `AssertionError` on `test_stream_chat_spawns_subprocess_with_correct_args` after making the `_convert_messages_to_prompt()` change.

### Pitfall 2: Pre-Existing Failing Test

**What goes wrong:** `test_stream_chat_passes_api_key_in_env` already fails (1 test failing in current baseline). It asserts `env["ANTHROPIC_API_KEY"] == "secret-key-123"` but the current code strips env vars without adding the API key. This is a pre-existing bug unrelated to Phase 68.

**How to avoid:** Do NOT fix this test as part of Phase 68 (out of scope). Document it as pre-existing. The planner should note this baseline state.

**Warning signs:** Seeing this test in failure output should not be treated as a Phase 68 regression.

### Pitfall 3: Tool Result User Messages Produce Empty Text

**What goes wrong:** After a tool call, the conversation history contains a user message whose content is `[{"type": "tool_result", "tool_use_id": "...", "content": "..."}]`. The `_extract_text_content()` method returns empty string for these. The empty-message skip condition (`if not text.strip(): continue`) correctly skips them. But if the skip is missing, the formatter emits `Human: ` (empty label) which confuses the model.

**How to avoid:** The empty-text skip applies to both user and assistant messages. Ensure the skip check comes AFTER extraction, not before.

**Warning signs:** Empty `Human: ` lines in the formatted prompt visible in backend logs.

### Pitfall 4: Flutter Mock File Generation

**What goes wrong:** The `assistant_conversation_provider_test.mocks.dart` file must be generated by `dart run build_runner build`. If the developer forgets to run this after creating the test file with `@GenerateNiceMocks`, the test fails with import errors.

**How to avoid:** Include the `build_runner build` step explicitly in the plan task. Generate mocks before writing test assertions.

**Warning signs:** `Error: 'MockAIService' isn't a type` compilation error in the test file.

### Pitfall 5: Integration Test Uses "Remember This" Phrasing

**What goes wrong:** If the integration test prompt includes "please remember X" or "remember this fact", Claude Code stores it in `memory.md`. The test then passes because Claude reads from memory.md, not because conversation history is working.

**How to avoid:** Use casual, natural phrasing in turn 1 ("I'm working on a FastAPI backend"). Ask about it naturally in turn 3 ("What framework are we using for the backend?"). This tests real conversation memory, not Claude Code memory injection.

**Warning signs:** Test passes even when `_convert_messages_to_prompt()` still uses `messages[-1]` (impossible with proper casual fact — would only happen with memory.md).

### Pitfall 6: `combined_prompt` System Prompt Wrapper Not Updated

**What goes wrong:** In `stream_chat()` at line 264, the combined prompt is assembled as:
```python
combined_prompt = f"[SYSTEM]: {system_prompt}\n\n[USER]: {prompt_text}"
```
After the fix, `prompt_text` is the full multi-turn history (e.g., `Human: ...\n\n---\n\nAssistant: ...\n\n---\n\nHuman: ...`). The outer `[USER]:` wrapper is now misleading but does NOT break the behavior — the CLI receives the full conversation after the system marker.

**How to avoid:** Consider whether to update the wrapper to `[CONVERSATION]:` for clarity. However, since the CLI is not explicitly parsing these labels (it just gets the full text as a single prompt), the behavior is correct either way. Decision: leave the outer wrapper as-is to minimize change surface. Add a comment explaining the structure.

---

## Code Examples

### Complete New `_convert_messages_to_prompt()` (Verified against locked decisions)

```python
# Source: Locked decisions in 68-CONTEXT.md + pattern from agent_service.py lines 102-120
def _convert_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
    """
    Convert full conversation history to multi-turn prompt string for CLI.

    Replaces POC implementation that only used the last user message.
    Now formats all user/assistant messages with role labels and separators.

    Format:
      Human: [user text]

      ---

      Assistant: [assistant text]

      ---

      Human: [next user text]

    Rules:
    - Role labels: Human / Assistant (Anthropic native format)
    - Separator: '---' between turns
    - System messages: excluded
    - Empty assistant messages (tool_use only, no text): skipped
    - Multi-part content: text blocks kept; tool_use replaced with annotation;
      tool_result blocks (in user messages) skipped; thinking blocks excluded

    Args:
        messages: Full conversation history in standard format

    Returns:
        str: Multi-turn prompt text for CLI stdin
    """
    if not messages:
        return ""

    parts = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "user":
            label = "Human"
        elif role == "assistant":
            label = "Assistant"
        else:
            continue  # Skip system messages and unknown roles

        text = self._extract_text_content(content)

        if not text.strip():
            continue  # Skip empty messages (e.g., tool_use-only assistant turns)

        parts.append(f"{label}: {text}")

    return "\n\n---\n\n".join(parts)


def _extract_text_content(self, content: Any) -> str:
    """
    Extract readable text from message content.

    Handles string content directly.
    For list content, processes each block:
    - text blocks: included as-is
    - thinking blocks: excluded (internal reasoning, not final response)
    - tool_use blocks: replaced with brief annotation
    - tool_result blocks: skipped (part of user messages, not conversation text)

    Args:
        content: Message content (str or list of content blocks)

    Returns:
        str: Extracted text, empty string if nothing readable
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if not isinstance(part, dict):
                continue
            block_type = part.get("type", "")
            if block_type == "text":
                text_parts.append(part.get("text", ""))
            elif block_type == "thinking":
                pass  # Exclude internal reasoning
            elif block_type == "tool_use":
                tool_name = part.get("name", "")
                if "search_documents" in tool_name:
                    text_parts.append("[searched documents]")
                else:
                    text_parts.append("[performed an action]")
            elif block_type == "tool_result":
                pass  # Skip tool results (can be very long, not conversation text)
        return "\n".join(text_parts)

    return str(content)
```

### Test Cases for `_convert_messages_to_prompt()`

```python
# Source: TEST-01 and TEST-02 requirements + existing test class pattern
class TestClaudeCLIAdapterMessageConversion:
    """Tests for _convert_messages_to_prompt method."""

    # --- EXISTING TESTS (to update) ---

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_converts_string_content(self, mock_which):
        """Single user message with string content is correctly labeled."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        prompt = adapter._convert_messages_to_prompt(messages)
        # After fix: output is "Human: Hello, how are you?"
        assert "Human: Hello, how are you?" in prompt

    # --- NEW TESTS (TEST-01) ---

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_three_turn_conversation_has_all_messages(self, mock_which):
        """3-turn conversation includes all turns in output."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        assert "Human: Hello" in prompt
        assert "Assistant: Hi there" in prompt
        assert "Human: How are you?" in prompt
        assert prompt.count("---") == 2  # Two separators for three turns

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_ten_turn_conversation_preserves_all(self, mock_which):
        """10-turn conversation includes all turns (no truncation in formatter)."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = []
        for i in range(5):
            messages.append({"role": "user", "content": f"User message {i}"})
            messages.append({"role": "assistant", "content": f"Assistant message {i}"})
        prompt = adapter._convert_messages_to_prompt(messages)
        for i in range(5):
            assert f"User message {i}" in prompt
            assert f"Assistant message {i}" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_uses_human_assistant_labels(self, mock_which):
        """Role labels are Human:/Assistant: (Anthropic native format)."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        assert "Human:" in prompt
        assert "Assistant:" in prompt
        # Ensure NOT the old bracket format
        assert "[USER]:" not in prompt
        assert "[ASSISTANT]:" not in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_uses_triple_dash_separator(self, mock_which):
        """Turns are separated by '---' lines."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        assert "---" in prompt

    # --- NEW TESTS (TEST-02: multi-part content) ---

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_use_blocks_replaced_with_annotation(self, mock_which):
        """tool_use blocks in assistant message are replaced with annotation."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "Search for docs"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me search."},
                    {"type": "tool_use", "id": "t1", "name": "search_documents",
                     "input": {"query": "test"}}
                ]
            },
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        assert "[searched documents]" in prompt
        assert "Let me search." in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_use_only_assistant_messages_skipped(self, mock_which):
        """Assistant messages with only tool_use (no text) are skipped."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "Do something"},
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "save_artifact",
                     "input": {"title": "Doc"}}
                ]
            },
            {"role": "user", "content": "Thanks"},
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        # Tool-only assistant message should not appear
        assert "Assistant:" not in prompt
        assert "Human: Do something" in prompt
        assert "Human: Thanks" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_thinking_blocks_excluded(self, mock_which):
        """Thinking blocks in assistant messages are excluded from output."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "What is 2+2?"},
            {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "Let me reason..."},
                    {"type": "text", "text": "The answer is 4."}
                ]
            },
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        assert "The answer is 4." in prompt
        assert "Let me reason..." not in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_tool_result_user_messages_skipped(self, mock_which):
        """User messages containing tool_result blocks are skipped."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "user", "content": "Search"},
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Searching."},
                    {"type": "tool_use", "id": "t1", "name": "search_documents",
                     "input": {"query": "test"}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "t1",
                     "content": "Result: found 3 documents"}
                ]
            },
            {"role": "user", "content": "What did you find?"},
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        # Tool result message (3rd message) should be skipped
        assert "Result: found 3 documents" not in prompt
        assert "Human: What did you find?" in prompt

    @patch('app.services.llm.claude_cli_adapter.shutil.which', return_value='/usr/bin/claude')
    def test_system_messages_excluded(self, mock_which):
        """System role messages are excluded from formatted output."""
        adapter = ClaudeCLIAdapter(api_key="test-key")
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        prompt = adapter._convert_messages_to_prompt(messages)
        assert "You are helpful." not in prompt
        assert "Human: Hello" in prompt
```

### stdin Content Assertion Update (Existing Test)

The test at line 566-610 in the existing test file asserts:
```python
# BEFORE fix (must be updated):
assert b"[USER]:" in written_bytes

# AFTER fix:
assert b"Human:" in written_bytes
```

The `b"[SYSTEM]:"` assertion at line 609 checks the outer `combined_prompt` wrapper which is NOT changed — it stays correct.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `messages[-1]` only (POC comment in code) | Full history iteration | Phase 68 | Enables multi-turn memory |
| No `_extract_text_content()` helper | Separate helper method | Phase 68 | Testable content extraction |

**Deprecated/outdated:**
- POC comment "Production: Format multi-turn conversation with role labels" (line 123) — this is the production fix being implemented.

---

## Open Questions

1. **Does the outer `combined_prompt` wrapper need updating?**
   - What we know: After fix, `prompt_text` contains `Human: ...\n\n---\n\nAssistant: ...`. The outer wrapper adds `[SYSTEM]: {system_prompt}\n\n[USER]: {prompt_text}`. For Assistant threads, `system_prompt` is empty string (`""`) per `ai_service.py` line 909.
   - What's unclear: Whether the empty `[SYSTEM]: \n\n[USER]:` prefix before multi-turn history confuses the CLI.
   - Recommendation: Keep as-is. For Assistant threads, system_prompt is empty so the wrapper becomes `[SYSTEM]: \n\n[USER]: Human: ...` which the CLI will treat as context. LOW risk. If the integration test fails, update the wrapper. Decision: plan a "verify and update if needed" step.

2. **Should `_extract_text_content()` be a private method or inline?**
   - What we know: The existing test class tests `_convert_messages_to_prompt()` directly. The helper method enables focused unit testing of extraction logic.
   - Recommendation: Make it a private method (`_extract_text_content`) for testability. HIGH confidence this is correct.

---

## Sources

### Primary (HIGH confidence)
- Direct code read: `backend/app/services/llm/claude_cli_adapter.py` — confirmed current implementation, bug location, call structure
- Direct code read: `backend/app/services/agent_service.py` lines 102-120 — confirmed proven formatting pattern to copy from
- Direct code read: `backend/app/services/conversation_service.py` — confirmed `build_conversation_context()` loads all messages, handles truncation
- Direct code read: `backend/app/routes/conversations.py` lines 136-165 — confirmed call chain passes full conversation list to AIService
- Direct code read: `backend/tests/unit/llm/test_claude_cli_adapter.py` — confirmed existing test class structure, assertion patterns, and pre-existing failing test
- Direct code read: `frontend/lib/providers/assistant_conversation_provider.dart` — confirmed provider structure, mock injection points, event types handled
- Direct code read: `frontend/test/unit/providers/conversation_provider_test.dart` — confirmed Flutter test pattern with mockito `@GenerateNiceMocks`
- Test run: `./venv/bin/python -m pytest tests/unit/llm/test_claude_cli_adapter.py -q` — confirmed 34 pass, 1 pre-existing fail (`test_stream_chat_passes_api_key_in_env`)
- Phase CONTEXT.md: `/Users/a1testingmac/projects/XtraSkill/.planning/phases/68-core-conversation-memory-fix/68-CONTEXT.md` — all decisions locked

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tooling already in project, no new dependencies
- Architecture: HIGH — single-file change confirmed by call chain analysis; pattern copied from proven agent_service.py
- Pitfalls: HIGH — identified from direct code analysis and test run; pre-existing test failure documented

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (stable architecture, no fast-moving dependencies)
