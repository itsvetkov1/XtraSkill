# Feature Landscape: Document Handling & Navigation (v1.9.3)

**Domain:** Document Preview, Download, Breadcrumb Navigation
**Researched:** 2026-02-04
**Confidence:** HIGH (Industry patterns well-established)

---

## Executive Summary

Research covers three feature areas for BA Assistant v1.9.3: document preview before upload, document download capabilities, and breadcrumb navigation extension. All three follow well-established UX patterns with clear industry consensus on implementation approaches.

**Key findings:**
- Document preview before upload is a **table stakes** feature for professional applications
- Download functionality from viewer and list follows standard patterns (toolbar for viewer, context menu for lists)
- Breadcrumb extension is straightforward; current implementation already has good foundation

---

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Preview file before upload | Users verify correct file selection; prevents errors | Low | Show filename, size, first ~20 lines |
| Clear error messages on upload failure | Users need to understand what went wrong | Low | Already exists, verify coverage |
| Cancel/change file before upload | Users make mistakes and need to correct them | Low | Add explicit "Cancel" and "Change" actions |
| Download from document viewer | Users need to retrieve their uploaded content | Low | AppBar download icon, standard placement |
| Current page in breadcrumb (non-clickable) | Standard breadcrumb convention | Low | Already implemented correctly |
| Clickable ancestor segments | Users navigate back to any level | Low | Already implemented for Projects |

---

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Text content preview with syntax highlighting | For code/config files, show content with highlighting | Medium | Stretch goal - may not be needed for plain text |
| Line count in preview | Quick verification of file completeness | Low | "453 lines" helps verify right file |
| Download from document list | Download without opening viewer first | Low | Context menu action (kebab menu) |
| Horizontal scroll for long breadcrumb trails | Mobile-friendly deep navigation | Low | Current implementation uses SingleChildScrollView - good |
| "Threads" segment in breadcrumb | Clear hierarchy: Projects > Project > Threads > Thread | Low | Missing currently - add for context |

---

## Anti-Features

Features to deliberately NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Path-based breadcrumbs (history trail) | Confusing, not hierarchical; NN/g explicitly advises against | Use location-based hierarchy showing site structure |
| Auto-upload on file selection | No chance to verify; causes errors and user frustration | Show preview, require explicit "Upload" button |
| Edit-in-place for uploaded documents | Scope creep; BA Assistant is for context, not document editing | Keep documents read-only, download for editing |
| Interactive document preview (zoom, scroll pages) | Over-engineering for plain text files | Simple scrollable text preview sufficient |
| Breadcrumb history showing all visited pages | Users don't understand this pattern | Show current location in hierarchy only |
| Multi-line breadcrumbs on mobile | Wastes vertical space, defeats purpose | Truncate or horizontal scroll instead |
| Download confirmation dialog | Unnecessary friction for low-risk action | Just download, show success snackbar |

---

## Feature Specifications

### 1. Document Preview Before Upload

**User Story:** [DOC-001](../../../user_stories/DOC-001_document-preview-upload.md)

**What users should see:**
```
+------------------------------------------+
| Selected File                            |
+------------------------------------------+
| Filename:  requirements_v2.txt           |
| Size:      12.4 KB                       |
| Lines:     324                           |
+------------------------------------------+
| Preview:                                 |
| ---------------------------------------- |
| 1  # Project Requirements v2.0           |
| 2                                        |
| 3  ## Overview                           |
| 4  This document outlines the functional |
| 5  requirements for the BA Assistant...  |
| ...                                      |
| 20 - User authentication via OAuth       |
| ---------------------------------------- |
| [Cancel]              [Upload]           |
+------------------------------------------+
```

**Implementation details:**
- Show first 20 lines of file content
- Use monospace font (consistent with Document Viewer)
- Line numbers optional but recommended
- File metadata at top: filename, size, line count
- Two clear actions: Cancel and Upload
- Preview should be scrollable if needed

**UX best practices applied:**
- Preview before commit (from Uploadcare, FileStack research)
- Clear feedback with visual confirmation
- User control with cancel option
- Consistent styling with existing Document Viewer

### 2. Document Download

**User Story:** [DOC-002](../../../user_stories/DOC-002_download-document.md)

**A. From Document Viewer (Primary)**
```
+------------------------------------------+
| AppBar: Document Name    [Download icon] |
+------------------------------------------+
```

- Download icon in AppBar actions (top right)
- Use standard download icon (Icons.download or Icons.file_download)
- On tap: initiate download, show snackbar "Downloaded {filename}"
- Use original filename from upload

**B. From Document List (Secondary)**
```
+------------------------------------------+
| requirements.txt    12.4 KB    [:] <-- kebab menu
+------------------------------------------+
                              +------------+
                              | View       |
                              | Download   |
                              | ---------- |
                              | Delete     |
                              +------------+
```

- Kebab menu (three vertical dots) on each document row
- Menu items: View, Download, Delete (delete at bottom, possibly red)
- Download triggers same action as viewer download
- View opens document viewer (existing behavior)

**Pattern rationale:**
- Primary action (View) should remain accessible without menu
- Download and Delete are secondary actions, appropriate for context menu
- Grouping: View and Download are positive actions; Delete is destructive (separate group)

### 3. Breadcrumb Navigation Extension

**User Story:** [NAV-001](../../../user_stories/NAV-001_breadcrumb-thread-context.md)

**Current state:**
- `/projects` -> "Projects"
- `/projects/:id` -> "Projects > {Project Name}"
- `/projects/:id/threads/:threadId` -> "Projects > {Project Name} > {Thread Title}"

**Proposed enhancement (from user story):**
- `/projects/:id/threads/:threadId` -> "Projects > {Project Name} > Threads > {Thread Title}"

**Analysis:** The user story requests adding "Threads" as a segment. This is a reasonable ask but consider:

| Option | Breadcrumb | Pros | Cons |
|--------|------------|------|------|
| Current | Projects > Project > Thread | Shorter | Less explicit |
| Proposed | Projects > Project > Threads > Thread | More explicit hierarchy | Longer |

**Recommendation:** Implement as proposed. The "Threads" segment:
- Provides clearer navigation context
- Clicking "Threads" could navigate to project's threads tab
- Follows NN/g guideline: breadcrumbs show site structure

**For project-less chats:**
- `/chats` -> "Chats"
- `/chats/:threadId` -> "Chats > {Thread Title}"

No "Threads" intermediate segment needed for chats since they're not nested in projects.

**Mobile considerations:**
- Current implementation uses `SingleChildScrollView` with horizontal scroll - good
- `maxVisible` property supports truncation if needed
- Touch targets maintained via TextButton with proper padding (8px horizontal, 4px vertical)

---

## Implementation Dependencies

```
Document Preview Before Upload
    |
    +-- Uses existing document reading logic
    +-- No external dependencies

Document Download
    |
    +-- Platform-specific file saving
    |     +-- Flutter: file_picker or path_provider + permission_handler
    |     +-- Web: html download attribute / Blob URL
    +-- Backend: document content retrieval (already exists)

Breadcrumb Extension
    |
    +-- Existing BreadcrumbBar widget (minimal changes)
    +-- Router already supports needed paths
    +-- No external dependencies
```

---

## MVP Recommendation

For v1.9.3 MVP, implement in this order:

1. **Document Preview Before Upload** (DOC-001)
   - High impact on error prevention
   - Low complexity
   - Self-contained implementation

2. **Document Download from Viewer** (DOC-002 - partial)
   - Core user need
   - Low complexity
   - AppBar action button only

3. **Breadcrumb Extension** (NAV-001)
   - Improves navigation consistency
   - Very low complexity (modify existing widget)
   - Quick win

**Defer to later:**
- Download from document list (nice-to-have, not critical)
- Syntax highlighting in preview (over-engineering for plain text)

---

## Feature Comparison: Industry Examples

| App | Preview Before Upload | Download from Viewer | Download from List | Breadcrumb Style |
|-----|----------------------|---------------------|-------------------|------------------|
| Google Drive | Yes (thumbnail) | Yes (toolbar) | Yes (context menu) | Location-based |
| Dropbox | Yes (preview modal) | Yes (toolbar) | Yes (context menu) | Location-based |
| Notion | No (inline upload) | Yes (hover action) | Yes (... menu) | Location-based |
| Slack | Yes (preview in chat) | Yes (download link) | N/A | N/A |

BA Assistant aligns with industry standard patterns.

---

## Sources

### Document Upload/Preview
- [Uploadcare - File Uploader UX Best Practices](https://uploadcare.com/blog/file-uploader-ux-best-practices/)
- [FileStack - Designing an Intuitive Document Upload UI](https://blog.filestack.com/designing-an-intuitive-document-upload-ui/)
- [FileStack - Document Upload UI: Enhancing UX](https://blog.filestack.com/document-upload-ui-2/)
- [UINKITS - Best Practices For File Upload Components](https://www.uinkits.com/blog-post/best-practices-for-file-upload-components)

### Document Download/Context Menus
- [NN/G - Designing Effective Contextual Menus: 10 Guidelines](https://www.nngroup.com/articles/contextual-menus-guidelines/)
- [Carbon Design System - Export Pattern](https://carbondesignsystem.com/community/patterns/export-pattern/)
- [Foldr - Web App File Viewer](https://foldr.com/foldr-support/web-app-file-viewer/)

### Breadcrumb Navigation
- [NN/G - Breadcrumbs: 11 Design Guidelines for Desktop and Mobile](https://www.nngroup.com/articles/breadcrumbs/)
- [Pencil & Paper - Breadcrumbs UX Navigation Guide](https://www.pencilandpaper.io/articles/breadcrumbs-ux)
- [IxDF - Mobile Breadcrumbs: 8 Best Practices in UX](https://www.interaction-design.org/literature/article/mobile-breadcrumbs)
- [LogRocket - Breadcrumbs vs Back Arrow UX Best Practices](https://blog.logrocket.com/ux-design/breadcrumbs-vs-back-arrow-ux-best-practices/)

### Flutter Implementation
- [Medium - Creating Breadcrumbs in Flutter Using GoRouter](https://blog.nonstopio.com/creating-breadcrumbs-in-flutter-using-gorouter-a-step-by-step-guide-cce006757266)
- [flutter_breadcrumb package](https://pub.dev/documentation/flutter_breadcrumb/latest/)

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Document Preview UX | HIGH | Multiple authoritative sources agree; industry standard |
| Document Download patterns | HIGH | Well-established conventions; Carbon Design System guidance |
| Breadcrumb best practices | HIGH | NN/G research (authoritative), multiple sources confirm |
| Flutter implementation | HIGH | Existing codebase shows working patterns; minor extensions needed |

---

*Research completed: 2026-02-04*
*Researcher: Claude (gsd-research-features)*
