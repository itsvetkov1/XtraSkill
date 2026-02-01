---
phase: 26
plan: 01
subsystem: backend-api
tags: [threads, association, ownership-transition, api]

dependency-graph:
  requires: [phase-25-dual-ownership]
  provides: [thread-project-association-api]
  affects: [phase-26-02-frontend]

tech-stack:
  patterns:
    - ownership-model-transition
    - one-way-association
    - validation-before-mutation

file-tracking:
  key-files:
    created: []
    modified:
      - backend/app/routes/threads.py

decisions:
  - id: PERMANENT-ASSOCIATION
    choice: "Thread association with project is permanent and one-way"
    reason: "Prevents complexity of re-association and maintains clear ownership"
  - id: OWNERSHIP-TRANSITION
    choice: "Clear user_id when setting project_id"
    reason: "Thread transitions from direct user ownership to project-based ownership"

metrics:
  duration: "54s"
  completed: "2026-02-01"
---

# Phase 26 Plan 01: Thread-Project Association Backend Summary

Extended PATCH /api/threads/{id} endpoint to support associating project-less chats with projects.

## One-liner

PATCH /threads/{id} now accepts project_id for permanent one-way association with ownership model transition.

## Changes Made

### Task 1: Extend ThreadUpdate model and PATCH endpoint

**Files modified:**
- `backend/app/routes/threads.py`

**Changes:**
1. Extended `ThreadUpdate` model with optional `project_id` field
2. Updated endpoint docstring to reflect extended capability
3. Renamed function from `rename_thread` to `update_thread` to reflect broader purpose
4. Added project association validation logic:
   - Check if thread already has a project (returns 400 if attempting re-association)
   - Validate project exists and belongs to current user (returns 404 if not found)
5. Implemented ownership model transition:
   - Sets `thread.project_id` to the new project
   - Clears `thread.user_id` to null (ownership transitions to project)
6. Title updates continue to work alongside or independent of association

**Commit:** `d3ef450`

## Verification Results

| Check | Status |
|-------|--------|
| ThreadUpdate accepts project_id | PASS |
| Syntax check passes | PASS |
| Imports resolve correctly | PASS |

## API Behavior

| Scenario | Expected Response |
|----------|-------------------|
| Associate project-less thread with valid project | 200, thread with project_id set, user_id cleared |
| Associate already-associated thread | 400 "Thread already associated with a project" |
| Associate with non-existent project | 404 "Project not found" |
| Associate with another user's project | 404 "Project not found" |
| Update title only | 200, thread with updated title |
| Update title and associate project | 200, both changes applied |

## Decisions Made

1. **PERMANENT-ASSOCIATION:** Thread-project association is permanent and one-way. Once a thread is associated with a project, it cannot be moved to a different project or back to project-less state. This simplifies the data model and prevents accidental data loss.

2. **OWNERSHIP-TRANSITION:** When a thread is associated with a project, the ownership model transitions from direct user ownership (`user_id` set) to project-based ownership (`project_id` set, `user_id` null). This maintains consistency with the dual ownership model from Phase 25.

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Ready for 26-02-PLAN.md (Frontend association UI):
- PATCH /threads/{id} accepts project_id for association
- Proper error handling for all edge cases
- Ownership model transition happens server-side
