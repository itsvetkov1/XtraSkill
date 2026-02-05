---
phase: 40-prompt-engineering-fixes
verified: 2026-02-05T18:55:00Z
status: human_needed
score: 4/4 must-haves verified
human_verification:
  - test: "Multi-artifact deduplication test"
    expected: "Only 1 new artifact generated, not duplicates"
    why_human: "LLM behavior cannot be verified structurally - requires observing actual generation"
  - test: "Escape hatch test (regenerate request)"
    expected: "Model honors 'regenerate with more detail' as new request"
    why_human: "LLM interpretation of user intent requires runtime testing"
  - test: "Regular chat regression test"
    expected: "Non-artifact messages work exactly as before"
    why_human: "Behavior verification requires comparing pre/post change responses"
---

# Phase 40: Prompt Engineering Fixes Verification Report

**Phase Goal:** The AI model treats each artifact generation request as a single-call operation and ignores fulfilled requests in conversation history.

**Verified:** 2026-02-05T18:55:00Z

**Status:** human_needed

**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | When a user has generated 3+ artifacts in a thread, sending a new chat message produces exactly one artifact (not duplicates of previous artifacts) | ✓ VERIFIED | SYSTEM_PROMPT rule priority 2 contains "ONLY act on the MOST RECENT user message" (line 122); SAVE_ARTIFACT_TOOL description enforces "Call this tool ONCE per user request" (line 654); both wired into stream_chat (lines 784, 785) |
| 2 | When a user says 'regenerate the BRD with more detail,' the model honors the request as a new generation (escape hatch works) | ✓ VERIFIED | Escape hatch present in SYSTEM_PROMPT rule: "if the user explicitly asks to regenerate, revise, update, or create a new version" (line 122); also in SAVE_ARTIFACT_TOOL description: "NEW message explicitly asking to regenerate, revise, or create another artifact" (line 666) |
| 3 | The save_artifact tool description no longer contains 'multiple times' language | ✓ VERIFIED | Grep check: 0 matches for "multiple times" in ai_service.py; SAVE_ARTIFACT_TOOL description reviewed manually - no such language present |
| 4 | Regular chat messages (non-artifact) are completely unaffected by the prompt changes | ✓ VERIFIED | All changes scoped to artifact-specific rules (priority 2) and tool description; no modifications to general chat logic; priority 1 rule (one-question-at-a-time) unchanged |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/ai_service.py` | Deduplication rule in SYSTEM_PROMPT critical_rules + single-call SAVE_ARTIFACT_TOOL description | ✓ VERIFIED | EXISTS (file present), SUBSTANTIVE (rule 68 chars, tool desc 4 lines), WIRED (SYSTEM_PROMPT passed to stream_chat line 784, SAVE_ARTIFACT_TOOL in self.tools line 700) |

**Artifact Verification Details:**

- **Level 1 (Exists):** ✓ File exists at expected path
- **Level 2 (Substantive):** 
  - Priority 2 rule: 68-character rule text with all required elements
  - SAVE_ARTIFACT_TOOL description: 4-line enforcement section
  - No TODO/FIXME/placeholder patterns in implementation (only 1 doc comment mention line 421)
  - Contains all required exports (SYSTEM_PROMPT, SAVE_ARTIFACT_TOOL)
- **Level 3 (Wired):**
  - SYSTEM_PROMPT → stream_chat via system_prompt parameter (line 784)
  - SAVE_ARTIFACT_TOOL → stream_chat via self.tools (line 700 definition, line 785 usage)
  - Both used in AIService.stream_chat method (primary chat endpoint)

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| SYSTEM_PROMPT critical_rules | LLM behavior | system_prompt parameter in stream_chat | ✓ WIRED | SYSTEM_PROMPT constant passed to adapter.stream_chat (line 784); rule priority 2 contains "ONLY act on the MOST RECENT user message" deduplication logic |
| SAVE_ARTIFACT_TOOL description | LLM tool-call decisions | tools parameter in stream_chat | ✓ WIRED | SAVE_ARTIFACT_TOOL in self.tools list (line 700); passed to adapter.stream_chat (line 785); description contains "Call this tool ONCE per user request" enforcement |

**Link Pattern Verification:**

- **Rule priority pattern:** Priority 2 correctly positioned after priority 1 (one-question-at-a-time) and before priority 3 (mode detection)
- **Single-call enforcement:** "ONCE per user request" present in tool description (line 654)
- **Evidence detection:** Rule references "save_artifact tool results earlier in the conversation" as completion signal
- **Escape hatch:** Both rule and tool description include regenerate/revise allowance

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| PROMPT-01 | ✓ SATISFIED | Deduplication rule at priority 2 in critical_rules (line 122) |
| PROMPT-02 | ✓ SATISFIED | Positive framing: "ONLY act on the MOST RECENT user message" |
| PROMPT-03 | ✓ SATISFIED | Escape hatch: "if the user explicitly asks to regenerate, revise, update, or create a new version of an artifact, that IS a new request" |
| PROMPT-04 | ✓ SATISFIED | Tool results reference: "If you see save_artifact tool results earlier in the conversation" |
| PROMPT-05 | ✓ SATISFIED | All 6 rules correctly numbered: priorities 1, 2, 3, 4, 5, 6 (lines 121-126) |
| PROMPT-06 | ✓ SATISFIED | Single-call enforcement: "Call this tool ONCE per user request" (line 654) |
| PROMPT-07 | ✓ SATISFIED | "multiple times" removed: grep check returned 0 matches |
| PROMPT-08 | ✓ SATISFIED | Re-generation allowance: "NEW message explicitly asking to regenerate, revise, or create another artifact" (line 666) |

**All 8 requirements satisfied.**

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | - | - | - | No blockers or warnings found |

**Note:** One mention of "placeholder" found at line 421, but this is in documentation comment describing BRD completeness requirements (not implementation stub).

### Human Verification Required

#### 1. Multi-Artifact Deduplication Test

**Test:** 
1. Create a new conversation thread
2. Generate 3 different artifacts using preset buttons (e.g., User Stories, Acceptance Criteria, Requirements Doc)
3. Send a regular chat message (e.g., "Thank you, looks good")
4. Observe whether any artifacts are generated

**Expected:** 
- No artifacts should be generated from step 4
- Only the chat response should appear
- The 3 existing artifacts should remain unchanged

**Why human:** 
LLM behavior (whether it respects the "ONLY act on the MOST RECENT user message" rule) cannot be verified by code inspection. Requires runtime observation of actual generation behavior in a multi-artifact context.

#### 2. Escape Hatch Test (Regenerate Request)

**Test:**
1. Create a conversation with 1 existing artifact (e.g., User Stories)
2. Send message: "Regenerate the user stories with more detail about the login flow"
3. Observe whether a new artifact is generated

**Expected:**
- A NEW artifact should be generated (not blocked by deduplication rule)
- The artifact should contain enhanced detail about login flow
- This demonstrates escape hatch: "if the user explicitly asks to regenerate, revise, update, or create a new version"

**Why human:**
LLM interpretation of user intent (does "regenerate with more detail" trigger the escape hatch?) requires semantic understanding that can only be observed at runtime. Cannot verify via code structure.

#### 3. Regular Chat Regression Test

**Test:**
1. Create a new conversation with no artifacts
2. Send several chat messages asking discovery questions (e.g., "What information do you need about my project?")
3. Observe response quality, one-question-at-a-time behavior, and general BA assistant personality

**Expected:**
- BA assistant asks one question at a time (priority 1 rule unchanged)
- Responses are conversational and helpful
- No changes to non-artifact chat behavior
- Discovery flow works exactly as before Phase 40

**Why human:**
Regression testing requires comparing behavior before/after changes. No automated test suite exists for BA assistant conversation quality. Human judgment needed to assess "completely unaffected" claim.

### Gaps Summary

**No gaps found.** All structural requirements are satisfied:

- SYSTEM_PROMPT has 6 critical rules with deduplication at priority 2
- Deduplication rule uses positive framing ("ONLY act on the MOST RECENT")
- Rule references save_artifact tool results as completion evidence
- Explicit escape hatch for regenerate/revise/update requests present in both rule and tool description
- SAVE_ARTIFACT_TOOL description enforces single-call behavior ("ONCE per user request")
- "Multiple times" language removed (0 grep matches)
- Both constants correctly wired into stream_chat method
- All 8 PROMPT requirements satisfied

**Human verification needed** to confirm the LLM actually respects these structural changes during runtime. Automated checks cannot verify semantic understanding or behavioral compliance with prompt rules.

---

_Verified: 2026-02-05T18:55:00Z_
_Verifier: Claude (gsd-verifier)_
