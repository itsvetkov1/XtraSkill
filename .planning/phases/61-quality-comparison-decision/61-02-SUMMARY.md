---
phase: 61-quality-comparison-decision
plan: 02
subsystem: evaluation
tags: [statistical-analysis, report-generation, cost-quality-tradeoff]
dependency_graph:
  requires: [backend/evaluation/quality_rubric.py, backend/evaluation/test_scenarios.json]
  provides: [statistical analysis pipeline, comparison report generator]
  affects: []
tech_stack:
  added: [pandas, scipy, jinja2 templating]
  patterns: [Mann-Whitney U test, cost-quality tradeoff analysis, decision matrix]
key_files:
  created:
    - backend/evaluation/analyze_results.py
    - backend/evaluation/generate_report.py
    - backend/evaluation/report_template.md
  modified:
    - backend/requirements.txt
decisions:
  - Statistical test choice: Mann-Whitney U (non-parametric, suitable for small samples and ordinal data)
  - Two-sided alternative hypothesis: detect both improvement and degradation
  - Decision threshold enforcement: >20% average improvement AND 3+ significant dimensions
  - Cost-quality metric: improvement % / cost increase % for tradeoff analysis
metrics:
  duration_seconds: 242
  tasks_completed: 2
  files_created: 3
  files_modified: 1
  commits: 2
completed_at: "2026-02-15T15:22:36Z"
---

# Phase 61 Plan 02: Analysis Pipeline & Report Generator Summary

**One-liner:** Statistical analysis pipeline with Mann-Whitney U tests and Jinja2 report generator producing comprehensive cost-quality tradeoff comparison with >20% improvement decision logic.

## Objective

Build the analysis scripts and report templates that transform human quality scores into statistical comparisons with clear go/no-go recommendations. These scripts are independent of BRD generation and can be written before scoring happens.

## What Was Built

### Statistical Analysis Script (analyze_results.py)

Complete analysis pipeline with 5 core functions:

1. **`load_scores(scores_path, mapping_path)`**
   - Reads completed scoring CSV from blind review
   - Merges with review_id → {provider, scenario_id} mapping
   - Validates: no empty score cells, all review_ids have mapping entries
   - Returns pandas DataFrame with provider info and all quality dimensions

2. **`analyze_provider_comparison(scores_df)`**
   - Groups scores by provider (anthropic, claude-code-sdk, claude-code-cli)
   - Per dimension (completeness, ac_quality, consistency, error_coverage):
     - Computes mean and std dev for each provider
     - Calculates improvement percentage relative to baseline
     - Runs Mann-Whitney U test (two-sided) for statistical significance
     - Records p-value and significance flag (alpha=0.05)
   - Computes aggregate scores (mean across all 4 dimensions)
   - Returns structured dict with per-dimension statistics

3. **`calculate_cost_summary()`**
   - Reads metadata files: evaluation_data/metadata/{provider}_{scenario_id}.json
   - Aggregates per provider: total tokens, total cost, avg cost per BRD, avg time
   - Computes cost increase percentages relative to baseline
   - Returns cost summary dict with all providers

4. **`make_recommendation(stats, cost_summary)`**
   - Applies decision criteria from STATE.md:
     - >20% average quality improvement threshold
     - 3+ dimensions with statistical significance
     - Cost overhead consideration (30-50% acceptable if quality justifies)
   - Decision matrix:
     - **ADOPT [provider]**: avg_improvement >= 20% AND significant_dims >= 3
     - **LARGER STUDY RECOMMENDED**: marginal (10-20%) improvement
     - **STAY WITH DIRECT API**: < 10% improvement
     - If both qualify, pick higher improvement with lower cost
   - Returns recommendation dict with confidence, rationale, summaries

5. **`run_full_analysis()`**
   - Orchestrates full pipeline: load → analyze → cost → recommend
   - Creates evaluation_results/ directory
   - Saves statistics.json with all results
   - Returns complete results dict

**Command-line interface:**
```bash
cd backend && python -m evaluation.analyze_results
```
Prints formatted summary table with quality scores, cost analysis, and recommendation.

**Dependencies:**
- `pandas>=2.0.0` — tabular data operations, statistical functions
- `scipy>=1.10.0` — Mann-Whitney U test (scipy.stats.mannwhitneyu)
- Both added to requirements.txt with comment marking as evaluation-only

**Key implementation details:**
- `try/except ImportError` for pandas/scipy with helpful error messages
- Two-sided Mann-Whitney U (detects degradation as well as improvement)
- Improvement percentage: ((provider_mean - baseline_mean) / baseline_mean) * 100
- Quality per cost metric: improvement % / cost increase %

### Report Generator (generate_report.py)

Jinja2-based report generation from analysis results:

**`generate_comparison_report(scores_path, mapping_path, output_path)`**
- Calls `run_full_analysis()` to get statistics
- Loads `report_template.md` Jinja2 template
- Prepares template context with:
  - Generated date, sample counts, provider list
  - Dimension data with display names
  - Aggregate means and improvement percentages
  - Quality per cost calculations
  - Significant dimension counts
  - Cost summary with proper nesting
- Renders template with all context
- Saves to evaluation_results/comparison_report.md
- Returns rendered report string

**Command-line interface:**
```bash
cd backend && python -m evaluation.generate_report
```
Generates comparison_report.md and prints file paths.

### Jinja2 Report Template (report_template.md)

Comprehensive markdown template with 8 sections:

1. **Executive Summary** — Recommendation and rationale upfront
2. **Methodology** — Experimental design, rubric, blind review, statistical tests, decision threshold
3. **Quality Scores by Dimension** — Table with means, improvements, significance markers
4. **Cost Analysis** — Per-provider cost, increase %, generation time
5. **Cost-Quality Tradeoff** — Improvement % vs cost increase % vs quality per cost
6. **Decision Matrix** — Thresholds comparison (quality, significance, cost, complexity)
7. **Limitations** — Small sample, single reviewer, scenario coverage, prompt differences
8. **Recommendation** — Final decision with confidence and next steps

**Template features:**
- Jinja2 `{{ }}` variables for dynamic content
- `{% for %}` loops for dimension rows
- `{% if %}` conditionals for recommendation-specific next steps
- Proper markdown formatting with tables
- Statistical significance markers (asterisks)
- Numeric formatting filters (%.2f, %+.1f%%, etc.)

**Next steps sections:**
- If "LARGER STUDY RECOMMENDED": expand to n=30, add second reviewer
- If "ADOPT [provider]": merge branch, production hardening, monitoring
- If "STAY WITH DIRECT API": enhance direct API, archive experiment

## Task Breakdown

### Task 1: Create statistical analysis script
**Status:** ✅ Complete
**Commit:** 7c564d4
**Files:** backend/evaluation/analyze_results.py, backend/requirements.txt

Created comprehensive analysis pipeline with Mann-Whitney U tests, >20% improvement threshold logic, cost summary calculation, and recommendation generation. Added pandas and scipy to requirements.txt. All verification passed.

### Task 2: Create report generator and template
**Status:** ✅ Complete
**Commit:** 60d5b6c
**Files:** backend/evaluation/generate_report.py, backend/evaluation/report_template.md

Built Jinja2 report generator and comprehensive markdown template with all 8 required sections. Template includes quality scores table, cost analysis, cost-quality tradeoff, decision matrix, limitations, and recommendation-specific next steps. All verification passed.

## Deviations from Plan

None - plan executed exactly as written. All must-haves satisfied:
- ✅ Analysis script computes per-dimension means, improvement percentages, and Mann-Whitney U significance tests
- ✅ Report generator produces markdown comparison report with statistical results, cost-quality tradeoff, and clear recommendation
- ✅ Decision logic applies >20% improvement threshold from STATE.md decision criteria
- ✅ All key_links present: analyze_results.py uses mannwhitneyu, generate_report imports from analyze_results, template loaded via Jinja2

## Verification Results

**Overall verification:** ✅ PASSED

1. ✅ All 3 evaluation scripts importable without runtime errors
2. ✅ Report template contains all 8 required sections
3. ✅ Analysis applies Mann-Whitney U test (scipy.stats.mannwhitneyu present in code)
4. ✅ Analysis applies >20% improvement threshold (>= 20 check in make_recommendation)
5. ✅ Report template renders decision matrix with quality vs cost tradeoff
6. ✅ Scripts follow codebase conventions (docstrings, type hints, error handling)

**Additional checks:**
- ✅ load_scores validates no empty score cells (isnull check present)
- ✅ Template uses Jinja2 syntax correctly ({{ }}, {% %}, filters)
- ✅ generate_report imports from analyze_results (run_full_analysis)
- ✅ pandas and scipy added to requirements.txt with appropriate versions

## Success Criteria

- ✅ Statistical analysis script computes per-dimension comparisons with significance testing
- ✅ Report generator produces comprehensive markdown report from Jinja2 template
- ✅ Decision logic implements the >20% improvement threshold from project decisions
- ✅ Cost-quality tradeoff analysis included in report
- ✅ All scripts importable without runtime errors

## Self-Check

### Files Created
```bash
$ test -f backend/evaluation/analyze_results.py && echo "✅ analyze_results.py"
✅ analyze_results.py
$ test -f backend/evaluation/generate_report.py && echo "✅ generate_report.py"
✅ generate_report.py
$ test -f backend/evaluation/report_template.md && echo "✅ report_template.md"
✅ report_template.md
```

### Files Modified
```bash
$ git diff HEAD~2 backend/requirements.txt | grep "^+pandas"
+pandas>=2.0.0
$ git diff HEAD~2 backend/requirements.txt | grep "^+scipy"
+scipy>=1.10.0
```

### Commits Exist
```bash
$ git log --oneline --all | grep "7c564d4"
7c564d4 feat(61-02): create statistical analysis script
$ git log --oneline --all | grep "60d5b6c"
60d5b6c feat(61-02): create report generator and Jinja2 template
```

**Self-Check Result:** ✅ PASSED

All claimed files exist. All claimed commits exist in git history. Dependencies added to requirements.txt.

## Next Steps

**Plan 61-03:** Execute BRD generation script to produce 15 samples (3 providers × 5 scenarios) and perform blind review anonymization.

**Plan 61-04:** Run blind review scoring, execute analysis pipeline, generate comparison report, and make final adoption decision.

## Technical Notes

**Why Mann-Whitney U test:**
- Non-parametric (no normal distribution assumption required)
- Suitable for small sample sizes (n=5 per provider)
- Appropriate for ordinal data (1-4 scoring scale)
- Two-sided alternative detects both improvement and degradation
- Per research: recommended for n<30 samples (PMC7745163)

**Why two-sided test:**
Plan specified two-sided (not one-sided) to detect quality degradation as well as improvement. This is more conservative and prevents missing cases where agent providers perform worse than baseline.

**Decision threshold enforcement:**
`make_recommendation()` strictly enforces STATE.md criteria:
- avg_improvement >= 20% (not just > 10%)
- significant_dims >= 3 (majority of dimensions must show significance)
- Cost increase considered in rationale and quality_per_cost metric

**Cost-quality tradeoff metric:**
Quality improvement % / Cost increase % gives normalized "value" metric. Higher is better (more quality improvement per dollar spent). Included in both recommendation summary and report template.

**Template design:**
- All numeric data formatted with Jinja2 filters (%.2f, %+.1f%%)
- Conditional next steps based on recommendation type
- Statistical significance markers (* asterisks) for p < 0.05
- Limitations section acknowledges small sample, single reviewer, prompt differences

**Error handling:**
- FileNotFoundError with helpful messages for missing files
- ValueError for empty scores or missing mappings
- ImportError with pip install instructions for optional dependencies

---

**Phase 61 Plan 02 complete.** Analysis pipeline and report generator ready. Next: generate BRD samples and run blind review scoring.
