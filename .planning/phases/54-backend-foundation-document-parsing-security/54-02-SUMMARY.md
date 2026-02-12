---
phase: 54-backend-foundation-document-parsing-security
plan: 02
subsystem: database-schema
tags: [document-model, encryption, fts5, unicode61, migration, binary-storage]

# Dependency graph
requires:
  - phase: 54-01
    provides: "Document parser infrastructure for extracting text from rich formats"
provides:
  - "Document model with content_type, content_text, metadata_json columns"
  - "Binary encryption/decryption methods (encrypt_binary, decrypt_binary)"
  - "FTS5 upgraded to unicode61 tokenizer for international text search"
  - "Idempotent database migration for new and existing databases"
  - "Dual-column storage pattern (content_encrypted for binary, content_text for search)"
affects: [54-03-upload-routes, 55-frontend-display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-column storage: content_encrypted (binary) + content_text (extracted plaintext)"
    - "Binary encryption: encrypt_binary/decrypt_binary for raw bytes without UTF-8 encoding"
    - "FTS5 tokenizer upgrade: porter ascii → porter unicode61 for international text"
    - "Nullable columns: all new columns nullable for backward compatibility"
    - "Migration idempotency: PRAGMA table_info checks prevent duplicate ALTER TABLE"

key-files:
  created: []
  modified:
    - backend/app/models.py
    - backend/app/database.py
    - backend/app/services/encryption.py

key-decisions:
  - "content_type defaults to 'text/plain' via ALTER TABLE DEFAULT for existing documents"
  - "content_text NULL for legacy documents (backfilled on first access in Plan 54-03)"
  - "FTS5 tokenizer upgrade drops and recreates table (SQLite doesn't support ALTER for virtual tables)"
  - "Legacy document FTS entries lost after tokenizer upgrade (re-indexed on access when content_text backfilled)"
  - "Binary encryption methods separate from text methods (no UTF-8 encoding/decoding)"
  - "All new columns nullable to avoid breaking existing documents"

patterns-established:
  - "Schema migration pattern: PRAGMA table_info check → conditional ALTER TABLE"
  - "FTS5 upgrade pattern: check CREATE TABLE sql → drop/recreate if tokenizer change needed"
  - "Backward compatibility: existing text encryption methods unchanged"

# Metrics
duration: 1min 24sec
completed: 2026-02-12
---

# Phase 54 Plan 02: Database Schema Extension Summary

**Document model extended with content_type/content_text/metadata_json columns, binary encryption methods added, FTS5 upgraded to unicode61 tokenizer for international text**

## Performance

- **Duration:** 1min 24sec
- **Started:** 2026-02-12T14:04:38Z
- **Completed:** 2026-02-12T14:06:02Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Extended Document model with 3 new nullable columns (content_type, content_text, metadata_json)
- Added binary encryption/decryption methods alongside existing text methods
- Created database migration for new columns with default values
- Upgraded FTS5 tokenizer from 'porter ascii' to 'porter unicode61' for international text
- Ensured migration is idempotent (safe to run multiple times)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend Document model with new columns and add binary encryption methods** - `60cbb90` (feat)
2. **Task 2: Database migration for new columns and FTS5 unicode61 tokenizer upgrade** - `ff8dbd9` (feat)

## Files Created/Modified

**Modified:**
- `backend/app/models.py` - Added content_type, content_text, metadata_json columns to Document model; updated docstring to reflect 10MB limit and rich format support
- `backend/app/services/encryption.py` - Added encrypt_binary/decrypt_binary methods for raw byte encryption (preserves existing text methods)
- `backend/app/database.py` - Added migration logic for new Document columns and FTS5 tokenizer upgrade with re-indexing

## Decisions Made

**Schema design:**
- **Nullable columns:** All three new columns (content_type, content_text, metadata_json) are nullable to avoid breaking existing documents
- **Default value:** content_type defaults to 'text/plain' via ALTER TABLE DEFAULT for existing documents
- **Lazy backfill:** content_text is NULL for legacy documents until they are accessed (backfilled in Plan 54-03)

**Binary encryption:**
- **Separate methods:** encrypt_binary/decrypt_binary handle raw bytes without UTF-8 encoding/decoding (unlike existing text methods)
- **Backward compatibility:** Existing encrypt_document/decrypt_document methods unchanged (used by legacy get_document endpoint)

**FTS5 tokenizer upgrade:**
- **Drop and recreate:** SQLite FTS5 doesn't support ALTER, so tokenizer upgrade requires DROP TABLE + CREATE TABLE
- **Re-indexing strategy:** After drop/recreate, only documents with content_text populated are re-indexed (legacy documents lose FTS until accessed)
- **Acceptable trade-off:** Legacy documents can't be re-indexed during migration (no access to Fernet key at SQL level), but new uploads and backfilled documents will be searchable

**Migration idempotency:**
- **PRAGMA table_info check:** Migration checks if columns exist before ALTER TABLE
- **SELECT sql check:** Migration checks if FTS5 already uses unicode61 before drop/recreate
- **Safe to run multiple times:** All migration steps are conditional and idempotent

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all migrations ran successfully on existing database, verification checks passed.

## Self-Check

Verifying modified files and commits exist:

**Files:**
- [✓] `/Users/a1testingmac/projects/XtraSkill/backend/app/models.py`
- [✓] `/Users/a1testingmac/projects/XtraSkill/backend/app/database.py`
- [✓] `/Users/a1testingmac/projects/XtraSkill/backend/app/services/encryption.py`

**Commits:**
- [✓] `60cbb90` - Task 1 (Document model columns + binary encryption)
- [✓] `ff8dbd9` - Task 2 (Database migration + FTS5 upgrade)

**Self-Check: PASSED**

## Next Phase Readiness

**Ready for Phase 54-03 (Upload Routes Integration):**
- Document model has content_type (routing), content_text (search), metadata_json (format details)
- Binary encryption methods ready (encrypt_binary for file storage, decrypt_binary for download)
- FTS5 supports international text (unicode61 tokenizer)
- Migration tested on existing database (idempotent, backward compatible)

**Schema changes required by upload routes:**
- content_type populated from file upload MIME type
- content_text populated from DocumentParser.parse() result
- metadata_json populated from DocumentParser metadata (sheet_names, page_count, etc.)
- content_encrypted populated from encrypt_binary(file_bytes)

**No blockers or concerns.**

---
*Phase: 54-backend-foundation-document-parsing-security*
*Completed: 2026-02-12*
