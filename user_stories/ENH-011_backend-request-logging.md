# ENH-011: Comprehensive Backend Request Logging

**Priority:** High
**Status:** Done

**Resolution:** Comprehensive logging is already implemented via `logging_service`. The `AIService.stream_chat()` logs LLM requests, tool executions, responses, and errors. `build_conversation_context()` logging happens via the logging service. Structured logging with correlation IDs is in place.
**Component:** Backend / Observability

---

## User Story

As a developer debugging issues, I want comprehensive logging throughout the backend request lifecycle,
so that I can trace exactly what happens when requests are processed.

---

## Problem

Current backend logging is minimal. When debugging issues like BUG-016 (artifact generation multiplies),
it's difficult to understand:

1. What requests are being made to which endpoints
2. What parameters are passed to services
3. What the LLM receives (conversation context)
4. What tool calls are made and their results
5. How the response flows back to the client

Without this visibility, debugging requires extensive code reading and guesswork.

---

## Acceptance Criteria

### Request Lifecycle Logging

- [ ] Log incoming HTTP requests with:
  - Endpoint path and method
  - Request ID (correlation ID)
  - User ID (from JWT, if authenticated)
  - Timestamp

- [ ] Log outgoing HTTP responses with:
  - Request ID (for correlation)
  - Status code
  - Response time (ms)

### AI Service Logging

- [ ] Log when `AIService.stream_chat()` is called with:
  - Thread ID
  - Message count in conversation context
  - Total estimated tokens in context
  - Provider being used

- [ ] Log LLM API calls with:
  - Model name
  - Input token estimate
  - Tool definitions sent (names only)

- [ ] Log tool executions with:
  - Tool name
  - Input parameters (sanitized - no full content)
  - Execution time
  - Success/failure

- [ ] Log LLM responses with:
  - Output token count
  - Tool calls made (names only)
  - Stop reason

### Conversation Context Logging

- [ ] Log when `build_conversation_context()` is called with:
  - Thread ID
  - Total messages loaded
  - Messages by role (user/assistant count)
  - Truncation applied (yes/no)

### Error Logging

- [ ] Ensure all exceptions are logged with:
  - Full stack trace
  - Request context (thread ID, user ID, endpoint)
  - Timestamp

---

## Technical Approach

### Logging Format

Use structured logging with JSON format for parseability:

```python
logger.info("llm_request", extra={
    "request_id": "abc-123",
    "thread_id": "xyz-456",
    "model": "claude-sonnet-4-5-20250514",
    "context_messages": 15,
    "estimated_tokens": 4500,
    "tools": ["search_documents", "save_artifact"]
})
```

### Log Levels

| Level | Use For |
|-------|---------|
| DEBUG | Detailed data (full prompts, responses) - disabled in production |
| INFO | Request lifecycle events, LLM calls, tool executions |
| WARNING | Retries, rate limits, degraded performance |
| ERROR | Exceptions, failures, unexpected states |

### Files to Modify

- `backend/app/main.py` - Add request/response middleware logging
- `backend/app/services/ai_service.py` - Add service-level logging
- `backend/app/services/conversation_service.py` - Add context building logging
- `backend/app/routes/conversations.py` - Add endpoint-specific logging
- `backend/app/services/llm/anthropic_adapter.py` - Add LLM call logging

### Configuration

Add log level configuration to `backend/app/config.py`:

```python
log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
log_format: str = "json"  # json or text
```

---

## Non-Goals

- Log aggregation service (Datadog, CloudWatch, etc.) - future enhancement
- Log rotation/retention policies - handled by hosting platform
- Performance metrics/APM - separate concern

---

## Testing

Manual verification:
1. Send chat request
2. Check logs show full request lifecycle
3. Verify no PII or secrets in logs
4. Confirm log format is parseable

---

## Technical References

- `backend/app/services/ai_service.py` - Primary logging target
- `backend/app/services/conversation_service.py` - Context building
- `backend/app/routes/conversations.py` - HTTP layer
- `backend/app/services/llm/anthropic_adapter.py` - LLM calls

---

*Created: 2026-02-04*
*Related to: BUG-016 debugging, general observability*
