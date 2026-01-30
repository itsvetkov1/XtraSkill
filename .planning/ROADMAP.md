# Project Roadmap

**Project:** Business Analyst Assistant
**Version:** Beta v1.5 - UI/UX Excellence
**Last Updated:** 2026-01-30

## Milestones

- ✅ **MVP v1.0** - Phases 1-5 (shipped 2026-01-28)
- 🚧 **Beta v1.5 - UI/UX Excellence** - Phases 6-10 (in progress)

## Overview

Beta v1.5 transforms the MVP into an executive-demo-ready application through five focused phases. The milestone follows a clear dependency chain: theme infrastructure enables settings page, navigation foundation supports all screens, deletion capabilities require stable navigation, and polish features enhance the complete experience. Each phase delivers a coherent, verifiable capability that builds toward professional, intuitive cross-platform UX.

## Phases

<details>
<summary>✅ MVP v1.0 (Phases 1-5) - SHIPPED 2026-01-28</summary>

### Phase 1: Foundation & Authentication
**Goal:** Users can securely access the application from any device with persistent authentication.

**Dependencies:** None (foundational phase)

**Requirements Covered:**
- AUTH-01: User can create account via Google OAuth 2.0
- AUTH-02: User can create account via Microsoft OAuth 2.0
- AUTH-03: User can log in with Google account and stay logged in across sessions
- AUTH-04: User can log in with Microsoft account and stay logged in across sessions
- AUTH-05: User can log out from any page
- PLAT-01: Application works on web browsers (Chrome, Firefox, Safari, Edge)
- PLAT-02: Application works on Android devices (native Flutter app)
- PLAT-03: Application works on iOS devices (native Flutter app)
- PLAT-04: All user data persists on server (not local storage only)
- PLAT-05: Data automatically syncs across devices when user logs in

**Success Criteria:**
1. User can create account using Google work email and is immediately logged in
2. User can create account using Microsoft work email and is immediately logged in
3. User can log in on web browser, close browser, return later and remain logged in
4. User can log in on mobile device, close app, reopen and remain logged in
5. User can log out from any page and is redirected to login screen
6. User's authentication works identically on web, Android, and iOS

**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Database schema + FastAPI server setup
- [x] 01-02-PLAN.md — OAuth backend + Flutter OAuth flows
- [x] 01-03-PLAN.md — Cross-platform testing & verification

---

### Phase 2: Project & Document Management
**Goal:** Users can organize work into projects with context documents that AI can reference.

**Dependencies:** Phase 1 (requires authentication and database)

**Requirements Covered:**
- PROJ-01: User can create new projects with name and optional description
- PROJ-02: User can view list of all their projects
- PROJ-03: User can open a project to view its contents (threads and documents)
- PROJ-04: Projects maintain isolated contexts (documents and threads don't leak across projects)
- PROJ-05: User can update project name and description
- DOC-01: User can upload text documents (.txt, .md) to a project
- DOC-02: User can view list of documents uploaded to a project
- DOC-03: Documents are stored encrypted at rest
- DOC-04: Documents are indexed for full-text search (FTS5)
- DOC-05: User can view document content within the application
- CONV-01: User can create multiple conversation threads within a project
- CONV-02: User can view list of threads in a project with AI-generated summaries
- CONV-03: User can open a thread to view full conversation history
- CONV-05: Threads display in chronological order with most recent first

**Success Criteria:**
1. User can create project named "Client Portal Redesign" with description and see it in project list
2. User can upload text file "requirements.txt" to project and view its contents in app
3. User can create multiple threads within project ("Login Flow", "Dashboard Features") that appear in thread list
4. User can switch between projects and see only that project's threads and documents (no cross-contamination)
5. User can update project name from "Client Portal" to "Customer Portal" and change persists

**Plans:** 5 plans

Plans:
- [x] 02-01-PLAN.md — Database schema for projects, documents, threads
- [x] 02-02-PLAN.md — Project CRUD API and UI
- [x] 02-03-PLAN.md — Document management with encryption and FTS5
- [x] 02-04-PLAN.md — Thread management API and UI
- [x] 02-05-PLAN.md — Integration testing and verification

---

### Phase 3: AI-Powered Conversations
**Goal:** Users conduct AI-assisted discovery conversations that proactively identify edge cases and autonomously reference project documents.

**Dependencies:** Phase 2 (requires projects, documents, threads)

**Requirements Covered:**
- CONV-04: User can send messages in a thread
- CONV-06: Thread summaries automatically update as conversation progresses
- AI-01: AI provides real-time streaming responses during conversation
- AI-02: AI proactively identifies edge cases and missing requirements
- AI-03: AI autonomously searches project documents when conversation requires context
- AI-04: AI asks clarifying questions to explore requirements deeply
- AI-05: AI maintains conversation context across multiple messages
- AI-06: AI responses stream progressively to user (SSE)
- AI-07: Token usage is tracked and enforced per request, conversation, and user

**Success Criteria:**
1. User types "We need a user login feature" and AI streams response immediately asking clarifying questions about auth methods
2. AI proactively asks "What happens if user enters wrong password 5 times?" without user prompting
3. User mentions "password requirements" and AI autonomously searches uploaded documents, references "security-policy.txt" in response
4. AI remembers earlier discussion about OAuth when user asks follow-up question 10 messages later
5. Thread summary updates from "New Conversation" to "User Login Feature - OAuth with MFA" after 5 exchanges
6. User can send 50 messages in thread and AI still references decisions from message 10

**Plans:** 3 plans

Plans:
- [x] 03-01-PLAN.md — Backend AI service with Claude integration and SSE streaming
- [x] 03-02-PLAN.md — Token tracking and thread summarization services
- [x] 03-03-PLAN.md — Flutter conversation UI with SSE streaming

---

### Phase 4: Artifact Generation & Export
**Goal:** Users convert conversations into professional documentation deliverables in multiple formats.

**Dependencies:** Phase 3 (requires completed conversations with AI context)

**Requirements Covered:**
- ART-01: User can request structured user stories from conversation
- ART-02: User can request acceptance criteria from conversation
- ART-03: User can request requirements documents from conversation
- ART-04: Generated artifacts are stored and associated with conversation thread
- ART-05: User can export artifacts in Markdown format
- ART-06: User can export artifacts in PDF format
- ART-07: User can export artifacts in Word (.docx) format

**Success Criteria:**
1. User says "Generate user stories" and AI produces structured stories with Given/When/Then format
2. User says "Create acceptance criteria" and AI produces testable criteria based on conversation context
3. User requests "Requirements document" and AI generates formal requirements doc with all discussed features
4. Generated artifacts appear in thread history and persist across sessions
5. User can export user story artifact as Markdown file and open in text editor
6. User can export requirements document as PDF and Word files that open correctly with proper formatting

---

### Phase 4.1: Business-Analyst Skill Integration (Direct API)
**Goal:** Integrate the /business-analyst skill behaviors for structured one-question-at-a-time discovery and comprehensive BRD generation.

**Dependencies:** Phase 4 (requires working AI service and artifact generation)

**Architecture Decision:** Originally planned to use Claude Agent SDK, but research revealed it requires Claude Code CLI runtime (unsuitable for web backend deployment). **Pivoted to Direct Anthropic API** with skill behaviors transformed into XML system prompt.

**Requirements Covered:**
- AI-02: AI proactively identifies edge cases and missing requirements (enhanced via skill methodology)
- AI-04: AI asks clarifying questions to explore requirements deeply (enhanced via one-question protocol)
- ART-03: User can request requirements documents from conversation (enhanced via BRD template)

**Success Criteria:**
1. AI asks mode question at session start: Meeting Mode vs Document Refinement Mode
2. AI maintains one-question-at-a-time protocol with rationale and 3 answer options
3. AI clarifies ambiguous terms ("seamless", "scalable") before proceeding
4. AI redirects technical implementation discussions to business focus
5. Generated BRDs follow complete template structure with all sections
6. Skill behavior validated through integration tests

**Implementation:**
- Transformed `.claude/business-analyst/` skill (5 files) into 7,437-token XML system prompt
- System prompt includes: mode detection, discovery protocol, zero-assumption clarification, technical boundaries, BRD structure, error protocols, tone guidelines
- Direct API preserves existing tool integration (search_documents, save_artifact)
- Structure validation: 9/10 tests passed
- No infrastructure changes required for deployment

**Documentation:**
- Architecture analysis: `.planning/ANALYSIS-claude-agent-sdk-workaround.md`
- System prompt documentation: `.planning/SYSTEM-PROMPT-business-analyst.md`
- Testing guide: `backend/TESTING-GUIDE.md`
- Phase summary: `.planning/phases/04.1-agent-sdk-skill-integration/PHASE-COMPLETE.md`

---

### Phase 5: Cross-Platform Polish & Launch
**Goal:** Application delivers consistent, professional experience across web, Android, and iOS with production-ready reliability.

**Dependencies:** Phase 4.1 (all features complete, now focus on quality)

**Requirements Covered:**
- PLAT-06: UI is responsive and adapts to screen size (mobile, tablet, desktop)

**Plans:** 5 plans

Plans:
- [x] 05-01-PLAN.md — UI polish with skeleton loaders and error handling
- [x] 05-02-PLAN.md — Expand test coverage (widget tests + backend integration)
- [x] 05-03-PLAN.md — Production environment validation and OAuth config guidance
- [x] 05-04-PLAN.md — Deployment configs and CI/CD pipeline setup
- [x] 05-05-PLAN.md — Cross-browser and mobile device verification

**Success Criteria:**
1. User accesses application on desktop and sees sidebar navigation, on mobile sees drawer navigation
2. User uploads document on desktop, opens mobile app and document appears immediately (sync verified)
3. User experiences no platform-specific bugs across Chrome, Firefox, Safari, Edge, Android, iOS
4. All loading states display skeleton loaders or progress indicators (no blank screens)
5. User encounters error (network failure, API timeout) and sees helpful error message with recovery action

</details>

---

## 🚧 Beta v1.5 - UI/UX Excellence (In Progress)

**Milestone Goal:** Transform the MVP into an executive-demo-ready application through comprehensive navigation improvements, professional empty states, deletion capabilities, and visual consistency enhancements.

### Phase 6: Theme Management Foundation
**Goal:** Users can switch between light and dark themes with persistent preferences that load instantly on app startup.

**Dependencies:** None (independent infrastructure phase)

**Requirements Covered:**
- SET-03: Settings page includes light/dark theme toggle switch
- SET-04: Theme preference persists across app restarts (SharedPreferences)
- SET-06: Theme loads before MaterialApp initialization (prevent white flash on dark mode)
- SET-07: Theme respects system preference on first launch (iOS/Android/web)

**Success Criteria:**
1. User toggles theme to dark mode and all screens immediately reflect dark theme
2. User closes and reopens app, dark theme persists without white flash during startup
3. New user launches app and theme matches their system preference (dark OS = dark app)
4. User can switch theme on any screen and preference saves within 1 second
5. Theme switching works identically on web, Android, and iOS

**Plans:** 2 plans

Plans:
- [x] 06-01-PLAN.md — Theme foundation (ThemeProvider + AppTheme colors)
- [x] 06-02-PLAN.md — Theme integration (main.dart async init + Settings screen)

---

### Phase 7: Responsive Navigation Infrastructure
**Goal:** Users access persistent navigation on every screen with responsive behavior that adapts from mobile to desktop seamlessly.

**Dependencies:** None (can run parallel to Phase 6)

**Requirements Covered:**
- NAV-01: Persistent sidebar navigation visible on all screens with responsive behavior (desktop always-visible ≥900px, mobile hamburger <600px)
- NAV-02: Breadcrumb navigation displays current location path (e.g., "Projects > Project Name > Thread Name")
- NAV-03: Back arrows show destination context (e.g., "← Projects" or "← Project Name")
- NAV-04: Navigation highlights current screen location in sidebar
- NAV-05: Sidebar state persists across navigation (expanded/collapsed preference on desktop)

**Success Criteria:**
1. User navigates from Projects to Thread on desktop and sidebar remains visible with current location highlighted
2. User navigates same path on mobile and sees hamburger menu with drawer that highlights current location
3. User resizes browser from 1200px to 500px and navigation smoothly transitions from sidebar to drawer
4. User sees breadcrumb "Projects > Client Portal > Login Thread" and can click any segment to navigate
5. User collapses sidebar on desktop, navigates between screens, and sidebar remains collapsed

**Plans:** 3 plans

Plans:
- [x] 07-01-PLAN.md — NavigationProvider + ResponsiveScaffold shell widget
- [x] 07-02-PLAN.md — StatefulShellRoute integration + sidebar highlighting
- [x] 07-03-PLAN.md — BreadcrumbBar + ContextualBackButton + screen refactoring

---

### Phase 8: Settings Page & User Preferences
**Goal:** Users access centralized settings page to view profile, manage theme, check token usage, and log out.

**Dependencies:** Phase 6 (requires ThemeProvider), Phase 7 (settings is a navigation destination)

**Requirements Covered:**
- SET-01: Settings page displays user profile information (email, name from OAuth provider)
- SET-02: Settings page provides logout button with confirmation
- SET-05: Settings page displays current month token budget usage (used/limit with percentage)

**Success Criteria:**
1. User navigates to Settings page and sees their email and name from OAuth provider
2. User taps logout button, sees confirmation dialog, confirms, and is redirected to login screen
3. User views token budget section showing "1,234 / 10,000 tokens used (12%)" with visual progress indicator
4. Settings page renders correctly on mobile (sectioned ListTiles) and desktop (same layout, centered)

**Plans:** 2 plans

Plans:
- [x] 08-01-PLAN.md — Backend API for display name and token usage endpoints
- [x] 08-02-PLAN.md — Settings screen UI with profile, logout confirmation, usage display

---

### Phase 9: Deletion Flows with Undo
**Goal:** Users can delete projects, threads, documents, and messages with confirmation dialogs and undo capability to prevent accidental data loss.

**Dependencies:** Phase 7 (requires navigation for post-delete routing)

**Requirements Covered:**
- DEL-01: User can delete projects with confirmation dialog showing cascade impact ("This will delete X threads and Y documents")
- DEL-02: User can delete threads with confirmation dialog showing impact ("This will delete X messages")
- DEL-03: User can delete documents from project (confirmation dialog)
- DEL-04: User can delete individual messages from thread (confirmation dialog)
- DEL-05: Backend performs cascade deletes maintaining referential integrity (threads→messages, projects→threads→messages)
- DEL-06: Deleted items show SnackBar with undo action (10-second window)
- DEL-07: Deletion uses optimistic UI updates (immediate removal from list, rollback on error)

**Success Criteria:**
1. User deletes project with 3 threads and 5 documents, sees confirmation "This will delete 3 threads and 5 documents", confirms, and project disappears with undo SnackBar
2. User taps undo within 10 seconds and project reappears in list with all threads and documents intact
3. User deletes thread, navigates to different screen, undo expires, returns to project and thread is permanently gone
4. User deletes document, sees optimistic removal, backend fails, document reappears with error message
5. User deletes message from thread, message disappears immediately, can undo within 10 seconds

**Plans:** 3 plans

Plans:
- [ ] 09-01-PLAN.md — Backend DELETE endpoints for projects, threads, documents, messages
- [ ] 09-02-PLAN.md — Frontend services, providers with optimistic delete and undo
- [ ] 09-03-PLAN.md — UI integration with confirmation dialogs and delete triggers

---

### Phase 10: Polish & Empty States
**Goal:** Users encounter professional empty states with clear guidance and enjoy consistent visual polish across all screens.

**Dependencies:** Phase 9 (empty states appear after deleting last item)

**Requirements Covered:**
- ONBOARD-01: Projects list displays empty state when user has no projects (illustration + message + "Create Project" CTA)
- ONBOARD-02: Threads list displays empty state when project has no threads (message + "Start Conversation" CTA)
- ONBOARD-03: Documents list displays empty state when project has no documents (message + "Upload Document" CTA)
- ONBOARD-04: Home screen displays primary action buttons ("Start Conversation", "Browse Projects") after authentication
- ONBOARD-05: Home screen removes development phase information ("Next Steps") and displays user-oriented welcome
- CONV-UI-01: AI mode selection presents as clickable ChoiceChip buttons (Meeting Mode, Document Refinement Mode) instead of typed "A"/"B" responses
- CONV-UI-02: Message pills have improved readability (increased padding, font size 15-16px)
- CONV-UI-03: Thread list items display mode indicator (chip or colored dot showing which mode was used)
- POLISH-01: Date/time formatting is consistent: relative for recent (<7 days: "4d ago", "Yesterday"), absolute for older (>7 days: "Jan 18, 2026")
- POLISH-02: Project detail headers are consolidated to reduce vertical space waste (single line name + metadata, not duplicate)
- POLISH-03: Thread list items show preview text (first line of last message, truncated to 80 chars)
- POLISH-04: Project cards display metadata badges (thread count, document count)
- POLISH-05: All dates use `intl` package with locale-aware formatting (not hard-coded strings)

**Success Criteria:**
1. New user with zero projects sees empty state with illustration, message "No projects yet", and prominent "Create Project" button
2. User deletes last thread in project and immediately sees empty state "No conversations yet - Start one to begin exploring requirements"
3. User starts new conversation and sees two ChoiceChip buttons (Meeting Mode / Document Refinement Mode) instead of text prompt
4. User views thread list and sees preview "User wants authentication with social login..." under thread title
5. User sees consistent dates: threads from today show "2h ago", threads from last week show "Jan 22, 2026"

**Plans:** TBD

Plans:
- [ ] 10-01: [TBD during planning]
- [ ] 10-02: [TBD during planning]

---

## Progress

**Execution Order:**
Phases execute in numeric order: 6 → 7 → 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Authentication | MVP v1.0 | 3/3 | Complete | 2026-01-19 |
| 2. Project & Document Management | MVP v1.0 | 5/5 | Complete | 2026-01-21 |
| 3. AI-Powered Conversations | MVP v1.0 | 3/3 | Complete | 2026-01-24 |
| 4. Artifact Generation & Export | MVP v1.0 | - | Complete | 2026-01-26 |
| 4.1. Agent SDK & Skill Integration | MVP v1.0 | 4/4 | Complete | 2026-01-27 |
| 5. Cross-Platform Polish & Launch | MVP v1.0 | 5/5 | Complete | 2026-01-28 |
| 6. Theme Management Foundation | Beta v1.5 | 2/2 | Complete | 2026-01-29 |
| 7. Responsive Navigation Infrastructure | Beta v1.5 | 3/3 | Complete | 2026-01-29 |
| 8. Settings Page & User Preferences | Beta v1.5 | 2/2 | Complete | 2026-01-29 |
| 9. Deletion Flows with Undo | Beta v1.5 | 0/3 | Planned | - |
| 10. Polish & Empty States | Beta v1.5 | 0/TBD | Not started | - |

---

## Phase Ordering Rationale

**Dependency-driven:** Phase 6 (Theme) is independent infrastructure that Phase 8 (Settings) consumes. Phase 7 (Navigation) is foundational for all screens and required by Phase 9 (Deletion) for post-delete routing. Phase 10 (Polish) depends on Phase 9 for empty state triggers.

**Risk-driven:** Theme infrastructure (Phase 6) completed early prevents FOUC issues during demos. Navigation foundation (Phase 7) established before complex deletion flows to ensure stable post-delete routing. Backend cascade deletes (Phase 9) front-loaded to validate database constraints before polish features.

**Value-driven:** Phase 7 (Navigation) delivers critical "never get lost" UX immediately. Phase 8 (Settings) provides central control point for executive demos. Phase 9 (Deletion) removes "can't clean up test data" friction. Phase 10 (Polish) maximizes first-impression quality for demo scenarios.

---

*Last updated: 2026-01-30*
*Status: Beta v1.5 Phase 9 planned (3 plans), ready for execution*
