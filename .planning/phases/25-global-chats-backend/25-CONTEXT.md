# Phase 25: Global Chats Backend - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend support for project-less threads and global chats listing. Users can start conversations without selecting a project first, and a "Chats" section shows all their threads across projects. Creating threads without project_id, fetching all user threads, and displaying them in navigation.

</domain>

<decisions>
## Implementation Decisions

### API Response Shape
- Use existing POST /threads endpoint with project_id as optional (null = project-less)
- Response includes separate nullable fields: `project_id: string|null`, `project_name: string|null`
- Minimal fields per thread: id, title, updated_at, project_id, project_name
- Offset-based pagination: return page of threads + total count, refresh on every load

### Chats Navigation Item
- Position: After Home, before Projects in sidebar
- Icon: Chat bubble (chat_bubble or forum Material icon)
- No badge or count displayed
- Clicking expands inline list in sidebar (like project expansion)

### New Chat Flow
- "New Chat" button in two places: Chats section header AND Home page
- Clicking goes direct to empty chat view (no title prompt)
- Placeholder title: "New Chat" until auto-generated
- Title auto-generates as summary of first 5 messages after 5th AI response received
- Users can manually edit title anytime (click to edit)

### Thread Ordering
- "Activity" defined as last user interaction (viewed or sent message)
- Default sort: newest first (descending by activity)
- Project-less and project threads mixed together by activity (no grouping)
- Project info displayed as badge/tag next to thread title

### Claude's Discretion
- Exact pagination page size (20-50 reasonable)
- Badge/tag styling for project names
- How to track "last user interaction" timestamp
- Title generation prompt/approach

</decisions>

<specifics>
## Specific Ideas

- Chats inline expansion should work like current project expansion in sidebar
- Title generation summarizes the conversation, not just first message
- "No project" threads should not look orphaned or lesser than project threads

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 25-global-chats-backend*
*Context gathered: 2026-02-01*
