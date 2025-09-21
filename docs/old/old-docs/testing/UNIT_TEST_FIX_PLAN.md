# Unit Test Fix Implementation Plan

## Executive Summary
This plan addresses the critical issue that **40% of unit tests are broken** and outlines a systematic approach to fix them, update outdated tests, and create missing tests for new components.

## Current Situation
- **10 test files** in `/tests/unit/`
- **4 files** with import errors (won't run)
- **6 files** that run but test outdated architecture
- **0% coverage** on new split-pane system

## Phase 1: Critical Fixes (Day 1 - Immediate)
**Goal**: Get all tests to at least import and run

### Task 1.1: Fix pytest Infrastructure (30 min)
```ini
# Update pytest.ini
[pytest]
markers =
    unit: marks tests as unit tests
    integration: marks tests as integration tests
    smoke: marks tests as smoke tests
```

### Task 1.2: Delete Obsolete Tests (15 min)
```bash
# Remove tests for non-existent components
rm tests/unit/test_tab_container.py      # Component doesn't exist
rm tests/unit/test_split_tree_manager.py # Replaced by split_pane architecture
```

### Task 1.3: Fix Import Errors (1 hour)

#### Fix test_workspace.py
```python
# OLD IMPORTS (broken):
from ui.workspace import Workspace, TabContainer

# NEW IMPORTS:
from ui.workspace_simple import Workspace
from ui.widgets.split_pane_widget import PaneContent, SplitPaneWidget
```

#### Fix test_layout_state.py
```python
# OLD IMPORTS (broken):
from models.layout_state import LayoutState, WorkspaceState, PaneState

# NEW IMPORTS:
from controllers.state_controller import LayoutState, StateController
```

### Task 1.4: Minimal Test Updates (2 hours)
Update test methods to work with new API:
- Replace `workspace.split_horizontal()` with command system
- Replace `TabContainer` references with `PaneContent`
- Update assertions for new widget structure

## Phase 2: Create Core Tests (Day 2-3)
**Goal**: Test the new split-pane architecture

### Task 2.1: Create test_split_pane_widget.py
```python
"""Test the core split pane functionality"""
- Test PaneContent creation
- Test tab management within panes
- Test pane splitting via commands
- Test pane closing
- Test maximize/restore functionality
```

### Task 2.2: Create test_split_pane_model.py
```python
"""Test the tree model for panes"""
- Test tree structure after splits
- Test node navigation
- Test model consistency
- Test serialization/deserialization
```

### Task 2.3: Create test_workspace_service.py
```python
"""Test the workspace service layer"""
- Test service registration
- Test workspace access
- Test pane management through service
- Test state persistence
```

## Phase 3: Update Existing Tests (Day 4-5)
**Goal**: Modernize tests to match current architecture

### Task 3.1: Update test_activity_bar.py
- Add tests for command execution
- Test toggle state management
- Test sidebar synchronization

### Task 3.2: Update test_sidebar.py
- Test command-based view switching
- Test animation with new architecture
- Test state persistence

### Task 3.3: Update test_main_window.py
- Test service initialization
- Test command system setup
- Test workspace integration

## Phase 4: Command System Tests (Week 2)
**Goal**: Comprehensive command testing

### Task 4.1: Create test_command_executor.py
- Test command execution flow
- Test context propagation
- Test error handling

### Task 4.2: Create test_command_implementations.py
- Test each command category
- Test command integration
- Test keyboard shortcuts

## Implementation Schedule

### Day 1 (4 hours) - URGENT
- [ ] Morning: Phase 1 - All critical fixes
- [ ] Afternoon: Verify all tests import successfully
- [ ] End of day: All tests should run (even if failing)

### Day 2-3 (8 hours)
- [ ] Create split-pane tests
- [ ] Create service tests
- [ ] Achieve 50% coverage on new components

### Day 4-5 (8 hours)
- [ ] Update existing tests
- [ ] Fix all test failures
- [ ] Achieve 70% overall coverage

### Week 2 (as time permits)
- [ ] Command system tests
- [ ] Integration test updates
- [ ] Achieve 80% coverage target

## Success Metrics

### Phase 1 Complete When:
- ✅ All tests import without errors
- ✅ pytest runs without collection errors
- ✅ No warnings about unknown markers

### Phase 2 Complete When:
- ✅ Split-pane system has >60% coverage
- ✅ All new component tests pass
- ✅ Service layer is tested

### Phase 3 Complete When:
- ✅ All unit tests pass
- ✅ No deprecated API usage
- ✅ Tests use command system where appropriate

### Phase 4 Complete When:
- ✅ 80% code coverage achieved
- ✅ All commands have tests
- ✅ CI/CD pipeline is green

## File Checklist

### To Delete (Day 1)
- [x] test_tab_container.py
- [x] test_split_tree_manager.py

### To Fix (Day 1)
- [ ] test_workspace.py - Fix imports and methods
- [ ] test_layout_state.py - Fix imports

### To Create (Day 2-3)
- [ ] test_split_pane_widget.py
- [ ] test_split_pane_model.py
- [ ] test_workspace_service.py

### To Update (Day 4-5)
- [ ] test_activity_bar.py
- [ ] test_sidebar.py
- [ ] test_main_window.py
- [ ] test_status_bar.py
- [ ] test_icon_manager.py

## Code Examples

### Example: Fixed test_workspace.py
```python
from ui.workspace_simple import Workspace
from ui.widgets.split_pane_widget import PaneContent
from core.commands.executor import execute_command

class TestWorkspace:
    def test_workspace_initialization(self, qtbot):
        workspace = Workspace()
        qtbot.addWidget(workspace)
        assert workspace.objectName() == "workspace"
        assert hasattr(workspace, 'split_pane_widget')
    
    def test_split_pane_command(self, qtbot, workspace):
        initial_count = len(workspace.get_all_panes())
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert result.success
        qtbot.wait(100)
        assert len(workspace.get_all_panes()) == initial_count + 1
```

### Example: New test_split_pane_widget.py
```python
from ui.widgets.split_pane_widget import PaneContent, SplitPaneWidget

class TestPaneContent:
    def test_pane_creation(self, qtbot):
        pane = PaneContent()
        qtbot.addWidget(pane)
        assert pane.tab_widget is not None
        assert pane.tab_widget.count() >= 0
    
    def test_add_tab(self, qtbot):
        pane = PaneContent()
        qtbot.addWidget(pane)
        initial_count = pane.tab_widget.count()
        pane.add_tab("Test Tab", QWidget())
        assert pane.tab_widget.count() == initial_count + 1
```

## Risk Mitigation

### Risk 1: Tests reveal bugs in main code
**Mitigation**: Document bugs, create issues, fix critical ones immediately

### Risk 2: Time overrun
**Mitigation**: Focus on Phase 1-2 first (critical path), Phase 3-4 can be delayed

### Risk 3: Complex test setup
**Mitigation**: Create shared fixtures and test utilities

## Conclusion

This plan transforms our broken test suite into a comprehensive testing framework. The phased approach ensures we quickly restore basic functionality (Phase 1) while systematically building toward comprehensive coverage (Phase 4).

**Total estimated time**: 
- Phase 1: 4 hours (Day 1)
- Phase 2-3: 16 hours (Day 2-5)
- Phase 4: 20 hours (Week 2)

**Priority**: Complete Phase 1 immediately to unblock development.