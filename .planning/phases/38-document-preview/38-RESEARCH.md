# Phase 38: Document Preview - Research

**Researched:** 2026-02-04
**Domain:** Flutter dialog UI, file_picker integration, UTF-8 text handling
**Confidence:** HIGH

## Summary

Phase 38 implements a document preview dialog that appears after file selection but before upload. This is a well-established UX pattern that reduces user errors by letting them verify file selection before committing to an upload. The implementation is straightforward: intercept the existing upload flow after `FilePicker.platform.pickFiles()` returns, display a confirmation dialog with file metadata and content preview, then either proceed to upload or allow the user to cancel.

The codebase already has all required infrastructure. `DocumentUploadScreen` captures `file.bytes` and `file.name` immediately after selection. The viewer screen already uses monospace font styling that should be matched. Three existing dialog patterns (`DeleteConfirmationDialog`, `ProjectPickerDialog`, `ModeChangeDialog`) provide templates for consistent styling and structure.

**Primary recommendation:** Create a new `DocumentPreviewDialog` widget that receives `PlatformFile` as input, shows filename/size/content preview, and returns a boolean indicating whether to proceed with upload.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| file_picker | 10.3.8 | File selection | Already used; provides bytes, name, size |
| flutter (material) | SDK | Dialog UI | AlertDialog/Dialog for consistent Material look |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dart:convert | SDK | UTF-8 decoding | Convert bytes to text for preview |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AlertDialog | Dialog with custom layout | More flexibility but AlertDialog sufficient for simple confirmation |
| Stateless widget | Stateful widget | No state needed - preview content is derived directly from input |

**Installation:**
```bash
# No new packages needed - all dependencies already present
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/lib/widgets/
├── document_preview_dialog.dart  # NEW - preview confirmation dialog
```

### Pattern 1: Confirmation Dialog After File Selection

**What:** Intercept upload flow after file selection, show preview, proceed only on confirmation
**When to use:** When user needs to verify selection before a destructive/irreversible action
**Example:**
```dart
// In DocumentUploadScreen._pickAndUploadFile():
// BEFORE: immediate upload after validation
// AFTER: show preview dialog, then upload on confirmation

FilePickerResult? result = await FilePicker.platform.pickFiles(...);
if (result == null) return;

final file = result.files.single;

// Existing validation (size check)
if (file.bytes!.length > _maxFileSizeBytes) {
  _showFileSizeError(file.bytes!.length);
  return;
}

// NEW: Preview confirmation
final shouldUpload = await showDialog<bool>(
  context: context,
  barrierDismissible: false,
  builder: (context) => DocumentPreviewDialog(file: file),
);

if (shouldUpload != true) return;

// Existing upload logic continues
```

### Pattern 2: Static Show Method for Dialogs

**What:** Provide a static `show()` method that handles showDialog boilerplate
**When to use:** When dialog is used from multiple places or to simplify calling code
**Example (from ModeChangeDialog):**
```dart
class DocumentPreviewDialog extends StatelessWidget {
  final PlatformFile file;

  const DocumentPreviewDialog({super.key, required this.file});

  /// Show preview dialog, returns true if user confirms upload
  static Future<bool> show(BuildContext context, PlatformFile file) async {
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => DocumentPreviewDialog(file: file),
    );
    return result ?? false;
  }

  // ... build method
}
```

### Pattern 3: Monospace Font for Code/Text Content

**What:** Use `fontFamily: 'monospace'` for code-like content
**When to use:** Document viewers, code blocks, logs
**Example (from DocumentViewerScreen):**
```dart
SelectableText(
  content,
  style: const TextStyle(
    fontFamily: 'monospace',
    fontSize: 14,
    height: 1.5,
  ),
)
```

### Anti-Patterns to Avoid
- **Stateful dialog when not needed:** Preview content is computed once from input; no need for StatefulWidget
- **Full-screen preview:** Overkill for quick confirmation; AlertDialog/Dialog is sufficient
- **Auto-upload without preview:** Violates user control principle; research explicitly marks this as anti-feature

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File size formatting | Custom formatter | Copy `_formatFileSize()` from upload screen | Already implemented, handles B/KB/MB |
| UTF-8 decoding | Manual byte conversion | `utf8.decode(bytes, allowMalformed: true)` | Handles encoding errors gracefully |
| Dialog styling | Custom dialog from scratch | AlertDialog or Dialog with ConstrainedBox | Material 3 consistency |

**Key insight:** The upload screen already has a `_formatFileSize()` helper. Extract it to a utility function or duplicate in dialog (small function, duplication acceptable).

## Common Pitfalls

### Pitfall 1: UTF-8 Decode Failures (PITFALL-04)
**What goes wrong:** `utf8.decode()` throws on invalid byte sequences
**Why it happens:** Files may have non-UTF-8 encoding or binary content despite .txt/.md extension
**How to avoid:** Use `utf8.decode(bytes, allowMalformed: true)` to replace invalid sequences with replacement character
**Warning signs:** Unhandled FormatException when loading certain files

### Pitfall 2: Context Lost After Async Gap (PITFALL-09)
**What goes wrong:** `context` becomes invalid after `await` in `_pickAndUploadFile()`
**Why it happens:** User might navigate away or dialog might be dismissed during file picker
**How to avoid:**
1. Capture provider reference BEFORE `await FilePicker.platform.pickFiles()`
2. Check `mounted` after any async operation before using context
**Warning signs:** `setState() called after dispose()` error

### Pitfall 3: Preview Content Too Large
**What goes wrong:** Large file (near 1MB limit) causes UI lag when rendering all content
**Why it happens:** Rendering 1MB of text is expensive
**How to avoid:** Limit preview to first 20 lines as specified in requirements
**Warning signs:** Jank when opening preview for large files

### Pitfall 4: Empty File Handling
**What goes wrong:** Division by zero or empty content display
**Why it happens:** User selects an empty .txt file
**How to avoid:** Check for empty bytes before processing; show "Empty file" message
**Warning signs:** Blank preview with no indication why

### Pitfall 5: barrierDismissible: true
**What goes wrong:** User accidentally dismisses preview by tapping outside
**Why it happens:** Default AlertDialog behavior allows dismissal
**How to avoid:** Set `barrierDismissible: false` to require explicit Cancel/Upload action
**Warning signs:** Files unexpectedly not uploading when user thought they confirmed

## Code Examples

Verified patterns from official sources and existing codebase:

### File Size Formatting (From DocumentUploadScreen)
```dart
// Source: frontend/lib/screens/documents/document_upload_screen.dart
String _formatFileSize(int bytes) {
  if (bytes < 1024) {
    return '$bytes B';
  } else if (bytes < 1024 * 1024) {
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  } else {
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
```

### Safe UTF-8 Decoding with Line Extraction
```dart
// Source: Derived from dart:convert documentation
import 'dart:convert';

String _getPreviewContent(List<int> bytes, {int maxLines = 20}) {
  if (bytes.isEmpty) return '(Empty file)';

  try {
    final content = utf8.decode(bytes, allowMalformed: true);
    final lines = content.split('\n');
    final previewLines = lines.take(maxLines);

    if (lines.length > maxLines) {
      return '${previewLines.join('\n')}\n\n... (${lines.length - maxLines} more lines)';
    }
    return previewLines.join('\n');
  } catch (e) {
    return '(Unable to preview file content)';
  }
}
```

### Dialog Structure (From Existing Codebase Pattern)
```dart
// Source: Pattern from delete_confirmation_dialog.dart, mode_change_dialog.dart
Future<bool?> showDialog<bool>(
  context: context,
  barrierDismissible: false,  // CRITICAL: prevent accidental dismissal
  builder: (BuildContext dialogContext) {
    return AlertDialog(
      title: Text('Preview: ${file.name}'),
      content: Column(
        mainAxisSize: MainAxisSize.min,  // Don't force full height
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Metadata row
          Text('Size: ${_formatFileSize(bytes.length)}'),
          const Divider(),
          // Preview content with scroll
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 300),
            child: SingleChildScrollView(
              child: Text(
                previewContent,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 14,
                ),
              ),
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(dialogContext).pop(false),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(dialogContext).pop(true),
          child: const Text('Upload'),
        ),
      ],
    );
  },
);
```

### Provider Reference Capture (From DocumentUploadScreen)
```dart
// Source: frontend/lib/screens/documents/document_upload_screen.dart
Future<void> _pickAndUploadFile() async {
  // Get provider reference BEFORE async gap
  final provider = context.read<DocumentProvider>();

  FilePickerResult? result = await FilePicker.platform.pickFiles(...);
  if (result == null) return;

  // ... rest of method uses `provider` not `context.read<>`
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Auto-upload on selection | Preview before upload | Industry standard | Error prevention |
| AlertDialog.icon | Icon in title Row | Material 3 | Consistent styling |
| TextButton for primary action | FilledButton for primary | Material 3 | Visual hierarchy |

**Deprecated/outdated:**
- `AlertDialog.content` with just Text: Use Column for complex content
- `Navigator.of(context).pop()` in same method as `showDialog`: Capture dialogContext from builder

## Open Questions

Things that couldn't be fully resolved:

1. **Line count display location**
   - What we know: Requirements say first 20 lines, research suggests showing total line count
   - What's unclear: Whether to show "X lines total" or just truncation indicator
   - Recommendation: Show truncation indicator only: "... (X more lines)" - simpler, meets requirements

2. **Preview dialog width on desktop**
   - What we know: Other dialogs use `ConstrainedBox(maxWidth: 400, maxHeight: 500)`
   - What's unclear: Is 400px wide enough for 80-character lines with monospace font?
   - Recommendation: Use 500px width to accommodate typical code/text widths

## Sources

### Primary (HIGH confidence)
- `frontend/lib/screens/documents/document_upload_screen.dart` - current upload flow
- `frontend/lib/screens/documents/document_viewer_screen.dart` - monospace styling pattern
- `frontend/lib/widgets/mode_change_dialog.dart` - dialog structure pattern
- `frontend/lib/widgets/delete_confirmation_dialog.dart` - confirmation dialog pattern
- `.planning/research/SUMMARY_v1.9.3.md` - prior research synthesis

### Secondary (MEDIUM confidence)
- Dart utf8 codec documentation - allowMalformed parameter

### Tertiary (LOW confidence)
- None - all patterns verified from codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all packages already in use, verified in pubspec.yaml
- Architecture: HIGH - patterns copied from existing codebase dialogs
- Pitfalls: HIGH - PITFALL-04, PITFALL-09 documented in prior research; others derived from implementation review

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (stable patterns, 30-day validity)
