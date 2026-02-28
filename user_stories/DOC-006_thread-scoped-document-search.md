# DOC-006: Thread-Scoped Document Search for Assistant Threads

**Priority:** Medium
**Status:** Done
**Component:** Backend / Document Search / MCP Tools
**Source:** ASSISTANT_FLOW_REVIEW.md — GAP-04

---

## User Story

As a user uploading documents to an assistant thread,
I want the AI to find and reference my uploaded documents,
So that I can have skill-enhanced conversations grounded in my own content.

---

## Problem

The `Document` model has a `thread_id` FK for thread-scoped documents. However, the `search_documents` tool in `mcp_tools.py` queries by `project_id` using a ContextVar.

For assistant threads that have no project association:
1. `project_id` is `None`
2. `search_documents` queries for documents where `project_id IS NULL` — may return nothing or all projectless documents
3. Documents uploaded to the specific thread are not findable via the search tool

### Expected vs Actual Behavior

**Expected:** If a user uploads a PDF to an assistant thread and asks "summarize my document," the AI's search tool finds documents scoped to that thread.

**Actual (needs verification):** The search tool uses `project_id` from ContextVar, which may be NULL for assistant threads, causing search to miss thread-scoped documents entirely.

---

## Acceptance Criteria

- [ ] Verify current behavior: what happens when `search_documents` is called in a projectless assistant thread?
- [ ] If broken: add `thread_id` as a fallback scope in `document_search.py`
- [ ] Documents uploaded to a specific thread are searchable within that thread
- [ ] Project-scoped document search continues to work (no regression for BA assistant)
- [ ] Thread-scoped documents from one thread are NOT visible in another thread's search

---

## Technical References

- `backend/app/models.py` — Document model with `thread_id` FK
- `backend/app/services/mcp_tools.py` — `search_documents` tool definition
- `backend/app/services/document_search.py` — Search implementation
- ContextVar for `project_id` — set in the request lifecycle

---

## Related

- This becomes critical once skills gain tool access (currently LOGIC-02 disables tools for assistant threads)
- Blocked by: assistant threads getting tool support (future milestone)

---

*Created: 2026-02-25*
*Source: Architecture review — assistant flow gaps*
