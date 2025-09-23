# Widget System Refactor - Detailed Task List

## How to Use This Document

1. **Check off tasks** as you complete them
2. **Run verification** after EVERY task
3. **Commit after** each task with message format: `refactor(widget): [Phase X.Y] Description`
4. **If verification fails**, DO NOT proceed - fix immediately
5. **Update WIP document** after completing each phase

---

## Phase 1: Preparation and Verification Setup

### Task 1.1: Commit Current Changes ⬜
**Time**: 15 minutes
**Dependencies**: None

#### Steps:
1. Review all modified files
```bash
git status
git diff
```

2. Run baseline tests
```bash
python test_workspace_command_fix.py  # Should pass
python test_comprehensive_widget_system.py  # Should pass
```

3. Commit with detailed message
```bash
git add -A
git commit -m "feat: Complete widget defaults system with registry-based discovery

- Removed all hardcoded widget IDs from core
- Implemented registry-based default discovery
- Added user preference support
- Fixed workspace commands undefined variable bug
- Updated architecture documentation with refactoring process

Closes: #XXX"
```

4. Create checkpoint tag
```bash
git tag checkpoint-widget-defaults
git push origin checkpoint-widget-defaults
```

#### Verification:
- [ ] Git status is clean
- [ ] All current tests pass
- [ ] Tag created successfully

#### North Star Check:
- [ ] No new hardcoded widget IDs introduced
- [ ] All changes follow one-way data flow

---

### Task 1.2: Create Feature Branch ⬜
**Time**: 5 minutes
**Dependencies**: Task 1.1

#### Steps:
1. Create and checkout feature branch
```bash
git checkout -b feature/widget-system-complete
git push -u origin feature/widget-system-complete
```

2. Update WIP document
```python
# In widget-system-refactor-WIP.md
Current Phase: Phase 1 - Preparation
Branch: feature/widget-system-complete
```

#### Verification:
- [ ] On correct branch
- [ ] Branch pushed to remote

---

### Task 1.3: Create Baseline Test Suite ⬜
**Time**: 30 minutes
**Dependencies**: Task 1.2

#### Steps:
1. Create file: `test_widget_system_baseline.py`
```python
#!/usr/bin/env python3
"""Baseline tests that must always pass during refactoring."""

import sys
import subprocess
sys.path.insert(0, "packages/viloapp/src")

def test_no_undefined_variables():
    """No undefined variables in codebase."""
    result = subprocess.run(
        ["python", "-m", "py_compile"] +
        glob.glob("packages/viloapp/src/**/*.py", recursive=True),
        capture_output=True, text=True
    )
    assert "NameError" not in result.stderr
    print("✅ No undefined variables")

def test_all_commands_execute():
    """All commands must execute without NameError."""
    from viloapp.core.commands.registry import command_registry
    from viloapp.core.commands.base import CommandContext
    from viloapp.models.workspace_model import WorkspaceModel

    context = CommandContext()
    context.model = WorkspaceModel()

    failed = []
    for cmd_id in command_registry.get_all_commands():
        try:
            cmd = command_registry.get_command(cmd_id)
            if cmd and hasattr(cmd, 'execute'):
                cmd.execute(context)
        except NameError as e:
            failed.append((cmd_id, str(e)))

    assert not failed, f"Commands with NameError: {failed}"
    print(f"✅ All {len(command_registry.get_all_commands())} commands execute")

def test_widget_creation():
    """All registered widgets must be creatable."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_registry import register_builtin_widgets

    app_widget_manager.clear()
    register_builtin_widgets()

    for widget_id in app_widget_manager.get_available_widget_ids():
        widget = app_widget_manager.create_widget(widget_id, "test-instance")
        assert widget is not None, f"Failed to create {widget_id}"

    print(f"✅ All {len(app_widget_manager.get_available_widget_ids())} widgets creatable")

def test_no_hardcoded_widget_ids():
    """No hardcoded widget IDs in core files."""
    import os
    import re

    bad_patterns = [
        r'"com\.viloapp\.(terminal|editor|settings)"',
        r"'com\.viloapp\.(terminal|editor|settings)'",
    ]

    violations = []
    for root, _, files in os.walk("packages/viloapp/src/viloapp/core"):
        for file in files:
            if not file.endswith('.py'):
                continue
            filepath = os.path.join(root, file)
            with open(filepath) as f:
                content = f.read()
                for pattern in bad_patterns:
                    if re.search(pattern, content):
                        violations.append(filepath)

    assert not violations, f"Hardcoded IDs in: {violations}"
    print("✅ No hardcoded widget IDs in core")

def test_app_startup():
    """Application must start without errors."""
    result = subprocess.run(
        ["python", "packages/viloapp/src/viloapp/main.py", "--test-startup"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, "App failed to start"
    print("✅ Application starts successfully")

if __name__ == "__main__":
    tests = [
        test_no_undefined_variables,
        test_all_commands_execute,
        test_widget_creation,
        test_no_hardcoded_widget_ids,
        test_app_startup,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            sys.exit(1)

    print("\n✅ All baseline tests passed!")
```

2. Run the baseline tests
```bash
python test_widget_system_baseline.py
```

3. Commit baseline tests
```bash
git add test_widget_system_baseline.py
git commit -m "refactor(widget): [Phase 1.3] Add baseline test suite"
```

#### Verification:
- [ ] All baseline tests pass
- [ ] File committed

#### North Star Check:
- [ ] Tests verify no hardcoded IDs (Rule 5)
- [ ] Tests verify command pattern (Rule 2)

---

### Task 1.4: Create Monitoring Script ⬜
**Time**: 20 minutes
**Dependencies**: Task 1.3

#### Steps:
1. Create file: `monitor_widget_refactoring.sh`
```bash
#!/bin/bash
# Continuous monitoring during widget system refactoring

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

while true; do
    clear
    echo "======================================"
    echo "    WIDGET REFACTORING MONITOR"
    echo "======================================"

    # Check for syntax errors
    echo -e "\n🔍 Syntax Check:"
    if python -m py_compile packages/viloapp/src/viloapp/**/*.py 2>/dev/null; then
        echo -e "${GREEN}✅ No syntax errors${NC}"
    else
        echo -e "${RED}❌ SYNTAX ERRORS FOUND${NC}"
        python -m py_compile packages/viloapp/src/viloapp/**/*.py
    fi

    # Check for undefined variables
    echo -e "\n🔍 Undefined Variables Check:"
    UNDEFINED=$(python -c "
import subprocess
import glob
files = glob.glob('packages/viloapp/src/**/*.py', recursive=True)
result = subprocess.run(['python', '-m', 'py_compile'] + files,
                       capture_output=True, text=True)
if 'NameError' in result.stderr or 'undefined' in result.stderr:
    print(result.stderr)
")
    if [ -z "$UNDEFINED" ]; then
        echo -e "${GREEN}✅ No undefined variables${NC}"
    else
        echo -e "${RED}❌ UNDEFINED VARIABLES:${NC}"
        echo "$UNDEFINED"
    fi

    # Variable naming consistency
    echo -e "\n📊 Variable Name Consistency:"
    WT_COUNT=$(grep -r "widget_type" packages/viloapp/src --include="*.py" 2>/dev/null | wc -l)
    WI_COUNT=$(grep -r "widget_id" packages/viloapp/src --include="*.py" 2>/dev/null | wc -l)
    echo "  widget_type: $WT_COUNT occurrences"
    echo "  widget_id:   $WI_COUNT occurrences"
    if [ $WT_COUNT -gt 0 ]; then
        echo -e "  ${YELLOW}⚠️  Still have widget_type references${NC}"
    fi

    # Hardcoded widget IDs
    echo -e "\n🔍 Hardcoded Widget IDs:"
    HARDCODED=$(grep -r '"com\.viloapp\.\(terminal\|editor\|settings\)"' \
                packages/viloapp/src/viloapp/core --include="*.py" 2>/dev/null | wc -l)
    if [ $HARDCODED -eq 0 ]; then
        echo -e "${GREEN}✅ No hardcoded widget IDs in core${NC}"
    else
        echo -e "${RED}❌ Found $HARDCODED hardcoded widget IDs${NC}"
    fi

    # Quick baseline test
    echo -e "\n🧪 Baseline Tests:"
    if python test_widget_system_baseline.py > /tmp/baseline_test.log 2>&1; then
        echo -e "${GREEN}✅ All baseline tests pass${NC}"
    else
        echo -e "${RED}❌ BASELINE TESTS FAILING${NC}"
        tail -5 /tmp/baseline_test.log
    fi

    # Git status
    echo -e "\n📝 Changed Files:"
    git status -s | head -10

    # Last commit
    echo -e "\n📌 Last Commit:"
    git log --oneline -1

    sleep 3
done
```

2. Make executable and test
```bash
chmod +x monitor_widget_refactoring.sh
# Run in separate terminal: ./monitor_widget_refactoring.sh
```

3. Commit monitoring script
```bash
git add monitor_widget_refactoring.sh
git commit -m "refactor(widget): [Phase 1.4] Add continuous monitoring script"
```

#### Verification:
- [ ] Script runs without errors
- [ ] Shows current state accurately
- [ ] Updates every 3 seconds

#### North Star Check:
- [ ] Monitors for hardcoded IDs (Rule 5)
- [ ] Checks for undefined variables (Rule 6)

---

### Task 1.5: Document Rollback Points ⬜
**Time**: 10 minutes
**Dependencies**: Task 1.4

#### Steps:
1. Create rollback script: `rollback_widget_refactor.sh`
```bash
#!/bin/bash
# Emergency rollback script for widget refactoring

echo "Widget Refactoring Rollback Options:"
echo "====================================="
git tag -l "checkpoint-*" | sort -r | head -10

echo ""
echo "To rollback to a checkpoint:"
echo "  git reset --hard checkpoint-name"
echo ""
echo "Current HEAD:"
git log --oneline -1
```

2. Set Phase 1 checkpoint
```bash
git tag checkpoint-phase-1-complete
git push origin checkpoint-phase-1-complete
```

3. Update WIP document
```markdown
# In widget-system-refactor-WIP.md
Phase 1: ✅ COMPLETE
Last Checkpoint: checkpoint-phase-1-complete
```

#### Verification:
- [ ] Rollback script works
- [ ] Checkpoint tag created
- [ ] WIP document updated

#### North Star Check:
- [ ] Rollback maintains working state
- [ ] No architectural violations

---

## Phase 2: Complete Model Layer

### Task 2.1: Enhance WorkspaceModel Widget Methods ⬜
**Time**: 45 minutes
**Dependencies**: Phase 1 Complete

#### Steps:
1. Open `packages/viloapp/src/viloapp/models/workspace_model.py`

2. Add widget management methods
```python
# After existing imports
from typing import Optional, List
from viloapp.core.app_widget_manager import app_widget_manager

# In WorkspaceModel class, add:

def get_available_widget_ids(self) -> List[str]:
    """Get widget IDs that can be used in panes.

    Returns:
        List of available widget IDs from registry
    """
    return app_widget_manager.get_available_widget_ids()

def change_pane_widget(self, pane_id: str, widget_id: str) -> bool:
    """Change the widget type of a pane.

    Args:
        pane_id: ID of pane to change
        widget_id: New widget ID to use

    Returns:
        True if successful, False otherwise
    """
    # Validate widget_id exists
    if widget_id not in self.get_available_widget_ids():
        logger.error(f"Widget ID {widget_id} not available")
        return False

    # Find pane in active tab
    active_tab = self.state.get_active_tab()
    if not active_tab:
        return False

    pane = self._find_pane_in_tree(active_tab.tree.root, pane_id)
    if not pane:
        logger.error(f"Pane {pane_id} not found")
        return False

    # Update widget ID
    old_widget_id = pane.widget_id
    pane.widget_id = widget_id

    # Notify observers
    self._notify_observers("pane_widget_changed", {
        "pane_id": pane_id,
        "old_widget_id": old_widget_id,
        "new_widget_id": widget_id,
        "tab_id": active_tab.id
    })

    logger.info(f"Changed pane {pane_id} from {old_widget_id} to {widget_id}")
    return True

def _find_pane_in_tree(self, node: PaneNode, pane_id: str) -> Optional[Pane]:
    """Recursively find pane in tree.

    Args:
        node: Tree node to search
        pane_id: ID of pane to find

    Returns:
        Pane if found, None otherwise
    """
    if node.node_type == NodeType.LEAF:
        if node.pane and node.pane.id == pane_id:
            return node.pane
    else:
        # Search in split children
        result = self._find_pane_in_tree(node.first, pane_id)
        if result:
            return result
        result = self._find_pane_in_tree(node.second, pane_id)
        if result:
            return result
    return None
```

3. Run tests to verify
```bash
python test_widget_system_baseline.py
```

4. Commit changes
```bash
git add packages/viloapp/src/viloapp/models/workspace_model.py
git commit -m "refactor(widget): [Phase 2.1] Add widget management methods to model"
```

#### Verification:
- [ ] New methods compile without errors
- [ ] Baseline tests still pass
- [ ] No UI imports in model

#### North Star Check:
- [ ] Model has no UI knowledge (Rule 3)
- [ ] Methods return data, not UI elements
- [ ] Observers notified of changes (Rule 1)

---

### Task 2.2: Add Widget Preferences to Model ⬜
**Time**: 30 minutes
**Dependencies**: Task 2.1

#### Steps:
1. Update `packages/viloapp/src/viloapp/models/workspace_model.py`

2. Add to WorkspaceState dataclass
```python
@dataclass
class WorkspaceState:
    """Complete workspace state."""
    tabs: List[Tab] = field(default_factory=list)
    active_tab_index: int = 0
    metadata: dict = field(default_factory=dict)

    # Add this new field:
    widget_preferences: dict[str, str] = field(default_factory=dict)
    # Maps context -> preferred widget_id
    # e.g., {"terminal": "plugin.awesome.terminal", "editor": "com.viloapp.editor"}
```

3. Add preference methods to WorkspaceModel
```python
def set_widget_preference(self, context: str, widget_id: str) -> bool:
    """Set user's preferred widget for a context.

    Args:
        context: Context name (e.g., "terminal", "editor")
        widget_id: Preferred widget ID

    Returns:
        True if successful
    """
    # Validate widget exists
    if widget_id not in self.get_available_widget_ids():
        logger.error(f"Widget {widget_id} not available")
        return False

    # Store preference
    old_pref = self.state.widget_preferences.get(context)
    self.state.widget_preferences[context] = widget_id

    # Notify observers
    self._notify_observers("preference_changed", {
        "context": context,
        "widget_id": widget_id,
        "old_widget_id": old_pref
    })

    logger.info(f"Set {context} preference to {widget_id}")
    return True

def get_widget_preference(self, context: str) -> Optional[str]:
    """Get user's preferred widget for a context.

    Args:
        context: Context name

    Returns:
        Preferred widget ID or None
    """
    return self.state.widget_preferences.get(context)

def get_default_widget_for_context(self, context: str) -> str:
    """Get default widget for context, considering preferences.

    Args:
        context: Context name

    Returns:
        Widget ID to use (preference or system default)
    """
    # Check user preference first
    pref = self.get_widget_preference(context)
    if pref:
        return pref

    # Fall back to system default
    return app_widget_manager.get_default_widget_id(context)
```

4. Test preference storage
```python
# Quick test script
model = WorkspaceModel()
assert model.set_widget_preference("terminal", "com.viloapp.terminal")
assert model.get_widget_preference("terminal") == "com.viloapp.terminal"
print("✅ Preferences work")
```

5. Commit changes
```bash
git add packages/viloapp/src/viloapp/models/workspace_model.py
git commit -m "refactor(widget): [Phase 2.2] Add widget preferences to model"
```

#### Verification:
- [ ] Preferences store correctly
- [ ] Observer notifications work
- [ ] Validation prevents invalid widgets

#### North Star Check:
- [ ] Model remains pure data (Rule 3)
- [ ] No business logic in model (Rule 4)
- [ ] Observers notified (Rule 1)

---

### Task 2.3: Add Migration for Existing Data ⬜
**Time**: 20 minutes
**Dependencies**: Task 2.2

#### Steps:
1. Update `packages/viloapp/src/viloapp/models/workspace_model.py`

2. Add migration in load_state method
```python
def load_state(self, state: dict) -> None:
    """Load workspace state from dictionary.

    Handles migration from old formats.
    """
    # Existing code...

    # Add migration for widget preferences
    if "widget_preferences" not in state:
        state["widget_preferences"] = {}

        # Migrate from old settings if they exist
        if "default_terminal" in state.get("metadata", {}):
            state["widget_preferences"]["terminal"] = state["metadata"]["default_terminal"]
        if "default_editor" in state.get("metadata", {}):
            state["widget_preferences"]["editor"] = state["metadata"]["default_editor"]

    # Continue with existing load...
```

3. Test migration
```python
# Test old format loads correctly
old_state = {
    "tabs": [],
    "metadata": {
        "default_terminal": "com.viloapp.terminal"
    }
}
model = WorkspaceModel()
model.load_state(old_state)
assert model.get_widget_preference("terminal") == "com.viloapp.terminal"
print("✅ Migration works")
```

4. Commit
```bash
git add packages/viloapp/src/viloapp/models/workspace_model.py
git commit -m "refactor(widget): [Phase 2.3] Add data migration for preferences"
```

5. Create Phase 2 checkpoint
```bash
git tag checkpoint-phase-2-complete
git push origin checkpoint-phase-2-complete
```

#### Verification:
- [ ] Old format loads without errors
- [ ] Preferences migrate correctly
- [ ] New format saves correctly

#### North Star Check:
- [ ] Backwards compatibility maintained
- [ ] No data loss

---

## Phase 3: Service Layer Enhancement

### Task 3.1: Create WidgetService ⬜
**Time**: 1 hour
**Dependencies**: Phase 2 Complete

#### Steps:
1. Create file: `packages/viloapp/src/viloapp/services/widget_service.py`
```python
#!/usr/bin/env python3
"""Service for widget-related business logic."""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from viloapp.core.app_widget_manager import app_widget_manager
from viloapp.core.app_widget_metadata import WidgetCategory
from viloapp.models.workspace_model import WorkspaceModel
from viloapp.services.base import OperationResult

logger = logging.getLogger(__name__)


@dataclass
class WidgetChoice:
    """A widget choice for UI display."""
    widget_id: str
    display_name: str
    category: WidgetCategory
    icon: Optional[str] = None
    description: Optional[str] = None


class WidgetService:
    """Service for widget-related business logic.

    All widget validation, rules, and business logic lives here.
    UI should never make these decisions.
    """

    def __init__(self, model: WorkspaceModel):
        """Initialize with model reference.

        Args:
            model: The workspace model
        """
        self._model = model
        logger.info("WidgetService initialized")

    def get_widget_choices_for_pane(self, pane_id: str) -> List[WidgetChoice]:
        """Get available widget choices for a pane.

        Business logic for which widgets can be used.

        Args:
            pane_id: ID of the pane

        Returns:
            List of available widget choices
        """
        choices = []

        # Get all available widgets from registry
        for widget_id in app_widget_manager.get_available_widget_ids():
            metadata = app_widget_manager.get_widget(widget_id)
            if not metadata:
                continue

            # Business rule: Only show widgets that allow menu display
            if not metadata.show_in_menu:
                continue

            # Business rule: Check if widget allows type changes
            if not metadata.allow_type_change:
                continue

            choices.append(WidgetChoice(
                widget_id=widget_id,
                display_name=metadata.display_name,
                category=metadata.category,
                icon=metadata.icon,
                description=metadata.description
            ))

        # Sort by category and name for consistent display
        choices.sort(key=lambda c: (c.category.value, c.display_name))

        logger.debug(f"Found {len(choices)} widget choices for pane {pane_id}")
        return choices

    def can_change_widget_type(self, pane_id: str, widget_id: str) -> Tuple[bool, str]:
        """Check if widget type can be changed.

        All validation rules for widget changes.

        Args:
            pane_id: ID of the pane
            widget_id: New widget ID

        Returns:
            Tuple of (can_change, reason_if_not)
        """
        # Rule 1: Pane must exist
        active_tab = self._model.state.get_active_tab()
        if not active_tab:
            return False, "No active tab"

        pane = self._model._find_pane_in_tree(active_tab.tree.root, pane_id)
        if not pane:
            return False, "Pane not found"

        # Rule 2: Widget must be available
        if not app_widget_manager.is_widget_available(widget_id):
            return False, f"Widget {widget_id} not available"

        # Rule 3: Check current widget allows changes
        current_metadata = app_widget_manager.get_widget(pane.widget_id)
        if current_metadata and not current_metadata.allow_type_change:
            return False, f"Widget {current_metadata.display_name} doesn't allow type changes"

        # Rule 4: Check if new widget can be created
        new_metadata = app_widget_manager.get_widget(widget_id)
        if not new_metadata:
            return False, f"Widget {widget_id} metadata not found"

        # Rule 5: Don't change to same type
        if pane.widget_id == widget_id:
            return False, "Already using this widget type"

        # All rules passed
        return True, ""

    def change_pane_widget_type(self, pane_id: str, widget_id: str) -> OperationResult:
        """Change pane widget type with full validation.

        This is the main business operation for widget changes.

        Args:
            pane_id: ID of the pane
            widget_id: New widget ID

        Returns:
            OperationResult with success/failure
        """
        # Validate
        can_change, reason = self.can_change_widget_type(pane_id, widget_id)
        if not can_change:
            logger.warning(f"Cannot change widget: {reason}")
            return OperationResult(success=False, error=reason)

        # Perform change
        if self._model.change_pane_widget(pane_id, widget_id):
            logger.info(f"Changed pane {pane_id} to widget {widget_id}")
            return OperationResult(success=True, data={"pane_id": pane_id, "widget_id": widget_id})

        return OperationResult(success=False, error="Failed to change widget in model")

    def get_widget_categories(self) -> List[WidgetCategory]:
        """Get all available widget categories.

        Returns:
            List of categories that have widgets
        """
        categories = set()
        for widget_id in app_widget_manager.get_available_widget_ids():
            metadata = app_widget_manager.get_widget(widget_id)
            if metadata:
                categories.add(metadata.category)

        return sorted(list(categories), key=lambda c: c.value)

    def set_default_widget_preference(self, context: str, widget_id: str) -> OperationResult:
        """Set default widget preference for a context.

        Business logic for preference changes.

        Args:
            context: Context name (e.g., "terminal", "editor")
            widget_id: Preferred widget ID

        Returns:
            OperationResult
        """
        # Validate widget exists and is appropriate for context
        if not app_widget_manager.is_widget_available(widget_id):
            return OperationResult(success=False, error=f"Widget {widget_id} not available")

        metadata = app_widget_manager.get_widget(widget_id)
        if not metadata:
            return OperationResult(success=False, error="Widget metadata not found")

        # Business rule: Check if widget is appropriate for context
        if context not in metadata.default_for_contexts:
            logger.warning(f"Widget {widget_id} not designed for {context} context")
            # Allow it anyway but log warning

        # Store preference
        if self._model.set_widget_preference(context, widget_id):
            # Also update global settings
            from viloapp.core.settings.app_defaults import set_default_widget_for_context
            set_default_widget_for_context(context, widget_id)

            return OperationResult(success=True)

        return OperationResult(success=False, error="Failed to store preference")
```

2. Run syntax check
```bash
python -m py_compile packages/viloapp/src/viloapp/services/widget_service.py
```

3. Add to service registry
```python
# In packages/viloapp/src/viloapp/services/__init__.py
from viloapp.services.widget_service import WidgetService

__all__ = [
    # ... existing
    "WidgetService",
]
```

4. Commit
```bash
git add packages/viloapp/src/viloapp/services/widget_service.py
git add packages/viloapp/src/viloapp/services/__init__.py
git commit -m "refactor(widget): [Phase 3.1] Create WidgetService for business logic"
```

#### Verification:
- [ ] Service compiles without errors
- [ ] No UI imports in service
- [ ] All business logic encapsulated

#### North Star Check:
- [ ] All business logic in service (Rule 4)
- [ ] Service only works with model (Rule 3)
- [ ] Returns OperationResult (Pattern 4)

---

### Task 3.2: Register WidgetService ⬜
**Time**: 20 minutes
**Dependencies**: Task 3.1

#### Steps:
1. Update service initialization in `packages/viloapp/src/viloapp/services/service_locator.py`
```python
# In ServiceLocator.initialize method:

# After workspace service
from viloapp.services.widget_service import WidgetService
widget_service = WidgetService(workspace_model)
self.register(WidgetService, widget_service)
logger.info("Registered WidgetService")
```

2. Test service availability
```python
# Quick test
from viloapp.services.service_locator import ServiceLocator
from viloapp.services.widget_service import WidgetService

ServiceLocator.get_instance().initialize()
service = ServiceLocator.get_instance().get(WidgetService)
assert service is not None
print("✅ WidgetService available")
```

3. Commit
```bash
git add packages/viloapp/src/viloapp/services/service_locator.py
git commit -m "refactor(widget): [Phase 3.2] Register WidgetService in ServiceLocator"
```

4. Create checkpoint
```bash
git tag checkpoint-phase-3-complete
git push origin checkpoint-phase-3-complete
```

#### Verification:
- [ ] Service registered correctly
- [ ] Service accessible via locator
- [ ] No circular dependencies

#### North Star Check:
- [ ] Dependency injection pattern (Pattern 1)
- [ ] Service layer complete

---

## Phase 4: Command Layer Updates

### Task 4.1: Create Widget Commands ⬜
**Time**: 45 minutes
**Dependencies**: Phase 3 Complete

#### Steps:
1. Create file: `packages/viloapp/src/viloapp/core/commands/builtin/widget_commands.py`
```python
#!/usr/bin/env python3
"""Commands for widget management."""

import logging
from typing import Optional

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command
from viloapp.services.widget_service import WidgetService

logger = logging.getLogger(__name__)


@command(
    id="pane.changeWidgetType",
    title="Change Pane Widget Type",
    category="Pane",
    description="Change the widget type of a pane",
    when="pane.focused"
)
def change_pane_widget_command(context: CommandContext) -> CommandResult:
    """Change the widget type of a pane.

    Required parameters:
    - pane_id: ID of pane to change
    - widget_id: New widget ID to use
    """
    try:
        # Get parameters
        pane_id = context.parameters.get("pane_id") if context.parameters else None
        widget_id = context.parameters.get("widget_id") if context.parameters else None

        if not pane_id or not widget_id:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message="Missing required parameters: pane_id and widget_id"
            )

        # Get service
        from viloapp.services.service_locator import ServiceLocator
        widget_service = ServiceLocator.get_instance().get(WidgetService)

        if not widget_service:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message="WidgetService not available"
            )

        # Perform change
        result = widget_service.change_pane_widget_type(pane_id, widget_id)

        if result.success:
            logger.info(f"Changed pane {pane_id} to widget {widget_id}")
            return CommandResult(
                status=CommandStatus.SUCCESS,
                data=result.data
            )
        else:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=result.error
            )

    except Exception as e:
        logger.error(f"Failed to change widget type: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE,
            message=str(e)
        )


@command(
    id="pane.showWidgetMenu",
    title="Show Widget Type Menu",
    category="Pane",
    description="Show menu to change pane widget type",
    when="pane.focused"
)
def show_widget_menu_command(context: CommandContext) -> CommandResult:
    """Show widget type menu for a pane.

    Required parameters:
    - pane_id: ID of pane
    """
    try:
        pane_id = context.parameters.get("pane_id") if context.parameters else None

        if not pane_id:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message="Missing pane_id parameter"
            )

        # Get available choices
        from viloapp.services.service_locator import ServiceLocator
        widget_service = ServiceLocator.get_instance().get(WidgetService)

        choices = widget_service.get_widget_choices_for_pane(pane_id)

        # Return choices for UI to display
        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={
                "pane_id": pane_id,
                "choices": [
                    {
                        "widget_id": c.widget_id,
                        "display_name": c.display_name,
                        "category": c.category.value,
                        "icon": c.icon
                    }
                    for c in choices
                ]
            }
        )

    except Exception as e:
        logger.error(f"Failed to get widget choices: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE,
            message=str(e)
        )


@command(
    id="settings.setDefaultWidget",
    title="Set Default Widget",
    category="Settings",
    description="Set the default widget for a context"
)
def set_default_widget_command(context: CommandContext) -> CommandResult:
    """Set default widget preference.

    Required parameters:
    - context: Context name (e.g., "terminal", "editor")
    - widget_id: Preferred widget ID
    """
    try:
        context_name = context.parameters.get("context") if context.parameters else None
        widget_id = context.parameters.get("widget_id") if context.parameters else None

        if not context_name or not widget_id:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message="Missing required parameters: context and widget_id"
            )

        # Use service for business logic
        from viloapp.services.service_locator import ServiceLocator
        widget_service = ServiceLocator.get_instance().get(WidgetService)

        result = widget_service.set_default_widget_preference(context_name, widget_id)

        if result.success:
            logger.info(f"Set {context_name} default to {widget_id}")
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=result.error
            )

    except Exception as e:
        logger.error(f"Failed to set default widget: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE,
            message=str(e)
        )


@command(
    id="widget.listAvailable",
    title="List Available Widgets",
    category="Widget",
    description="List all available widgets"
)
def list_widgets_command(context: CommandContext) -> CommandResult:
    """List all available widgets.

    Returns widget information for display.
    """
    try:
        from viloapp.core.app_widget_manager import app_widget_manager

        widgets = []
        for widget_id in app_widget_manager.get_available_widget_ids():
            metadata = app_widget_manager.get_widget(widget_id)
            if metadata:
                widgets.append({
                    "widget_id": widget_id,
                    "display_name": metadata.display_name,
                    "category": metadata.category.value,
                    "source": metadata.source,
                    "description": metadata.description
                })

        # Sort by category and name
        widgets.sort(key=lambda w: (w["category"], w["display_name"]))

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"widgets": widgets}
        )

    except Exception as e:
        logger.error(f"Failed to list widgets: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE,
            message=str(e)
        )


# Register commands
def register_widget_commands():
    """Register all widget commands."""
    logger.info("Widget commands registered")
```

2. Register in command router
```python
# In packages/viloapp/src/viloapp/core/commands/router.py
# Add to imports
from viloapp.core.commands.builtin import widget_commands

# In initialize_builtin_commands function:
widget_commands.register_widget_commands()
```

3. Test commands
```bash
python test_widget_system_baseline.py  # Should still pass
```

4. Commit
```bash
git add packages/viloapp/src/viloapp/core/commands/builtin/widget_commands.py
git add packages/viloapp/src/viloapp/core/commands/router.py
git commit -m "refactor(widget): [Phase 4.1] Create widget management commands"
```

#### Verification:
- [ ] Commands compile without errors
- [ ] Commands use service layer
- [ ] No direct model access

#### North Star Check:
- [ ] All operations through commands (Rule 2)
- [ ] Commands only call services (Rule 3)
- [ ] Return CommandResult (Pattern)

---

## Phase 5: Pure View Implementation

### Task 5.1: Create Pure SplitPaneWidget ⬜
**Time**: 2 hours
**Dependencies**: Phase 4 Complete

#### Steps:
1. Replace `packages/viloapp/src/viloapp/ui/widgets/split_pane_widget.py`
```python
#!/usr/bin/env python3
"""
Split pane widget - Pure view implementation.

This widget is a pure view that renders the pane tree from the model.
It contains NO business logic, only presentation and event forwarding.
"""

import logging
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QSplitter,
)

from viloapp.models.workspace_model import (
    WorkspaceModel,
    PaneNode,
    NodeType,
    Orientation,
    Pane
)
from viloapp.ui.widgets.pane_header import PaneHeader
from viloapp.core.app_widget_manager import app_widget_manager

logger = logging.getLogger(__name__)


class SplitPaneWidget(QWidget):
    """Pure view that renders pane tree from model.

    This widget:
    - Observes the model for changes
    - Renders the tree structure
    - Forwards user events to commands
    - Contains NO business logic
    """

    # Signals for UI events
    pane_added = Signal(str)       # pane_id
    pane_removed = Signal(str)     # pane_id
    active_pane_changed = Signal(str)  # pane_id
    layout_changed = Signal()

    def __init__(self, model: WorkspaceModel, tab_id: str, parent=None):
        """Initialize as pure view.

        Args:
            model: The workspace model to observe
            tab_id: ID of the tab to render
            parent: Parent widget
        """
        super().__init__(parent)

        self._model = model
        self._tab_id = tab_id
        self._widget_instances: Dict[str, QWidget] = {}  # pane_id -> AppWidget
        self._pane_containers: Dict[str, QWidget] = {}   # pane_id -> Container
        self._active_pane_id: Optional[str] = None

        # Setup UI
        self._setup_ui()

        # Observe model for changes
        self._model.add_observer(self._on_model_changed)

        # Initial render
        self._render_tree()

        logger.info(f"SplitPaneWidget created for tab {tab_id}")

    def _setup_ui(self):
        """Setup the UI structure."""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Will hold the tree widget
        self._tree_container = None

    def _on_model_changed(self, event: str, data: dict):
        """React to model changes.

        Pure observation - no business logic.

        Args:
            event: Event name
            data: Event data
        """
        # Only react to events for our tab
        tab_id = data.get("tab_id")
        if tab_id and tab_id != self._tab_id:
            return

        if event == "tree_structure_changed":
            logger.debug(f"Tree structure changed for tab {self._tab_id}")
            self._render_tree()
            self.layout_changed.emit()

        elif event == "pane_added":
            pane_id = data.get("pane_id")
            if pane_id:
                logger.debug(f"Pane {pane_id} added")
                self._render_tree()  # Re-render to include new pane
                self.pane_added.emit(pane_id)

        elif event == "pane_removed":
            pane_id = data.get("pane_id")
            if pane_id:
                logger.debug(f"Pane {pane_id} removed")
                self._remove_pane_widget(pane_id)
                self._render_tree()
                self.pane_removed.emit(pane_id)

        elif event == "pane_widget_changed":
            pane_id = data.get("pane_id")
            new_widget_id = data.get("new_widget_id")
            if pane_id and new_widget_id:
                logger.debug(f"Pane {pane_id} widget changed to {new_widget_id}")
                self._update_pane_widget(pane_id, new_widget_id)

        elif event == "active_pane_changed":
            pane_id = data.get("pane_id")
            if pane_id:
                self._update_active_pane(pane_id)

    def _render_tree(self):
        """Render the complete tree from model.

        Pure rendering - no business logic.
        """
        # Clear existing tree widget
        if self._tree_container:
            self._layout.removeWidget(self._tree_container)
            self._tree_container.deleteLater()
            self._tree_container = None

        # Get tab from model
        tab = None
        for t in self._model.state.tabs:
            if t.id == self._tab_id:
                tab = t
                break

        if not tab:
            logger.warning(f"Tab {self._tab_id} not found in model")
            return

        # Create widget for tree root
        root_widget = self._create_node_widget(tab.tree.root)
        if root_widget:
            self._tree_container = root_widget
            self._layout.addWidget(root_widget)

            # Set active pane if exists
            if tab.active_pane_id:
                self._update_active_pane(tab.active_pane_id)

        logger.debug(f"Rendered tree for tab {self._tab_id}")

    def _create_node_widget(self, node: PaneNode) -> Optional[QWidget]:
        """Create widget for a tree node.

        Pure widget creation - no business logic.

        Args:
            node: Tree node from model

        Returns:
            Widget representing the node
        """
        if node.node_type == NodeType.LEAF:
            # Create pane widget
            if node.pane:
                return self._create_pane_widget(node.pane)
            else:
                logger.warning("Leaf node without pane")
                return QWidget()

        elif node.node_type == NodeType.SPLIT:
            # Create splitter
            return self._create_split_widget(node)

        return None

    def _create_pane_widget(self, pane: Pane) -> QWidget:
        """Create widget for a pane.

        Pure widget creation - no business logic.

        Args:
            pane: Pane from model

        Returns:
            Container widget with header and content
        """
        # Create container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create header (also a pure view)
        header = PaneHeader(pane.id, self._model, container)
        layout.addWidget(header)

        # Create app widget from registry
        try:
            app_widget = app_widget_manager.create_widget(
                pane.widget_id,
                pane.id  # Use pane ID as instance ID
            )

            if app_widget:
                self._widget_instances[pane.id] = app_widget
                layout.addWidget(app_widget)

                # Connect focus signal if available
                if hasattr(app_widget, 'focused'):
                    app_widget.focused.connect(
                        lambda: self._on_pane_focused(pane.id)
                    )
            else:
                # Create placeholder if widget creation fails
                placeholder = QWidget()
                placeholder.setStyleSheet("background-color: #333;")
                layout.addWidget(placeholder)
                logger.warning(f"Failed to create widget {pane.widget_id}")

        except Exception as e:
            logger.error(f"Error creating widget {pane.widget_id}: {e}")
            # Add placeholder
            placeholder = QWidget()
            placeholder.setStyleSheet("background-color: #333;")
            layout.addWidget(placeholder)

        # Store container reference
        self._pane_containers[pane.id] = container

        return container

    def _create_split_widget(self, node: PaneNode) -> QSplitter:
        """Create splitter for split node.

        Pure widget creation - no business logic.

        Args:
            node: Split node from model

        Returns:
            Configured QSplitter
        """
        # Determine orientation
        orientation = (
            Qt.Horizontal if node.orientation == Orientation.HORIZONTAL
            else Qt.Vertical
        )

        splitter = QSplitter(orientation)
        splitter.setChildrenCollapsible(False)

        # Create child widgets
        if node.first:
            first_widget = self._create_node_widget(node.first)
            if first_widget:
                splitter.addWidget(first_widget)

        if node.second:
            second_widget = self._create_node_widget(node.second)
            if second_widget:
                splitter.addWidget(second_widget)

        # Set split ratio
        if node.ratio:
            total = 1000
            first_size = int(total * node.ratio)
            second_size = total - first_size
            splitter.setSizes([first_size, second_size])

        # Connect splitter moved signal to update model
        splitter.splitterMoved.connect(
            lambda pos, idx: self._on_splitter_moved(node, splitter)
        )

        return splitter

    def _on_splitter_moved(self, node: PaneNode, splitter: QSplitter):
        """Handle splitter movement.

        Forward to command - no business logic.

        Args:
            node: The split node
            splitter: The splitter widget
        """
        sizes = splitter.sizes()
        if sum(sizes) > 0:
            new_ratio = sizes[0] / sum(sizes)

            # Use command to update ratio
            from viloapp.core.commands.execution import execute_command
            execute_command("pane.setSplitRatio", {
                "node_id": id(node),  # Use object ID as identifier
                "ratio": new_ratio
            })

    def _update_pane_widget(self, pane_id: str, widget_id: str):
        """Update widget for a pane.

        Pure UI update - no business logic.

        Args:
            pane_id: ID of pane to update
            widget_id: New widget ID
        """
        # Remove old widget
        if pane_id in self._widget_instances:
            old_widget = self._widget_instances[pane_id]
            old_widget.deleteLater()
            del self._widget_instances[pane_id]

        # Re-render the affected pane
        # For simplicity, re-render entire tree
        self._render_tree()

    def _remove_pane_widget(self, pane_id: str):
        """Remove widget for a pane.

        Pure cleanup - no business logic.

        Args:
            pane_id: ID of pane to remove
        """
        # Remove widget instance
        if pane_id in self._widget_instances:
            widget = self._widget_instances[pane_id]
            widget.deleteLater()
            del self._widget_instances[pane_id]

        # Remove container
        if pane_id in self._pane_containers:
            container = self._pane_containers[pane_id]
            container.deleteLater()
            del self._pane_containers[pane_id]

    def _update_active_pane(self, pane_id: str):
        """Update active pane highlighting.

        Pure UI update - no business logic.

        Args:
            pane_id: ID of new active pane
        """
        # Remove previous active highlighting
        if self._active_pane_id and self._active_pane_id in self._pane_containers:
            container = self._pane_containers[self._active_pane_id]
            container.setProperty("active", False)
            container.style().polish(container)

        # Add active highlighting
        if pane_id in self._pane_containers:
            container = self._pane_containers[pane_id]
            container.setProperty("active", True)
            container.style().polish(container)

            self._active_pane_id = pane_id
            self.active_pane_changed.emit(pane_id)

    def _on_pane_focused(self, pane_id: str):
        """Handle pane focus event.

        Forward to command - no business logic.

        Args:
            pane_id: ID of focused pane
        """
        # Use command to set active pane
        from viloapp.core.commands.execution import execute_command
        execute_command("pane.setActive", {"pane_id": pane_id})

    # Public methods for compatibility
    def get_active_pane_id(self) -> Optional[str]:
        """Get active pane ID from model."""
        tab = None
        for t in self._model.state.tabs:
            if t.id == self._tab_id:
                tab = t
                break

        return tab.active_pane_id if tab else None

    def cleanup(self):
        """Cleanup resources."""
        # Remove observer
        self._model.remove_observer(self._on_model_changed)

        # Cleanup widgets
        for widget in self._widget_instances.values():
            widget.deleteLater()
        self._widget_instances.clear()

        for container in self._pane_containers.values():
            container.deleteLater()
        self._pane_containers.clear()

        logger.info(f"SplitPaneWidget cleaned up for tab {self._tab_id}")
```

2. Test the new implementation
```bash
python test_widget_system_baseline.py
```

3. Commit
```bash
git add packages/viloapp/src/viloapp/ui/widgets/split_pane_widget.py
git commit -m "refactor(widget): [Phase 5.1] Implement SplitPaneWidget as pure view"
```

#### Verification:
- [ ] Widget compiles without errors
- [ ] No business logic in view
- [ ] Observes model correctly
- [ ] Renders tree structure

#### North Star Check:
- [ ] Pure view - only renders (Rule 3)
- [ ] Events forwarded to commands (Rule 2)
- [ ] No business logic (Rule 4)
- [ ] Observer pattern used (Pattern 2)

---

## Checkpoint: Phase 5 Critical Test

### Task 5.2: Integration Test ⬜
**Time**: 30 minutes
**Dependencies**: Task 5.1

#### Steps:
1. Create integration test
```python
# test_split_pane_integration.py
"""Test SplitPaneWidget integration."""

from PySide6.QtWidgets import QApplication
from viloapp.models.workspace_model import WorkspaceModel
from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget

app = QApplication([])

# Create model with tab
model = WorkspaceModel()
tab_id = model.create_tab("Test Tab", "com.viloapp.terminal")

# Create view
widget = SplitPaneWidget(model, tab_id)
widget.show()

# Should render without errors
print("✅ SplitPaneWidget renders")

# Test model update
model.split_pane(model.state.tabs[0].active_pane_id, "horizontal")
print("✅ Split renders")

widget.cleanup()
```

2. Run integration test
```bash
python test_split_pane_integration.py
```

3. Create Phase 5 checkpoint
```bash
git tag checkpoint-phase-5-critical
git push origin checkpoint-phase-5-critical
```

#### Verification:
- [ ] Widget renders correctly
- [ ] Model updates reflected in view
- [ ] No crashes

---

## Final Validation

### Task X.1: Complete System Test ⬜
**Time**: 1 hour
**Dependencies**: All phases complete

#### Steps:
1. Run all tests
```bash
python test_widget_system_baseline.py
python test_comprehensive_widget_system.py
python test_all_commands.py
pytest packages/viloapp/tests
```

2. Start application
```bash
python packages/viloapp/src/viloapp/main.py
```

3. Manual testing checklist:
- [ ] Create new tab with different widgets
- [ ] Change pane widget types
- [ ] Split panes work
- [ ] Settings show preferences
- [ ] Plugin widgets work like built-in

#### North Star Final Check:
- [ ] One-way data flow maintained
- [ ] All operations through commands
- [ ] No business logic in UI
- [ ] No hardcoded widget IDs
- [ ] Plugins are first-class citizens

---

## Completion Checklist

When all tasks complete:
1. [ ] Update WIP document as COMPLETE
2. [ ] Create final tag: `checkpoint-widget-refactor-complete`
3. [ ] Update architecture documentation
4. [ ] Create migration guide
5. [ ] Merge to main branch

---

**Remember**: After EVERY task:
1. Run verification steps
2. Check North Star compliance
3. Commit with proper message
4. Update WIP document
5. Continue monitoring script

**If ANY verification fails**: STOP and fix before continuing.