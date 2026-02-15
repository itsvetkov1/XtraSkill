---
phase: 61-quality-comparison-decision
plan: 01
subsystem: evaluation
tags: [quality-comparison, test-scenarios, rubric, orchestrator]
dependency_graph:
  requires: [backend/app/services/ai_service.py, backend/app/database.py]
  provides: [evaluation framework, test scenarios, quality rubric, BRD generator]
  affects: []
tech_stack:
  added: [evaluation module]
  patterns: [multi-turn conversation simulation, blind review protocol, cost estimation]
key_files:
  created:
    - backend/evaluation/__init__.py
    - backend/evaluation/test_scenarios.json
    - backend/evaluation/quality_rubric.py
    - backend/evaluation/generate_samples.py
  modified: []
decisions:
  - Test scenario complexity distribution: 2 low, 2 medium, 1 high (prevents bias toward agent capabilities)
  - Multi-turn simulation approach: initial prompt + follow-ups + final prompt (exercises full provider pipeline)
  - Blind review protocol: random 8-char hex IDs with shuffled presentation order (eliminates confirmation bias)
  - Cost calculation: 40% overhead for agent providers (midpoint of research-observed 30-50% range)
metrics:
  duration_seconds: 191
  tasks_completed: 2
  files_created: 4
  commits: 2
completed_at: "2026-02-15T15:15:25Z"
---

# Phase 61 Plan 01: Evaluation Framework Summary

**One-liner:** Standardized test scenarios, multi-dimensional quality rubric, and BRD generation orchestrator for systematic quality comparison across three LLM providers.

## Objective

Build the evaluation framework infrastructure needed to run a controlled quality comparison across anthropic (baseline), claude-code-sdk, and claude-code-cli providers. This provides the foundation for Phase 61's go/no-go decision on Claude Code adoption.

## What Was Built

### Test Scenarios (test_scenarios.json)

Created 5 standardized test scenarios representing real-world BA use cases:

1. **TC-01: Simple Feature - User Login** (low complexity)
   - Basic auth with password reset and social login
   - 3 follow-up questions
   - Minimum 8 acceptance criteria expected

2. **TC-02: Medium Workflow - Expense Report Submission** (medium complexity)
   - Multi-role approval workflow with managers and finance
   - 4 follow-up questions covering thresholds, categories, reporting
   - Minimum 15 acceptance criteria expected

3. **TC-03: Complex Multi-Stakeholder - E-commerce Marketplace** (high complexity)
   - Three-sided platform: sellers, buyers, administrators
   - 6 follow-up questions covering onboarding, payments, disputes, analytics
   - Minimum 25 acceptance criteria expected

4. **TC-04: Integration Scenario - CRM Integration** (medium complexity)
   - System integration with email/calendar sync
   - 4 follow-up questions on data sync and conflict resolution
   - Minimum 12 acceptance criteria expected

5. **TC-05: Regulatory Domain - Healthcare Patient Portal** (high complexity)
   - HIPAA-compliant patient portal
   - 6 follow-up questions on compliance, security, access control
   - Minimum 30 acceptance criteria expected

**Key design decisions:**
- Complexity distribution prevents bias toward agent-friendly scenarios (not all complex)
- Multi-turn conversation structure (initial + follow-ups + final) exercises agent iteration capabilities
- Expected sections and minimum AC counts provide objective completeness benchmarks

### Quality Rubric (quality_rubric.py)

Multi-dimensional scoring framework with 4 dimensions on 1-4 scale:

1. **Completeness:** All required BRD sections present with sufficient detail
   - POOR: Missing 2+ major sections
   - FAIR: Missing 1 section or multiple lack detail
   - GOOD: All sections with adequate detail
   - EXCELLENT: Comprehensive, actionable detail addressing all requirements

2. **Acceptance Criteria Quality:** Specific, measurable, testable with explicit actors and thresholds
   - POOR: Vague without measurable thresholds
   - FAIR: Some specificity, many lack conditions
   - GOOD: Most testable with clear pass/fail
   - EXCELLENT: All fully testable with actors, thresholds, triggers

3. **Internal Consistency:** No contradictions, unified terminology, coherent narrative
   - POOR: Multiple contradictions confusing to implementers
   - FAIR: 1-2 inconsistencies in terminology
   - GOOD: Mostly consistent with minor variations
   - EXCELLENT: Perfect consistency throughout

4. **Error and Edge Case Coverage:** Addresses error handling, unhappy paths, recovery
   - POOR: No error cases mentioned
   - FAIR: General error mentions, lacks specifics
   - GOOD: Main scenarios with specific handling
   - EXCELLENT: Comprehensive error coverage with recovery flows

**Implementation features:**
- `ScoreLevel` enum (POOR=1, FAIR=2, GOOD=3, EXCELLENT=4)
- `QualityDimension` dataclass with per-level criteria descriptions
- `score_summary()` function for aggregate statistics (mean, min, max, total)
- `RUBRIC_DESCRIPTION` constant for formatted markdown presentation
- `validate_scores()` helper for score validation

### BRD Generation Orchestrator (generate_samples.py)

Standalone async script for generating BRDs across all providers:

**Core functions:**

1. **`generate_brd_sample(provider, scenario, db)`**
   - Simulates multi-turn conversation using AIService
   - Steps: initial prompt → follow-ups with AI responses → final BRD request
   - Accumulates token usage and timing across all turns
   - Returns dict with content, tokens, time, cost

2. **`calculate_cost(usage, provider)`**
   - Base pricing: Claude Sonnet 4.5 ($3/M input, $15/M output)
   - Applies 40% overhead for agent providers (claude-code-sdk/cli)
   - Returns USD cost estimate

3. **`generate_all_samples()`**
   - Generates 15 BRDs: 3 providers × 5 scenarios
   - Creates directory structure: evaluation_data/{provider}/TC-XX.md
   - Saves metadata separately: evaluation_data/metadata/{provider}_TC-XX.json
   - Prints progress and summary statistics

4. **`anonymize_for_blind_review()`**
   - Generates random 8-char hex review IDs for each BRD
   - Copies to evaluation_data/blind_review/{review_id}.md
   - Creates review_id_mapping.json (sealed until scoring complete)
   - Generates scoring_template.csv with empty score columns
   - Shuffles presentation order to prevent provider grouping

**CLI interface:**
- `python -m evaluation.generate_samples generate` — Generate all BRDs
- `python -m evaluation.generate_samples anonymize` — Anonymize for review
- `python -m evaluation.generate_samples all` — Run both steps

**Technical implementation:**
- Uses existing AIService infrastructure (no duplication)
- Async conversation simulation with streaming
- Token and cost tracking across multi-turn exchanges
- Graceful error handling with progress logging

## Task Breakdown

### Task 1: Create test scenarios and quality rubric
**Status:** ✅ Complete
**Commit:** 45fa814
**Files:** backend/evaluation/__init__.py, test_scenarios.json, quality_rubric.py

Created package marker, 5 standardized test scenarios with complexity distribution, and 4-dimension quality rubric with per-level criteria. All verification passed (5 scenarios confirmed, 4 dimensions confirmed, all fields present).

### Task 2: Create BRD generation orchestrator script
**Status:** ✅ Complete
**Commit:** 1a255f5
**File:** backend/evaluation/generate_samples.py

Built standalone async script with multi-turn conversation simulation, cost calculation, blind review anonymization, and CLI interface. Script is importable, function signatures match requirements, AIService integration verified.

## Deviations from Plan

None - plan executed exactly as written. All must-haves satisfied:
- ✅ 5 standardized test scenarios exist with varying complexity
- ✅ Quality rubric defines 4 dimensions with 1-4 scale and per-level criteria
- ✅ Generation script can create BRDs for all 3 providers using AIService

## Verification Results

**Overall verification:** ✅ PASSED

1. ✅ All files exist: evaluation/__init__.py, test_scenarios.json, quality_rubric.py, generate_samples.py
2. ✅ Test scenarios JSON valid with 5 scenarios
3. ✅ All scenario fields present (id, name, complexity, prompts, expected sections, AC count)
4. ✅ Quality rubric defines 4 dimensions
5. ✅ All rubric dimensions have 4-level scoring criteria
6. ✅ Generate script importable without errors
7. ✅ Function signature matches spec (provider, scenario, db)
8. ✅ AIService imported correctly from app.services.ai_service

## Success Criteria

- ✅ 5 standardized test scenarios with low/medium/high complexity distribution
- ✅ 4-dimension quality rubric with clear scoring criteria
- ✅ Generation orchestrator script that can produce BRDs from all 3 providers
- ✅ Blind review anonymization function for unbiased human scoring
- ✅ All code importable without runtime errors

## Self-Check

### Files Created
```bash
# Check all created files exist
$ test -f backend/evaluation/__init__.py && echo "✅ __init__.py"
✅ __init__.py
$ test -f backend/evaluation/test_scenarios.json && echo "✅ test_scenarios.json"
✅ test_scenarios.json
$ test -f backend/evaluation/quality_rubric.py && echo "✅ quality_rubric.py"
✅ quality_rubric.py
$ test -f backend/evaluation/generate_samples.py && echo "✅ generate_samples.py"
✅ generate_samples.py
```

### Commits Exist
```bash
# Verify commits in history
$ git log --oneline --all | grep "45fa814"
45fa814 feat(61-01): create test scenarios and quality rubric
$ git log --oneline --all | grep "1a255f5"
1a255f5 feat(61-01): create BRD generation orchestrator script
```

**Self-Check Result:** ✅ PASSED

All claimed files exist. All claimed commits exist in git history.

## Next Steps

1. **Plan 61-02:** Run generation script to produce 15 BRDs (3 providers × 5 scenarios)
2. **Plan 61-03:** Execute blind review scoring using quality rubric
3. **Plan 61-04:** Statistical analysis and comparison report with go/no-go recommendation

## Technical Notes

**Multi-turn conversation approach:**
The script simulates realistic BA discovery sessions by:
1. Sending initial prompt and collecting AI response
2. For each follow-up: appending prior AI response, sending follow-up, collecting new response
3. After all follow-ups: appending last response, sending final BRD request
4. Accumulating tokens and timing across ALL turns

This exercises the full provider pipeline and allows agents to demonstrate multi-turn refinement capabilities.

**Blind review protocol:**
Random hex IDs prevent reviewer from inferring provider from filename or ordering. Shuffling presentation order eliminates sequential bias. Mapping sealed until after scoring prevents confirmation bias.

**Cost calculation assumptions:**
- Base: Claude Sonnet 4.5 pricing ($3/M input, $15/M output)
- Agent overhead: 40% multiplier (midpoint of research-observed 30-50% range)
- Per research findings in 61-RESEARCH.md

---

**Phase 61 Plan 01 complete.** Evaluation framework infrastructure ready for BRD generation phase.
