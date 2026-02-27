# XtraSkill Assistant Flow — Review Report

**Date:** 2026-02-25
**Reviewer:** Alpharius(dev)
**Focus:** Assistant flow (the path forward), with general project health findings

---

## Executive Summary

The project is in a healthy state with 14 shipped milestones and clean architecture overall. The assistant flow (v3.x series) is mostly functional but has several structural gaps — the most critical being that **selected skills are never actually injected into the runtime system prompt**, which means the Skill Discovery UI (v3.1) is cosmetic for assistant threads right now. There are also two parallel implementations of the Agent SDK path that need reconciling, and several open user stories with stale statuses.

---

## 1. Architecture Map

### Two Separate Execution Paths

```
conversations.py /threads/{id}/chat
         │
         ▼
    AIService (ai_service.py)
         │
         ├─── thread_type == "ba_assistant"
         │         │
         │         ├── provider = anthropic/google/deepseek
         │         │     → Direct API adapter + manual tool loop
         │         │     → SYSTEM_PROMPT + BA tools (search_documents, save_artifact)
         │         │
         │         └── provider = claude-code-sdk
         │               → ClaudeAgentAdapter (SDK internal tool loop)
         │               → SYSTEM_PROMPT + MCP BA tools
         │
         └─── thread_type == "assistant"
                   │
                   └── HARDCODED → claude-code-cli
                         → ClaudeCLIAdapter (subprocess)
                         → Empty system prompt ← CRITICAL GAP
                         → No tools (intentional per LOGIC-02)
```

### Parallel (Unused) Path

`AgentService` in `agent_service.py` implements the Claude Agent SDK flow independently. It is **not wired into the production request path** — `conversations.py` uses `AIService`, not `AgentService`. This is dead or test-only code that duplicates the `ClaudeAgentAdapter` logic.

---

## 2. Critical Issues

---

### ISSUE-01: Skill selection is cosmetic — skills never reach the LLM

**Severity:** Critical
**Component:** `backend/app/services/ai_service.py` — LOGIC-01 (line 931)

```python
# LOGIC-01: No system prompt for Assistant threads (per locked decision)
system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""
```

The v3.1 milestone shipped a skill browser UI and selection mechanism. When a user picks a skill, that skill's content is never passed to the LLM for assistant threads. The system prompt is always empty for `thread_type == "assistant"`, regardless of what skill the user selected.

**Impact:** Every assistant conversation starts with a blank-slate Claude with no guidance, no persona, no constraints. The "skill" is purely a UI label.

**What needs to happen:** The skill system prompt must be loaded and passed as the system prompt for the CLI adapter when an assistant thread has a skill bound. Either:
- Pass skill identifier on the chat request, load it in `AIService`
- Or store the selected skill on the Thread model and load at chat time

**Context:** The `skill_loader.py` service exists and works — it just needs to be called in the assistant path.

---

### ISSUE-02: Dead code — AgentService is parallel to ClaudeAgentAdapter

**Severity:** High
**Component:** `backend/app/services/agent_service.py`

`AgentService` implements the Claude Agent SDK streaming with MCP tools (identical to `ClaudeAgentAdapter`), but is not instantiated by any route. `conversations.py` uses `AIService` exclusively. This creates:

- Maintenance double burden — two places to update when Agent SDK changes
- Confusion about which code path is active
- `AgentService` has `max_turns=3` while `ClaudeAgentAdapter` has no limit — different behavior if the wrong path is used by mistake

**Recommendation:** Either remove `agent_service.py` entirely, or document that it is a standalone test harness and not part of the production path. If it's kept, add a prominent comment at the top.

---

### ISSUE-03: BUG-023 is fixed but marked Open

**Severity:** Medium (tracking accuracy)
**Component:** `user_stories/BUG-023_cli-adapter-drops-conversation-history.md`, `user_stories/INDEX.md`

The bug story says the CLI adapter only sends the last user message. The actual code in `claude_cli_adapter.py` has been fixed (v3.1.1, Phases 68-70) — `_convert_messages_to_prompt()` now iterates all messages with `Human:/Assistant:` role labels and `---` separators.

**Status should be: Done** (shipped in v3.1.1)

**Remaining concern (separate from the bug):** The fixed implementation sends the full multi-turn history as a single formatted string wrapped in `[USER]: ...`. This is not the same as native multi-turn message passing. For very long conversations, the model receives all turns concatenated as one large user prompt, which can degrade attention and context understanding compared to proper alternating turns.

---

### ISSUE-04: Token tracking records wrong model for assistant threads

**Severity:** Medium
**Component:** `backend/app/routes/conversations.py` (line 29), tracked as BUG-022

```python
AGENT_MODEL = "claude-sonnet-4-5-20250514"  # Used for all token tracking
```

Assistant threads use `claude-sonnet-4-5-20250929` (DEFAULT_MODEL in `claude_cli_adapter.py`), but all token usage records write `claude-sonnet-4-5-20250514`. Cost projections and per-model analytics will be wrong for all assistant threads.

**Fix:** Pull the actual model string from `self.adapter.model` at track time, or pass it through the `message_complete` event data.

---

### ISSUE-05: subprocess per request — high latency path for simple conversations

**Severity:** Medium
**Component:** `backend/app/services/llm/claude_cli_adapter.py`

Assistant threads are hardcoded to use the CLI subprocess even when no agent capabilities (tools, file access, multi-step reasoning) are needed. For a simple "chat" interaction, spawning a Node.js process adds 120–400ms cold start overhead even with the pre-warming pool.

The process pool (`POOL_SIZE = 2`) is documented as "sufficient for single-user dev." With even 2 concurrent users, both will hit cold spawns frequently.

**Consideration for the path forward:** If assistant threads don't use tools (LOGIC-02), the CLI provides no advantage over the direct Anthropic API. The CLI makes sense when the agent loop's autonomous tool execution is needed. For skill-enhanced conversations, the direct API with explicit tool definitions (like BA Assistant) would be simpler and faster.

---

## 3. High-Priority Issues

---

### ISSUE-06: Message not saved on client disconnect

**Severity:** High
**Component:** `backend/app/routes/conversations.py`
**Open story:** THREAD-004

```python
# Save assistant message after streaming completes
if accumulated_text and not body.artifact_generation:
    await save_message(db, thread_id, "assistant", accumulated_text)
```

If the client disconnects mid-stream, this block never executes. The user's question is saved but the AI response is lost. On reconnect (or refresh), the thread shows an orphaned user message with no AI reply. This also corrupts the alternating user/assistant message requirement for the context builder.

The `request.is_disconnected()` check only prevents yielding to the disconnected client — the generator still runs to completion in the background, but the event loop will cancel it when the response finishes. In practice the behavior is non-deterministic.

**Fix:** Wrap the save in a try/finally or use a background task.

---

### ISSUE-07: Summarization service uses print() instead of logger

**Severity:** Low (but signals quality gap)
**Component:** `backend/app/services/summarization_service.py` line 167

```python
except Exception as e:
    print(f"Summarization failed: {e}")  # Not captured by logging infrastructure
    return None
```

Summarization failures are invisible to the logging system (the logging infrastructure added in v1.9.5). Errors go to stdout and are lost.

---

### ISSUE-08: `datetime.utcnow()` deprecation across the codebase

**Severity:** Medium
**Component:** Multiple files — `models.py`, `threads.py`, `conversation_service.py`, etc.

`datetime.utcnow()` was deprecated in Python 3.12. The pattern appears in default values and explicit calls throughout the codebase. Columns are declared `DateTime(timezone=True)` but receive naive datetime objects.

This will generate deprecation warnings now and break in future Python versions. The correct replacement is `datetime.now(timezone.utc)` from `from datetime import timezone`.

---

### ISSUE-09: Process pool refill loop has no backoff

**Severity:** Low-Medium
**Component:** `backend/app/services/llm/claude_cli_adapter.py` — `ClaudeProcessPool._refill_loop()`

```python
async def _refill_loop(self) -> None:
    while self._running:
        await asyncio.sleep(self.REFILL_DELAY)  # 0.1 seconds
        while self._running and self._queue.qsize() < self.POOL_SIZE:
            proc = await self._spawn_warm_process()
            ...
```

If `_spawn_warm_process()` fails (CLI not found, auth issue, etc.), the loop retries every 100ms indefinitely. On startup failure this will log thousands of warnings per minute. No error counting, no exponential backoff, no max retry limit.

---

### ISSUE-10: Artifact correlation is timestamp-based with 5-second window

**Severity:** Medium
**Component:** `backend/app/services/conversation_service.py` — `_identify_fulfilled_pairs()`

```python
ARTIFACT_CORRELATION_WINDOW = timedelta(seconds=5)
```

Artifact-to-message correlation uses a ±5s timestamp window. On a slow host (heavy DB load, large BRD generation), the window could expire before the artifact is created. This would leave the "generate BRD" exchange in the conversation history instead of filtering it out, leading to the conversation context growing with fulfilled artifact requests — which contributed to the original BUG-016 (artifact multiplication).

**Improvement:** Consider linking artifacts to messages explicitly (e.g., a `trigger_message_id` FK) rather than relying on timestamp proximity.

---

## 4. Architecture Gaps for the "Path Forward"

These are not bugs — they are design decisions that need to be made as the assistant flow is built out.

---

### GAP-01: No mechanism to bind a skill to a thread at runtime

The Thread model has `thread_type` and `model_provider` but no `skill_id` or `skill_name` field. When a user selects a skill from the skill browser (v3.1), there is no column to persist which skill was chosen. This means:

- After page refresh, the skill selection is lost
- The backend cannot load the correct system prompt
- Token tracking cannot attribute cost to a specific skill

**Path forward requires:** Either storing `selected_skill` on the Thread, or on each Message (if skills can change mid-conversation).

---

### GAP-02: Skill prompt injection architecture is undefined

Even once a skill is bound to a thread, the mechanism for injecting it into the system prompt needs to be decided:

**Option A:** BA-style — append skill SKILL.md content to a base system prompt
**Option B:** Full replacement — each skill's SKILL.md IS the system prompt
**Option C:** Tool-augmented — base prompt + skill as context in first user message

The current BA assistant uses Option A (`preset: "claude_code"` + `append: skill_prompt` in `AgentService`, or the explicit `SYSTEM_PROMPT` constant in `AIService`). For the assistant path, a clean decision is needed.

---

### GAP-03: Skills discovery UI exists but has no backend enforcement

`backend/app/routes/skills.py` serves skill metadata for the browser UI. But once selected, the skill name is not sent on the `/chat` request and not persisted. The backend cannot enforce "only use tools defined in this skill" or "apply this skill's system prompt."

---

### GAP-04: Assistant thread documents are thread-scoped but search is project-scoped

The `Document` model has a `thread_id` FK (for thread-scoped documents in assistant mode). The `search_documents` tool in `mcp_tools.py` queries by `project_id`. For assistant threads without a project, documents uploaded to that thread would not be searchable.

Looking at `document_search.py` (and the tool implementation), search uses `project_id` from ContextVar. For project-less assistant threads, `project_id` could be `None`, which would cause the search to return nothing or error.

**This needs verification** — if skills are expected to access uploaded documents, the search path must handle thread-scoped documents.

---

## 5. Stale User Story Statuses

| ID | Reported Status | Actual Status | Evidence |
|----|----------------|---------------|---------|
| BUG-023 | Open | Fixed | `_convert_messages_to_prompt()` now iterates all messages with full history |
| INDEX.md summary | 28 open / 20 done | Stale (not updated since 2026-02-18) | v3.1.1 shipped 2026-02-20 adding more fixes |

**Recommendation:** Run a story audit at the start of the next milestone.

---

## 6. Security Observations

These are not blocking for dev, but relevant before any external exposure:

- **`secret_key` default**: `"dev-secret-key-change-in-production"` only validated in production mode. A staging environment not explicitly set to "production" will use the insecure default.
- **Message content stored plaintext**: Documents are encrypted (Fernet), but conversation messages (`Message.content`) are plaintext in the DB. For a BA tool where customer requirements are discussed, this may be a concern.
- **v2.0 Security Audit still backlogged**: The entire security hardening milestone (Phases 49-53) has been deferred since 2026-02-13. If the project moves toward beta users, this is the next critical milestone regardless of feature state.

---

## 7. Quick Wins (Low Effort, High Value)

| Item | File | Effort |
|------|------|--------|
| Fix BUG-023 status to Done | `user_stories/BUG-023_*.md`, `INDEX.md` | 5 min |
| Replace `print()` with logger in summarization_service.py | `services/summarization_service.py:167` | 2 min |
| Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` | Multiple files | 30 min |
| Fix BUG-022: pass actual model to token tracking | `routes/conversations.py`, `services/ai_service.py` | 30 min |
| Add backoff to process pool refill loop | `services/llm/claude_cli_adapter.py` | 20 min |

---

## 8. Recommended Next Milestone Focus

Given that the **assistant flow is the path forward**, the next milestone should address:

1. **Skill-to-system-prompt wiring** (ISSUE-01 / GAP-01–03): Persist selected skill on Thread, load it at chat time, inject into system prompt. This makes v3.1 actually functional.
2. **Decide: CLI vs Direct API for Assistant threads**: The CLI subprocess adds latency and complexity. If skills don't need the agent loop, switch assistant threads to use the Anthropic direct API with the skill's system prompt. If they do need agent capabilities, keep the CLI but wire up MCP properly.
3. **Close BUG-022** (wrong model in token tracking): Easy fix, needed for accurate cost accounting.
4. **v2.0 Security Audit** (backlogged since Feb 13): Should be addressed before beta users.

---

*Report generated: 2026-02-25*
*Files reviewed: agent_service.py, ai_service.py, claude_agent_adapter.py, claude_cli_adapter.py, mcp_tools.py, conversations.py, threads.py, conversation_service.py, summarization_service.py, skill_loader.py, models.py, config.py, factory.py, base.py, ROADMAP.md, STATE.md, user_stories/INDEX.md, user_stories/BUG-023.md, .claude/business-analyst/SKILL.md*
