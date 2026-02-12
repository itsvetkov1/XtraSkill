# Architecture Patterns: Rich Document Support

**Domain:** Document parsing integration for BA Assistant
**Researched:** 2026-02-12

## Executive Summary

Rich document support (Excel, CSV, PDF, Word) integrates into the existing text-only document pipeline through a **dual-column storage pattern**: binary documents are stored encrypted in `content_encrypted` (existing), while extracted text is stored in a new `content_text` column for FTS5 indexing and AI context. This approach preserves the existing architecture while cleanly extending it for binary formats.

The architecture introduces **format-specific parser adapters** (Excel/CSV/PDF/Word) that extract text for search and structured data for preview, **content-type routing** to select parsers, and **metadata extraction** to support visual table previews in the frontend. All existing components (encryption, FTS5, AI tools, upload routes) remain functional with minimal modification.

**Critical insight:** The existing encryption and FTS5 infrastructure expects text. Binary documents need the same encryption (for compliance) and searchability (for AI context), but require an extraction step between upload and storage. The dual-column pattern solves this cleanly without architectural disruption.

## Recommended Architecture

### High-Level Data Flow

```
User uploads file → FastAPI route validates content type → Parser extracts text + metadata →
Encrypt original binary → Store encrypted binary + extracted text → Index text in FTS5 →
AI tool searches FTS5 → Returns extracted text to LLM → Frontend displays with format-aware preview
```

**Key principle:** Binary documents follow the same security/search path as text documents, with parsing inserted before encryption.

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Flutter Web)                                       │
│  - DocumentUploadScreen: file picker (multi-format)         │
│  - DocumentViewer: format-aware rendering                   │
│    - TextRenderer (existing .txt/.md)                       │
│    - TableRenderer (NEW: Excel/CSV with data_table widget)  │
│    - PDFRenderer (NEW: display extracted text + metadata)   │
│    - WordRenderer (NEW: structured content display)         │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP multipart upload
┌─────────────────────────────────────────────────────────────┐
│ Backend Routes (routes/documents.py)                        │
│  - POST /api/projects/{id}/documents                        │
│    ├─ Validate content_type (EXTENDED content type list)    │
│    ├─ Validate file size (INCREASED to 10MB for Excel/PDF)  │
│    ├─ Route to parser based on content_type                 │
│    └─ Call document_service.create_document()               │
│  - GET /api/documents/{id}                                  │
│    ├─ Return content_text for text preview                  │
│    └─ NEW: Return metadata JSON for table structure         │
│  - NEW: GET /api/documents/{id}/preview                     │
│    └─ Return structured preview data (table rows/cols)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Document Service (NEW: services/document_parsing.py)        │
│                                                              │
│  DocumentParser (Abstract Base)                             │
│   - parse(file_bytes) → ParsedDocument                      │
│                                                              │
│  ParsedDocument (dataclass)                                 │
│   - text_content: str (for FTS5 + AI)                       │
│   - metadata: dict (format-specific)                        │
│   - preview_data: dict (for frontend rendering)             │
│                                                              │
│  Concrete Parsers:                                          │
│   - ExcelParser(openpyxl): all sheets → text + table data   │
│   - CSVParser(csv stdlib): rows → text + preview            │
│   - PDFParser(PyMuPDF): pages → text (no OCR MVP)           │
│   - WordParser(python-docx): paragraphs → text + structure  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Database Layer (models.py)                                  │
│                                                              │
│  Document Model (MODIFIED):                                 │
│   - id: str (UUID, existing)                                │
│   - project_id: str (FK, existing)                          │
│   - filename: str (existing)                                │
│   - content_type: str (NEW: MIME type)                      │
│   - content_encrypted: bytes (existing, stores binary)      │
│   - content_text: bytes (NEW: encrypted extracted text)     │
│   - metadata_json: str (NEW: JSON with table structure)     │
│   - created_at: datetime (existing)                         │
│                                                              │
│  Migration:                                                 │
│   - Add content_type column (nullable, default text/plain)  │
│   - Add content_text column (nullable, backfill existing)   │
│   - Add metadata_json column (nullable)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Search & Encryption (existing, MINIMAL changes)             │
│                                                              │
│  FTS5 (document_fts table):                                 │
│   - Index content_text instead of decrypted content         │
│   - No structural changes to FTS5 table                     │
│                                                              │
│  Encryption Service (services/encryption.py):               │
│   - encrypt_document(bytes) → bytes (CHANGE signature)      │
│   - decrypt_document(bytes) → bytes (CHANGE signature)      │
│   - Add: encrypt_text(str) → bytes (for content_text)       │
│   - Add: decrypt_text(bytes) → str (for content_text)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ AI Integration (services/ai_service.py)                     │
│                                                              │
│  search_documents tool (UNCHANGED behavior):                │
│   - Searches FTS5 using content_text                        │
│   - Returns text snippets to LLM                            │
│   - Format-agnostic: LLM receives extracted text regardless │
│     of original format (Excel/PDF/Word all → text)          │
└─────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### New Components

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| **DocumentParser (Base)** | Define parsing interface | None (ABC) |
| **ExcelParser** | Extract text + table data from .xlsx | openpyxl |
| **CSVParser** | Extract text + table data from .csv | csv (stdlib) |
| **PDFParser** | Extract text from PDF pages | PyMuPDF (fitz) |
| **WordParser** | Extract structured text from .docx | python-docx (existing) |
| **ParserFactory** | Route content_type → parser | All parsers |
| **TableRenderer (Flutter)** | Display Excel/CSV as data table | data_table package |
| **GET /documents/{id}/preview** | Return structured preview data | DocumentService |

### Modified Components

| Component | Current State | Required Changes |
|-----------|--------------|------------------|
| **Document model** | Stores encrypted text, filename | Add: content_type, content_text, metadata_json columns |
| **routes/documents.py** | Validates text/plain, text/markdown | Extend ALLOWED_CONTENT_TYPES, increase MAX_FILE_SIZE, route to parser |
| **document_search.index_document()** | Accepts plaintext string | Accept extracted text (string) instead of original content |
| **encryption.py** | encrypt_document(str) → bytes | Change to encrypt_document(bytes) → bytes for binary |
| **DocumentViewer (Flutter)** | Renders text in monospace | Add format detection + specialized renderers |
| **Document.fromJson (Flutter)** | Expects content field | Add content_type, metadata fields |

### Unchanged Components

| Component | Why Unchanged |
|-----------|--------------|
| **FTS5 table (document_fts)** | Still indexes text; source column changes but schema doesn't |
| **search_documents service** | Searches FTS5, returns text snippets (format-agnostic) |
| **AI service search_documents tool** | Receives extracted text regardless of format |
| **Encryption key management** | Same Fernet key encrypts binary and text |
| **Project/Thread/Message models** | No relationship to document format |
| **OAuth authentication** | Orthogonal to document handling |

## Data Flow Changes

### Current Flow (Text Documents)

```
1. User uploads .txt file → FastAPI receives multipart
2. Validate content_type = text/plain
3. Read file → decode UTF-8 → plaintext string
4. Encrypt plaintext → encrypted bytes
5. Create Document(content_encrypted=encrypted)
6. Index plaintext in FTS5
7. Commit to DB
```

### New Flow (Binary Documents: Excel Example)

```
1. User uploads .xlsx file → FastAPI receives multipart
2. Validate content_type = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
3. Read file → bytes (NO decode)
4. Route to ExcelParser.parse(bytes)
5. Parser extracts:
   - text_content: "Sheet1: Name, Age, Email\nAlice, 30, alice@example.com\n..."
   - metadata: {"sheets": ["Sheet1"], "rows": 100, "cols": 3}
   - preview_data: {"headers": ["Name", "Age", "Email"], "rows": [...]}
6. Encrypt original bytes → encrypted_binary
7. Encrypt text_content → encrypted_text (NEW)
8. Create Document(
     content_encrypted=encrypted_binary,
     content_text=encrypted_text,
     content_type="application/vnd...",
     metadata_json=json.dumps(metadata)
   )
9. Index text_content in FTS5 (same as before, different source)
10. Commit to DB
```

### Retrieval Flow (Binary Documents)

```
GET /api/documents/{id}:
  - Decrypt content_text → return text for display
  - Return content_type, metadata_json for frontend rendering

GET /api/documents/{id}/preview:
  - Decrypt metadata_json → parse JSON
  - Return structured preview (table rows/headers)
  - Frontend uses TableRenderer with data_table widget

AI search (search_documents tool):
  - FTS5 search → content_text snippets
  - Return to LLM (format-agnostic: Excel → "Name: Alice, Age: 30")
```

## Build Order (Dependency-Aware)

### Phase 1: Database & Model Foundation
**Why first:** All other components depend on schema changes.

1. Create Alembic migration (add columns)
2. Run migration on dev database
3. Update Document SQLAlchemy model
4. Update encryption service signatures (bytes instead of str)
5. Backfill existing documents (content_type, content_text)
6. **Verification:** Existing text uploads still work

### Phase 2: Parser Infrastructure
**Why second:** Backend routes need parsers before accepting new formats.

1. Create DocumentParser base class + ParsedDocument dataclass
2. Implement TextParser (wrap existing logic)
3. Implement CSVParser (stdlib csv, no dependencies)
4. Implement ExcelParser (openpyxl)
5. Implement PDFParser (PyMuPDF)
6. Implement WordParser (python-docx, already installed)
7. Create ParserFactory
8. **Verification:** Unit tests for each parser with fixture files

### Phase 3: Backend Upload Integration
**Why third:** Now that parsers exist, wire them into upload route.

1. Update ALLOWED_CONTENT_TYPES in routes/documents.py
2. Increase MAX_FILE_SIZE to 10MB
3. Modify upload endpoint to route content_type → parser
4. Update document_search.index_document() to use content_text
5. Modify GET /documents/{id} to return content_type + metadata
6. Add GET /documents/{id}/preview endpoint
7. **Verification:** Upload Excel file → stored + searchable

### Phase 4: Frontend Model & Service
**Why fourth:** Backend is ready, update Flutter side to consume new fields.

1. Update Document model (add contentType, metadata fields)
2. Update DocumentService.getDocumentContent() to parse new fields
3. Add DocumentService.getDocumentPreview() method
4. **Verification:** Fetch document with contentType field

### Phase 5: Frontend Rendering
**Why fifth:** All data flows work, add specialized UI.

1. Install data_table_2 package
2. Create TableRenderer widget (Excel/CSV)
3. Create PDFRenderer widget (text display with page numbers)
4. Create WordRenderer widget (structured paragraphs)
5. Update DocumentViewerScreen with format routing
6. **Verification:** View Excel file shows table, PDF shows pages

### Phase 6: Export Feature (Optional)
**Why last:** Everything works, export is value-add.

1. Add GET /documents/{id}/export?format=csv endpoint
2. Backend converts preview_data back to CSV/Excel bytes
3. Frontend download button with format picker
4. **Verification:** Download Excel as CSV

## Patterns to Follow

### Pattern 1: Dual-Column Storage (Binary + Text)

**What:** Store original binary in `content_encrypted`, extracted text in `content_text`.

**When:** Any time a document format requires parsing to extract searchable content.

**Why:**
- Preserves original document for download/export
- Enables full-text search without re-parsing
- Separates concerns (storage vs search)

**Example:**
```python
# Upload Excel file
parsed = excel_parser.parse(file_bytes, filename)
doc = Document(
    content_encrypted=encrypt_binary(file_bytes),  # Original Excel
    content_text=encrypt_text(parsed.text_content),  # "Sheet1: A, B, C..."
    metadata_json=json.dumps(parsed.metadata)
)
```

### Pattern 2: Parser Adapter with Factory

**What:** Abstract parser interface + factory routing.

**When:** Multiple input formats require different processing logic.

**Why:**
- Single responsibility: each parser handles one format
- Easy to add formats (new parser + factory registration)
- Testable in isolation

**Example:**
```python
parser = ParserFactory.get_parser(content_type)
parsed = parser.parse(file_bytes, filename)
```

### Pattern 3: Metadata-Driven Rendering

**What:** Store structured metadata JSON, frontend reads to decide rendering.

**When:** Different formats need different preview UIs (table vs text vs pages).

**Why:**
- Backend describes structure, frontend interprets
- No backend changes when adding preview features
- Format-agnostic API (GET /documents/{id} same for all)

**Example:**
```dart
final metadata = jsonDecode(document.metadata);
if (metadata['format'] == 'xlsx') {
  return TableRenderer(sheets: metadata['sheets']);
}
```

### Pattern 4: Progressive Extraction (Preview Limits)

**What:** Extract limited rows/pages for preview, full text for search.

**When:** Large documents (1000-row Excel, 100-page PDF) would overwhelm frontend.

**Why:**
- Prevents UI lag from rendering massive tables
- Reduces API response size
- Search still covers full document

**Example:**
```python
MAX_PREVIEW_ROWS = 100
preview_data = {"rows": rows[:MAX_PREVIEW_ROWS]}  # Frontend sees 100
text_content = "\n".join(all_rows)  # FTS5 indexes all
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Re-Parsing on Every Request

**What goes wrong:** Parse Excel file on every GET /documents/{id} call.

**Why bad:**
- Parsing is CPU-expensive (openpyxl, PyMuPDF)
- 10MB Excel file = 2-5 seconds to parse
- Same document parsed repeatedly

**Instead:**
```python
# GOOD: Parse once at upload
parsed = parser.parse(file_bytes, filename)
doc.content_text = parsed.text_content  # Store extracted text
doc.metadata_json = json.dumps(parsed.preview_data)  # Store preview

# GOOD: Retrieve from DB
content = doc.content_text  # No re-parsing
preview = json.loads(doc.metadata_json)
```

### Anti-Pattern 2: Storing Parsed Data Unencrypted

**What goes wrong:** Store `content_text` as plaintext string.

**Why bad:**
- Violates existing encryption policy (content_encrypted is encrypted)
- Compliance risk: extracted text may contain PII
- Inconsistent: binary encrypted, text not

**Instead:**
```python
# GOOD: Encrypt both binary and text
doc.content_encrypted = encrypt_binary(file_bytes)
doc.content_text = encrypt_text(parsed.text_content)  # Also encrypted
```

### Anti-Pattern 3: Format Detection by Filename Extension

**What goes wrong:** Use `.xlsx` extension to route parser.

**Why bad:**
- Filename can be spoofed (upload malware as `file.xlsx`)
- Content-Type header is validated by FastAPI UploadFile
- Extension may be wrong (Excel file renamed to .csv)

**Instead:**
```python
# BAD
if filename.endswith('.xlsx'):
    parser = ExcelParser()

# GOOD
parser = ParserFactory.get_parser(file.content_type)  # Validated MIME type
```

### Anti-Pattern 4: Single Unified Renderer

**What goes wrong:** One frontend component tries to render all formats.

**Why bad:**
- Conditional logic explosion (if excel... elif pdf... elif word...)
- Excel needs DataTable, PDF needs page view, Word needs rich text
- Hard to maintain, test

**Instead:**
```dart
// GOOD: Dedicated renderers per format
switch (doc.contentType) {
  case 'text/csv': return TableRenderer(doc);
  case 'application/pdf': return PDFRenderer(doc);
  default: return TextRenderer(doc);
}
```

## Scalability Considerations

### At 100 Users (MVP Scale)

| Concern | Approach |
|---------|----------|
| Document storage | SQLite LargeBinary column (10MB limit OK for 100 users * 10 docs = 10GB max) |
| FTS5 index size | Extracted text only (not binary), 1-10KB per doc → 1MB index |
| Upload parsing time | Synchronous parsing acceptable (5s for 10MB Excel = tolerable) |
| Preview rendering | Client-side table rendering (100 rows = instant on modern browsers) |

### At 10K Users (Growth Scale)

| Concern | Approach |
|---------|----------|
| Document storage | Migrate to PostgreSQL with separate blob storage (S3/R2) for binaries |
| FTS5 index size | PostgreSQL full-text search or Elasticsearch if FTS5 insufficient |
| Upload parsing time | Background job queue (Celery) for async parsing (upload returns immediately) |
| Preview rendering | Server-side pagination (return 50 rows at a time with "Load more") |

### At 1M Users (Enterprise Scale)

| Concern | Approach |
|---------|----------|
| Document storage | S3/R2 for binaries, PostgreSQL for metadata + extracted text |
| FTS5 index size | Elasticsearch cluster with dedicated document search nodes |
| Upload parsing time | Distributed task queue (Celery + Redis) with autoscaling workers |
| Preview rendering | Server-side rendering + CDN caching for static previews |

## Integration Points Summary

### Existing Code That Changes

| File | Current | Change Required |
|------|---------|-----------------|
| `backend/app/models.py` | Document model with content_encrypted | Add: content_type, content_text, metadata_json |
| `backend/app/routes/documents.py` | ALLOWED_CONTENT_TYPES = ["text/plain", "text/markdown"] | Extend list, increase MAX_FILE_SIZE, route to parser |
| `backend/app/services/encryption.py` | encrypt_document(str) → bytes | Add: encrypt_binary(bytes), encrypt_text(str) |
| `backend/app/services/document_search.py` | index_document(doc_id, filename, content: str) | Change to accept extracted text parameter |
| `frontend/lib/models/document.dart` | Document(id, filename, content, createdAt) | Add: contentType, metadata fields |
| `frontend/lib/screens/documents/document_viewer_screen.dart` | Single SelectableText widget | Add format routing logic |

### New Code to Create

| File | Purpose |
|------|---------|
| `backend/app/services/document_parsing.py` | Parser base + concrete parsers + factory |
| `backend/app/services/document_preview.py` | Preview data extraction (separate from parsing) |
| `backend/app/routes/documents.py` | GET /documents/{id}/preview endpoint |
| `backend/alembic/versions/XXX_add_rich_doc_columns.py` | Database migration |
| `frontend/lib/widgets/table_renderer.dart` | Excel/CSV table display |
| `frontend/lib/widgets/pdf_renderer.dart` | PDF page-based display |
| `frontend/lib/widgets/word_renderer.dart` | Word structured content display |

### Unchanged Code (Zero Modifications)

| Component | Why Unchanged |
|-----------|--------------|
| `backend/app/services/ai_service.py` (search_documents tool) | Receives extracted text (format-agnostic) |
| `backend/app/services/document_search.py` (search_documents function) | FTS5 queries same, source column different |
| `backend/app/models.py` (Project, Thread, Message, Artifact) | No relationship to document format |
| `frontend/lib/providers/document_provider.dart` | Fetches documents same way, model changes only |
| All OAuth/authentication code | Orthogonal to document handling |

## Sources

### High Confidence (Official Documentation)

- [FastAPI Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) — UploadFile and multipart handling
- [SQLite FTS5 Extension](https://sqlite.org/fts5.html) — Full-text search capabilities
- [python-docx Documentation](https://python-docx.readthedocs.io/) — Word document parsing
- [PyMuPDF Features Comparison](https://pymupdf.readthedocs.io/en/latest/about.html) — PDF parsing capabilities
- [Flutter Data Table Package](https://fluttergems.dev/table/) — Table rendering options

### Medium Confidence (Technical Comparisons & Best Practices)

- [The Ultimate Guide to Intelligent Document Parsing](https://medium.com/@surajkhaitan16/the-ultimate-guide-to-intelligent-document-parsing-building-a-universal-file-reader-system-2fe285fca319) — BaseReader architecture pattern (2025)
- [Best Python PDF to Text Parser Libraries: A 2026 Evaluation](https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/) — PyMuPDF vs pypdf comparison
- [I Tested 7 Python PDF Extractors (2025 Edition)](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257) — Performance benchmarks
- [How to Create and Secure PDFs in Python with FastAPI](https://davidmuraya.com/blog/fastapi-create-secure-pdf/) — FastAPI + WeasyPrint integration
- [Technical Comparison — Python Libraries for Document Parsing](https://medium.com/@hchenna/technical-comparison-python-libraries-for-document-parsing-318d2c89c44e) — openpyxl, PyPDF2, python-docx comparison

### Supporting Resources

- [Column Level Encryption - Wikipedia](https://en.wikipedia.org/wiki/Column_level_encryption) — Encryption design patterns
- [Syncfusion Flutter DataGrid](https://www.syncfusion.com/blogs/post/introducing-excel-library-for-flutter) — Excel rendering for Flutter
- [universal_file_viewer Flutter package](https://pub.dev/packages/universal_file_viewer) — Multi-format preview package
- [SQLite Full-Text Search (FTS5) in Practice](https://thelinuxcode.com/sqlite-full-text-search-fts5-in-practice-fast-search-ranking-and-real-world-patterns/) — FTS5 indexing patterns

---

**Confidence Assessment:** HIGH

- Stack choices verified with official documentation (PyMuPDF, python-docx, openpyxl)
- Architecture patterns validated against 2025-2026 sources
- Integration points confirmed via existing codebase analysis
- Build order follows proven dependency management practices
