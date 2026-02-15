"""Quality rubric for BRD evaluation.

Defines multi-dimensional scoring framework for assessing BRD quality
across completeness, acceptance criteria quality, consistency, and error coverage.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ScoreLevel(Enum):
    """4-point scoring scale for quality dimensions."""
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4


@dataclass
class QualityDimension:
    """A single quality dimension with scoring criteria."""
    name: str
    description: str
    criteria: Dict[ScoreLevel, str]


# Multi-dimensional quality rubric for BRD assessment
RUBRIC: Dict[str, QualityDimension] = {
    "completeness": QualityDimension(
        name="Completeness",
        description="All required BRD sections present with sufficient detail per system prompt structure",
        criteria={
            ScoreLevel.POOR: "Missing 2+ major sections (e.g., no user personas, acceptance criteria, or success metrics)",
            ScoreLevel.FAIR: "Missing 1 major section OR multiple sections lack adequate detail or depth",
            ScoreLevel.GOOD: "All expected sections present with most containing adequate detail and actionable content",
            ScoreLevel.EXCELLENT: "All sections present with comprehensive, actionable detail that fully addresses scenario requirements"
        }
    ),
    "ac_quality": QualityDimension(
        name="Acceptance Criteria Quality",
        description="Acceptance criteria are specific, measurable, testable, with explicit actors and thresholds",
        criteria={
            ScoreLevel.POOR: "Vague criteria without measurable thresholds (e.g., 'system should be fast', 'handle errors gracefully')",
            ScoreLevel.FAIR: "Some specificity but many criteria lack measurable conditions, explicit actors, or clear pass/fail states",
            ScoreLevel.GOOD: "Most criteria are testable with clear pass/fail conditions, measurable thresholds, and identified actors",
            ScoreLevel.EXCELLENT: "All criteria are fully testable with explicit actors, specific measurable thresholds, and clear trigger conditions"
        }
    ),
    "consistency": QualityDimension(
        name="Internal Consistency",
        description="No contradictions, unified terminology, coherent narrative across all sections",
        criteria={
            ScoreLevel.POOR: "Multiple contradictions in requirements or terminology inconsistencies that would confuse implementers",
            ScoreLevel.FAIR: "1-2 inconsistencies in terminology, requirement definitions, or stakeholder descriptions",
            ScoreLevel.GOOD: "Mostly consistent with only minor terminology variations that don't impact understanding",
            ScoreLevel.EXCELLENT: "Perfectly consistent terminology, requirement alignment, and coherent narrative throughout"
        }
    ),
    "error_coverage": QualityDimension(
        name="Error and Edge Case Coverage",
        description="Document addresses error handling, edge cases, unhappy paths, and recovery flows",
        criteria={
            ScoreLevel.POOR: "No error cases, edge scenarios, or unhappy paths mentioned in requirements",
            ScoreLevel.FAIR: "Mentions errors generally but lacks specific handling requirements or edge case coverage",
            ScoreLevel.GOOD: "Covers main error scenarios with specific handling requirements for critical paths",
            ScoreLevel.EXCELLENT: "Comprehensive error coverage including edge cases, recovery flows, and fallback strategies for all major features"
        }
    )
}


def score_summary(dimension_scores: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate aggregate statistics from dimension scores.

    Args:
        dimension_scores: Dict mapping dimension name to score (1-4)

    Returns:
        Dict with mean, min, max, and total score

    Example:
        >>> scores = {"completeness": 3, "ac_quality": 4, "consistency": 3, "error_coverage": 2}
        >>> score_summary(scores)
        {'mean': 3.0, 'min': 2, 'max': 4, 'total': 12}
    """
    if not dimension_scores:
        return {"mean": 0.0, "min": 0, "max": 0, "total": 0}

    scores = list(dimension_scores.values())
    return {
        "mean": sum(scores) / len(scores),
        "min": min(scores),
        "max": max(scores),
        "total": sum(scores)
    }


# Formatted rubric description for human reviewers
RUBRIC_DESCRIPTION = """# BRD Quality Scoring Rubric

Score each BRD on 4 dimensions using a 1-4 scale:

## 1. Completeness
**Description:** All required BRD sections present with sufficient detail per system prompt structure

- **1 (POOR):** Missing 2+ major sections (e.g., no user personas, acceptance criteria, or success metrics)
- **2 (FAIR):** Missing 1 major section OR multiple sections lack adequate detail or depth
- **3 (GOOD):** All expected sections present with most containing adequate detail and actionable content
- **4 (EXCELLENT):** All sections present with comprehensive, actionable detail that fully addresses scenario requirements

## 2. Acceptance Criteria Quality
**Description:** Acceptance criteria are specific, measurable, testable, with explicit actors and thresholds

- **1 (POOR):** Vague criteria without measurable thresholds (e.g., 'system should be fast', 'handle errors gracefully')
- **2 (FAIR):** Some specificity but many criteria lack measurable conditions, explicit actors, or clear pass/fail states
- **3 (GOOD):** Most criteria are testable with clear pass/fail conditions, measurable thresholds, and identified actors
- **4 (EXCELLENT):** All criteria are fully testable with explicit actors, specific measurable thresholds, and clear trigger conditions

## 3. Internal Consistency
**Description:** No contradictions, unified terminology, coherent narrative across all sections

- **1 (POOR):** Multiple contradictions in requirements or terminology inconsistencies that would confuse implementers
- **2 (FAIR):** 1-2 inconsistencies in terminology, requirement definitions, or stakeholder descriptions
- **3 (GOOD):** Mostly consistent with only minor terminology variations that don't impact understanding
- **4 (EXCELLENT):** Perfectly consistent terminology, requirement alignment, and coherent narrative throughout

## 4. Error and Edge Case Coverage
**Description:** Document addresses error handling, edge cases, unhappy paths, and recovery flows

- **1 (POOR):** No error cases, edge scenarios, or unhappy paths mentioned in requirements
- **2 (FAIR):** Mentions errors generally but lacks specific handling requirements or edge case coverage
- **3 (GOOD):** Covers main error scenarios with specific handling requirements for critical paths
- **4 (EXCELLENT):** Comprehensive error coverage including edge cases, recovery flows, and fallback strategies for all major features

---

**Scoring Process:**
1. Read the BRD without knowing which provider generated it (blind review)
2. Score each dimension independently using the criteria above
3. Add brief notes explaining your scoring rationale
4. Calculate aggregate statistics after all BRDs are scored
"""


def get_rubric_for_dimension(dimension_name: str) -> QualityDimension:
    """
    Get rubric definition for a specific dimension.

    Args:
        dimension_name: Name of the dimension (completeness, ac_quality, consistency, error_coverage)

    Returns:
        QualityDimension object with scoring criteria

    Raises:
        KeyError: If dimension_name is not in RUBRIC
    """
    return RUBRIC[dimension_name]


def validate_scores(dimension_scores: Dict[str, int]) -> List[str]:
    """
    Validate dimension scores are within valid range.

    Args:
        dimension_scores: Dict mapping dimension name to score

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    for dimension, score in dimension_scores.items():
        if dimension not in RUBRIC:
            errors.append(f"Unknown dimension: {dimension}")
        elif not (1 <= score <= 4):
            errors.append(f"Score for {dimension} must be 1-4, got {score}")

    # Check all dimensions are present
    missing = set(RUBRIC.keys()) - set(dimension_scores.keys())
    if missing:
        errors.append(f"Missing scores for dimensions: {', '.join(missing)}")

    return errors
