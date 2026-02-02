# UX-003: Project-less Chats with Global Chats Menu

**Priority:** High
**Status:** Done (v1.9)
**Component:** Chat Organization, Navigation
**Created:** 2026-01-31

---

## User Story

As a user who wants to quickly start a conversation,
I want to create chats without selecting a project first,
So that I can get immediate AI assistance without workflow interruption.

As a user managing multiple conversations,
I want a central "Chats" section showing all my conversations,
So that I can easily find and resume any chat regardless of project association.

---

## Current Behavior

- Chats (threads) can only be created within a project
- User must: Navigate to Projects → Select/Create Project → Create Thread
- No way to start a quick conversation without project context
- Threads are only visible within their parent project

---

## Desired Behavior

### 1. Global "Chats" Section in Left Menu

New menu section showing ALL chats across the system:

```
┌─────────────────────┐
│ 🏠 Home             │
│ 📁 Projects         │
│ 💬 Chats            │  ← NEW SECTION
│ ⚙️ Settings         │
└─────────────────────┘
```

### 2. Chats List Format

Each chat displays with project association:

```
┌─────────────────────────────────┐
│ 💬 Chats                        │
├─────────────────────────────────┤
│ Login Flow Discussion [Acme]    │  ← Has project
│ API Requirements [Acme]         │  ← Has project
│ Quick Question [No Project]     │  ← No project
│ Feature Ideas [Beta Corp]       │  ← Has project
│ Random Thoughts [No Project]    │  ← No project
└─────────────────────────────────┘
```

### 3. New Chat Creation

**Entry points:**
- "New Chat" button in Chats section
- "New Chat" button on Home page

**Flow:**
1. User clicks "New Chat"
2. New chat created with no project association
3. User lands in conversation view
4. Chat appears in Chats list as "[No Project]"

### 4. Chat Detail View

When viewing a chat, show project info under title:

```
┌─────────────────────────────────────────┐
│ Login Flow Discussion                   │
│ 📁 Acme Project                         │  ← Project link (clickable)
├─────────────────────────────────────────┤
│                                         │
│  [Conversation messages...]             │
│                                         │
└─────────────────────────────────────────┘
```

For project-less chats:

```
┌─────────────────────────────────────────┐
│ Quick Question                          │
│ No Project    [+ Add to Project]        │  ← Add button
├─────────────────────────────────────────┤
│                                         │
│  [Conversation messages...]             │
│                                         │
└─────────────────────────────────────────┘
```

### 5. Add to Project (One-Way)

**Locations:**
- Button in chat header (always visible for project-less chats)
- Three-dot options menu

**Flow:**
1. User clicks "Add to Project"
2. Modal shows list of user's projects
3. User selects project
4. Chat becomes associated with project
5. Chat list updates: "Quick Question [Selected Project]"
6. Button disappears (association is permanent)

**Rules:**
- Can only add, never remove project association
- Once associated, chat appears in both Chats menu AND project's thread list

---

## Acceptance Criteria

### Chats Menu Section
- [ ] "Chats" section appears in left navigation menu
- [ ] Chats section shows ALL user's chats (with and without projects)
- [ ] Each chat shows title with project name in brackets
- [ ] Project-less chats show "[No Project]" in brackets
- [ ] Chats sorted by most recent activity (newest first)
- [ ] Clicking a chat navigates to conversation view

### New Chat Creation
- [ ] "New Chat" button in Chats section header
- [ ] "New Chat" button on Home page
- [ ] New chat created without project association
- [ ] User taken directly to conversation view after creation
- [ ] New chat appears in Chats list immediately

### Chat Detail View
- [ ] Project name displayed under chat title (clickable, navigates to project)
- [ ] "No Project" displayed for unassociated chats
- [ ] "Add to Project" button visible for project-less chats (header location)
- [ ] "Add to Project" option in three-dot menu for project-less chats

### Add to Project
- [ ] Clicking "Add to Project" opens project selection modal
- [ ] Modal shows all user's projects
- [ ] Selecting project associates chat with that project
- [ ] Chat list updates to show new project association
- [ ] "Add to Project" button/option disappears after association
- [ ] Chat now appears in project's thread list as well
- [ ] Association is permanent (no remove option)

### Data Integrity
- [ ] Project-less chats work with all AI providers
- [ ] Message history preserved when adding to project
- [ ] Chat accessible from both Chats menu and project after association

---

## Technical Notes

### Database Changes

**Thread model update:**
- `project_id` becomes nullable (currently required)
- Add migration for existing data (all existing threads keep their project_id)

**API changes:**
- `POST /api/threads` - create thread without project_id
- `PATCH /api/threads/{id}/project` - associate thread with project
- `GET /api/threads` - new endpoint for all user's threads (across projects)

### Frontend Changes

**Files likely affected:**
- `frontend/lib/widgets/app_drawer.dart` or navigation - add Chats section
- `frontend/lib/screens/chats/` - new screen for global chats list
- `frontend/lib/screens/conversation/conversation_screen.dart` - project info display
- `frontend/lib/models/thread.dart` - projectId becomes nullable
- `frontend/lib/services/thread_service.dart` - new endpoints
- `frontend/lib/screens/home/home_screen.dart` - add New Chat button

**New widgets needed:**
- `ChatsScreen` - list of all chats
- `AddToProjectModal` - project selection dialog
- `ChatProjectInfo` - displays project or "No Project" with add button

### State Management

- New `GlobalChatsProvider` or extend existing `ThreadProvider`
- Must handle threads with and without projects
- Consider caching/pagination for users with many chats

---

## Dependencies

- Requires backend API changes (new endpoints, nullable project_id)
- May impact existing thread-related features (verify no regressions)

---

## Edge Cases

1. **User has no projects** - "Add to Project" shows empty state with "Create Project" option
2. **Chat already in project** - No "Add to Project" option shown
3. **Project deleted** - Chat remains but shows "[Deleted Project]" or becomes project-less
4. **Offline creation** - Queue chat creation, sync when online

---

## Migration Considerations

- Existing threads all have project associations - no migration needed for data
- UI changes are additive - existing project→thread flow still works
- New Chats menu is additional access point, not replacement

---

*Created: 2026-01-31*
