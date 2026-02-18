---
phase: 62-backend-foundation
plan: 01
subsystem: data-model
tags: [database, migration, thread-type, thread-scoped-docs]
dependency_graph:
  requires: []
  provides: [thread-type-enum, thread-type-field, thread-scoped-documents]
  affects: [Thread, Document, all-future-plans]
tech_stack:
  added: [ThreadType enum]
  patterns: [3-step migration pattern, thread-type discriminator]
key_files:
  created:
    - backend/alembic/versions/e330b6621b90_add_thread_type_to_threads_and_thread_.py
  modified:
    - backend/app/models.py
decisions:
  - Use String(20) for thread_type field (not Enum) to match model_provider pattern
  - Implement 3-step migration for backward compatibility (nullable, backfill, NOT NULL)
  - Make Document.project_id nullable to support Assistant thread docs
  - Add bidirectional relationships between Thread and Document via thread_id
metrics:
  duration_seconds: 155
  tasks_completed: 2
  files_modified: 2
  commits: 2
  completed_date: 2026-02-17
---

# Phase 62 Plan 01: Database Foundation - Thread Types & Thread-Scoped Documents Summary

**One-liner:** ThreadType enum discriminator and thread-scoped document support with backward-compatible 3-step migration backfilling existing threads to 'ba_assistant'.

## Objective

Add ThreadType enum and thread_type field to Thread model, add thread_id to Document model, and create backward-compatible migration with backfill to establish the data foundation for BA Assistant vs Assistant mode differentiation.

## What Was Built

### 1. ThreadType Enum (app/models.py)
- Created `ThreadType(str, PyEnum)` with values: `BA_ASSISTANT = "ba_assistant"` and `ASSISTANT = "assistant"`
- Placed after OAuthProvider enum for consistency
- Used as validation enum, while DB column uses String(20) following model_provider pattern

### 2. Thread Model Updates (app/models.py)
- Added `thread_type` field:
  - Type: `Mapped[str]` with `String(20)` column
  - Constraint: `nullable=False`
  - Default: `server_default="ba_assistant"`
- Added `documents` relationship for thread-scoped documents:
  - Bidirectional with Document.thread
  - Cascade: `all, delete-orphan`
  - Passive deletes enabled
  - Foreign key: `Document.thread_id`

### 3. Document Model Updates (app/models.py)
- Made `project_id` nullable:
  - Changed from `Mapped[str]` to `Mapped[Optional[str]]`
  - Changed `nullable=False` to `nullable=True`
  - Purpose: Allow documents in Assistant mode without project context
- Added `thread_id` field:
  - Type: `Mapped[Optional[str]]` with `String(36)` column
  - Foreign key to `threads.id` with `CASCADE` delete
  - Indexed for query performance
- Added `thread` relationship:
  - Bidirectional with Thread.documents
  - Foreign key: thread_id
  - Optional (nullable)

### 4. Migration (e330b6621b90)
Implemented 3-step migration pattern for thread_type:

**Step 1:** Add thread_type as nullable with server_default
```python
batch_op.add_column(
    sa.Column('thread_type', sa.String(length=20),
              nullable=True,
              server_default='ba_assistant')
)
```

**Step 2:** Backfill existing threads
```python
connection.execute(
    sa.text("UPDATE threads SET thread_type = 'ba_assistant' WHERE thread_type IS NULL")
)
```

**Step 3:** Make NOT NULL after backfill
```python
batch_op.alter_column('thread_type', nullable=False)
```

**Document changes:**
- Made `project_id` nullable
- Added `thread_id` column with FK to threads
- Created index on `thread_id`
- Named FK constraint: `fk_documents_thread_id`

## Verification Results

### Model Import Test
```bash
python -c "from app.models import Thread, Document, ThreadType; print('ThreadType:', [e.value for e in ThreadType]); print('OK')"
# Output: ThreadType: ['ba_assistant', 'assistant']
#         OK
```

### Migration Application
```bash
alembic upgrade head
# INFO  [alembic.runtime.migration] Running upgrade b4ef9fb543d5 -> e330b6621b90
```

### Database Schema Verification
```python
# Verified:
# 1. threads.thread_type exists and is NOT NULL
# 2. No NULL values in threads.thread_type (all backfilled to 'ba_assistant')
# 3. documents.thread_id exists with index
# 4. documents.project_id is nullable
```

### Migration Roundtrip
```bash
alembic downgrade -1 && alembic upgrade head
# Result: Roundtrip successful (both directions clean)
```

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions

### 1. String(20) vs Enum for thread_type
**Decision:** Use `String(20)` column type instead of SQLAlchemy `Enum()`

**Rationale:**
- Matches existing `model_provider` field pattern (consistency)
- Avoids SQLAlchemy Enum complications with SQLite
- Enum defined at Python level for validation, DB uses string
- Simpler and more portable across databases

### 2. 3-Step Migration Pattern
**Decision:** Add nullable → backfill → make NOT NULL

**Rationale:**
- Ensures zero downtime on production databases
- Handles existing thread data without errors
- Guarantees no NULL values after migration
- Follows SQLite best practices for batch_alter_table

### 3. Bidirectional Relationships
**Decision:** Thread.documents ↔ Document.thread with explicit foreign_keys

**Rationale:**
- Clear navigation in both directions
- Cascade delete ensures cleanup when thread deleted
- Explicit foreign_keys avoids SQLAlchemy ambiguity (Document has both project_id and thread_id FKs)

## Dependencies & Integration Points

### Provides to Future Plans
- **thread_type field:** All plans can now distinguish BA vs Assistant threads
- **ThreadType enum:** Available for validation in API layer (62-02, 62-03)
- **thread_id on Document:** Enables thread-scoped documents in Assistant mode (64-02)
- **Nullable project_id:** Allows documents without project context

### Blocks on Nothing
- No dependencies - this is the foundation plan (Wave 1)

### Enables
- **62-02:** API validation logic can use ThreadType enum
- **62-03:** Service layer can route based on thread_type field
- **63-01:** Navigation can filter threads by type
- **64-02:** Document upload can associate with thread_id

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | dff0b9b | Add ThreadType enum and fields to models |
| 2 | bf55be2 | Create migration with 3-step backfill pattern |

## Files Changed

**Created:**
- `backend/alembic/versions/e330b6621b90_add_thread_type_to_threads_and_thread_.py` (70 lines)

**Modified:**
- `backend/app/models.py` (+36 lines, -5 lines)
  - Added ThreadType enum
  - Added Thread.thread_type field
  - Added Thread.documents relationship
  - Modified Document.project_id to nullable
  - Added Document.thread_id field and thread relationship

## Self-Check: PASSED

### Created Files
```bash
[ -f "backend/alembic/versions/e330b6621b90_add_thread_type_to_threads_and_thread_.py" ]
# FOUND: backend/alembic/versions/e330b6621b90_add_thread_type_to_threads_and_thread_.py
```

### Commits Exist
```bash
git log --oneline --all | grep -q "dff0b9b"
# FOUND: dff0b9b
git log --oneline --all | grep -q "bf55be2"
# FOUND: bf55be2
```

### Database Schema
```bash
sqlite3 ba_assistant.db "PRAGMA table_info(threads)" | grep thread_type
# FOUND: thread_type column with NOT NULL constraint

sqlite3 ba_assistant.db "PRAGMA table_info(documents)" | grep thread_id
# FOUND: thread_id column

sqlite3 ba_assistant.db "SELECT COUNT(*) FROM threads WHERE thread_type IS NULL"
# Result: 0 (no NULL values)
```

All checks passed. The data foundation is complete and ready for API and service layer integration.
