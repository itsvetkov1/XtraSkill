"""Statistical analysis of BRD quality comparison results.

This module processes human quality scores from the blind review and produces
statistical comparisons between providers (anthropic baseline vs claude-code-cli).
"""
import json
from pathlib import Path
from typing import Dict, Any

# Optional dependencies for evaluation-only functionality
try:
    import pandas as pd
except ImportError:
    raise ImportError(
        "pandas is required for evaluation analysis. Install with: pip install pandas>=2.0.0"
    )

try:
    from scipy import stats
except ImportError:
    raise ImportError(
        "scipy is required for statistical analysis. Install with: pip install scipy>=1.10.0"
    )


def load_scores(
    scores_path: str = "evaluation_data/blind_review/scoring_template.csv",
    mapping_path: str = "evaluation_data/metadata/review_id_mapping.json"
) -> pd.DataFrame:
    """
    Load completed quality scores and merge with provider metadata.

    Args:
        scores_path: Path to completed scoring CSV
        mapping_path: Path to review_id -> {provider, scenario_id} mapping JSON

    Returns:
        DataFrame with columns: review_id, provider, scenario_id, completeness,
        ac_quality, consistency, error_coverage, notes

    Raises:
        FileNotFoundError: If scores or mapping file not found
        ValueError: If any scores are missing or invalid
    """
    # Read scores CSV
    scores_path_obj = Path(scores_path)
    if not scores_path_obj.exists():
        raise FileNotFoundError(f"Scores file not found: {scores_path}")

    scores_df = pd.read_csv(scores_path)

    # Validate required columns
    required_cols = ["review_id", "completeness", "ac_quality", "consistency", "error_coverage"]
    missing_cols = set(required_cols) - set(scores_df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in scores CSV: {missing_cols}")

    # Check for empty scores (NaN values)
    score_cols = ["completeness", "ac_quality", "consistency", "error_coverage"]
    if scores_df[score_cols].isnull().any().any():
        empty_reviews = scores_df[scores_df[score_cols].isnull().any(axis=1)]["review_id"].tolist()
        raise ValueError(f"Empty scores found for review_ids: {empty_reviews}")

    # Read mapping file
    mapping_path_obj = Path(mapping_path)
    if not mapping_path_obj.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

    with open(mapping_path_obj) as f:
        mapping = json.load(f)

    # Merge provider info
    scores_df["provider"] = scores_df["review_id"].map(
        lambda rid: mapping.get(rid, {}).get("provider")
    )
    scores_df["scenario_id"] = scores_df["review_id"].map(
        lambda rid: mapping.get(rid, {}).get("scenario_id")
    )

    # Validate all review_ids have mapping entries
    missing_mappings = scores_df[scores_df["provider"].isnull()]["review_id"].tolist()
    if missing_mappings:
        raise ValueError(f"Review IDs missing from mapping: {missing_mappings}")

    return scores_df


def analyze_provider_comparison(scores_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Compare quality scores between anthropic baseline and claude-code-cli.

    Computes per-dimension statistics:
    - Mean and standard deviation for each provider
    - Improvement percentage relative to baseline (anthropic)
    - Mann-Whitney U test for statistical significance

    Args:
        scores_df: DataFrame from load_scores() with provider and score columns

    Returns:
        Dict structured as:
        {
            dimension: {
                baseline_mean, baseline_std,
                cli_mean, cli_std,
                cli_improvement_pct,
                cli_vs_baseline_pvalue,
                cli_significant
            }
        }
    """
    results = {}
    dimensions = ["completeness", "ac_quality", "consistency", "error_coverage"]

    for dim in dimensions:
        baseline = scores_df[scores_df["provider"] == "anthropic"][dim]
        cli = scores_df[scores_df["provider"] == "claude-code-cli"][dim]

        baseline_mean = baseline.mean()
        cli_mean = cli.mean()

        cli_improvement_pct = ((cli_mean - baseline_mean) / baseline_mean * 100) if baseline_mean > 0 else 0

        # Mann-Whitney U test (non-parametric, suitable for ordinal data and small samples)
        cli_vs_baseline = stats.mannwhitneyu(cli, baseline, alternative='two-sided')

        results[dim] = {
            "baseline_mean": baseline_mean,
            "baseline_std": baseline.std(),
            "cli_mean": cli_mean,
            "cli_std": cli.std(),
            "cli_improvement_pct": cli_improvement_pct,
            "cli_vs_baseline_pvalue": cli_vs_baseline.pvalue,
            "cli_significant": cli_vs_baseline.pvalue < 0.05
        }

    # Compute aggregate scores
    aggregate = {}
    for provider in ["anthropic", "claude-code-cli"]:
        provider_scores = scores_df[scores_df["provider"] == provider]
        aggregate[provider] = {
            "mean": provider_scores[dimensions].mean().mean(),
            "std": provider_scores[dimensions].mean().std()
        }

    results["aggregate"] = aggregate

    return results


def calculate_cost_summary() -> Dict[str, Dict[str, float]]:
    """
    Calculate cost summary statistics from metadata files.

    Returns:
        Dict with per-provider cost and timing stats.
    """
    metadata_dir = Path("evaluation_data/metadata")
    if not metadata_dir.exists():
        raise FileNotFoundError(f"Metadata directory not found: {metadata_dir}")

    provider_stats = {}
    providers = ["anthropic", "claude-code-cli"]

    for provider in providers:
        metadata_files = list(metadata_dir.glob(f"{provider}_*.json"))

        if not metadata_files:
            raise FileNotFoundError(f"No metadata files found for provider: {provider}")

        total_input = 0
        total_output = 0
        total_cost = 0.0
        total_time = 0.0
        count = 0

        for metadata_file in metadata_files:
            with open(metadata_file) as f:
                metadata = json.load(f)

            usage = metadata.get("token_usage", {})
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
            total_cost += metadata.get("cost_usd", 0.0)
            total_time += metadata.get("generation_time_seconds", metadata.get("generation_time_s", 0.0))
            count += 1

        provider_stats[provider] = {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": total_cost,
            "avg_cost_per_brd": total_cost / count if count > 0 else 0.0,
            "avg_generation_time_s": total_time / count if count > 0 else 0.0
        }

    # Calculate cost increase relative to baseline
    baseline_cost = provider_stats["anthropic"]["avg_cost_per_brd"]
    cli_cost = provider_stats["claude-code-cli"]["avg_cost_per_brd"]
    provider_stats["claude-code-cli"]["cost_increase_pct"] = (
        ((cli_cost - baseline_cost) / baseline_cost * 100) if baseline_cost > 0 else 0
    )
    provider_stats["anthropic"]["cost_increase_pct"] = 0.0

    return provider_stats


def make_recommendation(analysis_stats: Dict[str, Any], cost_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate adoption recommendation based on decision criteria.

    Decision criteria from STATE.md:
    - Need >20% average quality improvement to justify adoption
    - Cost overhead threshold: 30-50% increase acceptable IF quality justifies it
    - Statistical significance: prefer 3+ dimensions with p < 0.05
    """
    dimensions = ["completeness", "ac_quality", "consistency", "error_coverage"]

    cli_avg_improvement = sum(analysis_stats[dim]["cli_improvement_pct"] for dim in dimensions) / len(dimensions)
    cli_significant_dims = sum(1 for dim in dimensions if analysis_stats[dim]["cli_significant"])
    cli_cost_increase = cost_summary["claude-code-cli"]["cost_increase_pct"]

    cli_summary = {
        "avg_improvement_pct": cli_avg_improvement,
        "significant_dims": cli_significant_dims,
        "cost_increase_pct": cli_cost_increase,
        "quality_per_cost": cli_avg_improvement / cli_cost_increase if cli_cost_increase > 0 else 0
    }

    # Decision logic
    cli_qualifies = cli_avg_improvement >= 20 and cli_significant_dims >= 3

    if cli_qualifies:
        recommendation = "ADOPT claude-code-cli"
        confidence = "HIGH" if cli_significant_dims == 4 else "MEDIUM"
        rationale = (
            f"CLI shows {cli_avg_improvement:.1f}% average quality improvement with statistical significance "
            f"across {cli_significant_dims}/4 dimensions. Cost increase of {cli_cost_increase:.1f}% is justified "
            f"by quality gains."
        )
    elif cli_avg_improvement >= 10:
        recommendation = "LARGER STUDY RECOMMENDED"
        confidence = "LOW"
        rationale = (
            f"Marginal improvement observed (CLI: {cli_avg_improvement:.1f}%) "
            f"but below 20% decision threshold. Current sample size (n=5 per provider) limits statistical power. "
            f"Recommend expanding to n=30 per provider for higher confidence before making adoption decision."
        )
    else:
        recommendation = "STAY WITH DIRECT API"
        confidence = "MEDIUM"
        rationale = (
            f"No significant quality improvement observed (CLI: {cli_avg_improvement:.1f}%). "
            f"Integration complexity and cost increase ({cli_cost_increase:.1f}%) "
            f"not justified by quality gains. Focus on prompt engineering improvements for direct API approach."
        )

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "rationale": rationale,
        "cli_summary": cli_summary
    }


def run_full_analysis(
    scores_path: str = "evaluation_data/blind_review/scoring_template.csv",
    mapping_path: str = "evaluation_data/metadata/review_id_mapping.json",
    output_dir: str = "evaluation_results"
) -> Dict[str, Any]:
    """Run complete analysis pipeline and save results."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Loading scores...")
    scores_df = load_scores(scores_path, mapping_path)

    print("Analyzing provider comparison...")
    analysis_stats = analyze_provider_comparison(scores_df)

    print("Calculating cost summary...")
    cost_summary = calculate_cost_summary()

    print("Generating recommendation...")
    recommendation = make_recommendation(analysis_stats, cost_summary)

    results = {
        "statistics": analysis_stats,
        "cost_summary": cost_summary,
        "recommendation": recommendation,
        "metadata": {
            "total_samples": len(scores_df),
            "samples_per_provider": len(scores_df) // 2,
            "providers": ["anthropic", "claude-code-cli"]
        }
    }

    output_file = output_path / "statistics.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    return results


if __name__ == "__main__":
    """Run full analysis and print summary table."""
    try:
        results = run_full_analysis()

        print("\n" + "="*80)
        print("QUALITY COMPARISON ANALYSIS SUMMARY")
        print("="*80)

        analysis_stats = results["statistics"]
        cost = results["cost_summary"]
        rec = results["recommendation"]

        print("\nQuality Scores by Dimension:")
        print("-" * 70)
        print(f"{'Dimension':<20} {'Baseline':>10} {'CLI':>10} {'CLI Δ%':>10} {'p-value':>10}")
        print("-" * 70)

        dimensions = ["completeness", "ac_quality", "consistency", "error_coverage"]
        for dim in dimensions:
            d = analysis_stats[dim]
            sig = " *" if d["cli_significant"] else ""
            print(
                f"{dim:<20} {d['baseline_mean']:>10.2f} "
                f"{d['cli_mean']:>10.2f} "
                f"{d['cli_improvement_pct']:>9.1f}%{sig:2} "
                f"{d['cli_vs_baseline_pvalue']:>10.4f}"
            )

        print("\n* Statistically significant at p < 0.05")

        print("\n\nCost Analysis:")
        print("-" * 70)
        for provider in ["anthropic", "claude-code-cli"]:
            pc = cost[provider]
            print(
                f"{provider:<20} ${pc['avg_cost_per_brd']:>.4f}/BRD  "
                f"{pc['cost_increase_pct']:>+.1f}%  "
                f"{pc['avg_generation_time_s']:>.1f}s avg"
            )

        print(f"\n\nRecommendation: {rec['recommendation']} ({rec['confidence']} confidence)")
        print(f"\n{rec['rationale']}")
        print("="*80)

    except Exception as e:
        print(f"Error running analysis: {e}")
        raise
