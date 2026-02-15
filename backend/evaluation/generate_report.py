"""Report generation for BRD quality comparison.

This module generates a comprehensive markdown comparison report from
the statistical analysis results, including quality scores, cost analysis,
cost-quality tradeoff, and actionable recommendations.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from jinja2 import Template
except ImportError:
    raise ImportError(
        "jinja2 is required for report generation. Install with: pip install jinja2>=3.1.0"
    )

from evaluation.analyze_results import run_full_analysis


def generate_comparison_report(
    scores_path: str = "evaluation_data/blind_review/scoring_template.csv",
    mapping_path: str = "evaluation_data/metadata/review_id_mapping.json",
    output_path: Optional[str] = None
) -> str:
    """
    Generate comprehensive comparison report from quality scores.

    Runs full statistical analysis pipeline and renders a markdown report
    using the Jinja2 template.

    Args:
        scores_path: Path to completed scoring CSV
        mapping_path: Path to review_id mapping JSON
        output_path: Path to save report (default: evaluation_results/comparison_report.md)

    Returns:
        Rendered report as string
    """
    # Run full analysis
    print("Running statistical analysis...")
    results = run_full_analysis(scores_path, mapping_path)

    stats = results["statistics"]
    cost_summary = results["cost_summary"]
    recommendation = results["recommendation"]
    metadata = results["metadata"]

    # Load template
    template_path = Path(__file__).parent / "report_template.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Report template not found: {template_path}")

    with open(template_path) as f:
        template_content = f.read()

    template = Template(template_content)

    # Prepare dimension data for template
    dimension_names = ["completeness", "ac_quality", "consistency", "error_coverage"]
    dimension_display = {
        "completeness": "Completeness",
        "ac_quality": "AC Quality",
        "consistency": "Consistency",
        "error_coverage": "Error Coverage"
    }

    dimensions = []
    for dim in dimension_names:
        dim_stats = stats[dim]
        dimensions.append({
            "name": dimension_display[dim],
            "baseline_mean": dim_stats["baseline_mean"],
            "sdk_mean": dim_stats["sdk_mean"],
            "cli_mean": dim_stats["cli_mean"],
            "sdk_improvement_pct": dim_stats["sdk_improvement_pct"],
            "cli_improvement_pct": dim_stats["cli_improvement_pct"],
            "sdk_significant": dim_stats["sdk_significant"],
            "cli_significant": dim_stats["cli_significant"]
        })

    # Calculate aggregate means
    baseline_avg = stats["aggregate"]["anthropic"]["mean"]
    sdk_avg = stats["aggregate"]["claude-code-sdk"]["mean"]
    cli_avg = stats["aggregate"]["claude-code-cli"]["mean"]

    # Calculate aggregate improvement percentages
    sdk_avg_improvement = recommendation["sdk_summary"]["avg_improvement_pct"]
    cli_avg_improvement = recommendation["cli_summary"]["avg_improvement_pct"]

    # Calculate quality per cost
    sdk_quality_per_cost = recommendation["sdk_summary"]["quality_per_cost"]
    cli_quality_per_cost = recommendation["cli_summary"]["quality_per_cost"]

    # Count significant dimensions
    sdk_significant_dims = recommendation["sdk_summary"]["significant_dims"]
    cli_significant_dims = recommendation["cli_summary"]["significant_dims"]

    # Prepare cost data with proper nesting for template
    cost = {
        "anthropic": cost_summary["anthropic"],
        "sdk": cost_summary["claude-code-sdk"],
        "cli": cost_summary["claude-code-cli"]
    }

    # Render template
    context = {
        "generated_date": datetime.now().strftime("%Y-%m-%d"),
        "samples_per_provider": metadata["samples_per_provider"],
        "total_samples": metadata["total_samples"],
        "providers": metadata["providers"],
        "recommendation": recommendation,
        "dimensions": dimensions,
        "baseline_avg": baseline_avg,
        "sdk_avg": sdk_avg,
        "cli_avg": cli_avg,
        "sdk_avg_improvement": sdk_avg_improvement,
        "cli_avg_improvement": cli_avg_improvement,
        "sdk_quality_per_cost": sdk_quality_per_cost,
        "cli_quality_per_cost": cli_quality_per_cost,
        "sdk_significant_dims": sdk_significant_dims,
        "cli_significant_dims": cli_significant_dims,
        "cost": cost
    }

    report = template.render(**context)

    # Save report
    if output_path is None:
        output_path = "evaluation_results/comparison_report.md"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {output_file}")

    # Also save raw statistics JSON (already saved by run_full_analysis)
    stats_file = output_file.parent / "statistics.json"
    print(f"Statistics saved to: {stats_file}")

    return report


if __name__ == "__main__":
    """Run report generation and print path."""
    try:
        report = generate_comparison_report()
        print("\n" + "="*80)
        print("REPORT GENERATION COMPLETE")
        print("="*80)
        print("\nGenerated files:")
        print("  - evaluation_results/comparison_report.md")
        print("  - evaluation_results/statistics.json")
        print("\nOpen comparison_report.md to view the full analysis and recommendation.")
    except Exception as e:
        print(f"Error generating report: {e}")
        raise
