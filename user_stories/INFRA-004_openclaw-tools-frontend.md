# INFRA-004 | OpenClaw Tools Frontend UI

**Priority:** Medium
**Status:** In Progress
**Effort:** Medium
**Component:** Frontend / Settings

---

## User Story

As a user,
I want to configure which OpenClaw tools are available in XtraSkill,
so that I can control what the AI can do (e.g., disable email/Twitter if not configured).

---

## Acceptance Criteria

- [x] AC-1: Add "Tool Configuration" section in Settings screen
- [x] AC-2: List all available OpenClaw tools with toggle switches
- [x] AC-3: Save tool preferences to SharedPreferences
- [x] AC-4: Show which tools require external configuration (email, calendar, Twitter)
- [x] AC-5: Persist preferences per user (via SharedPreferences)

## Technical Notes

### Tools Configured

| Tool | Requires External Config |
|------|------------------------|
| Search Documents | No |
| Save Artifact | No |
| Send Email | Yes (email skill) |
| Check Calendar | Yes (Google OAuth) |
| Post Twitter | Yes (Twitter API) |
| Spawn Sub-Agent | No |
| Web Search | No |

### Files Modified

- `frontend/lib/providers/tool_config_provider.dart` — New provider
- `frontend/lib/providers/provider_provider.dart` — Added openclaw
- `frontend/lib/core/constants.dart` — Added OpenClaw config
- `frontend/lib/screens/settings_screen.dart` — Added tools section
- `frontend/lib/main.dart` — Wired up provider

## Dependencies

- INFRA-003: OpenClaw Tools Integration
