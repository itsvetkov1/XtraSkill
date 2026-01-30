# Business Analyst Assistant - Features & User Flows

**Version:** Beta v1.5
**Last Updated:** 2026-01-30

This document maps every screen, button, feature, and user flow in the application.

---

## Table of Contents

1. [Application Overview](#application-overview)
2. [Screen Map](#screen-map)
3. [User Flows](#user-flows)
4. [Screen Details](#screen-details)
5. [Reusable Widgets](#reusable-widgets)
6. [Button Reference](#button-reference)
7. [State Management](#state-management)

---

## Application Overview

### Platform Support
- Web (Chrome, Firefox, Safari, Edge)
- Android (native Flutter app)
- iOS (native Flutter app)

### Responsive Breakpoints
| Width | Layout | Navigation Style |
|-------|--------|------------------|
| < 600px | Mobile | Hamburger menu with Drawer |
| 600-899px | Tablet | Collapsed NavigationRail (icons only) |
| ≥ 900px | Desktop | Extended/Collapsible NavigationRail |

### Authentication
- Google OAuth 2.0
- Microsoft OAuth 2.0
- JWT session management with secure token storage

---

## Screen Map

### Route Structure

```
/splash          → SplashScreen (loading state)
/login           → LoginScreen (authentication)
/auth/callback   → CallbackScreen (OAuth redirect handler)

[Authenticated Shell - ResponsiveScaffold wrapper]
├── /home        → HomeScreen (Branch 0)
├── /projects    → ProjectListScreen (Branch 1)
│   └── /projects/:id → ProjectDetailScreen
│       ├── Documents Tab → DocumentListScreen
│       │   ├── Upload → DocumentUploadScreen
│       │   └── View → DocumentViewerScreen
│       └── Threads Tab → ThreadListScreen
│           └── Thread → ConversationScreen
└── /settings    → SettingsScreen (Branch 2)
```

### Route Guard Logic
| Condition | Redirect |
|-----------|----------|
| Unauthenticated + accessing protected route | → `/login` |
| Authentication loading | → `/splash` |
| Authenticated + on splash/login | → `/home` |
| Auth callback success | → `/home` |

---

## User Flows

### Flow 1: New User Onboarding

```
1. User opens app
   └── /splash (shows loading indicator)
       └── Auth check fails (not logged in)
           └── /login

2. User taps "Sign in with Google" or "Sign in with Microsoft"
   └── OAuth provider popup opens
       └── User authenticates with provider
           └── /auth/callback (processing)
               └── Token extracted and validated
                   └── /home (authenticated)

3. User sees Home screen
   └── Personalized greeting "Welcome back, {name}"
   └── Action buttons: "Start Conversation", "Browse Projects"
   └── Empty recent projects section

4. User taps "Browse Projects"
   └── /projects (empty state)
       └── EmptyState: "No projects yet"
       └── Button: "Create Project"

5. User taps "Create Project"
   └── Dialog opens
       └── User enters project name and description
           └── Taps "Create"
               └── Project appears in list
                   └── Taps project card
                       └── /projects/:id (Project Detail)
```

### Flow 2: Document Upload & Context Building

```
1. User navigates to Project Detail
   └── /projects/:id
       └── Tabs: Documents | Threads

2. User views Documents tab (empty)
   └── EmptyState: "No documents yet"
   └── Button: "Upload Document"

3. User taps "Upload Document" (or FAB)
   └── DocumentUploadScreen
       └── Taps "Select File"
           └── File picker opens
               └── User selects .txt or .md file
                   └── Upload progress shown
                       └── Success: "Document uploaded"
                           └── Auto-closes to Documents tab

4. Document appears in list
   └── Shows: filename, upload date
   └── Tap to view content
   └── Three-dot menu for View/Delete
```

### Flow 3: AI-Assisted Requirements Discovery

```
1. User navigates to Project Detail → Threads tab
   └── /projects/:id
       └── Tabs: Documents | Threads (selected)

2. User taps FAB "New Conversation"
   └── ThreadCreateDialog opens
       └── Optional: Enter thread title
           └── Taps "Create"
               └── Thread created
                   └── Auto-opens ConversationScreen

3. Conversation starts (empty state)
   └── Shows: "Start a conversation"
   └── Mode selector chips displayed:
       ├── "Meeting Mode" (for live discovery)
       └── "Document Refinement" (for async work)

4. User taps mode chip (e.g., "Meeting Mode")
   └── AI responds with opening question
       └── Streaming response visible in real-time

5. User types message in chat input
   └── Taps send button
       └── Message appears in chat
           └── AI responds (streaming)
               └── May show "Searching documents..." status
                   └── AI references uploaded documents if relevant

6. Conversation continues...
   └── User describes features
   └── AI asks clarifying questions
   └── AI identifies edge cases proactively
   └── AI generates requirements incrementally

7. User requests artifact
   └── Types: "Generate user stories" or "Create BRD"
       └── AI generates structured artifact
           └── User can copy content
```

### Flow 4: Theme Management

```
1. User navigates to Settings
   └── /settings (via sidebar or navigation)

2. User sees Appearance section
   └── "Dark Mode" toggle switch

3. User taps toggle
   └── Theme changes immediately (no page reload)
   └── Preference saved to device storage

4. User closes app completely

5. User reopens app
   └── App launches directly in dark mode
   └── No white flash during startup
```

### Flow 5: Resource Deletion with Undo

```
1. User wants to delete a project
   └── /projects/:id (Project Detail)
       └── Taps delete icon (trash) in header

2. Confirmation dialog appears
   └── Shows: "Delete this project?"
   └── Shows cascade info: "This will delete X threads and Y documents"

3. User taps "Delete"
   └── Project removed from UI immediately (optimistic)
   └── SnackBar appears: "Project deleted" with "Undo" action
   └── User navigates to /projects (redirected automatically)

4a. User taps "Undo" within 10 seconds
    └── Project restored
    └── SnackBar: "Restored"

4b. User does nothing for 10 seconds
    └── Deletion committed to backend
    └── Project permanently removed
```

### Flow 6: Profile & Logout

```
1. User navigates to Settings
   └── /settings

2. User views Account section
   └── Profile tile shows:
       ├── Avatar with initials
       ├── Display name (from OAuth)
       └── Email address

3. User views Usage section
   └── Token budget progress bar
   └── Shows: "$X.XX / $50.00 used (Y%)"

4. User taps "Log Out"
   └── Confirmation dialog: "Are you sure?"

5. User taps "Log Out" in dialog
   └── Session cleared
   └── Redirected to /login
```

### Flow 7: Navigation & Breadcrumbs

```
1. User on Home screen
   └── Sidebar shows: Home (highlighted) | Projects | Settings

2. User taps "Projects" in sidebar
   └── /projects
   └── Sidebar shows: Home | Projects (highlighted) | Settings
   └── Breadcrumb: "Projects"

3. User taps a project card
   └── /projects/:id
   └── Sidebar shows: Projects still highlighted
   └── Breadcrumb: "Projects > Project Name"
   └── Back button shows: "← Projects"

4. User opens a conversation
   └── ConversationScreen (pushed)
   └── AppBar shows: Thread title
   └── Back arrow navigates to Project Detail
```

---

## Screen Details

### 1. Splash Screen
**Route:** `/splash`
**File:** `frontend/lib/screens/splash_screen.dart`

**Purpose:** Initial loading state while checking authentication

**UI Elements:**
| Element | Description |
|---------|-------------|
| App Icon | `Icons.analytics_outlined` (80px) |
| Title | "Business Analyst Assistant" |
| Loading | `CircularProgressIndicator` |

**Actions:** None (auto-navigates based on auth status)

---

### 2. Login Screen
**Route:** `/login`
**File:** `frontend/lib/screens/auth/login_screen.dart`

**Purpose:** OAuth authentication entry point

**UI Elements:**
| Element | Description |
|---------|-------------|
| App Icon | `Icons.analytics_outlined` (64-80px responsive) |
| Title | "Business Analyst Assistant" |
| Subtitle | "AI-powered requirement discovery" |
| Google Button | White background, black text |
| Microsoft Button | #00A4EF background, white text |
| Loading State | CircularProgressIndicator replaces buttons |
| Error Card | Shows error message if auth fails |

**Buttons:**
| Button | Action |
|--------|--------|
| Sign in with Google | Initiates Google OAuth flow |
| Sign in with Microsoft | Initiates Microsoft OAuth flow |

---

### 3. Callback Screen
**Route:** `/auth/callback`
**File:** `frontend/lib/screens/auth/callback_screen.dart`

**Purpose:** Handle OAuth redirect and token extraction

**UI Elements:**
| State | Display |
|-------|---------|
| Processing | Spinner + "Completing authentication..." |
| Error | Error icon + message + "Return to Login" button |

**Buttons:**
| Button | Action |
|--------|--------|
| Return to Login | Navigate to `/login` |

---

### 4. Home Screen
**Route:** `/home`
**File:** `frontend/lib/screens/home_screen.dart`

**Purpose:** Authenticated landing page with quick actions

**UI Elements:**
| Element | Description |
|---------|-------------|
| App Icon | `Icons.analytics_outlined` (64px, primary color) |
| Greeting | "Welcome back, {displayName}" or "Welcome back, {email}" |
| Action Buttons | Primary + Secondary CTAs |
| Recent Projects | Up to 3 project cards |
| Empty State | "No projects yet" message |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| Start Conversation | FilledButton.icon | Navigate to `/projects` |
| Browse Projects | OutlinedButton.icon | Navigate to `/projects` |
| See all | TextButton | Navigate to `/projects` |
| Project Card | InkWell (tappable) | Navigate to `/projects/:id` |

---

### 5. Project List Screen
**Route:** `/projects`
**File:** `frontend/lib/screens/projects/project_list_screen.dart`

**Purpose:** Browse and manage all projects

**UI Elements:**
| Element | Description |
|---------|-------------|
| FAB | "+" icon for creating projects |
| Project Cards | Name, description, metadata badges, date |
| Skeleton Loaders | Shown while loading |
| Empty State | Icon + message + "Create Project" button |
| Pull-to-Refresh | Reloads project list |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| FAB (+) | FloatingActionButton | Opens Create Project dialog |
| Project Card | InkWell (tappable) | Navigate to `/projects/:id` |
| Create Project (empty state) | FilledButton.icon | Opens Create Project dialog |

**Dialog: Create Project**
| Field | Type | Required |
|-------|------|----------|
| Name | TextField | Yes |
| Description | TextField (multiline) | No |

| Button | Action |
|--------|--------|
| Cancel | Close dialog |
| Create | Create project, close dialog |

---

### 6. Project Detail Screen
**Route:** `/projects/:id`
**File:** `frontend/lib/screens/projects/project_detail_screen.dart`

**Purpose:** View project with Documents and Threads tabs

**UI Elements:**
| Element | Description |
|---------|-------------|
| Header | Project name (titleLarge) + last updated date |
| Edit Button | Pencil icon in header |
| Delete Button | Trash icon in header |
| Description | Optional text below header |
| Tab Bar | Documents / Threads tabs |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| Edit | IconButton | Opens Edit Project dialog |
| Delete | IconButton | Opens Delete confirmation dialog |
| Documents Tab | Tab | Shows DocumentListScreen |
| Threads Tab | Tab | Shows ThreadListScreen |

**Dialog: Edit Project**
| Field | Type | Required |
|-------|------|----------|
| Name | TextField (pre-filled) | Yes |
| Description | TextField (pre-filled) | No |

| Button | Action |
|--------|--------|
| Cancel | Close dialog |
| Save | Update project, close dialog |

---

### 7. Document List Screen
**Route:** Embedded in Project Detail (Documents tab)
**File:** `frontend/lib/screens/documents/document_list_screen.dart`

**Purpose:** View and manage project documents

**UI Elements:**
| Element | Description |
|---------|-------------|
| FAB | "+" icon for uploading documents |
| Document List Items | Icon + filename + upload date + menu |
| Empty State | Icon + message + "Upload Document" button |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| FAB (+) | FloatingActionButton | Opens DocumentUploadScreen |
| Document Item | ListTile (tappable) | Opens DocumentViewerScreen |
| Upload Document (empty state) | FilledButton.icon | Opens DocumentUploadScreen |

**PopupMenu per Document:**
| Option | Icon | Action |
|--------|------|--------|
| View | `Icons.visibility` | Opens DocumentViewerScreen |
| Delete | `Icons.delete_outline` | Opens Delete confirmation dialog |

---

### 8. Document Upload Screen
**Route:** Push navigation from Documents tab
**File:** `frontend/lib/screens/documents/document_upload_screen.dart`

**Purpose:** Upload .txt or .md files

**UI Elements:**
| Element | Description |
|---------|-------------|
| Cloud Icon | `Icons.cloud_upload` (100px, blue) |
| Title | "Upload a text document" |
| Instructions | File types (.txt, .md) and size limit (1MB) |
| Select File Button | Opens file picker |
| Progress Bar | Shows upload progress with percentage |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| Select File | ElevatedButton.icon | Opens file picker, uploads on selection |

**States:**
| State | Display |
|-------|---------|
| Idle | Select File button visible |
| Uploading | Progress bar + percentage |
| Success | SnackBar + auto-close screen |
| Error | SnackBar with error message |

---

### 9. Document Viewer Screen
**Route:** Push navigation from Document List
**File:** `frontend/lib/screens/documents/document_viewer_screen.dart`

**Purpose:** Display decrypted document content

**UI Elements:**
| Element | Description |
|---------|-------------|
| AppBar Title | Document filename |
| Content | SelectableText (monospace font, 14px) |
| Loading | CircularProgressIndicator |
| Error | Error icon + message + "Retry" button |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| Retry (error state) | ElevatedButton | Reload document |
| Back Arrow | AppBar leading | Return to Documents tab |

---

### 10. Thread List Screen
**Route:** Embedded in Project Detail (Threads tab)
**File:** `frontend/lib/screens/threads/thread_list_screen.dart`

**Purpose:** View and manage conversation threads

**UI Elements:**
| Element | Description |
|---------|-------------|
| FAB Extended | "New Conversation" with chat icon |
| Thread List Items | Icon + title + date + message count + menu |
| Empty State | Icon + message + "Start Conversation" button |
| Pull-to-Refresh | Reloads thread list |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| FAB (New Conversation) | FloatingActionButton.extended | Opens ThreadCreateDialog |
| Thread Item | ListTile (tappable) | Opens ConversationScreen |
| Start Conversation (empty state) | FilledButton.icon | Opens ThreadCreateDialog |

**PopupMenu per Thread:**
| Option | Icon | Action |
|--------|------|--------|
| Delete | `Icons.delete_outline` | Opens Delete confirmation dialog |

---

### 11. Thread Create Dialog
**File:** `frontend/lib/screens/threads/thread_create_dialog.dart`

**Purpose:** Create new conversation thread

**Dialog Elements:**
| Field | Type | Required |
|-------|------|----------|
| Title | TextField | No (untitled if empty) |

**Buttons:**
| Button | Action |
|--------|--------|
| Cancel | Close dialog |
| Create | Create thread, close dialog, auto-open ConversationScreen |

---

### 12. Conversation Screen
**Route:** Push navigation from Thread List
**File:** `frontend/lib/screens/conversation/conversation_screen.dart`

**Purpose:** AI chat interface for requirements discovery

**UI Elements:**
| Element | Description |
|---------|-------------|
| AppBar | Thread title or "New Conversation" |
| Error Banner | Dismissable Material banner with error |
| Message List | User and assistant message bubbles |
| Mode Selector | ActionChips for Meeting/Document mode (initial only) |
| Chat Input | TextField + send button |
| Streaming Indicator | Shows AI typing with status |

**Message Display:**
| Role | Alignment | Background |
|------|-----------|------------|
| User | Right | Primary color |
| Assistant | Left | Surface container |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| Meeting Mode | ActionChip | Send mode selection to AI |
| Document Refinement | ActionChip | Send mode selection to AI |
| Send | IconButton | Send message to AI |
| Dismiss (error banner) | TextButton | Clear error |

**Long-press on Message:**
| Option | Action |
|--------|--------|
| Delete | Opens Delete confirmation dialog |

---

### 13. Settings Screen
**Route:** `/settings`
**File:** `frontend/lib/screens/settings_screen.dart`

**Purpose:** User preferences and account management

**Sections:**

**1. Account Section:**
| Element | Description |
|---------|-------------|
| Profile Tile | Avatar (initials) + display name + email |

**2. Appearance Section:**
| Element | Description |
|---------|-------------|
| Dark Mode | SwitchListTile toggle |

**3. Usage Section:**
| Element | Description |
|---------|-------------|
| Token Budget | Progress bar + cost display |
| Loading | LinearProgressIndicator |
| Error | Error message + Retry button |

**4. Actions Section:**
| Element | Description |
|---------|-------------|
| Log Out | ListTile with logout icon (red) |

**Buttons:**
| Button | Type | Action |
|--------|------|--------|
| Dark Mode Toggle | SwitchListTile | Toggle theme immediately |
| Retry (usage error) | IconButton | Reload usage data |
| Log Out | ListTile (tappable) | Opens Logout confirmation dialog |

**Dialog: Logout Confirmation**
| Button | Action |
|--------|--------|
| Cancel | Close dialog |
| Log Out | Clear session, redirect to `/login` |

---

## Reusable Widgets

### 1. Responsive Scaffold
**File:** `frontend/lib/widgets/responsive_scaffold.dart`

**Purpose:** Shell wrapper for authenticated routes

**Features:**
- Responsive navigation (rail/drawer based on width)
- Breadcrumb bar integration
- Contextual back button
- App branding in expanded sidebar
- User email display

### 2. Empty State
**File:** `frontend/lib/widgets/empty_state.dart`

**Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| icon | IconData | Large centered icon (64px) |
| title | String | Bold title text |
| message | String | Descriptive subtitle |
| buttonLabel | String | CTA button text |
| buttonIcon | IconData? | Optional button icon |
| onPressed | VoidCallback | Button action |

### 3. Mode Selector
**File:** `frontend/lib/widgets/mode_selector.dart`

**Modes:**
| Mode | Icon | Description |
|------|------|-------------|
| Meeting Mode | `Icons.groups` | For live discovery sessions |
| Document Refinement | `Icons.edit_document` | For async document work |

### 4. Delete Confirmation Dialog
**File:** `frontend/lib/widgets/delete_confirmation_dialog.dart`

**Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| itemType | String | "project", "thread", "document", "message" |
| cascadeMessage | String? | Optional warning about cascade deletes |

**Returns:** `Future<bool>` (true = confirmed, false = cancelled)

### 5. Breadcrumb Bar
**File:** `frontend/lib/widgets/breadcrumb_bar.dart`

**Features:**
- Parses route to build breadcrumb trail
- Clickable segments navigate to routes
- Last segment is bold (current page)
- Supports truncation for narrow screens

### 6. Contextual Back Button
**File:** `frontend/lib/widgets/contextual_back_button.dart`

**Features:**
- Shows destination label (not generic arrow)
- Hidden on root pages (/home, /projects, /settings)
- Supports icon-only mode for mobile

### 7. Chat Input
**File:** `frontend/lib/screens/conversation/widgets/chat_input.dart`

**Features:**
- Multi-line (1-5 lines)
- Rounded border (24px radius)
- Send button icon
- Disables during streaming

### 8. Message Bubble
**File:** `frontend/lib/screens/conversation/widgets/message_bubble.dart`

**Features:**
- User: right-aligned, primary color
- Assistant: left-aligned, surface color
- Selectable text for copying
- Max width: 80%

### 9. Streaming Message
**File:** `frontend/lib/screens/conversation/widgets/streaming_message.dart`

**Features:**
- Shows AI response in real-time
- Optional status message (e.g., "Searching documents...")
- "Thinking..." indicator when no content yet

---

## Button Reference

### All Buttons by Screen

| Screen | Button | Type | Action | Navigation |
|--------|--------|------|--------|------------|
| Login | Sign in with Google | ElevatedButton | OAuth | External |
| Login | Sign in with Microsoft | ElevatedButton | OAuth | External |
| Callback | Return to Login | ElevatedButton | Navigate | `/login` |
| Home | Start Conversation | FilledButton.icon | Navigate | `/projects` |
| Home | Browse Projects | OutlinedButton.icon | Navigate | `/projects` |
| Home | See all | TextButton | Navigate | `/projects` |
| Home | Project Card | InkWell | Navigate | `/projects/:id` |
| Project List | FAB (+) | FAB | Dialog | Create Project |
| Project List | Project Card | InkWell | Navigate | `/projects/:id` |
| Project List | Create Project (empty) | FilledButton.icon | Dialog | Create Project |
| Project Detail | Edit | IconButton | Dialog | Edit Project |
| Project Detail | Delete | IconButton | Dialog | Delete Confirm |
| Document List | FAB (+) | FAB | Navigate | DocumentUploadScreen |
| Document List | Document Item | ListTile | Navigate | DocumentViewerScreen |
| Document List | View (menu) | PopupMenuItem | Navigate | DocumentViewerScreen |
| Document List | Delete (menu) | PopupMenuItem | Dialog | Delete Confirm |
| Document List | Upload (empty) | FilledButton.icon | Navigate | DocumentUploadScreen |
| Document Upload | Select File | ElevatedButton.icon | File Picker | — |
| Document Viewer | Retry | ElevatedButton | Reload | — |
| Thread List | FAB (New Conv) | FAB.extended | Dialog | Create Thread |
| Thread List | Thread Item | ListTile | Navigate | ConversationScreen |
| Thread List | Delete (menu) | PopupMenuItem | Dialog | Delete Confirm |
| Thread List | Start Conv (empty) | FilledButton.icon | Dialog | Create Thread |
| Thread Create | Cancel | TextButton | Close | — |
| Thread Create | Create | ElevatedButton | Create | ConversationScreen |
| Conversation | Meeting Mode | ActionChip | Send | — |
| Conversation | Document Mode | ActionChip | Send | — |
| Conversation | Send | IconButton | Send | — |
| Conversation | Dismiss (error) | TextButton | Clear | — |
| Conversation | Delete (msg) | BottomSheet | Dialog | Delete Confirm |
| Settings | Dark Mode | SwitchListTile | Toggle | — |
| Settings | Retry (usage) | IconButton | Reload | — |
| Settings | Log Out | ListTile | Dialog | `/login` |

---

## State Management

### Providers (ChangeNotifier pattern)

| Provider | Purpose | Key State |
|----------|---------|-----------|
| AuthProvider | Authentication | isAuthenticated, isLoading, email, displayName |
| ProjectProvider | Projects CRUD | projects, selectedProject, isLoading, error |
| ThreadProvider | Threads CRUD | threads, isLoading, error |
| DocumentProvider | Documents CRUD | documents, selectedDocument, uploading, uploadProgress |
| ConversationProvider | Chat messages | messages, isStreaming, streamingText, statusMessage, error |
| ThemeProvider | Theme toggle | isDarkMode |
| NavigationProvider | Sidebar state | isExpanded |

### Provider Dependencies by Screen

| Screen | Providers Used |
|--------|----------------|
| Splash | AuthProvider |
| Login | AuthProvider |
| Callback | AuthProvider |
| Home | AuthProvider, ProjectProvider |
| Project List | ProjectProvider |
| Project Detail | ProjectProvider, ThreadProvider |
| Document List | DocumentProvider |
| Document Upload | DocumentProvider |
| Document Viewer | DocumentProvider |
| Thread List | ThreadProvider |
| Conversation | ConversationProvider |
| Settings | AuthProvider, ThemeProvider |
| Responsive Scaffold | AuthProvider, NavigationProvider |

---

## Feature Summary

### Core Features (MVP v1.0)
- [x] Google OAuth authentication
- [x] Microsoft OAuth authentication
- [x] Project creation and management
- [x] Document upload (.txt, .md)
- [x] Document viewing
- [x] Conversation thread creation
- [x] AI-powered chat with streaming
- [x] Document context search (AI autonomously searches)
- [x] Artifact generation (user stories, acceptance criteria, BRDs)
- [x] Export to Markdown, PDF, Word

### UI/UX Features (Beta v1.5)
- [x] Responsive sidebar navigation
- [x] Light/dark theme toggle
- [x] Theme persistence (no white flash)
- [x] Professional empty states
- [x] Breadcrumb navigation
- [x] Contextual back buttons
- [x] Delete with 10-second undo
- [x] Cascade delete confirmations
- [x] Mode selector chips (Meeting/Document)
- [x] Settings page with profile
- [x] Token usage display
- [x] Consistent date formatting
- [x] Metadata badges on project cards
- [x] Skeleton loaders
- [x] Pull-to-refresh

---

*Document generated: 2026-01-30*
*Covers: Beta v1.5 (all screens and features)*
