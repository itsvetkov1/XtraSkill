---
phase: 08-settings-page-user-preferences
plan: 01
subsystem: backend-auth
tags: [user-model, oauth, api, token-tracking]

dependency-graph:
  requires:
    - "Phase 2: OAuth authentication infrastructure"
    - "Phase 3: Token tracking service"
  provides:
    - "User.display_name field for profile display"
    - "/auth/me enhanced with display_name"
    - "/auth/usage endpoint for token statistics"
  affects:
    - "08-02: Frontend settings page (consumes these APIs)"
    - "Future: User preferences storage"

tech-stack:
  added: []
  patterns:
    - "SQLite migration via PRAGMA table_info + ALTER TABLE"
    - "Nullable fields for backward compatibility with existing users"

file-tracking:
  key-files:
    created: []
    modified:
      - backend/app/models.py
      - backend/app/services/auth_service.py
      - backend/app/routes/auth.py
      - backend/app/database.py

decisions:
  - id: "08-01-d1"
    description: "display_name nullable for existing users"
    rationale: "Users created before this change won't have display_name until re-login"
  - id: "08-01-d2"
    description: "Update display_name on every login"
    rationale: "Stay current with provider if user changes name in Google/Microsoft"
  - id: "08-01-d3"
    description: "SQLite migration via ALTER TABLE"
    rationale: "SQLAlchemy create_all() doesn't modify existing tables"

metrics:
  duration: "~2 minutes"
  completed: "2026-01-29"
---

# Phase 8 Plan 1: Backend Settings Infrastructure Summary

Backend API infrastructure enabling Settings page user profile and token usage display.

## One-liner

Added User.display_name from OAuth providers and /auth/usage endpoint for monthly token statistics.

## What Was Built

### 1. User Model Enhancement

**File:** `backend/app/models.py`

Added `display_name` field to User model:
- `display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)`
- Nullable to support existing users who haven't re-logged

### 2. OAuth Service Updates

**File:** `backend/app/services/auth_service.py`

Google OAuth now extracts:
```python
display_name = user_info.get("name")
```

Microsoft OAuth now extracts:
```python
display_name = user_info.get("displayName")
```

`_upsert_user()` updated to:
- Accept `display_name` parameter
- Store on new user creation
- Update on existing user login (keeps name current with provider)

### 3. Auth API Enhancements

**File:** `backend/app/routes/auth.py`

`GET /auth/me` now returns:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "John Doe",
  "oauth_provider": "google",
  "created_at": "2026-01-29T..."
}
```

New `GET /auth/usage` endpoint:
```json
{
  "total_cost": 0.0,
  "total_requests": 0,
  "total_input_tokens": 0,
  "total_output_tokens": 0,
  "month_start": "2026-01-01T00:00:00",
  "budget": 50.0
}
```

### 4. SQLite Migration

**File:** `backend/app/database.py`

Added `_run_migrations()` function:
- Checks if `display_name` column exists using `PRAGMA table_info(users)`
- Auto-adds column via `ALTER TABLE users ADD COLUMN display_name VARCHAR(255)`
- Called after `create_all()` in `init_db()`

## Commits

| Hash | Message |
|------|---------|
| 3f63386 | feat(08-01): add display_name to User model and OAuth services |
| c16138a | feat(08-01): add /auth/usage endpoint and enhance /auth/me |
| e99e2a8 | feat(08-01): add SQLite migration for display_name column |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- Model check: `display_name` present in models.py (1 occurrence)
- Service check: `display_name` in auth_service.py (8 occurrences - extract, pass, store)
- Route check: `usage` in auth.py (11 occurrences - endpoint, import, usage)
- Syntax check: All imports successful

## Next Phase Readiness

**Ready for 08-02:** Frontend settings page can now consume:
- `GET /auth/me` for user profile with display_name
- `GET /auth/usage` for token budget display

**Frontend considerations:**
- Handle null `display_name` gracefully (show email as fallback)
- Format token cost as currency
- Show progress bar for budget usage percentage
