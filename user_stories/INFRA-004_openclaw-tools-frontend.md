# INFRA-004 | OpenClaw Tools Frontend UI

**Priority:** Medium
**Status:** Open
**Effort:** Medium
**Component:** Frontend / Settings

---

## User Story

As a user,
I want to configure which OpenClaw tools are available in XtraSkill,
so that I can control what the AI can do (e.g., disable email/Twitter if not configured).

---

## Acceptance Criteria

- [ ] AC-1: Add "Tool Configuration" section in Settings screen
- [ ] AC-2: List all available OpenClaw tools with toggle switches
- [ ] AC-3: Save tool preferences to backend/user settings
- [ ] AC-4: Show which tools require external configuration (email, calendar, Twitter)
- [ ] AC-5: Persist preferences per user

## Technical Notes

Tools to configure:
- search_documents (always available)
- save_artifact (always available)
- send_email (requires email skill)
- check_calendar (requires calendar skill)
- post_twitter (requires Twitter skill)
- spawn_subagent (optional)
- web_search (always available)

## Dependencies

- INFRA-003: OpenClaw Tools Integration

## Related

- Follow-up to INFRA-003 AC-5
