# DOC-005: Document Maximum File Size Enforcement

**Priority:** Medium
**Status:** Open
**Component:** Document Upload Screen

---

## User Story

As a user,
I want clear feedback if my file is too large,
So that I understand why upload failed.

---

## Problem

Spec mentions "1MB" limit but doesn't document the error state UX.

---

## Acceptance Criteria

- [ ] Document error state: "File too large. Maximum size is 1MB."
- [ ] Error shown before upload attempt (client-side validation)
- [ ] Snackbar or inline error message
- [ ] File selection cleared, user can try again

---

## Technical References

- `frontend/lib/screens/documents/document_upload_screen.dart`
