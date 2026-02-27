"""
Skill Integration Tests.

Tests verify that the business-analyst skill behaviors work correctly:
1. Mode detection at session start
2. One-question-at-a-time protocol
3. Ambiguous term clarification
4. Technical discussion redirect
5. BRD generation follows template
6. Overall skill behavior validation

These are integration tests that verify skill loading and prompt behavior.
For actual AI response testing, use manual verification with real API calls.
"""
import pytest
import re
from app.services.skill_loader import load_skill_prompt, get_skill_references
from app.services.brd_generator import (
    validate_brd_content,
    format_preflight_checklist,
    BRD_REQUIRED_SECTIONS,
    BRD_SECTIONS
)


class TestSkillLoading:
    """Test skill content loading and structure."""

    def test_skill_prompt_loads_successfully(self):
        """Verify skill prompt loads without errors."""
        prompt = load_skill_prompt()
        assert prompt is not None
        assert len(prompt) > 1000  # Skill + references should be substantial

    def test_skill_prompt_contains_core_identity(self):
        """Verify skill prompt contains business-analyst identity."""
        prompt = load_skill_prompt()
        assert "business analyst" in prompt.lower()
        assert "brd" in prompt.lower() or "business requirements document" in prompt.lower()

    def test_skill_references_loaded(self):
        """Verify all reference files are loaded."""
        refs = get_skill_references()
        expected_refs = [
            "discovery-framework",
            "brd-template",
            "tone-guidelines",
            "error-protocols"
        ]
        for ref in expected_refs:
            assert ref in refs, f"Missing reference: {ref}"

    def test_skill_prompt_contains_references(self):
        """Verify combined prompt includes reference content."""
        prompt = load_skill_prompt()
        # Check for content from each reference file
        assert "discovery priority sequence" in prompt.lower()  # discovery-framework
        assert "executive summary" in prompt.lower()  # brd-template
        assert "consultative" in prompt.lower()  # tone-guidelines


class TestModeDetection:
    """Test mode detection behavior (Success Criteria #1)."""

    def test_skill_includes_mode_question(self):
        """Verify skill prompt contains mode detection question."""
        prompt = load_skill_prompt()
        # Should contain the mode question or its key elements
        assert "meeting mode" in prompt.lower() or "document refinement mode" in prompt.lower()

    def test_skill_includes_mode_options(self):
        """Verify skill prompt includes both mode options."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        # Check for both modes
        has_meeting = "meeting mode" in prompt_lower or "live discovery" in prompt_lower
        has_refinement = "document refinement" in prompt_lower or "modifying an existing" in prompt_lower
        assert has_meeting, "Missing Meeting Mode reference"
        assert has_refinement, "Missing Document Refinement Mode reference"


class TestOneQuestionProtocol:
    """Test one-question-at-a-time protocol (Success Criteria #2)."""

    def test_skill_mandates_one_question(self):
        """Verify skill prompt enforces one question at a time."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        # Should contain explicit mandate
        assert "one question at a time" in prompt_lower
        assert "never batch" in prompt_lower or "never combine" in prompt_lower or "never batch multiple" in prompt_lower

    def test_skill_includes_question_format(self):
        """Verify skill prompt includes question format requirements."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        # Should require rationale and options
        assert "rationale" in prompt_lower
        assert "suggested answer options" in prompt_lower or "three suggested" in prompt_lower or "3 answer options" in prompt_lower.replace("three", "3")

    def test_skill_includes_question_example(self):
        """Verify skill prompt includes example questions."""
        prompt = load_skill_prompt()
        # Should have example questions with options (A), (B), (C)
        has_options = "(a)" in prompt.lower() and "(b)" in prompt.lower() and "(c)" in prompt.lower()
        assert has_options, "Missing example question with A/B/C options"


class TestAmbiguityClarification:
    """Test ambiguous term clarification (Success Criteria #3)."""

    def test_skill_includes_zero_assumption_protocol(self):
        """Verify skill prompt includes zero-assumption protocol."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        assert "zero-assumption" in prompt_lower or "never assume" in prompt_lower

    def test_skill_lists_ambiguous_terms(self):
        """Verify skill prompt lists common ambiguous terms."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        ambiguous_terms = ["seamless", "intuitive", "scalable", "user-friendly"]
        found_terms = sum(1 for term in ambiguous_terms if term in prompt_lower)
        assert found_terms >= 2, f"Should list at least 2 ambiguous terms, found {found_terms}"

    def test_skill_includes_clarification_format(self):
        """Verify skill prompt includes clarification format."""
        prompt = load_skill_prompt()
        # Should include the clarification template
        assert "when you say" in prompt.lower()
        assert "do you mean" in prompt.lower()


class TestTechnicalRedirect:
    """Test technical discussion redirect (Success Criteria #4)."""

    def test_skill_includes_technical_boundary(self):
        """Verify skill prompt includes technical boundary enforcement."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        assert "technical" in prompt_lower
        assert "redirect" in prompt_lower or "boundary" in prompt_lower

    def test_skill_lists_technical_topics_to_avoid(self):
        """Verify skill prompt lists technical topics to avoid."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        technical_topics = ["react", "vue", "python", "java", "database", "api", "microservices", "architecture"]
        found_topics = sum(1 for topic in technical_topics if topic in prompt_lower)
        assert found_topics >= 3, f"Should list at least 3 technical topics to avoid, found {found_topics}"

    def test_skill_includes_redirect_template(self):
        """Verify skill prompt includes redirect response template."""
        prompt = load_skill_prompt()
        # Should include redirect phrase
        assert "technical team" in prompt.lower()
        assert "business perspective" in prompt.lower()


class TestBRDGeneration:
    """Test BRD generation follows template (Success Criteria #5)."""

    def test_brd_required_sections_defined(self):
        """Verify required BRD sections are defined."""
        assert len(BRD_REQUIRED_SECTIONS) >= 5
        assert "Executive Summary" in BRD_REQUIRED_SECTIONS
        assert "Business Objectives" in BRD_REQUIRED_SECTIONS
        assert "User Personas" in BRD_REQUIRED_SECTIONS

    def test_brd_validation_catches_missing_sections(self):
        """Verify BRD validation catches missing required sections."""
        incomplete_brd = """# Business Requirements Document
## Executive Summary
This is a summary.
"""
        result = validate_brd_content(incomplete_brd)
        assert not result.is_valid
        assert len(result.missing_sections) > 0
        assert "Business Objectives" in result.missing_sections or "User Personas" in result.missing_sections

    def test_brd_validation_accepts_complete_brd(self, sample_brd_content):
        """Verify BRD validation accepts complete BRD."""
        result = validate_brd_content(sample_brd_content)
        assert result.is_valid, f"Valid BRD rejected. Missing: {result.missing_sections}"
        assert result.section_count >= 5

    def test_brd_validation_warns_on_placeholders(self):
        """Verify BRD validation warns on placeholder text."""
        brd_with_placeholder = """# Business Requirements Document
## Executive Summary
[TBD]
## Business Objectives
### Primary Objective
[To be determined]
## User Personas
### Persona 1
[Insert persona details]
## Functional Requirements
[Add requirements]
## Success Metrics
[TODO]
"""
        result = validate_brd_content(brd_with_placeholder)
        assert len(result.warnings) > 0

    def test_brd_validation_warns_on_technical_terms(self):
        """Verify BRD validation warns on technical implementation terms."""
        brd_with_tech = """# Business Requirements Document
## Executive Summary
We will build this using React and PostgreSQL.
## Business Objectives
### Primary Objective
Deploy on AWS using Kubernetes.
## User Personas
### Persona 1
Developer using Python.
## Functional Requirements
Build a microservices API.
## Success Metrics
API response time under 200ms.
"""
        result = validate_brd_content(brd_with_tech)
        assert len(result.warnings) > 0
        # Should flag multiple technical terms
        warning_text = " ".join(result.warnings).lower()
        assert "react" in warning_text or "python" in warning_text or "aws" in warning_text

    def test_preflight_checklist_formatting(self):
        """Verify preflight checklist formats correctly."""
        # All passed
        passed, checklist = format_preflight_checklist(
            has_objective=True,
            has_personas=True,
            has_flows=True,
            has_metrics=True,
            has_requirements=True,
            has_stakeholders=True
        )
        assert passed
        assert "[x]" in checklist
        assert "[ ]" not in checklist

        # Some missing
        passed, checklist = format_preflight_checklist(
            has_objective=True,
            has_personas=False,
            has_flows=True,
            has_metrics=False,
            has_requirements=True,
            has_stakeholders=True
        )
        assert not passed
        assert "[ ]" in checklist


class TestSkillBehaviorValidation:
    """End-to-end skill behavior validation (Success Criteria #6)."""

    def test_skill_has_session_management(self):
        """Verify skill includes session management guidance."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        assert "session" in prompt_lower
        assert "context" in prompt_lower or "cumulative" in prompt_lower

    def test_skill_has_contradiction_detection(self):
        """Verify skill includes contradiction detection."""
        prompt = load_skill_prompt()
        assert "contradiction" in prompt.lower()

    def test_skill_has_understanding_verification(self):
        """Verify skill includes understanding verification."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        assert "verify" in prompt_lower or "verification" in prompt_lower
        assert "understanding" in prompt_lower

    def test_skill_has_professional_tone(self):
        """Verify skill includes professional tone guidance."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        assert "professional" in prompt_lower or "consultative" in prompt_lower
        assert "tone" in prompt_lower

    def test_skill_has_error_handling(self):
        """Verify skill includes error handling protocols."""
        prompt = load_skill_prompt()
        prompt_lower = prompt.lower()
        assert "error" in prompt_lower
        # Should have guidance for common issues
        has_customer_guidance = "cannot articulate" in prompt_lower or "unfamiliar" in prompt_lower
        has_incomplete_guidance = "incomplete" in prompt_lower
        assert has_customer_guidance or has_incomplete_guidance
