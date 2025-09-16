#!/bin/bash

# Architecture Compliance Checker
# Runs all architecture tests and provides clear CI/CD integration

set -e  # Exit on first error

PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}ViloxTerm Architecture Compliance Check${NC}"
echo "========================================"

# Check if python environment is available
if [ ! -f ".direnv/python-3.12.3/bin/python" ]; then
    echo -e "${RED}ERROR: Python environment not found. Run 'direnv allow' first.${NC}"
    exit 1
fi

PYTHON=".direnv/python-3.12.3/bin/python"
FAILED_TESTS=0
TOTAL_TESTS=4

echo ""
echo -e "${BLUE}Running Architecture Compliance Tests...${NC}"
echo ""

# Function to run a test and capture result
run_test() {
    local test_file=$1
    local test_name=$2
    local priority=$3

    echo -n "  ${test_name}... "

    if $PYTHON -m pytest "tests/architecture/${test_file}" -q --tb=no > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        return 0
    else
        echo -e "${RED}FAIL${NC} (${priority} priority)"
        return 1
    fi
}

# Run individual tests
echo "1. ServiceLocator Compliance"
if ! run_test "test_no_service_locator_in_ui.py" "No ServiceLocator in UI" "HIGH"; then
    ((FAILED_TESTS++))
fi

echo ""
echo "2. Exception Handling"
if ! run_test "test_no_bare_exceptions.py" "No Bare Exception Handlers" "HIGH"; then
    ((FAILED_TESTS++))
fi

echo ""
echo "3. File Size Limits"
if ! run_test "test_file_size_limits.py" "File Size Compliance" "MEDIUM"; then
    ((FAILED_TESTS++))
fi

echo ""
echo "4. Command Pattern"
if ! run_test "test_command_pattern_compliance.py" "Command Pattern Compliance" "HIGH"; then
    ((FAILED_TESTS++))
fi

echo ""
echo "========================================"

# Summary
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ All architecture tests passed!${NC}"
    echo ""
    echo "The codebase follows all architectural principles."
    exit 0
elif [ $FAILED_TESTS -le 2 ]; then
    echo -e "${YELLOW}⚠️  ${FAILED_TESTS}/${TOTAL_TESTS} tests failed (warnings only)${NC}"
    echo ""
    echo "Some architectural improvements needed but not blocking."

    # If we want to be strict in CI, uncomment the next line:
    # exit 1

    exit 0
else
    echo -e "${RED}❌ ${FAILED_TESTS}/${TOTAL_TESTS} tests failed (critical issues)${NC}"
    echo ""
    echo "Critical architectural violations found!"
    echo ""
    echo -e "${BLUE}To see detailed violations:${NC}"
    echo "  $PYTHON -m pytest tests/architecture/ -v"
    echo ""
    echo -e "${BLUE}To fix high priority issues:${NC}"
    echo "  1. Replace bare 'except:' with specific exception types"
    echo "  2. Add missing @command decorators to command functions"
    echo "  3. Ensure commands return CommandResult objects"
    echo ""
    exit 1
fi