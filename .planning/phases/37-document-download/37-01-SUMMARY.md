---
phase: 37-document-download
plan: 01
subsystem: frontend-documents
tags: [file-saver, download, document-viewer, document-list]

dependency-graph:
  requires: []
  provides:
    - Document download from viewer screen
    - Document download from list context menu
  affects:
    - Phase 38 document preview (may want similar pattern)

tech-stack:
  added: []
  patterns:
    - file_saver for cross-platform downloads
    - Consumer wrapping Scaffold for AppBar access
    - Fetch-then-download for list items without content

key-files:
  created: []
  modified:
    - frontend/lib/screens/documents/document_viewer_screen.dart
    - frontend/lib/screens/documents/document_list_screen.dart

decisions:
  - id: DOWNLOAD-PATTERN
    choice: Screen-level download (no service)
    reason: Simple 10-line operation; service would be over-engineering
  - id: LIST-DOWNLOAD
    choice: Fetch content first then download
    reason: Documents in list don't have content loaded; fetching is required

metrics:
  duration: ~8 minutes
  completed: 2026-02-04
---

# Phase 37 Plan 01: Document Download Summary

**One-liner:** Download buttons using file_saver in DocumentViewerScreen AppBar and DocumentListScreen context menu

## What Was Built

### Task 1: DocumentViewerScreen Download Button
Added download capability to the document viewer screen:
- Download IconButton in AppBar (only shown when content is loaded)
- `_downloadDocument()` method with proper filename parsing
- Success snackbar "Downloaded {filename}" after download
- Error snackbar on failure

### Task 2: DocumentListScreen Download Menu Option
Added download option to document list context menu:
- Download menu item between View and Delete options
- `_downloadDocument()` method that fetches content first
- "Preparing download..." snackbar with spinner during content fetch
- Clears selected document after download completes

## Key Technical Details

### File Extension Handling
```dart
final extension = doc.filename.contains('.')
    ? doc.filename.split('.').last
    : 'txt';
final nameWithoutExt = doc.filename.replaceAll(RegExp(r'\.[^.]+$'), '');
```

### Consumer Pattern for AppBar
Wrapped entire Scaffold in Consumer to access DocumentProvider in both AppBar and body:
```dart
return Consumer<DocumentProvider>(
  builder: (context, provider, child) {
    return Scaffold(
      appBar: AppBar(
        title: Text(provider.selectedDocument?.filename ?? 'Loading...'),
        actions: [
          if (provider.selectedDocument != null &&
              provider.selectedDocument!.content != null)
            IconButton(...),
        ],
      ),
      body: _buildBody(context, provider),
    );
  },
);
```

### List Download Flow
Documents in the list don't have content loaded, so download requires:
1. Show "Preparing download..." snackbar with spinner
2. Call `provider.selectDocument(doc.id)` to fetch content
3. Download file with fetched content
4. Clear selected document after download
5. Show success snackbar

## Requirements Verified

| Requirement | Status | Verification |
|-------------|--------|--------------|
| DOWNLOAD-01 | Done | Download icon visible in Document Viewer AppBar |
| DOWNLOAD-02 | Done | Download option in document list context menu |
| DOWNLOAD-03 | Done | File downloads with original filename |
| DOWNLOAD-04 | Done | Snackbar shows "Downloaded {filename}" |
| DOWNLOAD-05 | Done | file_saver package handles web/Android/iOS |

## Commits

| Hash | Description |
|------|-------------|
| 4b70224 | feat(37-01): add download button to DocumentViewerScreen |
| 258c117 | feat(37-01): add download option to DocumentListScreen context menu |

## Deviations from Plan

None - plan executed exactly as written.

## Files Modified

- `frontend/lib/screens/documents/document_viewer_screen.dart`
  - Added imports: dart:convert, dart:typed_data, file_saver, Document model
  - Added `_downloadDocument()` method
  - Wrapped Scaffold in Consumer for AppBar access
  - Added download IconButton in AppBar actions

- `frontend/lib/screens/documents/document_list_screen.dart`
  - Added imports: dart:convert, dart:typed_data, file_saver
  - Added `_downloadDocument()` method with content fetching
  - Added Download menu option to PopupMenuButton
  - Added download handler in onSelected

## Next Phase Readiness

Phase 37 is complete with 1 plan (this one). Ready to proceed to Phase 38 (Document Preview).
