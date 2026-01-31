# Domain Pitfalls: Multi-LLM Provider Integration

**Domain:** Multi-provider LLM integration (Claude, Gemini, DeepSeek)
**Researched:** 2026-01-31
**Confidence:** HIGH (verified with official documentation)

---

## Critical Pitfalls

Mistakes that cause rewrites or major production issues.

---

### Pitfall 1: Thinking Mode Response Format Divergence

**Severity:** CRITICAL

**What goes wrong:** Each provider returns thinking/reasoning content in fundamentally different response structures, causing parsing failures and UI crashes when switching models.

**Root cause differences:**

| Provider | Thinking Field | Response Structure | Streaming Delta Type |
|----------|---------------|-------------------|---------------------|
| Claude | `thinking` block with `signature` | Separate content blocks | `thinking_delta` event |
| Gemini | `thought` boolean on parts | Parts with `thought` flag | Part has `thought: true` |
| DeepSeek | `reasoning_content` field | Separate from `content` | `delta.reasoning_content` |

**Consequences:**
- UI shows raw JSON when expecting parsed thinking
- Streaming breaks mid-response
- Token tracking becomes inaccurate (thinking tokens billed differently)
- Conversation context corrupted when passing back incorrect format

**Prevention:**
1. Create provider-specific response normalizers BEFORE building unified streaming
2. Define canonical internal format that ALL providers map to
3. Test with actual API responses, not mock data

**Detection (warning signs):**
- Tests pass with mocks but fail with real APIs
- Thinking content appears as `[object Object]` in UI
- Token counts don't match billing

**Phase to address:** Phase 1 - Provider abstraction layer must include response normalization

---

### Pitfall 2: DeepSeek Base URL Configuration

**Severity:** CRITICAL

**What goes wrong:** DeepSeek uses OpenAI-compatible SDK but requires different base URL. Forgetting to set `base_url` sends requests to OpenAI servers, failing with 401 errors.

**Why it happens:** Developers assume OpenAI SDK compatibility means drop-in replacement.

**Code trap:**
```python
# WRONG - Goes to OpenAI, fails with 401
client = OpenAI(api_key=DEEPSEEK_API_KEY)

# CORRECT - Must specify base_url
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)
```

**Consequences:**
- 401 errors with misleading "invalid API key" message
- Hours debugging authentication when problem is endpoint
- Production outages if deployed without testing

**Prevention:**
1. Use provider-specific client factory pattern
2. Validate base_url in configuration validation on startup
3. Integration tests against actual endpoints (not mocks)

**Detection:**
- 401 errors when DeepSeek key is valid
- Error messages mentioning OpenAI when using DeepSeek

**Phase to address:** Phase 1 - Client initialization with validation

---

### Pitfall 3: Thinking Mode Parameter Incompatibility

**Severity:** CRITICAL

**What goes wrong:** Each provider has different parameters that thinking mode DOES NOT support. Using unsupported parameters causes errors or silent behavior changes.

**Provider restrictions:**

| Provider | Unsupported with Thinking | Behavior |
|----------|--------------------------|----------|
| Claude | `temperature`, `top_p` (values other than 0.95-1) | Validation error |
| DeepSeek | `temperature`, `top_p`, `presence_penalty`, `frequency_penalty` | Silently ignored |
| DeepSeek | `logprobs`, `top_logprobs` | Throws error |
| Gemini | Varies by `thinking_level` setting | Unpredictable |

**Consequences:**
- Different behavior when switching models
- Silent parameter ignoring leads to unexpected outputs
- Hard-to-debug inconsistencies

**Prevention:**
1. Create per-provider parameter validation layer
2. Strip/warn on unsupported parameters BEFORE API call
3. Document which parameters apply to which providers

**Detection:**
- Same prompt produces wildly different responses across providers
- API errors mentioning unsupported parameters

**Phase to address:** Phase 1 - Parameter sanitization in abstraction layer

---

### Pitfall 4: Streaming Timeout and Connection Handling

**Severity:** CRITICAL

**What goes wrong:** Extended thinking can take 30+ seconds before first token. Standard HTTP timeouts (30s) kill connection, losing entire response.

**Why it happens:**
- Claude thinking budget can be 10,000+ tokens (significant processing time)
- Gemini with `thinking_level: high` delays first token significantly
- DeepSeek reasoner mode processes before streaming

**Consequences:**
- Users see "connection failed" after waiting
- Partial responses lost
- Retry logic sends duplicate requests (cost implications)

**Prevention:**
1. Increase backend timeout to 5+ minutes for thinking requests
2. Implement SSE heartbeats every 15 seconds
3. Use HTTP/2 where possible (better connection handling)
4. Show "thinking..." indicator before first token

**Specific configurations:**
```python
# Backend SSE endpoint
async def stream_response():
    # Send heartbeat comment every 15s
    yield ": heartbeat\n\n"

# Flutter client
http.Client()..timeout = Duration(minutes: 5)
```

**Detection:**
- Timeouts on complex queries only
- Works for simple queries, fails for thinking-enabled

**Phase to address:** Phase 2 - Streaming infrastructure must handle long waits

---

### Pitfall 5: Gemini Thought Signatures in Multi-Turn

**Severity:** CRITICAL

**What goes wrong:** Gemini requires "thought signatures" to maintain reasoning context across turns. Dropping these breaks multi-turn thinking conversations.

**Why it happens:** Unlike Claude/DeepSeek, Gemini's API is stateless and requires signature passback.

**Quote from official docs:**
> "Thought signatures are encrypted representations of the model's internal thought process that preserve the Gemini reasoning state during multi-turn conversations... you must return the thought signatures from previous responses in your subsequent requests."

**Consequences:**
- Multi-turn thinking conversations lose context
- Model "forgets" reasoning from previous turns
- Degraded response quality in conversations

**Prevention:**
1. Store complete Gemini response parts (don't strip metadata)
2. Pass back entire response with all parts in follow-up requests
3. Use official Python/JS SDK (handles signatures automatically)
4. If using REST: never merge parts with/without signatures

**Detection:**
- First thinking response is good, subsequent ones ignore context
- Works in single-turn, fails in multi-turn

**Phase to address:** Phase 3 - Conversation state management per-provider

---

## Moderate Pitfalls

Mistakes that cause delays or technical debt.

---

### Pitfall 6: Token Counting Varies by Provider

**Severity:** MODERATE

**What goes wrong:** Each provider uses different tokenization. Same text = different token counts = inaccurate cost estimation and context limit tracking.

**Tokenizer differences:**
- OpenAI/DeepSeek: tiktoken (o200k_base or cl100k_base)
- Claude: Custom tokenizer (API-only access)
- Gemini: Custom tokenizer (API-only access)

**Key issue:** Claude and Gemini tokenizers require API calls to count tokens accurately. Offline estimation is approximate only.

**Consequences:**
- Underestimating tokens leads to context overflow errors
- Overestimating wastes context window
- Cost tracking is inaccurate

**Prevention:**
1. Use provider-specific token counting APIs
2. Add buffer (10%) to estimated counts
3. Cache token counts for repeated content
4. Track actual vs estimated for calibration

**Detection:**
- "Context too long" errors when estimate said it should fit
- Billing doesn't match internal tracking

**Phase to address:** Phase 2 - Provider-aware token tracking

---

### Pitfall 7: Thinking Token Billing Asymmetry

**Severity:** MODERATE

**What goes wrong:** Thinking/reasoning tokens are billed as OUTPUT tokens even though user doesn't see full content. Claude 4 summarizes thinking but bills for FULL thinking.

**Quote from Claude docs:**
> "You're charged for the full thinking tokens generated by the original request, not the summary tokens. The billed output token count will not match the count of tokens you see in the response."

**DeepSeek:** Charges for `reasoning_content` tokens separately.
**Gemini:** `thinking_budget` controls maximum, but dynamic allocation means variable cost.

**Consequences:**
- Budget tracking is inaccurate
- Users surprised by costs
- Thinking-enabled conversations cost 10-30x more than expected

**Prevention:**
1. Track thinking tokens SEPARATELY from visible output
2. Show users "thinking cost" vs "response cost"
3. Add budget limits per conversation
4. Warn when thinking budget is high

**Detection:**
- Bills much higher than token counts suggest
- Users complain about unexpected costs

**Phase to address:** Phase 2 - Enhanced token tracking with thinking awareness

---

### Pitfall 8: Rate Limit Differences

**Severity:** MODERATE

**What goes wrong:** Each provider has different rate limits, requiring provider-specific retry logic.

**Rate limit patterns:**
- **Claude:** 429 with retry-after header
- **DeepSeek:** 429 + server busy (503) due to capacity constraints
- **Gemini:** Per-project quotas, may need Google Cloud quota increases

**DeepSeek specific issue:**
> "Users have frequently encountered server busy errors, often after just a few interactions with the API. This issue has been exacerbated by the temporary suspension of API service recharges due to server resource constraints."

**Consequences:**
- One provider failure affects entire app if not handled
- Retry storms when provider is overloaded
- User experience degraded during provider issues

**Prevention:**
1. Implement exponential backoff with jitter
2. Circuit breaker per provider (not global)
3. Provider fallback strategy (fail to alternative provider)
4. Rate limit tracking per provider

**Detection:**
- Bursts of 429 errors
- All requests failing when only one provider is down

**Phase to address:** Phase 4 - Error handling and fallback patterns

---

### Pitfall 9: Claude Extended Thinking Block Preservation

**Severity:** MODERATE

**What goes wrong:** Claude requires passing back `thinking` blocks when using tools. Stripping them breaks reasoning continuity.

**Quote from official docs:**
> "During tool use, you must pass thinking blocks back to the API, and you must include the complete unmodified block back to the API. This is critical for maintaining the model's reasoning flow and conversation integrity."

**Consequences:**
- Tool use + thinking = broken after first tool call
- Model loses reasoning context mid-workflow
- Mysterious quality degradation in multi-step tool use

**Prevention:**
1. NEVER strip thinking blocks during tool use loops
2. Store complete response including all content blocks
3. Test tool use + thinking combinations explicitly

**Detection:**
- First tool call works, subsequent ones lose context
- Quality drops after tool use in thinking mode

**Phase to address:** Phase 3 - Conversation state management

---

### Pitfall 10: API Version Mismatches

**Severity:** MODERATE

**What goes wrong:** SDKs update frequently with breaking changes. Mixing SDK versions or not updating causes failures.

**Examples:**
- Gemini: `thinking_config` requires Python SDK >= 1.51.0
- Claude: Extended thinking behavior differs between Claude 3.7 and Claude 4 models
- DeepSeek: API endpoints evolve rapidly

**Consequences:**
- New features don't work
- Mysterious errors on valid code
- "Works on my machine" issues

**Prevention:**
1. Pin SDK versions in requirements
2. Document minimum versions per feature
3. Test SDK upgrades before deploying
4. Monitor provider changelogs

**Detection:**
- Features work locally but not in production
- Errors mentioning unknown parameters

**Phase to address:** Phase 1 - Dependency management and version pinning

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

---

### Pitfall 11: Inconsistent Error Message Formats

**Severity:** MINOR

**What goes wrong:** Each provider returns errors in different formats, making unified error handling tedious.

**Error format examples:**
```python
# Claude
anthropic.APIError with structured error object

# DeepSeek
OpenAI-style errors but with DeepSeek-specific codes

# Gemini
Google Cloud error format with nested details
```

**Prevention:**
1. Create error normalization layer
2. Map all errors to common format with:
   - error_code (unified)
   - message (user-friendly)
   - provider (which provider failed)
   - retryable (boolean)

**Phase to address:** Phase 4 - Error handling standardization

---

### Pitfall 12: Model Name Variations

**Severity:** MINOR

**What goes wrong:** Model names aren't intuitive and change with versions.

**Current model names:**
- Claude: `claude-sonnet-4-5-20250929`, `claude-opus-4-5-20251101`
- Gemini: `gemini-3-flash-preview`, `gemini-3-pro`
- DeepSeek: `deepseek-chat`, `deepseek-reasoner` (V3.2)

**Prevention:**
1. Use internal model aliases (e.g., "claude-thinking", "gemini-fast")
2. Map aliases to actual model names in config
3. Single source of truth for model configuration

**Phase to address:** Phase 1 - Configuration and model registry

---

### Pitfall 13: SSE Event Format Differences

**Severity:** MINOR

**What goes wrong:** While all use SSE, event naming and data structure varies slightly.

**Differences:**
- Claude: `content_block_delta` with `thinking_delta` or `text_delta` type
- DeepSeek: OpenAI-compatible `delta` with `reasoning_content` or `content`
- Gemini: SDK handles streaming internally, different for REST

**Prevention:**
1. Normalize SSE events at backend before sending to frontend
2. Use consistent event names: `thinking`, `content`, `complete`, `error`
3. Frontend receives unified format regardless of provider

**Phase to address:** Phase 2 - Streaming normalization layer

---

## Phase-Specific Warnings

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|---------------|------------|
| 1 | Provider abstraction | Pitfall 2 (Base URL), Pitfall 3 (Parameters) | Strict validation on client init |
| 2 | Streaming | Pitfall 4 (Timeouts), Pitfall 13 (SSE format) | Heartbeats, unified event format |
| 3 | Conversation state | Pitfall 5 (Gemini signatures), Pitfall 9 (Claude thinking blocks) | Provider-specific state handling |
| 4 | Error handling | Pitfall 8 (Rate limits), Pitfall 11 (Error formats) | Circuit breakers, error normalization |
| 5 | Token tracking | Pitfall 6 (Token counting), Pitfall 7 (Thinking billing) | Provider-specific tracking, user visibility |

---

## Provider-Specific Quick Reference

### Claude Integration Checklist
- [ ] Use `thinking_delta` events in streaming
- [ ] Pass `signature` field back in multi-turn
- [ ] Preserve thinking blocks during tool use
- [ ] Don't set `temperature` when thinking enabled
- [ ] Track summarized vs actual thinking tokens separately

### Gemini Integration Checklist
- [ ] Use SDK >= 1.51.0 for thinking features
- [ ] Set `include_thoughts: true` to access thinking
- [ ] Preserve thought signatures for multi-turn
- [ ] Check `part.thought` boolean to identify thinking vs answer
- [ ] Handle `thinking_level` parameter correctly

### DeepSeek Integration Checklist
- [ ] Set `base_url="https://api.deepseek.com"` on client
- [ ] Use `deepseek-reasoner` for thinking mode
- [ ] Handle `reasoning_content` separately from `content`
- [ ] Don't pass `reasoning_content` back in conversation history
- [ ] Implement robust retry for server busy (503) errors

---

## Sources

### Official Documentation (HIGH confidence)
- [Claude Extended Thinking](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking)
- [DeepSeek Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode)
- [Gemini Thinking](https://ai.google.dev/gemini-api/docs/thinking)
- [DeepSeek Error Codes](https://api-docs.deepseek.com/quick_start/error_codes)

### Technical Resources (MEDIUM confidence)
- [LLM Streaming SSE Guide](https://dev.to/pockit_tools/the-complete-guide-to-streaming-llm-responses-in-web-applications-from-sse-to-real-time-ui-3534)
- [Resumable LLM Streams](https://upstash.com/blog/resumable-llm-streams)
- [Retry/Fallback Patterns](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/)
- [Multi-LLM Gateway Patterns](https://www.truefoundry.com/blog/llm-gateway)

### Community/Blog (LOW confidence - verify before implementing)
- [DeepSeek Troubleshooting](https://www.byteplus.com/en/topic/375031)
- [Token Counting Differences](https://github.com/sujankapadia/token-counter)
