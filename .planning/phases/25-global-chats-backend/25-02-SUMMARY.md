---
phase: 25
plan: 02
subsystem: frontend-navigation
tags: [chats, navigation, provider, flutter, routing]

dependency-graph:
  requires: [phase-25-01]
  provides: [global-chats-ui, new-chat-button, chats-navigation]
  affects: [user-workflow, navigation-experience]

tech-stack:
  patterns:
    - provider-pattern
    - go-router-shell-branches
    - paginated-list-ui

file-tracking:
  key-files:
    created:
      - frontend/lib/providers/chats_provider.dart
      - frontend/lib/screens/chats_screen.dart
    modified:
      - frontend/lib/models/thread.dart
      - frontend/lib/services/thread_service.dart
      - frontend/lib/screens/conversation/conversation_screen.dart
      - frontend/lib/widgets/responsive_scaffold.dart
      - frontend/lib/main.dart
      - frontend/lib/screens/home_screen.dart

decisions:
  - id: SERVICE-PATTERN
    choice: "Add methods to existing ThreadService instead of new ApiService"
    reason: "Project uses per-domain services, not monolithic ApiService"
  - id: NAV-INDEX
    choice: "Chats at index 1 (after Home, before Projects)"
    reason: "High-frequency action should be easily accessible"

metrics:
  duration: "4m 15s"
  completed: "2026-02-01"
---

# Phase 25 Plan 02: Frontend Global Chats Integration Summary

Frontend Chats navigation section and New Chat functionality with full routing support.

## One-liner

Chats navigation at index 1 with ChatsProvider, ChatsScreen, and New Chat buttons on Home and Chats pages.

## Changes Made

### Task 1: Add API service methods and update Thread model

**Files modified:**
- `frontend/lib/models/thread.dart`
- `frontend/lib/services/thread_service.dart`

**Changes:**
1. Made Thread.projectId nullable for project-less threads
2. Added Thread.projectName for global listing display
3. Added Thread.lastActivityAt for activity-based sorting
4. Added Thread.hasProject getter for convenience
5. Added PaginatedThreads response class for paginated API responses
6. Added ThreadService.getGlobalThreads() for paginated global thread listing
7. Added ThreadService.createGlobalThread() for creating threads with/without project

**Commit:** `9bdedd8`

### Task 2: Create ChatsProvider and ChatsScreen

**Files created:**
- `frontend/lib/providers/chats_provider.dart`
- `frontend/lib/screens/chats_screen.dart`

**Changes:**
1. ChatsProvider manages global thread state with load, pagination, createNewChat
2. ChatsScreen displays thread list with project badges
3. New Chat button in header creates project-less threads
4. Empty state with centered New Chat button
5. Pull-to-refresh and infinite scroll pagination
6. Navigation to project threads (/projects/:id/threads/:tid) or global chats (/chats/:id)

**Commit:** `e430b6e`

### Task 3: Make ConversationScreen.projectId optional

**Files modified:**
- `frontend/lib/screens/conversation/conversation_screen.dart`

**Changes:**
1. Changed projectId from required String to optional String?
2. Updated not-found back navigation to go to /chats for project-less threads
3. Enables conversation view for project-less threads

**Commit:** `95c6df7`

### Task 4: Add navigation and routes for Chats

**Files modified:**
- `frontend/lib/widgets/responsive_scaffold.dart`
- `frontend/lib/main.dart`

**Changes:**
1. Added Chats destination to navigation rail/drawer at index 1 (chat_bubble icon)
2. Registered ChatsProvider in MultiProvider
3. Updated _getSelectedIndex: /chats -> 1, /projects -> 2, /settings -> 3
4. Added /chats branch with ChatsScreen as root
5. Added /chats/:threadId nested route for project-less thread conversations

**Commit:** `583c67d`

### Task 5: Add New Chat button to Home screen

**Files modified:**
- `frontend/lib/screens/home_screen.dart`

**Changes:**
1. Added ChatsProvider import
2. Replaced "Start Conversation" with "New Chat" button
3. Creates project-less thread via ChatsProvider.createNewChat()
4. Navigates to /chats/{threadId} for conversation

**Commit:** `961db0d`

## Verification Results

| Check | Status |
|-------|--------|
| Flutter analyze (no errors) | PASS |
| Thread model nullable projectId | PASS |
| PaginatedThreads class exists | PASS |
| ThreadService.getGlobalThreads() exists | PASS |
| ThreadService.createGlobalThread() exists | PASS |
| ChatsProvider loadThreads, createNewChat | PASS |
| ChatsScreen with list and empty state | PASS |
| ConversationScreen.projectId optional | PASS |
| Navigation rail has Chats at index 1 | PASS |
| /chats route registered | PASS |
| /chats/:threadId route registered | PASS |
| Home screen New Chat button | PASS |

## User Story Coverage

| Story ID | Requirement | Status |
|----------|-------------|--------|
| CHATS-01 | Chats section in left navigation | DONE |
| CHATS-02 | Shows all user threads | DONE |
| CHATS-03 | Project badges on threads | DONE |
| CHATS-04 | Sorted by recent activity | DONE |
| CHATS-05 | New Chat in Chats section | DONE |
| CHATS-06 | New Chat on Home page | DONE |
| CHATS-07 | Navigate to conversation view | DONE |

## Decisions Made

1. **SERVICE-PATTERN:** Added methods to existing ThreadService instead of creating new ApiService. The project follows per-domain service pattern (auth_service, project_service, thread_service, etc.).

2. **NAV-INDEX:** Placed Chats at navigation index 1 (after Home, before Projects) for quick access to frequent action.

## Deviations from Plan

**[Rule 3 - Blocking] API service path mismatch**
- **Found during:** Task 1 planning
- **Issue:** Plan referenced `api_service.dart` which doesn't exist. Project uses separate service files.
- **Fix:** Added methods to `thread_service.dart` instead, following existing patterns.
- **Files modified:** `thread_service.dart`

## Next Phase Readiness

Phase 25 complete. UX-003 (Project-less chats with global Chats menu) fully implemented:
- Backend: GET/POST /threads endpoints (25-01)
- Frontend: Chats navigation, ChatsScreen, New Chat buttons (25-02)

Ready for next phase (thread search or other UX v1.9 features).
