# Stack Research: Rich Document Support

**Domain:** Document parsing (Excel, CSV, PDF, Word) with AI context integration
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

Adding Excel, CSV, PDF, and Word parsing to existing BA Assistant text-only document upload system requires minimal new dependencies. Most critical: **openpyxl** for Excel, **pdfplumber** for PDF text extraction, built-in **csv** module for CSV, **python-docx** (already installed) for Word. For Flutter web table preview: **excel** package for read/write and **pluto_grid** for advanced data grid display. All libraries are actively maintained, production-ready, and cost-free (AGPL-compliant for PDF).

**Key Decision:** Use pdfplumber over PyMuPDF to avoid AGPL commercial licensing concerns. Use pypdf (not PyPDF2) for PDF export if needed beyond current WeasyPrint.

---

## Recommended Stack

### Python Backend — NEW Additions

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **openpyxl** | >=3.1.5 | Excel (.xlsx) read/write | Industry standard for .xlsx. Active development, xlrd is deprecated. Both reads and writes Excel files. Pure Python (no C dependencies). Pandas uses openpyxl as backend engine. |
| **pdfplumber** | >=0.11.8 | PDF text extraction + tables | Best for tabular data extraction. Built on PDFMiner with higher-level API. Excellent coordinate-based extraction. Better licensing than PyMuPDF (no AGPL commercial issues). |
| **chardet** | >=5.2.0 | CSV encoding detection | Detects file encoding (UTF-8, Windows-1252, etc.) before parsing CSV to prevent Unicode errors. Python 3.7+ compatible. 0-1 confidence scores. |

**ALREADY INSTALLED (no changes needed):**
- `python-docx==1.2.0` — Word (.docx) read/write (currently used for artifact export)
- Built-in `csv` module — CSV parsing (standard library, no install needed)

### Python Backend — Optional Performance

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pandas** | >=2.0.0 | Data manipulation + export | ONLY if complex data transformations needed. Adds heavyweight dependency. For simple read/write, use openpyxl + csv module directly. |
| **pyarrow** | >=15.0.0 | Fast CSV parsing backend for pandas | ONLY if using pandas. 2-3x faster CSV parsing with `engine='pyarrow'`. Not needed for basic csv module usage. |

**Recommendation:** START without pandas. Add only if roadmap includes data analysis features (pivot tables, aggregations, etc.). Current use case (text extraction for AI context) does not require pandas overhead.

---

### Flutter Frontend — NEW Additions

| Package | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| **excel** | ^4.0.6 | Excel (.xlsx) read/write in Dart | Pure Dart implementation. Works on web without platform channels. Supports formulas, charts, images, encryption. For web, `save()` auto-downloads file. Client-side parsing + export. |
| **pluto_grid** | ^8.7.0 | Advanced data table display | Keyboard navigation, sorting, filtering, inline editing, pagination. Works well on web (canvas rendering compatible). Best for Excel/CSV preview with large datasets. Flutter DataTable too basic for spreadsheet-like UX. |

**ALREADY INSTALLED (no changes needed):**
- `file_saver: ^0.2.14` — File download for web (already used, will work for CSV/Excel export)

### Flutter Frontend — Alternative for Simple Tables

| Package | Version | Purpose | When to Use Instead |
|---------|---------|---------|---------------------|
| **DataTable** (built-in) | N/A (Flutter SDK) | Simple read-only tables | If preview is view-only, no sorting/filtering needed, and data is small (<100 rows). Zero dependencies. |

**Recommendation:** Use **pluto_grid** for Excel/CSV preview (users expect sorting/filtering for spreadsheets). Use **DataTable** ONLY for small embedded tables in chat artifacts.

---

## Installation

### Backend (Python)

```bash
# Add to backend/requirements.txt:
openpyxl>=3.1.5
pdfplumber>=0.11.8
chardet>=5.2.0

# Install in venv:
cd backend
source venv/bin/activate  # or venv/Scripts/activate on Windows
pip install -r requirements.txt
```

### Frontend (Flutter)

```bash
# Add to frontend/pubspec.yaml dependencies:
excel: ^4.0.6
pluto_grid: ^8.7.0

# Install:
cd frontend
flutter pub get
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| **Excel parsing** | openpyxl | xlrd | xlrd deprecated (no .xlsx support since 2020), maintainer recommends openpyxl |
| **Excel parsing** | openpyxl | pandas | Pandas adds 50MB+ dependency overhead. openpyxl sufficient for read/export. Use pandas ONLY if analysis features needed. |
| **PDF extraction** | pdfplumber | PyMuPDF (fitz) | PyMuPDF is 60x faster BUT dual-licensed (AGPL/commercial). Commercial use requires paid license. pdfplumber is pure open-source and fast enough for <1MB files. |
| **PDF extraction** | pdfplumber | PyPDF2 | PyPDF2 deprecated since 2023. Replaced by pypdf. Poor layout/table support vs pdfplumber. |
| **PDF extraction** | pdfplumber | pypdf | pypdf good for manipulation (merge/split), but pdfplumber superior for text+table extraction. May add pypdf later if PDF generation needs beyond WeasyPrint arise. |
| **CSV parsing** | csv module (built-in) | pandas | Built-in csv module is memory-efficient (line-by-line streaming). pandas loads entire file into RAM. For 1MB limit, csv module sufficient. |
| **Flutter table** | pluto_grid | DataTable (built-in) | DataTable lacks sorting, filtering, pagination, keyboard nav. Feels broken for spreadsheet preview. |
| **Flutter table** | pluto_grid | syncfusion_flutter_xlsio | Syncfusion requires commercial license for production use. pluto_grid is MIT-licensed and free. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **xlrd** | Deprecated. No .xlsx support since 2020. Maintainer says "use openpyxl". | openpyxl |
| **PyPDF2** | Deprecated since 2023. Fork merged into pypdf. Stale code. | pdfplumber (extraction) or pypdf (manipulation) |
| **PyMuPDF** for commercial app | AGPL 3.0 license requires open-source or paid license. BA Assistant is commercial SaaS. | pdfplumber (open-source, no licensing trap) |
| **XlsxWriter** for reading | Write-only library. Cannot read existing Excel files. | openpyxl (read + write) |
| **pandas** (for now) | 50MB+ dependency for simple read/export. Memory-heavy. Overkill for current scope. | openpyxl + csv module |

---

## Integration with Existing Upload Pipeline

### Current Flow (text-only)
```python
# backend/app/routes/documents.py lines 48-93
1. Validate content_type in ["text/plain", "text/markdown"]
2. Read bytes, check size <= 1MB
3. Decode UTF-8
4. Encrypt plaintext
5. Store in Document.content_encrypted
6. Index in FTS5 for search
```

### NEW Flow (rich documents)

**Changes to `documents.py`:**

```python
ALLOWED_CONTENT_TYPES = [
    "text/plain", "text/markdown",  # existing
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "text/csv",  # .csv
    "application/pdf",  # .pdf
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # .docx
]

# Add parser service:
from app.services.document_parser import extract_text_from_file

# In upload_document():
# 1. Validate content_type (expanded list)
# 2. Read bytes, check size <= 1MB
# 3. Extract text based on file type:
if file.content_type == "application/vnd.openxmlformats...xlsx":
    plaintext = extract_text_from_excel(content_bytes)
elif file.content_type == "text/csv":
    plaintext = extract_text_from_csv(content_bytes)
elif file.content_type == "application/pdf":
    plaintext = extract_text_from_pdf(content_bytes)
elif file.content_type == "application/vnd...docx":
    plaintext = extract_text_from_docx(content_bytes)
else:  # text/plain, text/markdown
    plaintext = content_bytes.decode('utf-8')

# 4. Encrypt plaintext (SAME as before)
# 5. Store encrypted (SAME)
# 6. Index for search (SAME)
# 7. NEW: Store original file metadata (file_type, row_count, etc.)
```

**NEW Service: `backend/app/services/document_parser.py`:**

```python
import openpyxl
import pdfplumber
import csv
import chardet
from io import BytesIO
from docx import Document  # already installed

def extract_text_from_excel(content_bytes: bytes) -> str:
    """Extract all text from Excel cells."""
    wb = openpyxl.load_workbook(BytesIO(content_bytes), read_only=True)
    text_parts = []
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            text_parts.append(" ".join(str(cell) for cell in row if cell))
    return "\n".join(text_parts)

def extract_text_from_csv(content_bytes: bytes) -> str:
    """Detect encoding and extract CSV text."""
    detected = chardet.detect(content_bytes)
    encoding = detected['encoding'] or 'utf-8'
    text = content_bytes.decode(encoding)
    return text  # CSV is already text, just decoded

def extract_text_from_pdf(content_bytes: bytes) -> str:
    """Extract text and tables from PDF."""
    text_parts = []
    with pdfplumber.open(BytesIO(content_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
            # Extract tables as text:
            for table in page.extract_tables():
                for row in table:
                    text_parts.append(" | ".join(str(cell) for cell in row if cell))
    return "\n".join(text_parts)

def extract_text_from_docx(content_bytes: bytes) -> str:
    """Extract text from Word document."""
    doc = Document(BytesIO(content_bytes))
    return "\n".join([para.text for para in doc.paragraphs])
```

**Database Changes (NEW):**

Add columns to `Document` model for rich metadata:

```python
# backend/app/models.py
class Document(Base):
    # ... existing fields ...
    file_type = Column(String)  # "excel", "csv", "pdf", "docx", "text"
    metadata_json = Column(Text)  # JSON: {"sheet_count": 3, "row_count": 150, etc.}
```

**Flutter Changes:**

- **Upload:** File picker already supports all types (`file_picker: ^10.3.8`). Just expand accepted extensions.
- **Preview:** Fetch document, parse with `excel` package, display in `pluto_grid` widget.
- **Export:** Use `excel` package to generate .xlsx, `file_saver` to download.

---

## Version Compatibility

| Package | Min Version | Python/Dart Compatibility | Notes |
|---------|-------------|---------------------------|-------|
| openpyxl | 3.1.5 | Python 3.7+ | Works with Python 3.9 (project's venv) |
| pdfplumber | 0.11.8 | Python 3.8+ | Latest release Jan 2026 |
| chardet | 5.2.0 | Python 3.7+ | No breaking changes expected |
| python-docx | 1.2.0 | Python 3.7+ | Already installed, no upgrade needed |
| excel (Dart) | 4.0.6 | Dart SDK 3.9.2+ | Compatible with current frontend |
| pluto_grid | 8.7.0 | Flutter 3.38+ | Web-compatible, no platform channels |

**No known compatibility conflicts** between new libraries and existing stack (FastAPI, SQLAlchemy, Flutter web).

---

## Performance Considerations

### Backend Parsing Limits

| File Type | 1MB Limit | Expected Parse Time | Memory Usage |
|-----------|-----------|---------------------|--------------|
| Excel (.xlsx) | ~10,000-50,000 rows | <500ms (openpyxl read-only mode) | 10-20MB RAM |
| CSV | ~50,000-100,000 rows | <200ms (csv module streaming) | <5MB RAM (line-by-line) |
| PDF | ~50-200 pages | 1-3s (pdfplumber) | 20-50MB RAM |
| Word (.docx) | ~500-1,000 pages | <300ms (python-docx) | 5-10MB RAM |

**Bottleneck:** PDF parsing (pdfplumber) is slowest. Mitigations:
1. Keep 1MB limit (prevents huge PDFs).
2. Extract text asynchronously (already async endpoint).
3. Consider background task queue if users report timeouts (future enhancement).

### Frontend Rendering Limits

| File Type | pluto_grid Performance | Recommendation |
|-----------|------------------------|----------------|
| Excel/CSV with <1,000 rows | Instant rendering, smooth scrolling | Full preview |
| Excel/CSV with 1,000-10,000 rows | 500ms-2s initial render, lazy loading works | Full preview with virtualization |
| Excel/CSV with >10,000 rows | May lag on initial load | Paginate or show first 5,000 rows with "export full file" option |

**pluto_grid** handles 10,000 rows well with lazy loading. If performance issues arise, add row limit to preview with full export capability.

---

## Sources

### Python Libraries
- [openpyxl PyPI](https://pypi.org/project/openpyxl/) — Latest version 3.1.5 (verified Feb 2026)
- [openpyxl vs xlrd comparison](https://stackshare.io/stackups/pypi-openpyxl-vs-pypi-xlrd) — xlrd deprecated, openpyxl recommended
- [xlrd GitHub](https://github.com/python-excel/xlrd) — Maintainer directs to openpyxl
- [pdfplumber PyPI](https://pypi.org/project/pdfplumber/) — Latest version 0.11.8 (Jan 2026)
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber) — Table extraction features
- [PDF extractor comparison](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257) — pdfplumber vs PyMuPDF benchmarks
- [PyMuPDF licensing](https://pymupdf.readthedocs.io/en/latest/about.html) — AGPL vs commercial license
- [pypdf vs PyPDF2](https://pypdf.readthedocs.io/en/stable/meta/history.html) — PyPDF2 deprecated, pypdf is successor
- [chardet PyPI](https://pypi.org/project/chardet/) — Encoding detection, version 5.2.0
- [Python CSV best practices](https://realpython.com/python-csv/) — csv module vs pandas comparison
- [Pandas vs CSV module](https://pytutorial.com/pandas-vs-csv-module-best-practices-for-csv-data-in-python/) — Performance and use case analysis

### Flutter Packages
- [excel package pub.dev](https://pub.dev/packages/excel) — Version 4.0.6, Dart Excel read/write
- [excel package GitHub](https://github.com/justkawal/excel) — Web download features
- [pluto_grid pub.dev](https://pub.dev/packages/pluto_grid) — Latest version verified Feb 2026
- [pluto_grid GitHub](https://github.com/bosskmk/pluto_grid) — Keyboard navigation, web support
- [Flutter table packages comparison](https://fluttergems.dev/table/) — DataTable vs pluto_grid features
- [Flutter web file download](https://iamkaival.medium.com/read-write-csv-in-flutter-web-9f8ec960914c) — CSV save patterns
- [Flutter CSV/Excel packages](https://fluttergems.dev/ods-xlsx-sheets/) — Comprehensive package list

---

**Stack Research Complete**
*Researched: 2026-02-12*
*Confidence: HIGH (all libraries verified with official docs/PyPI/pub.dev)*
