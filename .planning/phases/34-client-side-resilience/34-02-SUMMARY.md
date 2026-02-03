---
phase: 34-client-side-resilience
plan: 02
subsystem: frontend
tags: [file-validation, upload, ux, pitfall-prevention]

dependency_graph:
  requires:
    - PITFALLS-v1.9.2.md (PITFALL-09 guidance)
  provides:
    - Client-side file size validation before upload
    - Prominent size limit display
    - User-friendly error dialog with retry option
  affects:
    - Document upload UX
    - File validation flow

tech_stack:
  added: []
  patterns:
    - Validate immediately after picker returns
    - Error dialog with action button for retry
    - Theme-aware visual emphasis

key_files:
  created: []
  modified:
    - frontend/lib/screens/documents/document_upload_screen.dart

decisions:
  - id: D-34-02-01
    decision: Validate file size BEFORE setState(_uploading = true)
    rationale: PITFALL-09 - user should see error before any upload UI
  - id: D-34-02-02
    decision: Use AlertDialog instead of SnackBar for size error
    rationale: Dialog allows "Select Different File" action button
  - id: D-34-02-03
    decision: Get provider reference before async file picker call
    rationale: Avoid use_build_context_synchronously lint warning

metrics:
  duration: ~3 minutes
  completed: 2026-02-03
---

# Phase 34 Plan 02: File Size Validation Summary

Implemented client-side file size validation that runs immediately after file selection.

## One-liner

Client-side 1MB file size validation with human-readable error showing actual vs limit, plus retry button.

## Tasks Completed

| Task | Name | Commit | Result |
|------|------|--------|--------|
| 1 | Add client-side file size validation | 3749837 | Validation before upload UI, error dialog with retry |
| 2 | Update hint text to prominently show size limit | 1b6e356 | Container with info icon, theme-aware styling |

## Changes Made

### frontend/lib/screens/documents/document_upload_screen.dart (Modified)

**New constants and helpers:**
- `_maxFileSizeBytes = 1024 * 1024` (1MB constant)
- `_formatFileSize(int bytes)` - formats bytes to "2.4 MB" style

**Validation flow (PITFALL-09 prevention):**
```dart
// After picker returns, BEFORE setState:
final fileSize = file.bytes!.length;
if (fileSize > _maxFileSizeBytes) {
  if (mounted) {
    _showFileSizeError(fileSize);
  }
  return;  // Stop - user can select another file
}
```

**Error dialog with retry:**
```dart
void _showFileSizeError(int actualSize) {
  showDialog<void>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      icon: Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 48),
      title: Text('File too large'),
      content: Text(
        'The selected file is ${_formatFileSize(actualSize)}.\n\n'
        'Maximum file size is 1MB.\n\n'
        'Please select a smaller file.',
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(dialogContext), child: Text('Cancel')),
        FilledButton(
          onPressed: () {
            Navigator.pop(dialogContext);
            _pickAndUploadFile();  // Immediate retry
          },
          child: Text('Select Different File'),
        ),
      ],
    ),
  );
}
```

**Prominent size limit display:**
- Separate file type hint from size limit
- Container with background color and icon
- Theme-aware colors: `surfaceContainerHighest`, `primary`, `onSurfaceVariant`
- Font weight emphasis: `FontWeight.w500`

## Verification Results

| Check | Result |
|-------|--------|
| Flutter analyze | No issues on modified file |
| Validation timing | BEFORE setState (line 87-93 before line 97) |
| Error message content | Shows actual size (e.g., "2.4 MB") and limit ("1MB") |
| Retry capability | FilledButton opens file picker directly |
| Size limit visibility | Container with info icon, themed styling |

## Requirements Coverage

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| FILE-01: File size validated client-side before upload | Validation at line 87-93, before upload UI | COMPLETE |
| FILE-02: Clear error message with actual size | Dialog shows "2.4 MB" vs "1MB" limit | COMPLETE |
| FILE-03: User can immediately try again | "Select Different File" button in dialog | COMPLETE |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed use_build_context_synchronously lint warning**

- **Found during:** Task 1
- **Issue:** `context.read<DocumentProvider>()` used after async gap (FilePicker.platform.pickFiles)
- **Fix:** Moved provider reference acquisition BEFORE the async call
- **Files modified:** frontend/lib/screens/documents/document_upload_screen.dart
- **Commit:** 3749837

## Success Criteria Status

| Criterion | Status |
|-----------|--------|
| File size validation happens IMMEDIATELY after pickFiles() | PASS |
| Validation happens BEFORE setState({_uploading = true}) | PASS |
| Error message includes actual file size (e.g., "2.4 MB") | PASS |
| Error message includes limit ("Maximum file size is 1MB") | PASS |
| User can select different file directly from error dialog | PASS |
| Size limit prominently displayed before file picker opens | PASS |

## Plan 34-02 Complete

This plan addresses PITFALL-09 from the v1.9.2 research - validating file size before upload UI appears. Users now see immediate feedback when selecting oversized files and can retry without navigation.
