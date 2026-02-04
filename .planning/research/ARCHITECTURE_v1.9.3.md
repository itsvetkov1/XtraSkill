# Architecture Research: v1.9.3 Document Navigation & Handling

**Research Date:** 2026-02-04
**Milestone:** v1.9.3 - Document Navigation & Handling
**Confidence:** HIGH (verified against existing codebase)

## Executive Summary

This document analyzes how the three target features for v1.9.3 should integrate with the existing BA Assistant architecture:

1. **Document Preview** - Preview before upload confirmation
2. **Document Download** - Download document content as file
3. **Breadcrumb Enhancement** - Dynamic path display with document context

The existing architecture provides strong integration points. Document handling already flows through `DocumentProvider` and `DocumentService`. The `BreadcrumbBar` widget already parses routes and reads provider state. All features can be implemented with minimal structural changes by extending existing patterns.

**Key finding:** No new providers needed. All features integrate into existing component boundaries.

---

## Current Architecture Relevant to v1.9.3

### Document Data Flow (Existing)

```
+------------------+      +------------------+      +------------------+      +-------------+
|  Upload Screen   |----->| DocumentProvider |----->| DocumentService  |----->| Backend API |
|  (file_picker)   |      | (state mgmt)     |      | (HTTP client)    |      | /documents  |
+------------------+      +------------------+      +------------------+      +-------------+
        |                        |
        | PlatformFile           | Document model
        | .name                  | .id, .filename
        | .bytes                 | .content (optional)
        v                        v
+------------------+      +------------------+
| Local preview    |      | View/List        |
| (before upload)  |      | (after upload)   |
+------------------+      +------------------+
```

### Navigation Data Flow (Existing)

```
+------------------+      +------------------+      +------------------+
|  GoRouter        |----->| BreadcrumbBar    |----->| Provider reads   |
|  (path changes)  |      | (parses route)   |      | (context names)  |
+------------------+      +------------------+      +------------------+
                                 |
                                 | Reads from:
                                 | - ProjectProvider.selectedProject
                                 | - ConversationProvider.thread
                                 v
                          +------------------+
                          | Breadcrumb list  |
                          | with labels/links|
                          +------------------+
```

### Current Route Structure

```
/home
/chats
/chats/:threadId
/projects
/projects/:id
/projects/:id/threads/:threadId
/settings
```

**Note:** Document viewer is currently accessed via `Navigator.push()` (modal navigation), NOT via GoRouter routes. This affects breadcrumb handling.

---

## Feature 1: Document Preview (Pre-Upload)

### Current Upload Flow

```dart
// document_upload_screen.dart (current)
1. User taps "Select File"
2. FilePicker.platform.pickFiles() opens native picker
3. File returned as PlatformFile with .bytes and .name
4. VALIDATION: File size check (1MB limit)
5. If valid -> immediately call provider.uploadDocument()
6. Show progress -> success -> Navigator.pop()
```

**Gap:** No preview step between selection and upload.

### Proposed Architecture

```
+------------------+      +------------------+      +------------------+
|  DocumentUpload  |      |  Preview Dialog  |      | DocumentProvider |
|  Screen          |      |  (new widget)    |      |                  |
+------------------+      +------------------+      +------------------+
        |                        |                         |
        | 1. pickFiles()         |                         |
        |                        |                         |
        | 2. Get PlatformFile    |                         |
        |----------------------->|                         |
        |                        | 3. Display:             |
        |                        |    - filename           |
        |                        |    - file size          |
        |                        |    - content preview    |
        |                        |    (first N chars)      |
        |                        |                         |
        |                        | 4. User confirms        |
        |                        |------------------------>|
        |                        |                         | 5. uploadDocument()
        |                        |                         |
        |<-----------------------|<------------------------|
        | 6. Navigate back on success                      |
```

### Component Placement

| Component | Location | New/Modify |
|-----------|----------|------------|
| `DocumentPreviewDialog` | `lib/widgets/` or `lib/screens/documents/` | **NEW** |
| `DocumentUploadScreen` | `lib/screens/documents/document_upload_screen.dart` | MODIFY |
| `DocumentProvider` | `lib/providers/document_provider.dart` | NO CHANGE |

### Data Available for Preview

From `PlatformFile` (file_picker):
- `name` - filename with extension
- `bytes` - file content as `Uint8List`
- `size` - file size in bytes
- `extension` - file extension

**Preview content generation:**
```dart
String previewContent = utf8.decode(file.bytes!.take(2000).toList());
```

### Design Decision: Dialog vs Screen

**Recommendation: Dialog**

| Approach | Pros | Cons |
|----------|------|------|
| Dialog | Quick flow, no navigation complexity, file bytes stay in memory | Limited screen real estate |
| Full Screen | More space for preview | Requires passing bytes through navigation, more complex |

Dialog is preferred because:
1. Preview is a confirmation step, not a destination
2. `PlatformFile.bytes` is already in memory - passing to dialog is trivial
3. Matches existing dialog patterns (thread rename, project edit)

### Integration Points

1. **_pickAndUploadFile() in DocumentUploadScreen:**
   - After file selection and size validation
   - Before calling `provider.uploadDocument()`
   - Show `DocumentPreviewDialog` with file data

2. **DocumentPreviewDialog (new):**
   - Receives: `PlatformFile file, String projectId`
   - Displays: filename, size, content preview
   - Actions: Cancel (returns null), Confirm (returns file)

3. **Upload continues only if dialog confirms**

---

## Feature 2: Document Download

### Current State

Backend endpoint `GET /documents/{id}` returns:
```json
{
  "id": "uuid",
  "filename": "requirements.md",
  "content": "# Decrypted plaintext content...",
  "created_at": "2026-01-15T10:30:00Z"
}
```

Frontend `DocumentViewerScreen`:
- Calls `provider.selectDocument(documentId)`
- Displays content in `SelectableText` widget
- No download capability

### Proposed Architecture

```
+------------------+      +------------------+      +------------------+
| DocumentViewer   |      | DocumentProvider |      | Platform Layer   |
| Screen           |      |                  |      | (download impl)  |
+------------------+      +------------------+      +------------------+
        |                        |                         |
        | 1. Download tap        |                         |
        |                        |                         |
        | 2. Get document        |                         |
        |    (already loaded)    |                         |
        |                        |                         |
        | 3. Call download       |                         |
        |------------------------|------------------------>|
        |                        |                         | 4. Platform-specific
        |                        |                         |    file save
        |                        |                         |
        |<-----------------------|<------------------------|
        | 5. Show success/error snackbar                   |
```

### Platform-Specific Download Implementation

**Web Platform:**
```dart
// Use html package for web
import 'dart:html' as html;

void downloadFile(String content, String filename) {
  final bytes = utf8.encode(content);
  final blob = html.Blob([bytes]);
  final url = html.Url.createObjectUrlFromBlob(blob);
  final anchor = html.AnchorElement()
    ..href = url
    ..download = filename;
  anchor.click();
  html.Url.revokeObjectUrl(url);
}
```

**Mobile/Desktop (if needed later):**
```dart
// Use path_provider + file operations
// Or file_saver package for cross-platform
```

### Component Placement

| Component | Location | New/Modify |
|-----------|----------|------------|
| `DocumentViewerScreen` | `lib/screens/documents/document_viewer_screen.dart` | MODIFY (add download button) |
| `document_download_web.dart` | `lib/services/` | **NEW** (conditional import) |
| `document_download_stub.dart` | `lib/services/` | **NEW** (stub for non-web) |

### Backend API

**No changes needed.** Current `GET /documents/{id}` endpoint already returns:
- Full decrypted content
- Filename (for download name)

### Integration Points

1. **AppBar action in DocumentViewerScreen:**
   ```dart
   AppBar(
     actions: [
       IconButton(
         icon: Icon(Icons.download),
         onPressed: _downloadDocument,
       ),
     ],
   )
   ```

2. **_downloadDocument() method:**
   ```dart
   void _downloadDocument() {
     final doc = provider.selectedDocument;
     if (doc == null || doc.content == null) return;

     DocumentDownload.download(doc.content!, doc.filename);
   }
   ```

3. **Conditional import pattern** (established in codebase for web-specific features):
   ```dart
   import 'document_download_stub.dart'
     if (dart.library.html) 'document_download_web.dart';
   ```

---

## Feature 3: Breadcrumb Enhancement (Dynamic Paths)

### Current BreadcrumbBar Behavior

**Supported routes:**
- `/home` -> "Home"
- `/settings` -> "Settings"
- `/projects` -> "Projects"
- `/projects/:id` -> "Projects > [Project Name]"
- `/projects/:id/threads/:threadId` -> "Projects > [Project Name] > [Thread Title]"

**Data sources:**
- `ProjectProvider.selectedProject?.name` for project name
- `ConversationProvider.thread?.title` for thread title

**Unsupported:**
- Document viewer (uses modal `Navigator.push`, not GoRouter)
- Chats branch (`/chats/:threadId`)

### Current Limitation Analysis

Document viewing uses:
```dart
Navigator.of(context).push(
  MaterialPageRoute(
    builder: (context) => DocumentViewerScreen(documentId: documentId),
  ),
);
```

This means:
1. URL doesn't change (`/projects/:id` stays in address bar)
2. `BreadcrumbBar` sees `/projects/:id`, not document route
3. No deep linking to documents

### Approach Options

| Approach | Description | Complexity | URL Changes |
|----------|-------------|------------|-------------|
| A. GoRouter route | Add `/projects/:id/documents/:docId` route | Medium | Yes |
| B. Provider state | Track "viewing document" in provider, breadcrumb reads it | Low | No |
| C. Hybrid | Route for linking, provider for breadcrumb context | Medium | Yes |

### Recommended: Approach A (GoRouter Routes)

**Rationale:**
1. Consistent with existing routing patterns
2. Enables deep linking to documents
3. Browser back button works correctly
4. Clear URL for sharing/bookmarking
5. BreadcrumbBar already handles route parsing

### Proposed Route Structure

```
/projects/:id                           -> "Projects > [Project Name]"
/projects/:id/documents/:docId          -> "Projects > [Project Name] > [Document Name]"
/projects/:id/threads/:threadId         -> "Projects > [Project Name] > [Thread Title]"
```

**Chats branch extension:**
```
/chats                                  -> "Chats"
/chats/:threadId                        -> "Chats > [Thread Title]"
```

### Component Modifications

#### 1. main.dart (Router Configuration)

Add document route:
```dart
GoRoute(
  path: ':id',
  builder: (context, state) {
    final id = state.pathParameters['id']!;
    return ProjectDetailScreen(projectId: id);
  },
  routes: [
    // EXISTING: threads route
    GoRoute(
      path: 'threads/:threadId',
      builder: ...
    ),
    // NEW: documents route
    GoRoute(
      path: 'documents/:docId',
      builder: (context, state) {
        final docId = state.pathParameters['docId']!;
        return DocumentViewerScreen(documentId: docId);
      },
    ),
  ],
),
```

#### 2. BreadcrumbBar (_buildBreadcrumbs)

Extend route parsing:
```dart
// Handle /projects/:id/documents/:docId
if (segments.length >= 4 && segments[2] == 'documents') {
  // Projects link
  breadcrumbs.add(const Breadcrumb('Projects', '/projects'));

  // Project name link
  final projectId = segments[1];
  final projectName = projectProvider.selectedProject?.name ?? 'Project';
  breadcrumbs.add(Breadcrumb(projectName, '/projects/$projectId'));

  // Document name (current page, no link)
  final documentProvider = context.read<DocumentProvider>();
  final docName = documentProvider.selectedDocument?.filename ?? 'Document';
  breadcrumbs.add(Breadcrumb(docName));

  return breadcrumbs;
}
```

#### 3. Navigation Changes (documents_column.dart, document_list_screen.dart)

Replace:
```dart
Navigator.of(context).push(
  MaterialPageRoute(
    builder: (context) => DocumentViewerScreen(documentId: documentId),
  ),
);
```

With:
```dart
context.go('/projects/$projectId/documents/$documentId');
```

### Data Flow for Document Name in Breadcrumb

```
+------------------+      +------------------+      +------------------+
| GoRouter         |----->| DocumentViewer   |----->| DocumentProvider |
| (path: /docs/:id)|      | Screen           |      | selectDocument() |
+------------------+      +------------------+      +------------------+
                                                           |
                                                           v
                                                   +------------------+
                                                   | selectedDocument |
                                                   | .filename        |
                                                   +------------------+
                                                           |
                                                           v
                                                   +------------------+
                                                   | BreadcrumbBar    |
                                                   | reads provider   |
                                                   +------------------+
```

**Timing consideration:** `BreadcrumbBar` reads `DocumentProvider.selectedDocument` which is populated by `DocumentViewerScreen.initState()`. The breadcrumb may show "Document" briefly before the actual filename loads. This is acceptable as the same pattern exists for project/thread names.

---

## Build Order (Dependency Analysis)

### Dependency Graph

```
                    +------------------------+
                    | Feature 1: Preview     |
                    | (no dependencies)      |
                    +------------------------+
                              |
                              | (independent)
                              v
+------------------------+    +------------------------+
| Feature 2: Download    |    | Feature 3: Breadcrumbs |
| (no dependencies)      |    | (depends on F1 if      |
+------------------------+    |  preview shows in      |
                              |  upload flow)          |
                              +------------------------+
```

### Recommended Phase Order

**Phase 1: Document Preview**
- Completely isolated feature
- No provider changes
- New widget only
- Can be tested independently

**Phase 2: Document Download**
- Requires web-specific implementation
- No provider changes
- Minimal UI changes (one button)
- Can be tested independently

**Phase 3: Breadcrumb Enhancement**
- Requires router changes (coordination risk)
- Requires provider reads (existing pattern)
- Requires navigation refactor (modal -> route)
- **Should be done last** as it touches multiple files

**Rationale for this order:**
1. Preview and Download are isolated, easy to verify
2. Breadcrumb changes navigation patterns - higher coordination risk
3. If breadcrumbs block, other features are already complete

---

## Component Boundaries Summary

### What Talks to What

| Component | Communicates With | Direction |
|-----------|------------------|-----------|
| `DocumentUploadScreen` | `DocumentPreviewDialog` | Shows dialog, receives confirmation |
| `DocumentPreviewDialog` | N/A (receives props) | Pure UI component |
| `DocumentViewerScreen` | `DocumentDownload` service | Triggers download |
| `DocumentDownload` | Browser/Platform APIs | Saves file |
| `BreadcrumbBar` | `DocumentProvider` | Reads `selectedDocument` |
| `DocumentsColumn` | `GoRouter` | Navigation via `context.go()` |
| `GoRouter` | `DocumentViewerScreen` | Route parameter passing |

### New Files Required

| File | Purpose | Phase |
|------|---------|-------|
| `document_preview_dialog.dart` | Preview UI before upload | 1 |
| `document_download_web.dart` | Web download implementation | 2 |
| `document_download_stub.dart` | Stub for non-web platforms | 2 |

### Modified Files

| File | Change | Phase |
|------|--------|-------|
| `document_upload_screen.dart` | Show preview dialog | 1 |
| `document_viewer_screen.dart` | Add download button | 2 |
| `main.dart` | Add document route | 3 |
| `breadcrumb_bar.dart` | Handle document routes | 3 |
| `documents_column.dart` | Use `context.go()` | 3 |
| `document_list_screen.dart` | Use `context.go()` | 3 |

---

## Risk Assessment

### Low Risk
- **Document Preview:** Isolated change, new dialog widget
- **Document Download:** Web-only initially, isolated implementation

### Medium Risk
- **Breadcrumb Enhancement:** Router changes affect multiple screens
  - Mitigation: Test navigation thoroughly after router changes
  - Mitigation: Keep modal navigation as fallback if issues arise

### Technical Debt Consideration
- Current modal navigation for documents works but lacks URL consistency
- Route-based approach is cleaner long-term
- Migration is straightforward (change `Navigator.push` to `context.go`)

---

## Testing Implications

### Feature 1: Preview
- Unit test: Preview content truncation
- Widget test: Dialog shows correct file info
- Integration test: Full upload flow with preview step

### Feature 2: Download
- Manual test: File downloads with correct name and content
- Browser test: Chrome, Firefox, Safari, Edge

### Feature 3: Breadcrumb
- Widget test: Correct breadcrumb segments for document routes
- Integration test: Navigation from project -> document -> back
- URL test: Deep link to document works

---

## Summary

All three v1.9.3 features integrate cleanly with the existing architecture:

| Feature | Approach | New Components | Risk |
|---------|----------|----------------|------|
| Document Preview | Dialog before upload | `DocumentPreviewDialog` | Low |
| Document Download | Web platform download | `document_download_*.dart` | Low |
| Breadcrumb Enhancement | GoRouter routes + provider reads | Route config, breadcrumb parsing | Medium |

**Key architectural decisions:**
1. Preview uses dialog (not full screen) for simplicity
2. Download uses conditional imports for platform-specific code
3. Breadcrumbs require route change (modal -> GoRouter) for proper URL support

**Build order:** Preview -> Download -> Breadcrumbs (isolated first, coordination-heavy last)
