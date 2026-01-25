#!/usr/bin/env python3
"""
BRD structure validation script.

Validates markdown structure and formatting of Business Requirements Documents:
- Proper heading hierarchy (no skipped levels)
- Tables are properly formatted
- Lists use consistent formatting
- No malformed markdown

Usage:
    python validate_structure.py <brd-file-path>

Example:
    $ python validate_structure.py ./customer-brd.md

    BRD Structure Validation Report
    ================================
    File: customer-brd.md

    Heading Hierarchy: PASS
    ✓ No skipped heading levels

    Table Formatting: PASS
    ✓ All tables properly formatted

    List Formatting: WARNINGS
    ⚠ Inconsistent list markers at line 45 (use - or * consistently)

    Overall: PASS WITH WARNINGS
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple
import argparse


class StructureValidator:
    """Validates markdown structure and formatting of BRDs."""

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

    def check_heading_hierarchy(self):
        """Check that heading hierarchy is proper (no skipped levels)."""
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        headings = []

        for i, line in enumerate(self.lines, 1):
            match = heading_pattern.match(line)
            if match:
                level = len(match.group(1))
                text = match.group(2)
                headings.append((i, level, text))

        if not headings:
            self.warnings.append("No headings found in document")
            return

        # Check for skipped levels
        issues = []
        prev_level = 0

        for line_num, level, text in headings:
            if level > prev_level + 1 and prev_level > 0:
                issues.append(f"Line {line_num}: Skipped from h{prev_level} to h{level}: '{text}'")
            prev_level = level

        if issues:
            self.warnings.append("Heading hierarchy issues (skipped levels):")
            for issue in issues[:5]:
                self.warnings.append(f"  {issue}")
            if len(issues) > 5:
                self.warnings.append(f"  ... and {len(issues) - 5} more")
        else:
            self.passes.append("Heading hierarchy is correct (no skipped levels)")

    def check_table_formatting(self):
        """Check that markdown tables are properly formatted."""
        in_table = False
        table_start = -1
        table_issues = []

        for i, line in enumerate(self.lines, 1):
            # Detect table start (line with pipes)
            if '|' in line and not in_table:
                in_table = True
                table_start = i
                columns = line.count('|') - 1

            elif in_table:
                if '|' in line:
                    # Check if number of columns matches
                    current_columns = line.count('|') - 1
                    if current_columns != columns:
                        table_issues.append(f"Line {i}: Column count mismatch in table starting at line {table_start}")
                else:
                    # End of table
                    in_table = False

        if table_issues:
            self.warnings.append("Table formatting issues:")
            for issue in table_issues[:3]:
                self.warnings.append(f"  {issue}")
            if len(table_issues) > 3:
                self.warnings.append(f"  ... and {len(table_issues) - 3} more")
        else:
            # Check if there are any tables
            has_tables = any('|' in line for line in self.lines)
            if has_tables:
                self.passes.append("All tables properly formatted")

    def check_list_formatting(self):
        """Check for consistent list marker usage."""
        unordered_markers = []

        for i, line in enumerate(self.lines, 1):
            # Check for unordered list markers
            if re.match(r'^\s*[-*+]\s+', line):
                marker = re.match(r'^\s*([-*+])', line).group(1)
                unordered_markers.append((i, marker))

        if unordered_markers:
            # Check for mixing of markers
            markers_used = set(marker for _, marker in unordered_markers)
            if len(markers_used) > 1:
                self.warnings.append(f"Inconsistent list markers used: {', '.join(markers_used)}")
                self.warnings.append("  Recommendation: Use '-' consistently for all unordered lists")
            else:
                self.passes.append("Consistent list marker usage")

    def check_empty_sections(self):
        """Check for section headings followed immediately by another heading (empty sections)."""
        heading_pattern = re.compile(r'^#{1,6}\s+(.+)$')
        empty_sections = []

        prev_heading = None
        prev_heading_line = -1

        for i, line in enumerate(self.lines):
            if heading_pattern.match(line):
                if prev_heading and i - prev_heading_line == 1:
                    # Heading immediately follows another heading
                    empty_sections.append((prev_heading_line + 1, prev_heading))
                prev_heading = line.strip()
                prev_heading_line = i
            elif line.strip() and prev_heading:
                # Non-empty content after heading
                prev_heading = None

        if empty_sections:
            self.warnings.append("Empty sections (heading with no content):")
            for line_num, heading in empty_sections[:5]:
                self.warnings.append(f"  Line {line_num}: {heading}")
            if len(empty_sections) > 5:
                self.warnings.append(f"  ... and {len(empty_sections) - 5} more")
        else:
            self.passes.append("No empty sections found")

    def check_line_length(self):
        """Check for excessively long lines (>120 chars) that should be wrapped."""
        long_lines = []

        for i, line in enumerate(self.lines, 1):
            # Skip table rows, code blocks, and headings
            if line.startswith('|') or line.startswith('#') or line.startswith('```'):
                continue

            if len(line) > 120:
                long_lines.append((i, len(line)))

        if long_lines:
            self.warnings.append(f"Found {len(long_lines)} lines longer than 120 characters:")
            for line_num, length in long_lines[:3]:
                self.warnings.append(f"  Line {line_num}: {length} characters")
            if len(long_lines) > 3:
                self.warnings.append(f"  ... and {len(long_lines) - 3} more")
            self.warnings.append("  Recommendation: Wrap long lines for better readability")

    def check_multiple_blank_lines(self):
        """Check for multiple consecutive blank lines."""
        multiple_blanks = []
        blank_count = 0
        blank_start = -1

        for i, line in enumerate(self.lines, 1):
            if not line.strip():
                if blank_count == 0:
                    blank_start = i
                blank_count += 1
            else:
                if blank_count > 2:
                    multiple_blanks.append((blank_start, blank_count))
                blank_count = 0

        if multiple_blanks:
            self.warnings.append("Multiple consecutive blank lines:")
            for line_num, count in multiple_blanks[:5]:
                self.warnings.append(f"  Line {line_num}: {count} blank lines")
            if len(multiple_blanks) > 5:
                self.warnings.append(f"  ... and {len(multiple_blanks) - 5} more occurrences")
            self.warnings.append("  Recommendation: Use single blank lines for spacing")

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("BRD Structure Validation Report")
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
            print("\nThe BRD has structural issues that should be fixed.")
            return False
        elif self.warnings:
            print("Overall Status: ⚠ PASS WITH WARNINGS")
            print("\nThe BRD structure is acceptable but could be improved.")
            return True
        else:
            print("Overall Status: ✓ PASS")
            print("\nThe BRD structure is well-formatted.")
            return True

    def run_validation(self) -> bool:
        """
        Run complete structure validation.

        Returns:
            True if validation passed (possibly with warnings), False if critical errors
        """
        if not self.load_file():
            print(f"\nError: {self.errors[0]}", file=sys.stderr)
            return False

        # Run all validation checks
        self.check_heading_hierarchy()
        self.check_table_formatting()
        self.check_list_formatting()
        self.check_empty_sections()
        self.check_line_length()
        self.check_multiple_blank_lines()

        # Print report
        return self.print_report()


def main():
    """Main entry point for structure validation."""
    parser = argparse.ArgumentParser(
        description="Validate markdown structure and formatting of Business Requirements Document"
    )
    parser.add_argument(
        "brd_file",
        type=str,
        help="Path to the BRD markdown file to validate"
    )

    args = parser.parse_args()
    filepath = Path(args.brd_file)

    try:
        validator = StructureValidator(filepath)
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
