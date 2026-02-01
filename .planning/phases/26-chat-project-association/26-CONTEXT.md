# Phase 26: Chat Project Association - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Add project-less chats to projects with UI for association. Users can associate a chat with a project permanently via toolbar button or options menu. After association, the chat appears in both the global Chats menu and the project's thread list.

</domain>

<decisions>
## Implementation Decisions

### Confirmation flow
- Confirm dialog before association: "Add this chat to [Project]?" with Cancel/Confirm buttons
- Success feedback: Header updates in-place to show project name (no snackbar)
- After association: Stay in current chat view, header just updates
- Error handling: Error snackbar with retry option

### Toolbar button placement
- Button location: Toolbar area between message input and chat messages, next to LLM indicator
- Button style: Icon + "Add to Project" label for project-less chats
- For associated chats: Button disappears (nothing shown in this position)
- Note: This toolbar area will have more buttons added in future phases

### Options menu
- Keep BOTH toolbar button AND options menu item (dual entry points)
- Menu item hidden for chats that already have a project
- Menu item visible only for project-less chats

### Claude's Discretion
- Project picker modal layout and styling
- Icon choice for "Add to Project" button
- Exact wording of confirmation dialog
- Options menu item placement within menu

</decisions>

<specifics>
## Specific Ideas

- Toolbar button area is designed to accommodate future buttons (extensible design)
- Association is permanent and one-way (per ROADMAP.md key decisions)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 26-chat-project-association*
*Context gathered: 2026-02-01*
