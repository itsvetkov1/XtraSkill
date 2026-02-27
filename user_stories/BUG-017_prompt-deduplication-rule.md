# BUG-017: System Prompt Artifact Deduplication Rule

**Priority:** Critical
**Status:** Done - Already implemented (priority 2 rule exists)
**Component:** Backend / AI Service
**Parent:** BUG-016 (Artifact generation multiplies on repeated requests)
**Implementation Order:** 1 of 4 (implement first)

---

## User Story

As a user generating artifacts in a conversation,
I want the AI to only act on my most recent artifact request,
so that prior fulfilled requests in conversation history don't cause duplicate artifacts.

---

## Problem

The system prompt in `ai_service.py:114-617` has no instruction telling the model to ignore
prior artifact generation requests already present in conversation history. When the model
sees N prior generation requests, it treats all N as actionable.

---

## Solution

Add a new critical rule at **priority 2** in the `<critical_rules>` section of `SYSTEM_PROMPT`.
Use positive framing with reasoning context.

### Changes Required

**File:** `backend/app/services/ai_service.py`

**Section:** `SYSTEM_PROMPT` → `<critical_rules>` (around line 120)

**New rule (insert as priority 2):**

```xml
<rule priority="2">ARTIFACT DEDUPLICATION - ONLY act on the MOST RECENT user message
when generating artifacts. Prior artifact requests in conversation history have already
been fulfilled. If you see save_artifact tool results in history, those requests are
COMPLETE. Do not re-generate artifacts for them.</rule>
```

**Renumber existing rules:**

| Before | After |
|--------|-------|
| Priority 1: ASK ONE QUESTION AT A TIME | Priority 1: ASK ONE QUESTION AT A TIME (unchanged) |
| Priority 2: PROACTIVE MODE DETECTION | Priority 3: PROACTIVE MODE DETECTION |
| Priority 3: ZERO-ASSUMPTION PROTOCOL | Priority 4: ZERO-ASSUMPTION PROTOCOL |
| Priority 4: TECHNICAL BOUNDARY ENFORCEMENT | Priority 5: TECHNICAL BOUNDARY ENFORCEMENT |
| Priority 5: TOOL USAGE | Priority 6: TOOL USAGE |

---

## Acceptance Criteria

- [ ] New deduplication rule exists at priority 2 in `<critical_rules>`
- [ ] Rule uses positive framing: "ONLY act on the MOST RECENT user message"
- [ ] Rule provides reasoning: "Prior requests have already been fulfilled"
- [ ] Rule references save_artifact results as completion evidence
- [ ] Existing rules renumbered correctly (priorities 3-6)
- [ ] System prompt still parses correctly (valid XML structure)
- [ ] Existing test `test_service_architecture.py::test_ai_service_system_prompt_is_substantial` still passes

---

## Technical References

- `backend/app/services/ai_service.py:114-617` — SYSTEM_PROMPT constant
- `backend/app/services/ai_service.py:120-126` — Current `<critical_rules>` section

---

## Testing Notes

This is a prompt-only change. Verification requires:
1. Automated: Confirm rule text is present in SYSTEM_PROMPT
2. Manual: Send two artifact generation requests in same thread, verify only 1 artifact on second request

---

*Created: 2026-02-04*
*Part of BUG-016 layered fix (Layer 1: Prompt Engineering)*
