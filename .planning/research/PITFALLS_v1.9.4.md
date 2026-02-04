# Domain Pitfalls: Artifact Deduplication & Silent Generation (v1.9.4)

**Domain:** LLM tool deduplication, conversation context manipulation, silent API requests, SSE filtering
**Researched:** 2026-02-04
**Confidence:** HIGH (based on direct codebase analysis + verified patterns)

---

## Critical Pitfalls

Mistakes that cause the fix to fail, introduce regressions, or create new bugs worse than the original.

---

### PITFALL-01: ARTIFACT_CREATED Marker Does Not Exist in Active Code Path

**Severity:** Critical
**Affects:** Layer 3 (BUG-019 History Filtering)
**Warning signs:** Unit tests pass but production detection never triggers

**What goes wrong:** BUG-019 proposes scanning assistant messages for the `ARTIFACT_CREATED:` marker string. However, this marker only exists in `agent_service.py` (dead code, lines 174, 335, 338). The **active** `ai_service.py` returns `"Artifact saved successfully: '{title}' (ID: {id})"` from `execute_tool()` (line 733). This string is sent back to the model as a tool result (line 843) within the tool loop, but it is NOT part of `accumulated_text`.

The `accumulated_text` variable only collects `text_delta` chunks (line 786), not tool results. Furthermore, `accumulated_text` is reset to `""` on every iteration of the while loop (line 774). The `message_complete` event only contains the LAST iteration's text. The route handler in `conversations.py` accumulates ALL `text_delta` content across iterations (line 171), but what gets saved as the assistant message (line 183) is the model's conversational text -- something like "I've created a Business Requirements Document..." -- NOT the tool result string containing `ARTIFACT_CREATED`.

**Consequences:** If BUG-019 is implemented as written, it will scan for `ARTIFACT_CREATED:` in saved assistant messages and NEVER find it. The history filtering will silently do nothing. The structural guarantee claimed by BUG-019 will not exist.

**Prevention:**
1. Before implementing BUG-019, verify what string actually appears in saved assistant messages after artifact generation. Test with a real artifact generation and inspect the database.
2. Use a detection strategy based on what IS in the saved text. Options:
   - **(A)** Scan for `"Artifact saved successfully"` in assistant messages (this IS the text the model sees as tool result, and the model typically echoes/paraphrases it -- but this is fragile and depends on model behavior)
   - **(B)** Query the artifacts table for that thread -- check if any artifact was created between consecutive user messages (database-level detection, most reliable but adds a DB query)
   - **(C, Recommended)** Add an explicit marker when saving the assistant message in `conversations.py` -- when an `artifact_created` event was emitted during streaming, append `\n<!-- ARTIFACT_GENERATED -->` to the saved text. This creates a reliable marker that BUG-019 can detect.
3. Option C is recommended: it creates a reliable marker in the saved message, does not depend on model behavior, and is invisible to users (HTML comment format won't render in Markdown).

**Detection:** Write a test that generates an artifact, reads the saved assistant message from the DB, and asserts the expected marker is present. Run this BEFORE implementing the history filtering.

---

### PITFALL-02: Token Tracking Undercounts in Multi-Iteration Tool Loop

**Severity:** Critical
**Affects:** Layer 4 (THREAD-011 Silent Generation), pre-existing in all flows
**Warning signs:** Budget tracking shows lower costs than actual API usage

**What goes wrong:** The tool loop in `ai_service.py` resets `usage_data` on each iteration (line 776: `usage_data = None`). Only the LAST iteration's usage data makes it to the `message_complete` event (line 811). For a typical artifact generation flow (text + tool_use + tool result + final text), there are at least 2 API calls, but only the last one's token counts are reported.

This is a pre-existing bug, but THREAD-011 makes it worse because:
1. Silent mode suppresses `text_delta` events, but the model may still generate text (see PITFALL-05). This text consumes output tokens that are charged but never displayed.
2. If the first API call uses significant input tokens (the full conversation context), those tokens are undercounted since only the second call's input tokens are reported.
3. With more users using the artifact generation button (which THREAD-011 makes more convenient), the token undercounting becomes more frequent.

**Consequences:** Users appear to stay within budget but actual API costs are higher. Over time, the discrepancy compounds. Budget enforcement becomes unreliable.

**Prevention:**
1. Accumulate usage across ALL loop iterations. Instead of:
   ```python
   usage_data = chunk.usage  # overwrites previous iteration
   ```
   Use:
   ```python
   if usage_data is None:
       usage_data = chunk.usage
   else:
       usage_data = {
           "input_tokens": usage_data["input_tokens"] + chunk.usage["input_tokens"],
           "output_tokens": usage_data["output_tokens"] + chunk.usage["output_tokens"],
       }
   ```
2. This is a pre-existing issue that should be fixed as part of v1.9.4 since the silent generation path exercises the tool loop more frequently.
3. For silent mode specifically, ensure token tracking still runs even when messages are not saved.

**Detection:** Add logging that prints per-iteration usage counts. Compare the sum against the final `message_complete` usage. If they differ, the accumulation bug is confirmed.

---

### PITFALL-03: Prompt Deduplication Rule Blocks Legitimate Re-generation Requests

**Severity:** Critical
**Affects:** Layer 1 (BUG-017 Prompt Engineering) + Layer 2 (BUG-018 Tool Description)
**Warning signs:** User says "regenerate the BRD with more detail" and model refuses or only explains

**What goes wrong:** The proposed deduplication rule says "ONLY act on the MOST RECENT user message" and the tool description says "Call this tool ONCE per user request... Do not call again unless the user sends a NEW message explicitly requesting another artifact or re-generation."

Claude 4.x models are literal instruction followers (confirmed by [Anthropic's documentation on Claude 4.x behavior changes](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices)). If a user sends "regenerate the BRD but include section 7" in a thread where a BRD already exists, the model may:
1. See the existing `save_artifact` result in history
2. Interpret the previous request as the one being referenced
3. Conclude that the artifact was "already generated" per the deduplication rule
4. Refuse to call the tool, or explain what it already generated

The BUG-017 rule says "If you see save_artifact tool results in history, those requests are COMPLETE." This is correct for the ORIGINAL request, but the model may over-apply it to new re-generation requests because the rule does not clearly distinguish "a prior request being echoed in history" from "a new explicit request to revise."

**Consequences:** Users cannot iterate on artifacts. The deduplication fix breaks the core workflow of refining documents through conversation.

**Prevention:**
1. The deduplication rule MUST include an explicit escape hatch. Proposed revision:
   ```xml
   <rule priority="2">ARTIFACT DEDUPLICATION - When generating artifacts, ONLY act on the
   MOST RECENT user message. Prior artifact requests visible in conversation history have
   already been fulfilled (you can confirm this by the save_artifact tool results that follow
   them). Do not re-generate artifacts for those prior requests. HOWEVER, if the user
   explicitly asks to regenerate, revise, update, or create a new version, that IS a new
   request - honor it.</rule>
   ```
2. The tool description replacement should add: "A user asking to 'regenerate', 'revise', 'update', or 'redo' IS a new request and should be honored."
3. Test with these exact prompts after implementation:
   - "Generate user stories" (first time) -- should generate 1 artifact
   - "Generate user stories" (second time, no changes) -- should generate exactly 1 new artifact, not 2
   - "Regenerate the user stories with more detail" -- MUST generate, not refuse
   - "Create acceptance criteria" (different type) -- should generate
   - "Update the BRD to include section 7" -- MUST generate

**Detection:** Manual testing with the 5 prompts above is the minimum verification. If prompts 3 or 5 fail, the escape hatch is missing or insufficient.

---

### PITFALL-04: History Prefix Annotation Confuses Model or Leaks to User

**Severity:** Critical
**Affects:** Layer 3 (BUG-019 History Filtering)
**Warning signs:** Model refers to "[ALREADY PROCESSED]" text in its responses or behaves erratically

**What goes wrong:** The `[ALREADY PROCESSED - artifact was generated]` prefix is prepended to user messages in `build_conversation_context()`. This prefix becomes part of the prompt the model sees. Several risks:

1. **Model echoes the prefix.** Claude may reference "ALREADY PROCESSED" in its responses. Example: "I see that request was already processed. Would you like to..." This exposes internal mechanics to the user.
2. **Model misinterprets scope.** LLMs process structured annotations semantically, not syntactically ([per context injection research](https://arxiv.org/html/2405.20234v1)). The model might interpret `[ALREADY PROCESSED]` as a general behavioral instruction rather than metadata about that specific message, potentially affecting its response to subsequent non-artifact messages.
3. **Model breaks persona.** The system prompt establishes Claude as a "senior business analyst consultant." Seeing backend annotation markers in user messages breaks the fourth wall. The model may acknowledge being in a software system rather than maintaining its BA persona.
4. **Interacts with truncation.** If the conversation is truncated (line 114-115 of conversation_service.py), the truncation works backwards from most recent. Prefixed messages near the truncation boundary may end up as the oldest visible messages, making the prefix the first thing the model sees -- giving it disproportionate weight.

**Consequences:** Unpredictable model behavior. Internal markers visible in user-facing responses. Potential over-application of "skip" behavior.

**Prevention:**
1. Use a prefix format that instructs the model not to echo it. Better: add a system prompt instruction like: "Some user messages may be prefixed with `[FULFILLED]`. This means the request in that message was already completed in a prior turn. Do not generate artifacts for fulfilled messages. Never mention this prefix to the user."
2. Use a more neutral prefix. Instead of `[ALREADY PROCESSED - artifact was generated]`, use `[FULFILLED]` -- shorter, less likely to be echoed, less descriptive for the model to riff on.
3. Alternatively, use HTML comment syntax `<!-- fulfilled -->` which models are trained to recognize as non-content.
4. Test by generating an artifact, then asking 5 follow-up conversational questions. Inspect all 5 responses for any mention of the prefix text, "fulfilled", "already processed", or unusual behavior changes.

**Detection:** After implementing BUG-019, send 5 follow-up messages after artifact generation. Search all responses for any reference to the annotation. If found in even 1 of 5, the prefix is leaking.

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or subtle bugs that are not immediately catastrophic.

---

### PITFALL-05: Model Generates Text Despite Silent Instruction

**Severity:** Moderate
**Affects:** Layer 4 (THREAD-011 Silent Generation)
**Warning signs:** Backend logs show non-empty `accumulated_text` for silent requests; slight extra latency

**What goes wrong:** THREAD-011 appends "IMPORTANT: Generate the artifact silently. Do not include any conversational text." to the context and suppresses `text_delta` events at the route level. However:

1. Claude may still generate text BEFORE calling the tool (e.g., "Let me generate that for you...") followed by `tool_use`. This text gets suppressed by the SSE filter but still consumes output tokens and adds latency.
2. The route handler in `conversations.py` accumulates ALL `text_delta` content (line 171), including suppressed ones. If `accumulated_text` is non-empty when streaming ends, `save_message()` is called (line 182-183). For silent mode, this should NOT happen, but the current THREAD-011 proposal only suppresses SSE events -- it does not prevent message saving.

**Consequences:** Wasted tokens (~50-200 per request), ghost assistant messages in database, slight UX delay.

**Prevention:**
1. SSE suppression is necessary but NOT sufficient. The `event_generator()` in `conversations.py` must ALSO skip `save_message()` when `artifact_generation: true`, regardless of whether `accumulated_text` is non-empty.
2. Use a more specific silent instruction: "Respond ONLY with the save_artifact tool call. Do not generate any text content blocks." This tells Claude at the API structural level to not produce text blocks.
3. Consider server-side enforcement: in the `event_generator`, when `artifact_generation: true`, do not accumulate `text_delta` content at all -- set a flag that skips line 171.

**Detection:** Enable logging for `accumulated_text` value at the time of `message_complete`. If non-empty for silent requests, the model is generating text despite the instruction.

---

### PITFALL-06: SSE text_delta Suppression Breaks Frontend Streaming State Machine

**Severity:** Moderate
**Affects:** Layer 4 (THREAD-011 Silent Generation)
**Warning signs:** Frontend stuck in loading/streaming state, artifact card never appears

**What goes wrong:** The frontend `ConversationProvider.sendMessage()` manages streaming state through a specific event sequence:
1. `_isStreaming = true` when sending begins (line 151)
2. `TextDeltaEvent` appends to `_streamingText` (line 159)
3. `MessageCompleteEvent` sets `_isStreaming = false` and adds assistant message (lines 164-180)
4. `ArtifactCreatedEvent` adds to artifact list (lines 184-191)

If THREAD-011 reuses `sendMessage()` with server-side `text_delta` suppression:
- `_streamingText` stays empty (no text deltas arrive)
- `_isStreaming` is true throughout
- If `message_complete` arrives, line 169: `content: _streamingText.isNotEmpty ? _streamingText : event.content` -- this creates an assistant message with empty or minimal content
- An empty-content assistant message gets added to `_messages` (line 173), appearing as a blank bubble in the UI

The deeper problem: `sendMessage()` always adds an assistant message to `_messages` on `MessageCompleteEvent`. For silent generation, NO assistant message should be added.

**Consequences:** Frontend shows blank assistant message bubble, or gets stuck in streaming state.

**Prevention:**
1. The `generateArtifact()` method MUST be a separate code path from `sendMessage()`. It needs its own event loop that:
   - Sets `_isGeneratingArtifact = true` (a new state variable, not `_isStreaming`)
   - Ignores `TextDeltaEvent` entirely
   - Listens for `ArtifactCreatedEvent` to add artifact to list
   - Listens for `MessageCompleteEvent` as the stream-end signal
   - Sets `_isGeneratingArtifact = false` on `MessageCompleteEvent` or `ErrorEvent`
   - Does NOT add any message to `_messages` list
2. The `message_complete` event MUST still be sent from the backend for silent requests. It serves as the stream-end signal. Without it, the frontend has no way to know the stream is done.
3. The `artifact_type_picker` handler (conversation_screen.dart line 214) currently calls `provider.sendMessage(prompt)`. This must change to `provider.generateArtifact(prompt)`.
4. Add a frontend timeout: if `_isGeneratingArtifact` is true for more than 120 seconds, reset state and show error.

**Detection:** Generate an artifact via button click. If a blank message bubble appears, or the loading animation never stops, this pitfall has occurred.

---

### PITFALL-07: Silent Mode Creates Orphaned Artifacts on Mid-Stream Errors

**Severity:** Moderate
**Affects:** Layer 4 (THREAD-011 Silent Generation)
**Warning signs:** Artifacts appear in database with no corresponding conversation context

**What goes wrong:** In silent mode, user messages are not saved to the database. But the `save_artifact` tool executes DURING the stream, committing the artifact immediately via `db.commit()` at `execute_tool()` line 723. If the stream subsequently errors (network issue, timeout, client disconnect):

1. The artifact exists in the database (committed at line 723)
2. No user message exists explaining why it was generated
3. No assistant message exists acknowledging it
4. The `artifact_created` SSE event may not have reached the frontend
5. The frontend never adds the artifact to its local list

Result: An artifact exists server-side but is invisible to the user. On page reload, it appears without context.

In normal (non-silent) mode, at least the user message is saved (line 126 of conversations.py, before streaming begins), providing some context.

**Consequences:** Ghost artifacts with no conversation trail. User confusion on reload.

**Prevention:**
1. Accept this as a known edge case. Orphaned artifacts are better than lost artifacts.
2. The frontend already re-fetches thread details on `loadThread()`, which provides eventual consistency.
3. Do NOT try to make artifact creation transactional with message completion -- the tool executes mid-stream, and rolling back would require compensating transactions that add dangerous complexity.
4. Consider adding a lightweight context marker: when `artifact_generation: true`, save a minimal system note (not visible in chat) linking the artifact to the thread for traceability.

**Detection:** Disconnect the client mid-generation (close browser tab). Check database for artifacts without corresponding messages.

---

### PITFALL-08: Summarization Service Fires Unnecessarily on Silent Requests

**Severity:** Moderate
**Affects:** Layer 4 (THREAD-011 Silent Generation)
**Warning signs:** Extra API cost and latency after artifact button clicks

**What goes wrong:** After streaming completes, the route handler calls `maybe_update_summary()` (line 197 of conversations.py). This checks message count and generates a new thread title every 5 messages (SUMMARY_INTERVAL = 5).

In silent mode, no messages are saved. But `maybe_update_summary()` still runs. If the message count happens to be at a summary interval from PRIOR messages, summarization fires, consuming tokens and adding latency for no reason -- the title won't change since no new content was added.

**Consequences:** Wasted API calls (Anthropic API call for summarization costs tokens). Added latency (1-3 seconds) after what should be a fast silent operation.

**Prevention:**
1. Skip `maybe_update_summary()` when `artifact_generation: true`. This is a one-line conditional.
2. THREAD-011 already notes this in its edge cases: "Thread summary update skipped for silent requests." Ensure this is in the implementation checklist, not just the notes.

**Detection:** Log `maybe_update_summary()` calls. Check if any fire during silent artifact generation.

---

### PITFALL-09: Accumulated Text Discrepancy Between ai_service and Route Handler

**Severity:** Moderate
**Affects:** All layers, pre-existing bug
**Warning signs:** Saved assistant messages contain only the last iteration's text, not the full response

**What goes wrong:** There is a subtle but important discrepancy in text accumulation:

- `ai_service.py` line 774: `accumulated_text = ""` resets on EVERY loop iteration
- `ai_service.py` line 810: `message_complete` sends only the last iteration's `accumulated_text`
- `conversations.py` line 171: Route handler accumulates ALL `text_delta` content
- `conversations.py` line 177: `accumulated_text = data.get("content", accumulated_text)` -- this OVERWRITES the route's accumulated text with the `message_complete` content

Example flow for artifact generation:
1. **Iteration 1:** Model says "Let me generate that..." + calls save_artifact. Text is streamed as `text_delta`. Then `accumulated_text` resets in ai_service.
2. **Iteration 2:** Model says "I've created the BRD...". No tool calls. `message_complete` fires with content = "I've created the BRD..."
3. **Route handler:** Had accumulated "Let me generate that...\n\nI've created the BRD..." via text_delta. But line 177 overwrites this with just "I've created the BRD..."
4. **Saved message:** Only contains "I've created the BRD..." -- missing the first iteration text.

**Consequences:**
- Incomplete assistant messages in history (usually minor, since pre-tool text is short)
- Critically important for BUG-019: if the detection strategy relies on saved assistant message content, the content may not contain expected text from earlier iterations
- The frontend DOES show the full text (it accumulates `text_delta` independently at line 159 of conversation_provider.dart), creating a discrepancy between what the user saw and what is saved

**Prevention:**
1. For v1.9.4: Be aware of this when designing the detection strategy for BUG-019. Do NOT rely on the saved assistant message containing text from ALL loop iterations.
2. Consider fixing: either remove the overwrite at line 177 (let the route handler's accumulation stand), or fix `message_complete` to include all text across iterations. The simpler fix is removing the overwrite, since the route handler's accumulation is already correct.

**Detection:** Generate an artifact and immediately compare the chat display (frontend) with the saved message in the database. If they differ, this discrepancy is confirmed.

---

### PITFALL-10: Model Provider Switching Invalidates Prompt-Based Deduplication

**Severity:** Moderate
**Affects:** All layers, future concern
**Warning signs:** Deduplication works for Claude but fails for Gemini/DeepSeek

**What goes wrong:** The architecture supports multiple LLM providers via the adapter pattern. The deduplication fix assumes Claude-specific behavior:

1. **BUG-017 prompt rule:** Written using XML tags (`<critical_rules>`). Claude is trained on XML-structured prompts. Other models may not parse them as effectively.
2. **BUG-018 tool description:** Claude 4.x follows tool descriptions literally. Other models may not respect "Call this tool ONCE per user request."
3. **BUG-019 history filtering:** The `[ALREADY PROCESSED]` prefix is prompt engineering that works with Claude's instruction-following. Other models may interpret it differently or ignore it.

**Consequences:** If other providers are activated, the multiplication bug returns.

**Prevention:**
1. For v1.9.4, acceptable since only Claude is actively used. Document the assumption.
2. Layer 3 (BUG-019, structural history filtering) is the most provider-agnostic layer since it modifies the context before ANY model sees it. Strengthen this layer as the primary guarantee.
3. When adding other providers, validate deduplication behavior as part of provider integration tests.
4. Consider making detection database-backed (query artifacts table) rather than text-marker-based for full provider independence.

**Detection:** When Gemini or DeepSeek are activated, run the artifact deduplication smoke test.

---

## Low Pitfalls

Mistakes that cause minor annoyance but are straightforward to fix.

---

### PITFALL-11: Typed Artifact Requests Bypass Silent Mode

**Severity:** Low
**Affects:** Layer 4 (THREAD-011 Silent Generation)
**Warning signs:** Silent mode only works for button clicks, typed requests still clutter chat

**What goes wrong:** THREAD-011's silent generation is triggered by `artifact_generation: true` in the request body. This flag is set by the frontend when the artifact type picker button is used. But users can also TYPE "generate BRD from this conversation." Typed requests go through `sendMessage()`, not `generateArtifact()`, so they use the normal flow with full message persistence.

This is INTENTIONAL design -- typed requests should create visible messages since the user explicitly typed something. But it means:
1. Typed artifact requests still enter conversation history
2. The accumulation bug can still occur for typed requests
3. Layers 1-3 (BUG-017, BUG-018, BUG-019) are the ONLY protection for typed requests
4. Layer 4 (THREAD-011) does NOT protect typed requests

**Consequences:** If layers 1-3 fail, typed artifact requests can still accumulate.

**Prevention:**
1. This is the correct design. Silent mode is for button clicks only.
2. Ensure layers 1-3 are robust enough to handle typed requests independently.
3. The layered defense strategy means even if one layer has a gap, the others compensate.

**Detection:** Type "Generate user stories from this conversation" twice in the same thread. Verify exactly 1 artifact per request (layers 1-3 handle this).

---

### PITFALL-12: Custom Artifact Prompts Bypass Pattern-Based Detection

**Severity:** Low
**Affects:** Layer 3 (BUG-019 History Filtering), only if implemented incorrectly
**Warning signs:** Custom prompts accumulate while preset ones do not

**What goes wrong:** If BUG-019's detection strategy is changed from response-based (scan assistant message for markers) to input-based (scan user message for trigger phrases), custom prompts like "Write a comparison matrix of vendors" will bypass detection. No trigger phrase list can cover all possible artifact request phrasings.

**Consequences:** Custom artifact prompts accumulate while preset ones don't.

**Prevention:**
1. BUG-019 correctly proposes response-based detection (scan the assistant's response, not the user's request). This detects WHAT HAPPENED, not what was requested.
2. Never implement trigger-phrase matching for artifact detection. It is inherently incomplete.
3. The recommended approach (PITFALL-01 option C: explicit marker in saved message) works for all prompt types because the marker is added based on whether `save_artifact` was actually called, not based on what the user asked.

**Detection:** Generate a custom artifact via the picker. Then generate a preset artifact. Both should be correctly marked as fulfilled in history.

---

### PITFALL-13: Testing Deduplication Without Real LLM Calls Gives False Confidence

**Severity:** Low
**Affects:** All layers (testing strategy)
**Warning signs:** All unit tests pass but production behavior differs

**What goes wrong:** Prompt engineering changes (BUG-017, BUG-018) cannot be verified with unit tests -- they require actual LLM responses. Structural changes (BUG-019, THREAD-011) can be unit tested. Teams sometimes assume passing unit tests means the fix works, but:

1. Unit tests for BUG-019 in the user story use mock data: `Message(role="assistant", content="ARTIFACT_CREATED:{...}| Done!")`. This content does not match what the active code produces (see PITFALL-01). Tests pass against incorrect mock data.
2. Prompt engineering changes are inherently non-deterministic -- the same prompt may produce different behavior across runs or model versions.

**Consequences:** False confidence from passing tests. Fix may not work in production.

**Prevention:**
1. Layer the testing strategy:
   - **Unit tests** (no API calls): Test structural code paths -- history filtering logic, SSE event suppression, message save/skip conditionals, token accumulation
   - **Integration test with cassette** (one-time API call): Record one real artifact generation interaction using `pytest-recording` / `vcrpy`. Replay for regression testing. This captures actual model response format.
   - **Manual smoke test** (real API calls): The 5-prompt test from PITFALL-03. Run manually at least once per implementation and after model version changes.
2. Update BUG-019 unit test mock data to match actual saved message content (see PITFALL-01).
3. Document which tests are deterministic vs non-deterministic.

**Detection:** Compare unit test mock data against actual database content from a real artifact generation. If they don't match, tests are validating the wrong assumptions.

---

### PITFALL-14: Thread.model_provider Null for Legacy Threads

**Severity:** Low
**Affects:** All layers, edge case
**Warning signs:** N/A (handled by defaults)

**What goes wrong:** Older threads may have `model_provider = None`. The code handles this: `provider = thread.model_provider or "anthropic"` (line 138 of conversations.py). For the `ChatRequest` model extension adding `artifact_generation: bool = Field(default=False)`, older frontend clients that haven't updated will send requests without this field. The `Field(default=False)` default handles this.

**Consequences:** None. Defaults are correct.

**Prevention:** Already handled. No action needed.

**Detection:** N/A.

---

## Phase-Specific Warnings Summary

| Phase/Layer | Pitfall IDs | Critical Action Before Implementation |
|-------------|-------------|---------------------------------------|
| **Layer 1:** Prompt Engineering (BUG-017) | PITFALL-03, PITFALL-10 | Add re-generation escape hatch to rule text |
| **Layer 2:** Tool Description (BUG-018) | PITFALL-03 | Add re-generation allowance to tool description |
| **Layer 3:** History Filtering (BUG-019) | PITFALL-01, PITFALL-04, PITFALL-09, PITFALL-12 | Resolve marker detection strategy BEFORE coding. Fix mock test data. |
| **Layer 4:** Silent Generation (THREAD-011) | PITFALL-02, PITFALL-05, PITFALL-06, PITFALL-07, PITFALL-08, PITFALL-11 | Build separate `generateArtifact()` frontend path. Fix token accumulation. Skip summarization. |
| **Testing** (cross-cutting) | PITFALL-13 | Layer: unit + cassette + manual |
| **Pre-existing** (fix opportunistically) | PITFALL-02, PITFALL-09 | Token accumulation bug and text discrepancy affect all flows |

---

## Implementation Order Recommendation

The order from the user stories (BUG-017 -> BUG-018 -> BUG-019 -> THREAD-011) is correct, with these prerequisites:

**Before BUG-017:** Draft the rule text including PITFALL-03 escape hatch (re-generation support).

**Before BUG-019:** Resolve PITFALL-01 by determining the correct detection strategy:
- **(Recommended)** Add `<!-- ARTIFACT_GENERATED -->` marker to saved assistant messages when `artifact_created` event fires during streaming (modify `event_generator` in conversations.py)
- Then BUG-019 scans for this marker instead of `ARTIFACT_CREATED:`

**Before THREAD-011:** Fix PITFALL-02 (token accumulation across loop iterations) since this is a pre-existing bug that THREAD-011 will exercise more frequently.

**Critical blockers by layer:**

| Layer | Must Resolve Before Coding |
|-------|---------------------------|
| BUG-017 | PITFALL-03 (escape hatch) |
| BUG-018 | PITFALL-03 (escape hatch) |
| BUG-019 | PITFALL-01 (marker detection), PITFALL-04 (prefix format) |
| THREAD-011 | PITFALL-02 (token tracking), PITFALL-06 (frontend state), PITFALL-08 (summarization skip) |

---

## Sources

### Codebase Analysis (HIGH confidence)
- `backend/app/services/ai_service.py` -- tool loop (773-882), text accumulation (774, 786), tool result strings (733), tool description (649-683), system prompt (114-617)
- `backend/app/services/conversation_service.py` -- message persistence (38-74), context building (77-117), truncation (120-158)
- `backend/app/routes/conversations.py` -- SSE event handling (141-203), message saving (183), token tracking (186-194), summarization call (197)
- `backend/app/services/llm/anthropic_adapter.py` -- per-call usage reporting (111-118)
- `backend/app/services/token_tracking.py` -- cost calculation, budget enforcement
- `backend/app/services/summarization_service.py` -- auto-summarization trigger (116), SUMMARY_INTERVAL=5
- `backend/app/services/agent_service.py` -- dead code containing ARTIFACT_CREATED marker (174, 335, 338)
- `frontend/lib/providers/conversation_provider.dart` -- streaming state machine (135-209), artifact handling (184-191)
- `frontend/lib/services/ai_service.dart` -- SSE event parsing (134-175)
- `frontend/lib/screens/conversation/conversation_screen.dart` -- artifact picker handler (198-216)

### External Research (MEDIUM confidence)
- [Claude 4.x Prompt Engineering Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices) -- literal instruction following in Claude 4.x
- [How to implement tool use - Claude Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) -- tool loop patterns, max_steps, tool_choice
- [Context Injection Attacks on LLMs](https://arxiv.org/html/2405.20234v1) -- semantic vs syntactic parsing of structured annotations
- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) -- prefix injection risks
- [SSE - MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) -- event filtering, named events
- [LLM Testing Strategies 2026](https://www.confident-ai.com/blog/llm-testing-in-2024-top-methods-and-strategies) -- mock approaches, cassette-based testing
- [Mocking OpenAI for Unit Testing](https://laszlo.substack.com/p/mocking-openai-unit-testing-in-the) -- HTTP-layer mocking patterns
