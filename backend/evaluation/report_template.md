# Quality Comparison Report: Claude Code as AI Backend

**Generated:** {{ generated_date }}
**Samples per provider:** {{ samples_per_provider }}
**Providers compared:** {{ providers | join(', ') }}

## Executive Summary

{{ recommendation.rationale }}

**Recommendation:** {{ recommendation.recommendation }}
**Confidence:** {{ recommendation.confidence }}

## Methodology

- {{ samples_per_provider }} standardized test scenarios per provider ({{ total_samples }} total BRDs)
- 4-dimension quality rubric (1-4 scale): Completeness, AC Quality, Consistency, Error Coverage
- Blind review protocol (reviewer did not know which provider generated each BRD)
- Mann-Whitney U test for statistical significance (alpha = 0.05)
- Decision threshold: >20% average quality improvement required to justify adoption

## Quality Scores by Dimension

| Dimension | Baseline (anthropic) | SDK (claude-code-sdk) | CLI (claude-code-cli) | SDK Improvement | CLI Improvement |
|-----------|---------------------|-----------------------|-----------------------|-----------------|-----------------|
{% for dim in dimensions %}
| {{ dim.name }} | {{ "%.2f"|format(dim.baseline_mean) }} | {{ "%.2f"|format(dim.sdk_mean) }} | {{ "%.2f"|format(dim.cli_mean) }} | {{ "%+.1f%%"|format(dim.sdk_improvement_pct) }}{% if dim.sdk_significant %} *{% endif %} | {{ "%+.1f%%"|format(dim.cli_improvement_pct) }}{% if dim.cli_significant %} *{% endif %} |
{% endfor %}
| **Average** | {{ "%.2f"|format(baseline_avg) }} | {{ "%.2f"|format(sdk_avg) }} | {{ "%.2f"|format(cli_avg) }} | {{ "%+.1f%%"|format(sdk_avg_improvement) }} | {{ "%+.1f%%"|format(cli_avg_improvement) }} |

\* Statistically significant at p < 0.05

## Cost Analysis

| Metric | Baseline | SDK | CLI |
|--------|----------|-----|-----|
| Avg cost per BRD | ${{ "%.4f"|format(cost.anthropic.avg_cost_per_brd) }} | ${{ "%.4f"|format(cost.sdk.avg_cost_per_brd) }} | ${{ "%.4f"|format(cost.cli.avg_cost_per_brd) }} |
| Cost increase | — | {{ "%+.1f%%"|format(cost.sdk.cost_increase_pct) }} | {{ "%+.1f%%"|format(cost.cli.cost_increase_pct) }} |
| Avg generation time | {{ "%.1f"|format(cost.anthropic.avg_generation_time_s) }}s | {{ "%.1f"|format(cost.sdk.avg_generation_time_s) }}s | {{ "%.1f"|format(cost.cli.avg_generation_time_s) }}s |

## Cost-Quality Tradeoff

| Provider | Quality Improvement | Cost Increase | Improvement per Cost % |
|----------|--------------------|--------------|-----------------------|
| claude-code-sdk | {{ "%+.1f%%"|format(sdk_avg_improvement) }} | {{ "%+.1f%%"|format(cost.sdk.cost_increase_pct) }} | {{ "%.2f"|format(sdk_quality_per_cost) }} |
| claude-code-cli | {{ "%+.1f%%"|format(cli_avg_improvement) }} | {{ "%+.1f%%"|format(cost.cli.cost_increase_pct) }} | {{ "%.2f"|format(cli_quality_per_cost) }} |

## Decision Matrix

| Factor | claude-code-sdk | claude-code-cli | Threshold |
|--------|----------------|-----------------|-----------|
| Avg quality improvement | {{ "%+.1f%%"|format(sdk_avg_improvement) }} | {{ "%+.1f%%"|format(cli_avg_improvement) }} | >20% |
| Significant dimensions | {{ sdk_significant_dims }}/4 | {{ cli_significant_dims }}/4 | >=3/4 |
| Cost increase | {{ "%+.1f%%"|format(cost.sdk.cost_increase_pct) }} | {{ "%+.1f%%"|format(cost.cli.cost_increase_pct) }} | <50% |
| Implementation complexity | Medium (in-process MCP) | High (subprocess management) | — |

## Limitations

- Small sample size (n={{ samples_per_provider }} per condition) limits statistical power
- Results are directional insights, not definitive proof
- Single reviewer scoring (no inter-rater reliability metric)
- Test scenarios may not cover all production use cases
- Provider prompts may differ slightly (combined prompt approach for CLI vs native system prompt for SDK)

## Recommendation

**{{ recommendation.recommendation }}**

{{ recommendation.rationale }}

{% if recommendation.recommendation == "LARGER STUDY RECOMMENDED" %}
### Suggested Next Steps
- Increase sample size to n=30 per provider for 80% statistical power
- Add second independent reviewer for inter-rater reliability
- Include production conversation logs as test scenarios
{% elif "ADOPT" in recommendation.recommendation %}
### Suggested Next Steps
- Merge feature/claude-code-backend to master
- Production hardening: HTTP MCP transport, system prompt separation
- Monitor quality metrics in production for 2 weeks
{% else %}
### Suggested Next Steps
- Consider enhancing direct API with multi-pass refinement
- Archive experiment branch for future reference
- Focus on prompt engineering improvements for direct API
{% endif %}
