---
phase: 30-backend-llm-api-tests
plan: 01
subsystem: llm-adapters
tags: [testing, pytest, llm, anthropic, gemini, deepseek, mocking]

dependency-graph:
  requires:
    - "28-01: Test infrastructure (fixtures, factories)"
    - "29: Service test patterns (class-based organization)"
  provides:
    - "53 LLM adapter unit tests"
    - "Shared fixtures for adapter mocking"
  affects:
    - "30-02: SSE helper tests (uses similar patterns)"

tech-stack:
  added: []
  patterns:
    - "Module-level patching (patch where used, not defined)"
    - "Mock async generators for streaming responses"
    - "Proper SDK error construction (APIError signatures)"

key-files:
  created:
    - backend/tests/unit/llm/__init__.py
    - backend/tests/unit/llm/conftest.py
    - backend/tests/unit/llm/test_anthropic_adapter.py
    - backend/tests/unit/llm/test_gemini_adapter.py
    - backend/tests/unit/llm/test_deepseek_adapter.py
  modified: []

decisions:
  - name: "Patch at module level"
    rationale: "Python imports at module load; patching library directly fails"
    example: "patch('app.services.llm.deepseek_adapter.AsyncOpenAI')"
  - name: "Proper SDK error signatures"
    rationale: "Gemini APIError requires (code, response_json) with nested structure"
    example: "errors.APIError(429, {'error': {'message': 'Rate limited'}})"
  - name: "Mock final chunk with choices"
    rationale: "DeepSeek adapter skips chunks without choices; usage must be on valid chunk"
    example: "final.choices = [MagicMock()] with delta properties"

metrics:
  duration: "9 minutes"
  completed: "2026-02-02"
---

# Phase 30 Plan 01: LLM Adapter Tests Summary

Unit tests for all three LLM adapters (Anthropic, Gemini, DeepSeek) without real API calls.

## One-liner

53 LLM adapter tests covering streaming, tool calls, retry logic, and error handling with mocked HTTP clients.

## What Was Built

### Test Module Structure
- `backend/tests/unit/llm/__init__.py` - Package marker
- `backend/tests/unit/llm/conftest.py` - Shared fixtures:
  - `mock_anthropic_stream`: Async context manager with text_stream and get_final_message
  - `mock_tool_use_block`: Factory for tool_use content blocks
  - `mock_gemini_stream`: Async generator yielding chunks with text and usage_metadata
  - `mock_deepseek_stream`: OpenAI-compatible stream with reasoning_content filtering

### AnthropicAdapter Tests (14 tests)
- **TestAnthropicAdapterInit**: api_key initialization, default/custom model, provider property
- **TestAnthropicAdapterStreamChat**: text chunks, tool_use chunks, complete with usage, API parameter passing (messages, system, tools, max_tokens), APIError handling, unexpected error handling

### GeminiAdapter Tests (17 tests)
- **TestGeminiAdapterInit**: api_key initialization, default/custom model, provider property
- **TestGeminiAdapterStreamChat**: text chunks, usage tracking, message format conversion
- **TestGeminiAdapterNonStreaming**: tool calls via non-streaming API (Gemini limitation)
- **TestGeminiAdapterRetry**: 429/500/503 retry logic with configurable delay
- **TestGeminiAdapterErrors**: APIError handling with proper code/message
- **TestGeminiAdapterMessageConversion**: user role, assistant-to-model conversion, multi-part content

### DeepSeekAdapter Tests (22 tests)
- **TestDeepSeekAdapterInit**: api_key, base_url (DeepSeek endpoint), default/custom model, provider property
- **TestDeepSeekAdapterStreamChat**: text chunks, usage tracking, system prompt prepending
- **TestDeepSeekAdapterReasoningHidden**: reasoning_content filtering per CONTEXT.md decision
- **TestDeepSeekAdapterToolCalls**: tool_use chunks, Anthropic-to-OpenAI format conversion
- **TestDeepSeekAdapterRetry**: RateLimitError, APIStatusError (500/503) retry logic
- **TestDeepSeekAdapterErrors**: APIError handling, unexpected error handling
- **TestDeepSeekAdapterMessageConversion**: string content, multipart content, tool result conversion
- **TestDeepSeekAdapterToolParsing**: JSON argument parsing, empty/invalid JSON handling

## Key Implementation Details

### Patching Strategy
```python
# Wrong: Patches library, but module already imported genai
with patch('google.genai.Client') as MockClient:

# Correct: Patches where genai is used in adapter module
with patch('app.services.llm.gemini_adapter.genai.Client') as MockClient:
```

### SDK Error Construction
```python
# Gemini APIError requires nested response_json
mock_error = errors.APIError(429, {"error": {"message": "Rate limited"}})

# OpenAI errors need response and body
raise RateLimitError(
    message="Rate limited",
    response=MagicMock(status_code=429),
    body={"error": {"message": "Rate limited"}}
)
```

### Mock Stream Consumption
```python
# DeepSeek adapter skips chunks without choices
if not chunk.choices:
    continue  # Usage chunk with empty choices gets skipped!

# Fix: Final chunk must have choices for adapter to see usage
final.choices = [MagicMock()]
final.choices[0].delta = MagicMock()
final.choices[0].delta.content = None  # No content, but valid chunk
final.usage = MagicMock()
final.usage.prompt_tokens = 100
```

## Test Results

```
tests/unit/llm/test_anthropic_adapter.py: 14 passed
tests/unit/llm/test_gemini_adapter.py: 17 passed
tests/unit/llm/test_deepseek_adapter.py: 22 passed
======================= 53 passed ========================
```

## Verification Checklist

- [x] backend/tests/unit/llm/ directory exists with __init__.py and conftest.py
- [x] test_anthropic_adapter.py has 14 tests (325 lines, >80 min)
- [x] test_gemini_adapter.py has 17 tests (437 lines, >80 min)
- [x] test_deepseek_adapter.py has 22 tests (518 lines, >80 min)
- [x] All 53 tests pass with `pytest tests/unit/llm/ -v`
- [x] No real API calls made (all HTTP mocked via module-level patches)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed module-level patching**
- **Found during:** Task 2 initial run
- **Issue:** Tests hit real APIs because patches were at library level, not module level
- **Fix:** Changed patch paths from `'google.genai.Client'` to `'app.services.llm.gemini_adapter.genai.Client'`
- **Files modified:** All test files

**2. [Rule 1 - Bug] Fixed Gemini APIError signature**
- **Found during:** Task 3 test runs
- **Issue:** Gemini errors.APIError requires (code, response_json) not (message)
- **Fix:** Updated to `errors.APIError(429, {"error": {"message": "..."}})`
- **Files modified:** test_gemini_adapter.py

**3. [Rule 1 - Bug] Fixed DeepSeek usage tracking**
- **Found during:** Task 3 test runs
- **Issue:** Usage not captured because final chunk had empty choices
- **Fix:** Updated mock_deepseek_stream fixture to include valid choices on final chunk
- **Files modified:** conftest.py

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `24ea93a` | LLM test module structure with conftest.py |
| 2 | `cc517ac` | AnthropicAdapter unit tests (14 tests) |
| 3 | `787ce19` | GeminiAdapter and DeepSeekAdapter tests (39 tests) |

## Next Steps

- Plan 30-02: SSE helper tests
- Plan 30-03: API route tests (auth, projects, documents)
- Plan 30-04: More API route tests (threads, conversations, artifacts)
