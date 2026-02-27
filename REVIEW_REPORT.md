# XtraSkill Project Review Report

**Date:** 2025-02-25
**Reviewer:** Alpharius(dev)
**Scope:** Full codebase review with focus on Assistant flow
**Project Version:** v3.1.1 (shipped 2026-02-20)
**Codebase Size:** ~105,000 lines (Python/Dart)

---

## Executive Summary

XtraSkill is a well-architected AI-powered business analyst tool built on FastAPI + Flutter. The assistant flow — the primary path forward — is functional but has several issues ranging from architectural concerns to concrete bugs that will compound as usage scales. This report catalogs 28 findings across 7 categories, each with context explaining *why* it matters and what the downstream impact is.

The project has strong foundations: clean adapter pattern for LLM providers, proper SSE streaming, decent error recovery, and a thoughtful system prompt. The issues below are the delta between "works in dev" and "works in production."

---

## Table of Contents

1. [Critical Issues (Must Fix)](#1-critical-issues-must-fix)
2. [Assistant Flow Architecture Issues](#2-assistant-flow-architecture-issues)
3. [Data Integrity & Persistence Issues](#3-data-integrity--persistence-issues)
4. [Security Concerns](#4-security-concerns)
5. [Performance & Scalability](#5-performance--scalability)
6. [Frontend Assistant Flow Issues](#6-frontend-assistant-flow-issues)
7. [Testing & Quality Gaps](#7-testing--quality-gaps)
8. [Improvement Recommendations](#8-improvement-recommendations)

---

## 1. Critical Issues (Must Fix)

### 1.1 Token Pricing Model Mismatch

**File:** `backend/app/services/token_tracking.py:16-26`

**Issue:** The pricing dict keys don't match the model identifiers used elsewhere in the code.

```python
# token_tracking.py uses:
"claude-sonnet-4-5-20250929"

# conversations.py uses:
AGENT_MODEL = "claude-sonnet-4-5-20250514"

# agent_service.py uses:
model="claude-sonnet-4-5-20250514"
```

**Context:** The model name `claude-sonnet-4-5-20250929` in the pricing dict will never match the actual model name `claude-sonnet-4-5-20250514` sent from `conversations.py`. This means `calculate_cost()` always falls through to the `"default"` pricing tier. Today the prices happen to be identical, so the financial impact is zero — but when you add new models with different pricing (Gemini, DeepSeek, a future Claude model), the tracking will silently use wrong pricing. You have an open bug for this (BUG-022).

**Impact:** Incorrect cost reporting. Users may hit or miss budget limits incorrectly when model-specific pricing diverges.

**Fix:** Align the pricing dict key with the actual model string, or normalize model names before lookup.

---

### 1.2 OAuth State Stored In-Memory

**File:** `backend/app/services/auth_service.py`

**Issue:** OAuth CSRF state parameters are stored in a Python dict (`{}`) in process memory.

**Context:** This is explicitly marked as a TODO in the code ("Move to Redis for multi-instance"). In a single-process dev setup, this works fine. But in production on Railway/Render with multiple workers or process restarts, the state dict vanishes. A user who initiates OAuth on worker A gets their callback routed to worker B — state validation fails, login breaks silently.

**Impact:** Authentication failures in any multi-process or auto-scaling deployment. Race condition if the process restarts between initiate and callback (typical OAuth flow takes 5-30 seconds).

**Fix:** Use Redis, database, or signed JWT state tokens that don't require server-side storage.

---

### 1.3 `datetime.utcnow()` Deprecation and Timezone Inconsistency

**Files:**
- `backend/app/services/conversation_service.py:116`
- `backend/app/services/token_tracking.py:117`
- `backend/app/routes/conversations.py:132`

**Issue:** Multiple uses of `datetime.utcnow()` which is deprecated in Python 3.12+ and returns naive (timezone-unaware) datetimes.

**Context:** The SQLAlchemy models use `DateTime(timezone=True)` columns, so the database expects timezone-aware timestamps. Meanwhile, `datetime.utcnow()` returns naive datetimes. SQLite silently stores these without complaint, but PostgreSQL (the stated production target) will reject or mishandle them. The `token_tracking.py:117` usage is particularly concerning because it's the monthly budget boundary calculation — a timezone mismatch could let users exceed budgets by up to 24 hours.

**Impact:** Broken budget enforcement on PostgreSQL. Silent data corruption of timestamp comparisons.

**Fix:** Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`.

---

### 1.4 Unbounded Tool Loop (Anthropic Direct Path)

**File:** `backend/app/services/ai_service.py:1089`

**Issue:** The direct API tool loop (`while True:`) has no iteration cap.

```python
while True:  # Line 1089
    # Stream from adapter
    async for chunk in self.adapter.stream_chat(...):
        ...
    # If no tool calls, we're done
    if not tool_calls:
        ...
        return
    # Execute tools and continue conversation
```

**Context:** The AgentService path has `max_turns=3` as a safety valve. But the direct Anthropic/Gemini/DeepSeek path uses an unbounded `while True` loop. If the model keeps requesting tool calls without converging (documented as BUG-016), the loop continues indefinitely. The `save_artifact` early-exit at line 1196 partially mitigates this for artifact generation, but `search_documents` has no such guard — a model could search in a loop forever.

There *is* a partial fix at line 1196 that breaks the loop after artifact creation, but it's tool-specific rather than a general safety mechanism.

**Impact:** Potential infinite loop consuming tokens and server resources. A single pathological conversation could exhaust the monthly budget.

**Fix:** Add a `max_iterations` counter (e.g., 5) to the while loop, similar to AgentService's `max_turns=3`.

---

### 1.5 Database Session Shared Across Async SSE Stream

**File:** `backend/app/routes/conversations.py:86-233`

**Issue:** The `db` session from `Depends(get_db)` is created at request time but used throughout the SSE generator's lifetime, which can span minutes.

**Context:** FastAPI's dependency injection creates and closes the db session around the request lifecycle. But SSE generators run asynchronously after the response starts. The session's commit/rollback lifecycle doesn't align with the generator's actual execution timeline. During a long streaming response (up to 10 minutes with the heartbeat timeout), the session remains open. If another request triggers a commit or the connection pool recycles, you get `StatementError` or stale reads. This is a known FastAPI footgun with SSE/WebSocket endpoints.

The issue is compounded because the `ai_service.stream_chat()` also receives this same `db` session and passes it into tool execution (`execute_tool` and MCP tools), where it's used for artifact saves and document searches mid-stream.

**Impact:** Intermittent database errors during long conversations. Connection pool exhaustion under load. The PDF export 500 error (BUG-021) may be a symptom of this.

**Fix:** Create a dedicated session inside the SSE generator with explicit lifecycle management. Use `async with AsyncSession() as db:` within `event_generator()`.

---

## 2. Assistant Flow Architecture Issues

### 2.1 Dual Conversation Systems (BA Assistant vs. Assistant)

**Files:**
- `backend/app/services/ai_service.py:757-777` (thread_type routing)
- `frontend/lib/providers/assistant_conversation_provider.dart`
- `frontend/lib/providers/conversation_provider.dart`
- `frontend/lib/screens/assistant/` vs `frontend/lib/screens/conversation/`

**Issue:** Two parallel conversation systems exist: `ba_assistant` (full-featured with artifacts/budget) and `assistant` (simplified, no artifacts). They share ~80% of the same code but are implemented as separate providers, screens, and widget sets.

**Context:** The assistant flow is declared as "the path forward," but it currently routes to `claude-code-cli` (hardcoded at `ai_service.py:767`), has no system prompt (`ai_service.py:931`), no tools (`ai_service.py:776`), and no artifact generation. It's essentially a raw Claude chat wrapper.

Meanwhile, the BA assistant flow has the full skill prompt, tools, artifact generation, and budget tracking. If the assistant flow is the future, it needs to absorb the BA assistant's capabilities selectively, not remain a stripped-down parallel implementation.

The duplication is visible on the frontend too: `AssistantConversationProvider` and `ConversationProvider` share identical streaming logic, error handling, and retry mechanics. The widget layer has `assistant_chat_input.dart` vs `chat_input.dart`, `assistant_message_bubble.dart` vs `message_bubble.dart` — near-identical files.

**Impact:** Feature drift between the two flows. Bug fixes applied to one but not the other. Double maintenance cost.

**Recommendation:** Unify into a single conversation system with a `thread_type` parameter that controls which features are active (skills, tools, artifacts, budget). One provider, one set of widgets, conditional rendering.

---

### 2.2 Skill Selection Has No Backend Effect

**Files:**
- `frontend/lib/providers/assistant_conversation_provider.dart:197-199`
- `backend/app/routes/conversations.py:86-233`

**Issue:** When a user selects a skill in the assistant flow, the frontend prepends `[Using skill: business-analyst]` as plain text in the message. The backend has no awareness of this — it doesn't parse the tag or change behavior.

```dart
// Frontend (assistant_conversation_provider.dart:198-199)
if (_selectedSkill != null) {
  messageContent = '[Using skill: ${_selectedSkill!.name}]\n\n$content';
}
```

**Context:** The skill selection UI (skill browser sheet, skill cards, caching) is a polished feature. But the backend treats `[Using skill: X]` as regular user text. The BA assistant skill prompt will see it as part of the user's message but won't change its behavior. For the assistant thread type, there's no system prompt at all, so the skill tag is just noise.

The skill endpoint (`/api/skills`) serves skills from the filesystem, and the skill browser presents them attractively. But the connection between "selecting a skill" and "changing AI behavior" is missing.

**Impact:** Users see a skill selection UI that suggests functional skill switching, but the backend behavior doesn't change. This is a UX promise without a backend delivery.

**Recommendation:** Either (a) have the backend parse the skill tag and load the corresponding system prompt, or (b) send `skill_id` as a structured field in `ChatRequest` and have the backend resolve it to a prompt.

---

### 2.3 Message History Flattened to Text for Agent SDK

**File:** `backend/app/services/agent_service.py:103-120`

**Issue:** The AgentService converts structured message history into flat text with role tags.

```python
prompt_parts.append(f"[{role.upper()}]: {content}")
full_prompt = "\n\n".join(prompt_parts)
```

**Context:** The Claude Agent SDK's `query()` function accepts a single `prompt` string, not a structured message array. So the service flattens the entire conversation history into `[USER]: ...\n\n[ASSISTANT]: ...` format. This loses the structured turn-taking that Claude's API is optimized for. The model sees the entire history as a single user turn, which:

1. Degrades Claude's ability to maintain conversational coherence
2. Makes it harder for Claude to distinguish its own previous responses from user content
3. Wastes tokens on role tags that the native API handles implicitly
4. May confuse the artifact deduplication logic (rule priority 2 in the system prompt) because the model can't distinguish actual previous tool calls from text descriptions of them

The direct Anthropic adapter path (`stream_chat` → `AnthropicAdapter`) preserves the structured format correctly.

**Impact:** Lower conversation quality in Agent SDK mode. Potential false-positive artifact regeneration due to confused history parsing.

**Recommendation:** If the Agent SDK doesn't support structured messages, evaluate whether the direct API path (which does support them) should be the primary path for BA assistant threads, with the Agent SDK reserved for tool-heavy flows.

---

### 2.4 Conversation Context Truncation Loses Important Context

**File:** `backend/app/services/conversation_service.py:179-217`

**Issue:** The truncation strategy keeps only the most recent messages and prepends a generic summary note.

```python
summary = {
    "role": "user",
    "content": f"[System note: {truncated_count} earlier messages in this conversation..."
}
```

**Context:** The truncation preserves recency but not relevance. In a BA discovery session, the early messages typically contain the most important information: business objectives, persona definitions, success criteria. The recent messages are often incremental clarifications. Truncating from the front removes the foundational context that the entire BRD generation depends on.

The generic summary note doesn't include *what* was discussed — it just says "some messages were removed." The `SummarizationService` exists but isn't used during truncation. The system prompt explicitly references "cumulative understanding" and "Building on what you mentioned earlier about..." — but truncation silently removes what was mentioned earlier.

**Impact:** Degraded BRD quality in long conversations. The AI loses foundational business context and generates incomplete artifacts.

**Recommendation:** Use `SummarizationService` to generate an actual summary of truncated messages, or implement a "keep first + keep recent" strategy that preserves the initial discovery context.

---

### 2.5 Token Estimation Uses Fixed 4-char Ratio

**File:** `backend/app/services/conversation_service.py:21-23`

**Issue:** Token estimation uses a hardcoded `1 token ≈ 4 characters` ratio.

```python
CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN
```

**Context:** The 4-char ratio is a rough average for English prose. But BA conversations contain:
- Structured markdown (tables, headers, lists) — higher token density
- Technical terms and proper nouns — higher token density
- BRD content with nested bullet points — variable density
- Non-English content — potentially very different ratios

A 20% estimation error on a 150K token budget means you could send ~180K tokens to the API (overrun) or truncate at ~120K (unnecessary context loss). The `EMERGENCY_TOKEN_LIMIT` at 180K in `ai_service.py:19` adds a ceiling, but the gap between 150K soft limit and 180K emergency limit is exactly the error margin of bad estimation.

The Anthropic SDK has a `count_tokens()` method that gives exact counts. `tiktoken` provides fast approximations for Claude models.

**Impact:** Unnecessary truncation or API overruns. Budget enforcement is approximate.

**Recommendation:** Use `anthropic.count_tokens()` or `tiktoken` for accurate estimates, at least for the budget boundary check.

---

## 3. Data Integrity & Persistence Issues

### 3.1 Optimistic UI Messages Never Reconciled

**File:** `frontend/lib/providers/assistant_conversation_provider.dart:208-213`

**Issue:** User messages are added to the local list with `temp-` prefixed IDs. These are never reconciled with the server-generated IDs.

```dart
final userMessage = Message(
  id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
  role: MessageRole.user,
  content: content,
  createdAt: DateTime.now(),
);
_messages.add(userMessage);
```

**Context:** The `sendMessage()` method sends the message content to the backend, which saves it with a UUID. But the frontend never learns this UUID — the `message_complete` event only contains the assistant's response. If the user navigates away and returns, the thread is reloaded from the server with real UUIDs, so the temp IDs are replaced. But during the current session, operations that need message IDs (like delete) will fail because the frontend has `temp-XXX` while the server has a UUID.

The assistant message also gets a temp ID (`temp-assistant-XXX` at line 238), making it un-deletable until a page refresh.

**Impact:** Message deletion doesn't work during the current session. Any future feature that references message IDs (editing, reactions, threading) will break.

**Fix:** Either (a) include the saved message ID in the `message_complete` event, or (b) reload the thread after each exchange to sync IDs.

---

### 3.2 Assistant Threads Cannot Search Documents

**Files:**
- `backend/app/services/ai_service.py:773-776`
- `backend/app/routes/conversations.py:151`

**Issue:** Assistant thread type has `self.tools = []` — no document search, no artifact generation. File uploads go through but the AI can't access them.

**Context:** The frontend's `AssistantChatInput` widget supports file attachments. Files are uploaded via `_documentService.uploadThreadDocument()` and stored in the database. But the assistant thread type gets zero tools, so the AI has no way to search or reference those documents. The user sees a file upload confirmation but the AI acts as if no files exist.

The message does get `[Attached files: report.pdf]` appended, so the AI knows the user mentioned files — it just can't access them.

**Impact:** Users upload files expecting the AI to read them. The AI acknowledges the file names but cannot search their content. Broken user expectation.

**Recommendation:** Enable `search_documents` tool for assistant threads, or at minimum, include the document content directly in the message context.

---

### 3.3 Fulfilled Pair Detection Uses Fragile Timestamp Correlation

**File:** `backend/app/services/conversation_service.py:41-81`

**Issue:** Fulfilled artifact pairs are detected by comparing timestamps within a 5-second window.

```python
ARTIFACT_CORRELATION_WINDOW = timedelta(seconds=5)
# ...
time_diff = (artifact.created_at - msg.created_at).total_seconds()
if 0 <= time_diff <= ARTIFACT_CORRELATION_WINDOW.total_seconds():
```

**Context:** The idea is to remove "generate a BRD" + "Here's your BRD..." message pairs from context (since the artifact already exists). But 5-second correlation is fragile:
- BRD generation via Claude can take 30-60 seconds, easily exceeding the window
- Network latency adds variable delay between message save and artifact save
- The assistant message `created_at` is set when the message is saved *after* streaming completes, not when streaming starts

If the window is too tight, fulfilled pairs aren't detected and full BRD content stays in context (wasting tokens). If it's too wide, unrelated messages get filtered out.

**Impact:** Either bloated context (BRD content not filtered) or lost messages (unrelated messages incorrectly filtered).

**Recommendation:** Use explicit linking — store the `message_id` that triggered artifact generation on the Artifact model, eliminating the need for timestamp heuristics.

---

### 3.4 Double Commit on Message Save

**File:** `backend/app/services/conversation_service.py:102-118`

**Issue:** `save_message()` commits twice — once for the message, once for the thread timestamp update.

```python
db.add(message)
await db.commit()           # Commit 1
await db.refresh(message)

# Update thread's updated_at timestamp
thread.updated_at = datetime.utcnow()
await db.commit()           # Commit 2
```

**Context:** Two separate commits for a logically atomic operation. If the process crashes between commit 1 and commit 2, the message exists but the thread's `updated_at` is stale. Under load, the double commit doubles the database write pressure per message.

**Impact:** Thread ordering becomes unreliable if the second commit fails. Unnecessary database write amplification.

**Fix:** Single commit: add the message and update the thread timestamp in one transaction.

---

## 4. Security Concerns

### 4.1 Error Messages Leak Internal Details

**Files:**
- `backend/app/routes/conversations.py:222-225`
- `backend/app/services/ai_service.py:255-260`
- `backend/app/services/agent_service.py:256-260`

**Issue:** Exception messages are passed directly to the client in error events.

```python
# conversations.py:224
yield {
    "event": "error",
    "data": json.dumps({"message": str(e)})
}

# agent_service.py:259
yield {
    "event": "error",
    "data": json.dumps({"message": f"AI service error: {str(e)}"})
}
```

**Context:** Python exception messages can contain file paths, database connection strings, API keys in headers, stack trace fragments, or internal service URLs. Sending `str(e)` to the client exposes internal architecture. An `anthropic.APIError` includes the model name, retry-after headers, and error codes that reveal provider details. A `sqlalchemy.exc.OperationalError` includes the full connection string.

**Impact:** Information disclosure. An attacker can map internal architecture from error messages.

**Fix:** Return generic error messages to clients. Log the full exception server-side with the correlation ID.

---

### 4.2 JWT Secret Key Has Weak Default

**File:** `backend/app/config.py`

```python
secret_key: str = "dev-secret-key-change-in-production"
```

**Context:** The default JWT signing key is a predictable string. If the `SECRET_KEY` environment variable isn't set in production, JWTs are signed with this known key. Anyone who reads the source code (it's likely on GitHub) can forge valid JWTs and impersonate any user.

The config does have a production validation check, but it's a warning log, not a hard failure:

```python
if settings.environment == "production" and settings.secret_key == "dev-secret-key-change-in-production":
    logger.warning("Using default secret key in production!")
```

**Impact:** Full authentication bypass if deployed without setting the environment variable.

**Fix:** Make the startup validation a hard failure in production: refuse to start if the secret key is the default value.

---

### 4.3 ContextVar Session Registry Is Not Cleaned Up

**File:** `backend/app/services/mcp_tools.py:32-33`

**Issue:** The `_session_registry` dict grows unboundedly.

```python
_session_registry: Dict[str, Any] = {}
```

**Context:** `register_db_session()` adds entries but `unregister_db_session()` is only called if the consuming code remembers to clean up. If an exception occurs before cleanup, the session stays registered forever. This is a memory leak that also keeps database connections alive beyond their intended lifecycle.

In the current code, the AgentService uses ContextVars (not the registry), so this is mostly dead code path. But the HTTP MCP transport placeholder suggests future use, and the pattern is already problematic.

**Impact:** Memory leak proportional to error frequency. Database connection pool exhaustion in long-running processes.

**Fix:** Use a `try/finally` pattern or context manager that guarantees cleanup.

---

## 5. Performance & Scalability

### 5.1 Full Message History Loaded on Every Chat Request

**File:** `backend/app/services/conversation_service.py:140-147`

**Issue:** `build_conversation_context()` loads ALL messages and ALL artifacts for the thread on every single chat request.

```python
stmt = (
    select(Message)
    .where(Message.thread_id == thread_id)
    .order_by(Message.created_at)
)
result = await db.execute(stmt)
messages = result.scalars().all()
```

**Context:** A long BA discovery session could have 200+ messages. Loading all of them, converting to dicts, estimating tokens, running fulfilled pair detection, then truncating — all on every request — is wasteful. The most recent N messages are likely sufficient for 99% of requests, with the full load only needed when approaching the context window.

**Impact:** Increasing latency per request as conversations grow. Database load scales linearly with conversation length.

**Recommendation:** Load messages in reverse chronological order with a LIMIT, expanding only if the token budget allows more context.

---

### 5.2 SSE Heartbeat Polls Every 1 Second

**File:** `backend/app/services/ai_service.py:63-64`

**Issue:** The heartbeat producer checks every 1 second, even when data is flowing.

```python
async def heartbeat_producer():
    while not done:
        await asyncio.sleep(1)  # Check every second
```

**Context:** When the model is actively streaming (which is most of the time), heartbeats aren't needed. But the heartbeat producer still wakes up every second, checks `silence_duration`, and goes back to sleep. At 100 concurrent streams, that's 100 unnecessary wakeups per second.

**Impact:** Minor CPU overhead per stream. Negligible at current scale but worth noting for growth.

**Recommendation:** Use `asyncio.Event` instead of polling. Set the event when data arrives, wait on it with timeout in the heartbeat producer.

---

### 5.3 System Prompt Is ~5000 Tokens and Sent on Every Request

**File:** `backend/app/services/ai_service.py:120-683`

**Issue:** The `SYSTEM_PROMPT` constant is a 564-line XML document (~5000 tokens) sent with every API call.

**Context:** This is the full BA assistant skill prompt. It's comprehensive and well-written, but it's sent on *every* message in a conversation. Claude charges for system prompt tokens as input tokens. In a 20-message conversation, that's 20 * 5000 = 100K tokens just for the system prompt. At $3/1M input tokens, a 20-message conversation costs $0.30 in system prompt alone.

Anthropic supports prompt caching, which would amortize this cost. The Anthropic SDK allows marking system prompts as cacheable, reducing input token charges by 90% on cache hits.

**Impact:** ~$0.30 unnecessary cost per 20-message conversation. Compounds to significant spend at scale.

**Recommendation:** Enable Anthropic prompt caching for the system prompt. It's a one-line change in the API call.

---

## 6. Frontend Assistant Flow Issues

### 6.1 Auto-Retry Can Create Duplicate Messages

**File:** `frontend/lib/providers/assistant_conversation_provider.dart:267-281`

**Issue:** The auto-retry logic removes the last message if it's a user message, then calls `sendMessage()` again — which adds a new optimistic user message. But the *first* attempt already sent the message to the backend and it was saved to the database.

```dart
// Auto-retry once on error after 2-second delay
if (!_hasAutoRetried) {
    _hasAutoRetried = true;
    await Future.delayed(const Duration(seconds: 2));
    if (!_isStreaming && _error != null) {
        _error = null;
        _hasPartialContent = false;
        _streamingText = '';
        // Remove the optimistic user message to avoid duplicates
        if (_messages.isNotEmpty && _messages.last.role == MessageRole.user) {
            _messages.removeLast();
        }
        await sendMessage(content); // Retry with original content
    }
}
```

**Context:** When the SSE stream errors after the backend successfully saved the user message (which happens before streaming starts — `conversations.py:128`), the retry will:
1. Remove the optimistic UI message (correct)
2. Call `sendMessage()` which sends the same content again
3. Backend saves a *second* copy of the same user message
4. Now there are two identical user messages in the database

The user sees one message in the UI (the retry's optimistic message), but the database has two. On page refresh, both appear.

**Impact:** Duplicate messages in the conversation history after auto-retry. Confusing user experience on page refresh.

**Fix:** Check if the message was already persisted before retrying. Include a `message_id` in the API response or use an idempotency key.

---

### 6.2 Streaming Text State Not Cleaned on Navigation

**File:** `frontend/lib/providers/assistant_conversation_provider.dart:332-348`

**Issue:** `clearConversation()` is called from `dispose()` in the chat screen, but only if the widget is actually disposed. If the user navigates to a different tab and back (with `StatefulShellRoute` preserving branch state), the old streaming state persists.

**Context:** GoRouter with `StatefulShellRoute` keeps widget state alive across tab switches. If the user:
1. Starts a conversation in Assistant tab
2. Switches to Projects tab while streaming
3. Switches back to Assistant tab

The streaming state (`_isStreaming`, `_streamingText`, `_thinkingStartTime`) is preserved, but the SSE connection was likely dropped during the tab switch. The user sees a frozen streaming indicator with no new data arriving.

**Impact:** Stuck streaming state after tab switching. User sees a perpetual "Thinking..." indicator.

**Fix:** Detect when the widget becomes visible again and verify the streaming state is still valid. Cancel stale streams on widget pause.

---

### 6.3 Attached Files Held in Memory

**File:** `frontend/lib/providers/assistant_conversation_provider.dart:18-30`

**Issue:** `AttachedFile` holds the full file bytes (`Uint8List`) in the provider's state.

```dart
class AttachedFile {
  final Uint8List? bytes;
  // ...
}
```

**Context:** Users can attach multiple files. Each file's bytes are held in memory from selection until message send. A 10MB PDF stays in the Dart heap until `_attachedFiles.clear()` is called. If the user attaches several files and then navigates away without sending, the memory isn't reclaimed until `clearConversation()`.

On mobile devices (the stated target platform), this can trigger low-memory warnings or OOM kills. Flutter's garbage collector handles heap pressure, but large byte arrays fragment memory.

**Impact:** Memory pressure on mobile devices with large file attachments.

**Recommendation:** Stream files to temporary storage on selection, pass file paths instead of bytes. Upload on demand.

---

### 6.4 No Message Pagination

**Files:**
- `frontend/lib/providers/assistant_conversation_provider.dart:140-141`
- `backend/app/routes/threads.py` (GET /threads/{thread_id})

**Issue:** The entire message history is loaded in one API call and held in memory.

```dart
_thread = await _threadService.getThread(threadId);
_messages = _thread?.messages ?? [];
```

**Context:** The backend's `GET /threads/{thread_id}` endpoint returns ALL messages ordered chronologically. For a long conversation (200+ messages with markdown, code blocks, BRD content), this is a large payload. The frontend holds the entire list in a `List<Message>` and renders it in a `ListView`.

Flutter's `ListView.builder` only builds visible widgets, so rendering performance is fine. But the initial load time and memory footprint grow linearly with conversation length.

**Impact:** Slow initial load for long conversations. High memory usage on mobile.

**Recommendation:** Implement cursor-based message pagination. Load the most recent N messages, fetch more on scroll-up.

---

## 7. Testing & Quality Gaps

### 7.1 No Integration Tests for the Streaming Flow

**Context:** The test suite has unit tests for individual services (`test_ai_service.py`, `test_conversation_service.py`, `test_sse_streaming.py`) but no integration test that exercises the full `POST /threads/{thread_id}/chat` → SSE stream → message save → token tracking flow.

The streaming endpoint is the most complex code path: it involves authentication, thread validation, budget checking, message persistence, AI streaming, heartbeat wrapping, tool execution, artifact saving, token tracking, and summary updates. A failure in any step produces different error behavior, but none of these failure modes are tested end-to-end.

**Impact:** Regressions in the critical path go undetected until manual testing.

**Recommendation:** Add a parametrized integration test that mocks the LLM adapter and validates the full SSE event sequence.

---

### 7.2 E2E Test Framework Defined But Unclear Execution Status

**Context:** The `e2e_tests/` directory has a well-structured Playwright framework with Page Object Model, test markers, and CI integration examples. But the `.planning/STATE.md` doesn't mention E2E test results, and the CI workflow (`flutter-ci.yml`) only runs backend pytest and frontend Flutter tests — no Playwright tests.

**Impact:** The E2E framework may be a scaffolding that's never actually run. Manual regression testing (REGRESSION_TESTS.md) suggests the E2E automation isn't filling the gap.

**Recommendation:** Wire up E2E tests in CI or document which tests are manually executed and at what frequency.

---

### 7.3 Frontend Test Coverage Unknown

**Context:** The `codecov.yml` sets a 50% frontend target (informational), but no frontend test files were found during exploration beyond what's auto-generated by Flutter. The provider logic (`AssistantConversationProvider`) has complex state transitions, retry logic, and error handling that would benefit from unit tests.

**Impact:** Frontend bugs in state management, retry logic, and error handling go undetected.

**Recommendation:** Add widget and unit tests for `AssistantConversationProvider`, specifically testing: streaming state transitions, auto-retry behavior, file attachment lifecycle, and error recovery.

---

## 8. Improvement Recommendations

### 8.1 Unify the Two Conversation Flows

**Priority:** High
**Effort:** Medium

The dual system (BA Assistant + Assistant) creates maintenance burden and feature drift. Merge into a single conversation system where `thread_type` controls:
- Which system prompt to use (BA skill prompt vs. none/custom)
- Which tools are available (document search, artifact save)
- Which UI features are shown (artifact panel, budget display, mode selector)
- Which skill is active (from skill browser or thread default)

This gives the assistant flow the full power of the BA flow while keeping the clean, simplified UI.

---

### 8.2 Implement Proper Skill Routing

**Priority:** High
**Effort:** Medium

Currently skill selection is a text tag. Implement:
1. Add `skill_id` field to `ChatRequest` schema
2. Backend resolves `skill_id` to a system prompt (from `/api/skills` registry)
3. Use the resolved prompt as the system prompt for that request
4. Store the active skill on the Thread model for continuity

This turns the skill browser from decorative to functional.

---

### 8.3 Enable Anthropic Prompt Caching

**Priority:** Medium
**Effort:** Low (1-2 line change)

Add `cache_control` to the system prompt in the Anthropic API call:

```python
system=[{
    "type": "text",
    "text": SYSTEM_PROMPT,
    "cache_control": {"type": "ephemeral"}
}]
```

This caches the 5000-token system prompt across requests, reducing input token costs by ~90% for repeated conversations.

---

### 8.4 Add Idempotency Keys to Chat Requests

**Priority:** Medium
**Effort:** Low

Add a client-generated `idempotency_key` (UUID) to `ChatRequest`. The backend checks if a message with this key already exists before saving. This prevents duplicate messages from auto-retry, network retries, or double-clicks.

---

### 8.5 Implement Proper Conversation Summarization on Truncation

**Priority:** Medium
**Effort:** Medium

When truncation is needed, use the existing `SummarizationService` to generate a structured summary of the removed messages. Include key decisions, persona definitions, objectives, and constraints — the foundational context that truncation currently destroys.

---

### 8.6 Add Structured Logging for Token Costs

**Priority:** Low
**Effort:** Low

The token tracking records exist but there's no dashboard or alerting. Add:
- Daily/weekly cost summary endpoint
- Per-thread cost visibility (show users how much each conversation costs)
- Alert when a single conversation exceeds a threshold (prevents runaway loops)

---

### 8.7 Consider WebSocket for Bidirectional Streaming

**Priority:** Low
**Effort:** High

SSE is sufficient for the current one-directional streaming. But future features like:
- Cancel generation mid-stream
- Real-time typing indicators
- Collaborative editing of artifacts

...would benefit from WebSocket's bidirectional capability. SSE doesn't support client-to-server messages without a separate HTTP endpoint.

Not urgent, but worth noting for the architecture roadmap.

---

## Summary Matrix

| # | Finding | Severity | Effort | Category |
|---|---------|----------|--------|----------|
| 1.1 | Token pricing model mismatch | High | Low | Bug |
| 1.2 | OAuth state in-memory | High | Medium | Infra |
| 1.3 | datetime.utcnow() deprecated | High | Low | Bug |
| 1.4 | Unbounded tool loop | Critical | Low | Bug |
| 1.5 | DB session shared across SSE | Critical | Medium | Architecture |
| 2.1 | Dual conversation systems | Medium | High | Architecture |
| 2.2 | Skill selection no backend effect | Medium | Medium | Feature gap |
| 2.3 | Message history flattened for Agent SDK | Medium | Low | Architecture |
| 2.4 | Truncation loses important context | Medium | Medium | Architecture |
| 2.5 | Token estimation inaccurate | Low | Low | Quality |
| 3.1 | Optimistic messages never reconciled | Medium | Low | Bug |
| 3.2 | Assistant threads can't search docs | High | Low | Feature gap |
| 3.3 | Fulfilled pair detection fragile | Low | Medium | Architecture |
| 3.4 | Double commit on message save | Low | Low | Bug |
| 4.1 | Error messages leak internals | Medium | Low | Security |
| 4.2 | JWT secret weak default | High | Low | Security |
| 4.3 | Session registry not cleaned | Low | Low | Bug |
| 5.1 | Full message history loaded every request | Medium | Medium | Performance |
| 5.2 | Heartbeat polls every 1s | Low | Low | Performance |
| 5.3 | System prompt 5K tokens every request | Medium | Low | Cost |
| 6.1 | Auto-retry creates duplicate messages | High | Low | Bug |
| 6.2 | Streaming state not cleaned on nav | Medium | Low | Bug |
| 6.3 | File bytes held in memory | Low | Medium | Performance |
| 6.4 | No message pagination | Medium | Medium | Performance |
| 7.1 | No integration tests for streaming | Medium | Medium | Testing |
| 7.2 | E2E framework unused in CI | Low | Low | Testing |
| 7.3 | Frontend test coverage unknown | Medium | Medium | Testing |

---

**Recommended Priority Order:**
1. Fix 1.4 (unbounded loop) + 1.5 (DB session) — production stability
2. Fix 1.1 (pricing) + 1.3 (datetime) + 6.1 (duplicate messages) — data integrity
3. Fix 4.1 (error leak) + 4.2 (JWT default) — security baseline
4. Implement 8.1 (unify flows) + 8.2 (skill routing) — assistant flow viability
5. Implement 8.3 (prompt caching) — immediate cost savings
6. Address remaining medium/low items incrementally
