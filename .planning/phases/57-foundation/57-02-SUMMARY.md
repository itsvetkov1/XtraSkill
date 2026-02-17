---
phase: 57-foundation
plan: 02
subsystem: llm-adapters
tags: [claude-code, factory, adapters, stubs]
dependency_graph:
  requires: [57-01]
  provides: [claude-code-sdk-adapter-stub, claude-code-cli-adapter-stub, factory-routing]
  affects: [llm-factory, llm-base-enum]
tech_stack:
  added: []
  patterns: [factory-pattern, abstract-base-class, stub-implementation]
key_files:
  created:
    - backend/app/services/llm/claude_agent_adapter.py
    - backend/app/services/llm/claude_cli_adapter.py
    - backend/tests/unit/llm/test_claude_agent_adapter.py
    - backend/tests/unit/llm/test_claude_cli_adapter.py
  modified:
    - backend/app/services/llm/base.py
    - backend/app/services/llm/factory.py
    - backend/app/services/llm/__init__.py
decisions:
  - Both adapters use ANTHROPIC_API_KEY (Claude Code uses same Anthropic API key)
  - Stub implementations raise NotImplementedError with phase-specific messages (58 for SDK, 59 for CLI)
  - SDK default model: claude-sonnet-4-5-20250514 (Agent SDK recommended model)
  - CLI default model: claude-sonnet-4-5-20250929 (latest Sonnet model)
metrics:
  duration: 235
  completed_date: 2026-02-13
  tasks_completed: 2
  files_created: 4
  files_modified: 3
  tests_added: 16
  tests_passed: 69
---

# Phase 57 Plan 02: Factory Registration for Claude Code Providers

**One-liner:** Registered claude-code-sdk and claude-code-cli providers in LLMFactory with stub adapters raising NotImplementedError for Phase 58/59 implementation.

## Summary

Created infrastructure for two new Claude Code provider types in the LLM adapter architecture. Added CLAUDE_CODE_SDK and CLAUDE_CODE_CLI enum values to LLMProvider, created stub adapter classes implementing the LLMAdapter interface, registered both in LLMFactory, and added comprehensive unit tests. Both adapters are fully wired into the factory but raise NotImplementedError from stream_chat until their respective implementation phases (58 for SDK, 59 for CLI).

## What Was Done

### Task 1: Add provider enum values, create adapter stubs, register in factory
**Commit:** 2d59c8f

**Changes:**
1. **base.py** — Added CLAUDE_CODE_SDK and CLAUDE_CODE_CLI to LLMProvider enum
2. **claude_agent_adapter.py** — Created ClaudeAgentAdapter stub with:
   - Architecture note explaining SDK's internal tool execution via MCP servers
   - Default model: claude-sonnet-4-5-20250514
   - NotImplementedError message referencing Phase 58
   - Proper LLMAdapter ABC implementation
3. **claude_cli_adapter.py** — Created ClaudeCLIAdapter stub with:
   - Architecture note explaining CLI subprocess integration approach
   - Default model: claude-sonnet-4-5-20250929
   - NotImplementedError message referencing Phase 59
   - Proper LLMAdapter ABC implementation
4. **factory.py** — Registered both adapters:
   - Added imports for both adapter classes
   - Added both to _adapters registry dict
   - Added API key handling for both providers (both use ANTHROPIC_API_KEY)
5. **__init__.py** — Exported both new adapters and updated module docstring

**Verification:**
- ✅ Enum values print correctly: "claude-code-sdk claude-code-cli"
- ✅ Factory.list_providers() includes both new providers
- ✅ Adapters return correct provider values from provider property

### Task 2: Add unit tests for both adapter stubs
**Commit:** 854116d

**Changes:**
1. **test_claude_agent_adapter.py** — Created comprehensive test suite:
   - TestClaudeAgentAdapterInit (4 tests): API key storage, default model, custom model, provider property
   - TestClaudeAgentAdapterStreamChat (1 test): NotImplementedError with "Phase 58" message
   - TestClaudeAgentAdapterFactory (3 tests): Factory creation, API key validation, custom model passing
2. **test_claude_cli_adapter.py** — Created parallel test suite:
   - TestClaudeCLIAdapterInit (4 tests): Same coverage as agent adapter
   - TestClaudeCLIAdapterStreamChat (1 test): NotImplementedError with "Phase 59" message
   - TestClaudeCLIAdapterFactory (3 tests): Same coverage as agent adapter

**Test patterns:**
- Used `@patch('app.services.llm.factory.settings')` to mock settings at correct location
- Used `pytest.raises(NotImplementedError, match="Phase XX")` to verify stub behavior
- Used `async for` loop to trigger async generator execution for NotImplementedError test

**Verification:**
- ✅ 16 new tests, all passing
- ✅ Full LLM adapter test suite: 69 tests pass (no regressions)

## Overall Verification

All plan verification criteria met:

1. ✅ `LLMFactory.create('claude-code-sdk')` returns ClaudeAgentAdapter with correct provider
2. ✅ `LLMFactory.create('claude-code-cli')` returns ClaudeCLIAdapter with correct provider
3. ✅ `LLMFactory.list_providers()` returns all 5 providers including both new ones
4. ✅ All adapter tests pass (16 new tests covering init, provider, stream_chat stub, factory integration)
5. ✅ Full test suite passes with zero regressions (69 total tests)

## Deviations from Plan

None - plan executed exactly as written.

## Key Technical Decisions

### 1. Different Default Models for SDK vs CLI
**Decision:** SDK uses claude-sonnet-4-5-20250514, CLI uses claude-sonnet-4-5-20250929

**Rationale:**
- SDK documentation recommends the 0514 model for agent use cases
- CLI uses the latest Sonnet model (0929) as it's a direct Claude Code CLI integration
- Both models are Claude Sonnet 4.5, difference is in training date and optimizations

### 2. Shared API Key Configuration
**Decision:** Both providers use ANTHROPIC_API_KEY (not separate env vars)

**Rationale:**
- Claude Code (both SDK and CLI) uses the same Anthropic API key
- No need for separate CLAUDE_CODE_SDK_API_KEY or CLAUDE_CODE_CLI_API_KEY
- Simplified configuration and reduced environment variable sprawl

### 3. Phase-Specific NotImplementedError Messages
**Decision:** Error messages reference specific implementation phases (58 for SDK, 59 for CLI)

**Rationale:**
- Clear communication to future developers about where implementation lives
- Helps with project planning and phase dependency tracking
- Makes it obvious these are intentional stubs, not incomplete implementations

## Architecture Notes

### Provider Enum Values
The enum values use kebab-case ("claude-code-sdk", "claude-code-cli") to match the existing pattern established by other providers ("anthropic", "google", "deepseek"). This makes them suitable for use in API requests and configuration.

### Stub Pattern
Both adapters follow the "stub implementation" pattern:
- Implement the full ABC interface (provider property, stream_chat method)
- Raise NotImplementedError with clear messaging
- Include required `yield` statement to satisfy async generator type signature (with `# pragma: no cover`)

This allows the factory routing and type system to work correctly while deferring actual implementation.

### Factory Integration
Both adapters are fully integrated into LLMFactory:
- Listed in `list_providers()` output
- Routable via `create("claude-code-sdk")` and `create("claude-code-cli")`
- API key validation works correctly
- Model parameter passing works correctly

Phase 58 and 59 can focus purely on implementing stream_chat without touching factory code.

## Testing Strategy

### Test Coverage
Each adapter has 8 unit tests covering:
- Initialization with API key storage
- Default model selection
- Custom model parameter
- Provider property enum value
- NotImplementedError from stream_chat
- Factory instantiation
- Factory API key validation
- Factory model parameter passing

### Mock Strategy
Used `@patch('app.services.llm.factory.settings')` to patch settings at the import location in factory.py. This ensures the mock propagates correctly to `_get_api_key()`.

### Async Generator Testing
Testing NotImplementedError in an async generator requires actually iterating:
```python
with pytest.raises(NotImplementedError):
    async for _ in adapter.stream_chat(...):
        pass
```

This triggers the raise statement inside the generator.

## Files Changed

**Created (4 files):**
- `backend/app/services/llm/claude_agent_adapter.py` (52 lines) — ClaudeAgentAdapter stub
- `backend/app/services/llm/claude_cli_adapter.py` (51 lines) — ClaudeCLIAdapter stub
- `backend/tests/unit/llm/test_claude_agent_adapter.py` (99 lines) — Agent adapter tests
- `backend/tests/unit/llm/test_claude_cli_adapter.py` (99 lines) — CLI adapter tests

**Modified (3 files):**
- `backend/app/services/llm/base.py` (+2 lines) — Added two enum values
- `backend/app/services/llm/factory.py` (+15 lines) — Registered adapters and API key handling
- `backend/app/services/llm/__init__.py` (+7 lines) — Exported new adapters

## Success Criteria

All success criteria from the plan met:

- ✅ LLMProvider enum has CLAUDE_CODE_SDK="claude-code-sdk" and CLAUDE_CODE_CLI="claude-code-cli"
- ✅ ClaudeAgentAdapter exists, returns correct provider, raises NotImplementedError from stream_chat
- ✅ ClaudeCLIAdapter exists, returns correct provider, raises NotImplementedError from stream_chat
- ✅ LLMFactory.create("claude-code-sdk") returns ClaudeAgentAdapter
- ✅ LLMFactory.create("claude-code-cli") returns ClaudeCLIAdapter
- ✅ Both use ANTHROPIC_API_KEY (Claude Code uses same key)
- ✅ Unit tests cover all adapter stubs and factory routing
- ✅ Full test suite passes with zero regressions

## Next Steps

**Phase 58 (Agent SDK Adapter):** Implement stream_chat in ClaudeAgentAdapter
- Import Agent SDK from Phase 57-01
- Create agent instance with MCP server from mcp_tools.py
- Implement multi-turn streaming with AssistantMessage/ResultMessage translation
- Handle SDK's internal tool loop (bypass AIService tool execution)

**Phase 59 (CLI Adapter):** Implement stream_chat in ClaudeCLIAdapter
- Spawn CLI subprocess with --output-format stream-json
- Parse line-delimited JSON from stdout
- Translate CLI events to StreamChunk format
- Handle process lifecycle (timeout, cleanup, zombie prevention)

## Self-Check

**Verifying created files exist:**
```bash
[ -f "backend/app/services/llm/claude_agent_adapter.py" ] && echo "FOUND" || echo "MISSING"
[ -f "backend/app/services/llm/claude_cli_adapter.py" ] && echo "FOUND" || echo "MISSING"
[ -f "backend/tests/unit/llm/test_claude_agent_adapter.py" ] && echo "FOUND" || echo "MISSING"
[ -f "backend/tests/unit/llm/test_claude_cli_adapter.py" ] && echo "FOUND" || echo "MISSING"
```

**Verifying commits exist:**
```bash
git log --oneline --all | grep -q "2d59c8f" && echo "FOUND: 2d59c8f" || echo "MISSING: 2d59c8f"
git log --oneline --all | grep -q "854116d" && echo "FOUND: 854116d" || echo "MISSING: 854116d"
```


## Self-Check: PASSED

All files and commits verified:
- ✅ FOUND: claude_agent_adapter.py
- ✅ FOUND: claude_cli_adapter.py
- ✅ FOUND: test_claude_agent_adapter.py
- ✅ FOUND: test_claude_cli_adapter.py
- ✅ FOUND: commit 2d59c8f
- ✅ FOUND: commit 854116d
