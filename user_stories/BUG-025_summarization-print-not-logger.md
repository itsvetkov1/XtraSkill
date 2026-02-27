# BUG-025: Summarization Service Uses print() Instead of Logger

**Priority:** Low
**Status:** Open
**Component:** Backend / Summarization Service
**Discovered:** 2026-02-25

---

## User Story

As a developer debugging summarization failures,
I want errors captured by the logging infrastructure,
So that I can find them in structured logs instead of losing them to stdout.

---

## Problem

`backend/app/services/summarization_service.py` line 167 uses `print()` for error reporting:

```python
except Exception as e:
    print(f"Summarization failed: {e}")  # Not captured by logging infrastructure
    return None
```

The project added structured logging infrastructure in v1.9.5. This `print()` call bypasses it entirely — errors go to stdout and are invisible to log queries, monitoring, and the ENH-011 request logging initiative.

Summarization failures are silent and untraceable.

---

## Acceptance Criteria

- [ ] Replace `print()` with `logger.error()` using the module-level logger
- [ ] Include the exception traceback: `logger.error("Summarization failed", exc_info=True)`
- [ ] Verify the summarization service has a logger instance (add `logger = logging.getLogger(__name__)` if missing)

---

## Technical References

- `backend/app/services/summarization_service.py:167` — The print() call
- Related: ENH-011 (backend request logging initiative)

---

*Created: 2026-02-25*
*Source: ASSISTANT_FLOW_REVIEW.md — ISSUE-07*
