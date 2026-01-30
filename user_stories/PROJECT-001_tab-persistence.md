# PROJECT-001: Document Tab State Persistence

**Priority:** Medium
**Status:** Open
**Component:** Project Detail Screen

---

## User Story

As a user,
I want the app to remember which tab I was viewing in a project,
So that navigation feels consistent.

---

## Problem

Document doesn't specify tab persistence behavior when navigating away and back.

---

## Acceptance Criteria

- [ ] Document expected behavior in spec
- [ ] Implement: Remember last selected tab per project (stored in ProjectProvider or local)
- [ ] OR: Always default to Documents tab (simpler, document this choice)

---

## Technical References

- `frontend/lib/screens/projects/project_detail_screen.dart`
- `frontend/lib/providers/project_provider.dart`
