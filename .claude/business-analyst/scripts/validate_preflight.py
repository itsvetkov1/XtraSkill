#!/usr/bin/env python3
"""
Pre-flight validation script for Business Requirements Document generation.

Checks if critical information has been captured before generating BRD.
Provides actionable feedback on missing or incomplete areas.

Usage:
    python validate_preflight.py

The script will interactively ask about discovery completeness and provide
a validation report indicating readiness for BRD generation.

Example:
    $ python validate_preflight.py

    Business Requirements Pre-Flight Validation
    ===========================================

    This script checks if you have gathered sufficient information to generate
    a comprehensive Business Requirements Document.

    Answer the following questions based on your discovery conversation:

    [Interactive prompts follow]
"""

import sys
from typing import Dict, List, Tuple


class PreFlightValidator:
    """Validates completeness of requirements discovery before BRD generation."""

    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.missing_areas: List[str] = []
        self.recommendations: List[str] = []

    def print_header(self):
        """Print validation header."""
        print("\n" + "=" * 70)
        print("Business Requirements Pre-Flight Validation")
        print("=" * 70)
        print("\nThis script checks if you have gathered sufficient information")
        print("to generate a comprehensive Business Requirements Document.\n")

    def ask_yes_no(self, question: str, area_name: str) -> bool:
        """
        Ask a yes/no question and record result.

        Args:
            question: The question to ask
            area_name: Name of the requirement area being checked

        Returns:
            True if answered yes, False otherwise
        """
        while True:
            response = input(f"\n{question} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                self.results[area_name] = True
                return True
            elif response in ['n', 'no']:
                self.results[area_name] = False
                self.missing_areas.append(area_name)
                return False
            else:
                print("Please answer 'y' for yes or 'n' for no.")

    def check_business_objective(self) -> bool:
        """Check if primary business objective is clearly defined."""
        return self.ask_yes_no(
            "1. Do you have a CLEARLY DEFINED primary business objective with measurable success criteria?",
            "Business Objective"
        )

    def check_user_personas(self) -> bool:
        """Check if user personas are identified with sufficient detail."""
        return self.ask_yes_no(
            "2. Have you identified AT LEAST 2 user personas with sufficient detail (role, pain points, goals)?",
            "User Personas"
        )

    def check_functional_requirements(self) -> bool:
        """Check if core functional requirements are captured."""
        return self.ask_yes_no(
            "3. Have you captured MINIMUM 3 core functional requirements with business rationale?",
            "Functional Requirements"
        )

    def check_user_flows(self) -> bool:
        """Check if user flows are documented."""
        return self.ask_yes_no(
            "4. Have you documented AT LEAST 1 complete user flow end-to-end?",
            "User Flows"
        )

    def check_success_metrics(self) -> bool:
        """Check if success metrics are defined."""
        return self.ask_yes_no(
            "5. Have you defined success metrics (MINIMUM 2 KPIs with baselines and target values)?",
            "Success Metrics"
        )

    def check_stakeholders(self) -> bool:
        """Check if stakeholders are identified."""
        return self.ask_yes_no(
            "6. Have you identified key stakeholders (even if with limited detail initially)?",
            "Stakeholders"
        )

    def check_compliance(self) -> bool:
        """Check if regulatory/compliance needs are noted."""
        return self.ask_yes_no(
            "7. Have you asked about regulatory/compliance needs (even if answer is 'none')?",
            "Regulatory/Compliance"
        )

    def generate_recommendations(self):
        """Generate recommendations based on missing areas."""
        if not self.missing_areas:
            return

        print("\n" + "-" * 70)
        print("RECOMMENDATIONS - Missing Information")
        print("-" * 70)

        recommendations_map = {
            "Business Objective":
                "Ask: 'What is the primary business objective this product must achieve? "
                "How will you measure success?'",

            "User Personas":
                "Ask: 'Who are the primary users? What are their roles, current pain points, "
                "and goals they want to achieve?'",

            "Functional Requirements":
                "Ask: 'What are the must-have capabilities this product needs? Why does each "
                "capability matter to your business objectives?'",

            "User Flows":
                "Ask: 'Walk me through the most critical workflow users need to complete, "
                "step by step from start to finish.'",

            "Success Metrics":
                "Ask: 'What specific metrics will demonstrate this product's success? "
                "What are current baseline values and target values?'",

            "Stakeholders":
                "Ask: 'Beyond direct users, who else has a stake in this product's success? "
                "What do they need from it?'",

            "Regulatory/Compliance":
                "Ask: 'Are there any regulatory, compliance, or legal requirements this "
                "product must meet (GDPR, HIPAA, industry-specific regulations)?'"
        }

        for area in self.missing_areas:
            if area in recommendations_map:
                print(f"\n{area}:")
                print(f"  {recommendations_map[area]}")

    def print_summary(self) -> bool:
        """
        Print validation summary and return readiness status.

        Returns:
            True if ready for BRD generation, False otherwise
        """
        total_checks = len(self.results)
        passed_checks = sum(1 for v in self.results.values() if v)

        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)

        print(f"\nChecks Passed: {passed_checks}/{total_checks}")

        # Determine readiness
        critical_areas = ["Business Objective", "User Personas", "Functional Requirements"]
        missing_critical = [area for area in critical_areas if area in self.missing_areas]

        if not self.missing_areas:
            print("\nStatus: ✓ READY FOR BRD GENERATION")
            print("\nAll essential information has been captured.")
            print("You can proceed with generating the Business Requirements Document.")
            return True

        elif missing_critical:
            print("\nStatus: ✗ NOT READY - Critical Information Missing")
            print("\nThe following CRITICAL areas are incomplete:")
            for area in missing_critical:
                print(f"  - {area}")
            print("\nYou MUST gather this information before generating the BRD.")
            self.generate_recommendations()
            return False

        else:
            print("\nStatus: ⚠ READY WITH ASSUMPTIONS")
            print("\nYou can generate the BRD, but the following areas are incomplete:")
            for area in self.missing_areas:
                print(f"  - {area}")
            print("\nRecommendation: Document these as assumptions in the BRD and")
            print("note that they should be validated with the customer before")
            print("finalizing your proposal.")
            self.generate_recommendations()
            return True

    def run_validation(self) -> bool:
        """
        Run complete pre-flight validation.

        Returns:
            True if ready for BRD generation (possibly with assumptions),
            False if critical information is missing
        """
        self.print_header()

        print("Answer the following questions based on your discovery conversation:\n")

        # Run all checks
        self.check_business_objective()
        self.check_user_personas()
        self.check_functional_requirements()
        self.check_user_flows()
        self.check_success_metrics()
        self.check_stakeholders()
        self.check_compliance()

        # Print summary and recommendations
        return self.print_summary()


def main():
    """Main entry point for pre-flight validation."""
    try:
        validator = PreFlightValidator()
        ready = validator.run_validation()

        # Exit with appropriate code
        sys.exit(0 if ready else 1)

    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during validation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
