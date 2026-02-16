"""BRD generation orchestrator for quality comparison.

This script generates BRD samples across all three providers (anthropic,
claude-code-sdk, claude-code-cli) for each test scenario, then anonymizes
the results for blind review.

Usage:
    cd backend && python -m evaluation.generate_samples generate  # Generate all BRDs
    cd backend && python -m evaluation.generate_samples anonymize  # Anonymize for blind review
    cd backend && python -m evaluation.generate_samples all        # Run both steps
"""
import asyncio
import json
import sys
import time
import hashlib
import random
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai_service import AIService
from app.database import AsyncSessionLocal, init_db


def _build_single_prompt(scenario: Dict[str, Any]) -> str:
    """
    Build a single BRD generation prompt from a test scenario.

    Packages the entire discovery conversation into one prompt so that:
    - Both providers get identical input (fair comparison)
    - No multi-turn context loss issues with CLI subprocess
    - The AI focuses on BRD generation, not discovery
    """
    parts = [
        "Below is a complete requirements discovery conversation between a business analyst and a customer.",
        "Generate a comprehensive Business Requirements Document (BRD) based on this conversation.",
        "Include all standard BRD sections: Executive Summary, Business Objectives, User Personas,",
        "Functional Requirements, Acceptance Criteria, Success Metrics, and any other relevant sections.",
        "Do NOT ask clarifying questions — use the information provided below.",
        "",
        "IMPORTANT: Output the complete BRD directly as markdown text in your response.",
        "Do NOT use any tools, save as artifacts, or call any functions.",
        "Write the FULL BRD content inline.\n",
        "---\n",
        f"**Customer's initial request:**\n{scenario['initial_prompt']}\n",
    ]

    for i, follow_up in enumerate(scenario.get("follow_ups", []), 1):
        parts.append(f"**Customer's response #{i}:**\n{follow_up}\n")

    parts.append("---\n")
    parts.append("Now generate the comprehensive BRD based on all information above. Output it directly as markdown.")

    return "\n".join(parts)


async def generate_brd_sample(
    provider: str,
    scenario: Dict[str, Any],
    db
) -> Dict[str, Any]:
    """
    Generate a single BRD using specified provider and test scenario.

    Uses a single-call approach: packages the entire discovery conversation
    into one prompt to ensure fair comparison across providers.

    Args:
        provider: Provider name (anthropic, claude-code-cli)
        scenario: Test scenario dict from test_scenarios.json
        db: Database session

    Returns:
        Dict with:
            - content: Full BRD markdown text
            - metadata: Dict with tokens, time, cost estimate
    """
    print(f"[{provider}] {scenario['id']}: Starting generation...")

    # Create AIService for this provider
    ai_service = AIService(provider=provider)

    total_input_tokens = 0
    total_output_tokens = 0
    start_time = time.time()

    # Use a temporary evaluation project and thread
    project_id = "eval-project"
    thread_id = f"eval-{provider}-{scenario['id']}"

    try:
        # Build single prompt with all conversation context
        prompt = _build_single_prompt(scenario)
        messages = [{"role": "user", "content": prompt}]

        # Single API call — collect BRD output
        response_text = ""
        async for event in ai_service.stream_chat(messages, project_id, thread_id, db):
            if event["event"] == "text_delta":
                response_text += json.loads(event["data"])["text"]
            elif event["event"] == "message_complete":
                data = json.loads(event["data"])
                usage = data.get("usage", {})
                total_input_tokens += usage.get("input_tokens", 0)
                total_output_tokens += usage.get("output_tokens", 0)

        generation_time = time.time() - start_time

        # Calculate cost estimate
        cost_usd = calculate_cost(
            {"input_tokens": total_input_tokens, "output_tokens": total_output_tokens},
            provider
        )

        print(f"[{provider}] {scenario['id']}: Done ({total_input_tokens}/{total_output_tokens} tokens, ${cost_usd:.4f}, {generation_time:.1f}s)")

        return {
            "scenario_id": scenario["id"],
            "provider": provider,
            "content": response_text,
            "token_usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens
            },
            "generation_time_seconds": round(generation_time, 2),
            "cost_usd": cost_usd
        }

    except Exception as e:
        print(f"[{provider}] {scenario['id']}: ERROR - {str(e)}")
        raise


def calculate_cost(usage: Dict[str, int], provider: str) -> float:
    """
    Estimate USD cost based on token usage and provider.

    Pricing (approximate):
    - Claude Sonnet 4.5: $3/M input, $15/M output tokens
    - Agent providers: ~30-50% overhead (per research findings)

    Args:
        usage: Dict with input_tokens and output_tokens
        provider: Provider name

    Returns:
        float: Estimated cost in USD
    """
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # Base pricing for Claude Sonnet 4.5 (per million tokens)
    input_cost_per_m = 3.0
    output_cost_per_m = 15.0

    # Calculate base cost
    base_cost = (input_tokens / 1_000_000 * input_cost_per_m) + \
                (output_tokens / 1_000_000 * output_cost_per_m)

    # Apply overhead for agent providers
    if provider in ["claude-code-sdk", "claude-code-cli"]:
        # Research showed 30-50% overhead; use 40% as midpoint
        overhead_multiplier = 1.4
        return base_cost * overhead_multiplier

    return base_cost


async def generate_all_samples():
    """
    Generate 15 BRDs: 3 providers × 5 scenarios.

    Creates directory structure:
        evaluation_data/
            anthropic/TC-01.md, TC-02.md, ...
            claude-code-sdk/TC-01.md, TC-02.md, ...
            claude-code-cli/TC-01.md, TC-02.md, ...
            metadata/anthropic_TC-01.json, ...
    """
    # Load test scenarios
    scenarios_path = Path(__file__).parent / "test_scenarios.json"
    scenarios = json.loads(scenarios_path.read_text())["test_scenarios"]

    providers = ["anthropic", "claude-code-cli"]

    # Initialize database (needed for AI service)
    await init_db()

    # Create output directories
    base_dir = Path(__file__).parent.parent / "evaluation_data"
    base_dir.mkdir(exist_ok=True)

    for provider in providers:
        (base_dir / provider).mkdir(exist_ok=True)

    (base_dir / "metadata").mkdir(exist_ok=True)

    # Track totals
    total_cost = 0.0
    total_time = 0.0
    total_count = 0

    # Generate samples
    async with AsyncSessionLocal() as db:
        for provider in providers:
            print(f"\n=== Generating samples for {provider} ===\n")

            for scenario in scenarios:
                try:
                    sample = await generate_brd_sample(provider, scenario, db)

                    # Save BRD content
                    output_path = base_dir / provider / f"{scenario['id']}.md"
                    output_path.write_text(sample["content"], encoding="utf-8")

                    # Save metadata
                    metadata_path = base_dir / "metadata" / f"{provider}_{scenario['id']}.json"
                    metadata_path.write_text(json.dumps({
                        "provider": provider,
                        "scenario_id": scenario["id"],
                        "scenario_name": scenario["name"],
                        "complexity": scenario["complexity"],
                        "token_usage": sample["token_usage"],
                        "generation_time_seconds": sample["generation_time_seconds"],
                        "cost_usd": sample["cost_usd"]
                    }, indent=2), encoding="utf-8")

                    total_cost += sample["cost_usd"]
                    total_time += sample["generation_time_seconds"]
                    total_count += 1

                except Exception as e:
                    print(f"ERROR: Failed to generate {provider}/{scenario['id']}: {str(e)}")
                    continue

    print(f"\n=== Summary ===")
    print(f"Total BRDs generated: {total_count}")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Average cost per BRD: ${total_cost/total_count:.4f}")
    print(f"Average time per BRD: {total_time/total_count:.1f}s")


def anonymize_for_blind_review():
    """
    Create anonymized BRDs for blind review.

    Process:
    1. Read all generated BRDs from evaluation_data/{provider}/
    2. Generate random 8-char hex review_id for each
    3. Copy content to evaluation_data/blind_review/{review_id}.md
    4. Create mapping file: review_id -> {provider, scenario_id}
    5. Shuffle mapping to prevent ordering bias
    6. Create scoring template CSV with empty score columns
    """
    base_dir = Path(__file__).parent.parent / "evaluation_data"
    providers = ["anthropic", "claude-code-cli"]

    # Create blind review directory
    blind_dir = base_dir / "blind_review"
    blind_dir.mkdir(exist_ok=True)

    # Collect all BRDs and create anonymous copies
    review_mapping = {}
    samples = []

    for provider in providers:
        provider_dir = base_dir / provider
        if not provider_dir.exists():
            print(f"WARNING: {provider} directory not found, skipping")
            continue

        for brd_file in sorted(provider_dir.glob("*.md")):
            scenario_id = brd_file.stem  # TC-01, TC-02, etc.

            # Generate random review ID
            review_id = hashlib.sha256(
                f"{provider}{scenario_id}{random.random()}".encode()
            ).hexdigest()[:8].upper()

            # Copy content to blind review folder
            content = brd_file.read_text(encoding="utf-8")
            (blind_dir / f"{review_id}.md").write_text(content, encoding="utf-8")

            # Store mapping (to be sealed until scoring complete)
            review_mapping[review_id] = {
                "provider": provider,
                "scenario_id": scenario_id
            }

            # Add to samples list for scoring template
            samples.append({
                "review_id": review_id,
                "completeness": "",
                "ac_quality": "",
                "consistency": "",
                "error_coverage": "",
                "notes": ""
            })

    # Shuffle samples to prevent provider grouping in file listing
    random.shuffle(samples)

    # Save mapping (sealed until after scoring)
    mapping_path = base_dir / "metadata" / "review_id_mapping.json"
    mapping_path.write_text(json.dumps(review_mapping, indent=2), encoding="utf-8")

    # Create scoring template CSV
    import csv
    csv_path = blind_dir / "scoring_template.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "review_id", "completeness", "ac_quality", "consistency", "error_coverage", "notes"
        ])
        writer.writeheader()
        writer.writerows(samples)

    print(f"\n=== Blind Review Setup Complete ===")
    print(f"Total BRDs anonymized: {len(samples)}")
    print(f"Review files: {blind_dir}")
    print(f"Scoring template: {csv_path}")
    print(f"Mapping (sealed): {mapping_path}")
    print(f"\nNext steps:")
    print(f"1. Score BRDs using {csv_path}")
    print(f"2. After scoring, unseal {mapping_path} to analyze results")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m evaluation.generate_samples [generate|anonymize|all]")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "generate":
            asyncio.run(generate_all_samples())
        elif command == "anonymize":
            anonymize_for_blind_review()
        elif command == "all":
            asyncio.run(generate_all_samples())
            anonymize_for_blind_review()
        else:
            print(f"Unknown command: {command}")
            print("Valid commands: generate, anonymize, all")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
