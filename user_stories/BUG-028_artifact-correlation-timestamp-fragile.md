# BUG-028: Artifact Correlation Uses Fragile Timestamp Window

**Priority:** Medium
**Status:** Done

**Resolution:** Fixed by BUG-016 marker approach. The ARTIFACT_CREATED marker is now appended to assistant messages in the database, making timestamp correlation unnecessary. The `_identify_fulfilled_pairs()` function detects markers in message content, which is reliable regardless of server load or clock skew.
**Component:** Backend / Conversation Service
**Discovered:** 2026-02-25

---

## User Story

As a user generating BRDs and other artifacts,
I want artifact-to-message correlation to be reliable,
So that fulfilled artifact requests are properly filtered from conversation history.

---

## Problem

`_identify_fulfilled_pairs()` in `conversation_service.py` correlates artifacts to the messages that triggered them using a ±5-second timestamp window:

```python
ARTIFACT_CORRELATION_WINDOW = timedelta(seconds=5)
```

This is fragile. On a slow host (heavy DB load, large BRD generation with many tool calls), the window can expire before the artifact is created. When correlation fails:

1. The "generate BRD" exchange stays in conversation history instead of being filtered out
2. Conversation context grows with fulfilled-but-unfiltered artifact requests
3. This contributes to the original BUG-016 problem (artifact generation multiplies) by leaving stale generation requests in context

### Why Timestamp Matching is Fragile

- BRD generation involves multiple tool calls (search_documents → format → save_artifact) — each adds latency
- Database write of the artifact record happens after the tool chain completes
- Server clock skew between request processing and artifact save is not bounded
- Under load, the 5s window is not generous enough

---

## Acceptance Criteria

- [ ] Artifacts are linked to messages via explicit foreign key (`trigger_message_id` on Artifact model), not timestamp proximity
- [ ] `_identify_fulfilled_pairs()` uses the FK relationship instead of timestamp window
- [ ] Existing artifacts without FK get a migration to backfill where possible (or are left as-is with timestamp fallback)
- [ ] BRD generation under load no longer fails to correlate

---

## Alternative: Increase Window

A quick-and-dirty fix would be to increase `ARTIFACT_CORRELATION_WINDOW` to 30s or 60s. This reduces failure probability but doesn't eliminate the root cause. Consider this as an interim fix if the FK migration is deferred.

---

## Technical References

- `backend/app/services/conversation_service.py` — `_identify_fulfilled_pairs()`
- `ARTIFACT_CORRELATION_WINDOW = timedelta(seconds=5)` — The fragile window
- Related: BUG-016 (artifact generation multiplies)
- Related: BUG-019 (history filtering for fulfilled requests)

---

*Created: 2026-02-25*
*Source: ASSISTANT_FLOW_REVIEW.md — ISSUE-10*
