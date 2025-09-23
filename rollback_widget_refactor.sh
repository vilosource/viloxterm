#!/bin/bash
# Emergency rollback script for widget refactoring
# Use this if refactoring causes critical issues

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================"
echo "  Widget Refactoring Rollback Tool"
echo "======================================"
echo ""

# Show available checkpoints
echo -e "${BLUE}Available Checkpoints:${NC}"
git tag -l "checkpoint-*" | sort -r | while read tag; do
    COMMIT=$(git rev-list -n 1 $tag)
    DATE=$(git log -1 --format=%ci $tag)
    MESSAGE=$(git log -1 --format=%s $tag)
    echo -e "  ${GREEN}$tag${NC}"
    echo -e "    Date: $DATE"
    echo -e "    Message: $MESSAGE"
    echo ""
done

# Show current state
echo -e "${BLUE}Current State:${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo -e "  Branch: ${YELLOW}$CURRENT_BRANCH${NC}"
echo -e "  HEAD: $(git log --oneline -1)"

# Check for uncommitted changes
CHANGES=$(git status --porcelain | wc -l)
if [ $CHANGES -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Warning: You have $CHANGES uncommitted changes${NC}"
    echo "  These will be lost if you rollback!"
fi

echo ""
echo "======================================"
echo ""
echo -e "${BLUE}Rollback Options:${NC}"
echo "  1. Soft rollback (keep changes as uncommitted)"
echo "  2. Hard rollback (discard all changes)"
echo "  3. Create backup branch before rollback"
echo "  4. Exit without changes"
echo ""

read -p "Select option (1-4): " option

case $option in
    1)
        # Soft rollback
        echo ""
        read -p "Enter checkpoint name to rollback to: " checkpoint
        if git tag -l | grep -q "^$checkpoint$"; then
            echo -e "${YELLOW}Performing soft rollback to $checkpoint...${NC}"
            git reset --soft $checkpoint
            echo -e "${GREEN}✅ Soft rollback complete${NC}"
            echo "  Changes are preserved as uncommitted"
        else
            echo -e "${RED}❌ Checkpoint '$checkpoint' not found${NC}"
            exit 1
        fi
        ;;

    2)
        # Hard rollback
        echo ""
        read -p "Enter checkpoint name to rollback to: " checkpoint
        if git tag -l | grep -q "^$checkpoint$"; then
            echo -e "${RED}⚠️  This will DISCARD all changes since $checkpoint${NC}"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                echo -e "${YELLOW}Performing hard rollback to $checkpoint...${NC}"
                git reset --hard $checkpoint
                echo -e "${GREEN}✅ Hard rollback complete${NC}"
            else
                echo "Rollback cancelled"
            fi
        else
            echo -e "${RED}❌ Checkpoint '$checkpoint' not found${NC}"
            exit 1
        fi
        ;;

    3)
        # Backup and rollback
        echo ""
        BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
        echo -e "${YELLOW}Creating backup branch: $BACKUP_BRANCH${NC}"
        git branch $BACKUP_BRANCH
        echo -e "${GREEN}✅ Backup created${NC}"

        read -p "Enter checkpoint name to rollback to: " checkpoint
        if git tag -l | grep -q "^$checkpoint$"; then
            echo -e "${YELLOW}Performing hard rollback to $checkpoint...${NC}"
            git reset --hard $checkpoint
            echo -e "${GREEN}✅ Rollback complete${NC}"
            echo "  Your previous work is saved in branch: $BACKUP_BRANCH"
        else
            echo -e "${RED}❌ Checkpoint '$checkpoint' not found${NC}"
            exit 1
        fi
        ;;

    4)
        echo "No changes made"
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo -e "${BLUE}Post-Rollback Status:${NC}"
echo "  Branch: $(git branch --show-current)"
echo "  HEAD: $(git log --oneline -1)"
echo "  Uncommitted changes: $(git status --porcelain | wc -l)"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Run baseline tests: python test_widget_system_baseline.py"
echo "  2. Test app startup: python packages/viloapp/src/viloapp/main.py"
echo "  3. Review changes: git diff"
echo "======================================"