---
phase: 61-quality-comparison-decision
plan: 03
subsystem: evaluation
tags: [brd-generation, cli-adapter, experiment-data]
dependency_graph:
  requires: [backend/evaluation/generate_samples.py, backend/evaluation/test_scenarios.json]
  provides: [5 CLI-generated BRDs with metadata]
  affects: []
tech_stack:
  added: []
  patterns: [subprocess CLI invocation, multi-turn conversation simulation]
key_files:
  created:
    - backend/evaluation_data/claude-code-cli/TC-01.md
    - backend/evaluation_data/claude-code-cli/TC-02.md
    - backend/evaluation_data/claude-code-cli/TC-03.md
    - backend/evaluation_data/claude-code-cli/TC-04.md
    - backend/evaluation_data/claude-code-cli/TC-05.md
    - backend/evaluation_data/metadata/claude-code-cli_TC-01.json
    - backend/evaluation_data/metadata/claude-code-cli_TC-02.json
    - backend/evaluation_data/metadata/claude-code-cli_TC-03.json
    - backend/evaluation_data/metadata/claude-code-cli_TC-04.json
    - backend/evaluation_data/metadata/claude-code-cli_TC-05.json
  modified: []
decisions:
  - SDK provider excluded from comparison (Windows command line length limitation in SDK library)
  - Anthropic baseline skipped — user decision to wrap up experiment without formal comparison
  - Experiment concludes with CLI demonstration data only (no statistical comparison possible)
  - Blind review and scoring steps skipped (single provider, nothing to compare)
metrics:
  duration_seconds: null
  tasks_completed: 1
  files_created: 10
  files_modified: 0
  commits: 3
completed_at: "2026-02-16"
---

# Phase 61 Plan 03: BRD Generation Summary

**One-liner:** Generated 5 CLI BRDs across all test scenarios; anthropic baseline and SDK skipped — experiment concludes without formal quality comparison.

## Objective

Generate BRDs across providers and prepare blind review materials for human scoring.

## What Was Done

### CLI BRD Generation (5/5 Complete)

Successfully generated 5 BRDs using the Claude Code CLI adapter (agent pipeline with MCP tools):

| Scenario | File | Size | Output Tokens | Time (s) | Cost ($) |
|----------|------|------|---------------|----------|----------|
| TC-01: Simple Feature (Login, low) | TC-01.md | 62KB | 13,226 | 296 | $0.28 |
| TC-02: Medium Feature (Expense, medium) | TC-02.md | 75KB | 16,091 | 375 | ~$0.34 |
| TC-03: Complex Feature (Marketplace, high) | TC-03.md | 80KB | 16,915 | 397 | ~$0.36 |
| TC-04: Medium Feature (CRM, medium) | TC-04.md | 58KB | 12,708 | 278 | ~$0.27 |
| TC-05: Complex Feature (Healthcare, high) | TC-05.md | 96KB | 19,917 | 485 | ~$0.42 |
| **Total** | | **376KB** | **78,867** | **1,831s (~31 min)** | **~$1.67** |

### What Was Skipped

1. **SDK provider (claude-code-sdk):** Excluded earlier due to Windows command line length limitation in the SDK library. Not a viable production path.

2. **Anthropic baseline (direct API):** User decision to skip. Originally planned to generate via `claude -p` (subscription print mode), but experiment wrapped up without baseline generation.

3. **Blind review & scoring:** With only one provider, blind review anonymization and human scoring serve no comparative purpose. Skipped.

### Manual Testing Session (2026-02-16)

During CLI BRD generation testing, 3 bugs were discovered and fixed:

1. **Broken pipe error:** CLI subprocess failed because `CLAUDECODE=1` env var triggered nested session detection. Fix: strip `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` from subprocess environment.

2. **Projectless chat error:** "Adapter context not set" when creating chats without a project. Fix: relaxed guard in both CLI and SDK adapters to not require `project_id`.

3. **Text not selectable:** No visual feedback when selecting text in conversation view. Fix: wrapped message list with `SelectionArea`, converted nested `SelectableText` to `Text`.

## Deviations from Plan

**Major deviation:** Plan called for 15 BRDs (3 providers x 5 scenarios), blind review anonymization, and human scoring. Delivered 5 BRDs (1 provider x 5 scenarios) with no comparison.

- SDK excluded due to technical limitation (not a plan deviation — discovered during 61-03 execution)
- Anthropic baseline skipped by user decision (change of plans)
- Blind review and scoring skipped as consequence (single provider)

**Impact on Phase 61 goal:** The original goal was "Quality Comparison & Decision" — a data-driven go/no-go based on statistical quality improvement. Without baseline comparison data, the formal statistical analysis (Plan 61-04) cannot produce a meaningful comparison. The experiment outcome will be based on qualitative assessment of CLI capabilities rather than quantitative quality comparison.

## Verification Results

**Partial verification:** ✅ CLI portion complete

1. ✅ 5 CLI BRDs exist in `evaluation_data/claude-code-cli/`
2. ✅ 5 metadata files exist in `evaluation_data/metadata/`
3. ✅ All BRDs are non-empty and contain expected markdown content
4. ❌ No anthropic baseline BRDs (skipped)
5. ❌ No blind review materials (skipped)
6. ❌ No scoring template completed (skipped)

## Success Criteria

- ✅ CLI BRDs generated (5/5)
- ❌ Anthropic baseline BRDs (0/5 — skipped)
- ❌ SDK BRDs (0/5 — excluded)
- ❌ Blind review and scoring (skipped — single provider)

## CLI Adapter Observations

From the generation run, the CLI adapter demonstrated:

- **Consistent output:** All 5 BRDs produced complete, well-structured documents
- **Reasonable performance:** 278-485 seconds per BRD (varies with complexity)
- **Cost profile:** ~$0.27-$0.42 per BRD ($1.67 total for 5)
- **Token efficiency:** 12,708-19,917 output tokens per BRD
- **Complexity correlation:** Higher complexity scenarios produced larger, more detailed BRDs (as expected)

## Next Steps

Plan 61-04 (analysis + report) needs to be adapted or replaced since the formal statistical comparison cannot proceed. Options:

1. Write a qualitative conclusion report based on CLI demonstration data
2. Close the experiment with a decision based on implementation experience
3. Defer formal comparison to a future milestone if needed

---

**Phase 61 Plan 03 wrapped up.** CLI BRDs generated successfully. Experiment data is CLI-only; formal comparison deferred.
