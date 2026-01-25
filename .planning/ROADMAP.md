# Project Roadmap

**Project:** Business Analyst Assistant
**Version:** MVP v1.0
**Last Updated:** 2026-01-25

## Overview

This roadmap delivers an AI-powered conversational platform for business analysts in 8-10 weeks through 5 phases. The structure follows the critical dependency chain: authentication and infrastructure enable project/document management, which provides context for AI-assisted discovery conversations, which generate exportable artifacts for stakeholder delivery. Each phase delivers a complete, verifiable capability that unblocks the next phase.

## Phases

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
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Database schema + FastAPI server setup
- [x] 01-02-PLAN.md — OAuth backend + Flutter OAuth flows
- [x] 01-03-PLAN.md — Cross-platform testing & verification

1. User can create account using Google work email and is immediately logged in
2. User can create account using Microsoft work email and is immediately logged in
3. User can log in on web browser, close browser, return later and remain logged in
4. User can log in on mobile device, close app, reopen and remain logged in
5. User can log out from any page and is redirected to login screen
6. User's authentication works identically on web, Android, and iOS

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
**Plans:** 5 plans

Plans:
- [x] 02-01-PLAN.md — Database schema for projects, documents, threads
- [x] 02-02-PLAN.md — Project CRUD API and UI
- [x] 02-03-PLAN.md — Document management with encryption and FTS5
- [x] 02-04-PLAN.md — Thread management API and UI
- [x] 02-05-PLAN.md — Integration testing and verification

1. User can create project named "Client Portal Redesign" with description and see it in project list
2. User can upload text file "requirements.txt" to project and view its contents in app
3. User can create multiple threads within project ("Login Flow", "Dashboard Features") that appear in thread list
4. User can switch between projects and see only that project's threads and documents (no cross-contamination)
5. User can update project name from "Client Portal" to "Customer Portal" and change persists

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

**Plans:** 3 plans

Plans:
- [x] 03-01-PLAN.md — Backend AI service with Claude integration and SSE streaming
- [x] 03-02-PLAN.md — Token tracking and thread summarization services
- [x] 03-03-PLAN.md — Flutter conversation UI with SSE streaming

**Success Criteria:**
1. User types "We need a user login feature" and AI streams response immediately asking clarifying questions about auth methods
2. AI proactively asks "What happens if user enters wrong password 5 times?" without user prompting
3. User mentions "password requirements" and AI autonomously searches uploaded documents, references "security-policy.txt" in response
4. AI remembers earlier discussion about OAuth when user asks follow-up question 10 messages later
5. Thread summary updates from "New Conversation" to "User Login Feature - OAuth with MFA" after 5 exchanges
6. User can send 50 messages in thread and AI still references decisions from message 10

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

### Phase 4.1: Agent SDK & Business-Analyst Skill Integration
**Goal:** Refactor AI backend to use Claude Agent SDK and integrate the /business-analyst skill for structured one-question-at-a-time discovery and comprehensive BRD generation.

**Dependencies:** Phase 4 (requires working AI service and artifact generation)

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

Plans:
- [x] 04.1-01-PLAN.md — Claude Agent SDK integration and skill loader
- [x] 04.1-02-PLAN.md — Business-analyst skill prompt module
- [x] 04.1-03-PLAN.md — BRD generation tool and template
- [x] 04.1-04-PLAN.md — Integration tests and validation

---

### Phase 5: Cross-Platform Polish & Launch
**Goal:** Application delivers consistent, professional experience across web, Android, and iOS with production-ready reliability.

**Dependencies:** Phase 4.1 (all features complete, now focus on quality)

**Requirements Covered:**
- PLAT-06: UI is responsive and adapts to screen size (mobile, tablet, desktop)

**Success Criteria:**
1. User accesses application on desktop and sees sidebar navigation, on mobile sees drawer navigation
2. User uploads document on desktop, opens mobile app and document appears immediately (sync verified)
3. User experiences no platform-specific bugs across Chrome, Firefox, Safari, Edge, Android, iOS
4. All loading states display skeleton loaders or progress indicators (no blank screens)
5. User encounters error (network failure, API timeout) and sees helpful error message with recovery action

---

## Progress

| Phase | Status | Requirements | Completion |
|-------|--------|--------------|------------|
| 1 - Foundation & Authentication | Complete | 10 | 100% |
| 2 - Project & Document Management | Complete | 14 | 100% |
| 3 - AI-Powered Conversations | Complete | 9 | 100% |
| 4 - Artifact Generation & Export | Complete | 7 | 100% |
| 4.1 - Agent SDK & Skill Integration | Complete | 3 (enhanced) | 100% |
| 5 - Cross-Platform Polish & Launch | Pending | 1 | 0% |

**Total Requirements Covered:** 41/41 (includes 40 v1 requirements + PLAT-06 counted separately)
**Estimated Timeline:** 8-10 weeks (solo developer, 20-30 hours/week)

---

## Phase Ordering Rationale

**Dependency-driven:** Each phase is blocked by previous phases completing. Authentication enables project creation. Projects enable document upload. Documents enable AI context search. AI conversations enable artifact generation. All features complete before cross-platform polish.

**Risk-driven:** Token tracking in Phase 1 (before AI ships) prevents cost explosion. Document encryption and FTS5 indexing in Phase 2 (before AI search) prevents security debt and shallow RAG. AI service in Phase 3 as longest phase allows buffer time.

**Value-driven:** Phase 3 delivers core value proposition (AI-assisted discovery). Phase 4 completes value loop (conversation -> insights -> deliverable documents). Phase 5 ensures professional quality before user validation.

---

*Last updated: 2026-01-25*
*Ready for phase execution: Phase 5*
