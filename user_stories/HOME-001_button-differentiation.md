# HOME-001: Differentiate Home Screen Action Buttons

**Priority:** Medium
**Status:** Open
**Component:** Home Screen

---

## User Story

As a user,
I want the two home screen buttons to do different things,
So that I understand which to click.

---

## Problem

"Start Conversation" and "Browse Projects" both navigate to `/projects`. Redundant and confusing.

---

## Acceptance Criteria

- [ ] "Start Conversation" → `/projects` with most recent project auto-selected, Threads tab active
- [ ] OR "Start Conversation" → opens project picker dialog, then navigates to Threads tab
- [ ] "Browse Projects" → `/projects` (current behavior)
- [ ] Button labels/icons clearly indicate different actions

---

## Technical References

- `frontend/lib/screens/home_screen.dart`
