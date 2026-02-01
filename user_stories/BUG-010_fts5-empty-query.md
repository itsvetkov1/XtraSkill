# BUG-010: FTS5 Empty Query Syntax Error

**Priority:** Critical
**Status:** Open
**Component:** Backend - Document Search
**Discovered:** 2026-02-01 (Phase 26 testing)

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

- [ ] Document search handles empty query gracefully (return empty results)
- [ ] Project-less chats skip document search entirely
- [ ] No SQL errors when query string is empty or whitespace-only

---

## Technical References

- `backend/app/routes/conversations.py` - conversation endpoint
- `backend/app/services/` - document search service
- FTS5 documentation: empty MATCH queries are syntax errors

---

*Created: 2026-02-01*
