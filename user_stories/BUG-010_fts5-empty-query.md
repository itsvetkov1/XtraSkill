# BUG-010: FTS5 Empty Query Syntax Error

**Priority:** Critical
**Status:** Done
**Component:** Backend - Document Search
**Discovered:** 2026-02-01 (Phase 26 testing)
**Fixed:** 2026-02-01

---

## Problem

When starting a project-less chat and sending a message, the backend crashes with:

```
sqlite3.OperationalError: fts5: syntax error near ""
[SQL: SELECT d.id, d.filename, snippet(...) FROM documents d JOIN document_fts ...]
[parameters: ('6827e8c3-14ea-4c09-801b-6cd79ddab854', '')]
```

The document search is being called with an empty string query, which FTS5 cannot handle.

---

## Root Cause

The conversation flow calls document search even when:
1. The query/message is empty
2. The thread has no project (project-less chat shouldn't search documents)

---

## Acceptance Criteria

- [x] Document search handles empty query gracefully (return empty results)
- [x] Project-less chats skip document search entirely
- [x] No SQL errors when query string is empty or whitespace-only

---

## Fix

Added validation in `backend/app/services/document_search.py`:

```python
async def search_documents(db, project_id, query):
    # Skip search for project-less chats or empty queries
    if not project_id or not query or not query.strip():
        return []
    # ... rest of FTS5 search
```

**Tests:** `backend/tests/test_document_search.py`
- `test_search_with_empty_query_returns_empty`
- `test_search_with_whitespace_query_returns_empty`
- `test_search_with_none_project_id_returns_empty`

---

## Technical References

- `backend/app/routes/conversations.py` - conversation endpoint
- `backend/app/services/document_search.py` - document search service (FIXED)
- FTS5 documentation: empty MATCH queries are syntax errors

---

*Created: 2026-02-01*
*Fixed: 2026-02-01*
