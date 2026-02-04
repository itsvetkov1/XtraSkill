# Roadmap: BA Assistant v1.9.3

**Milestone:** Document & Navigation Polish
**Created:** 2026-02-04
**Depth:** Quick
**Coverage:** 17/17 requirements mapped

---

## Overview

v1.9.3 improves document workflow with upload preview and download capability, plus completes navigation context with enhanced breadcrumb trails. Three phases deliver independent, verifiable capabilities: download functionality (copy existing pattern), preview dialog (isolated UI), and breadcrumb enhancement (router changes).

---

## Phases

### Phase 37: Document Download

**Goal:** Users can download documents from the application to their device.

**Dependencies:** None (builds on existing file_saver pattern from artifact export)

**Requirements:** DOWNLOAD-01, DOWNLOAD-02, DOWNLOAD-03, DOWNLOAD-04, DOWNLOAD-05

**Plans:** 1 plan

Plans:
- [ ] 37-01-PLAN.md - Add download to viewer and list screens

**Success Criteria:**

1. User clicks download icon in Document Viewer AppBar and file downloads with original filename
2. User right-clicks document in list, selects Download, and file downloads with original filename
3. Success snackbar shows "Downloaded {filename}" after download completes
4. Download works on Chrome (web), Android emulator, and iOS simulator

**Research Notes:**
- Copy pattern from artifact_service.dart (file_saver already proven)
- Avoid dart:html (deprecated) - use file_saver package
- Lowest risk phase - single file touched for viewer download

---

### Phase 38: Document Preview

**Goal:** Users can review document content before uploading to confirm correct file selection.

**Dependencies:** None (isolated UI change, no backend work)

**Requirements:** DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06

**Plans:** TBD

Plans:
- [ ] TBD (created by /gsd:plan-phase)

**Success Criteria:**

1. After selecting file, preview dialog appears showing filename and human-readable size (KB/MB)
2. Preview dialog shows first 20 lines of content in monospace font matching Document Viewer
3. User clicks Cancel to close dialog and clear selection (ready to pick different file)
4. User clicks Upload to proceed with upload (same behavior as before, but after confirmation)

**Research Notes:**
- Use PlatformFile.bytes and size (already available from file_picker)
- Wrap UTF-8 decode in try-catch with allowMalformed: true
- Create new DocumentPreviewDialog widget
- Capture provider reference before async gap

---

### Phase 39: Breadcrumb Navigation

**Goal:** Users see full navigation context including thread and document names in breadcrumbs.

**Dependencies:** Phase 37 (Document Viewer route change benefits from existing download button)

**Requirements:** NAV-01, NAV-02, NAV-03, NAV-04, NAV-05, NAV-06

**Plans:** TBD

Plans:
- [ ] TBD (created by /gsd:plan-phase)

**Success Criteria:**

1. Thread screen shows breadcrumb: Projects > {Project Name} > Threads > {Thread Title}
2. Project-less thread shows breadcrumb: Chats > {Thread Title}
3. Document Viewer shows breadcrumb: Projects > {Project Name} > Documents > {Document Name}
4. Each breadcrumb segment is clickable and navigates to that location
5. Document Viewer has proper URL route (/projects/:id/documents/:docId) enabling deep links

**Research Notes:**
- NAV-06 requires changing Document Viewer from Navigator.push to GoRouter route
- Add /projects/:id/documents/:docId route to main.dart
- Continue using GoRouterState.of(context) for breadcrumb state
- Highest coordination phase - touches router + multiple screens
- Test browser back button behavior after router changes

---

## Progress

| Phase | Name | Status | Requirements | Plans |
|-------|------|--------|--------------|-------|
| 37 | Document Download | Planned | 5 | 1 |
| 38 | Document Preview | Pending | 6 | TBD |
| 39 | Breadcrumb Navigation | Pending | 6 | TBD |

**Total:** 0/17 requirements complete

---

## Requirement Coverage

| Requirement | Phase | Description |
|-------------|-------|-------------|
| DOC-01 | 38 | Preview dialog shows filename |
| DOC-02 | 38 | Preview dialog shows file size (KB/MB) |
| DOC-03 | 38 | Preview dialog shows first 20 lines |
| DOC-04 | 38 | Preview uses monospace font |
| DOC-05 | 38 | Cancel button clears selection |
| DOC-06 | 38 | Upload button proceeds |
| DOWNLOAD-01 | 37 | Download icon in Document Viewer AppBar |
| DOWNLOAD-02 | 37 | Download option in document list context menu |
| DOWNLOAD-03 | 37 | Download uses original filename |
| DOWNLOAD-04 | 37 | Success snackbar shows filename |
| DOWNLOAD-05 | 37 | Works on web, Android, iOS |
| NAV-01 | 39 | Thread: Projects > Project > Threads > Thread |
| NAV-02 | 39 | Project-less: Chats > Thread |
| NAV-03 | 39 | Document: Projects > Project > Documents > Doc |
| NAV-04 | 39 | Each segment clickable and navigates |
| NAV-05 | 39 | Breadcrumbs truncate on mobile |
| NAV-06 | 39 | Document Viewer has proper URL route |

**Coverage:** 17/17 requirements mapped (100%)

---

*Roadmap created: 2026-02-04*
*Last updated: 2026-02-04*
