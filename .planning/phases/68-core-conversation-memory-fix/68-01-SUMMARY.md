---
phase: 68-core-conversation-memory-fix
plan: 01
subsystem: testing
tags: [python, pytest, llm, cli-adapter, multi-turn, conversation-memory]

# Dependency graph
requires:
  - phase: 67-assistant-thread-ui
    provides: "AssistantConversationProvider and ClaudeCLIAdapter baseline code"
provides:
  - "Multi-turn _convert_messages_to_prompt() that sends full conversation history to CLI subprocess"
  - "_extract_text_content() helper for multi-part content (text/tool_use/thinking/tool_result)"
  - "47 passing unit tests covering multi-turn, multi-part content, BA flow regression, role alternation"
  - "1 integration test for 3-turn fact recall using real Claude CLI subprocess"
affects: [68-02, phase-69-token-optimization, phase-70-performance-tuning]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Multi-turn CLI prompt format: Human:/Assistant: labels with --- separators (Anthropic native)"
    - "Tool-use annotation: [searched documents] or [performed an action] only when text blocks present"
    - "Integration test marker: @pytest.mark.integration for real-subprocess tests (excludable from CI)"

key-files:
  created:
    - backend/tests/integration/__init__.py
    - backend/tests/integration/conftest.py
    - backend/tests/integration/test_cli_conversation_memory.py
  modified:
    - backend/app/services/llm/claude_cli_adapter.py
    - backend/tests/unit/llm/test_claude_cli_adapter.py

key-decisions:
  - "Tool-use-only assistant messages produce empty text via _extract_text_content() — the caller's empty-check skips them cleanly without special-casing"
  - "Tool-use annotations ([searched documents]/[performed an action]) only added when text blocks also present in same message"
  - "combined_prompt [USER]: outer wrapper kept unchanged — only inner content changed to multi-turn format"
  - "Pre-existing test_stream_chat_passes_api_key_in_env failure documented as out-of-scope (Phase 68 issue tracking)"

patterns-established:
  - "Pattern 1: _convert_messages_to_prompt iterates all messages with role validation, not just messages[-1]"
  - "Pattern 2: _extract_text_content separates text/tool_annotation collection, merges only when has_text_blocks=True"
  - "Pattern 3: Integration tests in backend/tests/integration/ with @pytest.mark.integration for selective CI exclusion"

requirements-completed: [CONV-01, CONV-02, CONV-03, CONV-04, TEST-01, TEST-02, TEST-03, TEST-05]

# Metrics
duration: 10min
completed: 2026-02-19
---

# Phase 68 Plan 01: Core Conversation Memory Fix Summary

**Multi-turn CLI prompt formatter with Human:/Assistant: labels replaces broken messages[-1]-only POC; 47-test unit suite + real-subprocess integration test validate full history delivery**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-19T12:04:29Z
- **Completed:** 2026-02-19T12:14:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Replaced broken `_convert_messages_to_prompt()` (POC that discarded all history except last message) with multi-turn formatter that iterates all messages with Human:/Assistant: role labels and --- separators
- Added `_extract_text_content()` helper handling string content, thinking exclusion, tool_use annotation, and tool_result skipping — with correct behavior for tool-use-only assistant turns
- Expanded unit test suite from 35 to 48 tests (+13) covering: multi-turn formatting (1/3/10+ messages), label format validation, separator presence, tool_use annotation, thinking exclusion, tool_result skipping, system message exclusion, BA flow regression check, and role alternation warning
- Created integration test directory with conftest marker registration and one 3-turn fact-recall test using real Claude CLI subprocess, properly guarded with @pytest.mark.skipif for environments without CLI

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace _convert_messages_to_prompt() with multi-turn formatter** - `cab87d7` (feat)
2. **Task 2: Add backend unit tests for message conversion** - `562f39a` (test)
3. **Task 3: Create integration test for conversation memory** - `561af22` (test)

## Files Created/Modified
- `backend/app/services/llm/claude_cli_adapter.py` - Replaced _convert_messages_to_prompt() with full history iterator; added _extract_text_content() helper; added clarifying comment on combined_prompt
- `backend/tests/unit/llm/test_claude_cli_adapter.py` - Updated 2 existing tests for new format; added 13 new tests (TEST-01, TEST-02, TEST-03, CONV-03)
- `backend/tests/integration/__init__.py` - Empty package init (created)
- `backend/tests/integration/conftest.py` - pytest 'integration' marker registration
- `backend/tests/integration/test_cli_conversation_memory.py` - 3-turn fact-recall integration test

## Decisions Made
- **Tool-use-only handling via empty-text skip:** Rather than special-casing tool-use-only messages in `_convert_messages_to_prompt()`, `_extract_text_content()` returns empty string for messages with no text blocks (tool_use annotations only added when text blocks are also present). The existing empty-text skip condition handles these cleanly.
- **[USER]: outer wrapper preserved:** The `combined_prompt` assembly wraps content with `[SYSTEM]: ... [USER]: ...`. After the fix, `[USER]:` precedes the full multi-turn history. This is slightly misleading but does not break CLI behavior, and minimizes change surface. A clarifying comment was added.
- **Role alternation = warning, not error:** Per locked decision in research, consecutive same-role messages trigger a logger.warning (not an exception) and messages are still included. This is a defensive check, not a hard enforcement.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _extract_text_content to not annotate tool-use-only messages**
- **Found during:** Task 2 (unit test for test_tool_use_only_assistant_messages_skipped)
- **Issue:** Original implementation annotated ALL tool_use blocks with `[performed an action]`, causing tool-use-only assistant messages to produce non-empty text. The empty-check skip would NOT skip them, contradicting the plan's requirement that tool-use-only assistant turns be skipped.
- **Fix:** Changed `_extract_text_content()` to track `has_text_blocks` and only include tool_use annotations when text blocks are also present. Pure tool-use-only messages return empty string, the caller's `if not text.strip(): continue` correctly skips them.
- **Files modified:** `backend/app/services/llm/claude_cli_adapter.py`
- **Verification:** All 13 new unit tests pass; `test_tool_use_only_assistant_messages_skipped` passes confirming no `"Assistant:"` in prompt for tool-use-only turns; `test_tool_use_blocks_replaced_with_annotation` passes confirming annotations still appear for text+tool_use messages.
- **Committed in:** `562f39a` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - logic bug in _extract_text_content)
**Impact on plan:** Auto-fix necessary for correctness. The plan's intent was clear (skip tool-use-only assistant messages) but the initial implementation conflicted with the annotation behavior. No scope creep.

## Issues Encountered
- Pre-existing test `test_stream_chat_passes_api_key_in_env` fails (1 failure in baseline before Phase 68). It asserts `env["ANTHROPIC_API_KEY"] == "secret-key-123"` but the current code strips env vars without explicitly adding the API key. This is an unrelated bug outside Phase 68 scope. Documented and NOT fixed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Core backend fix is complete: CLI adapter now sends full conversation history
- Unit test suite at 47 passing (1 pre-existing fail, documented)
- Integration test ready for real validation (requires Claude CLI in PATH)
- Phase 68-02 (frontend AssistantConversationProvider tests) can proceed independently
- Phase 69 (token optimization) has the correct multi-turn foundation to build on

## Self-Check: PASSED

- FOUND: backend/app/services/llm/claude_cli_adapter.py
- FOUND: backend/tests/unit/llm/test_claude_cli_adapter.py
- FOUND: backend/tests/integration/test_cli_conversation_memory.py
- FOUND: .planning/phases/68-core-conversation-memory-fix/68-01-SUMMARY.md
- FOUND commit cab87d7 (feat: multi-turn formatter)
- FOUND commit 562f39a (test: unit tests)
- FOUND commit 561af22 (test: integration test)
- agent_service.py: 0 lines changed (untouched)
- messages[-1]: 0 occurrences in claude_cli_adapter.py (removed)
- _extract_text_content: present in adapter (2 references)
- test_three_turn_conversation_has_all_messages: present in unit tests
- test_assistant_remembers_fact_across_turns: present in integration tests

---
*Phase: 68-core-conversation-memory-fix*
*Completed: 2026-02-19*
