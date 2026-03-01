# INFRA-003 | OpenClaw Tools Integration

**Priority:** Medium
**Status:** Open
**Effort:** Medium
**Component:** Backend / Tools

---

## User Story

As a user,
I want OpenClaw skills (email, calendar, Twitter) available in XtraSkill,
so that the AI agent can perform real-world tasks beyond just chat.

---

## Acceptance Criteria

- [ ] AC-1: Map XtraSkill MCP tools (search_documents, save_artifact) to OpenClaw skill calls
- [ ] AC-2: Add tool for spawning sub-agents (OpenClaw sessions_spawn)
- [ ] AC-3: Handle tool responses from OpenClaw back to XtraSkill format
- [ ] AC-4: Document tool mapping in `backend/docs/openclaw-tools.md`
- [ ] AC-5: Add tool configuration UI in frontend (which tools to enable)

## Technical Notes

OpenClaw provides these tool categories:
- **Skills:** email, calendar, Twitter, web search, browser
- **Sessions:** spawn, sessions_send, sessions_list
- **Messaging:** Telegram, Discord, Signal

XtraSkill currently has:
- search_documents (document_search.py)
- save_artifact (brd_generator.py)

Mapping strategy:
- Keep existing tools working with Claude Code
- Add OpenClaw tools only when using OpenClaw provider

## Dependencies

- INFRA-002: OpenClaw as LLM Provider
