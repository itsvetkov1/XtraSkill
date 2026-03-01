# INFRA-002 | OpenClaw as LLM Provider

**Priority:** High
**Status:** Open
**Effort:** Medium
**Component:** Backend / LLM / Infrastructure

---

## User Story

As a user,
I want to use OpenClaw as an AI provider in XtraSkill,
so that I have an alternative to Claude Code and reduce platform dependency.

---

## Problem

Currently XtraSkill relies on Claude Code (CLI/SDK) as the primary agentic backend. If Claude Code has issues or pricing changes, users have no alternative within XtraSkill.

---

## Acceptance Criteria

- [ ] AC-1: Add `LLMProvider.OPENCLAW` to `backend/app/services/llm/base.py`
- [ ] AC-2: Create `OpenClawAdapter` in `backend/app/services/llm/openclaw_adapter.py` implementing `LLMAdapter`
- [ ] AC-3: Register adapter in `LLMFactory._adapters`
- [ ] AC-4: Add OpenClaw config to settings: `OPENCLAW_API_KEY`, `OPENCLAW_GATEWAY_URL`, `OPENCLAW_AGENT_ID`
- [ ] AC-5: Support session reuse (map thread_id → session_key) or spawn-per-request
- [ ] AC-6: Convert OpenClaw SSE response to `StreamChunk` format
- [ ] AC-7: Handle OpenClaw errors gracefully (connection, auth, timeout)
- [ ] AC-8: Add "openclaw" to provider dropdown in frontend settings
- [ ] AC-9: Document required environment variables in `.env.example`

## Technical Notes

### Adapter Interface (must implement):
```python
class LLMAdapter(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        pass
```

### OpenClaw API:
- Gateway URL: configurable (default `http://localhost:8080`)
- Chat endpoint: `POST /api/chat` with SSE
- Auth: Bearer token in `Authorization` header

### Session Strategy:
- **Option A (simpler):** Spawn new session per chat request, no memory between requests
- **Option B (better):** Map XtraSkill thread_id → OpenClaw session_key, reuse session
- Recommendation: Start with Option A for POC, upgrade to B

## Dependencies

- INFRA-001: Docker Backend Setup (OpenClaw runs in Docker or alongside)
- LLMAdapter interface already exists

## Related

- Enables: Multi-provider fallback, A/B testing between Claude Code and OpenClaw
