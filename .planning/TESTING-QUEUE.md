# Testing Queue

Testing points collected during development for manual verification when available.

---

## Phase 9: Deletion Flows with Undo

**Status:** Pending user testing
**Collected:** 2026-01-30

### Test Environment Setup

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && flutter run -d chrome`
3. Log in and create a test project with a thread and document

### Test Cases

#### TC-09-01: Project Deletion with Undo

1. Open a test project
2. Click delete button (trash icon) in project header
3. **Expected:** Confirmation dialog with cascade warning "This will delete all threads and documents in this project."
4. Click "Delete"
5. **Expected:** Project disappears, SnackBar shows with "Undo" action
6. Click "Undo" within 10 seconds
7. **Expected:** Project reappears in list with all data intact

#### TC-09-02: Project Deletion Permanent

1. Delete a project and confirm
2. Do NOT click Undo
3. Wait 10+ seconds for timer to expire
4. **Expected:** Project is permanently deleted (refresh page to verify)

#### TC-09-03: Thread Deletion

1. Create a test project with a thread containing messages
2. Go to Threads tab
3. Click the three-dot menu on a thread
4. Select "Delete"
5. **Expected:** Confirmation dialog with "This will delete all messages in this thread."
6. Confirm deletion
7. **Expected:** Thread disappears, SnackBar shows "Undo"
8. Test undo works

#### TC-09-04: Document Deletion

1. Upload a document to a project
2. Go to Documents tab
3. Click the three-dot menu on a document
4. Select "Delete"
5. **Expected:** Confirmation dialog (no cascade message - documents have no children)
6. Confirm deletion
7. **Expected:** Document disappears with undo option

#### TC-09-05: Message Deletion

1. Open a thread with messages
2. Long-press on a message
3. **Expected:** Bottom sheet appears with "Delete message" option
4. Tap "Delete message"
5. **Expected:** Confirmation dialog appears
6. Confirm
7. **Expected:** Message disappears with undo option

#### TC-09-06: Rollback on Backend Error (Optional)

1. Start a deletion but don't click undo
2. Stop the backend while undo timer is running
3. Wait for timer to expire (backend call fails)
4. **Expected:** Item reappears with error message

### Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-09-01 | Pending | |
| TC-09-02 | Pending | |
| TC-09-03 | Pending | |
| TC-09-04 | Pending | |
| TC-09-05 | Pending | |
| TC-09-06 | Pending | |

**Tested by:**
**Date:**
**Issues found:**

---

## Phase 15: Route Architecture

**Status:** Pending user testing
**Collected:** 2026-01-31

### Test Environment Setup

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && flutter run -d chrome`
3. Log in and have at least one project with threads

### Test Cases

#### TC-15-01: 404 Error Page

1. Navigate to an invalid URL: `http://localhost:PORT/invalid/random/path`
2. **Expected:** 404 page displays with:
   - Error icon
   - "404 - Page Not Found" heading
   - Message showing the attempted path
   - "Go to Home" button
3. Click "Go to Home"
4. **Expected:** Navigates to /home

#### TC-15-02: Thread URL Structure

1. Navigate to Projects
2. Click on a project to open it
3. Click on a thread/conversation
4. **Expected:** URL bar shows `/projects/[project-id]/threads/[thread-id]`

#### TC-15-03: Thread Breadcrumbs

1. From a thread/conversation view
2. **Expected:** Breadcrumbs show "Projects > [Project Name] > [Thread Title]"
3. Click "Projects" in breadcrumb
4. **Expected:** Navigates to /projects
5. Navigate back to thread
6. Click "[Project Name]" in breadcrumb
7. **Expected:** Navigates to project detail page

#### TC-15-04: Page Refresh on Thread

1. Navigate to a thread (URL shows /projects/.../threads/...)
2. Press F5 to refresh
3. **Expected:** Page reloads (may require re-login, but URL structure preserved)

### Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-15-01 | Pending | |
| TC-15-02 | Pending | |
| TC-15-03 | Pending | |
| TC-15-04 | Pending | |

**Tested by:**
**Date:**
**Issues found:**

---

*Add new phases below as development continues*
