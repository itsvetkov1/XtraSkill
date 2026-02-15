"""Statistical analysis of BRD quality comparison results.

This module processes human quality scores from the blind review and produces
statistical comparisons between providers (anthropic baseline, claude-code-sdk, claude-code-cli).
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
    Compare quality scores across providers with statistical tests.

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
                baseline_mean: float,
                sdk_mean: float,
                cli_mean: float,
                sdk_improvement_pct: float,
                cli_improvement_pct: float,
                sdk_vs_baseline_pvalue: float,
                cli_vs_baseline_pvalue: float,
                sdk_significant: bool,
                cli_significant: bool
            }
        }
    """
    results = {}
    dimensions = ["completeness", "ac_quality", "consistency", "error_coverage"]

    for dim in dimensions:
        # Group by provider
        baseline = scores_df[scores_df["provider"] == "anthropic"][dim]
        sdk = scores_df[scores_df["provider"] == "claude-code-sdk"][dim]
        cli = scores_df[scores_df["provider"] == "claude-code-cli"][dim]

        # Calculate means and std dev
        baseline_mean = baseline.mean()
        sdk_mean = sdk.mean()
        cli_mean = cli.mean()

        # Calculate improvement percentages
        sdk_improvement_pct = ((sdk_mean - baseline_mean) / baseline_mean * 100) if baseline_mean > 0 else 0
        cli_improvement_pct = ((cli_mean - baseline_mean) / baseline_mean * 100) if baseline_mean > 0 else 0

        # Mann-Whitney U test (non-parametric, suitable for ordinal data and small samples)
        # Use two-sided alternative to detect both improvement and degradation
        sdk_vs_baseline = stats.mannwhitneyu(sdk, baseline, alternative='two-sided')
        cli_vs_baseline = stats.mannwhitneyu(cli, baseline, alternative='two-sided')

        results[dim] = {
            "baseline_mean": baseline_mean,
            "baseline_std": baseline.std(),
            "sdk_mean": sdk_mean,
            "sdk_std": sdk.std(),
            "cli_mean": cli_mean,
            "cli_std": cli.std(),
            "sdk_improvement_pct": sdk_improvement_pct,
            "cli_improvement_pct": cli_improvement_pct,
            "sdk_vs_baseline_pvalue": sdk_vs_baseline.pvalue,
            "cli_vs_baseline_pvalue": cli_vs_baseline.pvalue,
            "sdk_significant": sdk_vs_baseline.pvalue < 0.05,
            "cli_significant": cli_vs_baseline.pvalue < 0.05
        }

    # Compute aggregate scores (mean across all 4 dimensions)
    aggregate = {}
    for provider in ["anthropic", "claude-code-sdk", "claude-code-cli"]:
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

    Reads evaluation_data/metadata/{provider}_{scenario_id}.json files and
    aggregates token usage and cost per provider.

    Returns:
        Dict structured as:
        {
            provider: {
                total_input_tokens: int,
                total_output_tokens: int,
                total_cost_usd: float,
                avg_cost_per_brd: float,
                avg_generation_time_s: float,
                cost_increase_pct: float  # relative to baseline (anthropic)
            }
        }
    """
    metadata_dir = Path("evaluation_data/metadata")
    if not metadata_dir.exists():
        raise FileNotFoundError(f"Metadata directory not found: {metadata_dir}")

    # Aggregate by provider
    provider_stats = {}
    providers = ["anthropic", "claude-code-sdk", "claude-code-cli"]

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

            # Extract token usage
            usage = metadata.get("token_usage", {})
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)

            # Extract cost and time
            total_cost += metadata.get("cost_usd", 0.0)
            total_time += metadata.get("generation_time_s", 0.0)
            count += 1

        provider_stats[provider] = {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": total_cost,
            "avg_cost_per_brd": total_cost / count if count > 0 else 0.0,
            "avg_generation_time_s": total_time / count if count > 0 else 0.0
        }

    # Calculate cost increase percentages relative to baseline
    baseline_cost = provider_stats["anthropic"]["avg_cost_per_brd"]
    for provider in ["claude-code-sdk", "claude-code-cli"]:
        provider_cost = provider_stats[provider]["avg_cost_per_brd"]
        cost_increase_pct = ((provider_cost - baseline_cost) / baseline_cost * 100) if baseline_cost > 0 else 0
        provider_stats[provider]["cost_increase_pct"] = cost_increase_pct

    # Baseline has 0% increase by definition
    provider_stats["anthropic"]["cost_increase_pct"] = 0.0

    return provider_stats


def make_recommendation(stats: Dict[str, Any], cost_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate adoption recommendation based on decision criteria.

    Decision criteria from STATE.md:
    - Need >20% average quality improvement to justify adoption
    - Cost overhead threshold: 30-50% increase acceptable IF quality justifies it
    - Statistical significance: prefer 3+ dimensions with p < 0.05

    Args:
        stats: Output from analyze_provider_comparison()
        cost_summary: Output from calculate_cost_summary()

    Returns:
        Dict with:
        {
            recommendation: str,  # "ADOPT [provider]", "LARGER STUDY RECOMMENDED", "STAY WITH DIRECT API"
            confidence: str,  # "HIGH", "MEDIUM", "LOW"
            rationale: str,
            sdk_summary: Dict,
            cli_summary: Dict
        }
    """
    dimensions = ["completeness", "ac_quality", "consistency", "error_coverage"]

    # Calculate average improvement across all 4 dimensions
    sdk_avg_improvement = sum(stats[dim]["sdk_improvement_pct"] for dim in dimensions) / len(dimensions)
    cli_avg_improvement = sum(stats[dim]["cli_improvement_pct"] for dim in dimensions) / len(dimensions)

    # Count statistically significant dimensions
    sdk_significant_dims = sum(1 for dim in dimensions if stats[dim]["sdk_significant"])
    cli_significant_dims = sum(1 for dim in dimensions if stats[dim]["cli_significant"])

    # Get cost increases
    sdk_cost_increase = cost_summary["claude-code-sdk"]["cost_increase_pct"]
    cli_cost_increase = cost_summary["claude-code-cli"]["cost_increase_pct"]

    # Prepare summaries
    sdk_summary = {
        "avg_improvement_pct": sdk_avg_improvement,
        "significant_dims": sdk_significant_dims,
        "cost_increase_pct": sdk_cost_increase,
        "quality_per_cost": sdk_avg_improvement / sdk_cost_increase if sdk_cost_increase > 0 else 0
    }

    cli_summary = {
        "avg_improvement_pct": cli_avg_improvement,
        "significant_dims": cli_significant_dims,
        "cost_increase_pct": cli_cost_increase,
        "quality_per_cost": cli_avg_improvement / cli_cost_increase if cli_cost_increase > 0 else 0
    }

    # Decision logic
    # Check if SDK qualifies (>20% improvement AND 3+ significant dimensions)
    sdk_qualifies = sdk_avg_improvement >= 20 and sdk_significant_dims >= 3

    # Check if CLI qualifies
    cli_qualifies = cli_avg_improvement >= 20 and cli_significant_dims >= 3

    if sdk_qualifies and cli_qualifies:
        # Both qualify - pick the better one
        if sdk_avg_improvement > cli_avg_improvement:
            recommendation = "ADOPT claude-code-sdk"
            confidence = "HIGH" if sdk_significant_dims == 4 else "MEDIUM"
            rationale = (
                f"SDK shows {sdk_avg_improvement:.1f}% average quality improvement with statistical significance "
                f"across {sdk_significant_dims}/4 dimensions. Cost increase of {sdk_cost_increase:.1f}% is justified "
                f"by quality gains. SDK outperforms CLI ({cli_avg_improvement:.1f}% improvement) with lower "
                f"implementation complexity (in-process MCP vs subprocess management)."
            )
        else:
            recommendation = "ADOPT claude-code-cli"
            confidence = "HIGH" if cli_significant_dims == 4 else "MEDIUM"
            rationale = (
                f"CLI shows {cli_avg_improvement:.1f}% average quality improvement with statistical significance "
                f"across {cli_significant_dims}/4 dimensions. Cost increase of {cli_cost_increase:.1f}% is justified "
                f"by quality gains. CLI outperforms SDK ({sdk_avg_improvement:.1f}% improvement)."
            )
    elif sdk_qualifies:
        recommendation = "ADOPT claude-code-sdk"
        confidence = "HIGH" if sdk_significant_dims == 4 else "MEDIUM"
        rationale = (
            f"SDK shows {sdk_avg_improvement:.1f}% average quality improvement with statistical significance "
            f"across {sdk_significant_dims}/4 dimensions. Cost increase of {sdk_cost_increase:.1f}% is justified "
            f"by quality gains. In-process MCP integration simpler than CLI subprocess approach."
        )
    elif cli_qualifies:
        recommendation = "ADOPT claude-code-cli"
        confidence = "HIGH" if cli_significant_dims == 4 else "MEDIUM"
        rationale = (
            f"CLI shows {cli_avg_improvement:.1f}% average quality improvement with statistical significance "
            f"across {cli_significant_dims}/4 dimensions. Cost increase of {cli_cost_increase:.1f}% is justified "
            f"by quality gains."
        )
    elif sdk_avg_improvement >= 10 or cli_avg_improvement >= 10:
        # Marginal improvement (10-20%)
        recommendation = "LARGER STUDY RECOMMENDED"
        confidence = "LOW"
        rationale = (
            f"Marginal improvement observed (SDK: {sdk_avg_improvement:.1f}%, CLI: {cli_avg_improvement:.1f}%) "
            f"but below 20% decision threshold. Current sample size (n=5 per provider) limits statistical power. "
            f"Recommend expanding to n=30 per provider for higher confidence before making adoption decision."
        )
    else:
        # No significant improvement
        recommendation = "STAY WITH DIRECT API"
        confidence = "MEDIUM"
        rationale = (
            f"No significant quality improvement observed (SDK: {sdk_avg_improvement:.1f}%, CLI: {cli_avg_improvement:.1f}%). "
            f"Integration complexity and cost increase ({sdk_cost_increase:.1f}% SDK, {cli_cost_increase:.1f}% CLI) "
            f"not justified by quality gains. Focus on prompt engineering improvements for direct API approach."
        )

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "rationale": rationale,
        "sdk_summary": sdk_summary,
        "cli_summary": cli_summary
    }


def run_full_analysis(
    scores_path: str = "evaluation_data/blind_review/scoring_template.csv",
    mapping_path: str = "evaluation_data/metadata/review_id_mapping.json",
    output_dir: str = "evaluation_results"
) -> Dict[str, Any]:
    """
    Run complete analysis pipeline and save results.

    Steps:
    1. Load scores with provider mapping
    2. Analyze provider comparison (statistical tests)
    3. Calculate cost summary
    4. Generate recommendation

    Args:
        scores_path: Path to completed scoring CSV
        mapping_path: Path to review_id mapping JSON
        output_dir: Directory to save results

    Returns:
        Dict with all analysis results
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Run analysis pipeline
    print("Loading scores...")
    scores_df = load_scores(scores_path, mapping_path)

    print("Analyzing provider comparison...")
    stats = analyze_provider_comparison(scores_df)

    print("Calculating cost summary...")
    cost_summary = calculate_cost_summary()

    print("Generating recommendation...")
    recommendation = make_recommendation(stats, cost_summary)

    # Combine results
    results = {
        "statistics": stats,
        "cost_summary": cost_summary,
        "recommendation": recommendation,
        "metadata": {
            "total_samples": len(scores_df),
            "samples_per_provider": len(scores_df) // 3,
            "providers": ["anthropic", "claude-code-sdk", "claude-code-cli"]
        }
    }

    # Save to JSON
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

        stats = results["statistics"]
        cost = results["cost_summary"]
        rec = results["recommendation"]

        # Print quality scores table
        print("\nQuality Scores by Dimension:")
        print("-" * 80)
        print(f"{'Dimension':<20} {'Baseline':>10} {'SDK':>10} {'CLI':>10} {'SDK Δ%':>10} {'CLI Δ%':>10}")
        print("-" * 80)

        dimensions = ["completeness", "ac_quality", "consistency", "error_coverage"]
        for dim in dimensions:
            dim_stats = stats[dim]
            sig_sdk = " *" if dim_stats["sdk_significant"] else ""
            sig_cli = " *" if dim_stats["cli_significant"] else ""
            print(
                f"{dim:<20} {dim_stats['baseline_mean']:>10.2f} "
                f"{dim_stats['sdk_mean']:>10.2f} {dim_stats['cli_mean']:>10.2f} "
                f"{dim_stats['sdk_improvement_pct']:>9.1f}%{sig_sdk:2} "
                f"{dim_stats['cli_improvement_pct']:>9.1f}%{sig_cli:2}"
            )

        print("\n* Statistically significant at p < 0.05")

        # Print cost table
        print("\n\nCost Analysis:")
        print("-" * 80)
        print(f"{'Provider':<20} {'Avg Cost/BRD':>15} {'Cost Increase':>15} {'Avg Time (s)':>15}")
        print("-" * 80)
        for provider in ["anthropic", "claude-code-sdk", "claude-code-cli"]:
            provider_cost = cost[provider]
            print(
                f"{provider:<20} ${provider_cost['avg_cost_per_brd']:>14.4f} "
                f"{provider_cost['cost_increase_pct']:>14.1f}% "
                f"{provider_cost['avg_generation_time_s']:>14.1f}"
            )

        # Print recommendation
        print("\n\nRecommendation:")
        print("-" * 80)
        print(f"Decision: {rec['recommendation']}")
        print(f"Confidence: {rec['confidence']}")
        print(f"\n{rec['rationale']}")
        print("="*80)

    except Exception as e:
        print(f"Error running analysis: {e}")
        raise
