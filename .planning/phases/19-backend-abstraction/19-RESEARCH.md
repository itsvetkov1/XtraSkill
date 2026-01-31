# Phase 19: backend-abstraction - Research

**Researched:** 2026-01-31
**Domain:** Python adapter pattern for LLM provider abstraction
**Confidence:** HIGH

## Summary

Phase 19 establishes the foundation for multi-LLM provider support by extracting the existing Anthropic Claude integration into an adapter pattern. The current implementation in `backend/app/services/ai_service.py` is a single-provider design with direct Anthropic SDK calls, hardcoded model names, and Anthropic-specific streaming logic. This phase refactors that into an abstract `LLMAdapter` base class with an `AnthropicAdapter` implementation, a `LLMFactory` for instantiation, and a `StreamChunk` dataclass for normalized response format.

The existing codebase is well-structured for this refactoring. The `AIService` class handles streaming, tool execution, and SSE event generation. The adapter pattern will preserve this structure while abstracting provider-specific details. The `StreamChunk` dataclass must normalize: text content, thinking/reasoning content (for future providers), usage statistics, and errors.

**Primary recommendation:** Extract `AIService.stream_chat()` logic into `AnthropicAdapter.stream_chat()`, create abstract `LLMAdapter` base class, and wire `LLMFactory` into the existing route without changing the SSE contract to frontend.

## Current Implementation Analysis

### File Locations

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/services/ai_service.py` | Claude API integration, streaming, tool execution | ~760 |
| `backend/app/routes/conversations.py` | SSE endpoint, message persistence | ~230 |
| `backend/app/services/conversation_service.py` | Context building, token estimation | ~165 |
| `backend/app/config.py` | Settings including `anthropic_api_key` | Varies |
| `backend/app/models.py` | Database models (Thread, Message) | ~395 |

### Current Flow

```
POST /threads/{thread_id}/chat
    |
    v
conversations.py:stream_chat()
    |
    v
AIService.stream_chat(messages, project_id, thread_id, db)
    |
    +---> anthropic.AsyncAnthropic.messages.stream()
    |         |
    |         v
    |     text_stream yields text chunks
    |         |
    |         v
    |     Yields SSE events: text_delta, tool_executing, artifact_created, message_complete, error
    |
    v
EventSourceResponse to frontend
```

### Anthropic-Specific Coupling Points

1. **Model Constant (line 14)**:
   ```python
   MODEL = "claude-sonnet-4-5-20250929"
   ```

2. **Client Instantiation (lines 592-593)**:
   ```python
   self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
   ```

3. **Streaming Pattern (lines 672-688)**:
   ```python
   async with self.client.messages.stream(
       model=MODEL,
       max_tokens=4096,
       messages=messages,
       tools=self.tools,
       system=SYSTEM_PROMPT
   ) as stream:
       async for text in stream.text_stream:
           yield {"event": "text_delta", "data": json.dumps({"text": text})}
   ```

4. **Tool Use Detection (lines 692-704)**:
   ```python
   if final.stop_reason != "tool_use":
       # Done
   # Execute tools
   for block in final.content:
       if block.type == "tool_use":
           # Handle tool
   ```

5. **Error Handling (lines 753-761)**:
   ```python
   except anthropic.APIError as e:
       yield {"event": "error", ...}
   ```

### What Stays in ai_service.py

- `SYSTEM_PROMPT` - Business analyst skill prompt (provider-agnostic)
- `DOCUMENT_SEARCH_TOOL` - Tool definition (needs normalization for other providers)
- `SAVE_ARTIFACT_TOOL` - Tool definition (needs normalization for other providers)
- `execute_tool()` - Tool execution logic (provider-agnostic)

### What Moves to Adapter

- Model selection
- Client instantiation
- Message format conversion (if needed)
- Tool format conversion (for non-Anthropic providers)
- Streaming loop
- Stop reason detection
- Error type handling

## Standard Stack

### Core (No New Dependencies for Phase 19)

| Library | Version | Purpose | Already Installed |
|---------|---------|---------|-------------------|
| `anthropic` | `>=0.76.0` | Claude API client | Yes |
| Python stdlib | `abc` | Abstract base class | Yes |
| Python stdlib | `dataclasses` | StreamChunk definition | Yes |
| Python stdlib | `enum` | LLMProvider enum | Yes |
| Python stdlib | `typing` | Type hints | Yes |

Phase 19 requires NO new pip dependencies. The adapter pattern uses Python stdlib only.

### New Files to Create

```
backend/app/services/llm/
    __init__.py         # Package exports
    base.py             # LLMAdapter ABC, StreamChunk, LLMProvider enum
    anthropic_adapter.py # AnthropicAdapter implementation
    factory.py          # LLMFactory class
```

## Architecture Patterns

### Recommended Project Structure

```
backend/app/services/
    llm/                          # NEW: LLM provider abstraction
        __init__.py               # Exports: LLMAdapter, StreamChunk, LLMProvider, LLMFactory
        base.py                   # Abstract base class and dataclasses
        anthropic_adapter.py      # Anthropic implementation
        factory.py                # Factory for adapter creation
    ai_service.py                 # MODIFIED: Uses adapter, keeps tools + system prompt
    conversation_service.py       # UNCHANGED
```

### Pattern: Abstract Base Class with Factory

**What:** Define abstract `LLMAdapter` class with `stream_chat()` method. Factory instantiates correct adapter by provider string.

**When to use:** Multiple providers with similar interface but different implementation details.

**Example:**
```python
# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Dict, Any, List, Optional

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    # Future: GOOGLE = "google", DEEPSEEK = "deepseek"

@dataclass
class StreamChunk:
    """Normalized streaming response chunk."""
    chunk_type: str  # "text", "thinking", "tool_use", "tool_result", "complete", "error"
    content: str = ""
    thinking_content: Optional[str] = None
    tool_call: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None

class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""

    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Return the provider identifier."""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream chat response, yielding normalized StreamChunk objects."""
        pass
```

### Pattern: Provider Factory

**What:** Single class responsible for creating adapters by provider name.

**When to use:** Decouple adapter instantiation from usage.

**Example:**
```python
# factory.py
from .base import LLMAdapter, LLMProvider
from .anthropic_adapter import AnthropicAdapter
from app.config import settings

class LLMFactory:
    """Factory for creating LLM adapters."""

    _adapters = {
        LLMProvider.ANTHROPIC: AnthropicAdapter,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        model: Optional[str] = None,
    ) -> LLMAdapter:
        """Create adapter for specified provider."""
        provider_enum = LLMProvider(provider)
        adapter_class = cls._adapters.get(provider_enum)
        if not adapter_class:
            raise ValueError(f"Unsupported provider: {provider}")

        api_key = cls._get_api_key(provider_enum)
        return adapter_class(api_key=api_key, model=model)

    @classmethod
    def _get_api_key(cls, provider: LLMProvider) -> str:
        """Get API key from settings."""
        if provider == LLMProvider.ANTHROPIC:
            return settings.anthropic_api_key
        raise ValueError(f"No API key configured for {provider}")
```

### Anti-Patterns to Avoid

- **Direct SDK Usage in Routes:** Never call `anthropic.AsyncAnthropic()` in route handlers. Always use factory + adapter.

- **Provider-Specific SSE Events:** Do not create different event formats per provider. Normalize everything to StreamChunk before SSE emission.

- **Mixing Concerns:** Keep tool definitions and execution separate from provider-specific streaming logic.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Abstract base class | Custom metaclass | `abc.ABC` + `@abstractmethod` | Standard Python pattern, IDE support |
| Immutable data container | Regular class | `@dataclass` | Automatic `__init__`, `__eq__`, type hints |
| Provider enum | String constants | `Enum(str, Enum)` | Type safety, autocomplete, validation |
| Async iteration | Custom iterator | `AsyncGenerator[T, None]` | Standard typing, works with `async for` |

**Key insight:** Python stdlib provides all building blocks for the adapter pattern. No external libraries needed.

## Common Pitfalls

### Pitfall 1: Breaking SSE Contract

**What goes wrong:** Changing the SSE event format breaks the Flutter frontend.

**Why it happens:** Refactoring temptation to "clean up" event structure.

**How to avoid:** The existing SSE events (`text_delta`, `tool_executing`, `artifact_created`, `message_complete`, `error`) MUST remain unchanged. The adapter produces `StreamChunk` objects; the route handler converts to SSE.

**Warning signs:** Frontend stops receiving streaming updates after refactor.

### Pitfall 2: Losing Tool Use Loop

**What goes wrong:** Tool use conversation flow breaks because adapter doesn't handle multi-turn.

**Why it happens:** Current `AIService.stream_chat()` has a `while True` loop for tool use continuation.

**How to avoid:** Keep the tool use loop in `ai_service.py` or the route handler. Adapter only handles single API calls, not tool loops.

**Warning signs:** First tool call works, conversation ends prematurely.

### Pitfall 3: Over-Abstracting Too Early

**What goes wrong:** Adding methods for Gemini/DeepSeek features before they're needed.

**Why it happens:** Anticipating future needs without current requirements.

**How to avoid:** Extract ONLY what Anthropic needs now. Add `thinking_content` field to StreamChunk but don't implement it until Phase 21.

**Warning signs:** Abstract methods that return `NotImplemented`, unused parameters.

### Pitfall 4: Forgetting Type Hints

**What goes wrong:** Losing IDE autocomplete and type checking in refactored code.

**Why it happens:** Moving fast during extraction.

**How to avoid:** Every method signature must match the original type hints. Run `mypy` or IDE type checker before committing.

**Warning signs:** IDE shows `Any` types, missing parameter hints.

## StreamChunk Specification

### Required Fields for Phase 19

Based on current Anthropic integration and future provider needs:

```python
@dataclass
class StreamChunk:
    """
    Normalized streaming response chunk from any LLM provider.

    Used by route handler to generate SSE events.
    """

    chunk_type: str
    # One of: "text", "thinking", "tool_use", "tool_result", "complete", "error"

    content: str = ""
    # Text content for "text" chunks, error message for "error" chunks

    thinking_content: Optional[str] = None
    # Reserved for future: DeepSeek reasoning_content, Claude thinking blocks
    # Phase 19: Always None for Anthropic

    tool_call: Optional[Dict[str, Any]] = None
    # For "tool_use" chunks: {"id": str, "name": str, "input": dict}

    usage: Optional[Dict[str, int]] = None
    # For "complete" chunks: {"input_tokens": int, "output_tokens": int}

    error: Optional[str] = None
    # For "error" chunks: Error message string
```

### Mapping Current Events to StreamChunk

| Current SSE Event | StreamChunk | Fields Used |
|------------------|-------------|-------------|
| `text_delta` | `chunk_type="text"` | `content` |
| `tool_executing` | `chunk_type="tool_use"` | `tool_call` |
| `artifact_created` | Handled separately | N/A (route handler emits) |
| `message_complete` | `chunk_type="complete"` | `content`, `usage` |
| `error` | `chunk_type="error"` | `error` |

### Thinking Field Rationale

The `thinking_content` field exists in Phase 19 but is unused. This enables:
- Future Gemini adapter: `chunk_type="thinking"`, `thinking_content="..."`
- Future DeepSeek adapter: `reasoning_content` maps to `thinking_content`
- Future Claude extended thinking: `thinking` blocks map to `thinking_content`

## Code Locations

### Files to Modify

| File | Change | Reason |
|------|--------|--------|
| `backend/app/services/ai_service.py` | Import and use `AnthropicAdapter` via `LLMFactory` | Core refactoring |
| `backend/app/routes/conversations.py` | No changes if ai_service.py interface unchanged | Preserve contract |

### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/llm/__init__.py` | Package exports |
| `backend/app/services/llm/base.py` | LLMAdapter ABC, StreamChunk, LLMProvider |
| `backend/app/services/llm/anthropic_adapter.py` | AnthropicAdapter implementation |
| `backend/app/services/llm/factory.py` | LLMFactory class |

### Files to NOT Modify

| File | Reason |
|------|--------|
| `backend/app/models.py` | Phase 20 adds `model_provider` column |
| `backend/app/config.py` | Phase 21 adds new API keys |
| `frontend/*` | No frontend changes in Phase 19 |

## Recommendations

### Approach: Parallel Implementation Then Switch

1. **Create `llm/` package** with all new files alongside existing `ai_service.py`
2. **Implement AnthropicAdapter** that mirrors current streaming logic exactly
3. **Test adapter in isolation** (unit tests)
4. **Wire factory into ai_service.py** replacing direct Anthropic calls
5. **Verify no regression** in integration tests
6. **Verify frontend unchanged** in manual testing

### Success Criteria Verification

| Requirement | How to Verify |
|-------------|---------------|
| BACK-01: Adapter pattern abstracts provider API differences | `LLMAdapter` ABC exists with required methods |
| BACK-02: Anthropic adapter extracted from current implementation | `AnthropicAdapter` produces identical SSE events |
| BACK-06: StreamChunk normalizes response format | All streaming goes through StreamChunk dataclass |

### Testing Strategy

1. **Unit tests for adapter:**
   - Mock Anthropic client
   - Verify StreamChunk output for text, tools, completion, errors

2. **Integration tests:**
   - Real API call (requires API key)
   - Verify SSE event sequence matches current behavior

3. **Manual verification:**
   - Create thread, send message, receive streaming response
   - Use document search tool
   - Generate artifact
   - All flows work identically to before refactor

## Open Questions

None. This phase is well-defined with clear scope from existing codebase analysis and prior milestone research.

## Sources

### Primary (HIGH confidence)
- `backend/app/services/ai_service.py` - Current implementation analyzed
- `backend/app/routes/conversations.py` - SSE contract analyzed
- `.planning/research/ARCHITECTURE.md` - Adapter pattern design
- `.planning/research/SUMMARY.md` - Overall approach validated

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` - Common mistakes documented

### Python Patterns (HIGH confidence)
- Python `abc` module documentation
- Python `dataclasses` module documentation
- Python typing `AsyncGenerator` documentation

## Metadata

**Confidence breakdown:**
- Current implementation analysis: HIGH - Direct code review
- Adapter pattern design: HIGH - Standard Python pattern
- StreamChunk specification: HIGH - Based on actual SSE events
- File locations: HIGH - Direct code analysis

**Research date:** 2026-01-31
**Valid until:** Indefinite (refactoring existing code, no external API changes)

---

*Research complete. Ready for planning.*
