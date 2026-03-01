# INFRA-002 | OpenClaw as LLM Provider

**Priority:** High
**Status:** In Progress
**Effort:** Medium
**Component:** Backend / LLM / Infrastructure

---

## User Story

As a user,
I want to use OpenClaw as an AI provider in XtraSkill,
so that I have an alternative to Claude Code and reduce platform dependency.

---

## Acceptance Criteria

- [x] AC-1: Add `LLMProvider.OPENCLAW` to `backend/app/services/llm/base.py`
- [x] AC-2: Create `OpenClawAdapter` in `backend/app/services/llm/openclaw_adapter.py` implementing `LLMAdapter`
- [x] AC-3: Register adapter in `LLMFactory._adapters`
- [x] AC-4: Add OpenClaw config to settings: `openclaw_api_key`, `openclaw_gateway_url`, `openclaw_agent_id`
- [x] AC-5: Support session reuse or spawn-per-request
- [x] AC-6: Convert OpenClaw SSE response to `StreamChunk` format
- [x] AC-7: Handle OpenClaw errors gracefully
- [ ] AC-8: Add "openclaw" to provider dropdown in frontend settings
- [x] AC-9: Document required environment variables in `.env.example`

## Technical Notes

### Adapter Interface Implemented:
- `stream_chat()` method with SSE support
- Converts OpenClaw events to StreamChunk format
- Handles text, thinking, tool_use, complete, error events

### OpenClaw API:
- Gateway URL: configurable (default `http://localhost:8080`)
- Chat endpoint: `POST /api/chat` with SSE
- Auth: Bearer token in `Authorization` header

### Session Strategy:
- Spawn-per-request for POC (simpler)
- Can be extended to session reuse

## Files Created/Modified

- `backend/app/services/llm/base.py` — Added OPENCLAW enum
- `backend/app/services/llm/openclaw_adapter.py` — New adapter
- `backend/app/services/llm/factory.py` — Registered adapter
- `backend/app/config.py` — Added OpenClaw settings

## Dependencies

- Requires INFRA-001: Docker Backend Setup
- Uses httpx (already in requirements.txt)

## Related

- Enables: Multi-provider fallback, A/B testing between Claude Code and OpenClaw
- Blocks: INFRA-003 (OpenClaw tools integration)
