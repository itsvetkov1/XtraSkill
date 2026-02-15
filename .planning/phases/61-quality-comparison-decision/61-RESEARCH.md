# Phase 61: Quality Comparison & Decision - Research

**Researched:** 2026-02-15
**Domain:** Comparative evaluation methodology, LLM output quality assessment, BRD quality metrics
**Confidence:** MEDIUM

## Summary

Phase 61 requires systematic quality comparison of BRD outputs across three approaches (direct API baseline, Agent SDK, CLI subprocess) to determine if Claude Code's agent capabilities justify adoption. This is a **controlled experiment** requiring defined quality metrics, standardized test scenarios, structured scoring framework, and statistical rigor to support a go/no-go decision.

**Critical insight:** This is NOT an A/B test (user-facing traffic split), but a **laboratory comparison** of 5+ samples per condition with human evaluation using quality rubrics. The phase requires both quantitative metrics (completeness, consistency) and qualitative assessment (AC quality, error coverage) to determine if >20% quality improvement justifies 30-50% cost overhead (per STATE.md decision criteria).

**Primary recommendation:** Build a structured evaluation framework with (1) standardized test prompts, (2) multi-dimensional quality rubric (4-6 criteria), (3) blind review protocol, (4) statistical analysis tooling, and (5) cost-benefit comparison report template. Use Python scripts for automation but require human judgment for quality scoring.

## Standard Stack

### Core Evaluation Tools

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | 2.2+ | Data collection and analysis | Industry standard for tabular data, statistical operations |
| matplotlib / seaborn | 3.9+ / 0.13+ | Visualization of comparative results | Best practice for scientific visualization |
| scipy.stats | 1.13+ | Statistical significance testing | Gold standard for hypothesis testing (t-tests, Mann-Whitney U) |
| json | stdlib | Structured storage of test scenarios and results | Built-in, no dependencies |
| csv | stdlib | Export for human review | Universal format for spreadsheet review |

### Supporting Tools

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scikit-learn.metrics | 1.5+ | Inter-rater reliability (Cohen's kappa) | If multiple human raters assess quality |
| openpyxl | 3.1+ | Excel export for review templates | If stakeholders prefer Excel for scoring |
| jinja2 | 3.1+ | Report template generation | For automated comparison report |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual spreadsheet scoring | Automated LLM-as-judge | LLM-as-judge unreliable for nuanced BRD quality; human judgment required for acceptance criteria completeness |
| Python scripts | Dedicated platforms (Braintrust, LangSmith) | Platforms add cost and complexity; experiment scope is small (15 total BRDs) |
| Custom rubric | ISO/IEC 25010 standard | ISO standard too broad for specific BRD assessment; custom rubric allows BRD-specific criteria |

**Installation:**
```bash
pip install pandas matplotlib seaborn scipy openpyxl jinja2
```

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── evaluation/
│   ├── __init__.py
│   ├── test_scenarios.json        # 5+ standardized prompts
│   ├── generate_samples.py        # Orchestrates 3 providers × 5 scenarios = 15 BRDs
│   ├── quality_rubric.py          # Multi-dimensional scoring definitions
│   ├── scoring_template.csv       # Blind review template
│   ├── analyze_results.py         # Statistical analysis (means, t-tests, significance)
│   └── generate_report.py         # Comparison report with recommendation
├── evaluation_data/               # Created during generation
│   ├── anthropic/                 # Baseline samples (5 BRDs)
│   ├── claude-code-sdk/           # SDK samples (5 BRDs)
│   ├── claude-code-cli/           # CLI samples (5 BRDs)
│   ├── metadata/                  # Token usage, timing, cost per sample
│   └── blind_review/              # Anonymized BRDs for scoring
└── evaluation_results/            # Created during analysis
    ├── scores.csv                 # Rubric scores per sample
    ├── statistics.json            # Means, std dev, p-values
    ├── comparison_report.md       # Final recommendation
    └── charts/                    # Visualization outputs
```

### Pattern 1: Controlled Test Scenario Design

**What:** Standardized prompts representing real-world BA use cases with varying complexity levels

**When to use:** Before generation phase to ensure fair comparison

**Example:**
```json
{
  "test_scenarios": [
    {
      "id": "TC-01",
      "name": "Simple Feature Request",
      "complexity": "low",
      "initial_prompt": "I need a user login feature for our mobile app. Users should be able to log in with email and password.",
      "follow_ups": [
        "What about password reset?",
        "Should we support social login?"
      ],
      "expected_sections": ["objective", "user_personas", "user_flows", "acceptance_criteria", "success_metrics"],
      "minimum_AC_count": 5
    },
    {
      "id": "TC-02",
      "name": "Complex Workflow",
      "complexity": "high",
      "initial_prompt": "We need an approval workflow for expense reports. Employees submit expenses, managers approve or reject, and finance processes payments.",
      "follow_ups": [
        "What approval thresholds should we have?",
        "How do we handle expense categories?",
        "What reporting do managers need?"
      ],
      "expected_sections": ["objective", "user_personas", "user_flows", "acceptance_criteria", "success_metrics", "business_rules"],
      "minimum_AC_count": 15
    }
  ]
}
```

### Pattern 2: Multi-Dimensional Quality Rubric

**What:** Scoring framework covering 4-6 distinct quality dimensions with 3-5 point scales

**When to use:** During manual review phase for consistent scoring

**Example:**
```python
# quality_rubric.py
from dataclasses import dataclass
from enum import Enum

class ScoreLevel(Enum):
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4

@dataclass
class QualityDimension:
    name: str
    description: str
    criteria: dict[ScoreLevel, str]

# Based on research: completeness, accuracy, clarity, consistency
RUBRIC = {
    "completeness": QualityDimension(
        name="Completeness",
        description="All required BRD sections present with sufficient detail",
        criteria={
            ScoreLevel.POOR: "Missing 2+ major sections (e.g., no user personas or acceptance criteria)",
            ScoreLevel.FAIR: "Missing 1 major section OR multiple sections lack detail",
            ScoreLevel.GOOD: "All sections present, most have adequate detail",
            ScoreLevel.EXCELLENT: "All sections present with comprehensive, actionable detail"
        }
    ),
    "ac_quality": QualityDimension(
        name="Acceptance Criteria Quality",
        description="Acceptance criteria are specific, measurable, testable, and complete",
        criteria={
            ScoreLevel.POOR: "Vague criteria (e.g., 'system should be fast'), not testable",
            ScoreLevel.FAIR: "Some specificity but many criteria lack measurable conditions",
            ScoreLevel.GOOD: "Most criteria are testable with clear pass/fail conditions",
            ScoreLevel.EXCELLENT: "All criteria follow GIVEN-WHEN-THEN or similar pattern, fully testable"
        }
    ),
    "consistency": QualityDimension(
        name="Internal Consistency",
        description="No contradictions, unified terminology, coherent narrative",
        criteria={
            ScoreLevel.POOR: "Multiple contradictions or terminology inconsistencies",
            ScoreLevel.FAIR: "1-2 inconsistencies in terminology or requirements",
            ScoreLevel.GOOD: "Mostly consistent with minor terminology variations",
            ScoreLevel.EXCELLENT: "Perfectly consistent terminology and requirement alignment"
        }
    ),
    "error_coverage": QualityDimension(
        name="Error/Edge Case Coverage",
        description="Document addresses error handling, edge cases, and unhappy paths",
        criteria={
            ScoreLevel.POOR: "No error cases mentioned",
            ScoreLevel.FAIR: "Mentions errors generally but lacks specific handling",
            ScoreLevel.GOOD: "Covers main error scenarios with specific handling requirements",
            ScoreLevel.EXCELLENT: "Comprehensive error coverage including edge cases and recovery flows"
        }
    )
}
```

### Pattern 3: Blind Review Protocol

**What:** Anonymize BRDs by removing provider identifiers to prevent bias during scoring

**When to use:** After generation, before human review

**Example:**
```python
# generate_samples.py - anonymization step
import hashlib
import random

def anonymize_brd(brd_content: str, provider: str, scenario_id: str, sample_num: int) -> dict:
    """
    Create anonymized BRD for blind review.

    Returns dict with:
    - review_id: Random identifier (prevents provider inference)
    - content: BRD markdown
    - metadata: Hidden until scoring complete (provider, scenario, tokens)
    """
    # Generate random review ID (not sequential to prevent grouping by provider)
    review_id = hashlib.sha256(f"{provider}{scenario_id}{sample_num}{random.random()}".encode()).hexdigest()[:8]

    return {
        "review_id": review_id.upper(),
        "content": brd_content,
        "metadata_sealed": {
            "provider": provider,
            "scenario_id": scenario_id,
            "sample_num": sample_num,
            "token_usage": {...},  # Sealed until analysis
            "generation_time": {...}
        }
    }
```

### Pattern 4: Statistical Significance Testing

**What:** Use appropriate statistical tests to determine if quality differences are statistically significant

**When to use:** After scoring complete to validate findings

**Example:**
```python
# analyze_results.py
import pandas as pd
from scipy import stats

def analyze_provider_comparison(scores_df: pd.DataFrame) -> dict:
    """
    Compare quality scores across providers with statistical tests.

    Args:
        scores_df: DataFrame with columns [review_id, provider, completeness, ac_quality, consistency, error_coverage]

    Returns:
        dict with means, std dev, p-values for each dimension
    """
    results = {}
    dimensions = ["completeness", "ac_quality", "consistency", "error_coverage"]

    for dim in dimensions:
        # Group by provider
        baseline = scores_df[scores_df.provider == "anthropic"][dim]
        sdk = scores_df[scores_df.provider == "claude-code-sdk"][dim]
        cli = scores_df[scores_df.provider == "claude-code-cli"][dim]

        # Mann-Whitney U test (non-parametric, suitable for small sample sizes and ordinal data)
        # Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC7745163/ recommends non-parametric tests for n<30
        sdk_vs_baseline = stats.mannwhitneyu(sdk, baseline, alternative='greater')
        cli_vs_baseline = stats.mannwhitneyu(cli, baseline, alternative='greater')

        results[dim] = {
            "baseline_mean": baseline.mean(),
            "sdk_mean": sdk.mean(),
            "cli_mean": cli.mean(),
            "sdk_improvement_pct": ((sdk.mean() - baseline.mean()) / baseline.mean() * 100),
            "cli_improvement_pct": ((cli.mean() - baseline.mean()) / baseline.mean() * 100),
            "sdk_vs_baseline_pvalue": sdk_vs_baseline.pvalue,
            "cli_vs_baseline_pvalue": cli_vs_baseline.pvalue,
            "sdk_significant": sdk_vs_baseline.pvalue < 0.05,
            "cli_significant": cli_vs_baseline.pvalue < 0.05
        }

    return results
```

### Anti-Patterns to Avoid

- **Inadequate sample size**: Don't use fewer than 5 samples per condition; statistical power too low (per power analysis research, need 50+ for psychological research, but 5 is minimum for directional insights with limitations acknowledged)
- **Unblinded review**: Don't score BRDs with provider visible; introduces confirmation bias
- **Cherry-picking scenarios**: Don't select scenarios that favor one approach; use diverse complexity levels
- **Single dimension scoring**: Don't use single "quality score"; multi-dimensional rubric captures nuanced differences
- **Ignoring cost-quality tradeoff**: Don't compare quality in isolation; 10% improvement with 50% cost increase may not justify adoption

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Statistical analysis | Custom mean/variance calculators | scipy.stats, pandas.describe() | Pre-built functions handle edge cases (NaN, outliers, small samples) |
| Inter-rater reliability | Manual kappa calculation | scikit-learn.metrics.cohen_kappa_score | Handles weighted kappa, missing data, edge cases |
| Report generation | String concatenation for markdown | jinja2 templates | Maintainable, testable, supports conditional sections |
| Data visualization | Manual matplotlib bar charts | seaborn catplot, seaborn boxplot | Handles statistical annotations, confidence intervals automatically |
| Blind review shuffling | Custom randomization | pandas.sample(frac=1, random_state=seed) | Reproducible shuffling with seed control |

**Key insight:** The evaluation pipeline has many correctness-critical steps (statistical tests, anonymization, aggregation). Use battle-tested libraries to avoid subtle bugs that invalidate results.

## Common Pitfalls

### Pitfall 1: Sample Size Too Small for Definitive Conclusions

**What goes wrong:** 5 samples per condition gives directional insights but lacks statistical power for definitive claims

**Why it happens:** Experiment constraints (cost, time) limit sample generation, but stakeholders expect high-confidence recommendations

**How to avoid:**
- Acknowledge limitations explicitly in report ("directional insights, not definitive proof")
- Use non-parametric tests (Mann-Whitney U) suitable for small samples
- Focus on effect size (mean improvement %) not just p-values
- Consider Phase 61 as pilot; recommend larger follow-up study if marginal (10-15% improvement)

**Warning signs:**
- Inconsistent winner across dimensions (SDK wins completeness, CLI wins AC quality, baseline wins consistency)
- Large variance within provider (some samples excellent, some poor)
- p-values near threshold (0.04-0.06)

### Pitfall 2: Reviewer Fatigue and Inconsistent Scoring

**What goes wrong:** Scoring 15 BRDs (each 2000+ words) is mentally taxing; later scores drift from earlier ones

**Why it happens:** Human attention degrades; rubric interpretation evolves during review

**How to avoid:**
- Batch review sessions (5 BRDs per session, 3 sessions)
- Randomize presentation order within sessions
- Anchor scoring with reference examples (score 2 baseline BRDs first to calibrate)
- If possible, use 2 independent reviewers and calculate inter-rater reliability (Cohen's kappa)

**Warning signs:**
- Score variance increases in later samples
- All samples in one session scored similarly (compression effect)
- Reviewer notes inconsistency in interpretation

### Pitfall 3: Scenario Design Bias Toward One Approach

**What goes wrong:** Test scenarios inadvertently favor agent capabilities (e.g., all scenarios require multi-turn refinement)

**Why it happens:** Researcher knows agent strengths and unconsciously designs scenarios to demonstrate them

**How to avoid:**
- Use EXISTING real-world conversations from production database as scenarios (not synthetic)
- Include simple scenarios where single-pass direct API should suffice
- Include complex scenarios where agent iteration should shine
- Balance: 2 simple, 2 medium, 1 complex

**Warning signs:**
- All scenarios involve multi-document references (favors agent search_documents)
- All scenarios are trivial (no chance to show agent strengths)
- Baseline produces noticeably worse results across ALL dimensions

### Pitfall 4: Conflating Provider Differences with Prompt Differences

**What goes wrong:** SDK and CLI use different prompts (system prompt prepending), confounding provider comparison

**Why it happens:** Phase 59 POC used combined prompt approach for CLI; SDK uses native system prompt support

**How to avoid:**
- Verify prompts are functionally equivalent (log first request for each provider)
- If prompts differ, note in limitations section
- Consider this a "provider as configured" comparison (real-world deployment)

**Warning signs:**
- CLI produces different tone/structure (very formal vs conversational)
- SDK includes features not present in baseline (suggests prompt enhancement)

### Pitfall 5: No Cost-Quality Tradeoff Analysis

**What goes wrong:** Recommendation focuses purely on quality improvement, ignoring cost implications

**Why it happens:** STATE.md establishes >20% improvement threshold, but final report omits cost context

**How to avoid:**
- Calculate cost per BRD for each provider (token usage × model pricing)
- Include cost-quality ratio in recommendation (improvement % / cost increase %)
- Present decision matrix: Quality Improvement vs Cost Increase vs Implementation Complexity

**Warning signs:**
- Report recommends adoption despite 50% cost increase and 12% quality improvement
- Cost data collected but not included in final recommendation section

## Code Examples

Verified patterns from research and best practices:

### Generate Test Samples Across Providers

```python
# evaluation/generate_samples.py
import asyncio
import json
from pathlib import Path
from app.services.llm import LLMFactory
from app.services.ai_service import AIService

async def generate_brd_sample(provider: str, scenario: dict, sample_num: int, db) -> dict:
    """
    Generate a single BRD using specified provider and test scenario.

    Returns dict with content, metadata (tokens, time, cost).
    """
    # Create adapter
    adapter = LLMFactory.create(provider)
    ai_service = AIService(db, adapter)

    # Prepare conversation (initial prompt + follow-ups)
    messages = [
        {"role": "user", "content": scenario["initial_prompt"]}
    ]
    for followup in scenario.get("follow_ups", []):
        # Simulate turn-by-turn conversation (agents may self-refine)
        messages.append({"role": "assistant", "content": "..."})  # Placeholder
        messages.append({"role": "user", "content": followup})

    # Final request for BRD
    messages.append({"role": "user", "content": "Please generate a comprehensive Business Requirements Document."})

    # Stream response (collect full BRD)
    brd_content = ""
    token_usage = None
    async for event in ai_service.stream_chat(messages, project_id="eval", thread_id=f"eval-{provider}-{scenario['id']}-{sample_num}"):
        if event["event"] == "text_delta":
            brd_content += event["data"]["text"]
        elif event["event"] == "message_complete":
            token_usage = event["data"].get("usage", {})

    return {
        "scenario_id": scenario["id"],
        "provider": provider,
        "sample_num": sample_num,
        "content": brd_content,
        "token_usage": token_usage,
        "cost_usd": calculate_cost(token_usage, provider)
    }

async def generate_all_samples():
    """Generate 15 BRDs: 3 providers × 5 scenarios."""
    scenarios = json.loads(Path("evaluation/test_scenarios.json").read_text())["test_scenarios"]
    providers = ["anthropic", "claude-code-sdk", "claude-code-cli"]

    for provider in providers:
        provider_dir = Path(f"evaluation_data/{provider}")
        provider_dir.mkdir(parents=True, exist_ok=True)

        for scenario in scenarios:
            sample = await generate_brd_sample(provider, scenario, 1, db)
            output_path = provider_dir / f"{scenario['id']}.md"
            output_path.write_text(sample["content"])

            # Save metadata separately
            metadata_path = Path(f"evaluation_data/metadata/{provider}_{scenario['id']}.json")
            metadata_path.parent.mkdir(exist_ok=True)
            metadata_path.write_text(json.dumps({
                "token_usage": sample["token_usage"],
                "cost_usd": sample["cost_usd"]
            }, indent=2))

if __name__ == "__main__":
    asyncio.run(generate_all_samples())
```

### Scoring Template Generation

```python
# evaluation/generate_scoring_template.py
import pandas as pd
from pathlib import Path
import random

def generate_blind_review_template():
    """Create CSV template for blind scoring."""
    # Load all generated BRDs and anonymize
    samples = []
    for provider_dir in Path("evaluation_data").iterdir():
        if provider_dir.name in ["anthropic", "claude-code-sdk", "claude-code-cli"]:
            for brd_file in provider_dir.glob("*.md"):
                review_id = hashlib.sha256(f"{provider_dir.name}{brd_file.stem}{random.random()}".encode()).hexdigest()[:8].upper()
                samples.append({
                    "review_id": review_id,
                    "completeness": "",  # Human fills 1-4
                    "ac_quality": "",
                    "consistency": "",
                    "error_coverage": "",
                    "notes": ""
                })

    # Shuffle to prevent provider grouping
    random.shuffle(samples)

    # Export template
    df = pd.DataFrame(samples)
    df.to_csv("evaluation_data/blind_review/scoring_template.csv", index=False)

    # Copy BRDs to blind_review folder with review_id as filename
    # (mapping stored separately, unsealed after scoring)

if __name__ == "__main__":
    generate_blind_review_template()
```

### Statistical Analysis and Report Generation

```python
# evaluation/generate_report.py
import pandas as pd
import json
from pathlib import Path
from jinja2 import Template

def generate_comparison_report():
    """Analyze scores and generate recommendation report."""
    # Load scored results
    scores_df = pd.read_csv("evaluation_results/scores.csv")

    # Unseal metadata (provider identifiers)
    metadata = json.loads(Path("evaluation_data/metadata/review_id_mapping.json").read_text())
    scores_df["provider"] = scores_df["review_id"].map(metadata)

    # Statistical analysis
    stats = analyze_provider_comparison(scores_df)

    # Cost analysis
    cost_summary = calculate_cost_summary()

    # Recommendation logic
    decision = make_recommendation(stats, cost_summary)

    # Generate report from template
    template = Template(Path("evaluation/report_template.md").read_text())
    report = template.render(
        stats=stats,
        cost_summary=cost_summary,
        decision=decision,
        samples_per_provider=5
    )

    Path("evaluation_results/comparison_report.md").write_text(report)

def make_recommendation(stats: dict, cost_summary: dict) -> dict:
    """
    Apply decision criteria from STATE.md:
    - Need >20% quality improvement to justify integration complexity
    - Cost overhead: 30-50% increase per request
    """
    # Average improvement across all dimensions
    sdk_avg_improvement = sum(stats[dim]["sdk_improvement_pct"] for dim in stats) / len(stats)
    cli_avg_improvement = sum(stats[dim]["cli_improvement_pct"] for dim in stats) / len(stats)

    # Check statistical significance
    sdk_significant_dims = sum(1 for dim in stats if stats[dim]["sdk_significant"])
    cli_significant_dims = sum(1 for dim in stats if stats[dim]["cli_significant"])

    # Decision matrix
    if sdk_avg_improvement >= 20 and sdk_significant_dims >= 3:
        return {
            "recommendation": "ADOPT SDK",
            "confidence": "HIGH" if sdk_significant_dims == 4 else "MEDIUM",
            "rationale": f"SDK shows {sdk_avg_improvement:.1f}% average improvement with statistical significance across {sdk_significant_dims}/4 dimensions. Justifies {cost_summary['sdk_cost_increase_pct']:.1f}% cost increase."
        }
    elif cli_avg_improvement >= 20 and cli_significant_dims >= 3:
        return {
            "recommendation": "ADOPT CLI",
            "confidence": "HIGH" if cli_significant_dims == 4 else "MEDIUM",
            "rationale": f"CLI shows {cli_avg_improvement:.1f}% average improvement with statistical significance across {cli_significant_dims}/4 dimensions. Justifies {cost_summary['cli_cost_increase_pct']:.1f}% cost increase."
        }
    elif sdk_avg_improvement >= 10 or cli_avg_improvement >= 10:
        return {
            "recommendation": "LARGER STUDY RECOMMENDED",
            "confidence": "LOW",
            "rationale": f"Marginal improvement observed (SDK: {sdk_avg_improvement:.1f}%, CLI: {cli_avg_improvement:.1f}%) but below 20% threshold. Recommend n=30 study for higher confidence."
        }
    else:
        return {
            "recommendation": "STAY WITH DIRECT API",
            "confidence": "MEDIUM",
            "rationale": f"No significant quality improvement observed. Integration complexity and cost increase not justified."
        }

if __name__ == "__main__":
    generate_comparison_report()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| A/B testing with traffic split | Laboratory comparison with fixed sample sets | 2020s (LLM evaluation evolution) | Laboratory approach allows controlled comparison without risking production quality |
| Simple accuracy metrics | Multi-dimensional quality rubrics (PEARL framework) | 2024-2026 | Captures nuanced quality differences (completeness vs consistency vs error coverage) |
| LLM-as-judge for all evaluations | Hybrid: Human judgment for quality, LLM for factuality | 2025-2026 | Human evaluation more reliable for subjective dimensions like "AC quality" |
| Manual spreadsheet scoring | Automated pipelines with blind review protocols | 2024+ | Reduces bias, increases reproducibility |
| Large sample sizes (n=100+) for statistical power | Small pilot studies (n=5-10) with acknowledged limitations | 2020s (cost-aware experimentation) | Faster iteration, lower cost, directional insights sufficient for go/no-go |

**Deprecated/outdated:**
- **BLEU/ROUGE for BRD quality**: Lexical similarity metrics don't capture BRD quality (structure, completeness, testability of ACs)
- **Single quality score**: Multi-dimensional rubrics now standard (per PEARL research, MDPI 2026)
- **Post-hoc power analysis**: Research shows power analysis should be done before data collection, not after (PMC7745163)

## Open Questions

1. **How to handle multi-turn conversation simulation?**
   - What we know: Agents may self-refine BRDs across multiple turns; direct API is single-pass
   - What's unclear: Should test scenarios force equal turn counts, or let agents use as many turns as needed?
   - Recommendation: Let agents use natural turn count (represents real-world usage), but log turn count as confounding variable

2. **Should we use LLM-as-judge for any dimensions?**
   - What we know: Research shows LLM-as-judge unreliable for subjective quality (hallucination risk)
   - What's unclear: Could LLM pre-screen for objective metrics (section count, AC count) to reduce human review load?
   - Recommendation: Use LLM for objective counts only (sections present, number of ACs, word count), human judgment for quality dimensions

3. **How to handle provider-specific features?**
   - What we know: SDK/CLI may use extended thinking, which baseline doesn't have
   - What's unclear: Is this fair comparison, or should we disable extended thinking for parity?
   - Recommendation: Compare "provider as configured in production" (real-world deployment); note capability differences in report

4. **What if results are inconclusive (marginal improvement)?**
   - What we know: 10-15% improvement with high variance may not support clear recommendation
   - What's unclear: Should we expand sample size mid-study, or report inconclusive result?
   - Recommendation: Report as "directional insights, larger study recommended" and estimate required sample size for 80% power

## Sources

### Primary (HIGH confidence)

**BRD Quality Assessment:**
- [ISO/IEC/IEEE 29148 Requirements Quality Standards](https://www.inventive.ai/blog-posts/business-requirements-document) - Referenced for BRD structure and quality requirements
- [BRD Template Best Practices (PandaDoc 2026)](https://www.pandadoc.com/business-requirements-document-template/) - Industry-standard BRD components

**LLM Evaluation Methodologies:**
- [LLM Evaluation Metrics: The Ultimate Guide (Confident AI)](https://www.confident-ai.com/blog/llm-evaluation-metrics-everything-you-need-for-llm-evaluation) - Comprehensive overview of evaluation approaches
- [LLM Evaluation Frameworks 2026 (Future AGI / Medium)](https://medium.com/@future_agi/llm-evaluation-frameworks-metrics-and-best-practices-2026-edition-162790f831f4) - Current best practices
- [PEARL Multi-Metric Framework (MDPI 2026)](https://www.mdpi.com/2078-2489/16/11/926) - Multi-dimensional rubric approach

**Statistical Methods:**
- [Sample Size and Power Analysis (PMC7745163)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7745163/) - Guidelines for small sample studies
- [Inter-rater Reliability: Cohen's Kappa (PMC3900052)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/) - Kappa statistic methodology
- [Power Analysis for Clinical Research (PMC3409926)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3409926/) - Sample size determination

### Secondary (MEDIUM confidence)

**Comparative Evaluation:**
- [A/B Testing in Machine Learning (Medium)](https://medium.com/@weidagang/demystifying-a-b-testing-in-machine-learning-a923fe07018d) - Experimental design fundamentals
- [Prompt Engineering Evaluation (Leanware)](https://www.leanware.co/insights/prompt-engineering-evaluation-metrics-how-to-measure-prompt-quality) - Baseline comparison methodology
- [Best Prompt Testing Tools 2026 (Adaline)](https://www.adaline.ai/blog/best-prompt-testing-tools-in-2026) - Tool landscape overview

**Quality Rubrics:**
- [Measuring Documentation Quality Rubric (I'd Rather Be Writing)](https://idratherbewriting.com/blog/measuring-documentation-quality-rubric-developer-docs/) - Multi-dimensional rubric design
- [Rubric Development Best Practices (Frontiers in Education)](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2018.00022/full) - Criteria definition guidelines

### Tertiary (LOW confidence)

- Various prompt engineering tool vendor blogs (Braintrust, Adaline) - Marketing content, use cautiously for technical guidance

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pandas, scipy, matplotlib are proven for this use case
- Quality rubric design: MEDIUM - Research provides frameworks but BRD-specific rubric requires customization
- Statistical methodology: HIGH - Small sample non-parametric testing well-documented
- Sample size adequacy: MEDIUM - 5 samples gives directional insights but acknowledged limitations
- Cost-quality tradeoff framework: MEDIUM - Decision criteria from STATE.md, methodology derived from research

**Research date:** 2026-02-15
**Valid until:** 2026-04-15 (60 days; evaluation methodology stable, but LLM capabilities evolving rapidly)

---

**Key Planning Inputs for gsd-planner:**

1. **Must build**: Evaluation framework with test scenarios, quality rubric, blind review protocol, statistical analysis scripts
2. **Do NOT build**: Custom statistical functions (use scipy), LLM-as-judge for quality (use human review), large-scale A/B testing infrastructure
3. **Human intervention required**: Manual scoring of 15 BRDs using rubric template (estimated 4-6 hours)
4. **Success criteria**: Comparison report with statistical significance testing, cost-quality tradeoff analysis, clear go/no-go recommendation
5. **Acknowledged limitations**: Small sample size (n=5 per condition) limits statistical power; results are directional insights not definitive proof
