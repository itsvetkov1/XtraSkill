# Requirements: BA Assistant v1.9.3

**Defined:** 2026-02-04
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v1.9.3 Requirements

Requirements for Document & Navigation Polish milestone.

### Document Preview (DOC)

- [x] **DOC-01**: After file selection, preview dialog shows filename
- [x] **DOC-02**: Preview dialog shows file size (human readable: KB/MB)
- [x] **DOC-03**: Preview dialog shows first 20 lines of content
- [x] **DOC-04**: Preview uses monospace font consistent with Document Viewer
- [x] **DOC-05**: Cancel button clears selection and closes dialog
- [x] **DOC-06**: Upload button proceeds with upload

### Document Download (DOWNLOAD)

- [x] **DOWNLOAD-01**: Download icon button in Document Viewer AppBar
- [x] **DOWNLOAD-02**: Download option in document list context menu
- [x] **DOWNLOAD-03**: Download uses original filename
- [x] **DOWNLOAD-04**: Success snackbar: "Downloaded {filename}"
- [x] **DOWNLOAD-05**: Works on web, Android, and iOS

### Breadcrumb Navigation (NAV)

- [ ] **NAV-01**: Thread screen shows: Projects > {Project} > Threads > {Thread}
- [ ] **NAV-02**: Project-less thread shows: Chats > {Thread}
- [ ] **NAV-03**: Document Viewer shows: Projects > {Project} > Documents > {Doc}
- [ ] **NAV-04**: Each breadcrumb segment is clickable and navigates
- [ ] **NAV-05**: Breadcrumbs truncate gracefully on mobile
- [ ] **NAV-06**: Document Viewer has proper URL route (not modal)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Document editing | Out of project scope entirely |
| Bulk download | Deferred to v2.0 bulk operations |
| Document versioning | Not in project scope |
| Breadcrumb history (back path) | Anti-pattern per research |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DOC-01 | 38 | Complete |
| DOC-02 | 38 | Complete |
| DOC-03 | 38 | Complete |
| DOC-04 | 38 | Complete |
| DOC-05 | 38 | Complete |
| DOC-06 | 38 | Complete |
| DOWNLOAD-01 | 37 | Complete |
| DOWNLOAD-02 | 37 | Complete |
| DOWNLOAD-03 | 37 | Complete |
| DOWNLOAD-04 | 37 | Complete |
| DOWNLOAD-05 | 37 | Complete |
| NAV-01 | 39 | Pending |
| NAV-02 | 39 | Pending |
| NAV-03 | 39 | Pending |
| NAV-04 | 39 | Pending |
| NAV-05 | 39 | Pending |
| NAV-06 | 39 | Pending |

**Coverage:**
- v1.9.3 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-04 — Phase 38 complete (6 DOC requirements)*
