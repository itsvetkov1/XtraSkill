# THREAD-006: Add Search and Filter for Thread List

**Priority:** High
**Status:** Open
**Component:** Thread List Screen

---

## User Story

As a user,
I want to search and sort my conversation threads,
So that I can find specific discussions in large projects.

---

## Problem

Thread List only shows items with pull-to-refresh. No search or sort. Projects with many threads become unmanageable.

---

## Acceptance Criteria

- [ ] Search bar filters threads by title (real-time)
- [ ] Sort options: Newest, Oldest, Alphabetical
- [ ] Search persists until cleared
- [ ] Empty search result shows "No threads matching '{query}'"

---

## Technical References

- `frontend/lib/screens/threads/thread_list_screen.dart`
