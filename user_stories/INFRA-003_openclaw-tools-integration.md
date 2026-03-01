# INFRA-003 | OpenClaw Tools Integration

**Priority:** Medium
**Status:** In Progress
**Effort:** Medium
**Component:** Backend / Tools

---

## User Story

As a user,
I want OpenClaw skills (email, calendar, Twitter) available in XtraSkill,
so that the AI agent can perform real-world tasks beyond just chat.

---

## Acceptance Criteria

- [x] AC-1: Map XtraSkill MCP tools (search_documents, save_artifact) to OpenClaw skill calls
- [x] AC-2: Add tool for spawning sub-agents (OpenClaw sessions_spawn)
- [x] AC-3: Handle tool responses from OpenClaw back to XtraSkill format
- [x] AC-4: Document tool mapping in `backend/docs/openclaw-tools.md`
- [ ] AC-5: Add tool configuration UI in frontend (which tools to enable)

## Technical Notes

### Tools Implemented

| Tool | Description |
|------|-------------|
| `search_documents` | Search project documents |
| `save_artifact` | Save generated content |
| `send_email` | Send email (requires email skill) |
| `check_calendar` | Check Google Calendar |
| `post_twitter` | Post to Twitter/X |
| `spawn_subagent` | Spawn specialized sub-agent |
| `web_search` | Search the web |

### Sub-Agent Types

- `dev` - General development
- `debugger` - Bug fixing
- `code-reviewer` - Code review
- `architect` - Architecture planning

## Files Created

- `backend/app/services/openclaw_tools/__init__.py`
- `backend/app/services/openclaw_tools/tool_mapper.py`
- `backend/app/services/openclaw_tools/subagent.py`
- `backend/docs/OPENCLAW_TOOLS.md`

## Dependencies

- INFRA-002: OpenClaw as LLM Provider

## Related

- Blocks: Frontend settings for tool configuration
