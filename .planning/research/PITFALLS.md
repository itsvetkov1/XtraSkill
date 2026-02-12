# Pitfalls Research: Rich Document Support

**Domain:** Adding Excel/CSV/PDF/Word parsing to existing text-only document system
**Researched:** 2026-02-12
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Binary Storage Migration Breaks Existing Encryption

**What goes wrong:**
Current system stores encrypted text as `LargeBinary` (bytes), but the encryption layer assumes plaintext input. When adding binary file formats (xlsx, docx, pdf), developers often try to encrypt the raw binary data instead of extracted text, breaking decryption and making documents unrecoverable.

**Why it happens:**
- Current code: `content_bytes.decode('utf-8')` → `encrypt_document(plaintext)` → stores as bytes
- Binary files: Raw bytes can't be decoded as UTF-8
- Confusion: "content_encrypted is already bytes, so store binary directly" logic seems reasonable
- Schema says `LargeBinary` which implies "put binary data here"

**How to avoid:**
1. **Keep encryption working on TEXT, not binary:** Extract text from binary formats FIRST, then encrypt the extracted text
2. **Add content_type column:** Store original format separately (e.g., `application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
3. **Add metadata column:** Store original_filename, file_size, sheet_names (for Excel), page_count (for PDF) as JSON
4. **Separate binary and text paths clearly:**
   ```python
   # Binary upload → Extract text → Encrypt text → Store encrypted text
   # NOT: Binary upload → Encrypt binary → Store (breaks search, AI context)
   ```

**Warning signs:**
- UnicodeDecodeError when trying to view uploaded Excel/PDF documents
- FTS5 search returns no results for new document types
- AI context is garbled or empty when including rich documents
- Encryption service throws "expected string, got bytes" errors

**Phase to address:**
Phase 49-01 (File Upload & Parsing) — Must establish text extraction pipeline before storage

---

### Pitfall 2: FTS5 Index Out-of-Sync with Document Table

**What goes wrong:**
Current system indexes documents in the same transaction as insert (`await index_document(db, doc.id, doc.filename, plaintext)`). When adding text extraction for binary formats, extraction can fail AFTER document insert but BEFORE index, leaving orphaned documents that won't appear in search results. Worse: re-uploading fails because document exists but has no FTS5 entry.

**Why it happens:**
- Text extraction from PDF/Excel can fail (corrupted file, unsupported encoding, missing dependencies)
- Current code does: insert document → index document (if this fails, transaction rolls back)
- Binary files add failure modes: openpyxl import errors, pdfplumber memory exhaustion, WeasyPrint crashes
- Developers wrap only the insert in try/catch, not the indexing

**How to avoid:**
1. **Extract and validate text BEFORE database insert:**
   ```python
   # CORRECT order:
   binary_content = await file.read()
   extracted_text = extract_text(binary_content, content_type)  # Fail here if extraction broken
   encrypted = encrypt(extracted_text)
   doc = Document(...)  # Only create if extraction succeeded
   await index_document(...)
   ```
2. **Add extraction validation:** Ensure extracted text is non-empty and reasonable length
3. **Database constraint:** FTS5 indexing must be in same transaction (current approach is correct, just move extraction earlier)
4. **Migration path:** When adding FTS5 to existing documents, use background task with retry logic

**Warning signs:**
- Document count != FTS5 row count
- "Document uploaded successfully" but search returns nothing
- Error logs show "document X has no FTS5 entry"
- Re-uploading same file gives "file already exists" but file isn't searchable

**Phase to address:**
Phase 49-01 (File Upload & Parsing) — Text extraction must complete before insert

---

### Pitfall 3: Token Budget Explosion from Large Document Context

**What goes wrong:**
Current system passes full document content to AI during conversations. A 50-page PDF or 20-sheet Excel file can consume 50k-150k tokens, leaving minimal space for conversation history and responses. Users hit "context limit exceeded" errors or responses get truncated mid-sentence. With Claude's 200k context window, 3-4 large documents fill the entire context.

**Why it happens:**
- Text-only MVP had 1MB limit → ~250k characters → ~60k tokens max
- Binary formats compress: 500KB Excel file → 5MB extracted text → 1.25M tokens
- Developers test with small files, production users upload massive spreadsheets
- No per-document token estimation before adding to context
- "Lost in the middle" phenomenon: AI can't access info buried in middle of 100k+ token context

**How to avoid:**
1. **Enforce text extraction limits:**
   - PDF: Max 50 pages or 100k characters of extracted text
   - Excel: Max 10,000 rows across all sheets or 100k characters
   - CSV: Max 50k rows or 50k characters
   - Word: Max 100 pages or 100k characters
2. **Implement smart truncation:**
   - Store full extracted text separately
   - Create 5k-character summary for AI context (store in `summary_text` column)
   - Use full text only for FTS5 search
3. **Document chunking for AI:**
   - When user references document in chat, fetch relevant chunks via FTS5 search
   - Don't include entire document in every message
4. **Add token estimation endpoint:** Show "This document will use ~X tokens" before upload
5. **Context budget allocation:**
   - System prompt: 2k tokens
   - Conversation history: 50k tokens
   - Documents: 100k tokens (distributed across N documents)
   - Response buffer: 48k tokens
   - Total: 200k tokens

**Warning signs:**
- "Context too large" errors from AI API
- Responses cut off mid-sentence
- Slow response times (large context = slower generation)
- Token costs spike 10x after adding rich document support
- Users report "AI ignores my uploaded documents"

**Phase to address:**
Phase 49-02 (Document Viewer & AI Context) — Must implement smart context management before AI integration

---

### Pitfall 4: XXE and Zip Bomb Attacks via XLSX/DOCX

**What goes wrong:**
XLSX and DOCX files are ZIP archives containing XML files. Malicious files can include:
- **XXE (XML External Entity) attacks:** XML references external URLs to exfiltrate data
- **Zip bombs:** 42KB file expands to 4.5GB in memory, crashing the server
- **Billion laughs attack:** Nested XML entities cause exponential memory expansion

openpyxl versions before 2.6.1 are vulnerable to XXE. python-docx uses lxml which resolves external entities by default unless defusedxml is installed.

**Why it happens:**
- Developers install `openpyxl` and `python-docx` without reading security warnings
- Test files are benign, malicious files only appear in production
- Solo developer doesn't have security review process
- "It's just a spreadsheet" mindset ignores XML parsing risks

**How to avoid:**
1. **Install defusedxml:** `pip install defusedxml` (protects lxml-based parsers)
2. **Use latest versions:**
   - openpyxl >= 3.1.0 (includes XXE protections)
   - python-docx >= 0.8.11 (latest stable)
3. **File size validation BEFORE parsing:**
   ```python
   MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB max
   if len(content_bytes) > MAX_UPLOAD_SIZE:
       raise HTTPException(413, "File too large")
   ```
4. **Zip inspection before extraction:**
   ```python
   import zipfile
   with zipfile.ZipFile(io.BytesIO(content_bytes)) as zf:
       total_uncompressed = sum(info.file_size for info in zf.infolist())
       if total_uncompressed > 100 * 1024 * 1024:  # 100MB uncompressed
           raise HTTPException(400, "Zip bomb detected")
   ```
5. **Timeout on parsing operations:**
   ```python
   import signal
   signal.alarm(10)  # 10 second timeout on extraction
   try:
       extracted_text = extract_text(content_bytes)
   finally:
       signal.alarm(0)
   ```
6. **Memory limits:** Run parsing in subprocess with memory limit (e.g., Docker container with `--memory=512m`)

**Warning signs:**
- Server crashes when uploading specific XLSX/DOCX files
- Memory usage spikes to 100% during file processing
- Slow response times for "small" files (42KB file takes 30 seconds)
- Network requests to external IPs during file processing (XXE exfiltration)
- Log files show "MemoryError" during openpyxl/docx operations

**Phase to address:**
Phase 49-01 (File Upload & Parsing) — CRITICAL: Security validation before any parsing

---

### Pitfall 5: PDF Table Extraction Fails on Complex Layouts

**What goes wrong:**
pdfplumber successfully extracts text from PDFs but fails on tables with merged cells, nested tables, or irregular spacing. Extracted text becomes jumbled, with columns merged together or rows out of order. Users upload financial reports or requirement matrices and get unusable text. AI interprets garbled data, producing incorrect BRDs.

**Why it happens:**
- pdfplumber accuracy drops from 96% average to <50% on complex tables
- Merged cells aren't detected correctly (sees as separate cells)
- Irregular column spacing causes misalignment
- Developers test with simple PDFs (native text, no tables)
- Production users upload scanned documents (require OCR, not text extraction)

**How to avoid:**
1. **Detect table presence:**
   ```python
   page = pdf.pages[0]
   tables = page.extract_tables()
   if tables and len(tables) > 0:
       # Warn user: "Complex tables detected, extraction may be inaccurate"
   ```
2. **Provide table extraction settings:**
   ```python
   # Let user adjust table detection parameters
   table_settings = {
       "vertical_strategy": "lines",  # or "text"
       "horizontal_strategy": "lines",
       "intersection_tolerance": 3
   }
   tables = page.extract_tables(table_settings=table_settings)
   ```
3. **Fallback to image extraction:**
   - If table extraction produces low confidence results, save table as image
   - Display image in Document Viewer instead of garbled text
   - Use OCR (tesseract) for scanned PDFs
4. **Quality check extracted tables:**
   ```python
   def validate_table(table):
       # Check for reasonable row/column structure
       if not table or len(table) < 2:
           return False
       row_lengths = [len(row) for row in table]
       # All rows should have similar column count
       return max(row_lengths) - min(row_lengths) <= 2
   ```
5. **User feedback loop:**
   - Show preview of extracted text before final upload
   - "Does this look correct?" confirmation step
   - Allow re-upload with different settings

**Warning signs:**
- Users report "uploaded document text is scrambled"
- Tables in Document Viewer show merged cells as separate columns
- AI responses reference incorrect data from tables
- FTS5 search matches table content but results are incomprehensible
- Complaints about specific document types (financial reports, legal documents)

**Phase to address:**
Phase 49-02 (Document Viewer) — Must detect and handle complex tables before showing to users

---

### Pitfall 6: Excel Data Type Auto-Conversion Corrupts Data

**What goes wrong:**
pandas and openpyxl auto-infer data types when reading Excel files. Leading zeros disappear from IDs ("00123" → 123), scientific notation corrupts large numbers (123456789012345 → 1.23E+14), dates appear as integers (44927 instead of "2023-01-15"). Users upload requirement IDs, account numbers, or timestamps and data becomes unusable.

**Why it happens:**
- Excel stores "00123" as number 123, not string
- pandas `read_excel()` infers types per-chunk, causing mixed types in same column
- Developers test with clean datasets, production has messy real-world data
- No dtype specification = pandas guesses (often wrong)

**How to avoid:**
1. **Read all columns as strings initially:**
   ```python
   df = pd.read_excel(file, dtype=str, na_filter=False)
   # Preserve exact values as user sees them
   ```
2. **Detect numeric-looking IDs:**
   ```python
   # If column name contains "ID", "Code", "Number", keep as string
   id_columns = [col for col in df.columns if any(kw in col.lower() for kw in ["id", "code", "number"])]
   ```
3. **Date handling:**
   ```python
   # Check for Excel date serial numbers (e.g., 44927)
   if cell.is_date:
       value = cell.value.strftime('%Y-%m-%d')
   ```
4. **Low_memory=False for consistency:**
   ```python
   # Force pandas to read entire file before inferring types
   df = pd.read_excel(file, dtype=str, low_memory=False)
   ```
5. **Preserve original cell formatting:**
   - Store extracted text exactly as Excel displays it (not as underlying data)
   - Use openpyxl `cell.number_format` to format numbers correctly

**Warning signs:**
- Users report "my requirement IDs are missing leading zeros"
- Date columns show numbers like 44927 instead of dates
- Large numbers appear in scientific notation (1.23E+14)
- Mixed types in same column ("123" vs 123)
- FTS5 search fails to find IDs because "00123" stored as "123"

**Phase to address:**
Phase 49-01 (File Upload & Parsing) — Text extraction must preserve data as-seen in Excel

---

### Pitfall 7: CSV Encoding Issues Corrupt Non-ASCII Characters

**What goes wrong:**
CSV files have no standardized encoding. Users upload CSVs with UTF-8, Windows-1252, or UTF-8-with-BOM encoding. Special characters appear as mojibake (é → Ã©, — → â€"), breaking search and AI context. Excel exports CSVs with UTF-8-BOM which Python reads incorrectly, prepending ï»¿ to first column name.

**Why it happens:**
- No encoding metadata in CSV files (unlike XLSX which embeds encoding)
- Excel exports UTF-8-with-BOM on Windows, UTF-8 on Mac
- Users export from different tools (Excel, Google Sheets, database exports)
- Python defaults to `encoding='utf-8'` which fails on Windows-1252 files
- Developers test on their own machine, same encoding every time

**How to avoid:**
1. **Auto-detect encoding:**
   ```python
   import chardet

   result = chardet.detect(content_bytes)
   encoding = result['encoding']  # e.g., 'utf-8', 'windows-1252'
   text = content_bytes.decode(encoding)
   ```
2. **Handle UTF-8-BOM:**
   ```python
   if text.startswith('\ufeff'):  # UTF-8 BOM
       text = text[1:]  # Strip BOM
   ```
3. **Fallback encoding chain:**
   ```python
   for encoding in ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1']:
       try:
           text = content_bytes.decode(encoding)
           break
       except UnicodeDecodeError:
           continue
   else:
       raise HTTPException(400, "Unable to detect file encoding")
   ```
4. **Normalize to UTF-8 for storage:**
   - Always store extracted text as UTF-8 in database
   - Document content_encoding in metadata if original was different
5. **User encoding override:**
   - Provide dropdown: "File encoding: UTF-8 | Windows-1252 | Auto-detect"

**Warning signs:**
- Special characters appear as � or mojibake
- First column name has weird prefix (ï»¿Product_ID)
- Users report "French/Spanish characters are broken"
- FTS5 search fails on accented characters
- CSV files from Windows users fail, Mac users work fine

**Phase to address:**
Phase 49-01 (File Upload & Parsing) — Encoding detection during CSV processing

---

### Pitfall 8: WeasyPrint Memory Exhaustion on Large PDF Export

**What goes wrong:**
WeasyPrint loads entire document into memory before rendering. Exporting a 100-row Excel table as PDF spikes memory to 1.8GB+ and takes 60+ seconds. Server runs out of memory with concurrent exports. Users report "Export failed" with no useful error message.

**Why it happens:**
- WeasyPrint architecture requires full document in-memory (no streaming)
- Memory usage = ~50x original HTML size
- Tables with 5,000+ rows cause exponential memory growth
- Developers test with small documents, production has large spreadsheets
- No memory or timeout limits on export endpoint

**How to avoid:**
1. **Limit export size:**
   ```python
   MAX_EXPORT_ROWS = 1000
   if row_count > MAX_EXPORT_ROWS:
       raise HTTPException(400, f"Document too large for PDF export (max {MAX_EXPORT_ROWS} rows)")
   ```
2. **Pagination for large documents:**
   - Split into multiple PDFs if >1000 rows
   - Generate PDF per-sheet for Excel with many sheets
3. **Memory monitoring:**
   ```python
   import psutil

   before_memory = psutil.Process().memory_info().rss
   # Export operation
   after_memory = psutil.Process().memory_info().rss
   if after_memory - before_memory > 500 * 1024 * 1024:  # 500MB spike
       logger.warning("Large memory usage during PDF export")
   ```
4. **Background job for large exports:**
   - If document > 500 rows, queue as background task
   - Return "Export in progress, will email when ready"
5. **Alternative: Direct PDF generation:**
   - Use reportlab instead of HTML→PDF for tables
   - Streaming output, constant memory usage

**Warning signs:**
- Server memory usage spikes during PDF exports
- "502 Bad Gateway" errors on export endpoint
- Export takes >30 seconds for moderate-size documents
- OOM (Out of Memory) kills in server logs
- Multiple concurrent exports crash the server

**Phase to address:**
Phase 49-03 (Export Features) — Size limits and background jobs before enabling export

---

### Pitfall 9: Flutter DataTable Freezes Browser with 1000+ Rows

**What goes wrong:**
Flutter's DataTable widget is expensive to render. Displaying an Excel file with 1,000+ rows freezes the browser for 10+ seconds. Scrolling is janky. Users can't interact with the app while table renders. Mobile browsers crash entirely.

**Why it happens:**
- DataTable measures all rows twice (dimension negotiation + layout)
- No virtualization: renders ALL rows even if off-screen
- Flutter web uses canvas rendering (slower than DOM for tables)
- Developers test with 10-row samples, production has 5,000-row spreadsheets

**How to avoid:**
1. **Use pagination for large tables:**
   ```dart
   // Show 50 rows per page
   PaginatedDataTable(
     rowsPerPage: 50,
     columns: [...],
     source: MyDataTableSource(data),
   )
   ```
2. **Virtualized scrolling:**
   - Use `two_dimensional_scrollables.TableView` instead of DataTable
   - Renders only visible rows (constant memory/performance)
3. **Lazy loading:**
   ```dart
   // Load first 100 rows immediately, load more on scroll
   if (scrollController.position.pixels > threshold) {
     loadMoreRows();
   }
   ```
4. **Size warning before render:**
   ```dart
   if (rowCount > 500) {
     // Show dialog: "Large table detected. Switch to paginated view?"
   }
   ```
5. **Alternative view for huge tables:**
   - Offer "Download as CSV" instead of rendering
   - Show summary stats instead of full table

**Warning signs:**
- Browser "Page Unresponsive" warnings
- Scroll lag/jank on table views
- Memory usage climbs during table render
- Users report "app freezes when opening documents"
- Mobile users can't view Excel documents (crash)

**Phase to address:**
Phase 49-02 (Document Viewer) — Virtualization before rendering large tables

---

### Pitfall 10: SQLite Batch Insert Performance Degrades Without Transactions

**What goes wrong:**
Uploading 50 documents in batch takes 60+ seconds because each insert is its own transaction. SQLite fsync after every insert. Users think the app is broken, refresh page, restart upload (making it worse).

**Why it happens:**
- Current code uses `await db.commit()` per document
- SQLite default: auto-commit per statement
- Developers test with 1-2 file uploads, production has bulk imports
- No progress indicator for batch operations

**How to avoid:**
1. **Single transaction for batch uploads:**
   ```python
   async with db.begin():  # Single transaction
       for file in files:
           # Extract, encrypt, insert, index
           # No commit until all complete
   ```
2. **Prepared statements:**
   ```python
   # Compile insert statement once, execute many times
   stmt = insert(Document).values(...)
   for file in files:
       await db.execute(stmt, params)
   ```
3. **Batch size limits:**
   ```python
   MAX_BATCH_SIZE = 50
   if len(files) > MAX_BATCH_SIZE:
       # Process in chunks of 50
   ```
4. **Progress tracking:**
   ```python
   # WebSocket or SSE to send "Processed 15/50 files..."
   for i, file in enumerate(files):
       process_file(file)
       await send_progress(i+1, len(files))
   ```
5. **Rollback on partial failure:**
   ```python
   try:
       # Process all files
   except Exception:
       await db.rollback()
       raise HTTPException(400, "Batch upload failed, no documents saved")
   ```

**Warning signs:**
- Batch upload takes >1 second per file
- SQLite WAL file grows large during batch operations
- Users report "upload seems stuck"
- Server CPU usage spikes during batch uploads
- Logs show many individual INSERT statements instead of batched

**Phase to address:**
Phase 49-01 (File Upload) — Batch optimization before enabling multi-file upload

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip text extraction limits | Faster MVP, no truncation logic | Token budget explosions, slow AI responses | Never (limits prevent production issues) |
| Store binary data directly | Simpler upload code | No search, no AI context, breaks encryption | Never (defeats purpose of documents) |
| No encoding detection for CSV | Works with UTF-8 files | Breaks on Windows exports, user complaints | MVP only (add before beta) |
| Use pandas for all Excel parsing | Easy to implement | 50x memory overhead, zip bomb risk | Small files only (<5MB, <1000 rows) |
| No progress indicators | Less frontend code | Users think app is broken during batch uploads | Never (poor UX) |
| Skip XXE protection | Faster implementation | Security vulnerability, data exfiltration | Never (critical security) |
| Render full table in DataTable | Simple code | Browser freezes, bad UX | Tables <100 rows only |
| Export without size limits | Feature "works" immediately | Server crashes, OOM errors | Never (DoS risk) |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FTS5 indexing | Index after commit (orphaned documents) | Index in same transaction as insert |
| Encryption service | Encrypt binary data directly | Extract text first, then encrypt extracted text |
| AI context | Include full document content | Summarize or chunk, use 5k-character limit per doc |
| PDF parsing | Assume text-based PDFs | Detect scanned PDFs, use OCR (Tesseract) |
| Excel date parsing | Read as numbers | Check `cell.is_date`, format with strftime |
| CSV encoding | Default to UTF-8 | Auto-detect with chardet, handle BOM |
| WeasyPrint export | Export on main thread | Background job for >500 rows |
| DataTable rendering | Render all rows | Paginate or virtualize at 100+ rows |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full Excel into pandas | Memory spike, slow processing | Use `openpyxl` in read-only mode, stream rows | Files >5MB or >10k rows |
| No batch transaction | Slow bulk uploads (1s per file) | Single transaction for batch operations | Uploading >5 files |
| Rendering 1000+ rows in DataTable | Browser freeze, "Page Unresponsive" | Pagination or virtualization | Tables >100 rows |
| WeasyPrint full-document render | Memory exhaustion, 60s+ exports | Size limits + background jobs | Exporting >500 rows |
| Including all documents in AI context | Context limit errors, slow responses | Smart chunking, 100k token budget for docs | >3 large documents per chat |
| Synchronous text extraction | Request timeout, blocking server | Async extraction with timeout | Files >10MB |
| No zip inspection before parsing | Zip bomb extracts 4.5GB | Check uncompressed size first | Any malicious XLSX/DOCX |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Parse XLSX without defusedxml | XXE attack, data exfiltration | Install defusedxml, use openpyxl >=3.1.0 |
| No file size validation before parsing | Zip bomb DoS | Validate compressed AND uncompressed size |
| Client-side file type validation only | Attacker uploads .exe as .xlsx | Server-side content-type + magic number check |
| No timeout on text extraction | Infinite loop in parsing, DoS | 10-second timeout per file |
| Trust user-provided filenames | Path traversal, overwrite system files | Sanitize filenames, use UUIDs for storage |
| Parse Excel formulas | Formula injection (CSV injection) | Strip formulas, store values only |
| No memory limits on parsing | Memory exhaustion DoS | Subprocess with memory limit (--memory=512m) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No upload progress indicator | Users think app is broken, refresh page | WebSocket or SSE progress: "Processing file 3/10..." |
| Silent table extraction failure | Garbled text in Document Viewer | Preview extracted text, "Does this look correct?" |
| No error details on upload failure | "Upload failed" with no reason | Specific errors: "File too large (15MB, max 10MB)" |
| Render massive table immediately | Browser freeze, can't cancel | Warn "Large table detected. Load anyway?" |
| Export hangs without feedback | User clicks Export, nothing happens | "Generating PDF... 45% complete" or "Export queued" |
| No file size limit indication | Trial-and-error to find limit | "Max file size: 10MB" label on upload button |
| Auto-extract text without preview | User uploads wrong file, can't undo | Preview + confirm before final save |

## "Looks Done But Isn't" Checklist

- [ ] **Excel parsing:** Often missing data type preservation — verify leading zeros and dates render correctly
- [ ] **PDF table extraction:** Often missing complex layout handling — verify merged cells and nested tables
- [ ] **CSV import:** Often missing encoding detection — verify UTF-8-BOM and Windows-1252 files
- [ ] **Text extraction:** Often missing size limits — verify 1000-page PDF doesn't consume 500k tokens
- [ ] **FTS5 indexing:** Often missing transaction coordination — verify search works immediately after upload
- [ ] **AI context:** Often missing token estimation — verify 5 large documents don't exceed context limit
- [ ] **Document Viewer:** Often missing virtualization — verify 5000-row table renders without freezing
- [ ] **PDF export:** Often missing memory limits — verify 2000-row Excel export doesn't crash server
- [ ] **Security:** Often missing XXE/zip bomb checks — verify malicious files are rejected
- [ ] **Batch upload:** Often missing transaction batching — verify 50-file upload completes in <10s
- [ ] **Error messages:** Often missing specific details — verify "Upload failed" explains WHY
- [ ] **Progress indicators:** Often missing for long operations — verify users see feedback during processing

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Documents inserted without FTS5 index | LOW | Background job to re-index all documents: `for doc in orphaned: index_document(doc)` |
| Binary data stored directly (not text) | HIGH | Requires re-upload: fetch original files, re-extract text, update database |
| Encryption applied to binary not text | HIGH | Unrecoverable: decryption fails, requires user re-upload |
| Token budget exceeded in production | MEDIUM | Add summarization service, re-process existing documents with 5k limit |
| XXE vulnerability exploited | HIGH | Incident response: check logs for exfiltration, rotate secrets, patch openpyxl |
| Zip bomb crashes server | LOW | Restart server, add uncompressed size check, reject malicious file |
| DataType corruption (lost leading zeros) | MEDIUM | Re-upload original files with dtype=str fix applied |
| CSV encoding mojibake in database | MEDIUM | Re-upload with chardet auto-detection, update existing records |
| WeasyPrint OOM crash | LOW | Restart server, add row count limit, queue large exports as background jobs |
| No transaction batching (slow) | LOW | Refactor to use async with db.begin(), no data loss |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Binary storage breaks encryption | Phase 49-01 | Upload Excel, verify AI can read content in chat |
| FTS5 out-of-sync | Phase 49-01 | Upload document, immediately search for content |
| Token budget explosion | Phase 49-02 | Upload 50-page PDF, verify chat doesn't hit limit |
| XXE/Zip bomb attacks | Phase 49-01 | Try uploading XXE test file, verify rejection |
| PDF table extraction fails | Phase 49-02 | Upload complex table PDF, verify layout preserved |
| Excel data type corruption | Phase 49-01 | Upload sheet with "00123" ID, verify leading zero kept |
| CSV encoding issues | Phase 49-01 | Upload UTF-8-BOM and Windows-1252 CSVs, verify both work |
| WeasyPrint memory exhaustion | Phase 49-03 | Export 1000-row table, verify <500MB memory usage |
| DataTable freezes browser | Phase 49-02 | View 2000-row Excel, verify pagination/virtualization |
| Batch insert slow | Phase 49-01 | Upload 50 files, verify completes in <10 seconds |

## Sources

**SQLite Performance:**
- [SQLite 35% Faster Than Filesystem](https://sqlite.org/fasterthanfs.html)
- [Internal Versus External BLOBs](https://sqlite.org/intern-v-extern-blob.html)
- [How to improve bulk insert speed in SQLite | PDQ](https://www.pdq.com/blog/improving-bulk-insert-speed-in-sqlite-a-comparison-of-transactions/)
- [Towards Inserting One Billion Rows in SQLite Under A Minute](https://avi.im/blag/2021/fast-sqlite-inserts/)

**PDF Text Extraction:**
- [I Tested 7 Python PDF Extractors (2025 Edition)](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)
- [Comparing 4 methods for pdf text extraction in python](https://medium.com/social-impact-analytics/comparing-4-methods-for-pdf-text-extraction-in-python-fd34531034f)
- [Can PDFPlumber Extract Tables from PDFs?](https://www.pdfplumber.com/can-pdfplumber-extract-tables-from-pdfs/)
- [Dealing with merged table cells · Issue #79](https://github.com/jsvine/pdfplumber/issues/79)

**Security Vulnerabilities:**
- [Asymmetric Resource Consumption (Zip Bomb) in python | CVE-2024-0450](https://security.snyk.io/vuln/SNYK-UNMANAGED-PYTHON-7924823)
- [XML External Entity (XXE) Injection in openpyxl | CVE-2017-5992](https://security.snyk.io/vuln/SNYK-PYTHON-OPENPYXL-40459)
- [Unrestricted File Upload | OWASP Foundation](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [File Upload - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)

**Memory & Performance:**
- [Performance — openpyxl 3.1.3 documentation](https://openpyxl.readthedocs.io/en/stable/performance.html)
- [BUG: read_excel blows the memory when using openpyxl engine · Issue #40569](https://github.com/pandas-dev/pandas/issues/40569)
- [Weasyprint consumes a lot of memory for long documents · Issue #671](https://github.com/Kozea/WeasyPrint/issues/671)
- [WeasyPrint consuming memory when rendering tables with 5000 rows · Issue #1104](https://github.com/Kozea/WeasyPrint/issues/1104)

**AI Context Management:**
- [The Context Window Problem: Scaling Agents Beyond Token Limits | Factory.ai](https://factory.ai/news/context-window-problem)
- [Best LLMs for Extended Context Windows in 2026](https://aimultiple.com/ai-context-window)
- [Context Window Management: Strategies for Long-Context AI Agents](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/)

**Data Type & Encoding:**
- [Avoiding automatic data type conversion in Microsoft Excel and Pandas](https://sachachua.com/blog/2021/12/avoiding-automatic-data-type-conversion-in-microsoft-excel-and-pandas/)
- [How pandas infers data types when parsing CSV files](https://rushter.com/blog/pandas-data-type-inference/)
- [CSV isn't broken - Excel is broken - Peter Hilton](https://hilton.org.uk/blog/csv-excel/)
- [Opening CSV UTF-8 files correctly in Excel - Microsoft Support](https://support.microsoft.com/en-us/office/opening-csv-utf-8-files-correctly-in-excel-8a935af5-3416-4edd-ba7e-3dfd2bc4a032)

**Flutter Performance:**
- [DataTable class - material library - Dart API](https://api.flutter.dev/flutter/material/DataTable-class.html)
- [Datatable has jank and extreme memory usage · Issue #62596](https://github.com/flutter/flutter/issues/62596)
- [Flutter DataGrid | High-Performance Widget | Syncfusion](https://www.syncfusion.com/flutter-widgets/flutter-datagrid)

---
*Pitfalls research for: Rich Document Support (Excel/CSV/PDF/Word) added to existing text-only BA Assistant*
*Researched: 2026-02-12*
*Confidence: HIGH — Based on official documentation, security advisories, performance benchmarks, and existing system architecture review*
