# Phase 55: Frontend Display & AI Context Integration - Research

**Researched:** 2026-02-12
**Domain:** Flutter table rendering, document viewers, LLM token budget management, RAG context optimization
**Confidence:** HIGH

## Summary

Phase 55 builds on Phase 54's backend parsing infrastructure to deliver format-aware document rendering in Flutter and AI-powered document search with token budget management. The phase addresses three distinct technical challenges: (1) rendering large tabular datasets without browser freeze, (2) creating format-specific document viewers for Excel/CSV/PDF/Word, and (3) integrating rich documents into Claude's conversation context without exceeding token limits.

Flutter's built-in DataTable is unsuitable for 1000+ row datasets (requires laying out entire table twice). The ecosystem offers two production-ready alternatives: **pluto_grid** (comprehensive datagrid with keyboard navigation, sorting, filtering) and **PaginatedDataTable** (simpler, built-in widget with server-side pagination). For Phase 55's requirements (sorting, filtering, 1000+ rows), **pluto_grid 8.7.0** is the standard choice due to built-in virtualization, column operations, and active maintenance.

Token budget management follows RAG best practices: chunk documents at 512 tokens with 50-100 token overlap, use BM25-ranked retrieval to surface most relevant 2-3 chunks (not all 10), and Claude's context window is 200K tokens (500K on Enterprise for Sonnet 4.5). The existing document_search tool already implements FTS5 BM25 ranking with snippet extraction - Phase 55 extends it to include format-specific metadata (sheet name, page number) in results.

**Primary recommendation:** Implement upload preview dialog with pluto_grid table (DISP-01, DISP-02), create format-aware DocumentViewerScreen with conditional rendering (DISP-03, DISP-04), add pluto_grid to existing viewer for table formats (DISP-05), and extend document_search tool to include metadata in snippets (AI-01, AI-03). Token budget management (AI-02) requires limiting retrieved chunks, not truncating individual documents (Phase 54 already implements 5k-char AI summary strategy).

## Standard Stack

### Core Libraries

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pluto_grid | 8.7.0+ | Flutter datagrid with virtualization | Industry standard for large dataset rendering, supports sorting/filtering/pagination, keyboard navigation, 100k+ row virtualization |
| file_picker | 10.3.8 | Cross-platform file selection | Already in project (pubspec.yaml line 42), used in document_upload_screen.dart |
| dio | 5.9.0 | HTTP client for document APIs | Already in project (pubspec.yaml line 38), used in document_service.dart |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PaginatedDataTable (Flutter SDK) | N/A | Built-in paginated table widget | Simple use cases (<10 columns, server-side pagination), not suitable for Phase 55's client-side sorting/filtering |
| DataTable (Flutter SDK) | N/A | Basic table widget | Small datasets (<100 rows), Phase 55 requires virtualization |
| flutter_data_grid | Latest | Alternative high-performance grid | Commercial-grade features, but pluto_grid is more established in open-source community |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pluto_grid | PaginatedDataTable | PaginatedDataTable requires server-side pagination for large datasets, Phase 55 needs client-side sorting/filtering after parse |
| pluto_grid | flutter_data_grid | Both support virtualization, pluto_grid has better keyboard navigation for desktop/web |
| pluto_grid | DataTable | DataTable has no virtualization, lays out entire table (freezes at 1000+ rows) |
| Client preview | Server-side preview API | Preview during upload requires client-side parsing to show data before server commit |

**Installation:**
```bash
cd frontend
flutter pub add pluto_grid
```

**Already installed (from pubspec.yaml):**
- file_picker: ^10.3.8 (line 42)
- dio: ^5.9.0 (line 38)
- provider: ^6.1.5+1 (line 37)

## Architecture Patterns

### Recommended Project Structure

```
frontend/lib/
├── models/
│   └── document.dart                  # Add metadata field (Map<String, dynamic>)
├── screens/documents/
│   ├── document_upload_screen.dart    # Add preview dialog before upload
│   ├── document_viewer_screen.dart    # Conditional rendering by content_type
│   └── widgets/
│       ├── excel_table_viewer.dart    # PlutoGrid for Excel/CSV
│       ├── pdf_text_viewer.dart       # Text with [Page N] markers
│       ├── word_text_viewer.dart      # Structured paragraphs
│       └── upload_preview_dialog.dart # Sheet selector + first 10 rows preview
├── services/
│   └── document_service.dart          # Add getDocumentMetadata() method
└── widgets/
    └── source_attribution_chip.dart   # Format-specific info (sheet, page)

backend/app/services/
└── document_search.py                 # Extend search_documents() to include metadata
```

### Pattern 1: Conditional Viewer Rendering by Content Type

**What:** Route document display to format-specific viewers based on content_type

**When to use:** When multiple input formats require different UI components (table vs text)

**Example:**
```dart
// Source: Flutter conditional widget pattern
Widget _buildDocumentContent(Document doc) {
  final contentType = doc.contentType ?? 'text/plain';

  switch (contentType) {
    case 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
    case 'text/csv':
      // Excel/CSV: PlutoGrid with sorting/filtering
      return ExcelTableViewer(
        documentId: doc.id,
        metadata: doc.metadata, // sheet_names, row_counts, column_headers
      );

    case 'application/pdf':
      // PDF: Text viewer with [Page N] markers
      return PdfTextViewer(
        content: doc.content,
        pageCount: doc.metadata['page_count'],
      );

    case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
      // Word: Structured paragraph viewer
      return WordTextViewer(
        content: doc.content,
      );

    default:
      // Plain text/markdown
      return PlainTextViewer(
        content: doc.content,
      );
  }
}
```

### Pattern 2: PlutoGrid for Large Tabular Data

**What:** Use PlutoGrid with virtualized rendering for 1000+ row Excel/CSV files

**When to use:** When dataset size unknown at upload time (user may upload 10 rows or 10k rows)

**Example:**
```dart
// Source: pluto_grid documentation
import 'package:pluto_grid/pluto_grid.dart';

class ExcelTableViewer extends StatefulWidget {
  final String documentId;
  final Map<String, dynamic> metadata;

  @override
  State<ExcelTableViewer> createState() => _ExcelTableViewerState();
}

class _ExcelTableViewerState extends State<ExcelTableViewer> {
  List<PlutoColumn> columns = [];
  List<PlutoRow> rows = [];
  PlutoGridStateManager? stateManager;

  @override
  void initState() {
    super.initState();
    _loadTableData();
  }

  Future<void> _loadTableData() async {
    // Parse content_text from backend (tab-separated format)
    final doc = await documentService.getDocument(widget.documentId);
    final lines = doc.content.split('\n');

    // First line is column headers
    final headers = lines[0].split('\t');

    // Build PlutoGrid columns
    columns = headers.map((header) => PlutoColumn(
      title: header,
      field: 'col_${headers.indexOf(header)}',
      type: PlutoColumnType.text(),
      enableSorting: true,
      enableColumnDrag: false,
    )).toList();

    // Build PlutoGrid rows (skip header line)
    rows = lines.skip(1).map((line) {
      final cells = line.split('\t');
      return PlutoRow(
        cells: Map.fromIterables(
          headers.map((h) => 'col_${headers.indexOf(h)}'),
          cells.map((cell) => PlutoCell(value: cell)),
        ),
      );
    }).toList();

    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Metadata header
        Container(
          padding: EdgeInsets.all(16),
          child: Text('${widget.metadata['row_count']} rows, Sheet: ${widget.metadata['sheet_names'][0]}'),
        ),
        // Virtualized table
        Expanded(
          child: PlutoGrid(
            columns: columns,
            rows: rows,
            onLoaded: (PlutoGridOnLoadedEvent event) {
              stateManager = event.stateManager;
            },
            configuration: PlutoGridConfiguration(
              // Performance optimizations
              enableMoveDownAfterSelecting: false,
              enterKeyAction: PlutoGridEnterKeyAction.none,
            ),
          ),
        ),
      ],
    );
  }
}
```

**Why this works:**
- PlutoGrid virtualizes rows: only renders visible viewport (~20 rows at a time)
- Sorting/filtering built-in: no custom state management needed
- Handles 100k+ rows without freeze: tested by pluto_grid maintainers
- Keyboard navigation: desktop/web users can navigate with arrow keys

### Pattern 3: Upload Preview Dialog with Sheet Selector

**What:** Show preview of Excel/CSV data before upload, with sheet selector for multi-sheet workbooks

**When to use:** User needs to confirm data looks correct and choose which Excel sheets to parse

**Example:**
```dart
// Source: Flutter AlertDialog with DataTable pattern
Future<bool?> showUploadPreviewDialog(
  BuildContext context,
  PlatformFile file,
  Map<String, dynamic> parsedData,
) {
  return showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Preview: ${file.name}'),
      content: SizedBox(
        width: 600,
        height: 400,
        child: Column(
          children: [
            // Sheet selector (if multiple sheets)
            if (parsedData['sheet_names'] != null && parsedData['sheet_names'].length > 1)
              DropdownButton<String>(
                value: _selectedSheet,
                items: parsedData['sheet_names'].map<DropdownMenuItem<String>>((sheet) {
                  return DropdownMenuItem(value: sheet, child: Text(sheet));
                }).toList(),
                onChanged: (sheet) => setState(() => _selectedSheet = sheet),
              ),

            // Preview first 10 rows in DataTable (not PlutoGrid - too heavy for dialog)
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.vertical,
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: _buildColumns(parsedData['headers']),
                    rows: _buildRows(parsedData['preview_rows']), // First 10 rows only
                  ),
                ),
              ),
            ),

            Text('Showing first 10 of ${parsedData['total_rows']} rows'),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, true),
          child: Text('Upload'),
        ),
      ],
    ),
  );
}
```

**Why this approach:**
- Preview uses lightweight DataTable (10 rows only), not PlutoGrid (too heavy for modal)
- Sheet selector only shown for multi-sheet workbooks (conditional rendering)
- User confirmation required before server upload (UX best practice)
- Client-side parsing for preview: use excel package (Dart library) to read .xlsx bytes

### Pattern 4: Token Budget Management with Chunked Retrieval

**What:** Limit document context sent to LLM by retrieving only top-ranked chunks, not full documents

**When to use:** Large documents (10MB PDFs) would exceed context window if sent in full

**Example:**
```python
# Source: RAG best practices + existing document_search.py
async def search_documents(
    db: AsyncSession,
    project_id: str,
    query: str,
    max_chunks: int = 3,  # NEW: Limit retrieval to top 3 chunks
) -> List[Tuple[str, str, str, float, dict]]:
    """
    Search documents with BM25 ranking and metadata.

    Returns:
        List of tuples: (document_id, filename, snippet, score, metadata)
        metadata includes: sheet_name, page_number, row_count
    """
    result = await db.execute(
        text("""
            SELECT d.id, d.filename,
                   snippet(document_fts, 2, '<mark>', '</mark>', '...', 20) as snippet,
                   bm25(document_fts, 10.0, 1.0) as score,
                   d.metadata_json
            FROM documents d
            JOIN document_fts fts ON d.id = fts.document_id
            WHERE d.project_id = :project_id
              AND document_fts MATCH :query
            ORDER BY score
            LIMIT :max_chunks  -- Retrieve top N chunks only
        """),
        {"project_id": project_id, "query": query, "max_chunks": max_chunks}
    )

    results = []
    for row in result.fetchall():
        doc_id, filename, snippet, score, metadata_json = row
        metadata = json.loads(metadata_json) if metadata_json else {}

        # Add format-specific context to snippet
        if metadata.get('sheet_names'):
            snippet = f"[Sheet: {metadata['sheet_names'][0]}]\n{snippet}"
        elif metadata.get('page_count'):
            # Extract page number from snippet marker [Page N]
            page_match = re.search(r'\[Page (\d+)\]', snippet)
            if page_match:
                snippet = f"[Page {page_match.group(1)}]\n{snippet}"

        results.append((doc_id, filename, snippet, score, metadata))

    return results
```

**Why this works:**
- BM25 ranking already implemented in Phase 54 (document_search.py)
- Top 3 chunks (512 tokens each) = ~1500 tokens max, well under 200K context window
- Format-specific metadata (sheet name, page number) helps user trace source
- Claude's RAG feature automatically manages context if documents exceed limits

### Anti-Patterns to Avoid

- **Loading full document into PlutoGrid rows at once:** Parse content_text into rows lazily, or use pagination for 10k+ row files
- **Re-parsing documents on every viewer open:** Cache parsed PlutoGrid columns/rows in provider after first load
- **Sending full 10MB document text to Claude:** Use existing 5k-char summary from Phase 54, or implement chunked retrieval
- **DataTable for large datasets:** DataTable has no virtualization - browser freezes at 1000+ rows
- **Client-side Excel parsing in Flutter web:** Use backend parsing from Phase 54, only parse on client for upload preview

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table virtualization | Custom scrollable column renderer | pluto_grid or PaginatedDataTable | Edge cases: column resizing, frozen headers, keyboard navigation, accessibility |
| Excel parsing in Dart | Manual XLSX zip extraction | excel package (Dart) for preview only, backend openpyxl for storage | XLSX has 400+ cell format types, date systems (1900 vs 1904), merged cells |
| Token counting | Character-based estimation | tiktoken (Python) or anthropic.count_tokens() | LLM tokenizers are non-trivial: "hello" = 1 token, "🚀" = 3 tokens |
| Document chunking | Split on paragraphs | LangChain RecursiveCharacterTextSplitter | Handles chunk overlap, preserves semantic boundaries, respects token limits |
| Context window management | Manual truncation | Claude RAG + BM25 retrieval | Claude automatically manages context, BM25 surfaces most relevant chunks |

**Key insight:** Table rendering and token budget management are both deceptively complex. PlutoGrid handles 100+ virtualization edge cases (column pinning, cell editing, keyboard navigation). Token counting requires understanding subword tokenization (BPE, WordPiece). Use battle-tested libraries and leverage Claude's built-in RAG.

## Common Pitfalls

### Pitfall 1: Loading Entire Dataset into Memory on Viewer Open

**What goes wrong:** Loading 10k-row Excel file into List<PlutoRow> at once causes 2-3 second freeze

**Why it happens:** Parsing full content_text (tab-separated format) into PlutoGrid rows is synchronous

**How to avoid:**
- Use FutureBuilder for async loading with loading indicator
- For 10k+ rows, implement pagination (load 1000 rows at a time)
- Cache parsed rows in DocumentProvider after first load

**Warning signs:**
- CircularProgressIndicator shows briefly then UI freezes
- DevTools shows frame drops during viewer initialization
- Large Excel files take 5+ seconds to open

### Pitfall 2: Re-parsing Documents on Every Search Query

**What goes wrong:** AI document_search tool re-parses 10MB PDF for every user message

**Why it happens:** Parsing happens in search_documents() instead of upload time

**How to avoid:**
- Phase 54 already stores content_text at upload time (correct approach)
- FTS5 index built once at upload, search queries use index
- Never re-parse documents after initial upload

**Warning signs:**
- AI responses slow for projects with large documents
- Backend logs show "Parsing PDF..." on every search
- openpyxl/pdfplumber imports in document_search.py (should only be in parsers)

### Pitfall 3: Exceeding Context Window with Full Document Content

**What goes wrong:** Sending full 10MB PDF text to Claude causes "context limit exceeded" error

**Why it happens:** Attempting to include all document content in conversation context

**How to avoid:**
- Use document_search tool, not direct content injection
- Limit retrieval to top 2-3 chunks (max_chunks parameter)
- Phase 54's 5k-char summary strategy already prevents this for individual documents
- Claude's RAG feature automatically manages context if enabled

**Warning signs:**
- "Context limit exceeded" errors in AI responses
- Slow AI responses for large documents (>1MB)
- Token usage showing 150k+ input tokens per message

### Pitfall 4: Using DataTable Instead of PlutoGrid for Large Datasets

**What goes wrong:** Browser freezes when opening Excel file with 1000+ rows

**Why it happens:** DataTable lays out entire table twice (negotiation + render), no virtualization

**How to avoid:**
- Use PlutoGrid for Excel/CSV viewer (DISP-05 requirement)
- DataTable only for small datasets (<100 rows) or upload preview dialog (10 rows)
- Flutter docs explicitly warn against DataTable for large datasets

**Warning signs:**
- UI freeze lasting 3+ seconds when opening document viewer
- DevTools shows "Layout" phase taking 2000ms+
- Memory usage spikes when opening viewer

### Pitfall 5: No Sheet Selection for Multi-Sheet Excel Files

**What goes wrong:** User uploads 5-sheet workbook, only Sheet1 is parsed

**Why it happens:** Backend parser defaults to all sheets, but user may want specific sheets only

**How to avoid:**
- Show sheet selector in upload preview dialog (DISP-02)
- Send selected_sheets parameter to backend upload endpoint
- Backend parses only selected sheets (reduces token usage for 20-sheet workbooks)

**Warning signs:**
- User reports "missing data" from Excel upload
- AI search returns results only from Sheet1
- Backend logs show all sheets parsed despite user selecting subset

## Code Examples

### Example 1: Document Model with Metadata

```dart
// Source: Existing document.dart extended with metadata field
class Document {
  final String id;
  final String filename;
  final String? content;
  final String? contentType;  // NEW
  final Map<String, dynamic>? metadata;  // NEW
  final DateTime createdAt;

  Document({
    required this.id,
    required this.filename,
    required this.createdAt,
    this.content,
    this.contentType,
    this.metadata,
  });

  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'],
      filename: json['filename'],
      createdAt: DateTime.parse(json['created_at']),
      content: json['content'],
      contentType: json['content_type'],
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}
```

### Example 2: Format-Specific Metadata Display

```dart
// Source: Flutter conditional rendering pattern
Widget _buildMetadataHeader(Document doc) {
  final contentType = doc.contentType ?? 'text/plain';
  final metadata = doc.metadata ?? {};

  if (contentType.contains('spreadsheet') || contentType == 'text/csv') {
    // Excel/CSV metadata
    final rowCount = metadata['row_count'] ?? metadata['total_rows'] ?? 0;
    final sheetNames = metadata['sheet_names'] as List? ?? [];

    return Container(
      padding: EdgeInsets.all(16),
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      child: Row(
        children: [
          Icon(Icons.table_chart, size: 20),
          SizedBox(width: 8),
          Text('$rowCount rows'),
          if (sheetNames.isNotEmpty) ...[
            SizedBox(width: 16),
            Text('Sheet: ${sheetNames[0]}'),
          ],
        ],
      ),
    );
  } else if (contentType == 'application/pdf') {
    // PDF metadata
    final pageCount = metadata['page_count'] ?? 0;

    return Container(
      padding: EdgeInsets.all(16),
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      child: Row(
        children: [
          Icon(Icons.picture_as_pdf, size: 20),
          SizedBox(width: 8),
          Text('$pageCount pages'),
        ],
      ),
    );
  }

  // Default: no special metadata
  return SizedBox.shrink();
}
```

### Example 3: Client-Side Excel Preview Parsing

```dart
// Source: excel package documentation
import 'package:excel/excel.dart';

Future<Map<String, dynamic>> parseExcelForPreview(Uint8List bytes) async {
  var excel = Excel.decodeBytes(bytes);

  // Get first sheet
  var sheet = excel.tables.keys.first;
  var table = excel.tables[sheet]!;

  // Extract first 10 rows
  final previewRows = table.rows.take(10).map((row) {
    return row.map((cell) => cell?.value.toString() ?? '').toList();
  }).toList();

  return {
    'sheet_names': excel.tables.keys.toList(),
    'headers': previewRows.isNotEmpty ? previewRows[0] : [],
    'preview_rows': previewRows.skip(1).toList(),
    'total_rows': table.rows.length,
  };
}
```

### Example 4: AI Search with Format-Specific Attribution

```python
# Source: Extended document_search.py from Phase 54
async def format_search_results_for_ai(
    results: List[Tuple[str, str, str, float, dict]]
) -> str:
    """Format search results with format-specific attribution for AI context."""
    formatted = []

    for doc_id, filename, snippet, score, metadata in results[:3]:  # Top 3 only
        # Add format-specific prefix
        if metadata.get('sheet_names'):
            prefix = f"[{filename} - Sheet: {metadata['sheet_names'][0]}]"
        elif metadata.get('page_count'):
            # Extract page number from snippet
            page_match = re.search(r'\[Page (\d+)\]', snippet)
            page_info = f"Page {page_match.group(1)}" if page_match else "PDF"
            prefix = f"[{filename} - {page_info}]"
        else:
            prefix = f"[{filename}]"

        # Clean snippet HTML markers
        clean_snippet = snippet.replace('<mark>', '**').replace('</mark>', '**')

        formatted.append(f"{prefix}\n{clean_snippet}")

    return "\n\n---\n\n".join(formatted)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DataTable for all tables | PlutoGrid with virtualization | 2022+ | Performance: 100k+ rows without freeze |
| Client-side Excel parsing | Backend parsing + preview | 2020+ | Security: server-side validation, consistent format |
| Full document context | RAG with chunked retrieval | 2023+ | Scalability: 10x more documents per project |
| Manual token counting | Claude RAG auto-management | 2024+ | Reliability: no context overflow errors |
| Generic source chips | Format-specific attribution | 2025+ | UX: user knows which sheet/page AI referenced |

**Deprecated/outdated:**
- DataTable for large datasets: Flutter docs recommend PaginatedDataTable or custom virtualization
- Sending full documents to LLM: RAG with semantic search is now standard practice
- Character-based token estimation: Subword tokenization (BPE) requires proper token counting

## Open Questions

1. **Should upload preview parse Excel on client or request preview from backend?**
   - What we know: Client parsing (excel package) adds 500KB to web bundle, backend parsing reuses existing openpyxl infrastructure
   - What's unclear: Performance tradeoff for large files (10MB XLSX preview on client vs network roundtrip)
   - Recommendation: Client-side parsing for preview only (using excel package), keeps UX responsive without server roundtrip

2. **How many chunks should document_search return to Claude?**
   - What we know: Claude context window is 200K tokens, top 3 chunks = ~1500 tokens
   - What's unclear: Optimal retrieval count for accuracy vs token usage
   - Recommendation: Start with top 3 chunks (configurable), monitor AI response quality in testing

3. **Should PlutoGrid configuration enable cell editing?**
   - What we know: Phase 55 is display-only (DISP-03), Phase 56 adds export (EXP-01)
   - What's unclear: Whether editing is needed for Phase 56 export workflow
   - Recommendation: Disable editing in Phase 55 (readonly: true), enable in Phase 56 if export workflow requires it

## Sources

### Primary (HIGH confidence)

- [pluto_grid | Flutter package](https://pub.dev/packages/pluto_grid) - Package documentation and features
- [PaginatedDataTable class - Flutter API](https://api.flutter.dev/flutter/material/PaginatedDataTable-class.html) - Official Flutter documentation
- [DataTable class - Flutter API](https://api.flutter.dev/flutter/material/DataTable-class.html) - Performance limitations warning
- [Claude context windows - Anthropic Docs](https://platform.claude.com/docs/en/build-with-claude/context-windows) - Token limits and RAG features
- [Retrieval augmented generation (RAG) for projects](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects) - Claude RAG capabilities

### Secondary (MEDIUM confidence)

- [Mastering Flutter DataGrid with Pagination](https://www.syncfusion.com/blogs/post/add-pagination-in-flutter-datagrid) - Pagination best practices
- [Chunking Strategies for LLM Applications | Pinecone](https://www.pinecone.io/learn/chunking-strategies/) - RAG chunking strategies (512 tokens, 50-100 overlap)
- [Managing Token Budgets for Complex Prompts](https://apxml.com/courses/getting-started-with-llm-toolkit/chapter-3-context-and-token-management/managing-token-budgets) - Token budget management patterns
- [Flutter Performance Optimization 2026](https://dasroot.net/posts/2026/02/flutter-performance-optimization-large-scale-applications/) - Virtual scrolling and lazy loading
- [LLM Context Management: 5 Strategies That Work](https://fast.io/resources/llm-context-management-strategies/) - Chunking and truncation strategies

### Tertiary (LOW confidence - needs validation)

- [PlutoGrid Flutter Gems](https://fluttergems.dev/packages/pluto_grid/) - Community examples and usage stats
- [Excel library for Flutter | Syncfusion](https://www.syncfusion.com/blogs/post/introducing-excel-library-for-flutter) - Commercial Excel handling alternative

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pluto_grid is established (8.7.0 released 2024), Flutter SDK PaginatedDataTable is official
- Architecture: HIGH - Conditional rendering pattern is Flutter standard, RAG chunking is industry best practice
- Pitfalls: HIGH - DataTable performance limitation documented in official Flutter API docs, token limits from Anthropic docs

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days - stable domain, Flutter ecosystem mature)

**Flutter version:** 3.9.2 (from pubspec.yaml)
**Existing dependencies:** file_picker 10.3.8, dio 5.9.0, provider 6.1.5+1
**New dependencies required:** pluto_grid 8.7.0+, excel (for client-side preview parsing)

**Phase 54 dependencies:**
- Backend parsing complete (openpyxl, pdfplumber, python-docx, chardet)
- Document model has content_type, content_text, metadata_json fields
- FTS5 search returns BM25-ranked snippets with document metadata
- Upload endpoint validates and parses all 4 rich document formats
