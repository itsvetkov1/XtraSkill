# Feature Research: Rich Document Support

**Domain:** Excel, CSV, PDF, and Word document parsing for BA Assistant
**Researched:** 2026-02-12
**Confidence:** MEDIUM (WebSearch verified with multiple sources, some library-specific details need Context7 verification)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

#### Core Parsing Capabilities

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Excel (.xlsx) text extraction** | Primary format for requirements matrices, stakeholder data | MEDIUM | python-docx, openpyxl, or pandas. Must handle multiple sheets. Dependencies: existing upload pipeline |
| **CSV text extraction** | Universal data interchange format | LOW | Python csv module with delimiter detection. Dependencies: existing upload pipeline |
| **PDF text extraction** | Most common document format from stakeholders | HIGH | PyPDF2 or pdfplumber. Table extraction is notoriously difficult (67-74% accuracy for traditional tools). Dependencies: existing upload pipeline |
| **Word (.docx) text extraction** | Primary format for BRDs, user stories, requirements docs | MEDIUM | python-docx library. Must extract paragraphs in document order. Dependencies: existing upload pipeline |

#### File Validation & Security

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **File type validation (client + server)** | Security and UX baseline | LOW | Extension + MIME type checking. Never trust Content-Type header alone. Dependencies: existing upload preview dialog |
| **File size limits** | Prevent memory exhaustion, DoS | LOW | Recommend 10MB default, 50MB max. Streaming for large files. Dependencies: existing upload pipeline |
| **Malformed file rejection** | Prevent crashes from corrupt files | MEDIUM | Try-catch around parsers with clear error messages. Dependencies: existing error handling |
| **Encoding detection (CSV/TXT)** | International character support | MEDIUM | chardet library for auto-detection, UTF-8 default. Dependencies: existing text upload |

#### Upload Preview Enhancements

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Visual table preview (Excel/CSV)** | Users verify correct file before upload | MEDIUM | Show first 5-10 rows in grid format. Existing: text preview shows 20 lines. Dependencies: existing upload preview dialog |
| **Sheet selector (Excel multi-sheet)** | Users choose which sheet(s) to extract | MEDIUM | Dropdown/tabs showing sheet names. Default: all sheets or first sheet. Dependencies: Excel parsing |
| **Document metadata display** | File size, page count, sheet count, modification date | LOW | Extract during parsing. Existing: filename, size shown. Dependencies: existing preview dialog |
| **First page preview (PDF/Word)** | Visual confirmation of correct document | HIGH | Thumbnail generation. Defer to v2 if complex. Dependencies: PDF/Word parsing |

#### AI Context Integration

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Full-text search across rich docs** | Existing feature for text docs, expected for all types | MEDIUM | Extend existing FTS5 integration. Extract text during upload. Dependencies: existing FTS5 search, document_search tool |
| **AI reads rich document content** | Core value prop - AI accesses uploaded context | LOW | Text extraction feeds existing document_search tool. Dependencies: existing AI document search tool |
| **Source attribution for rich docs** | Existing feature - show which doc AI referenced | LOW | Extend existing document source chips. Include sheet name for Excel. Dependencies: existing artifact source attribution |
| **Document content in AI system prompt** | AI has access to project context | LOW | Feed extracted text to existing prompt assembly. Dependencies: existing system prompt generation |

#### Document Viewer Updates

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Download rich documents** | Existing feature for text docs | LOW | Serve original uploaded file. Already implemented for text. Dependencies: existing document viewer, encrypted storage |
| **Display extracted text content** | Users verify what AI sees | LOW | Markdown rendering of extracted content. Dependencies: existing document viewer |
| **Sheet navigation (Excel)** | View all sheets in workbook | MEDIUM | Tabs or dropdown to switch sheets in viewer. Dependencies: Excel parsing, document viewer |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

#### Advanced Parsing

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Table structure preservation (Excel/CSV)** | AI understands relationships between columns/rows | HIGH | Parse as structured data, not flat text. Preserve headers, cell relationships. LLMs handle schema detection better with structure |
| **Excel formula preservation** | Show calculated vs raw values | MEDIUM | python-docx can access formulas. Useful for requirements matrices with dependencies |
| **Cell formatting signals (Excel)** | Colors, borders indicate meaning (priorities, categories) | HIGH | Excel visual cues often convey business logic. Native parsing vs PDF conversion preserves this. Unstract research shows this improves extraction accuracy |
| **Multi-sheet context stitching (Excel)** | Parse all sheets as unified context | MEDIUM | Concatenate sheets with clear separators. Navigation pane pattern from Excel 2026. Dependencies: Sheet selector feature |
| **PDF table extraction with AI** | Use vision LLM for table understanding | HIGH | Traditional tools: 67-74% accuracy. AI approaches (TableFormer): 93.6% accuracy. Reducto/Docling use vision models for context-aware extraction |
| **Word document order parsing** | Paragraphs, tables, images in original sequence | HIGH | python-docx limitation: can only read all paragraphs OR all tables. Requires custom iteration. Critical for understanding document flow |

#### Export Capabilities

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Export to Excel** | Structured artifact output (user stories table, requirements matrix) | MEDIUM | Existing: MD/PDF/Word export. Add openpyxl for Excel. High user value for BA workflows |
| **Export to CSV** | Data portability, analysis tools | LOW | Python csv module. Simple addition if Excel export exists |
| **Preserve formatting in exports** | Professional output matching corporate standards | HIGH | Round-trip formatting preservation is challenging. Microsoft docs: "Some formatting might be lost" in conversions |

#### UX Enhancements

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Inline table viewer (modal)** | View spreadsheet without download | MEDIUM | React-like PDF viewer pattern: modal with grid display. Accessibility concern if taller than viewport |
| **Drag-and-drop upload** | Modern UX expectation | MEDIUM | More intuitive than file picker. Uploadcare research shows improved UX. Dependencies: existing upload flow |
| **Batch upload (multiple files)** | Upload entire project folder at once | MEDIUM | Process multiple files in one action. Dependencies: existing upload pipeline |
| **Real-time upload progress** | Transparency for large files | LOW | Stream upload with percentage indicator. Dependencies: existing upload flow |

### Anti-Features (Commonly Requested, Often Problematic)

Features to explicitly NOT build.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-time collaborative editing (like Google Sheets)** | "Modern" spreadsheet tools have this | Massive complexity (OT/CRDT algorithms), out of scope for BA tool, documents are uploaded reference material not live workspaces | Download → edit locally → re-upload new version. Focus on AI consumption, not editing |
| **Full Excel calculation engine** | "Support all Excel features" | Reimplementing Excel is impossible. Formulas, macros, pivot tables are 30+ years of features | Extract text/data only. Use Excel for calculations, BA Assistant for AI analysis |
| **OCR for scanned PDFs** | "Some PDFs are scanned images" | Adds Tesseract dependency, low accuracy on complex layouts, slow | Require text-based PDFs. If scanned, user converts first (Adobe, online tools) |
| **PDF editing/annotation** | "Mark up requirements in-app" | Out of scope for BA tool, complex PDF specification | Download → annotate in PDF reader → re-upload. Focus on AI consumption |
| **Version control for documents** | "Track changes like Git" | Complex conflict resolution, storage overhead, not core value | Re-upload creates new document entry. Delete old version manually. Focus on artifacts (which have versions) |
| **Advanced Excel features (macros, pivot tables, charts)** | "Preserve everything" | Security risk (macro execution), irrelevant for AI context, complex parsing | Text and data only. Visual elements ignored. AI analyzes content, not presentation |
| **Inline document editor** | "Edit docs without downloading" | Major feature creep, complex WYSIWYG editor, not core value | Download → edit → re-upload. Focus on AI generation of new artifacts, not editing uploads |

## Feature Dependencies

```
Document Upload Pipeline (existing)
    ├──requires──> File Type Validation (new)
    │                  └──requires──> MIME + Extension Check (new)
    │
    ├──requires──> File Size Limits (new)
    │                  └──enables──> Streaming Upload (optional, v2)
    │
    ├──requires──> Parser Selection (new)
    │                  ├──> Excel Parser (.xlsx)
    │                  ├──> CSV Parser (.csv)
    │                  ├──> PDF Parser (.pdf)
    │                  └──> Word Parser (.docx)
    │
    └──requires──> Text Extraction (new)
                       └──feeds──> FTS5 Full-Text Search (existing)
                                      └──used by──> AI Document Search Tool (existing)

Upload Preview Dialog (existing)
    ├──enhances──> Visual Table Preview (new, Excel/CSV)
    ├──enhances──> Sheet Selector (new, Excel)
    └──enhances──> Document Metadata Display (new)

Document Viewer (existing)
    ├──enhances──> Sheet Navigation (new, Excel)
    └──enhances──> Inline Table Viewer (optional, v2)

Export Feature (existing: MD/PDF/Word)
    ├──enhances──> Excel Export (new)
    └──enhances──> CSV Export (new)

Conflict: Inline Editor ──conflicts with──> Focus on AI Generation
Conflict: Version Control ──conflicts with──> Simplicity Principle
```

### Dependency Notes

- **Parser Selection requires File Type Validation:** Must verify file type before choosing parser to prevent crashes
- **Text Extraction feeds FTS5 Search:** Core integration point with existing document search feature
- **Visual Table Preview enhances Upload Preview Dialog:** Builds on existing preview pattern
- **Sheet Selector requires Excel Parser:** Can't show sheet list without parsing workbook structure
- **Excel Export enhances Export Feature:** Logical extension of existing MD/PDF/Word export
- **Inline Editor conflicts with Focus on AI Generation:** BA Assistant generates artifacts, doesn't edit uploads
- **Version Control conflicts with Simplicity Principle:** Adds complexity without clear ROI for BA workflow

## MVP Definition

### Launch With (v2.1 - Rich Document Support Milestone)

Minimum viable product — what's needed to validate the concept.

- [x] **Excel text extraction (all sheets)** — Table stakes, primary BA format (requirements matrices)
- [x] **CSV text extraction** — Table stakes, universal data format
- [x] **PDF text extraction (text-based PDFs)** — Table stakes, most common stakeholder format
- [x] **Word text extraction (paragraphs only)** — Table stakes, primary BRD/user story format
- [x] **File type validation (extension + MIME)** — Security baseline, prevent crashes
- [x] **File size limits (10MB default, 50MB max)** — Prevent memory issues
- [x] **FTS5 search integration** — Extend existing search to rich docs
- [x] **AI document_search tool integration** — AI reads rich doc content
- [x] **Source attribution for rich docs** — Extend existing chips to show sheet names
- [x] **Visual table preview (Excel/CSV)** — Users verify data before upload (first 10 rows)
- [x] **Sheet selector (Excel)** — Users choose which sheets to parse (default: all)
- [x] **Document viewer updates** — Display extracted text, download originals
- [x] **Encoding detection (CSV)** — Handle international characters

### Add After Validation (v2.2+)

Features to add once core is working.

- [ ] **Table structure preservation (Excel/CSV)** — Trigger: Users request better AI understanding of columnar data. Complexity: HIGH. Requires structured parsing + LLM prompt updates
- [ ] **Multi-sheet context stitching (Excel)** — Trigger: Users upload workbooks expecting AI to understand cross-sheet relationships. Complexity: MEDIUM
- [ ] **Excel export for artifacts** — Trigger: Users want requirements matrices as .xlsx. Complexity: MEDIUM. High value for BA workflows
- [ ] **Word document order parsing (tables + paragraphs)** — Trigger: AI misses context from tables in Word docs. Complexity: HIGH
- [ ] **Drag-and-drop upload** — Trigger: User feedback requests modern UX. Complexity: MEDIUM
- [ ] **Batch upload** — Trigger: Users upload entire project folders. Complexity: MEDIUM

### Future Consideration (v3+)

Features to defer until product-market fit is established.

- [ ] **PDF table extraction with AI (vision LLM)** — Why defer: HIGH complexity, vision LLM cost. Traditional extraction (67% accuracy) may be sufficient initially. Vision approach (93% accuracy) when ROI clear
- [ ] **Cell formatting signals (Excel)** — Why defer: HIGH complexity, requires native parsing. Validate if AI actually benefits from color/border context
- [ ] **Excel formula preservation** — Why defer: MEDIUM complexity, unclear if AI uses formulas vs calculated values
- [ ] **Inline table viewer (modal)** — Why defer: UX enhancement, not core functionality. Validate with download-first approach
- [ ] **First page preview (PDF/Word)** — Why defer: HIGH complexity (thumbnail generation). Text preview may suffice
- [ ] **CSV export** — Why defer: LOW complexity but lower priority than Excel export
- [ ] **Real-time upload progress** — Why defer: LOW complexity, nice-to-have UX polish

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Excel text extraction | HIGH | MEDIUM | P1 |
| CSV text extraction | HIGH | LOW | P1 |
| PDF text extraction | HIGH | HIGH | P1 |
| Word text extraction | HIGH | MEDIUM | P1 |
| File type validation | HIGH | LOW | P1 |
| File size limits | HIGH | LOW | P1 |
| FTS5 search integration | HIGH | MEDIUM | P1 |
| AI document_search integration | HIGH | LOW | P1 |
| Visual table preview | HIGH | MEDIUM | P1 |
| Sheet selector (Excel) | MEDIUM | MEDIUM | P1 |
| Source attribution | MEDIUM | LOW | P1 |
| Encoding detection (CSV) | MEDIUM | MEDIUM | P1 |
| Table structure preservation | HIGH | HIGH | P2 |
| Excel export | HIGH | MEDIUM | P2 |
| Multi-sheet context stitching | MEDIUM | MEDIUM | P2 |
| Word document order parsing | MEDIUM | HIGH | P2 |
| Drag-and-drop upload | MEDIUM | MEDIUM | P2 |
| Batch upload | MEDIUM | MEDIUM | P2 |
| PDF table extraction (AI) | HIGH | HIGH | P3 |
| Cell formatting signals | MEDIUM | HIGH | P3 |
| Inline table viewer | LOW | MEDIUM | P3 |
| First page preview | LOW | HIGH | P3 |
| Real-time upload progress | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for v2.1 launch (Rich Document Support milestone)
- P2: Should have, add in v2.2+ after validation
- P3: Nice to have, future consideration (v3+)

## Competitor Feature Analysis

| Feature | Docparser/Parseur (2026) | Docling (IBM, 2026) | Our Approach |
|---------|--------------------------|---------------------|--------------|
| **Excel parsing** | Template-based extraction, AI-powered schema detection | Native Excel reading (preserves context, formatting) | Text extraction (v2.1) → Structured parsing (v2.2+). Start simple, add structure when needed |
| **PDF table extraction** | Zonal OCR + AI parsers (mixed results) | Vision LLM approach (context-aware) | Traditional extraction (v2.1) → Vision LLM if accuracy insufficient (v3+) |
| **Word parsing** | Text + tables via docx2python | Unified API with context preservation | Paragraphs only (v2.1) → Document order parsing (v2.2+) |
| **CSV handling** | Delimiter detection, encoding handling | Standard parsing | chardet encoding detection + csv.Sniffer for delimiters (v2.1) |
| **Multi-format support** | PDF, Word, Excel, CSV, images (OCR) | PDF, images, spreadsheets, slides (unified API) | Focus on text-based: Excel, CSV, PDF, Word. No OCR (anti-feature) |
| **Export formats** | Excel, CSV, JSON, webhooks to 3000+ apps | Markdown, structured data for gen AI | MD/PDF/Word (existing) → Add Excel (v2.2+). Match BA workflow needs |
| **AI integration** | GPT-4+ for contextual extraction | Built for gen AI ecosystem (embeddings, RAG) | Direct integration with existing document_search tool. Simple text extraction → structured if needed |
| **Table preview** | Not mentioned in research | Visual region interpretation, linked labels/values | Grid display (first 10 rows) in upload preview dialog (v2.1) |
| **Sheet navigation** | Not applicable (extraction-focused) | Multi-page/multi-sheet support | Tabs/dropdown in document viewer (v2.1) |

**Key Differentiator:** BA Assistant focuses on AI consumption (feeding LLM context) rather than data extraction/automation. Competitors extract data for workflows; we extract text/structure for conversational AI analysis.

## Sources

### Document Parsing Tools & Features
- [Docparser - Automate Data Extraction from PDFs and Documents](https://docparser.com/)
- [Best AI tools for data extraction in 2026 | Parseur](https://parseur.com/compare-to/best-ai-tools)
- [GitHub - docling-project/docling: Get your documents ready for gen AI](https://github.com/docling-project/docling)
- [Reducto: AI document parsing & extraction software](https://reducto.ai/)
- [Extract Data from Excel Documents with AI in 2026](https://unstract.com/blog/extract-data-from-excel-documents-with-ai-unstract-excel-document-processing/)

### Table Preview & UX Patterns
- [Data Table Design UX Patterns & Best Practices - Pencil & Paper](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-data-tables)
- [Enterprise UX: essential resources to design complex data tables by Stéphanie Walter](https://stephaniewalter.design/blog/essential-resources-design-complex-data-tables/)
- [Spreadsheet Viewer - Handsontable](https://handsontable.com/spreadsheet-viewer/)

### Upload & Validation Best Practices
- [File Upload - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [UX best practices for designing a file uploader | Uploadcare](https://uploadcare.com/blog/file-uploader-ux-best-practices/)
- [10 File Upload System Features Every Developer Should Know in 2025](https://www.portotheme.com/10-file-upload-system-features-every-developer-should-know-in-2025/)
- [Document Upload Apps: Key Features and Best Practices](https://blog.filestack.com/document-upload-apps-key-features-and-best-practices/)

### Python Libraries & Parsing
- [Mastering python-docx: Create, Format, and Automate Word Documents](https://www.w3resource.com/python/mastering-python-docx.php)
- [GitHub - kmrambo/Python-docx-Reading-paragraphs-tables-and-images-in-document-order](https://github.com/kmrambo/Python-docx-Reading-paragraphs-tables-and-images-in-document-order-)
- [Best Python Libraries to Extract Tables From PDF in 2026](https://unstract.com/blog/extract-tables-from-pdf-python/)
- [I Tested 12 "Best-in-Class" PDF Table Extraction Tools](https://medium.com/@kramermark/i-tested-12-best-in-class-pdf-table-extraction-tools-and-the-results-were-appalling-f8a9991d972e)

### CSV & Encoding
- [Pandas read_csv: The Definitive Guide to pd.read_csv() in Python (2026) – Kanaries](https://docs.kanaries.net/topics/Pandas/pandas-read-csv)
- [How to manage CSV file encoding | LabEx](https://labex.io/tutorials/python-how-to-manage-csv-file-encoding-418947)
- [How to detect delimiter and encoding of CSV file in python/pandas | Yun Gao](https://yunkgao.wordpress.com/2020/09/11/how-to-detect-delimiter-and-encoding-of-csv-file-in-python-pandas/)

### File Size & Memory Efficiency
- [Parsing Large Files in the Browser Using JavaScript Streams API](https://medium.com/@AlexanderObregon/parsing-large-files-in-the-browser-using-javascript-streams-api-78cb88f30d23)
- [Processing large JSON files in Python without running out of memory](https://pythonspeed.com/articles/json-memory-streaming/)
- [smoores.dev - Overcoming I/O Limits in Node.js](https://smoores.dev/post/overcoming_io_limits/)

### Excel Multi-Sheet Navigation
- [Use the Navigation pane in Excel - Microsoft Support](https://support.microsoft.com/en-us/office/use-the-navigation-pane-in-excel-ddd037e7-22e3-41f0-8bbd-07f5479e92bf)
- [NPM + SheetJS XLSX in 2026](https://thelinuxcode.com/npm-sheetjs-xlsx-in-2026-safe-installation-secure-parsing-and-real-world-nodejs-patterns/)
- [How to Parse Excel Files in n8n: Sheets, Ranges, and Data Types](https://logicworkflow.com/blog/n8n-parse-excel-files/)

### Document Viewer Patterns
- [Preview a document inside a modal - React PDF Viewer](https://react-pdf-viewer.dev/examples/preview-a-document-inside-a-modal/)
- [Lessons Learned from Implementing an Inline Document Viewer](https://spin.atomicobject.com/inline-document-viewer/)

---
*Feature research for: Rich Document Support (Excel, CSV, PDF, Word)*
*Researched: 2026-02-12*
*Confidence: MEDIUM (WebSearch verified with multiple credible sources, library-specific implementation details need verification during development)*
