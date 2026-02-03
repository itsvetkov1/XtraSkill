---
phase: 36-ai-interaction-enhancement
plan: 01
subsystem: backend-agent
tags: [source-attribution, sse, agent-service, contextvars]

dependency-graph:
  requires:
    - "Phase 35: Mode selection API and UI"
  provides:
    - "documents_used array in message_complete SSE event"
    - "_documents_used_context ContextVar for source tracking"
  affects:
    - "36-02: Frontend source citation UI"

tech-stack:
  added: []
  patterns:
    - "ContextVar for request-scoped state accumulation"
    - "Duplicate-free document tracking via list comprehension"

key-files:
  created: []
  modified:
    - "backend/app/services/agent_service.py"

decisions:
  - id: "D-36-01-01"
    summary: "Track documents at backend search time, not from LLM response"
    rationale: "PITFALL-05: Prevents hallucinated citations"

metrics:
  duration: "~2 minutes"
  completed: "2026-02-03"
---

# Phase 36 Plan 01: Source Attribution Backend Summary

Backend now tracks which documents were searched and includes that information in the message_complete SSE event, enabling frontend to display source citations.

## What Changed

### agent_service.py Modifications

1. **New context variable** `_documents_used_context` (ContextVar[list])
   - Holds list of `{'id': doc_id, 'filename': filename}` dicts
   - Request-scoped via ContextVar pattern

2. **Initialization in stream_chat**
   - `_documents_used_context.set([])` before streaming begins
   - Ensures clean slate for each chat request

3. **Document tracking in search_documents_tool**
   - After search results returned, accumulates document metadata
   - Deduplicates by document ID (same doc may match multiple queries)
   - Tracks actual search results, not LLM-reported documents (PITFALL-05)

4. **message_complete event enrichment**
   - Both yield points now include `documents_used` array
   - Empty array `[]` when no documents searched (not null)
   - Gracefully handles LookupError if context unavailable

## Code Patterns

```python
# Context variable definition
_documents_used_context: ContextVar[list] = ContextVar("documents_used_context")

# Document tracking in search tool
docs_used = _documents_used_context.get()
for doc_id, filename, snippet, score in results[:5]:
    if not any(d['id'] == doc_id for d in docs_used):  # Dedupe
        docs_used.append({'id': doc_id, 'filename': filename})
_documents_used_context.set(docs_used)

# In message_complete event
"documents_used": documents_used  # SRC-04: empty array when no docs
```

## SSE Event Format

The message_complete event now includes:

```json
{
  "event": "message_complete",
  "data": {
    "content": "AI response text...",
    "usage": {"input_tokens": 1000, "output_tokens": 200},
    "documents_used": [
      {"id": "doc-uuid-1", "filename": "requirements.pdf"},
      {"id": "doc-uuid-2", "filename": "specs.docx"}
    ]
  }
}
```

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 08b1a20 | feat | Track documents used in search_documents_tool |
| 1903d46 | feat | Include documents_used in message_complete event |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- [x] _documents_used_context defined and used in search_documents_tool
- [x] message_complete event includes documents_used array
- [x] Backend imports without errors
- [x] Documents tracked by actual search results (PITFALL-05 compliance)

## Next Phase Readiness

**Dependencies for 36-02:**
- message_complete SSE event structure documented above
- documents_used array format: `[{id, filename}, ...]`
- Empty array when no documents (not null)

**Testing Notes:**
- Manual test: Send message that triggers document search, verify documents_used in SSE response
- Edge case: Message without document search should return empty array
