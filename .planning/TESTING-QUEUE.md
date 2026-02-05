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

## Phase 18: v1.7 URL & Deep Links Validation

**Status:** Pending user testing
**Collected:** 2026-01-31

### Test Environment Setup

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && flutter run -d chrome`
3. Use incognito window for clean state between auth tests
4. Have at least one project with threads for testing

### Test Cases

Full test matrix available in `.planning/phases/18-validation/18-VALIDATION.md`

#### Critical Tests

##### VAL-16 (ERR-04): Login with returnUrl to deleted resource

1. Create a project, note its ID
2. Delete the project
3. In incognito, access `/projects/{deleted-id}` while logged out
4. Complete OAuth login
5. **Expected:** See "Project not found" state (not crash)

##### SEC-01: Open redirect prevention (external URL)

1. In incognito, access `/login`
2. In DevTools Console: `sessionStorage.setItem('returnUrl', 'https://evil.com')`
3. Complete OAuth login
4. **Expected:** Land on `/home` (external URL rejected)

##### SEC-02: Open redirect prevention (malformed path)

1. In incognito, access `/login`
2. In DevTools Console: `sessionStorage.setItem('returnUrl', 'not-a-valid-path')`
3. Complete OAuth login
4. **Expected:** Land on `/home` (malformed URL rejected)

#### URL Preservation Tests

| Test ID | Requirement | Description |
|---------|-------------|-------------|
| VAL-01 | ROUTE-01 | Thread URL shows `/projects/:id/threads/:threadId` |
| VAL-02 | ROUTE-02 | Browser back/forward navigation works |
| VAL-03 | ROUTE-03 | Invalid route shows 404 page |
| VAL-04 | ROUTE-04 | ConversationScreen loads from URL params |
| VAL-05 | URL-01 | Page refresh preserves URL (authenticated) |
| VAL-06 | URL-02 | URL preserved through OAuth redirect |
| VAL-07 | URL-03 | Settings refresh returns to /settings |
| VAL-08 | URL-04 | Project detail refresh returns correctly |
| VAL-09 | AUTH-01 | Redirect captures returnUrl query param |
| VAL-10 | AUTH-02 | Login completes to stored returnUrl |
| VAL-11 | AUTH-03 | Direct login goes to /home |
| VAL-12 | AUTH-04 | returnUrl cleared after use |
| VAL-13 | ERR-01 | Invalid route shows 404 with nav options |
| VAL-14 | ERR-02 | Deleted project shows "Project not found" |
| VAL-15 | ERR-03 | Deleted thread shows "Thread not found" |
| VAL-16 | ERR-04 | Deleted resource via returnUrl handled |

### Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| VAL-01 | Pending | |
| VAL-02 | Pending | |
| VAL-03 | Pending | |
| VAL-04 | Pending | |
| VAL-05 | Pending | |
| VAL-06 | Pending | |
| VAL-07 | Pending | |
| VAL-08 | Pending | |
| VAL-09 | Pending | |
| VAL-10 | Pending | |
| VAL-11 | Pending | |
| VAL-12 | Pending | |
| VAL-13 | Pending | |
| VAL-14 | Pending | |
| VAL-15 | Pending | |
| VAL-16 | Pending | |
| SEC-01 | Pending | |
| SEC-02 | Pending | |

**Tested by:**
**Date:**
**Issues found:**

---

## Phase 22: LLM Provider Selection UI

**Status:** Pending user testing
**Collected:** 2026-01-31
**Bug fix included:** 317298e (provider not passed to createThread)

### Test Environment Setup

1. Start backend with API keys configured:
   ```bash
   cd backend
   # Set environment variables for providers you want to test:
   # ANTHROPIC_API_KEY=your-claude-key (required)
   # GOOGLE_API_KEY=your-gemini-key (optional)
   # DEEPSEEK_API_KEY=your-deepseek-key (optional)
   python run.py
   ```
2. Start frontend: `cd frontend && flutter run -d chrome`
3. Log in and have at least one project

### Test Cases

#### TC-22-01: Provider Selection in Settings

1. Navigate to Settings
2. Find "Preferences" section
3. **Expected:** "Default AI Provider" dropdown with Claude/Gemini/DeepSeek options
4. Each option shows colored icon + provider name

#### TC-22-02: Provider Preference Persistence

1. In Settings, change provider to Gemini
2. Close app completely (stop flutter run)
3. Restart app: `flutter run -d chrome`
4. Navigate to Settings
5. **Expected:** Gemini is still selected (persisted via SharedPreferences)

#### TC-22-03: New Conversation Uses Selected Provider

1. In Settings, select DeepSeek as default
2. Navigate to a project
3. Create new conversation
4. Send a message
5. **Expected:** Response comes from DeepSeek API (check backend logs or response style)
6. Check backend logs for: `Creating adapter for provider: deepseek`

#### TC-22-04: Provider Indicator Shows Thread's Provider

1. Create a conversation with Gemini selected
2. Note: indicator below messages should show Gemini (blue icon)
3. Go to Settings, change to DeepSeek
4. Return to the existing Gemini conversation
5. **Expected:** Indicator still shows Gemini (thread's bound provider, not current default)

#### TC-22-05: Multiple Providers in Same Project

1. Create conversation A with Claude (orange indicator)
2. Change default to Gemini
3. Create conversation B with Gemini (blue indicator)
4. Switch between A and B
5. **Expected:** Each shows correct provider indicator

#### TC-22-06: Provider Without API Key Configured

1. Ensure DEEPSEEK_API_KEY is NOT set in backend environment
2. Select DeepSeek in Settings
3. Create new conversation, send message
4. **Expected:** Error message about missing API key (not crash)

### Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-22-01 | Pass | Provider dropdown visible in Settings |
| TC-22-02 | Pass | Persistence works |
| TC-22-03 | Pass | New conversations use selected provider (bug fixed: 317298e) |
| TC-22-04 | Pending | |
| TC-22-05 | Pending | |
| TC-22-06 | Pending | |

**Tested by:** User
**Date:** 2026-01-31
**Issues found:** Bug fixed - provider not passed to createThread (317298e)

---

## Phase 40: Prompt Engineering Fixes (Artifact Deduplication Layers 1+2)

**Status:** Pending user testing
**Collected:** 2026-02-05

### Test Environment Setup

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && flutter run -d chrome`
3. Log in and open a project with existing threads

### Test Cases

#### TC-40-01: Multi-Artifact Deduplication Test

1. Create a new conversation thread
2. Generate 3 different artifacts using preset buttons (e.g., User Stories, Acceptance Criteria, Requirements Doc)
3. Send a regular chat message (e.g., "Thank you, looks good")
4. **Expected:** No artifacts are auto-generated from step 3 — only a chat response appears. The 3 existing artifacts remain unchanged.

#### TC-40-02: Escape Hatch Test (Regenerate Request)

1. Create a conversation with 1 existing artifact (e.g., User Stories)
2. Send message: "Regenerate the user stories with more detail about the login flow"
3. **Expected:** A NEW artifact IS generated (not blocked by dedup rule). The artifact contains enhanced detail about the login flow.

#### TC-40-03: Regular Chat Regression Test

1. Create a new conversation with no artifacts
2. Send several chat messages asking discovery questions (e.g., "What information do you need about my project?")
3. **Expected:** BA assistant asks one question at a time (unchanged behavior). Responses are conversational and helpful. No changes to non-artifact chat behavior.

### Results

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-40-01 | Pending | |
| TC-40-02 | Pending | |
| TC-40-03 | Pending | |

**Tested by:**
**Date:**
**Issues found:**

---

*Add new phases below as development continues*
