---
phase: 40-prompt-engineering-fixes
plan: 01
subsystem: llm
tags: [anthropic, claude, prompt-engineering, deduplication, system-prompt, tool-description]

# Dependency graph
requires:
  - phase: 39-doc-nav-improvements
    provides: BUG-016 identified (artifact multiplication root cause)
provides:
  - SYSTEM_PROMPT with 6-rule critical_rules including ARTIFACT DEDUPLICATION at priority 2
  - SAVE_ARTIFACT_TOOL description enforces single-call behavior
  - Deduplication via prompt layer (Layer 1) and tool description layer (Layer 2)
  - Re-generation escape hatch prevents blocking legitimate user requests
affects: [41-structural-history-filtering, 42-silent-artifact-generation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Defense-in-depth deduplication: prompt rule + tool description + history annotation + code path separation"
    - "Positive framing in prompt rules: ONLY act on MOST RECENT (not Don't act on previous)"
    - "Explicit escape hatches in deduplication rules to preserve user agency"

key-files:
  created: []
  modified:
    - backend/app/services/ai_service.py

key-decisions:
  - "Deduplication rule at priority 2 (after one-question-at-a-time, before mode detection)"
  - "Tool results as completion evidence (not dead ARTIFACT_CREATED marker from BUG-019)"
  - "Escape hatch covers regenerate/revise/update/create-new-version user requests"
  - "Single-call enforcement in tool description prevents permissive multiply language"

patterns-established:
  - "Prompt rules reference concrete evidence (tool results) not abstract state"
  - "Tool descriptions guide behavior via explicit constraints (ONCE per request)"
  - "Escape hatches preserve user control while preventing unwanted automation"

# Metrics
duration: 4min
completed: 2026-02-05
---

# Phase 40 Plan 01: Prompt Engineering Fixes Summary

**Prompt-layer deduplication with positive framing, tool-result evidence detection, and explicit re-generation escape hatch prevents artifact multiplication while preserving user control**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-02-05T08:46:45Z
- **Completed:** 2026-02-05T08:50:38Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added ARTIFACT DEDUPLICATION rule at priority 2 in SYSTEM_PROMPT critical_rules with positive framing ("ONLY act on MOST RECENT user message")
- Deduplication rule references save_artifact tool results as completion evidence (avoids dead ARTIFACT_CREATED marker from BUG-019)
- Explicit escape hatch for regenerate/revise/update requests preserves user agency
- SAVE_ARTIFACT_TOOL description enforces single-call behavior ("Call this tool ONCE per user request")
- Removed permissive "multiple times" language from tool description
- Renumbered existing critical_rules priorities 3-6 to accommodate new rule
- All changes include re-generation escape hatch per PITFALL-03

## Task Commits

Each task was committed atomically:

1. **Task 1: Add artifact deduplication rule to SYSTEM_PROMPT critical_rules** - `483eed2` (feat)
2. **Task 2: Enforce single-call behavior in SAVE_ARTIFACT_TOOL description** - `71ec7a2` (feat)

## Files Created/Modified

- `backend/app/services/ai_service.py` - Added ARTIFACT DEDUPLICATION rule at priority 2 in critical_rules; enforced single-call in SAVE_ARTIFACT_TOOL description; removed "multiple times" language

## Decisions Made

**1. Deduplication rule at priority 2**
- Rationale: After one-question-at-a-time (foundational behavior) but before mode detection (phase-specific). Artifact deduplication is critical for all phases.

**2. Tool results as completion evidence**
- Rationale: Research found ARTIFACT_CREATED marker from BUG-019 is dead code. Tool results in conversation history are reliable completion signal.

**3. Escape hatch wording: "regenerate, revise, update, or create a new version"**
- Rationale: Covers user intent to modify or recreate artifacts without overly broad catch-all that might re-enable duplication.

**4. Positive framing in rule**
- Rationale: Per PROMPT-02 research, "ONLY act on MOST RECENT" is clearer than negative framing like "Don't re-execute previous requests."

**5. Single-call enforcement in tool description**
- Rationale: Tool description guides model's tool-calling decisions directly. Explicit constraint prevents model from interpreting "multiple times" as permission to duplicate.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Testing environment unavailable**
- **Issue:** Backend tests require virtualenv with pytest installed. System Python lacks dependencies.
- **Resolution:** Verified changes via manual inspection and grep commands per plan verification section. All grep checks passed:
  - "multiple times" count: 0 (removed)
  - "ARTIFACT DEDUPLICATION" count: 1 (added)
  - "ONCE per user request" count: 1 (added)
  - Tool results reference present
  - Escape hatch text present in both locations

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Phase 41 ready to execute**
- Layers 1+2 (prompt rule + tool description) implemented
- Phase 41 will add Layer 3 (structural history filtering with HTML comment markers)
- Phase 42 will add Layer 4 (silent artifact generation code path)
- CRITICAL: Phase 41 must verify alternative detection strategy (tool results vs dead ARTIFACT_CREATED marker) per PITFALL-01

**Blockers:** None

**Concerns:**
- Testing in production environment recommended before Phase 42 to validate Layers 1+2 effectiveness
- Phase 41 research flagged CRITICAL detection strategy issue - must verify before coding

---
*Phase: 40-prompt-engineering-fixes*
*Completed: 2026-02-05*
