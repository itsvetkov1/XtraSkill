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
