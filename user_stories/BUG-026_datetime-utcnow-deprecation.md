# BUG-026: datetime.utcnow() Deprecation Across Codebase

**Priority:** Medium
**Status:** Open
**Component:** Backend / Multiple Files
**Discovered:** 2026-02-25

---

## User Story

As a developer,
I want the codebase to use non-deprecated datetime APIs,
So that we don't hit runtime warnings now or breakage in future Python versions.

---

## Problem

`datetime.utcnow()` was deprecated in Python 3.12 (PEP 587). The pattern appears in default column values and explicit calls throughout the backend:

- `backend/app/models.py` — Column defaults
- `backend/app/routes/threads.py` — Explicit calls
- `backend/app/services/conversation_service.py` — Explicit calls
- Potentially other service files

Columns are declared `DateTime(timezone=True)` but receive naive datetime objects from `utcnow()`. This mismatch can cause timezone-related bugs when the database stores timezone-aware datetimes alongside naive ones.

### Current Behavior
```python
created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

### Correct Replacement
```python
from datetime import datetime, timezone

created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

---

## Acceptance Criteria

- [ ] All occurrences of `datetime.utcnow()` replaced with `datetime.now(timezone.utc)`
- [ ] All occurrences of `datetime.utcnow` (without parens, used as default callable) replaced with `lambda: datetime.now(timezone.utc)`
- [ ] `from datetime import timezone` added where needed
- [ ] No deprecation warnings when running with Python 3.12+
- [ ] Existing stored datetimes remain compatible (no migration needed — the values are equivalent)

---

## Scope

Search for: `utcnow` across all `.py` files in `backend/`.

---

## Technical References

- Python 3.12 deprecation: https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow
- `backend/app/models.py` — Primary location (column defaults)
- `backend/app/routes/threads.py` — Explicit usage
- `backend/app/services/conversation_service.py` — Explicit usage

---

*Created: 2026-02-25*
*Source: ASSISTANT_FLOW_REVIEW.md — ISSUE-08*
