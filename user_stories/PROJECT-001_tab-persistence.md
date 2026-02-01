# PROJECT-001: Document Tab State Persistence

**Priority:** Medium
**Status:** Wont Do
**Component:** Project Detail Screen
**Closed:** 2026-01-31
**Reason:** Obsolete — UX-002 removes the tab structure entirely. Documents become a collapsible column, Threads are always the primary view.

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
