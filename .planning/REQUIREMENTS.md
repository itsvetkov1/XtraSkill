# Requirements: BA Assistant v1.9.3

**Defined:** 2026-02-04
**Core Value:** Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## v1.9.3 Requirements

Requirements for Document & Navigation Polish milestone.

### Document Preview (DOC)

- [ ] **DOC-01**: After file selection, preview dialog shows filename
- [ ] **DOC-02**: Preview dialog shows file size (human readable: KB/MB)
- [ ] **DOC-03**: Preview dialog shows first 20 lines of content
- [ ] **DOC-04**: Preview uses monospace font consistent with Document Viewer
- [ ] **DOC-05**: Cancel button clears selection and closes dialog
- [ ] **DOC-06**: Upload button proceeds with upload

### Document Download (DOWNLOAD)

- [ ] **DOWNLOAD-01**: Download icon button in Document Viewer AppBar
- [ ] **DOWNLOAD-02**: Download option in document list context menu
- [ ] **DOWNLOAD-03**: Download uses original filename
- [ ] **DOWNLOAD-04**: Success snackbar: "Downloaded {filename}"
- [ ] **DOWNLOAD-05**: Works on web, Android, and iOS

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
| DOC-01 | TBD | Pending |
| DOC-02 | TBD | Pending |
| DOC-03 | TBD | Pending |
| DOC-04 | TBD | Pending |
| DOC-05 | TBD | Pending |
| DOC-06 | TBD | Pending |
| DOWNLOAD-01 | TBD | Pending |
| DOWNLOAD-02 | TBD | Pending |
| DOWNLOAD-03 | TBD | Pending |
| DOWNLOAD-04 | TBD | Pending |
| DOWNLOAD-05 | TBD | Pending |
| NAV-01 | TBD | Pending |
| NAV-02 | TBD | Pending |
| NAV-03 | TBD | Pending |
| NAV-04 | TBD | Pending |
| NAV-05 | TBD | Pending |
| NAV-06 | TBD | Pending |

**Coverage:**
- v1.9.3 requirements: 17 total
- Mapped to phases: 0
- Unmapped: 17

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-04 after initial definition*
