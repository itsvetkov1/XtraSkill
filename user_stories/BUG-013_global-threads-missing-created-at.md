# BUG-013: Global Threads API Missing created_at Field

**Priority:** Critical
**Status:** Done
**Component:** Backend - Threads API
**Discovered:** 2026-02-02 (Phase 26 regression testing)
**Fixed:** 2026-02-02

---

## Problem

When user refreshes the Chats page, the app crashes with:

```
Type error: type null is not a subtype of type 'String'
```

The frontend expects `created_at` in thread responses, but the `GlobalThreadListResponse` model was missing this field.

---

## Root Cause

The `GlobalThreadListResponse` Pydantic model in `backend/app/routes/threads.py` did not include `created_at` field:

```python
class GlobalThreadListResponse(BaseModel):
    id: str
    title: Optional[str]
    updated_at: str           # Present
    last_activity_at: str     # Present
    # created_at: str         # MISSING - caused null error
    ...
```

Frontend's `Thread.fromJson` requires `created_at`:
```dart
createdAt: DateTime.parse(json['created_at']),  // Fails when null
```

---

## Acceptance Criteria

- [x] GlobalThreadListResponse includes created_at field
- [x] GET /api/threads returns created_at for all threads
- [x] Chats page loads correctly after refresh
- [x] No type errors in browser console

---

## Fix

Added `created_at: str` to `GlobalThreadListResponse` model and included it in the response builder:

```python
class GlobalThreadListResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str           # ADDED
    updated_at: str
    ...

# In list_all_threads endpoint:
GlobalThreadListResponse(
    id=t.id,
    created_at=t.created_at.isoformat(),  # ADDED
    ...
)
```

**Tests:** `backend/tests/test_global_threads.py`

---

## Technical References

- `backend/app/routes/threads.py` (FIXED)
- `frontend/lib/models/thread.dart` - Thread.fromJson

---

*Created: 2026-02-02*
*Fixed: 2026-02-02*
