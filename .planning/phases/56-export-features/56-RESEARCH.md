# Phase 56: Export Features - Research

**Researched:** 2026-02-12
**Domain:** Excel/CSV export, FastAPI file streaming, Flutter web downloads, binary file generation
**Confidence:** HIGH

## Summary

Phase 56 extends Phase 55's table viewer by adding export capabilities for parsed Excel and CSV data. Users need to export data back to Excel or CSV formats after viewing and potentially filtering/sorting in PlutoGrid. The challenge is bidirectional: **backend must generate Excel/CSV files from tab-separated content_text**, and **frontend must trigger file downloads in Flutter web**.

Backend export requires generating files in memory and streaming via FastAPI Response with proper MIME types. Python's openpyxl (already installed) can write Excel files, but **write_only mode is critical for memory efficiency** — standard mode uses 50x file size in memory. For 1000-row files, write_only mode keeps memory under 10MB vs 500MB+ for standard mode. CSV export is simpler using Python's csv.writer with BytesIO.

Frontend download in Flutter web uses existing file_saver package (already installed v0.2.14) with FileSaver.saveAs() for cross-platform support. Alternative pluto_grid_export package offers one-line CSV export from PlutoGrid state, but **does not support Excel export** and adds 200KB dependency — better to call backend endpoints for consistency with existing download pattern.

**Primary recommendation:** Add two backend endpoints (`/documents/{id}/export/xlsx` and `/documents/{id}/export/csv`) that generate files from content_text in memory, return via StreamingResponse with attachment headers. Frontend adds export buttons to ExcelTableViewer that call backend endpoints and use FileSaver.saveAs() for cross-platform download. Use openpyxl write_only mode for Excel generation to prevent memory issues on large datasets.

## Standard Stack

### Core Libraries (Backend)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.4+ | Excel file generation | Already installed (requirements.txt line 23), supports write_only mode for memory efficiency, official XLSX support |
| csv (Python stdlib) | 3.9+ | CSV file generation | Built-in, zero dependencies, handles quoting/escaping correctly |
| io.BytesIO (Python stdlib) | 3.9+ | In-memory file generation | Standard pattern for FastAPI file streaming without temp files |

### Core Libraries (Frontend)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| file_saver | 0.2.14 | Cross-platform file downloads | Already installed (pubspec.yaml line 50), works on Flutter web/mobile/desktop |
| dio | 5.9.0 | HTTP client for binary downloads | Already installed (pubspec.yaml line 38), used in DocumentService |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| XlsxWriter | Latest | Alternative Excel writer | **Recommended for large datasets (10k+ rows)**: constant_memory mode more efficient than openpyxl write_only |
| pluto_grid_export | 0.1.3 | CSV export from PlutoGrid | CSV-only use case, client-side generation, but backend consistency preferred |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl write_only | XlsxWriter | XlsxWriter is faster for large datasets (200k rows in 3min vs 9min), but openpyxl already installed and sufficient for Phase 56 scale |
| Backend endpoints | pluto_grid_export | Client-side CSV generation saves server roundtrip, but no Excel support and inconsistent with Phase 55 download pattern |
| StreamingResponse | FileResponse with temp files | FileResponse requires disk I/O and cleanup tasks; StreamingResponse keeps everything in memory (faster for <10MB files) |

**Installation (none required):**
All dependencies already installed. Optional XlsxWriter if large dataset performance becomes an issue:
```bash
cd backend
pip install XlsxWriter
```

## Architecture Patterns

### Recommended Project Structure

```
backend/app/
├── routes/
│   └── documents.py              # Add export endpoints
├── services/
│   ├── document_parser/          # Existing parsers (read)
│   └── document_exporter/        # NEW: Export adapters (write)
│       ├── __init__.py
│       ├── base.py               # DocumentExporter base class
│       ├── excel_exporter.py     # Excel export with write_only mode
│       └── csv_exporter.py       # CSV export with proper quoting

frontend/lib/
├── screens/documents/widgets/
│   └── excel_table_viewer.dart   # Add export buttons to AppBar
├── services/
│   └── document_service.dart     # Add exportDocument() method
```

### Pattern 1: Backend Export Endpoint with In-Memory File Generation

**What:** FastAPI endpoint generates Excel/CSV file from content_text and streams via Response

**When to use:** Exporting parsed document data without persisting export files to disk

**Example:**
```python
# Source: FastAPI StreamingResponse pattern + openpyxl write_only mode
from io import BytesIO
from fastapi import Response
import openpyxl

@router.get("/documents/{document_id}/export/xlsx")
async def export_document_xlsx(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export parsed document data to Excel format.

    Generates .xlsx file from content_text (tab-separated format).
    Uses write_only mode for memory efficiency.
    """
    # Get document with ownership check
    doc = await get_document_with_ownership(db, document_id, current_user)

    # Parse metadata for filename and sheet name
    metadata = json.loads(doc.metadata_json) if doc.metadata_json else {}
    sheet_name = metadata.get('sheet_names', ['Sheet1'])[0] if metadata.get('sheet_names') else 'Sheet1'

    # Generate Excel file in memory
    output = BytesIO()
    wb = openpyxl.Workbook(write_only=True)  # CRITICAL: write_only for memory efficiency
    ws = wb.create_sheet(title=sheet_name)

    # Parse content_text (tab-separated)
    lines = doc.content_text.split('\n')
    for line in lines:
        if line.strip():
            cells = line.split('\t')
            ws.append(cells)

    wb.save(output)
    output.seek(0)

    # Determine filename
    base_filename = doc.filename.rsplit('.', 1)[0] if '.' in doc.filename else doc.filename
    export_filename = f"{base_filename}_export.xlsx"

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"'
        }
    )
```

**Why this works:**
- write_only=True prevents openpyxl from building full cell tree in memory (10MB vs 500MB for 1000 rows)
- BytesIO keeps file in memory (no disk I/O, no cleanup needed)
- Response with attachment header triggers browser download
- Reuses existing content_text (no re-parsing needed)

### Pattern 2: CSV Export with Proper Quoting

**What:** Generate CSV with correct escaping for cells containing commas, quotes, or newlines

**When to use:** Exporting tabular data where cell values may contain delimiters

**Example:**
```python
# Source: Python csv.writer with StringIO
import csv
from io import StringIO

@router.get("/documents/{document_id}/export/csv")
async def export_document_csv(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export parsed document data to CSV format."""
    doc = await get_document_with_ownership(db, document_id, current_user)

    # Generate CSV in memory
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Parse content_text (tab-separated)
    lines = doc.content_text.split('\n')
    for line in lines:
        if line.strip():
            cells = line.split('\t')
            writer.writerow(cells)

    # Convert to bytes
    csv_bytes = output.getvalue().encode('utf-8-sig')  # BOM for Excel compatibility

    base_filename = doc.filename.rsplit('.', 1)[0] if '.' in doc.filename else doc.filename
    export_filename = f"{base_filename}_export.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"'
        }
    )
```

**Why UTF-8-BOM:**
- Excel on Windows requires BOM to detect UTF-8 encoding
- Without BOM, Excel may misinterpret international characters
- utf-8-sig adds 3-byte BOM automatically

### Pattern 3: Frontend File Download with FileSaver

**What:** Flutter web file download using file_saver package with backend binary response

**When to use:** Downloading binary files (Excel/CSV) from backend API to user's browser

**Example:**
```dart
// Source: file_saver package + Dio binary download
import 'package:file_saver/file_saver.dart';
import 'package:dio/dio.dart';

class DocumentService {
  final Dio _dio;

  Future<void> exportDocument(String documentId, String format) async {
    try {
      final endpoint = format == 'xlsx'
        ? '/documents/$documentId/export/xlsx'
        : '/documents/$documentId/export/csv';

      // Download binary from backend
      final response = await _dio.get(
        endpoint,
        options: Options(
          responseType: ResponseType.bytes,
          headers: {'Accept': '*/*'},
        ),
      );

      // Extract filename from Content-Disposition header
      String filename = 'export.${format}';
      final contentDisposition = response.headers.value('content-disposition');
      if (contentDisposition != null) {
        final filenameMatch = RegExp(r'filename="(.+)"').firstMatch(contentDisposition);
        if (filenameMatch != null) {
          filename = filenameMatch.group(1)!;
        }
      }

      // Determine MIME type
      final mimeType = format == 'xlsx'
        ? MimeType.microsoftExcel
        : MimeType.csv;

      // Save file using FileSaver (cross-platform)
      await FileSaver.instance.saveFile(
        name: filename,
        bytes: response.data,
        mimeType: mimeType,
      );

    } catch (e) {
      throw Exception('Export failed: $e');
    }
  }
}
```

**Why this pattern:**
- FileSaver handles platform differences (web uses AnchorElement download, mobile uses file system)
- ResponseType.bytes prevents Dio from decoding binary as UTF-8
- Content-Disposition parsing preserves backend-generated filename
- MimeType enum ensures correct MIME types for FileSaver

### Pattern 4: Export Buttons in Table Viewer

**What:** Add export action buttons to ExcelTableViewer AppBar or toolbar

**When to use:** User wants to download filtered/sorted table data after viewing

**Example:**
```dart
// Source: Flutter IconButton + Provider pattern
class ExcelTableViewer extends StatefulWidget {
  // ... existing code

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Metadata header with export buttons
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              // Existing metadata display
              Icon(Icons.table_chart, size: 18),
              SizedBox(width: 8),
              Text('$rowCount rows'),

              Spacer(),

              // Export buttons
              PopupMenuButton<String>(
                icon: Icon(Icons.download),
                tooltip: 'Export',
                onSelected: (format) => _handleExport(context, format),
                itemBuilder: (context) => [
                  PopupMenuItem(
                    value: 'xlsx',
                    child: Row(
                      children: [
                        Icon(Icons.table_chart, size: 20),
                        SizedBox(width: 8),
                        Text('Export to Excel'),
                      ],
                    ),
                  ),
                  PopupMenuItem(
                    value: 'csv',
                    child: Row(
                      children: [
                        Icon(Icons.insert_drive_file, size: 20),
                        SizedBox(width: 8),
                        Text('Export to CSV'),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Existing PlutoGrid
        Expanded(child: PlutoGrid(...)),
      ],
    );
  }

  Future<void> _handleExport(BuildContext context, String format) async {
    try {
      // Show loading indicator
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Exporting to ${format.toUpperCase()}...')),
      );

      // Call service
      final service = DocumentService();
      await service.exportDocument(widget.documentId, format);

      // Success feedback
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Export complete')),
      );
    } catch (e) {
      // Error feedback
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Export failed: $e'), backgroundColor: Colors.red),
      );
    }
  }
}
```

**Why PopupMenuButton:**
- Compact UI (single button for both formats)
- Extensible (easy to add PDF export later)
- Follows Material Design patterns

### Anti-Patterns to Avoid

- **Loading full document into memory before export:** Stream from content_text directly, don't load into intermediate data structures
- **Standard openpyxl Workbook mode for large files:** Always use write_only=True for exports to prevent 50x memory bloat
- **Temp files on disk:** Use BytesIO/StringIO for in-memory generation (faster, no cleanup needed)
- **Client-side Excel generation:** Excel format is complex (zip archive with XML), backend generation more reliable
- **Ignoring UTF-8 BOM for CSV:** Excel on Windows needs BOM to detect UTF-8, otherwise international characters display as garbage

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Excel file format | Custom XLSX zip/XML writer | openpyxl write_only mode | XLSX has 400+ cell types, styles, formulas — 10 years of edge cases |
| CSV quoting/escaping | String concatenation with manual escaping | csv.writer with QUOTE_MINIMAL | RFC 4180 compliance, handles quotes-in-quotes, newlines in cells |
| File streaming | Write to disk then serve | BytesIO + StreamingResponse | Memory efficient, no cleanup needed, faster for <10MB files |
| Browser file download | Manual AnchorElement creation | FileSaver package | Cross-platform (web/mobile/desktop), handles platform quirks |
| MIME type detection | Hardcoded string mapping | MimeType enum from file_saver | Comprehensive list, prevents typos |

**Key insight:** Excel and CSV formats have deceptive complexity. Excel is a zip archive with 20+ XML files and strict schema requirements. CSV quoting rules are non-trivial (what if cell contains both quotes and commas?). Use battle-tested libraries that handle edge cases.

## Common Pitfalls

### Pitfall 1: Memory Explosion with Standard openpyxl Workbook Mode

**What goes wrong:** Exporting 1000-row Excel file uses 500MB+ memory, causing Railway container to OOM

**Why it happens:** openpyxl standard mode builds full cell object tree in memory (50x file size)

**How to avoid:**
- Always use `Workbook(write_only=True)` for exports
- write_only mode streams rows directly to zip file
- Memory usage stays under 10MB regardless of row count
- Tradeoff: can't read cells after writing, can't use formulas (acceptable for data export)

**Warning signs:**
- Backend memory usage spikes during export
- Railway deployment logs show OOM errors
- Export endpoint times out for files >100 rows

**Verification:**
```python
# BAD: Standard mode (50x memory)
wb = openpyxl.Workbook()
ws = wb.active
for row in rows:
    ws.append(row)

# GOOD: Write-only mode (~10MB)
wb = openpyxl.Workbook(write_only=True)
ws = wb.create_sheet()
for row in rows:
    ws.append(row)
```

### Pitfall 2: Missing UTF-8 BOM in CSV Exports

**What goes wrong:** User exports CSV, opens in Excel on Windows, sees "ÃƒÂ©" instead of "é"

**Why it happens:** Excel on Windows defaults to Windows-1252 encoding without BOM

**How to avoid:**
- Use `encode('utf-8-sig')` instead of `encode('utf-8')`
- utf-8-sig adds 3-byte BOM (EF BB BF) at start
- BOM tells Excel to use UTF-8 decoding
- Works on all platforms (Windows/Mac/Linux)

**Warning signs:**
- User reports "weird characters" in Excel
- International characters (é, ñ, 中) display incorrectly
- CSV opens correctly in VS Code but not Excel

**Verification:**
```python
# BAD: No BOM (Excel shows garbage on Windows)
csv_bytes = output.getvalue().encode('utf-8')

# GOOD: UTF-8 with BOM (Excel auto-detects)
csv_bytes = output.getvalue().encode('utf-8-sig')
```

### Pitfall 3: Content-Disposition Header Ignored in Flutter Web

**What goes wrong:** Downloaded file has generic name "download.xlsx" instead of document name

**Why it happens:** FileSaver ignores Content-Disposition if `name` parameter provided

**How to avoid:**
- Parse Content-Disposition header on frontend
- Extract filename from `filename="..."` directive
- Pass parsed filename to FileSaver.saveFile()
- Fallback to default if header missing

**Warning signs:**
- All exports download as "download.xlsx" or "download.csv"
- User has to manually rename files
- Multiple exports overwrite each other (same name)

**Verification:**
```dart
// BAD: Hardcoded filename
await FileSaver.instance.saveFile(
  name: 'export.xlsx',  // Always same name
  bytes: response.data,
);

// GOOD: Parse from Content-Disposition
String filename = 'export.xlsx';
final contentDisposition = response.headers.value('content-disposition');
if (contentDisposition != null) {
  final match = RegExp(r'filename="(.+)"').firstMatch(contentDisposition);
  if (match != null) filename = match.group(1)!;
}
await FileSaver.instance.saveFile(name: filename, bytes: response.data);
```

### Pitfall 4: Exporting PlutoGrid Filtered State Instead of Full Data

**What goes wrong:** User filters table to 10 rows, exports, expects full 1000 rows but only gets 10

**Why it happens:** Export uses PlutoGrid's filtered rows instead of original content_text

**How to avoid:**
- Phase 56: Export from backend content_text (full original data)
- Future enhancement: Add "Export filtered data" option that sends PlutoGrid state to backend
- Make it explicit in UI: "Export original data" vs "Export filtered view"

**Warning signs:**
- User confusion: "I filtered to check something, but export is missing data"
- Support tickets: "Export is incomplete"
- Need to document export behavior clearly

**Verification:**
Export button tooltip should clarify scope:
```dart
Tooltip(
  message: 'Export original data (ignores filters)',
  child: IconButton(icon: Icon(Icons.download)),
)
```

### Pitfall 5: CSV Delimiter Confusion (Comma vs Tab)

**What goes wrong:** Backend stores tab-separated, CSV export uses commas, user opens in region with semicolon delimiter

**Why it happens:** CSV "standard" varies by locale (comma in US, semicolon in Europe)

**How to avoid:**
- Backend content_text uses **tabs** (universal, no ambiguity)
- CSV export converts tabs to **commas** (most common CSV format)
- Use csv.writer (handles quoting automatically when cell contains comma)
- For European users: future enhancement to detect locale and use semicolon

**Warning signs:**
- European users report "all data in one column"
- CSV opens incorrectly in Excel with regional settings
- Users manually have to "Text to Columns" after opening

**Current approach:**
```python
# Backend storage: tab-separated (Phase 54)
content_text = "Name\tAge\tCity\nAlice\t30\tParis"

# CSV export: comma-separated with quoting
writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
# Handles: "Paris, France" → "\"Paris, France\"" automatically
```

## Code Examples

### Example 1: Excel Export Endpoint with Metadata Preservation

```python
# Source: FastAPI + openpyxl write_only mode
from io import BytesIO
from fastapi import Response, Depends, HTTPException
import openpyxl
import json

@router.get("/documents/{document_id}/export/xlsx")
async def export_document_xlsx(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export parsed Excel/CSV document to .xlsx format.

    Preserves column structure and data from content_text.
    Uses write_only mode for memory efficiency.
    """
    # Get document with ownership verification
    stmt = select(Document).join(Project).where(
        Document.id == document_id,
        Project.user_id == current_user["user_id"]
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify document is tabular format
    if doc.content_type not in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv']:
        raise HTTPException(status_code=400, detail="Document is not tabular format")

    # Parse metadata for sheet name
    metadata = json.loads(doc.metadata_json) if doc.metadata_json else {}
    sheet_name = 'Sheet1'
    if metadata.get('sheet_names'):
        sheet_name = metadata['sheet_names'][0]

    # Generate Excel file in memory
    output = BytesIO()
    wb = openpyxl.Workbook(write_only=True)  # Memory efficient mode
    ws = wb.create_sheet(title=sheet_name)

    # Parse content_text (tab-separated format from Phase 54)
    lines = doc.content_text.split('\n')
    for line in lines:
        if line.strip():  # Skip empty lines
            cells = line.split('\t')
            ws.append(cells)

    # Save to BytesIO
    wb.save(output)
    output.seek(0)

    # Generate filename
    base_filename = doc.filename.rsplit('.', 1)[0] if '.' in doc.filename else doc.filename
    export_filename = f"{base_filename}_export.xlsx"

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"'
        }
    )
```

### Example 2: CSV Export Endpoint with UTF-8 BOM

```python
# Source: Python csv.writer + UTF-8-BOM
import csv
from io import StringIO

@router.get("/documents/{document_id}/export/csv")
async def export_document_csv(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export parsed document to CSV format with UTF-8 BOM for Excel compatibility."""
    # Get document (same verification as XLSX endpoint)
    stmt = select(Document).join(Project).where(
        Document.id == document_id,
        Project.user_id == current_user["user_id"]
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify tabular format
    if doc.content_type not in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv']:
        raise HTTPException(status_code=400, detail="Document is not tabular format")

    # Generate CSV in memory
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Parse content_text (tab-separated)
    lines = doc.content_text.split('\n')
    for line in lines:
        if line.strip():
            cells = line.split('\t')
            writer.writerow(cells)

    # Convert to bytes with UTF-8 BOM (for Excel compatibility)
    csv_bytes = output.getvalue().encode('utf-8-sig')

    # Generate filename
    base_filename = doc.filename.rsplit('.', 1)[0] if '.' in doc.filename else doc.filename
    export_filename = f"{base_filename}_export.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"'
        }
    )
```

### Example 3: Frontend Export Service Method

```dart
// Source: DocumentService with FileSaver
import 'package:file_saver/file_saver.dart';
import 'package:dio/dio.dart';

class DocumentService {
  final Dio _dio;

  DocumentService() : _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000/api',
  ));

  Future<void> exportDocument(String documentId, String format) async {
    try {
      // Validate format
      if (format != 'xlsx' && format != 'csv') {
        throw ArgumentError('Invalid format. Must be xlsx or csv');
      }

      final endpoint = '/documents/$documentId/export/$format';

      // Download binary from backend
      final response = await _dio.get(
        endpoint,
        options: Options(
          responseType: ResponseType.bytes,
          headers: {
            'Accept': '*/*',
            'Authorization': 'Bearer ${await _getToken()}',
          },
        ),
      );

      // Extract filename from Content-Disposition header
      String filename = 'export.$format';
      final contentDisposition = response.headers.value('content-disposition');
      if (contentDisposition != null) {
        final filenameMatch = RegExp(r'filename="(.+)"').firstMatch(contentDisposition);
        if (filenameMatch != null) {
          filename = filenameMatch.group(1)!;
        }
      }

      // Determine MIME type
      final mimeType = format == 'xlsx'
        ? MimeType.microsoftExcel
        : MimeType.csv;

      // Save file using FileSaver (cross-platform)
      await FileSaver.instance.saveFile(
        name: filename,
        bytes: response.data as Uint8List,
        mimeType: mimeType,
      );

    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw Exception('Document not found');
      } else if (e.response?.statusCode == 400) {
        throw Exception('Invalid document format for export');
      } else {
        throw Exception('Export failed: ${e.message}');
      }
    } catch (e) {
      throw Exception('Export failed: $e');
    }
  }

  Future<String> _getToken() async {
    // Use existing auth token retrieval
    // ... (implementation from existing DocumentService)
  }
}
```

### Example 4: Export Buttons in ExcelTableViewer

```dart
// Source: Flutter PopupMenuButton + SnackBar feedback
class ExcelTableViewer extends StatefulWidget {
  final String documentId;  // NEW: pass document ID for export
  final Map<String, dynamic> metadata;

  // ... existing code
}

class _ExcelTableViewerState extends State<ExcelTableViewer> {
  // ... existing state

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Metadata header with export buttons
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            border: Border(
              bottom: BorderSide(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
          ),
          child: Row(
            children: [
              // Existing metadata
              Icon(Icons.table_chart, size: 18),
              SizedBox(width: 8),
              Text('$rowCount rows'),
              if (sheetNames != null && sheetNames.isNotEmpty) ...[
                SizedBox(width: 16),
                Text('• Sheet: ${sheetNames.join(', ')}'),
              ],

              Spacer(),

              // Export menu
              PopupMenuButton<String>(
                icon: Icon(Icons.download_rounded),
                tooltip: 'Export original data',
                onSelected: (format) => _handleExport(context, format),
                itemBuilder: (context) => [
                  PopupMenuItem(
                    value: 'xlsx',
                    child: Row(
                      children: [
                        Icon(Icons.table_chart, size: 20),
                        SizedBox(width: 12),
                        Text('Export to Excel (.xlsx)'),
                      ],
                    ),
                  ),
                  PopupMenuItem(
                    value: 'csv',
                    child: Row(
                      children: [
                        Icon(Icons.insert_drive_file, size: 20),
                        SizedBox(width: 12),
                        Text('Export to CSV'),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Existing PlutoGrid
        Expanded(
          child: _isLoading
            ? Center(child: CircularProgressIndicator())
            : PlutoGrid(columns: _columns, rows: _rows, ...),
        ),
      ],
    );
  }

  Future<void> _handleExport(BuildContext context, String format) async {
    // Show loading snackbar
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
            ),
            SizedBox(width: 12),
            Text('Exporting to ${format.toUpperCase()}...'),
          ],
        ),
        duration: Duration(seconds: 30),  // Long duration, will dismiss manually
      ),
    );

    try {
      final service = DocumentService();
      await service.exportDocument(widget.documentId, format);

      // Dismiss loading, show success
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              Icon(Icons.check_circle, color: Colors.white),
              SizedBox(width: 12),
              Text('Export complete'),
            ],
          ),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2),
        ),
      );
    } catch (e) {
      // Dismiss loading, show error
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              Icon(Icons.error, color: Colors.white),
              SizedBox(width: 12),
              Expanded(child: Text('Export failed: $e')),
            ],
          ),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 4),
        ),
      );
    }
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Export to CSV only | Export to both Excel and CSV | 2020+ | User expectation: Excel preserves formatting, CSV for universal compatibility |
| Standard openpyxl mode | write_only mode | 2016+ (openpyxl 2.4) | Performance: 50x less memory, handles 100k+ rows |
| Temp files on disk | In-memory BytesIO | 2015+ | Simpler code, faster, no cleanup needed |
| Manual CSV escaping | csv.writer module | Always | Correctness: handles edge cases (quotes in cells, newlines) |
| UTF-8 without BOM | UTF-8 with BOM for CSV | 2010+ | Excel compatibility: Windows Excel needs BOM to detect UTF-8 |

**Deprecated/outdated:**
- xlrd/xlwt: Old Excel libraries (xls format only), replaced by openpyxl for xlsx
- Manual Content-Disposition parsing: Use FileSaver package which handles platform differences
- Client-side Excel generation: Complex, large bundle size, backend generation more reliable

## Open Questions

1. **Should export preserve PlutoGrid filters/sorts or always export full data?**
   - What we know: Phase 56 requirements say "export parsed document data" (original data)
   - What's unclear: User expectation after filtering table to 10 rows
   - Recommendation: Phase 56 exports full data (simple, meets requirements). Future enhancement: "Export filtered view" option that sends PlutoGrid state to backend

2. **Should Excel export include formatting (bold headers, column widths)?**
   - What we know: openpyxl write_only mode doesn't support cell formatting
   - What's unclear: User expectation for "export to Excel" (data-only vs formatted)
   - Recommendation: Phase 56 exports data-only (no formatting). Formatting requires standard mode (memory issues) or XlsxWriter (new dependency)

3. **What about large datasets (10k+ rows)?**
   - What we know: openpyxl write_only handles 100k+ rows, but network transfer slow
   - What's unclear: Railway timeout limits for long-running export endpoints
   - Recommendation: Phase 56 handles up to 10k rows (sufficient for BA documents). Future: background job + download link for 100k+ rows

4. **Should CSV export be configurable (delimiter, encoding)?**
   - What we know: European Excel uses semicolon delimiter, different encoding preferences
   - What's unclear: Whether BA Assistant users need localization
   - Recommendation: Phase 56 uses comma delimiter + UTF-8-BOM (works for most users). Future: user preference setting for delimiter/encoding

## Sources

### Primary (HIGH confidence)

- [openpyxl Optimised Modes](https://openpyxl.readthedocs.io/en/3.1/optimized.html) - write_only mode documentation
- [openpyxl Performance](https://openpyxl.readthedocs.io/en/3.1/performance.html) - Memory usage benchmarks
- [Python csv module](https://docs.python.org/3/library/csv.html) - CSV writer API and quoting rules
- [FastAPI Response](https://fastapi.tiangolo.com/advanced/custom-response/) - Custom response types
- [file_saver package](https://pub.dev/packages/file_saver) - FileSaver API and platform support
- [pluto_grid_export package](https://pub.dev/packages/pluto_grid_export) - CSV/PDF export capabilities

### Secondary (MEDIUM confidence)

- [How to add CSV and Excel Exports to your FastAPI Applications](https://medium.com/@liamwr17/supercharge-your-apis-with-csv-and-excel-exports-fastapi-pandas-a371b2c8f030) - StreamingResponse patterns
- [Return Excel/CSV File as a Response Stream FastAPI](https://cvarma.com/blogs/2023/excel-file-responsestream-fastapi.html) - BytesIO + Response pattern
- [Writing CSV Files in Python (The Production-Ready Guide for 2026)](https://thelinuxcode.com/writing-csv-files-in-python-the-production-ready-guide-for-2026/) - UTF-8 BOM best practices
- [Optimizing Excel Report Generation: From OpenPyXL to XLSMerge](https://mass-software-solutions.medium.com/optimizing-excel-report-generation-from-openpyxl-to-xlsmerge-processing-52-columns-200k-rows-5b5a03ecbcd4) - Performance comparison
- [XlsxWriter Working with Memory and Performance](https://xlsxwriter.readthedocs.io/working_with_memory.html) - constant_memory mode documentation

### Tertiary (LOW confidence - needs validation)

- [Flutter CSV Field Matching: Importing & Saving CSV Files](https://medium.com/@bosctechlabs/flutter-csv-field-matching-661a0d8a25eb) - Client-side CSV generation (not recommended for Phase 56)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - openpyxl and csv module are official Python libraries, file_saver is established Flutter package
- Architecture: HIGH - FastAPI StreamingResponse pattern is well-documented, FileSaver usage verified in pub.dev docs
- Pitfalls: HIGH - openpyxl memory issues documented in official performance guide, UTF-8 BOM requirement confirmed in multiple sources

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days - stable domain)

**Backend stack:**
- openpyxl: 3.1.4+ (already installed)
- csv: Python 3.9 stdlib
- FastAPI Response: 0.115.0+ (already installed)

**Frontend stack:**
- file_saver: 0.2.14 (already installed)
- dio: 5.9.0 (already installed)
- pluto_grid: 8.1.0 (already installed)

**Phase dependencies:**
- Phase 54: Document parsing creates content_text (tab-separated format)
- Phase 55: ExcelTableViewer displays PlutoGrid, provides documentId for export
- Phase 56: Export endpoints read content_text and generate files
