# SETTINGS-001: Show Authentication Provider

**Priority:** Medium
**Status:** Done (v1.6)
**Component:** Settings Screen

---

## User Story

As a user,
I want to see which account (Google/Microsoft) I'm logged in with,
So that I know which credentials to use.

---

## Problem

Settings shows email and name but not the OAuth provider used.

---

## Acceptance Criteria

- [ ] Provider icon (Google G / Microsoft logo) shown next to avatar
- [ ] OR subtitle text: "Signed in with Google" / "Signed in with Microsoft"

---

## Technical References

- `frontend/lib/screens/settings_screen.dart`
- `frontend/lib/providers/auth_provider.dart`
