# Phase 21: Provider Adapters - Research

**Researched:** 2026-01-31
**Domain:** LLM Provider Integration (Gemini, DeepSeek)
**Confidence:** HIGH

## Summary

This phase implements Gemini and DeepSeek adapters following the existing adapter pattern established in Phase 19. The existing codebase provides a clean `LLMAdapter` base class, `StreamChunk` dataclass, and `LLMFactory` registry that new adapters will extend.

**Gemini** uses the `google-genai` SDK (the current standard as of 2025, replacing deprecated `google-generativeai`). It supports async streaming via `client.aio.models.generate_content_stream()`. The model `gemini-3-flash-preview` has configurable thinking levels but thinking content is accessed via `include_thoughts=True` in the thinking config.

**DeepSeek** uses the OpenAI SDK with `base_url="https://api.deepseek.com"`. The `deepseek-reasoner` model returns reasoning in a separate `reasoning_content` field during streaming. Critical limitation: `reasoning_content` must NOT be included in subsequent messages or the API returns 400.

**Primary recommendation:** Implement both adapters following the AnthropicAdapter pattern exactly. Both adapters will hide thinking/reasoning content per user decision (CONTEXT.md). Tool/function calling works differently per provider but follows similar patterns to Anthropic.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-genai | latest | Gemini API access | Official Google SDK (GA since May 2025) |
| openai | existing | DeepSeek API access | DeepSeek is OpenAI-compatible |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | existing | HTTP client for google-genai | Default transport, already in deps |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| google-genai | google-generativeai | Legacy, deprecated Nov 2025, don't use |
| openai for DeepSeek | httpx/aiohttp | More code, less compatibility, no benefit |

**Installation:**
```bash
pip install google-genai
# openai already installed for potential future OpenAI support
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/services/llm/
├── base.py              # LLMAdapter, StreamChunk, LLMProvider (existing)
├── anthropic_adapter.py # AnthropicAdapter (existing)
├── gemini_adapter.py    # NEW: GeminiAdapter
├── deepseek_adapter.py  # NEW: DeepSeekAdapter
├── factory.py           # LLMFactory - add new registrations
└── __init__.py          # Export new adapters
```

### Pattern 1: Adapter Implementation Pattern (from existing AnthropicAdapter)
**What:** Each adapter implements `LLMAdapter.stream_chat()` yielding `StreamChunk` objects
**When to use:** All provider implementations
**Example:**
```python
# Source: backend/app/services/llm/anthropic_adapter.py (existing)
class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL
        # Create client with api_key

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GOOGLE

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        # Yield StreamChunk objects
        pass
```

### Pattern 2: Error Handling with Provider-Specific Messages
**What:** Catch provider-specific exceptions, yield StreamChunk with descriptive error
**When to use:** All error paths in adapters
**Example:**
```python
# Per CONTEXT.md decision: Show full error details with provider name + error code
except google_errors.APIError as e:
    yield StreamChunk(
        chunk_type="error",
        error=f"Gemini error ({e.code}): {e.message}",
    )
except openai.RateLimitError as e:
    yield StreamChunk(
        chunk_type="error",
        error=f"DeepSeek rate limit exceeded (429): {str(e)}",
    )
```

### Pattern 3: Simple Retry with Fixed Delay
**What:** 2 retries (3 total attempts) with fixed delay for transient errors
**When to use:** Rate limits (429), server errors (500, 503)
**Example:**
```python
# Per CONTEXT.md: 2 retries, fixed delay, same treatment for all transient errors
MAX_RETRIES = 2
RETRY_DELAY = 1.0  # seconds - Claude's discretion

for attempt in range(MAX_RETRIES + 1):
    try:
        async for chunk in self._stream_impl(...):
            yield chunk
        return  # Success, exit retry loop
    except TransientError as e:
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)
            continue
        yield StreamChunk(chunk_type="error", error=f"...")
```

### Anti-Patterns to Avoid
- **Including reasoning_content in DeepSeek messages:** API returns 400 error. Strip before subsequent calls.
- **Using deprecated google-generativeai:** End-of-life Nov 2025, use google-genai instead.
- **Exponential backoff for simple retries:** CONTEXT.md specifies fixed delay, keep it simple.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Gemini streaming | Custom HTTP/websocket | `client.aio.models.generate_content_stream()` | Handles chunking, errors, auth |
| DeepSeek API calls | Custom HTTP client | OpenAI SDK with base_url override | Full compatibility, retry logic |
| Tool schema conversion | Custom converter | Pass Anthropic format, minor adjustments | Similar structure across providers |
| Token counting | Custom estimation | Provider's usage_metadata | Accurate, includes thinking tokens |

**Key insight:** Both SDKs handle the complexity of streaming, authentication, and error formatting. Focus adapter code on normalization to StreamChunk format only.

## Common Pitfalls

### Pitfall 1: DeepSeek reasoning_content in Multi-turn
**What goes wrong:** Including `reasoning_content` field in subsequent messages causes 400 error
**Why it happens:** DeepSeek explicitly forbids passing previous reasoning back to the model
**How to avoid:** When building messages for next turn, use only `content` field, never `reasoning_content`
**Warning signs:** 400 "Invalid request" errors on second message in conversation

### Pitfall 2: Using Wrong Gemini SDK
**What goes wrong:** `google-generativeai` code fails or uses deprecated patterns
**Why it happens:** Training data includes old SDK patterns
**How to avoid:** Use `google-genai` SDK with `Client()` pattern, not `genai.GenerativeModel()`
**Warning signs:** Import errors, deprecated warnings, missing async support

### Pitfall 3: Gemini Streaming + Function Calling
**What goes wrong:** Attempting to use tools with `generate_content_stream()` fails
**Why it happens:** As of 2025, Gemini does NOT support streaming with tool/function calling for standard models
**How to avoid:** For tool use, use non-streaming `generate_content()` or Live API
**Warning signs:** Empty tool_calls, unexpected behavior during streaming with tools

### Pitfall 4: DeepSeek Unsupported Parameters
**What goes wrong:** Setting temperature, top_p, etc. on deepseek-reasoner has no effect
**Why it happens:** Reasoning model ignores these parameters (documented limitation)
**How to avoid:** Don't pass these parameters, or accept they'll be ignored
**Warning signs:** Same outputs regardless of temperature setting

### Pitfall 5: Gemini Thinking Level vs Thinking Budget
**What goes wrong:** Using `thinking_budget` with Gemini 3 models
**Why it happens:** Gemini 3 uses `thinking_level` (minimal/low/medium/high), not `thinking_budget` (token count)
**How to avoid:** Use `thinking_level="high"` for gemini-3-flash-preview per CONTEXT.md "heavy thinking"
**Warning signs:** Unexpected reasoning depth, parameter ignored warnings

## Code Examples

Verified patterns from official sources:

### Gemini Async Streaming (without thinking output per CONTEXT.md)
```python
# Source: https://googleapis.github.io/python-genai/
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)

# For streaming without capturing thinking (per CONTEXT.md decision)
async for chunk in await client.aio.models.generate_content_stream(
    model="gemini-3-flash-preview",
    contents=contents,
    config=types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=max_tokens,
        thinking_config=types.ThinkingConfig(thinking_level="high")
        # Note: NOT including include_thoughts=True per decision to hide thinking
    ),
):
    if chunk.text:
        yield StreamChunk(chunk_type="text", content=chunk.text)

# Access usage after streaming completes
# Note: May need to track final chunk for usage_metadata
```

### Gemini Error Handling
```python
# Source: https://googleapis.github.io/python-genai/
from google.genai import errors

try:
    async for chunk in await client.aio.models.generate_content_stream(...):
        yield StreamChunk(chunk_type="text", content=chunk.text)
except errors.APIError as e:
    yield StreamChunk(
        chunk_type="error",
        error=f"Gemini error ({e.code}): {e.message}",
    )
```

### DeepSeek Streaming with Reasoning (hidden per CONTEXT.md)
```python
# Source: https://api-docs.deepseek.com/guides/reasoning_model
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

stream = await client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages,
    stream=True
)

async for chunk in stream:
    delta = chunk.choices[0].delta
    # Per CONTEXT.md: Hide reasoning_content, only yield content
    if delta.reasoning_content:
        # Optional: Could store in database per Claude's discretion
        pass  # Skip yielding thinking content
    elif delta.content:
        yield StreamChunk(chunk_type="text", content=delta.content)
```

### DeepSeek Function Calling
```python
# Source: https://api-docs.deepseek.com/guides/function_calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "Tool description",
            "parameters": {...}
        }
    }
]

response = await client.chat.completions.create(
    model="deepseek-chat",  # Note: Use deepseek-chat for tools, not deepseek-reasoner
    messages=messages,
    tools=tools,
    stream=True
)

# Tool calls come in message.tool_calls
```

### Gemini Function Calling (non-streaming required)
```python
# Source: https://ai.google.dev/gemini-api/docs/function-calling
# WARNING: As of 2025, streaming + function calling NOT supported
# Must use non-streaming for tool use

response = await client.aio.models.generate_content(
    model="gemini-3-flash-preview",
    contents=contents,
    config=types.GenerateContentConfig(
        tools=[...],  # Tool definitions
    ),
)

# Access function calls from response
for part in response.candidates[0].content.parts:
    if hasattr(part, 'function_call') and part.function_call:
        yield StreamChunk(
            chunk_type="tool_use",
            tool_call={
                "id": part.function_call.id,
                "name": part.function_call.name,
                "input": dict(part.function_call.args),
            }
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| google-generativeai SDK | google-genai SDK | May 2025 GA | Different API patterns, async support |
| `model.generate_content(stream=True)` | `client.models.generate_content_stream()` | 2025 | Method name and client pattern |
| Gemini thinking_budget | Gemini 3 thinking_level | Dec 2025 | Different parameter for new models |
| DeepSeek separate reasoner | V3.2 unified model | Dec 2025 | deepseek-reasoner is now V3.2 thinking mode |

**Deprecated/outdated:**
- google-generativeai: EOL Nov 2025, use google-genai
- genai.GenerativeModel(): Use Client() pattern instead
- thinking_budget for Gemini 3: Use thinking_level parameter

## Open Questions

Things that couldn't be fully resolved:

1. **Gemini streaming + tools limitation scope**
   - What we know: Documentation says streaming doesn't support tools for "regular models"
   - What's unclear: Does this apply to gemini-3-flash-preview? Is Live API the only streaming+tools option?
   - Recommendation: Implement non-streaming fallback for tool use in Gemini adapter

2. **Gemini usage_metadata in streaming**
   - What we know: Non-streaming returns usage_metadata with token counts
   - What's unclear: How to reliably get final token count from streaming response
   - Recommendation: May need to track chunks and get usage from final chunk

3. **DeepSeek function calling stability**
   - What we know: Documentation notes "Function Calling capability is unstable, may result in looped calls or empty responses"
   - What's unclear: How reliable is it in practice with deepseek-reasoner vs deepseek-chat?
   - Recommendation: Use deepseek-chat for tool calls, monitor for issues

## Sources

### Primary (HIGH confidence)
- [Google GenAI SDK Documentation](https://googleapis.github.io/python-genai/) - Async streaming, error handling, client patterns
- [DeepSeek API Docs - Reasoning Model](https://api-docs.deepseek.com/guides/reasoning_model) - Streaming with reasoning_content
- [DeepSeek API Docs - Error Codes](https://api-docs.deepseek.com/quick_start/error_codes) - Error handling, retry guidance
- [Gemini Thinking Documentation](https://ai.google.dev/gemini-api/docs/thinking) - ThinkingLevel, include_thoughts
- Existing codebase: `backend/app/services/llm/` - Adapter pattern, StreamChunk format

### Secondary (MEDIUM confidence)
- [Gemini API Function Calling](https://ai.google.dev/gemini-api/docs/function-calling) - Tool definitions, response format
- [DeepSeek Function Calling](https://api-docs.deepseek.com/guides/function_calling) - OpenAI-compatible tools
- [Google Gemini API Troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting) - Error codes 400, 401, 403, 429

### Tertiary (LOW confidence)
- WebSearch results on streaming + tools limitation - Needs verification in implementation
- WebSearch results on Gemini streaming usage_metadata - May need experimentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation verified
- Architecture: HIGH - Based on existing working pattern (AnthropicAdapter)
- Pitfalls: HIGH - From official documentation limitations sections
- Tool calling patterns: MEDIUM - Gemini streaming+tools limitation needs verification

**Research date:** 2026-01-31
**Valid until:** ~30 days (both APIs actively evolving, Gemini 3 is preview)
