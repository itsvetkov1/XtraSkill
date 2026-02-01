---
phase: 25
plan: 01
subsystem: backend-api
tags: [threads, ownership, api, sqlalchemy]

dependency-graph:
  requires: [phase-02-models]
  provides: [global-threads-api, dual-ownership-model]
  affects: [phase-25-02-frontend, global-chats-feature]

tech-stack:
  patterns:
    - dual-ownership-model
    - outerjoin-query
    - paginated-api

file-tracking:
  key-files:
    created: []
    modified:
      - backend/app/models.py
      - backend/app/database.py
      - backend/app/routes/threads.py
      - backend/app/routes/conversations.py

decisions:
  - id: THREAD-OWNERSHIP
    choice: "Dual ownership model: user_id for project-less, project.user_id for project threads"
    reason: "Allows threads to exist independently or within projects"
  - id: LAST-ACTIVITY
    choice: "last_activity_at column for activity-based sorting"
    reason: "Global thread list needs activity-based ordering, not just creation date"
  - id: PROJECT-ONDELETE
    choice: "SET NULL on project_id FK instead of CASCADE"
    reason: "When project deleted, threads become project-less instead of being deleted"

metrics:
  duration: "3m 30s"
  completed: "2026-02-01"
---

# Phase 25 Plan 01: Global Chats Backend Summary

Backend support for project-less threads and global chats listing with dual ownership model.

## One-liner

Dual ownership Thread model with nullable project_id, GET/POST /threads endpoints, and paginated global listing.

## Changes Made

### Task 1: Update Thread model and database migration

**Files modified:**
- `backend/app/models.py`
- `backend/app/database.py`

**Changes:**
1. Made `project_id` nullable with `ondelete="SET NULL"` (instead of CASCADE)
2. Added `user_id` column for direct ownership of project-less threads
3. Added `last_activity_at` column for activity-based sorting
4. Updated `Project.threads` relationship to remove `delete-orphan` cascade
5. Added `User.threads` relationship for directly-owned threads
6. Added `Thread.user` relationship
7. Added database migration for `user_id` and `last_activity_at` columns

**Commit:** `24b2180`

### Task 2: Add global thread endpoints and update ownership validation

**Files modified:**
- `backend/app/routes/threads.py`
- `backend/app/routes/conversations.py`

**Changes:**
1. Added `GET /threads` endpoint for paginated global thread listing
   - Returns all user threads (directly owned + via projects)
   - Sorted by `last_activity_at` DESC
   - Includes `project_name` (null for project-less)
   - Pagination with page/page_size parameters
2. Added `POST /threads` endpoint for creating threads
   - Optional `project_id` parameter
   - Sets `user_id` when project-less, null when project-based
3. Updated `validate_thread_access` for dual ownership model
4. Updated `get_thread`, `rename_thread`, `delete_thread` for dual ownership
5. Added `GlobalThreadCreate`, `GlobalThreadListResponse`, `PaginatedThreadsResponse` models
6. Made `ThreadResponse.project_id` optional
7. Updates `last_activity_at` on chat activity

**Commit:** `67b609f`

## Verification Results

| Check | Status |
|-------|--------|
| Thread.project_id is nullable | PASS |
| Thread.user_id exists and indexes correctly | PASS |
| Thread.last_activity_at exists | PASS |
| User.threads relationship exists | PASS |
| threads.py imports OK | PASS |
| conversations.py imports OK | PASS |

## API Endpoints Added

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/threads` | List all user threads (paginated) |
| POST | `/api/threads` | Create thread (with or without project) |

## Decisions Made

1. **THREAD-OWNERSHIP:** Dual ownership model where project-less threads have `user_id` set, project threads have `project_id` set (user_id null).

2. **LAST-ACTIVITY:** Added `last_activity_at` column separate from `updated_at` to track chat activity specifically for sorting.

3. **PROJECT-ONDELETE:** Changed from CASCADE to SET NULL so deleting a project converts its threads to project-less threads instead of deleting them.

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Ready for 25-02-PLAN.md (Frontend global chats integration):
- GET /threads endpoint available for ChatsDrawer
- POST /threads endpoint available for "New Chat" from anywhere
- Thread detail/chat endpoints work for both ownership models
- last_activity_at updates on chat activity for proper sorting
