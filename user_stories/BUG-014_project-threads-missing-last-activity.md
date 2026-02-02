# BUG-014: Project Threads Missing last_activity_at

**Priority:** Critical
**Status:** Done
**Component:** Backend - Threads API
**Discovered:** 2026-02-02 (Phase 26 regression testing)
**Fixed:** 2026-02-02

---

## Problem

Threads created within a project (via `/projects/{project_id}/threads`) were not appearing in the global Chats list.

---

## Root Cause

The project-scoped thread creation endpoint did not set `last_activity_at`:

```python
# In create_thread (project-scoped):
thread = Thread(
    project_id=project_id,
    title=thread_data.title,
    model_provider=thread_data.model_provider or "anthropic"
    # last_activity_at NOT set - defaulted to NULL
)
```

The global threads query sorts by `last_activity_at DESC`:
```python
.order_by(Thread.last_activity_at.desc())
```

Threads with NULL `last_activity_at` may sort unexpectedly or cause issues with pagination/filtering.

---

## Acceptance Criteria

- [x] Project-scoped thread creation sets last_activity_at
- [x] Project threads appear in global Chats list
- [x] Threads sorted correctly by activity

---

## Fix

Added `last_activity_at=datetime.utcnow()` to project-scoped thread creation:

```python
thread = Thread(
    project_id=project_id,
    title=thread_data.title,
    model_provider=thread_data.model_provider or "anthropic",
    last_activity_at=datetime.utcnow()  # ADDED
)
```

**Tests:** `backend/tests/test_global_threads.py`

---

## Technical References

- `backend/app/routes/threads.py` - create_thread endpoint (FIXED)

---

*Created: 2026-02-02*
*Fixed: 2026-02-02*
