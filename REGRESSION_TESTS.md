# Regression Test Suite

**Project:** Business Analyst Assistant
**Last Updated:** 2026-02-02

This document contains essential manual test cases for verifying core functionality. Run these tests before releases and after major changes.

---

## Quick Setup

```bash
# Backend
cd backend && python run.py

# Frontend (new terminal)
cd frontend && flutter run -d chrome
```

---

## Test Results Log

| Date | Tester | Version | Passed | Failed | Notes |
|------|--------|---------|--------|--------|-------|
| | | | | | |

---

## Chat Features

### TC-CHAT-001: Create Project-less Chat from Home

**Pre-conditions:**
- User is logged in
- On Home screen

**Steps:**
1. Click "New Chat" button on Home screen
2. Observe navigation

**Expected Result:**
- New conversation screen opens
- No project associated (header shows "New Chat" without project name)
- Chat input is ready to type

---

### TC-CHAT-002: Create Project-less Chat from Chats Menu

**Pre-conditions:**
- User is logged in

**Steps:**
1. Click "Chats" in left navigation menu
2. Click "New Chat" button
3. Observe navigation

**Expected Result:**
- New conversation screen opens
- No project associated
- New chat appears in Chats list

---

### TC-CHAT-003: Chats List Shows All Threads

**Pre-conditions:**
- User has at least one project-based chat
- User has at least one project-less chat

**Steps:**
1. Click "Chats" in left navigation menu
2. Observe the chat list

**Expected Result:**
- Both project-based and project-less chats appear
- Project-based chats show project name badge
- Project-less chats show "No Project" badge
- List sorted by most recent activity (newest first)

---

### TC-CHAT-004: Add to Project Button Visibility

**Pre-conditions:**
- User has at least one project
- User has a project-less chat open

**Steps:**
1. Open a project-less chat
2. Look at the toolbar area (between messages and chat input)
3. Look at the three-dot menu in the app bar

**Expected Result:**
- "Add to Project" button visible in toolbar (next to LLM indicator)
- "Add to Project" option available in three-dot menu

---

### TC-CHAT-005: Add to Project Button Hidden for Project Chats

**Pre-conditions:**
- User has a chat that belongs to a project

**Steps:**
1. Navigate to a project-based chat (via Projects or Chats menu)
2. Look at the toolbar area
3. Look at the three-dot menu

**Expected Result:**
- "Add to Project" button NOT visible
- "Add to Project" option NOT in menu
- Project name visible in header/breadcrumb

---

### TC-CHAT-006: Add to Project Flow

**Pre-conditions:**
- User has at least one project
- User has a project-less chat open

**Steps:**
1. Click "Add to Project" button (toolbar or menu)
2. Observe the modal that opens
3. Select a project from the list
4. Observe the confirmation dialog
5. Click "Confirm"

**Expected Result:**
- Project picker modal shows list of user's projects
- Confirmation dialog shows: 'Add to "[Project Name]"?'
- After confirm: header updates to show project name
- "Add to Project" button and menu option disappear
- No page reload required (updates in-place)

---

### TC-CHAT-007: Add to Project Persistence

**Pre-conditions:**
- Just completed TC-CHAT-006 (chat was associated with project)

**Steps:**
1. Note which project the chat was added to
2. Refresh the page (F5 or browser refresh)
3. Navigate back to the same chat

**Expected Result:**
- Chat still shows association with the project
- Chat appears in the project's thread list
- Chat appears in global Chats list with project badge

---

### TC-CHAT-008: Add to Project - No Projects

**Pre-conditions:**
- User has NO projects (delete all if needed)
- User has a project-less chat open

**Steps:**
1. Click "Add to Project" button

**Expected Result:**
- Modal shows empty state: "No projects yet"
- Guidance text suggests creating a project first
- Can close modal without error

---

## Message Features

### TC-MSG-001: Send Message with Enter Key

**Pre-conditions:**
- User is in a conversation

**Steps:**
1. Type a message in the chat input
2. Press Enter key

**Expected Result:**
- Message sends immediately
- Input clears
- AI response begins streaming

---

### TC-MSG-002: New Line with Shift+Enter

**Pre-conditions:**
- User is in a conversation

**Steps:**
1. Type "Line 1" in chat input
2. Press Shift+Enter
3. Type "Line 2"
4. Press Enter to send

**Expected Result:**
- Shift+Enter inserts new line (input expands)
- Message displays with line break preserved
- Enter sends the multi-line message

---

### TC-MSG-003: Copy AI Response

**Pre-conditions:**
- Conversation has at least one AI response

**Steps:**
1. Hover over an AI message
2. Click the copy icon

**Expected Result:**
- Message content copied to clipboard
- Visual feedback (icon change or tooltip)
- Pasting elsewhere shows the copied text

---

### TC-MSG-004: Retry Failed Message

**Pre-conditions:**
- A message failed to send (network error or API error)

**Steps:**
1. Observe the failed message indicator
2. Click the retry button

**Expected Result:**
- Message resends
- On success: normal message appearance
- No duplicate message created

---

## Navigation Features

### TC-NAV-001: URL Preserved on Refresh

**Pre-conditions:**
- User is logged in
- User is viewing a specific conversation

**Steps:**
1. Note the URL in browser (should include project/thread IDs)
2. Press F5 or refresh the page

**Expected Result:**
- Same conversation loads after refresh
- URL remains the same
- No redirect to home page

---

### TC-NAV-002: Deep Link to Conversation

**Pre-conditions:**
- User is logged in
- User has a conversation URL copied

**Steps:**
1. Open a new browser tab
2. Paste the conversation URL
3. Navigate to it

**Expected Result:**
- Conversation loads directly
- Correct project context shown
- All messages visible

---

## Project Layout

### TC-PROJ-001: Threads Primary View

**Pre-conditions:**
- User has a project with threads and documents

**Steps:**
1. Navigate to a project (click project card)
2. Observe the default view

**Expected Result:**
- Threads list is primary view (not documents)
- Documents appear in collapsible left column
- Column is collapsed/minimized by default

---

### TC-PROJ-002: Documents Column Toggle

**Pre-conditions:**
- User is viewing a project

**Steps:**
1. Click the collapsed documents column
2. Observe it expand
3. Click to collapse again

**Expected Result:**
- Column expands to show document list
- All document operations available (upload, view, delete)
- Column collapses back to thin strip

---

## Settings

### TC-SET-001: LLM Provider Selection

**Pre-conditions:**
- User is logged in

**Steps:**
1. Navigate to Settings
2. Change the LLM provider (e.g., Claude -> Gemini)
3. Create a new chat

**Expected Result:**
- Provider selection persists
- New chats use the selected provider
- Provider indicator shows correct provider

---

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-02 | Initial test suite with Chat and core features |

---

*Test cases added during v1.9 milestone*
