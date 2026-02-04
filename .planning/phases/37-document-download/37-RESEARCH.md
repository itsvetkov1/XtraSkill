# Phase 37: Document Download - Research

**Researched:** 2026-02-04
**Domain:** Flutter file download with file_saver package
**Confidence:** HIGH

## Summary

Document download is the lowest-risk phase in v1.9.3 because the exact pattern already exists in `artifact_service.dart`. The implementation requires copying the proven `file_saver` approach to download text document content as files. The document model already has `filename` and `content` properties that provide everything needed for download.

The key difference from artifact export is simplicity: documents are plain text files (`.txt` or `.md`) that don't need backend export endpoint conversion. The content is already available in `DocumentProvider.selectedDocument.content` as a string, which just needs UTF-8 encoding to bytes.

**Primary recommendation:** Add `downloadDocument()` method using existing `file_saver` pattern, with download icon in DocumentViewerScreen AppBar and download option in DocumentListScreen context menu.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| file_saver | 0.2.14 | Cross-platform file download | Already proven in artifact export; works on web, Android, iOS |
| provider | 6.1.5 | State management | DocumentProvider already provides document content |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dart:typed_data | built-in | Uint8List for bytes | Required by file_saver.saveFile() |
| dart:convert | built-in | UTF-8 encoding | Convert string content to bytes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| file_saver | dart:html (web) | DEPRECATED - don't use; file_saver handles cross-platform |
| file_saver | web package | More complex; file_saver already works |

**Installation:**
```bash
# No installation needed - file_saver 0.2.14 already in pubspec.yaml
```

## Architecture Patterns

### Recommended Project Structure
No new files needed. Changes go in existing files:

```
frontend/lib/
├── screens/documents/
│   ├── document_viewer_screen.dart  # Add download IconButton to AppBar
│   └── document_list_screen.dart    # Add download to PopupMenuButton
└── (no new service needed - pattern is simple enough for screen-level code)
```

### Pattern 1: Screen-Level Download (Recommended)

**What:** Implement download directly in the screen widget rather than creating a service method
**When to use:** Simple operations that don't need reuse across multiple screens
**Why:** Document download is 10 lines of code; creating a service method adds unnecessary abstraction

**Example (adapted from artifact_service.dart):**
```dart
// Source: artifact_service.dart lines 97-104 (adapted)
import 'dart:convert';
import 'dart:typed_data';
import 'package:file_saver/file_saver.dart';

Future<void> _downloadDocument(Document doc) async {
  if (doc.content == null) return;

  final bytes = Uint8List.fromList(utf8.encode(doc.content!));
  final extension = doc.filename.split('.').last;
  final nameWithoutExt = doc.filename.replaceAll(RegExp(r'\.[^.]+$'), '');

  await FileSaver.instance.saveFile(
    name: nameWithoutExt,
    bytes: bytes,
    ext: extension,
    mimeType: MimeType.text,
  );
}
```

### Pattern 2: AppBar Action Button

**What:** Download icon in AppBar actions array
**When to use:** Primary action on detail/viewer screens
**Why:** Consistent with artifact viewer, easily discoverable

**Example:**
```dart
// Source: artifact_card.dart pattern
AppBar(
  title: Text(provider.selectedDocument?.filename ?? 'Loading...'),
  actions: [
    IconButton(
      icon: const Icon(Icons.download),
      tooltip: 'Download',
      onPressed: () => _downloadDocument(provider.selectedDocument!),
    ),
  ],
),
```

### Pattern 3: Context Menu Option

**What:** Download option in PopupMenuButton
**When to use:** Secondary action in list items
**Why:** Consistent with existing View/Delete options in document list

**Example (from document_list_screen.dart lines 128-148):**
```dart
PopupMenuButton<String>(
  onSelected: (value) {
    if (value == 'download') {
      _downloadDocument(doc);
    }
    // ... other options
  },
  itemBuilder: (context) => [
    const PopupMenuItem(
      value: 'download',
      child: Row(
        children: [
          Icon(Icons.download),
          SizedBox(width: 8),
          Text('Download'),
        ],
      ),
    ),
    // ... other menu items
  ],
),
```

### Pattern 4: Success Snackbar (from artifact_card.dart)

**What:** Show confirmation after download completes
**When to use:** Always after successful download
**Why:** User feedback that action completed (especially on web where download may be silent)

**Example:**
```dart
// Source: artifact_card.dart lines 213-221 (adapted)
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(
    content: Text('Downloaded ${doc.filename}'),
    action: SnackBarAction(
      label: 'OK',
      onPressed: () {},
    ),
  ),
);
```

### Anti-Patterns to Avoid
- **Using dart:html:** Deprecated; breaks on mobile. Use file_saver instead.
- **Creating a full DocumentDownloadService:** Over-engineering for 10 lines of code.
- **Showing download confirmation dialog:** Unnecessary friction (per v1.9.3 research).
- **Custom filename generation:** Use original filename from document model.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-platform file save | Platform-specific code with dart:io/dart:html | file_saver | Already handles web/Android/iOS differences |
| MIME type detection | Custom extension-to-MIME mapping | MimeType.text | Text files (.txt, .md) all use text MIME type |

**Key insight:** The entire download implementation is already proven in artifact_service.dart. The only adaptation needed is using document content (string) instead of API response (bytes).

## Common Pitfalls

### Pitfall 1: Using dart:html (PITFALL-02 from v1.9.3)
**What goes wrong:** Code fails on Android/iOS; package is deprecated
**Why it happens:** Old tutorials use dart:html for web downloads
**How to avoid:** Use file_saver package which handles all platforms
**Warning signs:** Import of `dart:html`

### Pitfall 2: Forgetting mounted check after async
**What goes wrong:** "setState() called after dispose()" error
**Why it happens:** Download completes after user navigates away
**How to avoid:** Check `if (mounted)` before showing snackbar
**Warning signs:** Console errors about disposed widgets

### Pitfall 3: Document content is null in list view
**What goes wrong:** Download from list fails because doc.content is null
**Why it happens:** Document list only has metadata, not content
**How to avoid:** For list download, either:
  1. Fetch content first with `getDocumentContent(docId)`
  2. Or add download API endpoint (overkill for v1.9.3)
**Warning signs:** Null content when downloading from list

### Pitfall 4: Wrong file extension parsing
**What goes wrong:** File downloads as "document.txt.txt" or loses extension
**Why it happens:** file_saver concatenates name + ext
**How to avoid:** Strip extension from name, pass extension separately
**Warning signs:** Double extension or missing extension in downloaded file

## Code Examples

Verified patterns from codebase:

### File Saver Usage (from artifact_service.dart)
```dart
// Source: frontend/lib/services/artifact_service.dart lines 97-104
await FileSaver.instance.saveFile(
  name: filename,           // Without extension
  bytes: Uint8List.fromList(response.data!),
  ext: format,              // Extension only (e.g., 'txt', 'md')
  mimeType: _getMimeType(format),
);
```

### Success Snackbar Pattern (from artifact_card.dart)
```dart
// Source: frontend/lib/screens/conversation/widgets/artifact_card.dart lines 212-221
if (mounted) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text('Exported: $filename'),
      action: SnackBarAction(
        label: 'OK',
        onPressed: () {},
      ),
    ),
  );
}
```

### Error Snackbar Pattern (from artifact_card.dart)
```dart
// Source: frontend/lib/screens/conversation/widgets/artifact_card.dart lines 225-229
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(
    content: Text('Export failed: $e'),
    backgroundColor: Theme.of(context).colorScheme.error,
  ),
);
```

### Context Menu Pattern (from document_list_screen.dart)
```dart
// Source: frontend/lib/screens/documents/document_list_screen.dart lines 114-150
trailing: PopupMenuButton<String>(
  onSelected: (value) {
    if (value == 'view') {
      Navigator.push(context, MaterialPageRoute(
        builder: (context) => DocumentViewerScreen(documentId: doc.id),
      ));
    } else if (value == 'delete') {
      _deleteDocument(context, doc.id);
    }
  },
  itemBuilder: (context) => [
    const PopupMenuItem(
      value: 'view',
      child: Row(
        children: [
          Icon(Icons.visibility),
          SizedBox(width: 8),
          Text('View'),
        ],
      ),
    ),
    const PopupMenuItem(
      value: 'delete',
      child: Row(
        children: [
          Icon(Icons.delete_outline),
          SizedBox(width: 8),
          Text('Delete'),
        ],
      ),
    ),
  ],
),
```

### Document Model Properties
```dart
// Source: frontend/lib/models/document.dart
class Document {
  final String id;
  final String filename;       // Original filename with extension (e.g., "requirements.txt")
  final String? content;       // Decrypted text content (null in list view, populated in viewer)
  final DateTime createdAt;
}
```

### DocumentProvider Access Pattern
```dart
// Source: frontend/lib/screens/documents/document_viewer_screen.dart
Consumer<DocumentProvider>(
  builder: (context, provider, child) {
    final doc = provider.selectedDocument;  // Full document with content
    // doc.filename = "requirements.txt"
    // doc.content = "Full text content..."
  },
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| dart:html for web download | file_saver package | 2023+ | dart:html deprecated; file_saver is cross-platform |
| Separate download per platform | Unified file_saver API | 2022+ | Single code path for web/Android/iOS |

**Deprecated/outdated:**
- `dart:html`: Deprecated per Flutter web evolution. Use `web` package or `file_saver`.

## Open Questions

Things that couldn't be fully resolved:

1. **Download from list without content**
   - What we know: Document list only has metadata; content requires API call
   - What's unclear: Should we fetch content first or accept this limitation?
   - Recommendation: For v1.9.3, require user to open document viewer first, then download. Future enhancement could add direct download with content fetch.

## Sources

### Primary (HIGH confidence)
- `frontend/lib/services/artifact_service.dart` - file_saver usage pattern (lines 97-104)
- `frontend/lib/screens/conversation/widgets/artifact_card.dart` - snackbar patterns (lines 212-229)
- `frontend/lib/screens/documents/document_viewer_screen.dart` - AppBar structure (lines 37-46)
- `frontend/lib/screens/documents/document_list_screen.dart` - context menu structure (lines 114-150)
- `frontend/lib/models/document.dart` - document model with filename/content
- `frontend/pubspec.yaml` - file_saver 0.2.14 already installed

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY_v1.9.3.md` - v1.9.3 milestone research confirming file_saver approach

### Tertiary (LOW confidence)
- None - all findings verified against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - file_saver already in pubspec and proven in artifact export
- Architecture: HIGH - verified against actual codebase files
- Pitfalls: HIGH - based on v1.9.3 research and codebase patterns

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - stable pattern, no expected changes)

---

## Implementation Checklist

Pre-verified implementation steps based on research:

### DocumentViewerScreen Changes
- [ ] Add `import 'dart:convert';`
- [ ] Add `import 'dart:typed_data';`
- [ ] Add `import 'package:file_saver/file_saver.dart';`
- [ ] Add `_downloadDocument(Document doc)` method
- [ ] Add download IconButton to AppBar actions
- [ ] Show success snackbar "Downloaded {filename}"
- [ ] Handle errors with error snackbar

### DocumentListScreen Changes
- [ ] Add same imports
- [ ] Add download menu item to PopupMenuButton
- [ ] Note: Document in list has `content: null`, need to fetch first
- [ ] Option A: Navigate to viewer, tell user to download there
- [ ] Option B: Fetch content then download (adds complexity)

### File Extension Handling
```dart
// Parse filename for file_saver
final filename = doc.filename;  // e.g., "requirements.txt"
final extension = filename.contains('.')
    ? filename.split('.').last
    : 'txt';  // Default to txt
final nameWithoutExt = filename.replaceAll(RegExp(r'\.[^.]+$'), '');
```

### Complete Download Method Template
```dart
Future<void> _downloadDocument(Document doc) async {
  if (doc.content == null) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Document content not loaded')),
    );
    return;
  }

  try {
    final bytes = Uint8List.fromList(utf8.encode(doc.content!));
    final extension = doc.filename.contains('.')
        ? doc.filename.split('.').last
        : 'txt';
    final nameWithoutExt = doc.filename.replaceAll(RegExp(r'\.[^.]+$'), '');

    await FileSaver.instance.saveFile(
      name: nameWithoutExt,
      bytes: bytes,
      ext: extension,
      mimeType: MimeType.text,
    );

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Downloaded ${doc.filename}'),
          action: SnackBarAction(label: 'OK', onPressed: () {}),
        ),
      );
    }
  } catch (e) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }
}
```
