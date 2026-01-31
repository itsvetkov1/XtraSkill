---
phase: 21-provider-adapters
plan: 02
subsystem: llm-providers
tags: [deepseek, openai-sdk, streaming, async, adapter, reasoning]
dependency_graph:
  requires: [21-01-gemini-adapter]
  provides: [deepseek-adapter, deepseek-provider]
  affects: [22-provider-selection-ui]
tech_stack:
  added: []  # Uses existing openai package
  patterns: [openai-base-url-override, reasoning-content-hidden, retry-with-fixed-delay]
key_files:
  created:
    - backend/app/services/llm/deepseek_adapter.py
  modified:
    - backend/app/config.py
    - backend/app/services/llm/base.py
    - backend/app/services/llm/factory.py
    - backend/app/services/llm/__init__.py
decisions:
  - key: deepseek-model-default
    value: deepseek-reasoner
    rationale: Per CONTEXT.md - reasoning model for BA conversations
  - key: reasoning-hidden
    value: true
    rationale: Per CONTEXT.md - reasoning_content not exposed to user
  - key: retry-strategy
    value: 2-retries-1s-fixed-delay
    rationale: Per CONTEXT.md - simple retry, no exponential backoff
  - key: openai-sdk-reuse
    value: true
    rationale: DeepSeek is OpenAI-compatible, use existing SDK with base_url override
metrics:
  duration: 6 minutes
  completed: 2026-01-31
---

# Phase 21 Plan 02: DeepSeek Adapter Summary

DeepSeekAdapter implementation using OpenAI SDK with base_url override, reasoning hidden, retry logic.

## What Was Built

### DeepSeekAdapter (backend/app/services/llm/deepseek_adapter.py)
- **272 lines** implementing LLMAdapter interface
- Uses AsyncOpenAI with `base_url="https://api.deepseek.com"`
- Handles `reasoning_content` field but does NOT yield it (hidden per CONTEXT.md)
- Does NOT include reasoning_content in subsequent messages (would cause 400 error)
- Simple retry: 2 retries, 1 second fixed delay
- Provider-specific error messages: `DeepSeek error ({code}): {message}`

### Configuration
- `DEEPSEEK_API_KEY` environment variable for API authentication
- `DEEPSEEK_MODEL` environment variable for model override (default: deepseek-reasoner)
- `LLMProvider.DEEPSEEK` enum value added

### Factory Registration
- `LLMFactory.create("deepseek")` returns DeepSeekAdapter instance
- `LLMFactory.list_providers()` includes "deepseek"
- API key validation with helpful error message pointing to platform.deepseek.com

## Key Implementation Details

### Message Conversion
Converts Anthropic-format messages to OpenAI format:
- System prompt becomes first message with `role: "system"`
- Multi-part content blocks handled (text, tool_result)
- No reasoning_content passed in messages (API requirement)

### Tool Handling
Converts Anthropic tool format to OpenAI function calling format:
- `input_schema` becomes `parameters`
- Wrapped in `{"type": "function", "function": {...}}` structure
- Note: deepseek-reasoner tool support may be unstable per RESEARCH.md

### Error Handling
- `RateLimitError` caught with 429 status code in message
- `APIStatusError` caught with specific status code
- Retryable errors: 429, 500, 503
- Generic Exception fallback for unexpected errors

### Reasoning Content
Per CONTEXT.md decision: reasoning_content is completely hidden from users.
- `delta.reasoning_content` is checked but NOT yielded as StreamChunk
- Could optionally store in database for debugging (Claude's discretion - not implemented)

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| a2243b3 | feat | Create DeepSeekAdapter implementation |
| ae04c4c | feat | Register DeepSeek adapter in factory |

## Verification Results

All success criteria verified:
- [x] DEEPSEEK_API_KEY and DEEPSEEK_MODEL settings exist in config
- [x] LLMProvider.DEEPSEEK enum value exists
- [x] DeepSeekAdapter class implements LLMAdapter with stream_chat async generator
- [x] DeepSeekAdapter uses OpenAI SDK with base_url="https://api.deepseek.com"
- [x] DeepSeekAdapter registered in LLMFactory._adapters
- [x] LLMFactory.create("deepseek") returns DeepSeekAdapter instance (with API key check)
- [x] All imports work without errors

## Deviations from Plan

### Pre-existing Configuration

**Found:** Task 1 (Add DeepSeek configuration) was already complete in HEAD.

The commit `dbd4d8d` from 21-01 execution already added:
- `deepseek_api_key` and `deepseek_model` to config.py
- `LLMProvider.DEEPSEEK` enum value to base.py

The 21-01 commit message says "Gemini" but the changes included DeepSeek configuration proactively.

**Resolution:** Verified configuration exists, proceeded to Task 2.

**No fixes required** - Task 1 was essentially a no-op (already done).

## Next Phase Readiness

**Phase 21 Complete:** Both Gemini and DeepSeek adapters implemented.

**Ready for Phase 22:** Provider selection UI
- Three providers available: anthropic, google, deepseek
- Factory pattern established for provider creation
- All adapters normalize to StreamChunk format

**Testing note:** Full integration testing requires DEEPSEEK_API_KEY configuration. Manual testing deferred to user environment with valid API credentials.

---

*Completed: 2026-01-31*
*Duration: ~6 minutes*
