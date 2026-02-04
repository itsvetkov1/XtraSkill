---
phase: 38-document-preview
plan: 01
subsystem: frontend-documents
tags: [preview-dialog, file-picker, upload-flow, utf8-decode]

dependency-graph:
  requires:
    - Phase 37 Document Download (established file handling patterns)
  provides:
    - Document preview confirmation before upload
    - DocumentPreviewDialog reusable widget
  affects:
    - Phase 39 breadcrumb navigation (may need to consider dialog states)

tech-stack:
  added: []
  patterns:
    - Static show() method for dialogs (from ModeChangeDialog)
    - utf8.decode with allowMalformed for safe text preview
    - ConstrainedBox for scrollable content areas in dialogs

key-files:
  created:
    - frontend/lib/widgets/document_preview_dialog.dart
  modified:
    - frontend/lib/screens/documents/document_upload_screen.dart

decisions:
  - id: PREVIEW-PATTERN
    choice: Static show() method returning Future<bool>
    reason: Consistent with ModeChangeDialog pattern; simplifies caller code
  - id: LINE-LIMIT
    choice: First 20 lines with truncation indicator
    reason: Prevents UI lag on large files; meets requirements
  - id: MONOSPACE-FONT
    choice: fontFamily: 'monospace' with fontSize: 14
    reason: Consistent with DocumentViewerScreen styling

metrics:
  duration: ~6 minutes
  completed: 2026-02-04
---

# Phase 38 Plan 01: Document Preview Summary

**One-liner:** Preview confirmation dialog with filename, size, and first 20 lines in monospace before upload proceeds

## What Was Built

### Task 1: DocumentPreviewDialog Widget
Created new reusable dialog widget at `frontend/lib/widgets/document_preview_dialog.dart`:
- Static `show()` method returning `Future<bool>` for easy calling
- Displays filename in title (truncated to 40 chars with extension preserved)
- Shows file size in human-readable format (B/KB/MB)
- Renders first 20 lines of content with truncation indicator
- Monospace font (fontFamily: 'monospace', fontSize: 14)
- Cancel returns false, Upload returns true
- barrierDismissible: false to require explicit action

### Task 2: Upload Flow Integration
Modified `_pickAndUploadFile()` in DocumentUploadScreen:
- Added import for DocumentPreviewDialog
- Inserted preview dialog call after size validation, before upload
- Proper mounted check before showing dialog
- Returns early if user cancels (shouldUpload == false)
- Upload proceeds normally if user confirms

## Key Technical Details

### UTF-8 Safe Decoding
```dart
final content = utf8.decode(bytes, allowMalformed: true);
```
Handles invalid byte sequences by replacing with replacement character instead of throwing.

### Preview Content Extraction
```dart
String _getPreviewContent(List<int> bytes, {int maxLines = 20}) {
  if (bytes.isEmpty) return '(Empty file)';
  final content = utf8.decode(bytes, allowMalformed: true);
  final lines = content.split('\n');
  final previewLines = lines.take(maxLines);
  if (lines.length > maxLines) {
    return '${previewLines.join('\n')}\n\n... (${lines.length - maxLines} more lines)';
  }
  return previewLines.join('\n');
}
```

### Filename Truncation
```dart
if (displayName.length > 40) {
  final extension = displayName.contains('.')
      ? '.${displayName.split('.').last}'
      : '';
  final nameWithoutExt = displayName.substring(0, displayName.length - extension.length);
  displayName = '${nameWithoutExt.substring(0, 40 - extension.length - 3)}...$extension';
}
```
Preserves file extension when truncating long filenames.

## Requirements Verified

| Requirement | Status | Verification |
|-------------|--------|--------------|
| DOC-01 | Done | Preview dialog shows filename in title |
| DOC-02 | Done | Preview dialog shows file size (human readable KB/MB) |
| DOC-03 | Done | Preview dialog shows first 20 lines of content |
| DOC-04 | Done | Preview uses monospace font (fontFamily: 'monospace') |
| DOC-05 | Done | Cancel button clears selection (returns false, method returns) |
| DOC-06 | Done | Upload button proceeds (returns true, upload continues) |

## Commits

| Hash | Description |
|------|-------------|
| c3ef442 | feat(38-01): add document preview dialog before upload |

## Deviations from Plan

None - plan executed exactly as written.

## Files Changed

- `frontend/lib/widgets/document_preview_dialog.dart` (NEW)
  - 122 lines
  - DocumentPreviewDialog StatelessWidget
  - Static show() method
  - _formatFileSize() helper
  - _getPreviewContent() helper

- `frontend/lib/screens/documents/document_upload_screen.dart`
  - Added import for DocumentPreviewDialog
  - Added 4 lines for preview dialog call after size validation

## Next Phase Readiness

Phase 38 is complete with 1 plan (this one). Ready to proceed to Phase 39 (Breadcrumb Navigation).
