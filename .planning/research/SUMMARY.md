# Research Summary: Multi-LLM Provider Integration (v1.8)

**Project:** BA Assistant - Multi-Provider Support
**Synthesized:** 2026-01-31
**Overall Confidence:** HIGH

---

## Executive Summary

Adding multi-LLM provider support (Claude, Gemini 3 Flash Preview, DeepSeek V3.2 Reasoner) to BA Assistant is a well-understood domain with established patterns. The core challenge is building a proper abstraction layer that normalizes the significant differences in thinking/reasoning mode output formats across providers. The existing Anthropic integration provides a solid foundation - the `sse-starlette` streaming infrastructure remains unchanged, and all three providers support async streaming suitable for the current SSE-based frontend architecture.

The recommended approach is an adapter pattern with a factory for provider instantiation. Each provider has unique characteristics: Claude's extended thinking returns `thinking` blocks requiring preservation during tool use; Gemini's thinking mode requires signature passback for multi-turn context; DeepSeek uses the OpenAI SDK with a custom base URL and separates `reasoning_content` from `content`. The abstraction layer must normalize these differences so the frontend receives a unified stream format regardless of provider.

Key risks center on response format divergence (each provider structures thinking output differently), timeout handling (thinking can delay first token by 30+ seconds), and multi-turn state management (Gemini signatures, Claude thinking blocks). Mitigation requires building response normalization into the adapter layer from day one, implementing SSE heartbeats for long-running requests, and provider-specific conversation state handlers. The cost differential is significant - DeepSeek is 10-30x cheaper than Claude, making this feature valuable for cost optimization.

---

## Key Findings

### From STACK.md

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| `google-genai>=1.51.0` | Gemini 3 API | Required for `thinking_config`; deprecated `google-generativeai` is EOL |
| `openai>=2.16.0` | DeepSeek API | OpenAI-compatible SDK with custom `base_url` |
| `anthropic>=0.76.0` | Claude API | Already integrated, continue using |

**Critical:** Do NOT use `google-generativeai` (EOL Nov 2025) or third-party DeepSeek packages. Use official SDKs only.

### From FEATURES.md

| Category | Features |
|----------|----------|
| **Must Have (Table Stakes)** | Global default model in settings, per-conversation model binding, model selector at conversation start, visual model indicator, model persistence on return, API key management (BYOK), provider availability indication |
| **Should Have (Differentiators)** | Cost indicator per model, capability tags |
| **Defer to Post-v1.8** | Quick model switcher mid-conversation, multi-model comparison, automatic model selection, token/cost tracking per model |

**Anti-Features (Explicitly Avoid):**
- Mid-conversation model switching without warning
- Automatic model downgrade without consent
- Provider-specific feature parity assumptions
- Complex model routing rules
- Real-time pricing API integration
- Cross-provider conversation migration

### From ARCHITECTURE.md

| Component | Responsibility |
|-----------|----------------|
| `LLMAdapter` (abstract) | Unified streaming interface with `stream_chat()`, `normalize_messages()`, `normalize_tools()` |
| `AnthropicAdapter` | Existing Claude logic extracted to adapter pattern |
| `GeminiAdapter` | Google GenAI SDK with thinking level configuration |
| `DeepSeekAdapter` | OpenAI SDK with custom base_url, reasoning_content handling |
| `LLMFactory` | Provider instantiation with API key lookup |
| `StreamChunk` | Normalized streaming response dataclass |

**Database Changes:**
- Add `model_provider` (string) and `model_name` (string) columns to `threads` table
- Optional: `user_preferences` table for default provider

**Key Pattern:** Backend normalizes ALL provider responses to `StreamChunk` format before SSE; frontend treats all providers identically.

### From PITFALLS.md

| Severity | Count | Key Issues |
|----------|-------|------------|
| **Critical** | 5 | Thinking format divergence, DeepSeek base URL, parameter incompatibility, streaming timeouts, Gemini thought signatures |
| **Moderate** | 5 | Token counting variance, thinking token billing, rate limit differences, Claude thinking block preservation, SDK version mismatches |
| **Minor** | 3 | Error format differences, model name variations, SSE event format differences |

---

## Critical Pitfalls to Address

### 1. Thinking Mode Response Format Divergence (Phase 1)

**Problem:** Claude uses `thinking` blocks, Gemini uses `thought` boolean on parts, DeepSeek uses `reasoning_content` field. Parsing failures and UI crashes when switching models.

**Prevention:** Create provider-specific response normalizers BEFORE building unified streaming. Define canonical internal format that ALL providers map to. Test with actual API responses.

### 2. DeepSeek Base URL Configuration (Phase 1)

**Problem:** DeepSeek uses OpenAI SDK but requires `base_url="https://api.deepseek.com"`. Without it, requests go to OpenAI and fail with 401.

**Prevention:** Use provider-specific client factory pattern. Validate base_url in configuration validation on startup.

### 3. Streaming Timeout and Connection Handling (Phase 2)

**Problem:** Extended thinking can take 30+ seconds before first token. Standard 30s HTTP timeouts kill connection, losing entire response.

**Prevention:** Increase backend timeout to 5+ minutes for thinking requests. Implement SSE heartbeats every 15 seconds. Show "thinking..." indicator before first token.

### 4. Gemini Thought Signatures in Multi-Turn (Phase 3)

**Problem:** Gemini requires "thought signatures" to maintain reasoning context across turns. Dropping these breaks multi-turn thinking conversations.

**Prevention:** Store complete Gemini response parts (don't strip metadata). Pass back entire response with all parts in follow-up requests. Use official Python SDK.

### 5. Claude Extended Thinking Block Preservation (Phase 3)

**Problem:** Claude requires passing back `thinking` blocks when using tools. Stripping them breaks reasoning continuity.

**Prevention:** NEVER strip thinking blocks during tool use loops. Store complete response including all content blocks. Test tool use + thinking combinations explicitly.

---

## Recommended Phase Structure

Based on combined architecture and pitfall analysis, the following phase structure addresses dependencies and critical pitfalls in logical order:

### Phase 1: Backend Abstraction Layer

**Rationale:** Must establish provider abstraction before any other work. Addresses Pitfall 1 (format divergence), Pitfall 2 (base URL), Pitfall 3 (parameters), Pitfall 10 (SDK versions).

**Delivers:**
- LLMAdapter abstract base class with StreamChunk dataclass
- AnthropicAdapter (extract from current ai_service.py)
- LLMFactory with API key validation
- Configuration updates (new API keys in config.py, .env.example)
- Provider-specific parameter sanitization

**Features:** Foundation for TS-06 (API key management), TS-07 (provider availability)

**Research Needed:** No - well-documented patterns in ARCHITECTURE.md

### Phase 2: Database Schema and API Updates

**Rationale:** Thread model must support provider before frontend can select/display. Addresses Pitfall 4 (streaming timeouts), Pitfall 13 (SSE format).

**Delivers:**
- Alembic migration adding `model_provider`, `model_name` to threads
- Updated Thread model and Pydantic schemas
- Thread creation API accepts provider/model
- Chat endpoint uses Thread's provider to select adapter
- SSE heartbeat implementation for long-running requests

**Features:** TS-02 (per-conversation binding), TS-05 (persistence on return)

**Research Needed:** No - standard Alembic/SQLAlchemy patterns

### Phase 3: Additional Provider Adapters

**Rationale:** With abstraction layer proven, add new providers. Addresses Pitfall 5 (Gemini signatures), Pitfall 9 (Claude thinking blocks).

**Delivers:**
- GeminiAdapter with thinking_level configuration
- DeepSeekAdapter with reasoning_content handling
- Provider-specific conversation state management
- Integration tests for all three providers

**Features:** Multi-provider capability for TS-03 (model selector)

**Research Needed:** Maybe - verify Gemini thinking signature passback implementation details

### Phase 4: Frontend Provider Selection

**Rationale:** Backend is complete; frontend can now display and select providers.

**Delivers:**
- Updated Flutter Thread model with provider fields
- ProviderSelector widget
- ThreadCreateDialog with provider/model dropdown
- Model indicator in ConversationScreen AppBar
- Settings screen default provider selection

**Features:** TS-01 (global default), TS-03 (model selector), TS-04 (visual indicator)

**Research Needed:** No - standard Flutter widget patterns

### Phase 5: Error Handling and Polish

**Rationale:** Production hardening after core functionality complete. Addresses Pitfall 8 (rate limits), Pitfall 11 (error formats).

**Delivers:**
- Per-provider error normalization
- Exponential backoff with jitter
- Circuit breaker per provider
- Rate limit tracking
- End-to-end testing for all providers

**Features:** Production-ready multi-provider support

**Research Needed:** No - standard resilience patterns

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official SDK documentation is comprehensive; clear version requirements |
| Features | HIGH | Competitor analysis from established products (Open WebUI, TypingMind, ChatGPT) |
| Architecture | HIGH | Adapter pattern well-suited; existing codebase analyzed for integration points |
| Pitfalls | HIGH | Based on official provider documentation and known API behaviors |

### Gaps to Address During Planning

1. **Gemini thinking signature passback:** Documented in principle but implementation details may need verification with actual API testing
2. **DeepSeek server capacity:** Documentation notes frequent 503 errors due to capacity constraints - may need fallback strategy
3. **Claude thinking + tool use combination:** May need testing to confirm block preservation requirements with current Claude model

---

## Implications for Roadmap

### Phase Structure Recommendation

5 phases over approximately 8 days:
1. Backend Abstraction Layer (2 days)
2. Database Schema and API Updates (1 day)
3. Additional Provider Adapters (2 days)
4. Frontend Provider Selection (2 days)
5. Error Handling and Polish (1 day)

### Research Flags

| Phase | Research Needed | Rationale |
|-------|-----------------|-----------|
| Phase 1 | No | Adapter pattern is well-documented |
| Phase 2 | No | Standard database migration |
| Phase 3 | Maybe | Gemini signature passback may need verification |
| Phase 4 | No | Standard Flutter patterns |
| Phase 5 | No | Standard resilience patterns |

### Critical Success Factors

1. **Abstraction first:** Do not add new providers until adapter interface is proven with extracted Anthropic logic
2. **Response normalization:** All providers must produce identical StreamChunk format before SSE emission
3. **Timeout handling:** SSE heartbeats are mandatory for thinking-enabled requests
4. **State preservation:** Provider-specific conversation state handlers for multi-turn thinking

### Cost Optimization Opportunity

The 10-30x cost difference between DeepSeek and Claude makes provider selection a significant cost lever. Consider making DeepSeek the default for simple tasks and Claude for complex reasoning (user-controlled, not automatic).

---

## Aggregated Sources

### Official Documentation (HIGH confidence)
- [Google GenAI SDK Documentation](https://googleapis.github.io/python-genai/)
- [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [DeepSeek API Docs](https://api-docs.deepseek.com/)
- [DeepSeek Reasoning Model](https://api-docs.deepseek.com/guides/reasoning_model)
- [Claude Extended Thinking](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking)
- [OpenAI Python SDK](https://github.com/openai/openai-python)

### Feature Research (HIGH confidence)
- [Open WebUI Documentation](https://docs.openwebui.com/features/chat-features/)
- [TypingMind Feature List](https://docs.typingmind.com/feature-list)
- [ChatGPT Model Selector](https://help.openai.com/en/articles/7864572-what-is-the-chatgpt-model-selector)

### Architecture Patterns (MEDIUM confidence)
- [LiteLLM - Multi-Provider Interface](https://docs.litellm.ai/docs/)
- [Multi-LLM Systems with Abstract Classes](https://medium.com/algomart/multi-llm-systems-with-abstract-classes-in-python-038cd6ce78d5)

### Deprecation Notices (HIGH confidence)
- [Deprecated generative-ai-python](https://github.com/google-gemini/deprecated-generative-ai-python) - EOL Nov 2025

---

*Synthesis completed 2026-01-31. Ready for roadmap creation.*
