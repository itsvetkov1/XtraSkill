# Domain Pitfalls: BA Assistant v1.9.2 Resilience & AI Transparency

**Domain:** AI Chat Application with SSE Streaming, Token Budgets, and Document RAG
**Researched:** 2026-02-02
**Tech Stack:** Flutter + FastAPI + SSE + Multi-LLM Adapters
**Milestone:** v1.9.2 Resilience & AI Transparency

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or major user experience failures.

---

### PITFALL-01: Network Drop Discards Partial Streaming Content

**Severity:** Critical
**Affects:** Network interruption handling during SSE streaming (THREAD-004)

**What goes wrong:**
When network connection drops during SSE streaming, the partial AI response accumulated in `_streamingText` is discarded. The user loses potentially valuable content mid-response.

**Why it happens:**
The current `ConversationProvider.sendMessage()` catch block clears `_streamingText` on any exception:
```dart
} catch (e) {
  _error = e.toString();
  _isStreaming = false;
  _streamingText = '';  // <-- Content lost here
  _statusMessage = null;
  notifyListeners();
}
```

**Consequences:**
- User loses partial AI response that may have contained useful information
- No way to copy or view what was generated before disconnect
- User frustration when lengthy responses are lost

**Prevention:**
1. **Preserve partial content on error:** Do NOT clear `_streamingText` in the catch block
2. **Add error state that retains content:** Create an `_errorWithPartialContent` state
3. **Allow content interaction during error:** User should be able to select/copy partial text
4. **Offer "Resume" vs "Retry":** Resume attempts to continue from Last-Event-ID; Retry starts fresh

**Detection (Warning Signs):**
- Users reporting lost responses during Wi-Fi switching
- Mobile users on spotty networks losing content
- Test case: Disable network mid-stream and check if content is preserved

**Phase to Address:** Phase 1 (Network interruption handling)

**Sources:**
- [EventFlux Package - Auto-reconnect](https://pub.dev/packages/eventflux)
- [Making a Connection: Handling Network Issues in Flutter](https://medium.com/@mksl/making-a-connection-handling-network-issues-in-flutter-217e7cfd30e9)

---

### PITFALL-02: Flutter Web SSE Buffering Causes "Bulk Delivery"

**Severity:** Critical
**Affects:** SSE streaming on Flutter Web platform

**What goes wrong:**
On Flutter Web, many HTTP libraries buffer SSE responses and deliver events in bulk when the server closes the connection, rather than streaming in real-time. Users see nothing until the full response arrives.

**Why it happens:**
Higher-level HTTP libraries in Flutter Web (like `http` package) don't support true streaming. They wait for response completion before exposing data.

**Consequences:**
- Web users see no typing indicator, then entire response appears at once
- Defeats the purpose of streaming (no incremental feedback)
- UX is significantly worse on web than mobile

**Prevention:**
1. **Use platform-specific implementations:** Conditional imports for web vs mobile
2. **Use XMLHttpRequest directly on web:** The browser's native XHR supports streaming
3. **Consider EventFlux or flutter_client_sse:** Packages designed for cross-platform SSE
4. **Test on all platforms:** Don't assume mobile behavior matches web

**Detection (Warning Signs):**
- Web testing shows "Thinking..." for extended time then instant full response
- No heartbeat detection on web platform
- Mobile works fine but web doesn't

**Phase to Address:** Phase 1 (Network interruption handling) - verify current web behavior

**Sources:**
- [Actual Real-Time SSE in Flutter Web](https://medium.com/@thorsten_79724/actual-real-time-server-sent-events-sse-in-flutter-web-3e22f3d65445)
- [Flutter SSE Web Issue #43343](https://github.com/flutter/flutter/issues/43343)

---

### PITFALL-03: Server-Side Disconnect Detection Failure in FastAPI

**Severity:** Critical
**Affects:** Network interruption handling, resource cleanup

**What goes wrong:**
FastAPI's StreamingResponse doesn't automatically detect client disconnection. The server continues generating responses even after the client has disconnected, wasting API tokens and compute resources.

**Why it happens:**
Unlike WebSocket, SSE connections in FastAPI don't get automatic disconnect events. The stream generator keeps running until explicitly stopped or an error occurs.

**Consequences:**
- LLM API tokens wasted on responses no one will receive
- Server resources tied up for disconnected clients
- Potential for runaway costs if many users disconnect mid-stream

**Prevention:**
1. **Use sse-starlette library:** Provides automatic disconnect detection
2. **Check `request.is_disconnected()` periodically:**
   ```python
   async def event_generator():
       while True:
           if await request.is_disconnected():
               break
           yield event
   ```
3. **Implement heartbeat pings:** Server pings that fail indicate disconnect
4. **Set reasonable timeouts:** Don't let streams run indefinitely

**Detection (Warning Signs):**
- Server logs show continued LLM calls after client disappears
- Token costs higher than expected for actual usage
- Backend processes accumulating for "ghost" connections

**Phase to Address:** Phase 1 (Backend disconnect detection)

**Sources:**
- [FastAPI Client Disconnection Discussion #7572](https://github.com/fastapi/fastapi/discussions/7572)
- [Understanding Client Disconnection in FastAPI](https://fastapiexpert.com/blog/2024/06/06/understanding-client-disconnection-in-fastapi/)
- [sse-starlette Package](https://pypi.org/project/sse-starlette/)

---

### PITFALL-04: Token Counting Fails During Streaming

**Severity:** Critical
**Affects:** Token budget tracking with warning thresholds (BUDGET-001)

**What goes wrong:**
Token counting handlers may return 0 or incorrect counts when used with streaming responses. The tokens are generated incrementally but not properly aggregated.

**Why it happens:**
- Streaming responses don't have a single `usage` field until completion
- Some tokenizers only work with complete text
- TokenCounterHandler may not intercept streaming chunks correctly

**Consequences:**
- Budget tracking shows incorrect usage
- Users hit budget limits unexpectedly (undercount) or get blocked prematurely (overcount)
- Trust erosion in usage display accuracy

**Prevention:**
1. **Count tokens from message_complete event:** Wait for final usage data:
   ```python
   {"event": "message_complete", "data": {"usage": {"input_tokens": X, "output_tokens": Y}}}
   ```
2. **Use API-provided token counts:** Don't calculate independently; use what the LLM API returns
3. **Handle partial stream interruption:** If stream ends early, estimate based on content length
4. **Test with real streaming:** Unit tests with mock streams may miss timing issues

**Detection (Warning Signs):**
- `get_usage_from_events()` returning None unexpectedly
- Token counts showing 0 after successful responses
- Discrepancy between displayed usage and actual LLM API billing

**Phase to Address:** Phase 2 (Token budget tracking)

**Sources:**
- [LlamaIndex Token Count Issue #19740](https://github.com/run-llama/llama_index/issues/19740)
- [LLM Token Counting Guide](https://winder.ai/calculating-token-counts-llm-context-windows-practical-guide/)

---

### PITFALL-05: RAG Source Attribution Hallucination

**Severity:** Critical
**Affects:** Document source attribution in AI responses (THREAD-008)

**What goes wrong:**
LLM may cite documents incorrectly, claim to use documents it didn't, or misinterpret document content. RAG does not prevent hallucination - it can actually create new hallucination vectors.

**Why it happens:**
- LLM retrieves relevant chunks but misinterprets context
- Chunk boundaries don't respect semantic meaning
- Metadata linking chunks to source documents is inadequate
- LLM "fills in" missing information from training data

**Consequences:**
- Users trust incorrect source attributions
- Clicking "Source: requirements.md" takes them to content that doesn't match
- False confidence in AI accuracy
- Legal/compliance issues if used for authoritative documentation

**Prevention:**
1. **Track chunk-to-document mapping explicitly:** Store document ID with each chunk
2. **Include document citations in prompt:** Instruct LLM to cite [Doc X] inline
3. **Verify citations match content:** Post-process to check cited docs contain claimed info
4. **Display source spans:** Show the actual text from the document, not just filename
5. **Aim for 95%+ attribution accuracy:** Build test suite of known query-document pairs

**Detection (Warning Signs):**
- Users report clicking source and not finding expected content
- Citations reference documents not in project
- Same response cites multiple documents but content is generic
- Build attribution accuracy tests: 20-30 queries with known correct sources

**Phase to Address:** Phase 5 (Document source attribution)

**Sources:**
- [How to Make RAG Agent Cite Sources Correctly](https://particula.tech/blog/fix-rag-citations)
- [23 RAG Pitfalls and How to Fix Them](https://www.nb-data.com/p/23-rag-pitfalls-and-how-to-fix-them)
- [Understanding Source Attribution in RAG](https://gautam75.medium.com/understanding-source-attribution-in-rag-6c8d64cfaed8)

---

## Moderate Pitfalls

Mistakes that cause delays, user confusion, or technical debt.

---

### PITFALL-06: Budget Warning Race Condition

**Severity:** Moderate
**Affects:** Token budget tracking with warning thresholds (BUDGET-001)

**What goes wrong:**
User sees "80% budget used" warning, sends a message, but the response pushes them past 100%. Warning was based on stale data, not accounting for in-flight requests.

**Why it happens:**
- Budget check happens before request
- LLM response tokens not known until after generation
- Multiple concurrent requests can all pass the 80% check

**Consequences:**
- User surprised by "budget exhausted" after passing warning
- Users may start long operations thinking they have budget
- Difficult to predict actual remaining capacity

**Prevention:**
1. **Estimate response tokens:** Based on conversation length and model
2. **Reserve estimated tokens during request:** Subtract estimate from available budget
3. **Pessimistic warnings:** Show 80% when actually at 75%, accounting for response
4. **Block new requests during streaming:** Prevent concurrent budget drain
5. **Show "estimated messages remaining"** not just percentage

**Detection (Warning Signs):**
- Users report going from warning to blocked without intermediate feedback
- Multiple concurrent requests from same user
- Budget jumps more than expected after single request

**Phase to Address:** Phase 2 (Token budget tracking)

---

### PITFALL-07: Mode State Persistence Scope Confusion

**Severity:** Moderate
**Affects:** Persistent conversation mode indicator (THREAD-005)

**What goes wrong:**
Mode persistence implemented at wrong scope. User expects mode to be per-thread but it's saved globally, or vice versa. Switching threads shows stale mode.

**Why it happens:**
- Unclear whether mode is thread property or user preference
- Using global SharedPreferences instead of thread metadata
- Not syncing mode to backend on change

**Consequences:**
- User sets mode for Thread A, opens Thread B, sees Thread A's mode
- Mode changes not reflected after app restart
- Inconsistent behavior causes confusion

**Prevention:**
1. **Mode is a thread property:** Store in Thread model, persist to backend
2. **Load mode with thread:** When `loadThread()` runs, mode comes with it
3. **Optimistic update with backend sync:** Change UI immediately, sync to backend
4. **Test across sessions:** Kill app, reopen, verify mode persisted for specific thread

**Detection (Warning Signs):**
- Mode selector shows wrong mode when switching threads
- Mode resets after app restart
- Different modes shown on different devices for same thread

**Phase to Address:** Phase 3 (Persistent conversation mode indicator)

---

### PITFALL-08: Artifact UI Overloads Message List

**Severity:** Moderate
**Affects:** Artifact generation UI (THREAD-007)

**What goes wrong:**
Artifacts rendered inline with messages make the conversation list heavy and slow. Large artifacts (BRDs, user story sets) cause scroll jank and memory issues.

**Why it happens:**
- Artifacts treated as regular messages with special rendering
- No virtualization for artifact content
- Markdown rendering of large documents is expensive

**Consequences:**
- Conversation becomes slow after generating artifacts
- Mobile devices lag or crash with multiple artifacts
- Users avoid artifact feature due to performance

**Prevention:**
1. **Artifact summary in message list:** Show collapsed card with title and preview
2. **Full artifact in separate view:** Expand to full-screen or side panel
3. **Lazy render artifact content:** Only render markdown when user expands
4. **Artifact list/tab:** Separate section for managing all artifacts
5. **Test with realistic artifact sizes:** Generate 50+ user stories and measure performance

**Detection (Warning Signs):**
- Frame drops when scrolling past artifacts
- Memory usage spikes after artifact generation
- Slow re-renders when new messages arrive in artifact-heavy thread

**Phase to Address:** Phase 4 (Artifact generation UI)

---

### PITFALL-09: File Size Validation After Upload Start

**Severity:** Moderate
**Affects:** File size validation UX (DOC-005)

**What goes wrong:**
File size checked after user clicks upload, after the file picker closes, or after upload begins. User has already committed to the action before learning of the error.

**Why it happens:**
```dart
// Bad: Check happens after picker returns
FilePickerResult? result = await FilePicker.platform.pickFiles();
if (result.files.single.size > 1024 * 1024) {  // Too late!
  showError("File too large");
}
```

**Consequences:**
- User picks large file, waits, then sees error
- On mobile, file picker is a context switch; error feels jarring
- User may have spent time selecting from cloud storage

**Prevention:**
1. **Show size limit prominently before picker:** "Maximum file size: 1MB"
2. **Validate immediately after picker returns:** Check before any upload UI
3. **Friendly error with file size shown:** "File is 2.4MB. Maximum size is 1MB."
4. **Keep picker open or allow re-pick:** Don't force navigation back to upload screen
5. **Consider platform differences:** Web file picker behavior differs from mobile

**Detection (Warning Signs):**
- Users report seeing upload progress then error
- Error appears after significant delay
- File picker opens twice for same upload attempt

**Phase to Address:** Phase 6 (File size validation UX)

---

### PITFALL-10: Reconnect Loop Without Backoff

**Severity:** Moderate
**Affects:** Network interruption handling (THREAD-004)

**What goes wrong:**
Client detects disconnect and immediately retries, server is still down, retry fails, client retries again. Creates tight loop hammering server and draining battery.

**Why it happens:**
- Reconnect logic uses `while(disconnected) { connect(); }`
- No delay between attempts
- No maximum retry count
- No exponential backoff

**Consequences:**
- Server flooded with reconnect attempts
- Client battery drained
- User sees "Reconnecting..." forever
- Network congestion worsens the outage

**Prevention:**
1. **Exponential backoff:** 1s, 2s, 4s, 8s, max 30s
2. **Maximum retry count:** Give up after N attempts (e.g., 5)
3. **User control:** "Connection lost. [Retry Now] or tap to dismiss"
4. **Network state awareness:** Use `connectivity_plus` to wait for network before retry
5. **Jitter:** Add randomness to prevent thundering herd

**Detection (Warning Signs):**
- Server logs show rapid-fire reconnect attempts from single client
- Battery drain complaints during outages
- Network monitoring shows request spikes after server restart

**Phase to Address:** Phase 1 (Network interruption handling)

**Sources:**
- [EventFlux - Exponential Backoff](https://pub.dev/packages/eventflux)
- [Building Flutter App with Seamless Connectivity Handling](https://ashutoshagarwal2014.medium.com/building-a-flutter-app-with-seamless-internet-connectivity-handling-2e98824e20c4)

---

## Low Pitfalls

Mistakes that cause minor annoyance but are easily fixable.

---

### PITFALL-11: Mode Badge Not Tappable on Small Screens

**Severity:** Low
**Affects:** Persistent conversation mode indicator (THREAD-005)

**What goes wrong:**
Mode badge in AppBar has small hit target. Users try to tap to change mode but miss the target on mobile.

**Why it happens:**
- Badge sized to content, not touch target
- No padding or InkWell wrapper
- AppBar space constraints squeeze the badge

**Prevention:**
1. **Minimum 48x48 touch target:** Per Material Design guidelines
2. **Use Chip with onTap:** Built-in touch target sizing
3. **Test on real device:** Simulator click precision differs from finger taps

**Detection (Warning Signs):**
- Users report mode won't change
- Heat maps show taps missing the badge area

**Phase to Address:** Phase 3 (Persistent conversation mode indicator)

---

### PITFALL-12: Artifact Export Without Filename Suggestion

**Severity:** Low
**Affects:** Artifact generation UI (THREAD-007)

**What goes wrong:**
Export dialog shows "Save file" with generic name like "document.md". User must manually rename to something meaningful.

**Why it happens:**
- Export function uses hardcoded filename
- No context about artifact type or content passed to save dialog

**Prevention:**
1. **Generate meaningful filename:** `user-stories-thread-123-2026-02-02.md`
2. **Include artifact type:** `brd-meeting-notes.docx`
3. **Allow user edit:** Suggest name but let user modify before save

**Detection (Warning Signs):**
- Downloads folder fills with `document (1).md`, `document (2).md`
- User feedback about manual renaming

**Phase to Address:** Phase 4 (Artifact generation UI)

---

### PITFALL-13: Source Chips Overflow on Many Documents

**Severity:** Low
**Affects:** Document source attribution (THREAD-008)

**What goes wrong:**
AI references 10 documents, all shown as chips. Chips overflow the message width, causing horizontal scroll or layout break.

**Why it happens:**
- Linear Row of chips with no wrap
- No limit on visible chips
- Long filenames exacerbate overflow

**Prevention:**
1. **Wrap chips:** Use Wrap widget instead of Row
2. **Limit visible chips:** Show 3-4, then "+N more" expandable
3. **Truncate filenames:** `requirements...md` with tooltip for full name
4. **Test with edge cases:** 10+ documents, 50+ character filenames

**Detection (Warning Signs):**
- Horizontal scrollbar appears in message bubble
- Chips cut off or overlap

**Phase to Address:** Phase 5 (Document source attribution)

---

### PITFALL-14: Token Display Precision Confusion

**Severity:** Low
**Affects:** Token budget tracking (BUDGET-001)

**What goes wrong:**
Display shows "You've used $12.34567 of $50.00" with too many decimal places, or rounds to "$12" hiding meaningful precision.

**Why it happens:**
- Decimal cost values displayed directly without formatting
- No consideration for user-meaningful precision
- Different precision for cost vs percentage

**Prevention:**
1. **Two decimal places for cost:** `$12.35 of $50.00`
2. **Whole number for percentage:** `25% used`
3. **Significant figures for large values:** `$1.2k` for thousands
4. **Consistent formatting across app:** Same rules in settings and conversation screen

**Detection (Warning Signs):**
- UI shows `$0.0000000001` or similar
- Users confused about actual usage

**Phase to Address:** Phase 2 (Token budget tracking)

---

## Phase-Specific Warnings

| Phase | Target Feature | Likely Pitfall | Mitigation |
|-------|---------------|----------------|------------|
| 1 | Network interruption handling | PITFALL-01 (content loss), PITFALL-02 (web buffering), PITFALL-03 (server disconnect), PITFALL-10 (reconnect loop) | Preserve partial content, platform-specific SSE, server disconnect detection, exponential backoff |
| 2 | Token budget tracking | PITFALL-04 (streaming count failure), PITFALL-06 (race condition), PITFALL-14 (display precision) | Use API-provided counts, estimate tokens, consistent formatting |
| 3 | Mode indicator | PITFALL-07 (persistence scope), PITFALL-11 (touch target) | Mode as thread property, minimum 48px touch target |
| 4 | Artifact generation UI | PITFALL-08 (list performance), PITFALL-12 (export filename) | Collapsed cards with expand, meaningful filenames |
| 5 | Document source attribution | PITFALL-05 (hallucination), PITFALL-13 (chip overflow) | Track chunk-to-document mapping, limit visible chips |
| 6 | File size validation UX | PITFALL-09 (late validation) | Validate before upload, show limit prominently |

---

## Integration with Existing Patterns

The following existing patterns in BA Assistant should be preserved and may inform pitfall prevention:

| Pattern | Location | How It Helps |
|---------|----------|--------------|
| 10-second undo window | `ConversationProvider.deleteMessage()` | Model for optimistic UI with recovery |
| Synchronous clipboard for Safari | `MessageBubble` copy action | Reminder to test cross-platform edge cases |
| FocusNode.onKeyEvent | Keyboard handling | Avoid breaking existing input behavior |
| Immediate persistence | ThemeProvider | Model for mode persistence |
| MockLLMAdapter | Testing infrastructure | Use for streaming interruption tests |

---

## Recommended Test Cases

For each phase, create these test scenarios:

### Phase 1 - Network Interruption
- [ ] TC-NET-01: Disable network mid-stream, verify partial content preserved
- [ ] TC-NET-02: Re-enable network, verify reconnect with backoff
- [ ] TC-NET-03: User can copy partial content during error state
- [ ] TC-NET-04: Server-side: verify streaming stops on client disconnect

### Phase 2 - Token Budget
- [ ] TC-BUDGET-01: Send message at 75% usage, verify warning appears
- [ ] TC-BUDGET-02: Usage persists across app restart
- [ ] TC-BUDGET-03: Concurrent requests don't bypass budget check
- [ ] TC-BUDGET-04: Token count matches API response usage field

### Phase 3 - Mode Indicator
- [ ] TC-MODE-01: Mode persists for specific thread across app restart
- [ ] TC-MODE-02: Switching threads shows correct mode for each
- [ ] TC-MODE-03: Mode badge tap target is 48x48 or larger

### Phase 4 - Artifact UI
- [ ] TC-ART-01: Generate 50 user stories, verify scroll performance
- [ ] TC-ART-02: Export suggests meaningful filename
- [ ] TC-ART-03: Collapsed artifact card shows preview

### Phase 5 - Source Attribution
- [ ] TC-SOURCE-01: Known query returns correct source documents
- [ ] TC-SOURCE-02: Clicking source chip opens correct document
- [ ] TC-SOURCE-03: 10+ sources handled with overflow

### Phase 6 - File Validation
- [ ] TC-FILE-01: 2MB file shows error before upload progress
- [ ] TC-FILE-02: Error message includes actual file size
- [ ] TC-FILE-03: User can select new file without navigating away

---

## Sources

**Network/SSE:**
- [EventFlux Package](https://pub.dev/packages/eventflux)
- [Flutter HTTP SSE](https://github.com/ElshiatyTube/flutter_http_sse)
- [FastAPI Client Disconnection](https://github.com/fastapi/fastapi/discussions/7572)
- [sse-starlette Package](https://pypi.org/project/sse-starlette/)
- [Handling Network Connectivity in Flutter](https://blog.logrocket.com/handling-network-connectivity-flutter/)

**Token Budget:**
- [LLM Economics: Avoiding Costly Pitfalls](https://www.aiacceleratorinstitute.com/llm-economics-how-to-avoid-costly-pitfalls/)
- [From Bills to Budgets: Tracking LLM Token Usage](https://www.traceloop.com/blog/from-bills-to-budgets-how-to-track-llm-token-usage-and-cost-per-user)
- [LiteLLM Token Usage Tracking](https://docs.litellm.ai/docs/completion/token_usage)

**RAG/Attribution:**
- [How to Fix RAG Citations](https://particula.tech/blog/fix-rag-citations)
- [23 RAG Pitfalls](https://www.nb-data.com/p/23-rag-pitfalls-and-how-to-fix-them)
- [Source Attribution in RAG](https://gautam75.medium.com/understanding-source-attribution-in-rag-6c8d64cfaed8)
- [Common Pitfalls in Generative AI Applications](https://huyenchip.com/2025/01/16/ai-engineering-pitfalls.html)

**UX/File Upload:**
- [File Uploader UX Best Practices](https://uploadcare.com/blog/file-uploader-ux-best-practices/)
- [AI UX Design Mistakes to Avoid](https://www.letsgroto.com/blog/ai-ux-design-mistakes)
- [Designing AI Products UX Tips](https://uzer.co/en/mistakes-designing-ai-products-ux-tips/)
