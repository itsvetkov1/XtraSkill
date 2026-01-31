# Technology Stack: Multi-LLM Provider Integration

**Project:** BA Assistant - Multi-Provider Support
**Researched:** 2026-01-31
**Overall Confidence:** HIGH

---

## Executive Summary

Adding Gemini 3 Flash Preview and DeepSeek V3.2 Reasoner alongside existing Anthropic Claude integration requires two new Python libraries. The DeepSeek API is OpenAI-compatible, so you reuse the `openai` SDK with a different `base_url`. Google Gemini uses the new unified `google-genai` SDK. All three providers support async streaming suitable for SSE delivery to the Flutter frontend.

**Key Finding:** The existing `sse-starlette` infrastructure remains unchanged. All providers stream chunks that can be converted to the same SSE event format currently used for Claude.

---

## Recommended Stack

### Core Libraries

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| `anthropic` | `>=0.76.0` (existing) | Claude API - already integrated | HIGH |
| `google-genai` | `>=1.51.0` | Gemini 3 Flash Preview API | HIGH |
| `openai` | `>=2.16.0` | DeepSeek API via OpenAI-compatible endpoint | HIGH |

### Version Rationale

| Library | Minimum Version | Why This Version |
|---------|-----------------|------------------|
| `google-genai` | 1.51.0 | Required for Gemini 3 thinking_config. Current: 1.61.0 |
| `openai` | 2.16.0 | Latest stable with AsyncOpenAI and streaming fixes. Python 3.9+ |

### Installation

```bash
# Add to requirements.txt
google-genai>=1.51.0
openai>=2.16.0

# Install
pip install google-genai>=1.51.0 openai>=2.16.0

# Optional: Faster async performance
pip install google-genai[aiohttp] openai[aiohttp]
```

---

## Provider Integration Details

### 1. Anthropic Claude (Existing)

**Status:** Already implemented in `backend/app/services/ai_service.py`

**Model:** `claude-sonnet-4-5-20250929`

**Authentication:**
```python
anthropic_api_key: str  # Already in config.py
```

**Streaming Pattern:**
```python
async with self.client.messages.stream(
    model=MODEL,
    max_tokens=4096,
    messages=messages,
    system=SYSTEM_PROMPT
) as stream:
    async for text in stream.text_stream:
        yield {"event": "text_delta", "data": json.dumps({"text": text})}
```

**Confidence:** HIGH - Already working in production.

---

### 2. Google Gemini 3 Flash Preview (New)

**Model:** `gemini-3-flash-preview`

**Context Window:** 1M tokens input, 64K tokens output

**Authentication:**
```python
# Environment variable
GEMINI_API_KEY=your_api_key_here

# Python
from google import genai
client = genai.Client(api_key=settings.gemini_api_key)
```

**Async Client Setup:**
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)
async_client = client.aio
```

**Streaming Pattern:**
```python
async for chunk in await client.aio.models.generate_content_stream(
    model='gemini-3-flash-preview',
    contents=user_message,
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        thinking_config=types.ThinkingConfig(thinking_level="medium")
    )
):
    yield {"event": "text_delta", "data": json.dumps({"text": chunk.text})}
```

**Thinking Levels:**
| Level | Use Case | Latency |
|-------|----------|---------|
| `minimal` | Simple tasks, fast responses | Lowest |
| `low` | Basic Q&A, instruction following | Low |
| `medium` | Moderate complexity, balanced | Medium |
| `high` | Complex reasoning (default) | Highest |

**Known Issue (as of Jan 2026):**
- Streaming + Tools combination may return empty responses in some cases
- Workaround: Use `stream=False` when tools are enabled, or test thoroughly

**Confidence:** HIGH - Official Google SDK, well-documented.

**Source:** [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3), [Google GenAI SDK](https://googleapis.github.io/python-genai/)

---

### 3. DeepSeek V3.2 Reasoner (New)

**Model:** `deepseek-reasoner` (thinking mode of V3.2)

**Authentication:**
```python
# Environment variable
DEEPSEEK_API_KEY=your_api_key_here

# Python - Uses OpenAI SDK with custom base_url
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com"
)
```

**Streaming Pattern:**
```python
response = await client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages,
    stream=True
)

async for chunk in response:
    delta = chunk.choices[0].delta
    if delta.reasoning_content:
        # Chain-of-thought reasoning (optional: stream to frontend)
        yield {"event": "thinking_delta", "data": json.dumps({"text": delta.reasoning_content})}
    elif delta.content:
        # Final answer
        yield {"event": "text_delta", "data": json.dumps({"text": delta.content})}
```

**Critical Behavior - Reasoning Content:**
- DeepSeek Reasoner outputs TWO streams: `reasoning_content` (CoT) and `content` (answer)
- The `reasoning_content` shows the model's thinking process
- **CRITICAL:** Never include `reasoning_content` in conversation history - returns 400 error
- Only append `content` to the message history for multi-turn conversations

**Unsupported Parameters (No Effect):**
- `temperature`
- `top_p`
- `presence_penalty`
- `frequency_penalty`

**Unsupported Features:**
- Function calling / tool use
- FIM completion

**Confidence:** HIGH - Uses battle-tested OpenAI SDK with well-documented API.

**Source:** [DeepSeek API Docs](https://api-docs.deepseek.com/guides/reasoning_model), [DeepSeek Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode)

---

## Configuration Changes

### backend/app/config.py Additions

```python
class Settings(BaseSettings):
    # Existing
    anthropic_api_key: str = ""

    # New for v1.8
    gemini_api_key: str = ""
    deepseek_api_key: str = ""
```

### backend/.env.example Additions

```bash
# AI Service - Multi-Provider (v1.8)
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
DEEPSEEK_API_KEY=your_deepseek_key
```

---

## Streaming Architecture Comparison

| Aspect | Anthropic | Gemini | DeepSeek |
|--------|-----------|--------|----------|
| SDK | `anthropic` | `google-genai` | `openai` |
| Async Class | `AsyncAnthropic` | `client.aio` | `AsyncOpenAI` |
| Stream Method | `messages.stream()` | `models.generate_content_stream()` | `chat.completions.create(stream=True)` |
| Chunk Access | `stream.text_stream` | `chunk.text` | `chunk.choices[0].delta.content` |
| Context Manager | Yes (`async with`) | No (async iterator) | No (async iterator) |
| Thinking Output | N/A | Configurable via `thinking_level` | `reasoning_content` field |
| Tool Support | Full | Partial (streaming issue) | None in reasoner mode |

---

## What NOT to Use

### Deprecated: `google-generativeai`

**Do NOT use:** `pip install google-generativeai`

**Why:** This package reached End-of-Life on November 30, 2025. It will not receive updates and does not support Gemini 3 models.

**Use instead:** `google-genai` (the new unified SDK)

**Source:** [Deprecated generative-ai-python](https://github.com/google-gemini/deprecated-generative-ai-python)

### Unofficial DeepSeek Packages

**Do NOT use:** `pip install deepseek-python` or similar third-party packages

**Why:**
1. DeepSeek officially recommends using the OpenAI SDK
2. Third-party packages may lag behind API changes
3. OpenAI SDK is battle-tested and well-maintained

**Use instead:** `openai` SDK with `base_url="https://api.deepseek.com"`

### LiteLLM (For This Use Case)

**Consider avoiding:** `litellm` for this implementation

**Why:**
1. Adds abstraction layer when direct SDKs work fine
2. Each provider has unique features (thinking_level, reasoning_content) that LiteLLM may abstract away
3. Direct SDKs give better control over streaming behavior
4. Debugging is easier with direct SDK calls

**When to use LiteLLM:** If you need to support 10+ providers with uniform interface and don't need provider-specific features.

---

## Requirements.txt Update

```
# Existing
fastapi[standard]>=0.115.0
anthropic==0.76.0
sqlalchemy>=2.0.35
alembic>=1.13.0
python-jose[cryptography]>=3.3.0
authlib>=1.3.0
cryptography>=43.0.0
pytest>=8.3.0
pytest-asyncio>=0.24.0
aiosqlite>=0.20.0
httpx>=0.27.0
sse-starlette>=2.0.0
python-docx==1.2.0
weasyprint==68.0
markdown>=3.5
jinja2>=3.1.0
claude-agent-sdk>=0.1.0
gunicorn==21.2.0
uvicorn[standard]==0.27.0

# NEW for v1.8 Multi-LLM Support
google-genai>=1.51.0
openai>=2.16.0
```

---

## Pricing Comparison (as of Jan 2026)

| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) |
|----------|-------|----------------------|------------------------|
| Anthropic | Claude Sonnet 4.5 | $3.00 | $15.00 |
| Google | Gemini 3 Flash Preview | $0.50 | $3.00 |
| DeepSeek | V3.2 Reasoner | $0.28 (uncached) | $0.42 |

**Cost Implication:** DeepSeek is 10-30x cheaper than Claude, Gemini is 6x cheaper. Consider default provider selection based on task complexity.

---

## Implementation Priority

1. **Add configuration** - API keys in config.py and .env
2. **Create provider abstraction** - Interface for all three providers
3. **Implement Gemini service** - google-genai streaming
4. **Implement DeepSeek service** - openai SDK with custom base_url
5. **Add provider selection** - Frontend UI and backend routing
6. **Handle reasoning output** - Special UI for DeepSeek thinking mode

---

## Sources

### Official Documentation
- [Google GenAI SDK Documentation](https://googleapis.github.io/python-genai/)
- [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [DeepSeek API Docs](https://api-docs.deepseek.com/)
- [DeepSeek Reasoning Model](https://api-docs.deepseek.com/guides/reasoning_model)
- [OpenAI Python SDK](https://github.com/openai/openai-python)

### Package Registries
- [google-genai on PyPI](https://pypi.org/project/google-genai/) - v1.61.0 (Jan 2026)
- [openai on PyPI](https://pypi.org/project/openai/) - v2.16.0 (Jan 2026)

### Deprecation Notices
- [Deprecated generative-ai-python](https://github.com/google-gemini/deprecated-generative-ai-python) - EOL Nov 2025
