# NAV-001: Extend Breadcrumb to Include Thread Context

**Priority:** High
**Status:** Done

**Resolution:** Already implemented. Breadcrumb at `breadcrumb_bar.dart:145` handles `/projects/:id/threads/:threadId` route with full path: "Projects > {Project} > Threads > {Thread}". Also handles `/chats/:threadId` and `/assistant/:threadId`.
**Component:** Breadcrumb Bar

---

## User Story

As a user,
I want breadcrumbs to show my full location including the current thread,
So that I can navigate back to any level.

---

## Problem

Breadcrumb stops at Project Detail. In ConversationScreen, user can't navigate directly to Threads tab.

---

## Acceptance Criteria

- [ ] Breadcrumb in ConversationScreen: "Projects > {Project} > Threads > {Thread}"
- [ ] Each segment is clickable and navigates to that route
- [ ] Truncation works gracefully on mobile

---

## Technical References

- `frontend/lib/widgets/breadcrumb_bar.dart`
- Depends on: US-004 (unique conversation URLs)
