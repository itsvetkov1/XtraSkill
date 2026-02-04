# Research Summary: v1.9.3 Document Navigation & Handling

**Project:** BA Assistant
**Milestone:** v1.9.3
**Synthesized:** 2026-02-04
**Research Files:**
- STACK_v1.9.3.md
- FEATURES_v1.9.3.md
- ARCHITECTURE_v1.9.3.md
- PITFALLS_v1.9.3.md

---

## Executive Summary

BA Assistant v1.9.3 targets three user-facing enhancements: document preview before upload, document download functionality, and enhanced breadcrumb navigation. Research confirms all three features follow well-established industry patterns with clear implementation paths. The most important finding is that **zero new dependencies are required** - the existing stack (file_picker, file_saver, go_router, provider) already provides all necessary capabilities.

The recommended approach is to implement features in order of isolation: download first (copy existing artifact_service pattern), preview second (new dialog widget, no backend changes), and breadcrumbs last (router changes touch multiple files). This ordering front-loads quick wins while deferring the highest-coordination feature. The existing codebase already avoids several common pitfalls (uses bytes not path for web compatibility, reads route from GoRouterState not NavigatorObserver), but new code must be careful about UTF-8 encoding assumptions and the deprecated dart:html package.

Key risks center on the breadcrumb enhancement, which requires changing document navigation from modal (`Navigator.push`) to route-based (`context.go`) patterns. This is the right architectural direction for URL consistency and deep linking, but touches the most files. Download and preview are low-risk, self-contained changes that can be tested independently.

---

## Key Findings

### From STACK.md: Technology Choices

| Technology | Use Case | Rationale |
|------------|----------|-----------|
| `file_picker` (existing) | Document preview | `PlatformFile.bytes` provides content; `size` and `name` already used |
| `file_saver` (existing) | Document download | Pattern proven in `artifact_service.dart`; cross-platform |
| `go_router` (existing) | Breadcrumbs | `GoRouterState.of(context)` provides current route |
| `provider` (existing) | Name resolution | `DocumentProvider.selectedDocument` for breadcrumb labels |

**No new dependencies needed.** Current versions are sufficient:
- file_picker 10.3.8 (latest 10.3.10 optional)
- file_saver 0.2.14 (latest 0.3.1 optional)
- go_router 17.0.1 (latest 17.1.0 optional)

### From FEATURES.md: Feature Scope

**Table Stakes (must implement):**
| Feature | Complexity | Notes |
|---------|------------|-------|
| Preview file before upload (filename, size, first 20 lines) | Low | Error prevention, standard UX |
| Cancel/change file option in preview | Low | User control |
| Download from document viewer (AppBar icon) | Low | Core user need |
| Document name in breadcrumb trail | Low | Navigation consistency |

**Differentiators (consider for v1.9.3):**
| Feature | Complexity | Notes |
|---------|------------|-------|
| Line count in preview | Low | Quick file verification |
| Download from document list (context menu) | Low | Convenience feature |
| "Threads" intermediate breadcrumb segment | Low | Clearer hierarchy |

**Anti-Features (do not build):**
- Edit-in-place for documents (scope creep)
- Interactive preview with zoom/scroll (over-engineering for text)
- Auto-upload on file selection (no verification = user errors)
- Download confirmation dialog (unnecessary friction)
- Path-based breadcrumbs showing history (confuses users)

### From ARCHITECTURE.md: Component Design

**Document Preview:**
- Approach: Dialog (not full screen) - file bytes already in memory, quick confirmation flow
- New component: `DocumentPreviewDialog` widget
- Integration point: After file selection in `DocumentUploadScreen`, before upload

**Document Download:**
- Approach: Reuse `file_saver` pattern from artifact_service
- New component: None needed - add method to existing service or screen
- Integration point: AppBar action in `DocumentViewerScreen`

**Breadcrumb Enhancement:**
- Approach: Add GoRouter route for documents (`/projects/:id/documents/:docId`)
- Changes required:
  1. Router configuration in main.dart
  2. Route parsing in breadcrumb_bar.dart
  3. Navigation calls in documents_column.dart, document_list_screen.dart
- This enables deep linking, proper back button, URL sharing

**Navigation Pattern Change:**
```
Before: Navigator.push(DocumentViewerScreen)  // URL unchanged
After:  context.go('/projects/:id/documents/:docId')  // URL reflects location
```

### From PITFALLS.md: Critical Risks

**Top 5 Pitfalls to Prevent:**

| ID | Pitfall | Severity | Feature | Prevention |
|----|---------|----------|---------|------------|
| PITFALL-01 | Web path always null | Critical | Preview | Use `bytes` property, not `path` (codebase already does this) |
| PITFALL-02 | dart:html deprecated | Critical | Download | Use `web` package or `file_saver` (not dart:html) |
| PITFALL-03 | NavigatorObserver misses go() | Critical | Breadcrumbs | Use `GoRouterState.of(context)` (codebase already does this) |
| PITFALL-04 | UTF-8 decode failures | Critical | Preview | Wrap in try-catch, use `allowMalformed: true` |
| PITFALL-09 | Context lost after async | Moderate | Preview/Download | Capture provider reference before await |

**Codebase Strengths (already mitigated):**
- Uses `file.bytes` not `file.path` for web compatibility
- Breadcrumbs read from GoRouterState, not NavigatorObserver
- Provider references captured before async gaps
- Has `maxVisible` truncation for breadcrumb overflow

---

## Implications for Roadmap

### Recommended Phase Structure

Based on dependency analysis and risk assessment, implement in this order:

**Phase 1: Document Download**
- **Rationale:** Lowest risk, copy existing pattern from artifact_service
- **Delivers:** Download button in document viewer, success feedback
- **Features:** DOC-002 (partial - viewer download only)
- **Pitfalls to avoid:** PITFALL-02 (use file_saver, not dart:html)
- **Estimated complexity:** Low
- **Files touched:** `document_viewer_screen.dart` only

**Phase 2: Document Preview Before Upload**
- **Rationale:** Isolated UI change, no backend work, self-contained
- **Delivers:** Preview dialog showing filename, size, line count, content sample
- **Features:** DOC-001
- **Pitfalls to avoid:** PITFALL-04 (UTF-8 encoding), PITFALL-09 (async context)
- **Estimated complexity:** Low-Medium
- **Files touched:** `document_upload_screen.dart`, new `document_preview_dialog.dart`

**Phase 3: Breadcrumb Enhancement with Document Routes**
- **Rationale:** Highest coordination, touches router + multiple screens
- **Delivers:** Document names in breadcrumbs, deep linking to documents
- **Features:** NAV-001, plus document route integration
- **Pitfalls to avoid:** PITFALL-03 (continue using GoRouterState), PITFALL-06 (responsive truncation)
- **Estimated complexity:** Medium
- **Files touched:** `main.dart`, `breadcrumb_bar.dart`, `documents_column.dart`, `document_list_screen.dart`

**Optional Phase 4: Download from Document List (defer to v1.9.4 if time-constrained)**
- **Rationale:** Nice-to-have, not critical for core experience
- **Delivers:** Context menu with Download option in document list
- **Estimated complexity:** Low

### Research Flags

| Phase | Research Needed? | Notes |
|-------|------------------|-------|
| Phase 1 (Download) | NO | Pattern exists in artifact_service, copy it |
| Phase 2 (Preview) | NO | Standard dialog pattern, data already available |
| Phase 3 (Breadcrumbs) | MAYBE | Verify route change doesn't break existing navigation; test browser back button behavior |

**Recommendation:** Phase 3 should include a brief verification step after router changes to ensure existing project/thread navigation still works correctly.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All packages verified in official docs; versions compatible; existing patterns in codebase |
| Features | HIGH | NN/g and industry sources agree on UX patterns; table stakes well-defined |
| Architecture | HIGH | Verified against actual codebase files; clear integration points identified |
| Pitfalls | HIGH | GitHub issues cited; existing mitigations confirmed in codebase |

**Overall Confidence:** HIGH

### Gaps Identified

1. **Download behavior on mobile platforms:** Research focused on web (primary platform). Mobile/desktop download may need additional testing but `file_saver` should handle it.

2. **Breadcrumb timing edge case:** If user deep-links directly to document URL, `DocumentProvider.selectedDocument` may not be populated yet. The breadcrumb might show "Document" briefly. Acceptable UX but worth noting.

3. **Large file preview performance:** For files near 1MB limit, preview generation might have noticeable delay. Should show loading indicator (PITFALL-11).

---

## Sources (Aggregated)

### Official Documentation
- [file_picker pub.dev](https://pub.dev/packages/file_picker) - v10.3.10
- [file_saver pub.dev](https://pub.dev/packages/file_saver) - v0.3.1
- [go_router pub.dev](https://pub.dev/packages/go_router) - v17.1.0

### UX Research
- [NN/G - Breadcrumbs: 11 Design Guidelines](https://www.nngroup.com/articles/breadcrumbs/)
- [NN/G - Designing Effective Contextual Menus](https://www.nngroup.com/articles/contextual-menus-guidelines/)
- [Uploadcare - File Uploader UX Best Practices](https://uploadcare.com/blog/file-uploader-ux-best-practices/)
- [Carbon Design System - Export Pattern](https://carbondesignsystem.com/community/patterns/export-pattern/)

### Technical References
- [file_picker GitHub FAQ - Web limitations](https://github.com/miguelpruivo/flutter_file_picker/wiki/FAQ)
- [GoRouter NavigatorObserver limitations](https://github.com/flutter/flutter/issues/142720)
- [web package for downloads](https://quickcoder.org/how-to-download-files-with-the-web-package-in-flutter-apps/)

### Codebase Verification
- `frontend/lib/screens/documents/document_upload_screen.dart`
- `frontend/lib/services/artifact_service.dart`
- `frontend/lib/widgets/breadcrumb_bar.dart`
- `frontend/lib/providers/document_provider.dart`

---

## Implementation Checklist

### Pre-Implementation Verification
- [ ] Confirm file_saver works in artifact export (existing pattern)
- [ ] Review document_upload_screen.dart for current upload flow
- [ ] Review breadcrumb_bar.dart for current route parsing

### Phase 1: Download
- [ ] Add download icon to DocumentViewerScreen AppBar
- [ ] Use file_saver.saveFile() with document content
- [ ] Show success snackbar
- [ ] Test on Chrome

### Phase 2: Preview
- [ ] Create DocumentPreviewDialog widget
- [ ] Show filename, size, line count, first 20 lines
- [ ] Add Cancel and Upload buttons
- [ ] Wrap UTF-8 decode in try-catch
- [ ] Integrate into upload flow after file selection
- [ ] Test with various file encodings

### Phase 3: Breadcrumbs
- [ ] Add `/projects/:id/documents/:docId` route to main.dart
- [ ] Add document case to breadcrumb_bar.dart
- [ ] Change document navigation from push to go()
- [ ] Test deep linking to document
- [ ] Test browser back button
- [ ] Test existing project/thread navigation still works

---

*Research synthesis complete. Ready for roadmap creation.*
