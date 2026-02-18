# Pitfalls Research: CLI Adapter Conversation Memory Fix

**Domain:** Python subprocess-based LLM adapter with conversation history
**Researched:** 2026-02-18
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Shell Argument Length Explosion (ARG_MAX)

**What goes wrong:**
Passing conversation history via command-line arguments (`-p "long history..."`) hits shell argument length limits, causing "Argument list too long" errors (E2BIG). On macOS, ARG_MAX is **1,048,576 bytes** (1MB), but the effective limit is ~950KB after subtracting environment variables and 2KB safety buffer.

With Claude CLI, the current implementation passes prompt via **stdin** (avoiding CLI args), but if refactored to use CLI flags, a single 20-turn conversation with rich responses could easily exceed 100KB. Ten concurrent conversations = 1MB+ argument string = hard failure.

**Why it happens:**
Developers assume "command-line arguments can hold any text" without understanding that `exec()` enforces a hard limit shared between `argv[]` and `envp[]`. The POC comment "Production: Format multi-turn conversation with role labels" suggests future CLI flag usage, which would be a disaster.

**How to avoid:**
✅ **ALWAYS pass prompts via stdin** for CLI subprocesses — this is what the current implementation does (line 285-300) and must be preserved.
✅ Calculate effective ARG_MAX with: `getconf ARG_MAX - $(env | wc -c) - 2048`
✅ On this system: **~1MB limit, effective limit ~950KB** — but stdin bypasses this entirely.
❌ NEVER use `-p "$(cat prompt.txt)"` pattern — shell expansion hits limits before subprocess sees it.

**Warning signs:**
- Error message: `OSError: [Errno 7] Argument list too long`
- Subprocess fails only in long conversations (10+ turns)
- Works in development, fails in production (different env var sizes)

**Phase to address:**
Phase 1 of conversation memory fix — document stdin requirement in plan, add warning comment in code.

---

### Pitfall 2: Token Budget Explosion Without Summarization

**What goes wrong:**
Sending full unfiltered conversation history to the API causes:
1. **Context window overflow**: Claude Opus 4.6 has a **200K token context window** (1M in beta with special header). A 50-turn conversation with document context can easily hit 150K+ tokens.
2. **Cost explosion**: Claude charges **2× for input tokens above 200K**. A 300K token request costs ~$1.50 (vs. $0.45 for 100K tokens).
3. **Performance degradation**: "Lost-in-the-middle" effect — models lose accuracy beyond 32K tokens. Even with 1M context, accuracy drops from 93% (256K) to 76% (1M) on retrieval tasks.
4. **Rate limiting**: Long-context requests (>200K tokens) have **separate, lower rate limits** than standard requests.

**Why it happens:**
Naive approach: "Just send everything!" seems simple and works in POC testing (5-10 turns). Production conversations (50+ turns with document search results) hit the wall suddenly.

**How to avoid:**
✅ **Implement conversation summarization** at 70-80% context capacity (~140K tokens for 200K window)
✅ **Sliding window strategy**: Keep last 10 messages verbatim + summarized history of older messages
✅ **Document context pruning**: Don't send full document text in every turn — use search_documents tool results only when relevant
✅ **Token counting**: Track estimated tokens with `len(text) / 4` approximation (accurate within 20%)
✅ **Tiered memory**: Recent messages (full) → mid-conversation (summarized) → ancient (key facts only)

**Budget recommendations:**
- **Development**: 50K token target (~30 full-fidelity messages with moderate document context)
- **Production**: 140K token hard limit (triggers summarization), 180K token ceiling (error out)
- **Emergency**: Use 1M context window with `context-1m-2025-08-07` beta header only as overflow valve

**Warning signs:**
- API returns 400 error: "prompt is too long"
- Cost per request suddenly 3x higher (indicates >200K token usage)
- Response quality degrades (lost-in-the-middle effect)
- Rate limiting errors (429) on specific threads

**Phase to address:**
Phase 2 of conversation memory fix — implement summarization strategy before shipping to production. Phase 1 can ship with warning about token limits + hard 50K token ceiling.

---

### Pitfall 3: Message Role Ordering Violations

**What goes wrong:**
LLM APIs enforce strict role alternation: `user → assistant → user → assistant`. Violations cause:
- API rejection: `"Conversation roles must alternate user/assistant/user/assistant/..."` (vLLM, others)
- Context confusion: Model treats consecutive user messages as single turn, losing separation
- Tool call orphaning: `assistant` message with `tool_use` must be followed by `user` message with `tool_result`

In CLI adapter context, formatting history as text removes API-level role enforcement, but **semantic alternation still matters** for model understanding.

**Why it happens:**
1. **System prompt injection**: Prepending system prompt as a message instead of using separate system parameter
2. **Tool result handling**: Inserting tool results without wrapping in proper `user` role message
3. **Message deduplication**: Removing duplicate messages breaks alternation (e.g., user → user after removing assistant)
4. **Streaming retries**: Retry logic might send two consecutive user messages

**How to avoid:**
✅ **Format history as role-labeled text** for CLI:
```
[system]: {system_prompt}

[user]: First question
[assistant]: First answer
[user]: Follow-up
[assistant]: Follow-up answer
[user]: Latest question
```
✅ **Validate alternation before formatting** — assert that message list follows `user`/`assistant` pattern
✅ **Handle edge cases**:
   - First message must be `user` (after system)
   - Last message must be `user` (the new query)
   - Tool calls: treat as part of `assistant` message, tool results as part of next `user` message

**Warning signs:**
- AI ignores parts of conversation
- Responses reference wrong message in history
- Tool results appear in incorrect context
- "Model seems confused about who said what"

**Phase to address:**
Phase 1 of conversation memory fix — implement proper role alternation validation and formatting.

---

### Pitfall 4: Special Character Mangling in Shell Escaping

**What goes wrong:**
Passing conversation history through shell (even via stdin) can corrupt:
- **Newlines**: Messages with `\n` might get collapsed or misinterpreted
- **Quotes**: User messages containing `"` or `'` break string escaping
- **Unicode**: Emoji, international characters might get mojibaked (encoding mismatch)
- **Backslashes**: Windows paths like `C:\Users\...` get eaten by escape processing
- **Shell metacharacters**: Backticks, dollar signs, pipe symbols in code blocks

Current implementation uses `shlex.quote()` but **writes to stdin as bytes** (line 297: `.encode('utf-8')`), which is correct but fragile if refactored.

**Why it happens:**
Python's `shlex.quote()` is designed for POSIX shell safety, not Windows. UTF-8 encoding/decoding errors occur when:
- Subprocess stdin uses wrong encoding (defaults to system locale, not UTF-8)
- User messages contain non-BMP Unicode (surrogate pairs)
- Binary data accidentally included (e.g., uploaded file metadata)

**How to avoid:**
✅ **ALWAYS use stdin for prompt delivery** (current code at line 285-300 is correct)
✅ **Explicit UTF-8 encoding**: `.encode('utf-8')` when writing to stdin
✅ **Validate message content**: Strip null bytes, validate UTF-8 before sending
✅ **Test with adversarial inputs**:
   - Messages containing: `"; rm -rf /; echo "attack`
   - Emoji: 👍🏽 (with skin tone modifiers — 2+ Unicode codepoints)
   - Multiline code blocks with backticks
   - Windows paths: `C:\Users\test\file.txt`

**Warning signs:**
- Subprocess fails with encoding errors
- Messages appear corrupted in AI responses (missing characters)
- Security scanner flags command injection risks
- Works on macOS/Linux, fails on Windows or vice versa

**Phase to address:**
Phase 1 of conversation memory fix — add input validation helper, document encoding requirements, add test cases.

---

### Pitfall 5: Subprocess Spawn Latency Accumulation

**What goes wrong:**
Current architecture spawns a **new CLI subprocess per message** (line 287-294). Overhead breakdown:
- **Python subprocess spawn**: ~290µs (with vfork), ~350µs (posix_spawn)
- **Node.js/CLI startup**: ~300-400ms for full interpreter initialization
- **Total per-message overhead**: ~400-450ms minimum

For a 20-turn conversation, that's **8-9 seconds of pure subprocess overhead** (independent of model thinking time). User perceives this as "AI is slow to respond."

**Why it happens:**
Subprocess-per-request is the simplest architecture — stateless, no process lifecycle management complexity. Works fine for single-shot interactions. Fails at scale.

**How to avoid:**
✅ **Accept the overhead for POC/beta** — Claude CLI is experimental feature, not default
✅ **Document performance characteristics** in phase plan:
   - "Each message has ~400ms subprocess overhead on top of model latency"
   - "For <10 turn conversations, acceptable. For >30 turns, consider persistent process pool."
✅ **Future optimization path** (Phase 3+):
   - Persistent CLI daemon (spawned once per thread, reused across messages)
   - Process pooling (5 warm processes, round-robin allocation)
   - Migrate to native SDK if performance becomes issue

**Performance budget:**
- **Acceptable**: <1s first response (subprocess + model), <500ms subsequent (model only with warm process)
- **Current reality**: ~800ms first response (400ms subprocess + 400ms model), ~800ms subsequent (400ms subprocess + 400ms model)
- **User perception**: Feels slower than Anthropic/Gemini adapters (direct API, no subprocess)

**Warning signs:**
- Users report "Assistant section feels slower than BA Assistant"
- Profiling shows 40%+ of request time in subprocess spawn
- High CPU usage from repeated interpreter initialization

**Phase to address:**
Phase 1 (document and accept), Phase 3+ (optimize with persistent processes if needed).

---

### Pitfall 6: System Prompt + Conversation History Confusion

**What goes wrong:**
The CLI adapter prepends system prompt to the conversation history (line 264):
```python
combined_prompt = f"[SYSTEM]: {system_prompt}\n\n[USER]: {prompt_text}"
```

With conversation history, this becomes ambiguous:
- Where does system prompt end and conversation begin?
- Does the model treat system prompt as part of turn 1 context?
- If system prompt is 5,000 tokens, does it get "pushed out" of context in long conversations?

**Critical edge case**: Assistant threads get **empty system prompt** per `LOGIC-01` (ai_service.py:909). The current code would format:
```
[SYSTEM]:

[USER]: prompt_text
```
Empty `[SYSTEM]:` section might confuse model or waste tokens.

**Why it happens:**
Claude CLI's `-p` flag accepts a single text prompt, not structured message arrays. The adapter hacks system prompt into the text by prefixing it, but this loses the semantic separation that proper API calls maintain.

**How to avoid:**
✅ **Structured history formatting** with clear delimiters:
```
<system_context>
{system_prompt}
</system_context>

<conversation_history>
[user]: First message
[assistant]: First response
...
</conversation_history>

[user]: {latest_message}
```
✅ **Skip system section if empty** (Assistant thread case):
```python
if system_prompt.strip():
    prompt_parts.append(f"<system_context>\n{system_prompt}\n</system_context>\n")
prompt_parts.append(format_conversation_history(messages[:-1]))
prompt_parts.append(f"[user]: {last_message}")
```
✅ **Test both thread types**:
   - BA Assistant: Long system prompt with tool descriptions
   - Assistant: Empty system prompt, conversation-only

**Warning signs:**
- Model ignores system instructions in multi-turn conversations
- System prompt content "bleeds" into conversation context
- Empty system prompt causes formatting errors or confusion

**Phase to address:**
Phase 1 of conversation memory fix — implement proper prompt structure with system/conversation separation.

---

### Pitfall 7: Streaming Response Format Changes with Multi-Turn Context

**What goes wrong:**
Assumption: "CLI stream-json output format is consistent regardless of context length."
Reality: **Streaming parsers can choke on edge cases**:
- Very long responses (>1MB) might trigger buffer overflows (current limit: 1MB at line 293)
- Multi-turn context with tool usage might reorder event types
- Error events might appear mid-stream instead of at end

Current parser (line 304-327) reads line-by-line and parses JSON per line. Risks:
- JSON event spans multiple lines (unlikely but possible with debug output)
- Binary data in stdout (CLI subprocess stderr leak)
- Partial UTF-8 sequences at buffer boundary (1MB limit)

**Why it happens:**
Line-delimited JSON parsing assumes **one event = one line**. CLI debug output or error messages can break this:
```
{"type": "assistant", "message": {...}}
Warning: rate limit approaching
{"type": "result", "usage": {...}}
```
Non-JSON line causes `json.JSONDecodeError`, logged but skipped (line 326).

**How to avoid:**
✅ **Validate current implementation handles stdout pollution** — test with `--verbose` flag (already present at line 274)
✅ **Increase buffer limit proactively** from 1MB to 5MB if responses might include large artifacts:
```python
limit=5 * 1024 * 1024  # 5MB buffer for large BRD artifacts
```
✅ **Add stream corruption detection**:
```python
if consecutive_json_errors > 10:
    yield StreamChunk(chunk_type="error", error="Stream corrupted")
    break
```

**Warning signs:**
- `JSONDecodeError` warnings in logs (currently silent)
- Streaming stops mid-response with no error
- Response truncated at exactly 1MB
- Multi-turn conversations fail more often than single-shot

**Phase to address:**
Phase 1 of conversation memory fix — increase buffer limit, add corruption detection, test with verbose CLI output.

---

### Pitfall 8: Document Context Duplication in Conversation History

**What goes wrong:**
When user asks question → AI searches documents → user asks follow-up, the conversation history includes:
```
[user]: First question
[assistant]: <includes document search results>
[user]: Follow-up question
```

If the adapter passes ALL assistant responses verbatim, **document search results get resent** in every subsequent turn:
- Turn 1: 50K tokens (10K conversation + 40K docs)
- Turn 2: 100K tokens (10K new conversation + 40K docs from turn 1 + 40K new docs)
- Turn 3: 190K tokens (exponential growth)

**Token explosion formula**: Each turn duplicates previous document context → O(n²) token growth.

**Why it happens:**
The `assistant` message content includes both generated text AND tool results. Storing it verbatim in history means replaying tool results in future turns even when irrelevant.

**How to avoid:**
✅ **Filter assistant messages** before formatting for history:
```python
def filter_assistant_message(content):
    # Keep text blocks, drop tool_use blocks
    if isinstance(content, list):
        return [block for block in content if block.get("type") == "text"]
    return content
```
✅ **Store tool results separately** in message metadata, don't include in formatted history
✅ **Trust model to re-search** if it needs document context for follow-up (tool available in current turn)

**Warning signs:**
- Token usage grows quadratically with conversation length
- Long conversations hit 200K token limit unexpectedly
- Same document chunks appear multiple times in streaming tool_use events

**Phase to address:**
Phase 2 of conversation memory fix (optimization phase) — document filtering strategy, possibly Phase 1 if testing reveals immediate issue.

---

### Pitfall 9: Test Brittleness from Hardcoded Response Expectations

**What goes wrong:**
Testing conversation memory with assertions like:
```python
assert "mentioned earlier" in response  # Brittle!
```
Works in development, fails in CI due to model non-determinism. With multi-turn context, model might:
- Paraphrase instead of quoting
- Answer correctly without explicit reference
- Use synonyms ("as discussed before" vs. "mentioned earlier")

**Why it happens:**
Developers test LLM features like deterministic functions. LLM outputs are stochastic — even with `temperature=0`, minor prompt changes cause output variance.

**How to avoid:**
✅ **Semantic assertions** instead of string matching:
```python
# Bad: assert "mentioned earlier" in response
# Good: assert references_conversation_context(response, previous_topic)
```
✅ **Structured output validation**: Test for presence of key facts, not exact wording
✅ **Reference-based testing**:
```python
messages = [
    {"role": "user", "content": "My favorite color is blue"},
    {"role": "assistant", "content": "Noted!"},
    {"role": "user", "content": "What's my favorite color?"}
]
assert extract_color(response) == "blue"  # Test understanding, not verbatim
```

**Test strategy for conversation memory**:
1. **Factual recall**: "I said X. What did I say?" → assert response contains X concept
2. **Context dependency**: Ask ambiguous question ("What about it?") → assert resolution uses history
3. **Negation**: Ask question requiring info NOT in last message → assert retrieval from earlier turns

**Warning signs:**
- Tests pass locally, fail in CI (model API variance)
- Tests fail after model updates (GPT-4 → GPT-4.5)
- Tests need constant tuning of expected strings

**Phase to address:**
Phase 1 of conversation memory fix — define semantic test strategy upfront, not after writing brittle tests.

---

### Pitfall 10: Regression Risk — Breaking Existing BA Assistant Adapter

**What goes wrong:**
The fix targets `claude_cli_adapter.py` (Assistant threads), but code changes might accidentally break BA Assistant threads which use different adapters (`anthropic_adapter.py`, `gemini_adapter.py`, `deepseek_adapter.py`).

**Integration point**: `ai_service.py` (line 909) routes threads:
- `thread_type=assistant` → `claude_cli_adapter` (LOGIC-03)
- `thread_type=ba_assistant` → default provider adapter

Shared code paths:
- `conversation_service.py:build_conversation_context()` — builds history for ALL adapters
- Message storage in SQLite — shared by both thread types

**Why it happens:**
"I'm only changing the CLI adapter, what could go wrong?" But refactoring message formatting helpers, changing SQLite schema, or modifying `build_conversation_context()` affects all adapters.

**How to avoid:**
✅ **Test BOTH thread types** in every phase:
   - Create BA Assistant thread → send multi-turn conversation → verify response quality
   - Create Assistant thread → send multi-turn conversation → verify conversation memory works
✅ **Isolate changes** to CLI adapter only — don't refactor shared helpers unless necessary
✅ **Schema changes require migration** with backward compatibility:
```python
# If adding message metadata field:
messages = session.query(Message).all()
for msg in messages:
    msg.metadata = msg.metadata or {}  # Backfill nulls
```

**Regression test checklist**:
- [ ] BA Assistant: Single-turn chat works
- [ ] BA Assistant: Multi-turn chat works
- [ ] BA Assistant: Document search works
- [ ] BA Assistant: Artifact generation works
- [ ] Assistant: Single-turn chat works
- [ ] Assistant: Multi-turn chat works (NEW)
- [ ] Assistant: Document upload works

**Warning signs:**
- "BA Assistant suddenly stopped working"
- Error: `AttributeError: 'NoneType' object has no attribute 'content'` (schema issue)
- Existing tests fail after conversation memory fix

**Phase to address:**
Phase 1 of conversation memory fix — add regression tests first, then implement fix, verify both adapters work.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| "Pass last message only" (current POC) | Simple implementation, no formatting logic | No conversation memory, user frustration | POC/demo only — NOT acceptable for beta |
| Skip conversation summarization | Avoid complexity of summarization logic | Token budget explosions, cost overruns, rate limiting | Acceptable if conversations <20 turns AND token monitoring exists |
| Hardcode 1MB stdin buffer | Simple subprocess config | Memory waste for short messages, crashes on huge artifacts | Acceptable — 1MB is reasonable safety margin |
| Format history as plain text instead of structured | Works with CLI `-p` flag constraint | Loses semantic role information, harder to implement advanced features (tool result filtering, summarization) | Acceptable for CLI adapter — required by CLI interface |
| Spawn subprocess per message | Stateless, simple, no lifecycle management | ~400ms overhead per message, CPU waste | Acceptable for experimental feature with <1000 DAU |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **Claude CLI subprocess** | Passing prompt via `-p "$(cat file)"` (shell expansion) | Write prompt to stdin, close pipe, read stdout line-by-line |
| **SQLite conversation history** | Assuming chronological order without `ORDER BY created_at` | Explicit sort: `query(Message).filter(...).order_by(Message.created_at.asc())` |
| **Context window management** | Sending all messages blindly | Count tokens (rough: `len(text)/4`), summarize at 70% capacity |
| **Shell escaping** | Using `shlex.quote()` on entire conversation string | Encode as UTF-8 bytes, write to stdin (bypasses shell parsing) |
| **Streaming JSON parsing** | Assuming one JSON object per call | Line-delimited: one object per line, skip non-JSON lines with warning |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| **Subprocess spawn overhead** | Assistant feels slower than BA Assistant | Document expected latency, optimize in Phase 3+ with process pooling | >30 turn conversations (30× 400ms = 12s overhead) |
| **Quadratic token growth** | Cost spikes after 10 turns | Filter tool results from assistant messages before formatting history | Turn 15-20 (hits 200K context limit) |
| **Lost-in-the-middle degradation** | AI quality drops in long threads | Implement sliding window (last 10 messages + summarized history) | >32K tokens of context (~50 messages) |
| **Buffer overflow on large responses** | Stream cuts off mid-response | Set subprocess buffer limit to 5MB | Single BRD artifact >1MB |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| **Command injection via message content** | User sends message with `; rm -rf /`, shell executes it | Use stdin for prompt delivery, NOT shell arguments |
| **Credentials in conversation history** | User accidentally includes API key in message, stored in SQLite | Input validation: regex scan for patterns like `sk-[a-zA-Z0-9]+`, warn before storing |
| **Cross-thread memory leakage** | Bug causes thread A's history to appear in thread B | Filter by `thread_id` in SQL query, add assertion: `assert all(m.thread_id == thread_id for m in messages)` |
| **Subprocess environment leakage** | Subprocess inherits sensitive env vars (ANTHROPIC_API_KEY, etc.) | Strip sensitive vars: `env = {k: v for k, v in os.environ.items() if k not in SENSITIVE_VARS}` (already done at line 281-282) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| **Silent conversation memory failure** | AI forgets, user confused, no error shown | Log warning when message history >50 turns: "Conversation too long, older messages summarized" |
| **Inconsistent memory across thread types** | BA Assistant remembers, Assistant forgets → "Is this a bug?" | Document different adapter behaviors in UI, possibly add badge: "Powered by Claude CLI (experimental)" |
| **Slow response time with no feedback** | 400ms subprocess overhead + 500ms model = 900ms blank screen | Show "Initializing..." indicator for first 300ms, then "Thinking..." |
| **History flooding the prompt** | User sees 50-turn history prepended to their message in debug view | Collapse history in UI: "Conversation context: 45 previous messages" (expandable) |

## "Looks Done But Isn't" Checklist

- [ ] **Conversation memory implementation:** Often missing role alternation validation — verify with test: `[user, user, assistant]` → assert formatting handles gracefully (merge consecutive user messages)
- [ ] **Token counting:** Often missing document context in calculation — verify `count_tokens(messages)` includes system prompt + message history + document search results
- [ ] **System prompt handling:** Often hardcoded for BA threads — verify Assistant threads (empty system prompt) format correctly
- [ ] **Buffer limit tuning:** Often uses default 64KB — verify subprocess created with `limit=5*1024*1024` for large artifacts
- [ ] **Error handling:** Often catches `JSONDecodeError` but doesn't detect stream corruption — verify consecutive errors trigger failure, not silent skip
- [ ] **Regression tests:** Often tests new feature only — verify both `thread_type=assistant` AND `thread_type=ba_assistant` work

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| **ARG_MAX overflow** | LOW | Already using stdin (line 297), no recovery needed — just document why |
| **Token budget explosion** | MEDIUM | 1. Add token counting before API call, 2. Implement emergency summarization (truncate to last 10 messages), 3. Return error if >180K tokens |
| **Role ordering broken** | LOW | 1. Add validation function, 2. Merge consecutive same-role messages, 3. Log warning and continue |
| **Special character corruption** | LOW | 1. Add input sanitization (strip null bytes), 2. Validate UTF-8 encoding, 3. Escape only if using shell args (not needed for stdin) |
| **Subprocess latency** | HIGH | 1. Document as known limitation, 2. Implement process pooling (warm process reuse), 3. Migrate to SDK if latency critical |
| **System prompt confusion** | LOW | 1. Restructure prompt format with clear delimiters, 2. Skip system section if empty, 3. Test both thread types |
| **Streaming corruption** | MEDIUM | 1. Increase buffer limit to 5MB, 2. Add corruption detection (consecutive errors), 3. Implement partial recovery (yield what was parsed) |
| **Document context duplication** | MEDIUM | 1. Filter assistant messages before formatting, 2. Store tool results separately, 3. Implement smart history (keep text, drop tool_use blocks) |
| **Brittle tests** | LOW | 1. Rewrite tests with semantic assertions, 2. Use structured output validation, 3. Test concepts not exact strings |
| **BA Assistant regression** | HIGH | 1. Rollback changes, 2. Add regression tests first, 3. Isolate CLI adapter changes, 4. Test both adapters after every change |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ARG_MAX overflow | Phase 1 (document stdin requirement) | Code review: assert prompt passed via stdin, not CLI args |
| Token budget explosion | Phase 2 (implement summarization) | Integration test: 50-turn conversation → verify <140K tokens |
| Role ordering violations | Phase 1 (validation + formatting) | Unit test: various message patterns → assert valid role alternation |
| Special character mangling | Phase 1 (input validation) | Unit test: adversarial inputs (emoji, quotes, newlines) → assert round-trip |
| Subprocess spawn latency | Phase 1 (document), Phase 3+ (optimize) | Performance test: measure p95 latency, document in TESTING-QUEUE.md |
| System prompt confusion | Phase 1 (structured formatting) | Integration test: both thread types → verify system prompt handling |
| Streaming corruption | Phase 1 (increase buffer, add detection) | Stress test: 1000-turn conversation → verify stream completes |
| Document context duplication | Phase 2 (filter tool results) | Token counting test: multi-turn with docs → verify linear not quadratic growth |
| Test brittleness | Phase 1 (semantic test strategy) | Test review: no hardcoded response strings, only semantic assertions |
| BA Assistant regression | Phase 1 (add regression tests first) | Regression suite: both adapters, all features → all pass |

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Phase 1: Basic conversation memory** | Role ordering violations, system prompt confusion, regression risk | Add validation, test both thread types, regression suite first |
| **Phase 2: Token optimization** | Quadratic token growth, summarization complexity | Implement simple sliding window first, full summarization later |
| **Phase 3: Performance tuning** | Over-engineering process pooling, premature optimization | Profile first, optimize only if latency >2s p95 |

## Sources

**ARG_MAX and shell limits:**
- [ARG_MAX, maximum length of arguments for a new process](https://www.in-ulm.de/~mascheck/various/argmax/)
- [Maximum Character Length of Arguments In a Shell Command - nixCraft](https://www.cyberciti.biz/faq/linux-unix-arg_max-maximum-length-of-arguments/)
- [Will the real ARG_MAX please stand up? Part 1 — mina86.com](https://mina86.com/2021/the-real-arg-max-part-1/)

**Python subprocess performance:**
- [Issue 11314: Subprocess suffers 40% process creation overhead penalty - Python tracker](https://bugs.python.org/issue11314)
- [subprocess.Popen: Performance regression on Linux since 124af17b6e - Python Issue #112334](https://github.com/python/cpython/issues/112334)

**Shell escaping and shlex:**
- [Python shlex — Simple lexical analysis](https://docs.python.org/3/library/shlex.html)
- [Avoiding Command Injection: A Guide to shlex.quote() and Safer Alternatives](https://runebook.dev/en/docs/python/library/shlex/shlex.shlex.quotes)

**LLM context windows and token limits:**
- [Context Window Overflow in 2026: Fix LLM Errors Fast](https://redis.io/blog/context-window-overflow/)
- [LLM context windows: what they are & how they work](https://redis.io/blog/llm-context-windows/)
- [Claude API Pricing - 1M Context Window Documentation](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude API Context Windows Documentation](https://platform.claude.com/docs/en/build-with-claude/context-windows)

**Streaming JSON and SSE pitfalls:**
- [How to handle stream response with SSE and assemble into JSON](https://docs.agentx.so/docs/how-to-handle-stream-response-with-sse-and-assemble-into-json)
- [The line break problem when using Server Sent Events (SSE)](https://medium.com/@thiagosalvatore/the-line-break-problem-when-using-server-sent-events-sse-1159632d09a0)
- [Transports - Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)

**LLM message roles and ordering:**
- [Conversation roles must alternate user/assistant/user/assistant/... - vLLM Discussion #2112](https://github.com/vllm-project/vllm/discussions/2112)
- [The Difference Between System Messages and User Messages in Prompt Engineering](https://medium.com/@dan_43009/the-difference-between-system-messages-and-user-messages-in-prompt-engineering-04eaca38d06e)
- [System Prompts vs. User Prompts: The Missing Manual for Controlling LLMs](https://medium.com/@frenzur007/system-prompts-vs-user-prompts-the-missing-manual-for-controlling-llms-53034f0c75ac)

**Project-specific:**
- `/Users/a1testingmac/projects/XtraSkill/backend/app/services/llm/claude_cli_adapter.py` (current implementation)
- `/Users/a1testingmac/projects/XtraSkill/user_stories/BUG-023_cli-adapter-drops-conversation-history.md` (bug report)
- System ARG_MAX: `1048576` bytes (verified via `getconf ARG_MAX` on macOS)

---

*Pitfalls research for: CLI adapter conversation memory fix*
*Researched: 2026-02-18*
*Confidence: HIGH (quantified limits, official docs, existing codebase analysis)*
