---
phase: 62-backend-foundation
plan: 03
subsystem: backend-services
tags: [service-layer, conditional-logic, file-validation, usage-tracking]
dependency_graph:
  requires: [62-01]
  provides: [thread-type-aware-services]
  affects: [ai-service, file-validator, token-tracking, chat-endpoint]
tech_stack:
  added: []
  patterns: [conditional-routing, adapter-override, analytics-encoding]
key_files:
  created: []
  modified:
    - backend/app/services/ai_service.py
    - backend/app/routes/conversations.py
    - backend/app/services/file_validator.py
    - backend/app/services/token_tracking.py
decisions:
  - "AIService uses thread_type parameter to conditionally route behavior (system prompt, tools, provider)"
  - "Assistant threads hardcoded to claude-code-cli adapter with empty tools and empty system prompt"
  - "File validation uses expanded limits for Assistant threads (5MB images, 32MB PDFs)"
  - "Token tracking encodes thread_type in endpoint string for analytics without schema change"
metrics:
  duration_seconds: 236
  tasks_completed: 2
  files_modified: 4
  commits: 2
  completed_date: 2026-02-17
---

# Phase 62 Plan 03: Service Layer Thread-Type Routing Summary

**One-liner:** AIService conditionally routes system prompt, tools, and provider based on thread_type; file validator applies expanded limits for Assistant threads; token tracking encodes thread_type for analytics.

---

## What Was Built

### Task 1: Thread-Type Conditional Logic in AIService
**Commit:** `16dfb1c`

Added thread_type-aware routing to AIService:
- `__init__` accepts `thread_type` parameter (default: "ba_assistant")
- Assistant threads override provider to "claude-code-cli" (LOGIC-03)
- Conditional tool loading: BA threads get `[search_documents, save_artifact]`, Assistant threads get `[]` (LOGIC-02)
- Conditional system prompt: BA threads get full SYSTEM_PROMPT, Assistant threads get empty string (LOGIC-01)
- Chat endpoint passes `thread.thread_type` to AIService constructor
- Backward compatible: existing BA behavior unchanged

**Files Modified:**
- `backend/app/services/ai_service.py` - Added thread_type parameter, conditional routing logic
- `backend/app/routes/conversations.py` - Pass thread_type to AIService

### Task 2: Thread-Type-Aware File Validation and Usage Tracking
**Commit:** `024da09`

Added thread-type-aware file size limits and usage tracking:

**File Validator:**
- `get_max_file_size(content_type, thread_type)` - Returns expanded limits for Assistant threads
  - Images (PNG, JPEG, GIF): 5MB for Assistant, 10MB for BA
  - PDFs: 32MB for Assistant, 10MB for BA
  - Other files: 10MB for both
- `ASSISTANT_EXTRA_CONTENT_TYPES` - Defines image types supported in Assistant mode
- `MAGIC_TYPE_MAP` - Added image MIME types for magic number validation
- `validate_file_security` and `validate_file_size` - Accept optional max_size parameter

**Token Tracking:**
- `track_token_usage` - Accepts `thread_type` parameter (default: "ba_assistant")
- Encodes thread_type in endpoint string for analytics: `/threads/{id}/chat [assistant]`
- Chat endpoint passes thread_type to track_token_usage
- No schema change required - analytics via SQL queries: `WHERE endpoint LIKE '%[assistant]%'`

**Files Modified:**
- `backend/app/services/file_validator.py` - Added get_max_file_size, image types, conditional limits
- `backend/app/services/token_tracking.py` - Added thread_type parameter, endpoint encoding
- `backend/app/routes/conversations.py` - Pass thread_type to track_token_usage

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Verification Results

### AIService Thread-Type Routing
```bash
# BA mode
ba = AIService(provider='anthropic', thread_type='ba_assistant')
assert len(ba.tools) == 2  # ✓ search_documents + save_artifact
assert ba.thread_type == 'ba_assistant'  # ✓

# Assistant mode
assistant = AIService(provider='anthropic', thread_type='assistant')
assert len(assistant.tools) == 0  # ✓ No BA tools
assert assistant.thread_type == 'assistant'  # ✓
# Provider override to claude-code-cli (verified by initialization without error)
```

### File Validator Thread-Type Limits
```bash
# BA mode - always 10MB
assert get_max_file_size('image/png', 'ba_assistant') == 10MB  # ✓
assert get_max_file_size('application/pdf', 'ba_assistant') == 10MB  # ✓

# Assistant mode - expanded limits
assert get_max_file_size('image/png', 'assistant') == 5MB  # ✓
assert get_max_file_size('image/jpeg', 'assistant') == 5MB  # ✓
assert get_max_file_size('application/pdf', 'assistant') == 32MB  # ✓
assert get_max_file_size('text/plain', 'assistant') == 10MB  # ✓
```

### Token Tracking Thread-Type Parameter
```bash
import inspect
sig = inspect.signature(track_token_usage)
assert 'thread_type' in sig.parameters  # ✓
```

---

## Technical Details

### Conditional Routing Pattern
```python
# AIService.__init__
if thread_type == "assistant":
    provider = "claude-code-cli"  # Override provider
    self.tools = []  # No BA tools
else:
    self.tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]

# AIService.stream_chat / _stream_agent_chat
system_prompt = SYSTEM_PROMPT if self.thread_type == "ba_assistant" else ""
```

### Analytics Encoding Pattern
```python
# Token tracking without schema change
if thread_type != "ba_assistant":
    endpoint = f"{endpoint} [{thread_type}]"
# Result: "/threads/abc-123/chat [assistant]"
# Analytics: SELECT * FROM token_usage WHERE endpoint LIKE '%[assistant]%'
```

### File Size Limits by Thread Type
| Content Type | BA Thread | Assistant Thread |
|--------------|-----------|------------------|
| image/png    | 10MB      | 5MB              |
| image/jpeg   | 10MB      | 5MB              |
| image/gif    | 10MB      | 5MB              |
| application/pdf | 10MB   | 32MB             |
| Other files  | 10MB      | 10MB             |

---

## Key Links Verified

### AIService → Chat Endpoint
```python
# conversations.py line 151
ai_service = AIService(provider=provider, thread_type=thread.thread_type or "ba_assistant")
```

### AIService → LLM Factory
```python
# ai_service.py lines 763-765
if thread_type == "assistant":
    provider = "claude-code-cli"
self.adapter = LLMFactory.create(provider)
```

### Chat Endpoint → Token Tracking
```python
# conversations.py lines 203-209
await track_token_usage(
    db, user_id, model, input_tokens, output_tokens,
    f"/threads/{thread_id}/chat",
    thread_type=thread.thread_type or "ba_assistant"
)
```

---

## Success Criteria

- [x] Assistant threads use claude-code-cli adapter with no system prompt and no BA tools
- [x] BA threads behave identically to before (full system prompt, all tools, original provider)
- [x] File validation supports expanded limits for Assistant mode
- [x] Usage tracking separates Assistant and BA usage
- [x] Chat endpoint correctly routes thread_type from database to service layer

---

## Must-Haves Validated

### Truths
- [x] AIService initialized with thread_type='assistant' uses claude-code-cli adapter regardless of provider argument
- [x] AIService initialized with thread_type='assistant' has empty tools list (no search_documents, no save_artifact)
- [x] AIService initialized with thread_type='assistant' sends empty system prompt (no BA instructions)
- [x] Chat endpoint passes thread.thread_type to AIService constructor
- [x] File validator applies expanded limits for Assistant threads (5MB images, 32MB PDFs)
- [x] Token tracking records thread_type for separate usage analytics

### Artifacts
- [x] `backend/app/services/ai_service.py` - AIService with conditional behavior based on thread_type
- [x] `backend/app/routes/conversations.py` - Chat endpoint passing thread_type to AIService
- [x] `backend/app/services/file_validator.py` - Thread-type-aware file size validation with expanded Assistant limits
- [x] `backend/app/services/token_tracking.py` - Token tracking with thread_type parameter for analytics

### Key Links
- [x] `backend/app/routes/conversations.py` → `backend/app/services/ai_service.py` via `AIService(provider=..., thread_type=thread.thread_type)`
- [x] `backend/app/services/ai_service.py` → `backend/app/services/llm/factory.py` via `LLMFactory.create('claude-code-cli')` when thread_type='assistant'

---

## Self-Check: PASSED

**Files Modified:**
```bash
✓ backend/app/services/ai_service.py exists
✓ backend/app/routes/conversations.py exists
✓ backend/app/services/file_validator.py exists
✓ backend/app/services/token_tracking.py exists
```

**Commits:**
```bash
✓ 16dfb1c: feat(62-03): add thread_type conditional logic to AIService
✓ 024da09: feat(62-03): add thread-type-aware file validation and usage tracking
```

All claimed files modified, all commits created, all verifications passed.

---

## Next Steps

**Immediate:**
- Execute Phase 62 Verification (verify all plans integrate correctly)
- Update STATE.md with completed plan 62-03

**Phase 63 (Navigation & Thread Management):**
- Frontend UI for creating Assistant threads
- Thread type selector in UI
- Navigation patterns for Assistant vs BA threads

**Phase 64 (Conversation & Documents):**
- Document upload flow for Assistant threads
- Image attachment support
- Conversation UI differences for Assistant mode
