# Domain Pitfalls: v1.9.3 Document Preview/Download & Breadcrumb Navigation

**Domain:** Flutter cross-platform document handling and navigation
**Researched:** 2026-02-04
**Overall Confidence:** HIGH (verified against existing codebase + official docs)

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### PITFALL-01: Web Platform File Path Reliance

**What goes wrong:** Code assumes `PlatformFile.path` is available on all platforms. On Flutter Web, `path` is always `null` due to browser security restrictions - browsers don't expose filesystem paths to JavaScript/Dart.

**Why it happens:** Developers test on mobile/desktop first where `path` works, then deploy to web.

**Consequences:**
- Null pointer exceptions on web
- Feature completely broken for web users
- Code that worked in development fails in production

**Affected feature:** Document Preview Before Upload

**Warning signs:**
- Code uses `file.path` without platform check
- No `kIsWeb` conditional logic
- Tests only run on mobile/desktop emulators

**Prevention:**
```dart
// ALWAYS use bytes on web, path on mobile
if (kIsWeb) {
  final bytes = result.files.single.bytes; // Web: use bytes
} else {
  final path = result.files.single.path; // Mobile: can use path
}
```

**Detection:** Test on Chrome browser early in development cycle.

**Sources:**
- [file_picker GitHub FAQ](https://github.com/miguelpruivo/flutter_file_picker/wiki/FAQ)
- [Issue #443: Path is always null on Web](https://github.com/miguelpruivo/flutter_file_picker/issues/443)

---

### PITFALL-02: dart:html Deprecation for Web Downloads

**What goes wrong:** Using `dart:html` for file downloads (blob URLs, anchor elements) works today but is deprecated as of Dart 3.7. Future Flutter versions will break this code.

**Why it happens:** Most Stack Overflow answers and tutorials still reference `dart:html` approach.

**Consequences:**
- Code works now but will break in future Flutter upgrades
- Tech debt accumulation
- Forced migration under time pressure later

**Affected feature:** Document Download Functionality

**Warning signs:**
- `import 'dart:html'` in codebase
- Using `html.Blob`, `html.Url.createObjectUrlFromBlob`
- Using `html.AnchorElement` for downloads

**Prevention:** Use the `web` package instead of `dart:html`:
```dart
// OLD (deprecated)
import 'dart:html' as html;
final blob = html.Blob([bytes]);
final url = html.Url.createObjectUrlFromBlob(blob);

// NEW (web package)
import 'package:web/web.dart' as web;
final blob = web.Blob([bytes.toJS].toJS);
final url = web.URL.createObjectURL(blob);
```

Or use `universal_downloader` package which handles platform differences.

**Detection:** Run `grep -r "dart:html" lib/` to find deprecated imports.

**Sources:**
- [How To Download Files With The web Package In Flutter Apps](https://quickcoder.org/how-to-download-files-with-the-web-package-in-flutter-apps/)
- [universal_downloader package](https://pub.dev/packages/universal_downloader)

---

### PITFALL-03: GoRouter NavigatorObserver Not Tracking go() Calls

**What goes wrong:** Breadcrumb implementation using `NavigatorObserver` doesn't capture all navigation events. When using `context.go()`, the observer methods (`didPush`, `didPop`, etc.) are not called.

**Why it happens:** GoRouter's declarative navigation model differs from imperative Navigator. `go()` replaces the entire stack rather than pushing/popping.

**Consequences:**
- Breadcrumbs show stale data
- Navigation history incomplete
- Inconsistent UI state

**Affected feature:** Enhanced Breadcrumb Navigation

**Warning signs:**
- Using `NavigatorObserver.didPush` to track breadcrumbs
- Breadcrumbs don't update after `context.go()` calls
- Works with `push()` but not `go()`

**Prevention:**
The existing `BreadcrumbBar` implementation in this codebase correctly avoids this pitfall by:
1. Reading route directly from `GoRouterState.of(context).uri.path`
2. Rebuilding breadcrumbs from current path on each build
3. NOT relying on NavigatorObserver at all

Continue this pattern for enhanced breadcrumbs.

**Detection:** Test breadcrumb updates after `context.go('/new/path')` calls.

**Sources:**
- [Flutter Issue #142720: NavigatorObserver doesn't track go() changes](https://github.com/flutter/flutter/issues/142720)
- [Flutter Issue #114958: Same-level route transitions not tracked](https://github.com/flutter/flutter/issues/114958)

---

### PITFALL-04: UTF-8 Encoding Assumptions for Text Preview

**What goes wrong:** Code assumes all text files are valid UTF-8. When a file contains invalid UTF-8 sequences (Windows-1252, Latin-1, or corrupted data), `utf8.decode()` throws `FormatException`.

**Why it happens:** Most modern files are UTF-8, so the issue surfaces rarely - usually in production with user data.

**Consequences:**
- App crashes when previewing certain files
- Uncaught exception
- Poor user experience with no graceful fallback

**Affected feature:** Document Preview Before Upload

**Warning signs:**
- Using `utf8.decode(bytes)` without try-catch
- No `allowMalformed` parameter
- Preview crashes on "special" files

**Prevention:**
```dart
// SAFE: Handle malformed UTF-8 gracefully
String content;
try {
  content = utf8.decode(bytes);
} catch (e) {
  // Fallback: decode with replacement characters for invalid sequences
  content = utf8.decode(bytes, allowMalformed: true);
  // OR: Show warning to user that file may have encoding issues
}
```

**Detection:** Test with files saved in Windows Notepad with ANSI encoding (not UTF-8).

**Sources:**
- [Flutter Issue: Bad UTF-8 encoding](https://www.omi.me/blogs/flutter-errors/bad-utf-8-encoding-0x-at-offset-in-flutter-causes-and-how-to-fix)
- [Flutter/Dart UTF-8 encoding discussions](https://github.com/flutter/flutter/issues/113300)

---

## Moderate Pitfalls

Mistakes that cause delays or technical debt.

### PITFALL-05: Memory Issues with Large File Downloads

**What goes wrong:** Loading entire file content into `Uint8List` memory for download. For large files (>10MB), this can exhaust available memory and crash the app.

**Why it happens:** Simple download implementation loads everything into memory for convenience.

**Consequences:**
- App crashes on large files
- Memory pressure affects other parts of app
- Poor performance

**Affected feature:** Document Download Functionality

**Warning signs:**
- No file size limits on download
- Using `getData()` without `maxSize` parameter
- Full file content in memory during download

**Prevention:**
For this project (text files, 1MB limit already enforced), this is LOWER RISK. However:
1. Maintain the existing 1MB upload limit
2. For download, consider streaming if files could be larger
3. Add explicit size check before loading to memory

**Detection:** Test with files approaching size limit.

---

### PITFALL-06: Breadcrumb Overflow on Deep Navigation

**What goes wrong:** Breadcrumb trail becomes too long for screen width when navigating deeply nested routes (e.g., Projects > Project Name > Documents > Document Name > Section).

**Why it happens:** No truncation strategy for long breadcrumb chains.

**Consequences:**
- Breadcrumbs wrap awkwardly or overflow
- UI breaks on mobile
- Horizontal scroll may not be discoverable

**Affected feature:** Enhanced Breadcrumb Navigation

**Warning signs:**
- Fixed-width breadcrumb container
- No `maxVisible` parameter used
- Testing only with shallow navigation

**Prevention:**
The existing `BreadcrumbBar` has good foundations:
1. `maxVisible` parameter exists (use it!)
2. `_applyTruncation` method shows "..." for overflow
3. `SingleChildScrollView` allows horizontal scroll

Enhancement: Apply responsive truncation based on screen width:
```dart
// Narrow screens: show fewer breadcrumbs
final maxVisible = MediaQuery.of(context).size.width < 600 ? 2 : 4;
```

**Detection:** Test on mobile viewport with deep navigation path.

---

### PITFALL-07: Document Name Not in Breadcrumbs

**What goes wrong:** Current breadcrumb implementation handles projects and threads but not documents. When viewing a document, breadcrumb shows "Projects > Project Name" but not the document name.

**Why it happens:** Breadcrumb parsing logic doesn't have a case for document routes.

**Consequences:**
- User doesn't see current document in breadcrumb trail
- Inconsistent navigation experience
- "Where am I?" confusion

**Affected feature:** Enhanced Breadcrumb Navigation

**Warning signs (in current code):**
```dart
// Current code only handles:
// - /projects
// - /projects/:id
// - /projects/:id/threads/:threadId
// Missing: /projects/:id/documents/:docId
```

**Prevention:**
Add document route handling to `_buildBreadcrumbs`:
```dart
if (segments.length >= 4 && segments[2] == 'documents') {
  // Add document name breadcrumb
  final documentProvider = context.read<DocumentProvider>();
  final docName = documentProvider.selectedDocument?.filename ?? 'Document';
  breadcrumbs.add(Breadcrumb(docName));
}
```

**Detection:** Navigate to document viewer and check breadcrumb trail.

---

### PITFALL-08: Cancel Button Ambiguity on Web File Picker

**What goes wrong:** On web, `FilePicker.platform.pickFiles()` returns `null` both when user cancels AND in some error conditions. There's no way to distinguish cancellation from failure.

**Why it happens:** Browser APIs don't fire events when file picker is dismissed without selection.

**Consequences:**
- Can't show appropriate feedback (cancel vs error)
- User confusion if silent on cancel
- Logging/analytics inaccurate

**Affected feature:** Document Preview Before Upload

**Warning signs:**
- Treating all `null` results as "user cancelled"
- No error handling for picker failures
- Assuming picker always works

**Prevention:**
```dart
FilePickerResult? result;
try {
  result = await FilePicker.platform.pickFiles();
} catch (e) {
  // Actual error - show error message
  showErrorDialog('Failed to open file picker: $e');
  return;
}

if (result == null) {
  // User cancelled (or unknown web issue) - silent return is OK
  return;
}
```

**Detection:** Test file picker cancellation on both web and mobile.

**Sources:**
- [file_picker GitHub FAQ - Web limitations](https://github.com/miguelpruivo/flutter_file_picker/wiki/FAQ)

---

### PITFALL-09: Provider Context Lost After Async Gap

**What goes wrong:** Reading provider after `await` (async gap) when widget may have been disposed. Common pattern:
```dart
await FilePicker.platform.pickFiles();
context.read<Provider>().doSomething(); // Widget may be disposed!
```

**Why it happens:** User can navigate away while file picker is open.

**Consequences:**
- "Looking up a deactivated widget's ancestor is unsafe" error
- Crashes when user navigates during file selection

**Affected feature:** Document Preview Before Upload, Document Download

**Warning signs:**
- `context.read<Provider>()` after `await` without `mounted` check
- No provider reference captured before async operation

**Prevention:**
The existing `document_upload_screen.dart` correctly handles this:
```dart
// CORRECT: Capture provider BEFORE async gap
final provider = context.read<DocumentProvider>();

FilePickerResult? result = await FilePicker.platform.pickFiles();

// Now safe to use provider (captured reference, not context lookup)
await provider.uploadDocument(...);
```

Apply same pattern to any new preview/download code.

**Detection:** Navigate away while file picker is open, then return.

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

### PITFALL-10: Preview Dialog Size on Different Screens

**What goes wrong:** Preview dialog has fixed dimensions that work on desktop but are too large for mobile or too small for desktop.

**Why it happens:** Dialog size hardcoded without responsive consideration.

**Consequences:**
- Dialog clips on mobile
- Dialog wastes space on desktop
- Inconsistent experience

**Affected feature:** Document Preview Before Upload

**Prevention:**
```dart
showDialog(
  context: context,
  builder: (context) => Dialog(
    child: ConstrainedBox(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.9,
        maxHeight: MediaQuery.of(context).size.height * 0.8,
        minWidth: 300,
      ),
      child: PreviewContent(),
    ),
  ),
);
```

**Detection:** Test preview on mobile viewport.

---

### PITFALL-11: Missing Loading State During Preview Generation

**What goes wrong:** File is selected but preview takes time to generate (decoding, rendering). UI shows no feedback during this time.

**Why it happens:** Preview generation assumed to be instant.

**Consequences:**
- User thinks app is frozen
- Double-clicks causing issues
- Poor perceived performance

**Affected feature:** Document Preview Before Upload

**Prevention:**
```dart
// Show loading immediately after file selection
setState(() => _isLoadingPreview = true);

final content = await _decodeFileContent(bytes);

if (mounted) {
  setState(() => _isLoadingPreview = false);
  _showPreviewDialog(content);
}
```

**Detection:** Test with files that take >100ms to decode.

---

### PITFALL-12: Breadcrumb Click Target Too Small

**What goes wrong:** Clickable breadcrumb segments are difficult to tap on mobile due to small touch target.

**Why it happens:** Text-only buttons without sufficient padding.

**Consequences:**
- Frustrating mobile experience
- Users miss clicks
- Accessibility issues

**Affected feature:** Enhanced Breadcrumb Navigation

**Warning signs (current code has appropriate padding):**
```dart
// Current implementation has decent tap target
padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
```

But could be improved for touch:
```dart
// Better for touch: minimum 48px tap target
minimumSize: const Size(48, 48),
tapTargetSize: MaterialTapTargetSize.padded,
```

**Detection:** Test breadcrumb tapping on actual mobile device (not just emulator).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Document Preview | PITFALL-01 (web path null) | Use bytes property, test on Chrome |
| Document Preview | PITFALL-04 (UTF-8 encoding) | Use allowMalformed, add try-catch |
| Document Preview | PITFALL-09 (async context) | Capture provider before await |
| Document Download | PITFALL-02 (dart:html deprecated) | Use web package or universal_downloader |
| Document Download | PITFALL-05 (memory) | Maintain 1MB limit, check size |
| Breadcrumb Enhancement | PITFALL-03 (observer not tracking go()) | Use GoRouterState.of(context), not observer |
| Breadcrumb Enhancement | PITFALL-06 (overflow) | Use maxVisible with responsive values |
| Breadcrumb Enhancement | PITFALL-07 (document not shown) | Add document route handling |

---

## Existing Codebase Strengths

The current implementation already avoids several common pitfalls:

1. **PITFALL-01 mitigated:** `document_upload_screen.dart` uses `file.bytes` not `file.path`
2. **PITFALL-03 mitigated:** `breadcrumb_bar.dart` reads path from GoRouterState, not NavigatorObserver
3. **PITFALL-06 partially mitigated:** Has `maxVisible` parameter and truncation logic
4. **PITFALL-09 mitigated:** Captures provider reference before async gap

---

## Checklist for Implementation

Before implementing v1.9.3 features, verify:

### Document Preview
- [ ] Using `bytes` property (not `path`) for file content
- [ ] UTF-8 decode wrapped in try-catch with `allowMalformed` fallback
- [ ] Provider reference captured before async operations
- [ ] Loading state shown during preview generation
- [ ] Preview dialog responsive to screen size
- [ ] Tested on Chrome browser

### Document Download
- [ ] NOT using `dart:html` (use `web` package or `universal_downloader`)
- [ ] File size checked before loading to memory
- [ ] Platform-specific download implementation (web vs mobile)
- [ ] Tested on all target platforms (web, Android, iOS)

### Breadcrumb Navigation
- [ ] Reading route from `GoRouterState.of(context)` (not NavigatorObserver)
- [ ] Document route handling added to `_buildBreadcrumbs`
- [ ] Responsive `maxVisible` based on screen width
- [ ] Touch targets adequate for mobile (48px minimum)
- [ ] Tested with deep navigation paths

---

## Sources

### Official Documentation
- [file_picker package](https://pub.dev/packages/file_picker)
- [go_router package](https://pub.dev/packages/go_router)
- [showDialog function - Flutter API](https://api.flutter.dev/flutter/material/showDialog.html)

### GitHub Issues & Discussions
- [file_picker FAQ - Web limitations](https://github.com/miguelpruivo/flutter_file_picker/wiki/FAQ)
- [Path is always null on Web](https://github.com/miguelpruivo/flutter_file_picker/issues/443)
- [GoRouter NavigatorObserver limitations](https://github.com/flutter/flutter/issues/142720)
- [ShellRoutes NavigatorObserver issues](https://github.com/flutter/flutter/issues/112196)

### Community Resources
- [Flutter Breadcrumb with GoRouter - nonstopio](https://blog.nonstopio.com/creating-breadcrumbs-in-flutter-using-gorouter-a-step-by-step-guide-cce006757266)
- [Go router navigation observer - DEV Community](https://dev.to/mattia/go-router-navigation-observer-1gj4)
- [Flutter Web Troubleshooting 2025](https://medium.com/@mrlimon28/flutter-web-troubleshooting-guide-2025-fixing-image-picker-database-screen-size-and-cors-issues-fef7e8676562)
- [Cross-Platform Flutter Issues - Smashing Magazine](https://www.smashingmagazine.com/2020/06/common-cross-platform-issues-flutter/)
- [universal_downloader package](https://pub.dev/packages/universal_downloader)
