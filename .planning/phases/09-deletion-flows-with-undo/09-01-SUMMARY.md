---
phase: 09-deletion-flows-with-undo
plan: 01
subsystem: backend-deletion
tags: [delete-api, cascade-delete, fastapi, sqlite]

dependency-graph:
  requires:
    - "Phase 1-2: Existing CRUD endpoints for projects, threads, documents"
    - "SQLite CASCADE constraints configured in models.py"
  provides:
    - "DELETE /api/projects/{id} endpoint with cascade deletion"
    - "DELETE /api/threads/{id} endpoint with cascade deletion"
    - "DELETE /api/documents/{id} endpoint"
    - "DELETE /api/threads/{thread_id}/messages/{message_id} endpoint"
  affects:
    - "09-02: Frontend deletion UI will call these endpoints"
    - "Future: Soft delete or undo feature would modify these endpoints"

tech-stack:
  added: []
  patterns:
    - "Response(status_code=204) for no-content DELETE responses"
    - "Ownership verification before deletion (same as existing read patterns)"
    - "SQLite ON DELETE CASCADE for automatic child record cleanup"

file-tracking:
  key-files:
    created: []
    modified:
      - backend/app/routes/projects.py
      - backend/app/routes/threads.py
      - backend/app/routes/documents.py
      - backend/app/routes/conversations.py

decisions:
  - id: "09-01-d1"
    description: "Hard delete with database CASCADE for child records"
    rationale: "Simplest approach - leverage existing SQLite FK constraints"
  - id: "09-01-d2"
    description: "Return 404 for both not-found and unauthorized resources"
    rationale: "Security best practice - don't reveal resource existence to unauthorized users"
  - id: "09-01-d3"
    description: "Reuse validate_thread_access helper for message deletion"
    rationale: "DRY - thread ownership check already implemented"

metrics:
  duration: "~3 minutes"
  completed: "2026-01-30"
---

# Phase 9 Plan 1: Backend DELETE Endpoints Summary

Add DELETE endpoints for projects, threads, documents, and messages to enable resource cleanup.

## One-liner

Four DELETE endpoints returning 204 No Content with ownership verification and SQLite CASCADE handling.

## What Was Built

### 1. DELETE /api/projects/{project_id}

**File:** `backend/app/routes/projects.py`

```python
@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, current_user: dict, db: AsyncSession):
    # Query and verify ownership
    # await db.delete(project), await db.commit()
    # CASCADE deletes threads, documents, messages
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### 2. DELETE /api/threads/{thread_id}

**File:** `backend/app/routes/threads.py`

```python
@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(thread_id: str, current_user: dict, db: AsyncSession):
    # Query with selectinload(Thread.project) for ownership check
    # await db.delete(thread), await db.commit()
    # CASCADE deletes messages, artifacts
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### 3. DELETE /api/documents/{document_id}

**File:** `backend/app/routes/documents.py`

```python
@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, current_user: dict, db: AsyncSession):
    # Query with join(Project) for ownership check
    # await db.delete(doc), await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### 4. DELETE /api/threads/{thread_id}/messages/{message_id}

**File:** `backend/app/routes/conversations.py`

```python
@router.delete("/threads/{thread_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(thread_id: str, message_id: str, current_user: dict, db: AsyncSession):
    # Reuse validate_thread_access helper for ownership
    # Query message by id and thread_id
    # await db.delete(message), await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

## Commits

| Hash | Message |
|------|---------|
| 1552691 | feat(09-01): add DELETE endpoints for projects and threads |
| f9d350e | feat(09-01): add DELETE endpoints for documents and messages |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- Backend imports successfully without errors
- All four DELETE endpoints registered with /api prefix:
  - `DELETE /api/projects/{project_id}`
  - `DELETE /api/threads/{thread_id}`
  - `DELETE /api/documents/{document_id}`
  - `DELETE /api/threads/{thread_id}/messages/{message_id}`
- Each endpoint has ownership verification
- Each endpoint returns 204 No Content on success
- Each endpoint returns 404 for non-existent or unauthorized resources

## Expected API Behavior

| Endpoint | Success | Not Found/Unauthorized |
|----------|---------|----------------------|
| DELETE /api/projects/{id} | 204 (cascade to threads/docs/messages) | 404 |
| DELETE /api/threads/{id} | 204 (cascade to messages/artifacts) | 404 |
| DELETE /api/documents/{id} | 204 | 404 |
| DELETE /api/threads/{tid}/messages/{mid} | 204 | 404 |

## Next Steps

- 09-02: Frontend deletion UI with confirmation dialogs
- Frontend will call these endpoints to delete resources
- Future: Consider soft delete for undo functionality
