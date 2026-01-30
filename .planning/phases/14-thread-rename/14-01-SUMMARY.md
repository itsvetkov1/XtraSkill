---
phase: 14-thread-rename
plan: 01
subsystem: backend-api
tags: [fastapi, patch, threads, crud]
dependency-graph:
  requires: []
  provides: [PATCH /api/threads/{thread_id} endpoint]
  affects: [14-02 frontend service, 14-03 frontend provider]
tech-stack:
  added: []
  patterns: [PATCH for partial update, ownership validation via selectinload]
key-files:
  created: []
  modified: [backend/app/routes/threads.py]
decisions:
  - decision: "Use PATCH (not PUT) for partial title update"
    rationale: "Semantically correct for single-field updates"
  - decision: "Return 404 for non-owner (not 403)"
    rationale: "Security - don't leak thread existence to non-owners"
metrics:
  duration: ~3 minutes
  completed: 2026-01-30
---

# Phase 14 Plan 01: Backend PATCH Endpoint Summary

PATCH /api/threads/{thread_id} endpoint for title updates with ownership validation

## What Was Built

### ThreadUpdate Model
Added Pydantic model for thread update requests:
```python
class ThreadUpdate(BaseModel):
    """Request model for updating a thread."""
    title: Optional[str] = Field(None, max_length=255)
```

### rename_thread Endpoint
Added PATCH endpoint following delete_thread ownership pattern:
- Route: `PATCH /threads/{thread_id}`
- Request body: `{"title": "New Title"}` or `{"title": null}`
- Response: `ThreadResponse` with updated title and timestamps
- Auth: JWT required, ownership validated via project relationship
- Validation: 255 char max enforced by Pydantic

Key implementation details:
```python
@router.patch("/threads/{thread_id}", response_model=ThreadResponse)
async def rename_thread(
    thread_id: str,
    update_data: ThreadUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load thread with project for ownership check
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(selectinload(Thread.project))
    )
    # ... ownership validation ...
    thread.title = update_data.title
    await db.commit()
    await db.refresh(thread)
    return ThreadResponse(...)
```

## Commits

| Hash | Message |
|------|---------|
| 6d9f40d | feat(14-01): add PATCH endpoint for thread rename |

## Verification

- [x] Backend starts without errors
- [x] PATCH endpoint added at /threads/{thread_id}
- [x] ThreadUpdate model with max_length=255 validation
- [x] Ownership validation follows delete_thread pattern
- [x] Returns 404 for non-owner (security: no existence leak)
- [x] Null title allowed (clears title)
- [x] ThreadResponse returned with updated timestamps

## Deviations from Plan

None - plan executed exactly as written.

## Next Steps

Plan 14-02: Frontend ThreadService.renameThread() method
Plan 14-03: Frontend ThreadProvider.renameThread() with optimistic UI

## Files Modified

```
backend/app/routes/threads.py
  - Added ThreadUpdate model (lines 30-32)
  - Added rename_thread endpoint (lines 264-323)
```
