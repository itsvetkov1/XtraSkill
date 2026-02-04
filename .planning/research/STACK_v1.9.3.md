# Technology Stack: v1.9.3 Features

**Project:** BA Assistant - Document Preview, Download, and Breadcrumb Enhancement
**Researched:** 2026-02-04
**Scope:** Targeted research for three specific features

---

## Executive Summary

All three features can be implemented with **zero new dependencies**. The existing stack already provides everything needed:

| Feature | Solution | New Packages |
|---------|----------|--------------|
| Document Preview | `file_picker` PlatformFile properties | None |
| Document Download | `file_saver` (already installed) | None |
| Enhanced Breadcrumbs | `go_router` GoRouterState + Provider | None |

---

## Feature 1: Document Preview Before Upload

### Current State

The upload flow (`document_upload_screen.dart`) already uses `file_picker` and receives a `PlatformFile` with:
- `name` - filename
- `bytes` - full file content (Uint8List)
- `size` - file size in bytes
- `extension` - file extension

### Recommendation: Use Existing `file_picker` Properties

**No new packages needed.**

| Data Point | Source | Implementation |
|------------|--------|----------------|
| Filename | `PlatformFile.name` | Already used |
| File size | `PlatformFile.size` | Already used for validation |
| First N lines | `PlatformFile.bytes` | Decode bytes, split by newline, take first 5-10 lines |

### Implementation Pattern

```dart
// After picking file, before upload:
final file = result.files.single;
final previewData = _buildPreview(file);

class FilePreview {
  final String filename;
  final int sizeBytes;
  final String formattedSize;
  final List<String> firstLines;
  final int totalLines;
}

FilePreview _buildPreview(PlatformFile file) {
  final content = utf8.decode(file.bytes!);
  final lines = content.split('\n');
  return FilePreview(
    filename: file.name,
    sizeBytes: file.size,
    formattedSize: _formatFileSize(file.size), // Already exists in codebase
    firstLines: lines.take(5).toList(),
    totalLines: lines.length,
  );
}
```

### What NOT to Use

| Anti-pattern | Why Avoid |
|--------------|-----------|
| Additional file reading packages | `file_picker` already provides bytes |
| Streaming/chunked reading | Unnecessary for 1MB max text files |
| Platform-specific file access | `file_picker` abstracts this already |

**Confidence:** HIGH (verified file_picker 10.3.10 docs, existing code uses these properties)

---

## Feature 2: Document Download

### Current State

- `file_saver: ^0.2.14` already installed (added in phase 36 for artifact export)
- `artifact_service.dart` demonstrates working pattern
- Documents are text-only, stored encrypted in backend
- Backend already has `GET /api/documents/:id` returning content

### Recommendation: Reuse `file_saver` Pattern from Artifacts

**No new packages needed.**

| Component | Approach |
|-----------|----------|
| Get content | Already exists via `DocumentService.getDocumentContent()` |
| Trigger download | Use `FileSaver.instance.saveFile()` like artifact_service |
| MIME type | `MimeType.text` for .txt, `MimeType.text` for .md |

### Implementation Pattern

```dart
// In document_service.dart or new download helper:
import 'package:file_saver/file_saver.dart';

Future<String> downloadDocument(Document doc) async {
  // Content already loaded via selectDocument()
  final bytes = utf8.encode(doc.content!);

  await FileSaver.instance.saveFile(
    name: doc.filename.replaceAll(RegExp(r'\.[^.]+$'), ''), // Remove extension
    bytes: Uint8List.fromList(bytes),
    ext: doc.filename.split('.').last, // 'txt' or 'md'
    mimeType: MimeType.text,
  );

  return doc.filename;
}
```

### Download Triggers

Two locations need download buttons:

1. **Document Viewer Screen** - AppBar action button
2. **Document List Screen** - PopupMenu item (alongside View/Delete)

### Cross-Platform Behavior

`file_saver` handles platform differences automatically:

| Platform | Behavior |
|----------|----------|
| Web | Browser download dialog |
| Android | Downloads folder (with permission) |
| iOS | Share sheet or Files app |
| Windows/macOS/Linux | Save dialog |

### What NOT to Use

| Anti-pattern | Why Avoid |
|--------------|-----------|
| `dart:html` for web downloads | Deprecated; not cross-platform |
| `url_launcher` with blob URLs | Complex, platform-specific |
| New download packages | `file_saver` already handles all platforms |
| Backend streaming endpoint | Overkill for 1MB text files |

**Confidence:** HIGH (verified file_saver 0.3.1 docs, working artifact_service pattern in codebase)

---

## Feature 3: Enhanced Breadcrumb Navigation

### Current State

`breadcrumb_bar.dart` already provides:
- Route-based breadcrumb generation
- Clickable segments with `context.go(route)`
- Project and Thread name resolution via providers
- Truncation for narrow screens

Currently missing:
- Document-level breadcrumbs (stops at Project)
- Document viewer integration

### Recommendation: Extend Existing Pattern

**No new packages needed.**

| Enhancement | Approach |
|-------------|----------|
| Document segment | Add case for `/documents/:docId` route pattern |
| Document name | Fetch from `DocumentProvider.selectedDocument` |
| Thread breadcrumb refinement | Already works, may need provider timing fix |

### Route Hierarchy for Documents

Current routes don't include a document viewer route in go_router. Two options:

**Option A: Add nested route (Recommended)**
```
/projects/:id/documents/:docId -> "Projects > Project Name > Documents > filename.txt"
```

**Option B: Keep modal/push navigation**
```
Documents accessible via Navigator.push (current)
Breadcrumbs show "Projects > Project Name" only
```

Recommendation: **Option A** for consistency with thread navigation pattern.

### Implementation Pattern

```dart
// In _buildBreadcrumbs():
if (segments.length >= 4 && segments[2] == 'documents') {
  final projectId = segments[1];
  final docId = segments[3];

  breadcrumbs.add(const Breadcrumb('Projects', '/projects'));
  breadcrumbs.add(Breadcrumb(projectName, '/projects/$projectId'));
  breadcrumbs.add(Breadcrumb('Documents', '/projects/$projectId')); // Tab hint

  final docProvider = context.read<DocumentProvider>();
  final docName = docProvider.selectedDocument?.filename ?? 'Document';
  breadcrumbs.add(Breadcrumb(docName)); // Current page, no link
}
```

### Provider Coordination

Document name resolution requires `DocumentProvider.selectedDocument` to be populated. The current viewer screen already calls `selectDocument()` in `initState`, so the name should be available after first frame.

If timing issues occur (name shows as "Document" briefly), use:
```dart
// In breadcrumb_bar.dart
Consumer<DocumentProvider>(
  builder: (context, docProvider, child) {
    // Rebuild when document loads
  },
)
```

### What NOT to Use

| Anti-pattern | Why Avoid |
|--------------|-----------|
| `flutter_breadcrumb` package | Unnecessary, custom solution already works |
| Complex state management (Bloc) | Provider pattern already established |
| Passing document name via route params | Bloats URL, provider pattern cleaner |

**Confidence:** HIGH (verified go_router 17.0.1 GoRouterState API, existing breadcrumb pattern)

---

## Stack Summary

### No New Dependencies

```yaml
# pubspec.yaml - NO CHANGES NEEDED

# Existing relevant dependencies:
dependencies:
  file_picker: ^10.3.8    # Preview: already provides bytes, size, name
  file_saver: ^0.2.14     # Download: already installed for artifacts
  go_router: ^17.0.1      # Breadcrumbs: GoRouterState.of(context)
  provider: ^6.1.5+1      # State: DocumentProvider, ProjectProvider
```

### Version Notes

| Package | Installed | Latest | Action |
|---------|-----------|--------|--------|
| file_picker | 10.3.8 | 10.3.10 | Optional bump (minor fixes) |
| file_saver | 0.2.14 | 0.3.1 | Optional bump (minor improvements) |
| go_router | 17.0.1 | 17.1.0 | Optional bump (minor fixes) |

None of these bumps are required for the features. The current versions are fully sufficient.

---

## Implementation Complexity

| Feature | Complexity | Rationale |
|---------|------------|-----------|
| Document Preview | Low | UI-only, data already available |
| Document Download | Low | Copy artifact_service pattern |
| Enhanced Breadcrumbs | Medium | Route changes needed, provider coordination |

### Suggested Phase Order

1. **Document Download** - Lowest risk, copy existing pattern
2. **Document Preview** - UI change, no backend work
3. **Breadcrumb Enhancement** - May need route refactoring

---

## Potential Pitfalls

### Pitfall 1: File Encoding Assumptions

**Risk:** Assuming all text files are UTF-8
**Mitigation:** Wrap decode in try/catch, show error for invalid encoding
```dart
try {
  final content = utf8.decode(file.bytes!);
} on FormatException {
  // Show error: "File encoding not supported"
}
```

### Pitfall 2: Document Not Loaded for Breadcrumb

**Risk:** Breadcrumb renders before `selectDocument()` completes
**Mitigation:** Use Consumer or listen to DocumentProvider changes

### Pitfall 3: Download on Web Without User Gesture

**Risk:** Browser blocks programmatic downloads without user interaction
**Mitigation:** Always trigger from button press (already the plan)

---

## Sources

- [file_picker pub.dev](https://pub.dev/packages/file_picker) - v10.3.10, PlatformFile properties verified
- [file_saver pub.dev](https://pub.dev/packages/file_saver) - v0.3.1, saveFile API verified
- [go_router pub.dev](https://pub.dev/packages/go_router) - v17.1.0, GoRouterState verified
- Existing codebase:
  - `frontend/lib/screens/documents/document_upload_screen.dart` - file_picker usage
  - `frontend/lib/services/artifact_service.dart` - file_saver pattern
  - `frontend/lib/widgets/breadcrumb_bar.dart` - current breadcrumb implementation

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Document Preview | HIGH | file_picker properties verified in docs and existing code |
| Document Download | HIGH | file_saver pattern already working in artifact_service |
| Breadcrumb Enhancement | HIGH | go_router API verified, existing pattern extensible |
| No New Dependencies | HIGH | All required functionality exists in current stack |

---

*Research complete. Ready for roadmap creation.*
