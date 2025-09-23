#!/bin/bash
# Continuous monitoring during widget system refactoring
# Run this in a separate terminal during all refactoring work

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear

echo "======================================"
echo "    WIDGET REFACTORING MONITOR"
echo "======================================"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    # Move cursor to line 7 to overwrite previous output
    tput cup 7 0

    # Clear from cursor to end of screen
    tput ed

    # Timestamp
    echo -e "${BLUE}Last Check:${NC} $(date '+%H:%M:%S')"
    echo ""

    # Check for syntax errors
    echo -e "${BLUE}🔍 Syntax Check:${NC}"
    SYNTAX_ERRORS=0
    for file in $(find packages/viloapp/src -name "*.py" -type f 2>/dev/null | head -20); do
        if ! python -m py_compile "$file" 2>/dev/null; then
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
        fi
    done

    if [ $SYNTAX_ERRORS -eq 0 ]; then
        echo -e "  ${GREEN}✅ No syntax errors${NC}"
    else
        echo -e "  ${RED}❌ $SYNTAX_ERRORS files with syntax errors${NC}"
    fi

    # Check for undefined variables (simplified check)
    echo -e "\n${BLUE}🔍 Common Issues:${NC}"

    # Check for widget_type references (should be widget_id)
    WT_COUNT=$(grep -r "widget_type" packages/viloapp/src --include="*.py" 2>/dev/null | grep -v "# OLD" | grep -v "migration" | wc -l)
    if [ $WT_COUNT -eq 0 ]; then
        echo -e "  ${GREEN}✅ No 'widget_type' references${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Found $WT_COUNT 'widget_type' references (should be widget_id)${NC}"
    fi

    # Check for WidgetType enum references
    ENUM_COUNT=$(grep -r "WidgetType\." packages/viloapp/src --include="*.py" 2>/dev/null | wc -l)
    if [ $ENUM_COUNT -eq 0 ]; then
        echo -e "  ${GREEN}✅ No WidgetType enum references${NC}"
    else
        echo -e "  ${RED}❌ Found $ENUM_COUNT WidgetType enum references${NC}"
    fi

    # Variable naming consistency
    echo -e "\n${BLUE}📊 Variable Consistency:${NC}"
    WI_COUNT=$(grep -r "\bwidget_id\b" packages/viloapp/src --include="*.py" 2>/dev/null | wc -l)
    echo -e "  widget_id: $WI_COUNT occurrences"

    # Check for hardcoded widget IDs in wrong places
    echo -e "\n${BLUE}🔍 Hardcoded Widget IDs:${NC}"
    HARDCODED=$(grep -r '"com\.viloapp\.\(terminal\|editor\|settings\)"' \
                packages/viloapp/src/viloapp/core --include="*.py" 2>/dev/null | \
                grep -v "registry" | grep -v "metadata" | grep -v "default" | \
                grep -v "fallback" | grep -v "placeholder" | wc -l)

    if [ $HARDCODED -eq 0 ]; then
        echo -e "  ${GREEN}✅ No problematic hardcoded IDs${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Found $HARDCODED potentially hardcoded IDs${NC}"
    fi

    # Quick baseline test
    echo -e "\n${BLUE}🧪 Baseline Tests:${NC}"
    if python test_widget_system_baseline.py > /tmp/baseline_test.log 2>&1; then
        echo -e "  ${GREEN}✅ All baseline tests pass${NC}"
    else
        echo -e "  ${RED}❌ BASELINE TESTS FAILING${NC}"
        echo "  Check /tmp/baseline_test.log for details"
    fi

    # Git status summary
    echo -e "\n${BLUE}📝 Git Status:${NC}"
    MODIFIED=$(git status --porcelain | grep "^ M" | wc -l)
    ADDED=$(git status --porcelain | grep "^A" | wc -l)
    UNTRACKED=$(git status --porcelain | grep "^??" | wc -l)
    echo -e "  Modified: $MODIFIED | Added: $ADDED | Untracked: $UNTRACKED"

    # Current branch
    BRANCH=$(git branch --show-current)
    echo -e "  Branch: ${YELLOW}$BRANCH${NC}"

    # Last commit
    echo -e "\n${BLUE}📌 Last Commit:${NC}"
    git log --oneline -1 | sed 's/^/  /'

    # Phase tracking
    echo -e "\n${BLUE}📋 Current Phase:${NC}"
    if [ -f "docs/widget-system-refactor-WIP.md" ]; then
        PHASE=$(grep "Current Phase:" docs/widget-system-refactor-WIP.md | sed 's/.*Current Phase: //' | head -1)
        echo -e "  $PHASE"
    else
        echo -e "  ${YELLOW}WIP document not found${NC}"
    fi

    sleep 3
done