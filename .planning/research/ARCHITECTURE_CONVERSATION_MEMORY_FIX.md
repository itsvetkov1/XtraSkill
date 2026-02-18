# Architecture Research: Conversation Memory Fix Integration

**Domain:** Assistant conversation memory fix
**Researched:** 2026-02-18
**Confidence:** HIGH

## Problem Statement

The ClaudeCLIAdapter currently passes only the last user message to the Claude CLI via the `-p` prompt flag (line 106-137 in `claude_cli_adapter.py`). This causes the CLI to have no memory of previous conversation turns, making multi-turn conversations impossible.

The BA flow (AgentService in `agent_service.py`) formats full history by concatenating all messages with role labels into a single prompt string (lines 103-120). We need a similar approach for the Assistant flow, but integrated with the CLI subprocess architecture.

## Current Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AIService (Router)                       │
│  Detects thread type, routes to correct adapter             │
├─────────────────────────────────────────────────────────────┤
│              ┌──────────────┐    ┌──────────────┐            │
│              │ AgentService │    │ ClaudeCLI    │            │
│              │  (BA flow)   │    │   Adapter    │            │
│              │              │    │ (Assistant)  │            │
│              │ SDK query()  │    │ Subprocess   │            │
│              └──────┬───────┘    └──────┬───────┘            │
│                     │                   │                    │
├─────────────────────┴───────────────────┴────────────────────┤
│                 conversation_service.py                       │
│           build_conversation_context(thread_id)              │
│  Returns: List[Dict] messages from SQLite (chronological)    │
└─────────────────────────────────────────────────────────────┘
```

### Current Data Flow

1. **Frontend sends message** → Backend `/api/threads/{id}/chat` endpoint
2. **ConversationService** loads full message history from SQLite
3. **AIService** routes based on `thread_type` field:
   - BA Assistant → AgentService (SDK)
   - Assistant → ClaudeCLIAdapter (subprocess)
4. **ClaudeCLIAdapter._convert_messages_to_prompt()** extracts ONLY last message (BUG)
5. **Subprocess spawned:** `claude -p "{prompt}" --output-format stream-json`
6. **CLI has no memory** of previous turns → context lost

### Integration Points

| Component | Interface | Notes |
|-----------|-----------|-------|
| `conversation_service.build_conversation_context()` | Returns `List[Dict[str, Any]]` | Standard message format: `{"role": "user/assistant", "content": str}` |
| `ClaudeCLIAdapter._convert_messages_to_prompt()` | Converts message list → string | Currently broken (only takes last message) |
| `ClaudeCLIAdapter.stream_chat()` | Spawns subprocess with prompt via stdin | Uses `process.stdin.write(combined_prompt.encode())` |
| `AgentService.stream_chat()` | Formats full history for SDK | Lines 103-120: `[ROLE]: content` blocks |

## Approach Comparison

### Approach A: Format All History in Prompt String (RECOMMENDED)

**What:** Concatenate all messages with role labels into a single prompt string, like the BA flow does.

**Implementation:**
```python
def _convert_messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
    """Convert full message history to formatted prompt string."""
    if not messages:
        return ""

    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if isinstance(content, str):
            prompt_parts.append(f"[{role.upper()}]: {content}")
        elif isinstance(content, list):
            # Handle multi-part content (tool results, images)
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            if text_parts:
                prompt_parts.append(f"[{role.upper()}]: {'\n'.join(text_parts)}")

    return "\n\n".join(prompt_parts)
```

**Integration points:**
- Change: `claude_cli_adapter.py` lines 106-137 (replace POC implementation)
- No change: Everything else stays the same
- Testing: Modify existing Assistant conversation to verify memory persists

**Pros:**
- ✅ Minimal code changes (single method in one file)
- ✅ Proven pattern (BA flow already works this way)
- ✅ No new dependencies or external state
- ✅ Works with existing subprocess architecture
- ✅ Simple to test and verify
- ✅ HIGH confidence (directly mirrors working BA flow)

**Cons:**
- ⚠️ Shell argument length limits (8,191 chars on Windows, ~2MB on Unix)
  - **Mitigation:** Already using stdin pipe (line 297-299), not command-line args
  - **No actual risk:** Prompt already passed via stdin in current code
- ⚠️ No rich structure (flattens conversation to text)
  - **Not a problem:** CLI doesn't support structured message API anyway

**Data flow changes:**
```
BEFORE:
messages (all) → _convert_messages_to_prompt() → last message only → CLI

AFTER:
messages (all) → _convert_messages_to_prompt() → "[USER]: ...\n\n[ASSISTANT]: ..." → CLI
```

**Code change scope:**
- Files modified: 1 (`backend/app/services/llm/claude_cli_adapter.py`)
- Lines changed: ~30 (replace _convert_messages_to_prompt method)
- New files: 0
- New dependencies: 0

**Testing strategy:**
1. Unit test: Verify `_convert_messages_to_prompt()` formats multiple messages correctly
2. Integration test: Create Assistant thread, send 3 messages, verify context preserved
3. Regression test: Verify BA flow still works (unchanged)
4. Edge case: Test with long conversation (100+ messages) to verify no truncation issues

---

### Approach B: Use Claude CLI Session/Resume Features

**What:** Maintain a CLI session per thread using `--session-id` flag, let CLI handle persistence.

**Implementation:**
```python
def stream_chat(self, messages, system_prompt, tools, max_tokens):
    # Use thread_id as session_id (must be UUID)
    session_id = self.thread_id  # Already set via set_context()

    # Extract only the new user message (last in list)
    new_message = messages[-1].get("content", "")

    cmd = [
        self.cli_path,
        "-p",
        "--session-id", session_id,  # Resume session
        "--output-format", "stream-json",
        "--model", self.model,
    ]

    # Pipe new message only
    process.stdin.write(new_message.encode())
```

**Integration points:**
- Change: `claude_cli_adapter.py` stream_chat() method
- Change: Session lifecycle management (create/cleanup)
- Change: Thread model (ensure thread.id is UUID)
- Testing: Verify sessions persist across requests

**Pros:**
- ✅ CLI handles conversation history (less code)
- ✅ Rich session state (permissions, context, tools)
- ✅ Natural fit with CLI's design intent

**Cons:**
- ❌ **CRITICAL BUG:** Session resume broken in v2.1.31+ (Feb 2026)
  - `/resume` only shows ~5-10 recent sessions
  - `sessions-index.json` no longer updated/read
  - In-session `/resume` command broken
  - Source: [GitHub Issue #26123](https://github.com/anthropics/claude-code/issues/26123), [GitHub Issue #25729](https://github.com/anthropics/claude-code/issues/25729)
- ❌ Sessions are local to machine (can't transfer/backup)
- ❌ `--no-session-persistence` doesn't work with `-p` mode in all versions
- ❌ Session files grow linearly (~3-5 MB at 180K tokens)
- ❌ **Cannot access previous messages via API** (GitHub Issue #109)
  - No programmatic way to display conversation history in UI
  - Would need to manually parse `.jsonl` files from `~/.claude/projects/`
- ❌ Extra complexity: session lifecycle management, cleanup, orphan detection
- ⚠️ Requires thread.id to be UUID (current: string, might not be UUID format)

**Verdict:** **NOT VIABLE** due to active regression bug and lack of message access API.

**Confidence:** MEDIUM (CLI features well-documented, but regression makes it unusable)

**Sources:**
- [Claude Code Session Management - Steve Kinney](https://stevekinney.com/courses/ai-development/claude-code-session-management)
- [Session Persistence - ruvnet/claude-flow Wiki](https://github.com/ruvnet/claude-flow/wiki/session-persistence)
- [BUG: /resume broken in v2.1.31+](https://github.com/anthropics/claude-code/issues/26123)
- [BUG: Session history inaccessible via API](https://github.com/anthropics/claude-agent-sdk-python/issues/109)

---

### Approach C: Pipe Conversation via stdin with `--input-format stream-json`

**What:** Use CLI's stream-json input format to send structured message history.

**Implementation:**
```python
def stream_chat(self, messages, system_prompt, tools, max_tokens):
    cmd = [
        self.cli_path,
        "-p",
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--model", self.model,
    ]

    # Convert messages to NDJSON format
    ndjson_messages = []
    for msg in messages:
        ndjson_messages.append(json.dumps({
            "type": msg["role"],
            "message": {"role": msg["role"], "content": msg["content"]},
            "session_id": self.thread_id,
            "parent_tool_use_id": None
        }) + "\n")

    # Pipe all messages via stdin
    process.stdin.write("".join(ndjson_messages).encode())
```

**Integration points:**
- Change: `claude_cli_adapter.py` stream_chat() and message conversion
- Change: Input format from text to NDJSON
- Change: Output parsing (already stream-json, but verify message structure)
- Testing: Verify multi-turn conversations work, tool calls preserved

**Pros:**
- ✅ Structured message format (preserves tool calls, multi-part content)
- ✅ Designed for multi-agent pipelines and programmatic use
- ✅ Supports chaining multiple Claude instances
- ✅ Native support for session_id tracking

**Cons:**
- ❌ **KNOWN BUG:** Duplicate session entries in `.jsonl` files (Issue #5034)
  - Each message causes history duplication in session file
  - Affects v1.0.67+ (macOS confirmed, likely all platforms)
  - Source: [GitHub Issue #5034](https://github.com/anthropics/claude-code/issues/5034)
- ❌ More complex parsing (NDJSON instead of simple text)
- ❌ Limited documentation on message format edge cases
- ❌ Unclear if system prompts work properly in stream-json input mode
- ⚠️ Requires reformatting existing message history to NDJSON structure
- ⚠️ May complicate tool result handling (need to verify format)

**Verdict:** **NOT RECOMMENDED** due to active duplication bug and added complexity for minimal benefit.

**Confidence:** MEDIUM (feature well-documented, but bug makes it risky)

**Sources:**
- [Stream-JSON Chaining - ruvnet/claude-flow Wiki](https://github.com/ruvnet/claude-flow/wiki/Stream-Chaining)
- [CLI Reference - Claude Code Docs](https://code.claude.com/docs/en/cli-reference)
- [BUG: Duplicate entries in stream-json mode](https://github.com/anthropics/claude-code/issues/5034)

---

### Approach D: Use Claude Code SDK Directly (No CLI)

**What:** Replace ClaudeCLIAdapter with a direct SDK integration (like AgentService uses).

**Implementation:**
```python
# New adapter: ClaudeCodeSDKAdapter
from claude_agent_sdk import query, ClaudeAgentOptions

class ClaudeCodeSDKAdapter(LLMAdapter):
    async def stream_chat(self, messages, system_prompt, tools, max_tokens):
        # Convert messages to single prompt (SDK limitation)
        prompt = self._messages_to_prompt(messages)

        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            model=self.model,
            max_turns=1  # Don't loop, we handle tools externally
        )

        async for message in query(prompt=prompt, options=options):
            # Translate SDK events to StreamChunk
            yield self._translate_sdk_event(message)
```

**Integration points:**
- Change: Create new `claude_code_sdk_adapter.py` (copy from `agent_service.py`)
- Change: `ai_service.py` routing logic (use SDK adapter instead of CLI)
- Change: Remove subprocess management code
- Testing: Full integration test suite (SDK behaves differently than CLI)

**Pros:**
- ✅ Native Python API (no subprocess overhead)
- ✅ Better error handling (exceptions vs stderr parsing)
- ✅ Easier debugging (no process lifecycle issues)
- ✅ Proven working (AgentService already uses it)

**Cons:**
- ❌ **Architectural inconsistency:** AgentService already uses SDK for BA flow
  - If we use SDK for Assistant too, why have ClaudeCLIAdapter at all?
  - Would make ClaudeCLIAdapter dead code
- ❌ Duplication of existing AgentService code
- ❌ Same limitation as Approach A (flattens messages to prompt string)
- ❌ SDK's `query()` function doesn't handle conversation history
  - Need `ClaudeSDKClient` for proper history management (more complex)
  - Source: [Claude Agent SDK Documentation](https://blog.gopenai.com/claude-agent-sdk-reference-92c0c2f3b3ef)
- ⚠️ Requires refactoring existing code (not just fixing a bug)
- ⚠️ May introduce regressions in CLI-specific behavior

**Verdict:** **OUT OF SCOPE** for a memory fix. This is a rewrite, not a bug fix.

**Confidence:** HIGH (SDK well-documented and proven), but **not appropriate for this milestone**.

**Sources:**
- [Claude Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [Getting Started with Claude Agent SDK](https://medium.com/@aiablog/claude-agent-sdk-python-826a2216381d)

---

## Architectural Patterns

### Pattern: Message History Formatting

**What:** Convert structured message list to a text format the CLI can understand.

**When to use:** When interfacing with text-based LLM inputs (CLI, curl, etc.)

**Trade-offs:**
- Pro: Simple, no external dependencies
- Pro: Works with any LLM that accepts text prompts
- Con: Loses rich structure (tool results become text)
- Con: No type safety on message format

**Example (Current BA Flow):**
```python
# From agent_service.py lines 103-120
prompt_parts = []
for msg in messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if isinstance(content, str):
        prompt_parts.append(f"[{role.upper()}]: {content}")
    elif isinstance(content, list):
        # Handle tool results or multi-part content
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "tool_result":
                    prompt_parts.append(f"[TOOL_RESULT]: {part.get('content', '')}")
                elif part.get("type") == "text":
                    prompt_parts.append(f"[{role.upper()}]: {part.get('text', '')}")

full_prompt = "\n\n".join(prompt_parts)
```

**Recommendation:** Use this pattern for ClaudeCLIAdapter (Approach A).

---

### Pattern: Subprocess Lifecycle Management

**What:** Proper cleanup of spawned processes to prevent zombies.

**Current implementation (lines 364-378):**
```python
finally:
    if process and process.returncode is None:
        logger.warning("CLI subprocess still running, terminating...")
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("CLI subprocess did not terminate, killing...")
            process.kill()
            await process.wait()
```

**Trade-offs:**
- Pro: Prevents zombie processes
- Pro: Graceful shutdown with fallback to kill
- Con: Adds complexity to error handling

**Recommendation:** Keep existing pattern, it's well-implemented.

---

## Data Flow (Proposed with Approach A)

### Request Flow

```
Frontend sends message
    ↓
POST /api/threads/{id}/chat
    ↓
conversation_service.build_conversation_context(thread_id)
    ↓ Returns: [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]
    ↓
AIService.stream_chat(messages=full_history, ...)
    ↓
ClaudeCLIAdapter._convert_messages_to_prompt(messages)
    ↓ Returns: "[USER]: Hi\n\n[ASSISTANT]: Hello\n\n[USER]: <new message>"
    ↓
combined_prompt = f"[SYSTEM]: {system_prompt}\n\n{formatted_history}"
    ↓
Subprocess: claude -p (reads from stdin)
    ↓
CLI has full context → generates contextual response
    ↓
StreamChunk events → SSE to frontend
```

### Key Changes from Current Flow

| Step | Current (Broken) | Proposed (Fixed) |
|------|------------------|------------------|
| Message extraction | Last message only | All messages formatted |
| Prompt format | `content` string | `[USER]: ...\n\n[ASSISTANT]: ...` |
| Context window | Single turn | Full conversation history |

---

## Anti-Patterns

### Anti-Pattern 1: Relying on External Session Persistence for Core Functionality

**What people do:** Use CLI session features (`--session-id`, `--resume`) to maintain conversation history.

**Why it's wrong:**
- CLI session features are buggy (v2.1.31+ regression)
- Sessions are local to machine (no backup/transfer)
- No programmatic access to message history
- Session lifecycle adds complexity

**Do this instead:** Treat CLI as stateless subprocess, manage conversation history in application database (SQLite).

---

### Anti-Pattern 2: Premature Abstraction

**What people do:** Create generic "conversation history to prompt" converter with plugins, strategies, formats.

**Why it's wrong:**
- We only have 2 flows (BA and Assistant)
- Both use same format (`[ROLE]: content`)
- Abstraction adds complexity without benefit

**Do this instead:** Copy working pattern from BA flow directly. If a third flow needs different format, refactor then.

---

### Anti-Pattern 3: Using stream-json Input for Simple Text Conversations

**What people do:** Use `--input-format stream-json` with NDJSON message objects for regular chat.

**Why it's wrong:**
- stream-json designed for multi-agent pipelines, not simple chat
- Known duplication bug in session files
- Added complexity (NDJSON parsing, message structure)
- Text format works fine and is simpler

**Do this instead:** Use simple text format with role labels. stream-json is for chaining multiple Claude instances together, not for single conversations.

---

## Recommendation Summary

**RECOMMENDED: Approach A — Format All History in Prompt String**

**Rationale:**
1. **Proven pattern:** BA flow already works this way (lines 103-120 in `agent_service.py`)
2. **Minimal changes:** Single method in one file (`claude_cli_adapter.py`)
3. **HIGH confidence:** No new dependencies, no active bugs, simple to test
4. **No regressions:** Doesn't change subprocess architecture or other flows
5. **Quick win:** Can be implemented and tested in <1 hour

**Alternative approaches rejected:**
- **Approach B (Session/Resume):** BLOCKED by active CLI bugs, no message API access
- **Approach C (stream-json):** Active duplication bug, complexity without benefit
- **Approach D (SDK):** Out of scope (rewrite, not bug fix), would make ClaudeCLIAdapter obsolete

**Implementation plan:**
1. Replace `_convert_messages_to_prompt()` method (lines 106-137)
2. Copy formatting logic from `agent_service.py` (lines 103-120)
3. Add unit tests for multi-message formatting
4. Add integration test (3-turn conversation in Assistant thread)
5. Verify no regression in BA flow

**Testing checklist:**
- [ ] Unit: `_convert_messages_to_prompt()` formats 3 messages correctly
- [ ] Unit: Handles multi-part content (tool results)
- [ ] Integration: Assistant thread with 3 turns preserves context
- [ ] Integration: Long conversation (100+ messages) works without truncation
- [ ] Regression: BA flow still works (no changes to `agent_service.py`)
- [ ] Edge case: Empty message list returns empty string
- [ ] Edge case: Single message (backward compatibility)

**Estimated complexity:** LOW (1-2 hours implementation, 1 hour testing)

---

## Sources

**CLI Features & Documentation:**
- [CLI Reference - Claude Code Docs](https://code.claude.com/docs/en/cli-reference)
- [Claude Code Session Management - Steve Kinney](https://stevekinney.com/courses/ai-development/claude-code-session-management)
- [Session Persistence - ruvnet/claude-flow Wiki](https://github.com/ruvnet/claude-flow/wiki/session-persistence)
- [Stream-JSON Chaining - ruvnet/claude-flow Wiki](https://github.com/ruvnet/claude-flow/wiki/Stream-Chaining)
- [Shipyard Claude Code Cheatsheet](https://shipyard.build/blog/claude-code-cheat-sheet/)

**Active Bugs:**
- [BUG #26123: /resume broken since v2.1.31](https://github.com/anthropics/claude-code/issues/26123)
- [BUG #25729: Session history inaccessible](https://github.com/anthropics/claude-code/issues/25729)
- [BUG #5034: Duplicate entries in stream-json mode](https://github.com/anthropics/claude-code/issues/5034)
- [QUESTION #109: No API access to historical messages](https://github.com/anthropics/claude-agent-sdk-python/issues/109)

**Agent SDK Documentation:**
- [Claude Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [Claude Developer Guide Agent SDK Reference](https://blog.gopenai.com/claude-agent-sdk-reference-92c0c2f3b3ef)
- [Getting Started with Claude Agent SDK](https://medium.com/@aiablog/claude-agent-sdk-python-826a2216381d)

**General Resources:**
- [Claude CLI stdin piping and -p flag usage](https://deepwiki.com/anthropics/claude-code/2.3-cli-commands-and-interaction-modes)
- [Running Claude Code from Windows CLI](https://dstreefkerk.github.io/2026-01-running-claude-code-from-windows-cli/)

---

*Architecture research for: Assistant conversation memory fix*
*Researched: 2026-02-18*
*Confidence: HIGH (Approach A), MEDIUM (Approaches B/C), HIGH but out-of-scope (Approach D)*
