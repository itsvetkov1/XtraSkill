# Phase 2: Project & Document Management - Context

**Gathered:** 2026-01-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Users organize business analysis work into isolated project containers. Each project holds context documents (text files with requirements, notes, specifications) and conversation threads for AI-assisted discovery sessions. This phase delivers:

- Project CRUD (create, read, update, list with isolation per user)
- Document upload (.txt, .md), encryption at rest, FTS5 indexing, and in-app viewing
- Thread CRUD with AI-generated summaries and chronological ordering

**Out of scope:** AI conversation capabilities (Phase 3), artifact generation (Phase 4), deletion workflows (deferred to Beta per PROJECT.md)

</domain>

<decisions>
## Implementation Decisions

### Project list & navigation
- Card-based grid layout for project list (consistent with modern Flutter Material 3 patterns)
- Projects sorted by most recently updated first
- Empty state: Friendly illustration with "Create your first project" CTA and brief explanation of what projects are for
- Quick actions on project cards: Open project, Edit details (name/description)
- Apply responsive layout patterns from Phase 1: Grid on desktop (3 columns), list on mobile

### Project detail view
- Two-tab layout within project: "Threads" tab and "Documents" tab
- Threads tab shows conversation list with AI-generated summaries, timestamps, message counts
- Documents tab shows uploaded files with name, upload date, file size
- Floating action buttons: "New Thread" (Threads tab), "Upload Document" (Documents tab)
- Project name and description editable inline (pencil icon)
- Navigation: Drawer/sidebar shows project switcher + current project name

### Document upload & viewing
- Upload flow: Both drag-drop zone and file picker button for flexibility
- Accepted formats: .txt and .md only (per PROJECT.md constraint)
- Document list: Simple list with filename, upload date, file size, tap to view
- Viewing document content: Full-screen reader with markdown rendering for .md files, plain text display for .txt
- Document content stored encrypted at rest using SQLAlchemy's encryption utilities
- FTS5 full-text search indexing on document content (backend implementation detail)

### Thread list & organization
- Thread list item shows: AI-generated summary (bold), timestamp (relative: "2 hours ago"), message count badge
- Threads sorted chronologically with most recent first (CONV-05 requirement)
- AI-generated summaries update automatically as conversations progress (Phase 3 delivers this capability)
- Empty state: "Start a conversation" CTA with brief description of AI-assisted discovery workflow
- Visual distinction: Threads use chat bubble icon, documents use document icon

### Claude's Discretion
- Exact card styling, shadows, spacing (following Material 3 Design System)
- Loading skeleton design for project list, thread list, document list
- Error state handling (network failures, upload errors, invalid files)
- Specific encryption algorithm choice (as long as encrypted at rest is guaranteed)
- Exact FTS5 configuration parameters (as long as full-text search works)
- Progress indicators for document uploads
- Responsive breakpoint handling details (building on Phase 1 patterns)

</decisions>

<specifics>
## Specific Ideas

- Reuse ResponsiveLayout widget from Phase 1 for project list grid/list switching
- Reuse drawer/sidebar navigation pattern from Phase 1 for project switcher
- Project and thread creation flows should feel lightweight (modal dialogs, not full screens)
- Document viewer should support markdown rendering for .md files (use a Flutter markdown package)
- Follow Material 3 Design System conventions established in Phase 1

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Deletion workflows (projects, documents, threads) explicitly deferred to Beta per PROJECT.md decisions.

</deferred>

---

*Phase: 02-project-document-management*
*Context gathered: 2026-01-18*
