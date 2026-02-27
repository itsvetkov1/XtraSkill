"""
BRD Generator Service.

Provides tools for generating and validating Business Requirements Documents
following the brd-template.md structure.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from contextvars import ContextVar

from claude_agent_sdk import tool

logger = logging.getLogger(__name__)

# Required sections in a BRD (must be present)
BRD_REQUIRED_SECTIONS = [
    "Executive Summary",
    "Business Objectives",
    "User Personas",
    "Functional Requirements",
    "Success Metrics",
]

# Optional sections (should be present if applicable)
BRD_OPTIONAL_SECTIONS = [
    "Business Context",
    "User Flows and Journeys",
    "Business Processes",
    "Stakeholder Analysis",
    "Regulatory and Compliance Requirements",
    "Assumptions and Constraints",
    "Risks and Mitigation Strategies",
    "Next Steps",
]

# All sections in recommended order
BRD_SECTIONS = BRD_REQUIRED_SECTIONS + BRD_OPTIONAL_SECTIONS


@dataclass
class ValidationResult:
    """Result of BRD validation."""
    is_valid: bool
    missing_sections: List[str]
    warnings: List[str]
    section_count: int


def validate_brd_content(content: str) -> ValidationResult:
    """
    Validate BRD content against template requirements.

    Checks for:
    - All required sections present
    - Sections have content (not empty placeholders)
    - No technical implementation language

    Args:
        content: BRD markdown content

    Returns:
        ValidationResult with validation status and issues
    """
    missing_sections = []
    warnings = []
    found_sections = 0

    # Check required sections
    for section in BRD_REQUIRED_SECTIONS:
        # Look for section header (## or ###)
        pattern = rf"##\s*{re.escape(section)}"
        if not re.search(pattern, content, re.IGNORECASE):
            missing_sections.append(section)
        else:
            found_sections += 1

    # Check optional sections (warnings only)
    for section in BRD_OPTIONAL_SECTIONS:
        pattern = rf"##\s*{re.escape(section)}"
        if re.search(pattern, content, re.IGNORECASE):
            found_sections += 1

    # Check for empty placeholders
    placeholder_patterns = [
        r"\[TBD\]",
        r"\[TODO\]",
        r"\[To be determined\]",
        r"\[Insert .+\]",
        r"\[Add .+\]",
    ]
    for pattern in placeholder_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"Found placeholder text matching: {pattern}")

    # Check for technical implementation language
    technical_terms = [
        r"\bReact\b",
        r"\bVue\b",
        r"\bAngular\b",
        r"\bPython\b",
        r"\bJava\b",
        r"\bNode\.js\b",
        r"\bAPI endpoint\b",
        r"\bmicroservice\b",
        r"\bPostgreSQL\b",
        r"\bMongoDB\b",
        r"\bAWS\b",
        r"\bAzure\b",
        r"\bDocker\b",
        r"\bKubernetes\b",
    ]
    for term in technical_terms:
        if re.search(term, content, re.IGNORECASE):
            warnings.append(f"Technical term found (should be business-focused): {term}")

    is_valid = len(missing_sections) == 0

    return ValidationResult(
        is_valid=is_valid,
        missing_sections=missing_sections,
        warnings=warnings,
        section_count=found_sections
    )


def get_brd_template_structure() -> str:
    """
    Get the BRD template structure as a reference.

    Returns markdown template with section headers and guidance.
    """
    return """# Business Requirements Document

## Executive Summary
[2-3 paragraphs: project name, primary business objective, target users, expected business value]

## Business Context
[Current state challenges, market drivers, strategic alignment]

## Business Objectives

### Primary Objective
[Detailed description with measurable success criteria]

### Secondary Objectives
[Additional goals with rationale]

## User Personas

### Persona 1: [Role/Name]
- **Demographics:** [Relevant characteristics]
- **Role and Responsibilities:** [What they do]
- **Pain Points:** [Current challenges]
- **Goals:** [What they want to achieve]
- **Technical Proficiency:** [Skill level]

## User Flows and Journeys

### Flow 1: [Flow Name]
**User Persona:** [Which persona]
**Business Goal:** [Objective supported]
**User Goal:** [What user wants to accomplish]

**Steps:**
1. [Step-by-step flow]

## Functional Requirements

### Must-Have Requirements (Priority 0)
1. **[Requirement Title]**
   - Description: [What is needed]
   - Business rationale: [Why it matters]
   - User story: As a [user], I need [capability] so that [benefit]
   - Success criteria: [How to verify]

### Should-Have Requirements (Priority 1)
[Same structure as P0]

### Nice-to-Have Requirements (Priority 2)
[Same structure as P0]

## Business Processes

### Process 1: [Process Name]
- **Current State:** [How it works today]
- **Future State:** [How product improves this]
- **Process Flow:** [Step-by-step future state]
- **Stakeholders:** [Who is involved]

## Stakeholder Analysis

| Stakeholder Group | Role | Key Requirements | Success Criteria | Concerns |
|-------------------|------|------------------|------------------|----------|
| [Group] | [Role] | [Requirements] | [Success] | [Concerns] |

## Success Metrics and KPIs

| KPI | Current State | Target State | Measurement Method | Timeline |
|-----|---------------|--------------|-------------------|----------|
| [Metric] | [Baseline] | [Goal] | [Measurement] | [When] |

## Regulatory and Compliance Requirements
[Specific mandates, standards, certifications, or "No specific requirements identified"]

## Assumptions and Constraints
**Assumptions:**
- [Key assumptions]

**Constraints:**
- [Known constraints]

## Risks and Mitigation Strategies

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|-------------------|
| [Risk] | [H/M/L] | [H/M/L] | [Strategy] |

## Next Steps
- Technical team review and architecture design
- Proposal development with cost and timeline estimates
- Customer review and sign-off on requirements
"""


def format_preflight_checklist(
    has_objective: bool,
    has_personas: bool,
    has_flows: bool,
    has_metrics: bool,
    has_requirements: bool,
    has_stakeholders: bool
) -> Tuple[bool, str]:
    """
    Format pre-flight validation checklist.

    Args:
        has_*: Boolean flags for each required element

    Returns:
        Tuple of (all_passed, formatted_checklist)
    """
    checks = [
        ("Primary business objective clearly defined", has_objective),
        ("Target user personas identified", has_personas),
        ("Key user flows documented", has_flows),
        ("Success metrics specified", has_metrics),
        ("Core functional requirements captured", has_requirements),
        ("Stakeholders identified", has_stakeholders),
    ]

    lines = ["**Pre-Flight Validation Checklist:**"]
    all_passed = True

    for label, passed in checks:
        icon = "[x]" if passed else "[ ]"
        lines.append(f"- {icon} {label}")
        if not passed:
            all_passed = False

    checklist = "\n".join(lines)

    return all_passed, checklist


# Context variables for tool
_db_context: ContextVar[Any] = ContextVar("db_context")
_thread_id_context: ContextVar[str] = ContextVar("thread_id_context")


@tool(
    "generate_brd",
    """Generate a complete Business Requirements Document (BRD).

USE THIS TOOL ONLY WHEN:
- Customer explicitly requests BRD generation with phrases like:
  - "Create the documentation"
  - "Generate the BRD"
  - "I'm ready for the deliverables"
  - "Build the requirements document"

BEFORE CALLING THIS TOOL:
1. Verify you have gathered:
   - Primary business objective (clearly defined, measurable)
   - Target user personas (at least one with role, pain points, goals)
   - Key user flows (what users need to accomplish)
   - Success metrics (how success will be measured)
   - Core functional requirements (what product must do)
   - Stakeholders (who cares about this product)

2. If any critical information is missing, ask targeted questions first (max 3-4)

3. After generating, present to user with:
   "Business Requirements Document complete. Review for accuracy and completeness."

The generated BRD will follow the complete template structure with all sections.""",
    {
        "title": str,
        "executive_summary": str,
        "business_context": str,
        "primary_objective": str,
        "secondary_objectives": str,
        "personas": str,
        "user_flows": str,
        "functional_requirements": str,
        "business_processes": str,
        "stakeholder_analysis": str,
        "success_metrics": str,
        "compliance_requirements": str,
        "assumptions_constraints": str,
        "risks_mitigation": str,
        "next_steps": str
    }
)
async def generate_brd_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate and save a complete BRD artifact.

    Assembles all sections into a complete BRD following template structure.
    Validates content before saving.
    """
    from app.models import Artifact, ArtifactType

    try:
        db = _db_context.get()
        thread_id = _thread_id_context.get()
    except LookupError:
        return {
            "content": [{
                "type": "text",
                "text": "Error: BRD context not available"
            }]
        }

    # Assemble BRD content
    brd_content = f"""# Business Requirements Document: {args.get('title', 'Untitled')}

## Executive Summary
{args.get('executive_summary', '[Not provided]')}

## Business Context
{args.get('business_context', '[Not provided]')}

## Business Objectives

### Primary Objective
{args.get('primary_objective', '[Not provided]')}

### Secondary Objectives
{args.get('secondary_objectives', 'None identified.')}

## User Personas
{args.get('personas', '[Not provided]')}

## User Flows and Journeys
{args.get('user_flows', '[Not provided]')}

## Functional Requirements
{args.get('functional_requirements', '[Not provided]')}

## Business Processes
{args.get('business_processes', 'To be analyzed during implementation planning.')}

## Stakeholder Analysis
{args.get('stakeholder_analysis', '[Not provided]')}

## Success Metrics and KPIs
{args.get('success_metrics', '[Not provided]')}

## Regulatory and Compliance Requirements
{args.get('compliance_requirements', 'No specific regulatory or compliance requirements identified.')}

## Assumptions and Constraints
{args.get('assumptions_constraints', 'To be validated during implementation planning.')}

## Risks and Mitigation Strategies
{args.get('risks_mitigation', 'To be assessed during implementation planning.')}

## Next Steps
{args.get('next_steps', '''- Technical team review and architecture design
- Proposal development with cost and timeline estimates
- Customer review and sign-off on requirements''')}
"""

    # Validate the generated content
    validation = validate_brd_content(brd_content)

    # Log validation results
    if not validation.is_valid:
        logger.warning(f"BRD validation failed: missing {validation.missing_sections}")
    if validation.warnings:
        logger.info(f"BRD validation warnings: {validation.warnings}")

    # Save as artifact
    artifact = Artifact(
        thread_id=thread_id,
        artifact_type=ArtifactType.BRD,
        title=f"BRD: {args.get('title', 'Untitled')}",
        content_markdown=brd_content
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    event_data = {
        "id": artifact.id,
        "artifact_type": "brd",
        "title": artifact.title
    }

    # Build response message
    response_parts = [
        f"Business Requirements Document saved: '{artifact.title}' (ID: {artifact.id})",
        f"Sections included: {validation.section_count}",
    ]

    if validation.warnings:
        response_parts.append(f"Warnings: {len(validation.warnings)} items to review")

    response_parts.append("User can export as PDF, Word, or Markdown from the artifacts list.")

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(response_parts)
        }],
        "event": event_data
    }
