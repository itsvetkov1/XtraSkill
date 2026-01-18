---
phase: 02-project-document-management
plan: 01
subsystem: database, models
tags: [sqlalchemy, alembic, flutter, models, foreign-keys, cascade-delete, encryption, uuid]

# Dependency graph
requires:
  - phase: 01-foundation-authentication
    provides: User model, database setup, async SQLAlchemy patterns
provides:
  - Project model (user-owned containers for conversations)
  - Document model (encrypted content storage)
  - Thread model (conversation threads within projects)
  - Message model (user/assistant messages in threads)
  - SQLite foreign key enforcement via PRAGMA
  - Alembic migration for all new tables
  - Frontend Dart models with JSON serialization
affects: [02-02-project-crud, 02-03-document-upload, 02-04-conversation-ui, 02-05-thread-management]

# Tech tracking
tech-stack:
  added: [LargeBinary]
  patterns: [one-to-many-relationships, cascade-delete, foreign-key-constraints, sqlite-pragma, dart-enums]

key-files:
  created:
    - backend/app/models.py (Project, Document, Thread, Message models)
    - backend/alembic/versions/4c40ac075452_add_project_document_thread_message_.py
    - frontend/lib/models/project.dart
    - frontend/lib/models/document.dart
    - frontend/lib/models/thread.dart
    - frontend/lib/models/message.dart
  modified:
    - backend/app/database.py (added SQLite PRAGMA event listener)

key-decisions:
  - "Use LargeBinary for encrypted document content (Fernet encryption in Phase 2)"
  - "Store content_encrypted in Document model (not exposed to frontend)"
  - "Use MessageRole enum in Dart with fromJson/toJson methods"
  - "Enable SQLite foreign keys on every connection via event listener"
  - "Use back_populates on both sides (SQLAlchemy 2.0 pattern)"
  - "Set passive_deletes=True on relationships to let database handle cascades"
  - "Index created_at on threads and messages for chronological ordering"

patterns-established:
  - "Database cascade: ondelete CASCADE at ForeignKey plus cascade all delete-orphan at relationship"
  - "SQLite PRAGMA: event listener on Engine connect to enable foreign keys"
  - "Bidirectional relationships: back_populates on both parent and child"
  - "Dart models: fromJson/toJson with DateTime.parse and toIso8601String"
  - "Dart enums: MessageRole enum with custom fromJson/toJson methods"

# Metrics
duration: 33min
completed: 2026-01-18
---

# Phase 02 Plan 01: Database Schema & Models Summary

**Project/Document/Thread/Message models with cascade deletes, SQLite foreign key enforcement, and matching Dart models for API serialization**

## Performance

- **Duration:** 33 minutes
- **Started:** 2026-01-18T11:20:21+00:00
- **Completed:** 2026-01-18T11:54:19+00:00
- **Tasks:** 3
- **Files created:** 6
- **Files modified:** 1
- **Commits:** 3 atomic task commits

## Accomplishments

- Four new backend models (Project, Document, Thread, Message) with proper SQLAlchemy 2.0 relationships
- Database-level cascade deletes via ondelete="CASCADE" on all foreign keys
- ORM-level cascade deletes via cascade="all, delete-orphan" on all relationships
- SQLite PRAGMA foreign_keys=ON event listener ensures constraints are enforced
- Alembic migration creates tables in dependency order with proper indexes
- Four matching Dart models with fromJson/toJson for API integration
- MessageRole enum in Dart for type-safe role handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Backend Models with Relationships** - `a2e89b8` (feat)
   - Project, Document, Thread, Message models with UUID PKs and timezone-aware timestamps
   - Foreign keys with ondelete="CASCADE" and relationships with cascade="all, delete-orphan"
   - SQLite PRAGMA foreign_keys event listener added to database.py

2. **Task 2: Create Alembic Migration** - `ee1c280` (feat)
   - Migration creates tables in dependency order with proper indexes
   - Foreign key constraints verified with PRAGMA foreign_key_list

3. **Task 3: Create Frontend Dart Models** - `4f73c89` (feat)
   - Project, Document, Thread, Message models with fromJson/toJson
   - MessageRole enum with custom serialization
   - All models pass flutter analyze

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions Made

### SQLite PRAGMA Event Listener
Added event listener to execute "PRAGMA foreign_keys=ON" on every database connection. This ensures foreign key constraints are always enforced. Verified with test insert that raised IntegrityError for invalid foreign key.

### LargeBinary for Document Content
Use LargeBinary column type to store Fernet-encrypted bytes directly without base64 encoding overhead.

### MessageRole Enum in Dart
Created enum with custom fromJson/toJson methods for type-safe role handling in frontend.

### back_populates Instead of backref
Use explicit back_populates on both sides following SQLAlchemy 2.0 best practices.

## Next Phase Readiness

All models ready for Phase 2 API development. No blockers identified.

