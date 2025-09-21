# Unit Test Audit Report

## Overview
This document provides a comprehensive audit of the unit tests in the `/tests/unit/` directory, identifying issues and recommending updates to align with the current codebase architecture.

## Executive Summary

### Current Status
- **Total Unit Test Files**: 10 files in `/tests/unit/`
- **Failing Tests**: 4 files cannot import due to architecture changes
- **Passing Tests**: 6 files (but may have outdated assertions)
- **Main Issues**: Outdated imports, missing modules, architecture drift

### Critical Findings
1. **40% of unit tests are broken** due to import errors
2. Tests reference old architecture (pre-refactoring)
3. Missing pytest marker registration for `@pytest.mark.unit`
4. Tests not aligned with new split-pane widget architecture

## Detailed Analysis

### 1. BROKEN TEST FILES (Import Errors)

#### test_workspace.py
- **Issue**: Imports `from ui.workspace import Workspace, TabContainer`
- **Reality**: Module renamed to `ui.workspace_simple.py`, class structure changed
- **Required Updates**:
  - Change import to `from ui.workspace_simple import Workspace`
  - Remove `TabContainer` import (doesn't exist anymore)
  - Update tests to use new `PaneContent` and split-pane architecture
  - Test methods like `split_horizontal()` no longer exist

#### test_tab_container.py
- **Issue**: Imports `from ui.widgets.tab_container import TabContainer, PlaceholderWidget`
- **Reality**: Module doesn't exist
- **Required Updates**:
  - Remove this test file or rewrite for new architecture
  - Tab functionality now integrated in `PaneContent` widget
  - Consider testing `ui.widgets.split_pane_widget.PaneContent` instead

#### test_split_tree_manager.py
- **Issue**: Imports `from ui.widgets.split_tree import SplitTreeManager`
- **Reality**: Module doesn't exist
- **Required Updates**:
  - Architecture changed to `split_pane_widget.py` and `split_pane_model.py`
  - Test should focus on `SplitPaneModel` and `SplitPaneWidget`
  - Completely rewrite tests for new tree structure

#### test_layout_state.py
- **Issue**: Imports `from models.layout_state import ...`
- **Reality**: No `layout_state.py` in models directory
- **Required Updates**:
  - State persistence now handled by `controllers/state_controller.py`
  - Test should import from `controllers.state_controller`
  - Update to test `StateController` and `LayoutState` classes

### 2. POTENTIALLY OUTDATED TEST FILES (Pass but may be incorrect)

#### test_activity_bar.py
- **Status**: Likely outdated
- **Concerns**: 
  - May not test command integration
  - Doesn't test new action toggling behavior
- **Required Updates**:
  - Add tests for `execute_command()` integration
  - Test toggle state management
  - Verify sidebar synchronization

#### test_sidebar.py
- **Status**: Needs review
- **Concerns**:
  - May not test view switching via commands
  - Animation testing might be outdated
- **Required Updates**:
  - Test command-based view switching
  - Verify integration with activity bar

#### test_main_window.py
- **Status**: Needs review
- **Concerns**:
  - May not test new workspace architecture
  - Service initialization tests might be missing
- **Required Updates**:
  - Test service registration
  - Verify command system initialization
  - Test new workspace_simple integration

#### test_status_bar.py
- **Status**: Probably okay
- **Concerns**: Minor
- **Required Updates**:
  - Add tests for new status messages
  - Test command feedback display

#### test_icon_manager.py
- **Status**: Likely okay
- **Concerns**: None major
- **Required Updates**:
  - Verify all new icons are tested
  - Test theme switching with new icons

### 3. MISSING UNIT TESTS

The following components lack unit tests:

1. **Split Pane System**
   - `ui/widgets/split_pane_widget.py` - Core pane functionality
   - `ui/widgets/split_pane_model.py` - Tree model for panes

2. **Command System**
   - Individual command implementations in `core/commands/implementations/`
   - Command context and executor

3. **Services**
   - `services/workspace_service.py`
   - `services/service_locator.py`

4. **Controllers**
   - `controllers/state_controller.py`
   - `controllers/shortcut_controller.py`

5. **New Widgets**
   - `ui/widgets/pane_header.py`
   - `ui/widgets/rename_editor.py`
   - `ui/widgets/app_widget.py`

### 4. TEST INFRASTRUCTURE ISSUES

#### pytest.mark.unit Warning
```python
# Issue: Unknown pytest.mark.unit
@pytest.mark.unit  # This marker is not registered
```

**Solution**: Add to `pytest.ini`:
```ini
[pytest]
markers =
    unit: marks tests as unit tests
    integration: marks tests as integration tests
```

#### Missing Test Utilities
- No shared fixtures for common widgets
- No mock services for testing
- No test data factories

## Recommended Actions

### Priority 1: Fix Broken Tests (Immediate)

1. **Update test_workspace.py**
   ```python
   # Old
   from ui.workspace import Workspace, TabContainer
   
   # New
   from ui.workspace_simple import Workspace
   from ui.widgets.split_pane_widget import PaneContent
   ```

2. **Delete or Rewrite Obsolete Tests**
   - Delete `test_tab_container.py` (component no longer exists)
   - Delete `test_split_tree_manager.py` (replaced by new architecture)
   - Rewrite `test_layout_state.py` for new state controller

### Priority 2: Create Missing Tests (This Week)

1. **test_split_pane_widget.py** - Test core pane functionality
2. **test_split_pane_model.py** - Test tree model
3. **test_workspace_service.py** - Test service layer
4. **test_command_context.py** - Test command infrastructure

### Priority 3: Update Existing Tests (Next Sprint)

1. Update all tests to use command system where appropriate
2. Add integration points testing
3. Improve test coverage to 80%+

## Test Organization Proposal

```
tests/
├── unit/
│   ├── ui/
│   │   ├── test_main_window.py
│   │   ├── test_activity_bar.py
│   │   ├── test_sidebar.py
│   │   ├── test_status_bar.py
│   │   └── test_workspace_simple.py
│   ├── widgets/
│   │   ├── test_split_pane_widget.py
│   │   ├── test_split_pane_model.py
│   │   ├── test_pane_header.py
│   │   └── test_app_widget.py
│   ├── core/
│   │   ├── test_command_executor.py
│   │   ├── test_command_registry.py
│   │   └── test_command_context.py
│   ├── services/
│   │   ├── test_workspace_service.py
│   │   └── test_service_locator.py
│   └── controllers/
│       ├── test_state_controller.py
│       └── test_shortcut_controller.py
```

## Migration Checklist

- [ ] Fix import errors in 4 broken test files
- [ ] Register pytest.mark.unit marker
- [ ] Create test for split pane widget
- [ ] Create test for split pane model
- [ ] Create test for workspace service
- [ ] Update workspace tests for new architecture
- [ ] Remove obsolete test files
- [ ] Add command system tests
- [ ] Update all tests to check actual behavior, not just mocks
- [ ] Achieve 80% code coverage for unit tests

## Code Coverage Target

Current coverage: Unknown (tests not running)
Target coverage: 80% for all modules

### Coverage by Module (Target)
- `ui/` - 75%
- `ui/widgets/` - 85%
- `core/` - 90%
- `services/` - 85%
- `controllers/` - 80%

## Summary

The unit tests are significantly out of date due to architectural changes. The immediate priority is fixing the 40% of tests that won't even import. After that, new tests need to be created for the split-pane architecture and command system. Finally, existing tests should be updated to properly test the new architecture rather than just mocking everything.

The test suite needs a comprehensive overhaul to match the current codebase architecture and provide meaningful coverage of the application's functionality.