# DOC-001: Add Document Preview Before Upload

**Priority:** High
**Status:** Done
**Component:** Document Upload Screen

---

## User Story

As a user,
I want to preview a file before uploading,
So that I can verify I selected the correct document.

---

## Problem

File selection immediately triggers upload. No confirmation or preview step.

---

## Acceptance Criteria

- [ ] After file selection, show preview: filename, size, first ~20 lines
- [ ] "Upload" button confirms and starts upload
- [ ] "Cancel" button clears selection
- [ ] Preview uses monospace font consistent with Document Viewer

---

## Technical References

- `frontend/lib/screens/documents/document_upload_screen.dart`
