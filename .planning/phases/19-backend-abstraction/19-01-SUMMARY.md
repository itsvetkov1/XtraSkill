---
phase: 19-backend-abstraction
plan: 01
subsystem: backend-llm
tags: [adapter-pattern, abstraction, anthropic, streaming, factory]
dependency-graph:
  requires: []
  provides: [LLM abstraction layer, AnthropicAdapter, StreamChunk dataclass, LLMFactory]
  affects: [Phase 20 integration, Phase 21 additional adapters]
tech-stack:
  added: []
  patterns: [adapter pattern, factory pattern, abstract base class, dataclass]
key-files:
  created:
    - backend/app/services/llm/__init__.py
    - backend/app/services/llm/base.py
    - backend/app/services/llm/anthropic_adapter.py
    - backend/app/services/llm/factory.py
  modified: []
decisions:
  - id: DEC-19-01-01
    choice: Adapter yields StreamChunk, tool loop stays in AIService
    rationale: Single API call per adapter invocation, orchestration remains in AIService
  - id: DEC-19-01-02
    choice: Include thinking_content field in StreamChunk but always None for Anthropic
    rationale: Prepares for future providers (Gemini, DeepSeek) without over-abstracting
metrics:
  duration: 8 minutes
  completed: 2026-01-31
---

# Phase 19 Plan 01: LLM Provider Abstraction Layer Summary

Adapter pattern with StreamChunk dataclass, LLMFactory, and AnthropicAdapter extracted from ai_service.py.

## What Was Done

### Task 1: Create LLM Base Module with Abstractions

Created `backend/app/services/llm/` package with:

1. **LLMProvider enum** with ANTHROPIC value (extensible for future providers)
2. **StreamChunk dataclass** with fields:
   - `chunk_type`: "text", "thinking", "tool_use", "tool_result", "complete", "error"
   - `content`: Text content for text chunks
   - `thinking_content`: Reserved for future providers (always None for Anthropic)
   - `tool_call`: For tool_use chunks: {"id", "name", "input"}
   - `usage`: For complete chunks: {"input_tokens", "output_tokens"}
   - `error`: For error chunks
3. **LLMAdapter ABC** with:
   - `provider` property (abstract)
   - `stream_chat()` method (abstract async generator)

### Task 2: Create AnthropicAdapter Implementation

Extracted streaming logic from `ai_service.py` into `AnthropicAdapter`:

1. **Initialization** with api_key and optional model override
2. **stream_chat()** implementation:
   - Streams text chunks using `stream.text_stream`
   - Yields tool_use chunks from final message content
   - Yields complete chunk with usage statistics
   - Handles Anthropic API errors and unexpected exceptions
3. **Key difference from current ai_service.py:**
   - NO while True loop (single API call only)
   - NO tool execution (just yields tool_use chunks)
   - NO SSE event formatting (yields StreamChunk objects)

### Task 3: Create LLMFactory

Created factory class for adapter instantiation:

1. **create(provider, model)** method:
   - Validates provider name against LLMProvider enum
   - Retrieves API key from settings
   - Instantiates appropriate adapter class
2. **list_providers()** method returns supported provider names
3. **Private _adapters registry** maps LLMProvider to adapter class

## Commits

| Commit | Description |
|--------|-------------|
| 8a7d048 | feat(19-01): create LLM base module with abstractions |
| e750c0b | feat(19-01): create AnthropicAdapter implementation |
| 814c29d | feat(19-01): create LLMFactory |

## Verification

- [x] LLM package exists at `backend/app/services/llm/`
- [x] LLMAdapter ABC defines provider property and stream_chat method
- [x] StreamChunk dataclass has all required fields (chunk_type, content, thinking_content, tool_call, usage, error)
- [x] LLMProvider enum has ANTHROPIC value
- [x] AnthropicAdapter implements LLMAdapter, yields StreamChunk from Anthropic API
- [x] LLMFactory.create("anthropic") returns AnthropicAdapter instance
- [x] All imports work without errors
- [x] Line counts meet minimums: base.py (130 > 50), factory.py (118 > 25), anthropic_adapter.py (129 > 80)
- [x] Key links verified: factory imports AnthropicAdapter, AnthropicAdapter inherits LLMAdapter

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Phase 20 (ai_service integration) can now:
- Import `LLMFactory` and `StreamChunk` from `app.services.llm`
- Create adapter via `LLMFactory.create("anthropic")`
- Replace direct Anthropic SDK calls with adapter.stream_chat()
- Convert StreamChunk to SSE events in route handler

---

*Summary created: 2026-01-31*
*Plan duration: 8 minutes*
