# Project Research Summary

**Project:** XtraSkill (BA Assistant) — Rich Document Support
**Domain:** Document parsing (Excel, CSV, PDF, Word) for AI-enhanced business analysis
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

Rich document support (Excel, CSV, PDF, Word) extends BA Assistant's existing text-only upload system through a **dual-column storage architecture**: binary documents are stored encrypted in `content_encrypted` (existing behavior), while extracted text is stored in a new `content_text` column for FTS5 indexing and AI context. This approach preserves the existing security and search infrastructure while cleanly extending it for binary formats without architectural disruption.

The recommended stack adds minimal dependencies: **openpyxl** for Excel, **pdfplumber** for PDF text extraction, built-in **csv** module with **chardet** for encoding detection, and existing **python-docx** for Word. Flutter frontend adds **excel** (pure Dart implementation, web-compatible) and **pluto_grid** for advanced table display with sorting, filtering, and keyboard navigation. All libraries are actively maintained, production-ready, and MIT/Apache licensed (pdfplumber chosen over PyMuPDF to avoid AGPL commercial licensing).

**Critical insight:** The parsing layer sits BETWEEN upload and encryption. Extract text first, then encrypt both original binary and extracted text separately. This prevents the most common pitfall: storing encrypted binary data that can't be searched or fed to AI. Three major risks dominate the implementation: (1) XXE/zip bomb attacks via malicious XLSX/DOCX files, (2) token budget explosion from large documents filling AI context, and (3) data type corruption (Excel auto-converts "00123" to 123, losing leading zeros). All three require prevention in Phase 1, not remediation later.

## Key Findings

### Recommended Stack

**Backend additions** focus on parsing with security and performance in mind. openpyxl is the industry standard for Excel (.xlsx) after xlrd's deprecation, offering both read and write capabilities with no C dependencies. pdfplumber provides superior table extraction compared to alternatives while avoiding PyMuPDF's AGPL commercial licensing trap. chardet handles CSV encoding detection (critical for Windows-1252 vs UTF-8 files). python-docx is already installed for artifact export, requiring no changes.

**Frontend additions** enable rich preview without platform channels (web-compatible). The excel package (v4.0.6+) provides pure Dart Excel read/write with web download support. pluto_grid (v8.7.0+) delivers spreadsheet-like UX with sorting, filtering, pagination, and keyboard navigation—essential for 1000+ row tables where Flutter's DataTable would freeze the browser.

**Core technologies:**
- **openpyxl >=3.1.5**: Excel parsing — Read-only mode for performance, handles formulas/charts, Pandas uses it as backend engine
- **pdfplumber >=0.11.8**: PDF text extraction — Superior table detection vs PyPDF2, better licensing than PyMuPDF, actively maintained
- **chardet >=5.2.0**: CSV encoding detection — Prevents UTF-8/Windows-1252 mojibake, handles UTF-8-BOM from Excel exports
- **python-docx 1.2.0**: Word parsing — Already installed, no upgrade needed, extracts paragraphs and tables
- **excel ^4.0.6 (Flutter)**: Client-side Excel parsing — Pure Dart, web-compatible, auto-downloads via save()
- **pluto_grid ^8.7.0 (Flutter)**: Advanced data grid — Virtualization for large tables, canvas rendering compatible

**What NOT to use:**
- **pandas** (for now): 50MB+ dependency overhead, unnecessary for text extraction (defer until data analysis features needed)
- **PyMuPDF**: AGPL license requires paid commercial license for SaaS applications
- **xlrd**: Deprecated since 2020, maintainer recommends openpyxl
- **PyPDF2**: Deprecated since 2023, replaced by pypdf (but pdfplumber superior for extraction)

### Expected Features

**Must have (table stakes) — MVP v2.1:**
All four core formats (Excel, CSV, PDF, Word) with text extraction feeding existing FTS5 search and AI document_search tool. File validation (content-type + MIME + extension) prevents security issues. Visual table preview shows first 10 rows for Excel/CSV uploads. Sheet selector allows users to choose which Excel sheets to parse (default: all). Encoding detection handles international characters in CSVs. Document metadata display shows row count, sheet names, page count.

**Core parsing features:**
- Excel (.xlsx) text extraction — Must handle multiple sheets, preserve data types (leading zeros, dates)
- CSV text extraction — Delimiter detection, encoding auto-detection (chardet), UTF-8-BOM handling
- PDF text extraction — Text-based PDFs only (no OCR for MVP), table extraction with pdfplumber
- Word (.docx) text extraction — Paragraphs only initially (document order parsing deferred)

**Security and validation:**
- File type validation — Client + server, MIME type + magic number verification (never trust extension)
- File size limits — 10MB default (up from 1MB for text), prevents zip bomb and memory exhaustion
- Malformed file rejection — Try-catch around parsers, clear error messages for corrupt files
- Encoding detection — chardet for CSV/TXT, handle UTF-8-BOM from Excel exports

**AI integration:**
- FTS5 search across rich docs — Extend existing full-text search to index extracted text
- AI document_search tool integration — Format-agnostic: AI receives extracted text regardless of source
- Source attribution — Extend existing chips to show sheet names for Excel references

**Should have (competitive) — v2.2+:**
Table structure preservation moves beyond flat text extraction to maintain columnar relationships, improving AI's understanding of data semantics. Excel export for artifacts creates professional requirements matrices matching BA workflows. Multi-sheet context stitching helps AI understand cross-sheet dependencies in complex workbooks. Drag-and-drop upload improves UX over file picker. Batch upload enables project folder imports.

**High-value differentiators:**
- Table structure preservation — Parse as structured data, not flat text (LLMs handle schema detection better with structure)
- Excel export for artifacts — Requirements matrices, user story tables (high BA workflow value)
- Multi-sheet context stitching — Unified context from workbooks with clear sheet separators
- Word document order parsing — Tables + paragraphs in sequence (python-docx limitation: requires custom iteration)

**Defer (v2+):**
PDF table extraction with vision LLM would improve accuracy from 67% (traditional) to 93% (AI-powered) but adds complexity and vision model costs. Cell formatting signals (colors, borders indicating priorities) require native parsing vs PDF conversion. Inline table viewer (modal) is UX polish, not core functionality. Real-time upload progress is nice-to-have. CSV export has lower priority than Excel export for BA workflows.

**Anti-features (explicitly NOT building):**
Real-time collaborative editing (massive OT/CRDT complexity, out of scope). Full Excel calculation engine (impossible to reimplement 30+ years of features). OCR for scanned PDFs (Tesseract dependency, low accuracy on complex layouts, require text-based PDFs). PDF editing/annotation (out of scope for BA tool). Version control for documents (complex conflict resolution, focus on artifacts instead). Advanced Excel features (macros = security risk, pivot tables/charts irrelevant for AI context). Inline document editor (feature creep, download-edit-reupload workflow sufficient).

### Architecture Approach

The **dual-column storage pattern** is the architectural cornerstone: `content_encrypted` stores original binary (for download/export), `content_text` stores extracted text (for FTS5 + AI). This separates concerns cleanly—storage vs search—without disrupting existing encryption or search infrastructure. The parsing layer sits between upload validation and encryption: extract text first, encrypt both binary and text separately.

**Parser adapter pattern** with factory routing enables clean extension: abstract DocumentParser interface, concrete implementations per format (ExcelParser, CSVParser, PDFParser, WordParser), ParserFactory routes content-type to parser. Each parser returns ParsedDocument dataclass with text_content (for search/AI), metadata (format-specific), and preview_data (for frontend rendering). This pattern makes adding formats trivial (new parser + factory registration) and enables isolated testing.

**Metadata-driven rendering** decouples backend structure description from frontend interpretation. Backend stores structured metadata JSON (sheet names, row count, column headers), frontend reads to decide rendering approach (TableRenderer for Excel/CSV, PDFRenderer for paginated display, WordRenderer for structured paragraphs). Format-agnostic API means GET /documents/{id} works uniformly across all types.

**Major components:**
1. **DocumentParser service** — Abstract base with format-specific adapters, extracts text + metadata from binary files
2. **Dual-column Document model** — content_encrypted (binary), content_text (encrypted extracted text), content_type (MIME), metadata_json (structure)
3. **ParserFactory** — Routes content-type to appropriate parser, single entry point for all formats
4. **Frontend format-aware renderers** — TableRenderer (Excel/CSV with pluto_grid), PDFRenderer (text + page numbers), WordRenderer (structured paragraphs)

**Integration pattern:**
```
Upload → Validate content-type → Route to parser → Extract text + metadata →
Encrypt original binary → Encrypt extracted text → Store both columns →
Index text in FTS5 → Frontend fetches with content-type for rendering
```

Existing components (FTS5, encryption, AI tools, OAuth) require minimal modification. FTS5 indexes `content_text` instead of decrypted `content_encrypted`. Encryption service adds `encrypt_binary()` and `encrypt_text()` variants. AI's search_documents tool is format-agnostic—receives extracted text regardless of source. Zero changes to Project/Thread/Message models or authentication.

**Build order follows dependencies:**
1. Database migration (all components depend on schema)
2. Parser infrastructure (routes need parsers)
3. Backend upload integration (wire parsers into routes)
4. Frontend model updates (consume new fields)
5. Frontend rendering (display parsed data)
6. Export features (optional, value-add after core works)

### Critical Pitfalls

**Top 5 pitfalls with prevention strategies:**

1. **Binary storage migration breaks existing encryption** — CRITICAL (Phase 49-01)
   - **Problem:** Storing encrypted binary data directly prevents search and AI context. Current encryption layer expects text input; binary files can't be decoded as UTF-8. Developers try to encrypt raw bytes, breaking decryption and making documents unrecoverable.
   - **Prevention:** Extract text BEFORE encryption. Store extracted text in `content_text` column (encrypted), original binary in `content_encrypted` (encrypted). Add `content_type` column to track format. Never encrypt binary directly—always extract text first.
   - **Warning signs:** UnicodeDecodeError on document view, FTS5 returns no results for new formats, AI context garbled or empty.

2. **Token budget explosion from large document context** — CRITICAL (Phase 49-02)
   - **Problem:** 50-page PDF or 20-sheet Excel can consume 50k-150k tokens, leaving minimal space for conversation. 500KB Excel → 5MB extracted text → 1.25M tokens. Users hit "context limit exceeded" or responses truncate mid-sentence.
   - **Prevention:** Enforce extraction limits (PDF: 50 pages max, Excel: 10k rows max, text: 100k chars max). Create 5k-character summary for AI context in `summary_text` column. Use full text only for FTS5 search. Chunk documents for AI (fetch relevant chunks via FTS5, not entire document in every message). Budget: system 2k + history 50k + documents 100k + response 48k = 200k total.
   - **Warning signs:** "Context too large" API errors, responses cut off, 10x token cost spike, AI ignores uploaded documents.

3. **XXE and zip bomb attacks via XLSX/DOCX** — CRITICAL (Phase 49-01)
   - **Problem:** XLSX/DOCX are ZIP archives with XML. Malicious files enable XML External Entity (XXE) attacks to exfiltrate data or zip bombs (42KB → 4.5GB in memory) crashing server. openpyxl <2.6.1 vulnerable to XXE, python-docx uses lxml which resolves external entities by default.
   - **Prevention:** Install defusedxml (`pip install defusedxml`). Use openpyxl >=3.1.0 (includes XXE protections). Validate file size BEFORE parsing (10MB max). Inspect ZIP uncompressed size before extraction (reject if >100MB uncompressed). Timeout on parsing operations (10 second max). Memory limits via subprocess or Docker.
   - **Warning signs:** Server crashes on specific files, memory spikes to 100%, 42KB file takes 30s, network requests during parsing, MemoryError logs.

4. **Excel data type auto-conversion corrupts data** — CRITICAL (Phase 49-01)
   - **Problem:** openpyxl/pandas auto-infer data types. Leading zeros disappear ("00123" → 123), scientific notation corrupts large numbers (123456789012345 → 1.23E+14), dates become integers (44927 instead of "2023-01-15"). Requirement IDs, account numbers, timestamps become unusable.
   - **Prevention:** Read all columns as strings initially (`dtype=str, na_filter=False`). Detect ID columns by name (if "ID", "Code", "Number" in column name, keep as string). Handle dates via `cell.is_date` with strftime formatting. Preserve original cell formatting using `cell.number_format`. Store extracted text exactly as Excel displays it.
   - **Warning signs:** Users report "missing leading zeros", dates show as 44927, large numbers in scientific notation, mixed types in same column.

5. **PDF table extraction fails on complex layouts** — HIGH (Phase 49-02)
   - **Problem:** pdfplumber struggles with merged cells, nested tables, irregular spacing. Accuracy drops from 96% average to <50% on complex tables. Columns merge, rows disorder, financial reports and requirement matrices become jumbled. AI interprets garbled data, producing incorrect BRDs.
   - **Prevention:** Detect table presence, warn users of complex layouts. Provide table extraction settings (vertical/horizontal strategy, intersection tolerance). Quality check extracted tables (validate row/column structure consistency). Show preview of extracted text with "Does this look correct?" confirmation before final upload. Consider fallback to image extraction for low-confidence results.
   - **Warning signs:** Users report "scrambled text", tables show merged cells as separate columns, AI references incorrect table data, FTS5 matches but results incomprehensible.

**Additional high-severity pitfalls:**
- **FTS5 index out-of-sync** — Extract and validate text BEFORE database insert (Phase 49-01)
- **CSV encoding issues** — Auto-detect with chardet, handle UTF-8-BOM from Excel exports (Phase 49-01)
- **WeasyPrint memory exhaustion** — Limit export size to 1000 rows, background jobs for large exports (Phase 49-03)
- **Flutter DataTable browser freeze** — Pagination or virtualization at 100+ rows (Phase 49-02)
- **SQLite batch insert performance** — Single transaction for batch uploads, not per-file commits (Phase 49-01)

## Implications for Roadmap

Based on combined research, Rich Document Support should be structured into **3-4 sequential phases** following a "foundation → integration → polish" pattern. The architecture demands database-first (all components depend on schema), parsers before routes (can't process without extraction), and backend before frontend (API must exist before UI consumes it).

### Phase 1: Backend Foundation (File Upload & Parsing)

**Rationale:** Database schema and parser infrastructure are dependencies for all other work. Security validation (XXE, zip bombs, data type preservation) must happen at upload time—remediation is expensive or impossible after storage. This phase establishes the text extraction pipeline that feeds search and AI context.

**Delivers:**
- Database migration adding `content_type`, `content_text`, `metadata_json` columns
- DocumentParser base class + concrete parsers (Excel, CSV, PDF, Word)
- ParserFactory for content-type routing
- Updated upload route supporting 4 new formats with security validation
- Encryption service variants for binary vs text
- FTS5 indexing of extracted text

**Addresses features:**
- Excel/CSV/PDF/Word text extraction (table stakes)
- File type validation + size limits (security baseline)
- Encoding detection for CSV (international character support)
- Malformed file rejection (error handling)

**Avoids pitfalls:**
- Pitfall 1: Binary storage breaks encryption (extract text first)
- Pitfall 2: FTS5 out-of-sync (validate before insert)
- Pitfall 4: XXE/zip bomb attacks (defusedxml, size limits, timeouts)
- Pitfall 6: Excel data type corruption (dtype=str, preserve formatting)
- Pitfall 7: CSV encoding issues (chardet auto-detection)
- Pitfall 10: Batch insert performance (single transaction)

**Technical notes:**
Use openpyxl read-only mode for performance. Install defusedxml immediately. Validate uncompressed ZIP size before parsing XLSX/DOCX. Store extracted text as encrypted bytes in `content_text` column, original binary in `content_encrypted`. Index text extraction in same transaction as document insert.

### Phase 2: Frontend Display & AI Context

**Rationale:** Backend can now parse and store rich documents. This phase makes them visible to users and usable by AI. Token budget management prevents context explosion that would make AI unusable with multiple documents. Preview validation prevents bad data from entering the system.

**Delivers:**
- Updated Document model with contentType, metadata fields
- Format-aware DocumentViewer with specialized renderers
- TableRenderer widget using pluto_grid (Excel/CSV)
- PDFRenderer and WordRenderer widgets
- Visual table preview in upload dialog (first 10 rows)
- Sheet selector for Excel uploads
- Token budget allocation (100k tokens for documents)
- Document summarization for AI context (5k chars per doc)

**Addresses features:**
- Visual table preview (users verify data before upload)
- Sheet selector for Excel (choose which sheets to parse)
- Document metadata display (row count, sheet names, page count)
- Download rich documents (serve original encrypted file)
- Display extracted text content (users verify what AI sees)
- AI reads rich document content (extend document_search tool)
- Source attribution for rich docs (show sheet names in chips)

**Avoids pitfalls:**
- Pitfall 3: Token budget explosion (5k summaries, 100k doc budget)
- Pitfall 5: PDF table extraction fails (preview with confirmation)
- Pitfall 9: DataTable freezes browser (pluto_grid pagination/virtualization)

**Technical notes:**
pluto_grid handles 10k rows well with lazy loading. For preview, limit to first 100 rows (preview_data in metadata_json). For AI context, use FTS5 search to fetch relevant chunks, not full document. Store both full text (search) and summary (AI context).

### Phase 3: Export Features (Optional)

**Rationale:** Core upload and viewing functionality complete. Export adds value for BA workflows (requirements matrices, user story tables). This phase is independent—can be deferred if timeline tight.

**Delivers:**
- GET /documents/{id}/export?format=csv endpoint
- Backend Excel/CSV generation from parsed data
- Frontend download button with format picker
- Size limits and background jobs for large exports

**Addresses features:**
- Export to Excel (requirements matrices, high BA value)
- Export to CSV (data portability, analysis tools)

**Avoids pitfalls:**
- Pitfall 8: WeasyPrint memory exhaustion (1000 row limit, background jobs)

**Technical notes:**
Use openpyxl for Excel generation (same library as parsing). WeasyPrint already handles PDF export. Limit export to 1000 rows; queue larger exports as background tasks. Consider reportlab for direct PDF generation (streaming, lower memory than HTML→PDF).

### Phase Ordering Rationale

**Why Phase 1 first (Backend Foundation):**
- Database schema is dependency for all other work (can't update models without columns)
- Security validation must happen at upload time (XXE/zip bombs can't be fixed after storage)
- Text extraction enables search and AI (core value prop depends on this)
- Parser infrastructure required before routes can accept new formats

**Why Phase 2 second (Frontend Display & AI Context):**
- Backend API must exist before frontend can consume it
- Token budget management prevents AI becoming unusable after launch
- Preview validation catches bad data before storage (cheaper than remediation)
- Virtualization prevents browser freezes (UX issue would require emergency fix)

**Why Phase 3 last (Export Features):**
- Independent of core upload/view functionality
- Lower priority than consumption (viewing + AI usage)
- Can be deferred if timeline pressure (MVP works without export)

**Dependency chain:**
```
Schema migration → Parsers → Upload routes → Frontend models → Renderers → Export
     ↓               ↓            ↓              ↓              ↓
 All depend on  Routes need   AI needs    UI needs      Value-add
   columns       parsers      backend     backend      after core
                                API        API works
```

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 1 (Backend Foundation):** openpyxl API documentation for read-only mode, data type preservation patterns, defusedxml integration with python-docx. pdfplumber table extraction settings for complex layouts. chardet encoding detection thresholds (confidence scores for fallback chain).
- **Phase 2 (Frontend Display):** pluto_grid virtualization configuration for 10k+ rows, lazy loading patterns. Flutter web file download patterns (file_saver integration). Token estimation algorithms (chars → tokens for different models).

**Phases with standard patterns (skip research-phase):**
- **Phase 3 (Export):** openpyxl write patterns well-documented. WeasyPrint memory limits have established solutions (size caps, background jobs).

**During execution, if complexity spikes:**
Use `/gsd:research-phase` for:
- PDF table extraction if accuracy <70% on test files (may need vision LLM research)
- Excel formula preservation if users request calculated values (complex parsing)
- Word document order parsing if paragraph-only insufficient (python-docx iteration patterns)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries verified with official docs (PyPI, pub.dev). Version compatibility confirmed with Python 3.9 and current Flutter SDK. Licensing reviewed (avoided AGPL trap with pdfplumber over PyMuPDF). |
| Features | MEDIUM | Table stakes features validated with multiple sources (competitor analysis, OWASP security guidelines). Differentiator priorities based on BA workflow research. Anti-features identified from feature creep patterns. Some UX details need user testing. |
| Architecture | HIGH | Dual-column pattern verified with SQLite blob storage best practices. Parser adapter pattern confirmed against 2025-2026 document parsing implementations. Integration points validated via existing codebase analysis (models.py, routes/documents.py, document_search.py). |
| Pitfalls | HIGH | Security vulnerabilities confirmed with CVE databases (XXE: CVE-2017-5992, zip bombs: CVE-2024-0450). Performance traps validated with GitHub issues (WeasyPrint #1104, Flutter DataTable #62596). Token budget math verified against Claude context window specs. |

**Overall confidence:** HIGH

Research is production-ready. Stack choices are mature and well-documented. Architecture integrates cleanly with existing system (minimal disruption). Security pitfalls are well-known with established mitigations. Performance traps have proven solutions.

### Gaps to Address

**Minor gaps requiring validation during implementation:**

- **pdfplumber table extraction accuracy:** Research shows 67-96% accuracy depending on layout complexity. Need to test with real BA documents (requirement matrices, financial reports) to determine if MVP quality sufficient or if vision LLM needed sooner. Test strategy: upload 10 sample PDFs from real projects, measure extraction quality.

- **Token estimation algorithm:** Research provides rough guidelines (1 char ≈ 0.25 tokens) but varies by model and language. Need to implement empirical measurement: send sample documents to Claude API, track actual token usage, build calibration curve. This affects summarization thresholds.

- **Excel formula handling:** Research confirms openpyxl can access formulas, but unclear if BA users need calculated values, formulas, or both. During Phase 1 execution, add basic formula detection (warn if formulas present), defer full preservation until user feedback. Document as "known limitation" in MVP.

- **Word document order parsing:** python-docx limitation well-documented (can read all paragraphs OR all tables, not interspersed). Research shows custom iteration possible via document._element. Complexity HIGH, defer to v2.2+ unless users report missing context from interleaved content. Test with real BRDs during Phase 2 to validate paragraph-only extraction.

- **Batch upload UX:** Research shows progress indicators critical for >5 files, but unclear if users upload in batches. During Phase 1, implement single transaction (performance) but defer progress UI until user feedback requests it. Can add via WebSocket or SSE later if needed.

**How to handle during planning:**
- **Test with real data:** Source sample Excel/PDF/Word files from typical BA workflows during Phase 1 planning
- **Measure, don't guess:** Add instrumentation for token usage, parsing time, extraction quality from day 1
- **Document limitations:** Known gaps (paragraph-only Word parsing, formula detection) go in release notes, not blocking issues
- **Defer until feedback:** Don't add complexity (vision LLM, document order parsing) until users confirm need

**No blocking gaps.** Implementation can proceed immediately. Gaps are optimization opportunities, not architecture unknowns.

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- [openpyxl PyPI](https://pypi.org/project/openpyxl/) — Version 3.1.5, Python Excel library
- [pdfplumber PyPI](https://pypi.org/project/pdfplumber/) — Version 0.11.8, PDF text extraction
- [chardet PyPI](https://pypi.org/project/chardet/) — Version 5.2.0, encoding detection
- [python-docx Documentation](https://python-docx.readthedocs.io/) — Word document parsing
- [excel package pub.dev](https://pub.dev/packages/excel) — Flutter Excel read/write
- [pluto_grid pub.dev](https://pub.dev/packages/pluto_grid) — Flutter data grid widget
- [FastAPI Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) — Multipart upload handling
- [SQLite FTS5 Extension](https://sqlite.org/fts5.html) — Full-text search capabilities
- [SQLite BLOB Storage](https://sqlite.org/intern-v-extern-blob.html) — Binary storage patterns

**Security Advisories:**
- [CVE-2017-5992: XXE in openpyxl](https://security.snyk.io/vuln/SNYK-PYTHON-OPENPYXL-40459)
- [CVE-2024-0450: Zip bomb in Python](https://security.snyk.io/vuln/SNYK-UNMANAGED-PYTHON-7924823)
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)

### Secondary (MEDIUM confidence)

**Technical Comparisons:**
- [PDF Extractors Comparison 2025](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257) — Performance benchmarks
- [Python Libraries for Document Parsing](https://medium.com/@hchenna/technical-comparison-python-libraries-for-document-parsing-318d2c89c44e) — openpyxl vs pandas vs PyPDF2
- [openpyxl vs xlrd comparison](https://stackshare.io/stackups/pypi-openpyxl-vs-pypi-xlrd) — Why xlrd deprecated
- [PyMuPDF licensing](https://pymupdf.readthedocs.io/en/latest/about.html) — AGPL vs commercial license

**Best Practices:**
- [Intelligent Document Parsing Guide](https://medium.com/@surajkhaitan16/the-ultimate-guide-to-intelligent-document-parsing-building-a-universal-file-reader-system-2fe285fca319) — BaseReader architecture pattern
- [UX best practices for file upload](https://uploadcare.com/blog/file-uploader-ux-best-practices/) — Progress indicators, validation
- [Data Table Design UX Patterns](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables) — Table preview best practices

**Performance Research:**
- [WeasyPrint memory issues #1104](https://github.com/Kozea/WeasyPrint/issues/1104) — 5000-row table memory consumption
- [Flutter DataTable jank #62596](https://github.com/flutter/flutter/issues/62596) — Performance issues >100 rows
- [SQLite bulk insert optimization](https://www.pdq.com/blog/improving-bulk-insert-speed-in-sqlite-a-comparison-of-transactions/) — Transaction batching
- [openpyxl performance docs](https://openpyxl.readthedocs.io/en/stable/performance.html) — Read-only mode, optimized iteration

**AI Context Management:**
- [Context Window Problem](https://factory.ai/news/context-window-problem) — Token budget strategies
- [Best LLMs for Extended Context](https://aimultiple.com/ai-context-window) — 200k context window management

**Data Type Handling:**
- [Avoiding automatic data type conversion](https://sachachua.com/blog/2021/12/avoiding-automatic-data-type-conversion-in-microsoft-excel-and-pandas/) — Leading zeros, dates
- [How pandas infers data types](https://rushter.com/blog/pandas-data-type-inference/) — dtype=str patterns
- [CSV encoding issues](https://hilton.org.uk/blog/csv-excel/) — UTF-8-BOM, Windows-1252

### Tertiary (Context validation)

**Existing Codebase Analysis:**
- `backend/app/models.py` — Document model structure, encryption patterns
- `backend/app/routes/documents.py` — Upload route, validation logic
- `backend/app/services/document_search.py` — FTS5 indexing integration
- `backend/app/services/encryption.py` — Current encryption layer
- `frontend/lib/models/document.dart` — Document model structure
- `frontend/lib/screens/documents/document_viewer_screen.dart` — Existing text display patterns

---

**Research completed:** 2026-02-12
**Ready for roadmap:** YES

**Next steps:**
1. Load SUMMARY.md as context during roadmap creation (`/gsd:new-roadmap`)
2. Use phase suggestions as starting point (3-phase structure: Backend Foundation → Frontend Display & AI Context → Export Features)
3. Reference pitfall-to-phase mapping during task planning
4. Flag Phase 1 and Phase 2 for openpyxl/pdfplumber API research during execution
5. Phase 3 (Export) uses standard patterns, skip research-phase
