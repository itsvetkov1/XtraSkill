---
phase: 28-test-infrastructure
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/analysis_options.yaml
  - frontend/coverage_report.sh
autonomous: true

must_haves:
  truths:
    - "Running flutter test --coverage generates lcov.info"
    - "Script converts lcov.info to HTML report"
    - "Coverage report shows line coverage percentages"
  artifacts:
    - path: "frontend/coverage_report.sh"
      provides: "Coverage HTML generation script"
      contains: "genhtml"
    - path: "frontend/analysis_options.yaml"
      provides: "Dart analysis configuration"
      contains: "linter"
  key_links:
    - from: "flutter test --coverage"
      to: "coverage/lcov.info"
      via: "flutter test runner"
      pattern: "lcov.info"
---

<objective>
Configure Flutter lcov for HTML coverage reports.

Purpose: Enable coverage measurement for frontend tests. Flutter generates lcov.info by default; we need a script to convert it to human-readable HTML.

Output: Running `flutter test --coverage` followed by coverage script produces HTML report.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@frontend/pubspec.yaml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create coverage report generation script</name>
  <files>frontend/coverage_report.sh</files>
  <action>
Create frontend/coverage_report.sh with cross-platform coverage HTML generation:

```bash
#!/bin/bash
# Coverage report generation script for Flutter
# Generates HTML coverage report from lcov.info
#
# Prerequisites:
#   - Linux/macOS: Install lcov (apt install lcov / brew install lcov)
#   - Windows: Use WSL or install lcov via chocolatey
#
# Usage:
#   ./coverage_report.sh        # Run tests and generate report
#   ./coverage_report.sh --skip-tests  # Generate report from existing lcov.info

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Flutter Coverage Report Generator${NC}"
echo "=================================="

# Check for genhtml
if ! command -v genhtml &> /dev/null; then
    echo -e "${RED}Error: genhtml not found${NC}"
    echo ""
    echo "Install lcov:"
    echo "  Ubuntu/Debian: sudo apt install lcov"
    echo "  macOS:         brew install lcov"
    echo "  Windows:       Use WSL or choco install lcov"
    exit 1
fi

# Run tests unless --skip-tests flag
if [[ "$1" != "--skip-tests" ]]; then
    echo -e "${YELLOW}Running Flutter tests with coverage...${NC}"
    flutter test --coverage
    echo ""
fi

# Check lcov.info exists
if [[ ! -f "coverage/lcov.info" ]]; then
    echo -e "${RED}Error: coverage/lcov.info not found${NC}"
    echo "Run 'flutter test --coverage' first"
    exit 1
fi

# Generate HTML report
echo -e "${YELLOW}Generating HTML report...${NC}"
genhtml coverage/lcov.info \
    --output-directory coverage/html \
    --title "BA Assistant Frontend Coverage" \
    --show-details \
    --highlight \
    --legend

echo ""
echo -e "${GREEN}Coverage report generated!${NC}"
echo "Open: coverage/html/index.html"

# Print summary
echo ""
echo "Summary:"
lcov --summary coverage/lcov.info 2>&1 | tail -3
```

Make the script executable (on Unix systems) by noting it needs chmod +x.
On Windows, this script runs via Git Bash or WSL.
  </action>
  <verify>File exists at frontend/coverage_report.sh with genhtml command</verify>
  <done>coverage_report.sh script created with lcov prerequisites documentation</done>
</task>

<task type="auto">
  <name>Task 2: Add coverage directory to gitignore</name>
  <files>frontend/.gitignore</files>
  <action>
Check if frontend/.gitignore exists. If it does, ensure these lines are present (add if missing):

```
# Coverage
coverage/
```

If frontend/.gitignore does not exist, create it with:

```
# Coverage reports
coverage/

# Generated files
*.g.dart
*.mocks.dart

# Build outputs
build/
.dart_tool/
```

This prevents committing generated coverage files and mocks.
  </action>
  <verify>frontend/.gitignore contains "coverage/" line</verify>
  <done>Coverage directory excluded from git</done>
</task>

<task type="auto">
  <name>Task 3: Document lcov setup in README</name>
  <files>frontend/README.md</files>
  <action>
Check if frontend/README.md exists. If not, create it. Add or update a "Testing" section:

```markdown
## Testing

### Running Tests

```bash
# Run all tests
flutter test

# Run tests with coverage
flutter test --coverage

# Run specific test file
flutter test test/unit/chats_provider_test.dart
```

### Coverage Reports

Generate HTML coverage reports:

```bash
# Prerequisites: Install lcov
# Ubuntu/Debian: sudo apt install lcov
# macOS: brew install lcov
# Windows: Use WSL or Git Bash with lcov

# Generate report (runs tests first)
./coverage_report.sh

# Generate report from existing lcov.info
./coverage_report.sh --skip-tests

# Open report
# Linux: xdg-open coverage/html/index.html
# macOS: open coverage/html/index.html
# Windows: start coverage/html/index.html
```
```

If README.md already exists with other content, append the Testing section at an appropriate location.
  </action>
  <verify>frontend/README.md contains "Testing" section with coverage instructions</verify>
  <done>README documents how to run tests and generate coverage reports</done>
</task>

</tasks>

<verification>
1. Script exists: `ls frontend/coverage_report.sh` succeeds
2. Gitignore updated: `grep "coverage/" frontend/.gitignore` shows coverage directory excluded
3. Documentation: `grep "coverage" frontend/README.md` shows coverage section exists
4. Optional (if lcov installed): Run `cd frontend && flutter test --coverage && ./coverage_report.sh --skip-tests` generates coverage/html/index.html
</verification>

<success_criteria>
- coverage_report.sh script exists with genhtml commands and prerequisite docs
- frontend/.gitignore excludes coverage/ directory
- frontend/README.md documents testing and coverage commands
- (If lcov available) HTML report generates successfully
</success_criteria>

<output>
After completion, create `.planning/phases/28-test-infrastructure/28-02-SUMMARY.md`
</output>
