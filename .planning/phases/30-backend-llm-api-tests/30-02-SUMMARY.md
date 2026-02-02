---
phase: 30-backend-llm-api-tests
plan: 02
subsystem: backend/tests
tags: [sse, fts5, streaming, search, testing]

dependency_graph:
  requires: [30-01]
  provides: ["SSE test helpers", "Comprehensive FTS5 tests"]
  affects: [30-03, 30-04]

tech_stack:
  added: []
  patterns:
    - "SSE helper functions for streaming test utilities"
    - "BM25 ranking validation in FTS5 tests"
    - "Edge case testing patterns (empty, null, special chars)"

key_files:
  created:
    - backend/tests/fixtures/sse_helpers.py
    - backend/tests/unit/services/test_sse_streaming.py
  modified:
    - backend/tests/fixtures/__init__.py
    - backend/tests/unit/services/test_document_search.py

decisions:
  - key: "SSE helpers as standalone functions"
    rationale: "Simple utility functions vs class for easier imports and composition"
  - key: "Heartbeat timing tests use short intervals"
    rationale: "Can't test 1s intervals reliably; test format correctness instead"

metrics:
  duration: "~8 minutes"
  completed: "2026-02-02"
---

# Phase 30 Plan 02: SSE Helper & FTS5 Tests Summary

**One-liner:** SSE parsing test helpers and comprehensive FTS5 search tests covering BM25 ranking, snippets, and edge cases.

## What Was Built

### SSE Test Helper Module

Created `backend/tests/fixtures/sse_helpers.py` with utilities for testing SSE streaming endpoints:

| Function | Purpose |
|----------|---------|
| `parse_sse_line()` | Parse event, data, comment SSE lines |
| `collect_sse_events()` | Async collect events from streaming response |
| `filter_events_by_type()` | Filter events by type (text_delta, etc.) |
| `assert_event_sequence()` | Verify event types appear in order |
| `get_text_content()` | Extract concatenated text from deltas |
| `get_usage_from_events()` | Extract usage from message_complete |
| `has_heartbeat()` | Check for heartbeat comments |

### SSE Streaming Tests

Created `backend/tests/unit/services/test_sse_streaming.py` with 25 tests:

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestParseSSELine | 9 | Event, data, comment, empty line parsing |
| TestFilterEventsByType | 3 | Single type, no matches, excludes comments |
| TestAssertEventSequence | 3 | Found, with heartbeats, missing raises |
| TestGetTextContent | 3 | Extract text, ignore non-text, empty |
| TestGetUsageFromEvents | 2 | Extract usage, no complete event |
| TestHasHeartbeat | 2 | True/false cases |
| TestStreamWithHeartbeat | 3 | Original events, heartbeat format, completion |

### Expanded FTS5 Document Search Tests

Expanded `backend/tests/unit/services/test_document_search.py` from 6 to 20 tests:

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestIndexDocument | 1 | Index content in FTS5 |
| TestSearchDocuments | 5 | Empty, matching, isolation, snippets |
| TestSearchDocumentsRanking | 3 | BM25 term frequency, filename, multiple results |
| TestSearchDocumentsSnippets | 3 | Contains term, mark tags, truncation |
| TestSearchDocumentsEdgeCases | 8 | Empty query, no matches, special chars, case insensitive, wildcards |

## Test Results

```
===== 45 passed =====
- test_sse_streaming.py: 25 tests
- test_document_search.py: 20 tests (14 new)
```

## Requirements Satisfied

| Requirement | Status |
|-------------|--------|
| BLLM-04: SSE streaming tests | Satisfied - helpers and stream_with_heartbeat tests |
| BLLM-05: FTS5 search tests | Satisfied - ranking, snippets, edge cases |

## Deviations from Plan

None - plan executed exactly as written.

## Technical Notes

1. **SSE helper design:** Functions return structured dicts (e.g., `{"event": "text_delta", "data": {...}}`) that match the internal SSE event format used by ai_service.py.

2. **Heartbeat testing:** Used very short intervals (5ms) for testing to avoid slow tests. Real heartbeat timing behavior (5s/15s) tested via format verification.

3. **BM25 ranking tests:** SQLite FTS5 BM25 returns negative scores ordered ascending, so "first" result is actually lowest (most negative) score.

## Files Changed

| File | Change |
|------|--------|
| `backend/tests/fixtures/sse_helpers.py` | Created - 148 lines |
| `backend/tests/fixtures/__init__.py` | Modified - export sse_helpers |
| `backend/tests/unit/services/test_sse_streaming.py` | Created - 271 lines |
| `backend/tests/unit/services/test_document_search.py` | Modified - +308 lines |

## Next Phase Readiness

Ready for 30-03 (LLM Adapter Tests) - SSE helpers available for integration tests.
