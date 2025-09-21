# Unit Test Issues - Quick Reference

## Critical Problems (40% of tests broken)

### Broken Import Tests - Won't Run
1. **test_workspace.py** - Wrong import: `ui.workspace` → Should be `ui.workspace_simple`
2. **test_tab_container.py** - Module doesn't exist anymore (delete this file)
3. **test_split_tree_manager.py** - Module doesn't exist (replaced by split_pane architecture)
4. **test_layout_state.py** - Wrong path: `models.layout_state` → Should be `controllers.state_controller`

### Architecture Changes Not Reflected
- Old: Workspace → TabContainer → tabs
- New: Workspace → SplitPaneWidget → PaneContent → tabs
- Tests still reference old methods like `split_horizontal()` that don't exist

### Missing Tests for New Components
- `ui/widgets/split_pane_widget.py` - No tests
- `ui/widgets/split_pane_model.py` - No tests
- Command system implementations - No tests
- Services layer - No tests

### Infrastructure Issues
- `@pytest.mark.unit` not registered (causing warnings)
- No shared test fixtures
- No mock services for testing

## Immediate Fix Required

```python
# Fix imports in test_workspace.py
# OLD:
from ui.workspace import Workspace, TabContainer

# NEW:
from ui.workspace_simple import Workspace
from ui.widgets.split_pane_widget import PaneContent

# Fix imports in test_layout_state.py
# OLD:
from models.layout_state import LayoutState

# NEW:
from controllers.state_controller import LayoutState, StateController
```

## Files to Delete
- `tests/unit/test_tab_container.py` - Component no longer exists
- `tests/unit/test_split_tree_manager.py` - Replaced by new architecture

## Fix pytest.ini
```ini
[pytest]
markers =
    unit: marks tests as unit tests
    integration: marks tests as integration tests
```

## Priority Actions
1. Fix 4 broken imports - **TODAY**
2. Delete 2 obsolete test files - **TODAY**
3. Add pytest markers to pytest.ini - **TODAY**
4. Create test_split_pane_widget.py - **THIS WEEK**
5. Create test_split_pane_model.py - **THIS WEEK**

## Current State
- **10 test files** in `/tests/unit/`
- **4 files** can't import (40% broken)
- **6 files** run but may test wrong things
- **0% coverage** on new split-pane architecture

## Target State
- All tests passing
- 80% code coverage
- Tests for all new components
- Proper test organization by module