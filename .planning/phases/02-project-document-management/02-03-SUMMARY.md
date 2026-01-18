---
phase: 02-project-document-management
plan: 03
subsystem: documents, encryption, search
tags: [fernet, fts5, file-upload, flutter, file-picker, encryption, multipart]

# Dependency graph
requires:
  - phase: 01-foundation-authentication
    provides: JWT auth, protected endpoints, secure storage
  - phase: 02-project-document-management
    plan: 01
    provides: Document model, database schema
provides:
  - Fernet encryption service for documents at rest
  - FTS5 full-text search with porter tokenizer
  - Document upload API with validation (text files, 1MB max)
  - Document list/view/search endpoints
  - Frontend file picker with upload progress
  - Document list/upload/viewer screens
affects: [02-04-conversation-ui, 03-ai-integration]

# Tech tracking
tech-stack:
  added: [cryptography, file_picker]
  patterns: [fernet-encryption, fts5-search, multipart-upload, file-validation]

key-files:
  created:
    - backend/app/services/encryption.py (EncryptionService)
    - backend/app/services/document_search.py (FTS5 helpers)
    - backend/app/routes/documents.py (upload/list/view/search endpoints)
    - backend/alembic/versions/daca512f660c_add_fts5_virtual_table_for_document_.py
    - frontend/lib/services/document_service.dart (API client with multipart upload)
    - frontend/lib/providers/document_provider.dart (state management)
    - frontend/lib/screens/documents/document_list_screen.dart
    - frontend/lib/screens/documents/document_upload_screen.dart
    - frontend/lib/screens/documents/document_viewer_screen.dart
  modified:
    - backend/main.py (registered documents router)
    - backend/.env (added FERNET_KEY)
    - frontend/pubspec.yaml (added file_picker dependency)
    - frontend/lib/models/document.dart (added optional content field)
    - frontend/lib/main.dart (added DocumentProvider)

key-decisions:
  - "Use Fernet for symmetric encryption with environment-based key management"
  - "Store encrypted content in documents.content_encrypted (bytes), plaintext in document_fts for search"
  - "FTS5 virtual table with porter ascii tokenizer for text normalization"
  - "Validate file type (text/plain, text/markdown) and size (1MB max) before upload"
  - "file_picker with custom allowedExtensions to filter .txt and .md only"
  - "Show upload progress with Dio onSendProgress callback"
  - "Decrypt content on-demand (not returned in list endpoint)"

patterns-established:
  - "Encryption: Fernet.encrypt(plaintext.encode('utf-8')) → bytes"
  - "FTS5 search: BM25 ranking with snippet() for highlighted results"
  - "File upload: FormData.fromMap with MultipartFile.fromFile"
  - "Validation: Check content_type AND file extension, validate UTF-8 encoding"
  - "Transactional consistency: Insert document and FTS5 entry in same transaction"

# Metrics
duration: 82min
completed: 2026-01-18
---

# Phase 02 Plan 03: Document Management with Encryption Summary

**Complete document management with encrypted storage, FTS5 search, and cross-platform file upload**

## Performance

- **Duration:** 82 minutes
- **Started:** 2026-01-18T14:16:22Z
- **Completed:** 2026-01-18T15:39:00Z (approx)
- **Tasks:** 3
- **Files created:** 9
- **Files modified:** 5
- **Commits:** 1 atomic commit (frontend implementation; backend already committed)

## Accomplishments

- Fernet encryption service with environment-based key management
- FTS5 virtual table for full-text search with porter tokenizer
- Document upload API with comprehensive validation (file type, size, UTF-8 encoding)
- Document list/view/search endpoints with project ownership validation
- Frontend document service with multipart upload support
- Document provider with upload progress tracking
- Three responsive screens: list, upload, viewer
- Cross-platform file picker filtering to .txt and .md files

## Task Commits

All backend work (Tasks 1-2) was already committed in initial project setup. Frontend work (Task 3) committed atomically:

1. **Tasks 1-2: Backend Encryption & API (already committed)**
   - EncryptionService with Fernet for document encryption/decryption
   - FTS5 virtual table migration with porter ascii tokenizer
   - Document API endpoints: POST upload, GET list, GET view, GET search
   - File validation: content type, size, UTF-8 encoding
   - Transactional FTS5 indexing synchronized with document inserts

2. **Task 3: Frontend Document UI** - `2efa35c` (feat)
   - DocumentService with multipart upload, auth headers, base URL
   - DocumentProvider with upload progress tracking
   - DocumentListScreen with empty state and card-based layout
   - DocumentUploadScreen with file picker and progress indicator
   - DocumentViewerScreen with monospace font for code/markdown
   - Added file_picker dependency to pubspec.yaml
   - Added optional content field to Document model
   - Registered DocumentProvider in MultiProvider

## Deviations from Plan

### Pre-existing Implementation
Backend files (encryption service, document_search helpers, FTS5 migration, document routes) were already implemented before plan execution. These were verified to match plan specifications and requirements, so execution continued to frontend implementation (Task 3).

**Impact:** No functional deviation; all requirements satisfied. Execution time focused on frontend implementation only.

## Technical Decisions Made

### Fernet Encryption Strategy
Environment variable `FERNET_KEY` loaded at service initialization. Encryption key generated once with `Fernet.generate_key()` and stored in `.env`. Documents encrypted before database storage, decrypted on-demand when viewing.

**Tradeoff:** FTS5 table contains plaintext for search. Acceptable for MVP; consider column-level encryption or "exclude from search" option for sensitive documents in production.

### FTS5 Search Configuration
Porter stemming tokenizer with ASCII normalization for robust text matching. BM25 ranking with snippet generation (20 tokens context, `<mark>` tags for highlights). Limits results to 20 per query.

**Performance:** FTS5 supports ~10k documents efficiently in SQLite; plan migration to PostgreSQL FTS or external search service for larger scale.

### File Upload Validation
Three-layer validation: (1) content_type check, (2) file size limit (1MB), (3) UTF-8 decoding verification. Prevents binary file uploads, oversized files, and encoding errors.

**Security:** Validation occurs server-side before encryption. File extension checked on frontend for UX only (not security).

### Upload Progress Tracking
Dio `onSendProgress` callback updates provider state during multipart upload. LinearProgressIndicator shows visual feedback. Provider tracks `_uploading` flag to prevent concurrent uploads.

## Next Phase Readiness

Document management complete. All DOC requirements (DOC-01 through DOC-05) satisfied:
- DOC-01: Upload text documents (.txt, .md) - DONE
- DOC-02: View list of documents in project - DONE
- DOC-03: Documents encrypted at rest - DONE (Fernet)
- DOC-04: Documents indexed for FTS - DONE (FTS5 with BM25)
- DOC-05: View document content in app - DONE

**Ready for Phase 2 Plan 4:** Conversation/thread management can reference documents via FTS5 search.

**Ready for Phase 3:** AI integration can autonomously search project documents using existing search endpoint.

No blockers identified.
