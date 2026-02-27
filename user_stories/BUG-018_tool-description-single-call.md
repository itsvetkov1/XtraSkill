# BUG-018: Tool Description Single-Call Enforcement

**Priority:** Critical
**Status:** Done - Already implemented (line removed)
**Component:** Backend / AI Service
**Parent:** BUG-016 (Artifact generation multiplies on repeated requests)
**Implementation Order:** 2 of 4 (implement after BUG-017)

---

## User Story

As a user generating artifacts,
I want the save_artifact tool to enforce single-call behavior,
so that the model doesn't call the tool multiple times per request.

---

## Problem

The current `SAVE_ARTIFACT_TOOL` description at `ai_service.py:663` contains:

```
"You may call this tool multiple times to create multiple artifacts."
```

This line actively encourages the accumulation behavior described in BUG-016. The model
interprets it as permission to call `save_artifact` repeatedly when it sees multiple
generation requests in history.

---

## Solution

Replace the permissive multi-call instruction with a single-call enforcement that still
allows explicit user-requested re-generation.

### Changes Required

**File:** `backend/app/services/ai_service.py`

**Section:** `SAVE_ARTIFACT_TOOL` description (lines 649-683)

**Remove this line (line 663):**
```
"You may call this tool multiple times to create multiple artifacts."
```

**Replace with:**
```
"Call this tool ONCE per user request. After generating an artifact, STOP and present
the result. Do not call again unless the user sends a NEW message explicitly requesting
another artifact or re-generation of the same one."
```

**No other changes to the tool definition.** History awareness is handled by the system
prompt rule (BUG-017). Tool description stays focused on single-call behavior.

---

## Acceptance Criteria

- [ ] "You may call this tool multiple times" line is removed
- [ ] Replacement text enforces single-call: "Call this tool ONCE per user request"
- [ ] Replacement allows explicit re-generation: "unless the user sends a NEW message"
- [ ] Tool description does NOT contain history-awareness logic (that's BUG-017's job)
- [ ] Tool `input_schema` is unchanged
- [ ] Existing test `test_service_architecture.py::test_ai_service_defines_tools_inline` still passes

---

## Technical References

- `backend/app/services/ai_service.py:649-683` — SAVE_ARTIFACT_TOOL definition
- `backend/app/services/ai_service.py:663` — Line to replace

---

## Testing Notes

Prompt-only change. Verification requires:
1. Automated: Confirm new text is present in SAVE_ARTIFACT_TOOL description
2. Manual: Generate artifact, then request another in same thread — should produce exactly 1 new artifact

---

*Created: 2026-02-04*
*Part of BUG-016 layered fix (Layer 2: Tool Description)*
