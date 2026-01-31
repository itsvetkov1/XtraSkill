---
phase: 20-database-api
plan: 01
subsystem: backend-llm
tags: [database, api, provider-binding, threads, migration]
dependency-graph:
  requires: [19-02]
  provides: [Thread.model_provider column, provider-aware Thread API, provider-routed chat]
  affects: [Phase 21 frontend provider selection, end-to-end provider switching]
tech-stack:
  added: []
  patterns: [column migration, request validation, provider binding]
key-files:
  created:
    - backend/alembic/versions/c07d77df9b74_add_model_provider_to_threads.py
  modified:
    - backend/app/models.py
    - backend/app/routes/threads.py
    - backend/app/routes/conversations.py
decisions:
  - id: DEC-20-01-01
    choice: Nullable column with application-level default
    rationale: Existing threads get NULL, application defaults to 'anthropic' for backward compatibility
  - id: DEC-20-01-02
    choice: Provider validation at API layer with 400 response
    rationale: Explicit error message helps frontend developers, prevents invalid data in database
metrics:
  duration: 4 minutes
  completed: 2026-01-31
---

# Phase 20 Plan 01: Thread Provider Database and API Summary

Added model_provider column to Thread model and wired provider selection through API endpoints to AIService.

## What Was Done

### Task 1: Add model_provider Column to Thread Model

Modified `backend/app/models.py`:

```python
# LLM provider binding (anthropic, google, deepseek)
model_provider: Mapped[Optional[str]] = mapped_column(
    String(20),
    nullable=True,
    default="anthropic"
)
```

Created Alembic migration `c07d77df9b74_add_model_provider_to_threads.py`:
- Uses batch_alter_table for SQLite compatibility
- Adds nullable VARCHAR(20) column
- Existing threads get NULL (default to anthropic in application)

Applied migration successfully.

### Task 2: Update Thread API Endpoints

Modified `backend/app/routes/threads.py`:

1. **Added validation constant:**
   ```python
   VALID_PROVIDERS = ["anthropic", "google", "deepseek"]
   ```

2. **Updated ThreadCreate schema:**
   ```python
   model_provider: Optional[str] = Field(None, max_length=20)
   ```

3. **Updated ThreadResponse schema:**
   ```python
   model_provider: Optional[str] = "anthropic"  # Default for backward compat
   ```

4. **Added provider validation in create_thread:**
   - Returns 400 Bad Request for invalid providers
   - Defaults to "anthropic" if not specified

5. **Updated all response constructions:**
   - create_thread, list_threads, get_thread, rename_thread
   - All include `model_provider=thread.model_provider or "anthropic"`

### Task 3: Wire Chat Endpoint to Use Thread's Provider

Modified `backend/app/routes/conversations.py`:

```python
# Use thread's bound provider (set at creation time)
# This ensures consistency - conversations stay with their original provider
provider = thread.model_provider or "anthropic"
ai_service = AIService(provider=provider)
```

## Commits

| Commit | Description |
|--------|-------------|
| f6cfedb | feat(20-01): add model_provider column to Thread model |
| 53ffe1f | feat(20-01): add provider support to Thread API endpoints |
| d75af26 | feat(20-01): wire chat endpoint to use thread's provider |

## Verification

- [x] Thread.model_provider column exists in model
- [x] Migration applied successfully (c07d77df9b74 is head)
- [x] Database schema includes model_provider column
- [x] ThreadCreate accepts optional model_provider
- [x] ThreadResponse includes model_provider in all response types
- [x] Invalid provider returns 400 Bad Request
- [x] Chat endpoint passes thread.model_provider to AIService
- [x] Existing threads work (default to anthropic)

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Phase 20-01 establishes the foundation for multi-provider support:

**API Contract Now:**
- POST /projects/{id}/threads accepts `{"model_provider": "google"}`
- GET responses include `"model_provider": "google"`
- Chat uses thread's provider to select AIService adapter

**Ready for Phase 21 (Frontend):**
- Add provider selector dropdown in thread creation UI
- Display current provider in thread list/detail
- Provider persists across sessions via database

**Ready for Phase 22 (Validation):**
- Test creating threads with each provider
- Verify chat routes to correct adapter
- Confirm existing threads still use Claude

---

*Summary created: 2026-01-31*
*Plan duration: 4 minutes*
