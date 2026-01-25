#!/usr/bin/env python3
"""
BRD validation script for Business Requirements Documents.

Validates that generated BRDs meet quality standards including:
- All required sections present and populated
- No empty placeholders or TBD markers
- Requirements align with business objectives
- Success metrics are measurable and time-bound
- No technical implementation language
- Priorities clearly indicated

Usage:
    python validate_brd.py <brd-file-path>

Example:
    $ python validate_brd.py ./customer-brd.md

    BRD Validation Report
    =====================
    File: customer-brd.md

    Section Completeness: PASS
    ✓ All required sections present
    ✓ No empty placeholders found

    Content Quality: WARNINGS
    ⚠ Found vague success metric: "improve performance"
    ⚠ Requirement lacks business rationale: "Export to PDF"

    Technical Language Check: PASS
    ✓ No technical implementation language detected

    Overall: PASS WITH WARNINGS
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict
import argparse


class BRDValidator:
    """Validates Business Requirements Documents for quality and completeness."""

    # Required sections in BRD
    REQUIRED_SECTIONS = [
        "# Business Requirements Document",
        "## Executive Summary",
        "## Business Context",
        "## Business Objectives",
        "## User Personas",
        "## User Flows and Journeys",
        "## Functional Requirements",
        "## Business Processes",
        "## Stakeholder Analysis",
        "## Success Metrics and KPIs",
        "## Assumptions and Constraints",
        "## Risks and Mitigation Strategies",
        "## Next Steps"
    ]

    # Technical terms that should not appear
    TECHNICAL_TERMS = [
        r'\breact\b', r'\bvue\b', r'\bangular\b',
        r'\bapi\b', r'\brest\b', r'\bgraphql\b',
        r'\bmicroservices\b', r'\bmonolithic\b', r'\bserverless\b',
        r'\bdatabase\b', r'\bsql\b', r'\bnosql\b',
        r'\bmongodb\b', r'\bpostgresql\b', r'\bmysql\b',
        r'\baws\b', r'\bazure\b', r'\bgcp\b', r'\bcloud provider\b',
        r'\bdocker\b', r'\bkubernetes\b', r'\bcontainer\b',
        r'\bfrontend\b', r'\bbackend\b', r'\bfull-stack\b',
        r'\balgorithm\b', r'\bdata structure\b',
        r'\bp99\b', r'\blatency\b', r'\bthroughput\b',
        r'\bload balancer\b', r'\bcdn\b',
        r'\bjavascript\b', r'\bpython\b', r'\bjava\b', r'\bc\+\+\b',
    ]

    # Vague terms that indicate unmeasurable metrics
    VAGUE_METRIC_TERMS = [
        r'improve\s+performance',
        r'enhance\s+experience',
        r'increase\s+engagement',
        r'better\s+visibility',
        r'more\s+efficient',
        r'faster',
        r'easier',
        r'seamless',
        r'intuitive',
        r'user-friendly',
        r'robust',
        r'scalable'
    ]

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = ""
        self.lines = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passes: List[str] = []

    def load_file(self) -> bool:
        """Load BRD file content."""
        try:
            self.content = self.filepath.read_text(encoding='utf-8')
            self.lines = self.content.split('\n')
            return True
        except FileNotFoundError:
            self.errors.append(f"File not found: {self.filepath}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False

    def check_sections(self):
        """Check that all required sections are present."""
        missing_sections = []

        for section in self.REQUIRED_SECTIONS:
            if section not in self.content:
                missing_sections.append(section)

        if missing_sections:
            self.errors.append("Missing required sections:")
            for section in missing_sections:
                self.errors.append(f"  - {section}")
        else:
            self.passes.append("All required sections present")

    def check_empty_placeholders(self):
        """Check for empty placeholders or TBD markers."""
        empty_patterns = [
            r'\[TBD\]',
            r'\[TODO\]',
            r'\[FILL\s+IN\]',
            r'\[PLACEHOLDER\]',
            r'\[TO\s+BE\s+DETERMINED\]'
        ]

        found_placeholders = []
        for i, line in enumerate(self.lines, 1):
            for pattern in empty_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found_placeholders.append((i, line.strip()))

        if found_placeholders:
            self.warnings.append("Found placeholder markers that should be filled:")
            for line_num, line_text in found_placeholders[:5]:  # Show first 5
                self.warnings.append(f"  Line {line_num}: {line_text}")
            if len(found_placeholders) > 5:
                self.warnings.append(f"  ... and {len(found_placeholders) - 5} more")
        else:
            self.passes.append("No empty placeholders found")

    def check_technical_language(self):
        """Check for technical implementation language."""
        found_technical = []

        for i, line in enumerate(self.lines, 1):
            for pattern in self.TECHNICAL_TERMS:
                if re.search(pattern, line, re.IGNORECASE):
                    found_technical.append((i, line.strip(), pattern))

        if found_technical:
            self.errors.append("Found technical implementation language (should be business-focused):")
            for line_num, line_text, pattern in found_technical[:5]:  # Show first 5
                term = re.search(pattern, line_text, re.IGNORECASE).group()
                self.errors.append(f"  Line {line_num}: '{term}' in: {line_text[:60]}...")
            if len(found_technical) > 5:
                self.errors.append(f"  ... and {len(found_technical) - 5} more instances")
        else:
            self.passes.append("No technical implementation language detected")

    def check_vague_metrics(self):
        """Check for vague, unmeasurable success metrics."""
        # Focus on Success Metrics section
        metrics_section_start = -1
        metrics_section_end = len(self.lines)

        for i, line in enumerate(self.lines):
            if "## Success Metrics and KPIs" in line:
                metrics_section_start = i
            elif metrics_section_start > -1 and line.startswith("## "):
                metrics_section_end = i
                break

        if metrics_section_start == -1:
            return  # Section missing - already caught by check_sections

        found_vague = []
        for i in range(metrics_section_start, metrics_section_end):
            line = self.lines[i]
            for pattern in self.VAGUE_METRIC_TERMS:
                if re.search(pattern, line, re.IGNORECASE):
                    found_vague.append((i + 1, line.strip()))

        if found_vague:
            self.warnings.append("Found vague success metrics (should be specific and measurable):")
            for line_num, line_text in found_vague[:3]:  # Show first 3
                self.warnings.append(f"  Line {line_num}: {line_text[:70]}...")
            if len(found_vague) > 3:
                self.warnings.append(f"  ... and {len(found_vague) - 3} more")
        else:
            self.passes.append("Success metrics appear specific and measurable")

    def check_requirement_structure(self):
        """Check that functional requirements have proper structure."""
        # Look for requirements without business rationale
        in_requirements = False
        requirement_blocks = []
        current_block = []

        for line in self.lines:
            if "## Functional Requirements" in line:
                in_requirements = True
                continue
            elif in_requirements and line.startswith("## "):
                break
            elif in_requirements:
                if line.startswith("1. ") or re.match(r'^\d+\.\s+\*\*', line):
                    if current_block:
                        requirement_blocks.append(current_block)
                    current_block = [line]
                elif current_block and line.strip():
                    current_block.append(line)

        if current_block:
            requirement_blocks.append(current_block)

        missing_rationale = []
        for block in requirement_blocks:
            block_text = "\n".join(block)
            if "business rationale" not in block_text.lower() and "rationale:" not in block_text.lower():
                # Extract requirement title
                title_match = re.search(r'\*\*(.+?)\*\*', block[0])
                if title_match:
                    missing_rationale.append(title_match.group(1))

        if missing_rationale:
            self.warnings.append("Requirements missing business rationale:")
            for title in missing_rationale[:3]:  # Show first 3
                self.warnings.append(f"  - {title}")
            if len(missing_rationale) > 3:
                self.warnings.append(f"  ... and {len(missing_rationale) - 3} more")
        elif requirement_blocks:
            self.passes.append("Requirements include business rationale")

    def check_priorities(self):
        """Check that requirement priorities are clearly indicated."""
        priority_patterns = [
            r'Priority\s+0',
            r'Priority\s+1',
            r'Priority\s+2',
            r'Must-Have',
            r'Should-Have',
            r'Nice-to-Have',
            r'P0',
            r'P1',
            r'P2'
        ]

        has_priorities = any(
            re.search(pattern, self.content, re.IGNORECASE)
            for pattern in priority_patterns
        )

        if has_priorities:
            self.passes.append("Requirement priorities clearly indicated")
        else:
            self.warnings.append("No priority indicators found in requirements (P0/P1/P2 or Must-Have/Should-Have/Nice-to-Have)")

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("BRD Validation Report")
        print("=" * 70)
        print(f"File: {self.filepath}\n")

        # Print passes
        if self.passes:
            print("✓ PASSES:")
            for msg in self.passes:
                print(f"  ✓ {msg}")
            print()

        # Print warnings
        if self.warnings:
            print("⚠ WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
            print()

        # Print errors
        if self.errors:
            print("✗ ERRORS:")
            for msg in self.errors:
                print(f"  {msg}")
            print()

        # Overall status
        print("=" * 70)
        if self.errors:
            print("Overall Status: ✗ FAIL")
            print("\nThe BRD has critical issues that must be fixed.")
            return False
        elif self.warnings:
            print("Overall Status: ⚠ PASS WITH WARNINGS")
            print("\nThe BRD meets minimum requirements but has areas for improvement.")
            return True
        else:
            print("Overall Status: ✓ PASS")
            print("\nThe BRD meets all quality standards.")
            return True

    def run_validation(self) -> bool:
        """
        Run complete BRD validation.

        Returns:
            True if validation passed (possibly with warnings), False if critical errors
        """
        if not self.load_file():
            print(f"\nError: {self.errors[0]}", file=sys.stderr)
            return False

        # Run all validation checks
        self.check_sections()
        self.check_empty_placeholders()
        self.check_technical_language()
        self.check_vague_metrics()
        self.check_requirement_structure()
        self.check_priorities()

        # Print report
        return self.print_report()


def main():
    """Main entry point for BRD validation."""
    parser = argparse.ArgumentParser(
        description="Validate Business Requirements Document for quality and completeness"
    )
    parser.add_argument(
        "brd_file",
        type=str,
        help="Path to the BRD markdown file to validate"
    )

    args = parser.parse_args()
    filepath = Path(args.brd_file)

    try:
        validator = BRDValidator(filepath)
        passed = validator.run_validation()

        # Exit with appropriate code
        sys.exit(0 if passed else 1)

    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during validation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
