# BUG-023: Claude CLI Adapter Drops Conversation History

**Priority:** Critical
**Status:** Done
**Component:** Backend / LLM Adapters / Claude CLI Adapter
**Fixed In:** v3.1.1 (Phases 68-70)

---

## User Story
As a user chatting in an Assistant thread, I want the AI to remember everything discussed in my current conversation, so that I can have coherent multi-turn interactions without the AI forgetting what we just talked about.

---

## Problem

The Claude CLI adapter (`backend/app/services/llm/claude_cli_adapter.py`) only sends the **last user message** to the CLI subprocess, discarding the entire conversation history. This is a POC limitation that was never upgraded for production.

### Root Cause

`_convert_messages_to_prompt()` at line 118-137:

```python
# For POC: Use last user message
# Production: Format multi-turn conversation with role labels
last_message = messages[-1]
content = last_message.get("content", "")
```

The backend correctly loads all thread messages from SQLite via `build_conversation_context()` (conversation_service.py:122) and passes the full history to the adapter. But the adapter throws away everything except the final message before sending to the CLI.

### Observed Symptoms

1. **AI forgets within same thread**: User discusses topic A, then references it later — AI has no memory because only the latest message was sent. Example: User improves a prompt with prompt-enhancer skill, then asks AI to execute it — AI doesn't know what prompt was created.

2. **AI appears to have cross-thread memory**: Without thread-specific context, the AI relies on system prompt + project-level files (CLAUDE.md, .claude/ config), making responses seem like they "remember" things from other conversations when it's actually shared project context.

### Data Flow

```
[SQLite: all thread messages]
  → build_conversation_context() loads full history ✓
    → AIService passes messages[] to adapter ✓
      → ClaudeCLIAdapter._convert_messages_to_prompt()
        → DROPS ALL BUT LAST MESSAGE ✗
          → CLI receives: "[SYSTEM]: {system_prompt}\n\n[USER]: {last_message_only}"
```

---

## Acceptance Criteria

- [ ] `_convert_messages_to_prompt()` formats ALL messages from thread history
- [ ] Messages maintain chronological order with clear role labels
- [ ] AI can reference earlier parts of the same conversation
- [ ] Different threads remain fully isolated (no cross-contamination)
- [ ] Assistant threads (thread_type="assistant") work correctly — note: these get empty system prompt per LOGIC-01 (ai_service.py:909)
- [ ] BA Assistant threads (thread_type="ba_assistant") continue to work (they use a different adapter path via anthropic/gemini/deepseek, not CLI)
- [ ] Long conversations handle gracefully (consider token limits)

---

## Technical References

- **Bug location**: `backend/app/services/llm/claude_cli_adapter.py:106-137` (`_convert_messages_to_prompt`)
- **CLI invocation**: `backend/app/services/llm/claude_cli_adapter.py:258-299` (`stream_chat`)
- **Prompt assembly**: Line 264: `combined_prompt = f"[SYSTEM]: {system_prompt}\n\n[USER]: {prompt_text}"`
- **Context builder**: `backend/app/services/conversation_service.py:122` (`build_conversation_context`)
- **Thread type routing**: `backend/app/services/ai_service.py:909` — Assistant threads get empty system prompt
- **CLI flag**: `-p` (print mode, non-interactive) accepts prompt via stdin

### Key Constraint

Claude CLI `-p` flag accepts a single prompt string, not structured message arrays. The fix must format multi-turn history into a readable text format like:

```
[user]: First message
[assistant]: First response
[user]: Follow-up question
[assistant]: Follow-up response
[user]: Latest message
```

### Additional Fix Applied During Investigation

`frontend/lib/services/skill_service.dart` was missing auth headers — API returned 401 silently, showing no skills in the browser. Fixed by adding `_getAuthHeaders()` pattern matching all other services.

---

## Related

- Discovered during Phase 67 (Skill Info Popup) verification
- Only affects threads using Claude CLI adapter (provider: claude-code-cli)
- BA Assistant threads use anthropic/gemini/deepseek adapters which correctly pass structured messages

---

*Created: 2026-02-18*
