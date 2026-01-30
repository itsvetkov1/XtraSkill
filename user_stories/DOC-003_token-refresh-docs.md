# DOC-003: Document OAuth Token Refresh Behavior

**Priority:** Medium
**Status:** Open
**Component:** Authentication (Documentation)

---

## Description

Document that OAuth tokens auto-refresh silently in the background. Users should never be interrupted for re-authentication during normal use.

---

## Acceptance Criteria

- [ ] Add to spec under Authentication section or new "Session Management" section
- [ ] Text: "JWT tokens are automatically refreshed before expiration. Users remain authenticated without interruption."
- [ ] Document edge case: If refresh fails (revoked access), user sees friendly re-auth prompt

---

## Technical References

- `frontend/lib/services/auth_service.dart`
- `.planning/APP-FEATURES-AND-FLOWS.md` (Authentication section)
