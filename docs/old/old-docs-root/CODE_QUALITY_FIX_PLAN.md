# Code Quality Fix Implementation Plan

## Overview
This plan addresses all critical, major, and minor issues identified in the code quality audit performed on 2025-09-15. The plan is organized into 4 phases with clear priorities and measurable outcomes.

## Current State
- **Architecture Compliance**: 65% (Target: 95%)
- **ServiceLocator Violations**: 26+ instances in UI layer
- **Bare Exception Handlers**: 20+ instances
- **Oversized Files**: 6 files >800 LOC
- **Test Coverage**: ~30% (Target: 80%)

## Phase 1: Critical Architecture Violations (Week 1)
**Goal**: Remove all ServiceLocator usage from UI layer and restore Command Pattern integrity

### 1.1 ServiceLocator Removal Campaign
**Priority**: P0 - CRITICAL
**Effort**: 2-3 days
**Files to Fix**:
1. `ui/workspace.py` (lines 97-100)
2. `ui/widgets/shortcut_config_app_widget.py` (line 157)
3. `ui/command_palette/palette_controller.py` (line 45)
4. `ui/widgets/theme_editor_widget.py`
5. `ui/widgets/settings_app_widget.py`
6. All remaining UI components (23+ files)

**Implementation Strategy**:
```python
# BEFORE (Wrong):
from services.service_locator import ServiceLocator
service_locator = ServiceLocator()
service = service_locator.get_service(SomeService)
result = service.do_something(args)

# AFTER (Correct):
from core.commands.executor import execute_command
result = execute_command("category.action.doSomething", **args)
```

**Required New Commands**:
- `workspace.widget.register`
- `workspace.widget.unregister`
- `workspace.widget.focus`
- `theme.apply`
- `theme.save`
- `settings.update`

### 1.2 Exception Handling Fixes
**Priority**: P0 - CRITICAL
**Effort**: 1-2 days
**Files to Fix**:
1. `services/state_service.py:425` - Critical bare except
2. `core/environment_detector.py:64` - File system errors
3. All other bare except handlers (18+ locations)

**Implementation Pattern**:
```python
# BEFORE (Wrong):
try:
    dangerous_operation()
except:
    pass  # Silent failure

# AFTER (Correct):
try:
    dangerous_operation()
except (SpecificError, AnotherError) as e:
    logger.error(f"Operation failed: {e}")
    # Proper error handling or re-raise
    raise OperationError(f"Failed to complete operation: {e}")
```

### 1.3 Architectural Compliance Testing
**Priority**: P0 - CRITICAL
**Effort**: 1 day
**Deliverables**:
- Create `tests/architecture/test_no_service_locator_in_ui.py`
- Create `tests/architecture/test_command_pattern_compliance.py`
- Add to CI/CD pipeline to prevent regressions

**Test Example**:
```python
def test_no_service_locator_in_ui():
    """Ensure UI components don't use ServiceLocator."""
    ui_files = glob.glob("ui/**/*.py", recursive=True)
    violations = []

    for file_path in ui_files:
        with open(file_path, 'r') as f:
            content = f.read()
            if 'ServiceLocator' in content:
                violations.append(file_path)

    assert not violations, f"ServiceLocator found in UI files: {violations}"
```

## Phase 2: Major Refactoring (Week 2)
**Goal**: Break down oversized files and establish proper boundaries

### 2.1 Split Oversized Files
**Priority**: P1 - HIGH
**Effort**: 3-4 days

#### File: `ui/widgets/split_pane_widget.py` (1,044 LOC)
**Refactor into**:
- `split_pane_widget.py` (300 LOC) - Main widget
- `split_pane_model.py` (200 LOC) - Data model
- `split_pane_controller.py` (200 LOC) - Logic controller
- `split_pane_view_helpers.py` (200 LOC) - View utilities
- `split_pane_drag_handler.py` (144 LOC) - Drag operations

#### File: `ui/widgets/theme_editor_widget.py` (956 LOC)
**Refactor into**:
- `theme_editor_widget.py` (300 LOC) - Main widget
- `theme_editor_controls.py` (300 LOC) - Control panels
- `theme_preview_widget.py` (200 LOC) - Preview component
- `theme_persistence.py` (156 LOC) - Save/load logic

#### File: `ui/main_window.py` (937 LOC)
**Refactor into**:
- `main_window.py` (400 LOC) - Main window
- `main_window_layout.py` (200 LOC) - Layout management
- `main_window_actions.py` (200 LOC) - Action handlers
- `main_window_state.py` (137 LOC) - State management

#### File: `services/workspace_service.py` (885 LOC)
**Refactor into**:
- `workspace_service.py` (300 LOC) - Core service
- `workspace_tab_manager.py` (250 LOC) - Tab operations
- `workspace_pane_manager.py` (200 LOC) - Pane operations
- `workspace_widget_registry.py` (135 LOC) - Widget tracking

### 2.2 Input Validation Framework
**Priority**: P1 - HIGH
**Effort**: 2 days
**Deliverables**:
- Create `core/commands/validation.py` with validation decorators
- Add validation to all command parameters
- Create validation test suite

**Implementation**:
```python
@command(id="workspace.action.splitPane")
@validate_params({
    'direction': OneOf(['horizontal', 'vertical']),
    'ratio': Range(0.1, 0.9),
    'pane_id': Optional(String())
})
def split_pane_command(context: CommandContext) -> CommandResult:
    # Parameters are pre-validated
    pass
```

## Phase 3: Quality Improvements (Week 3)
**Goal**: Enhance error handling, testing, and monitoring

### 3.1 Consistent Error Propagation
**Priority**: P2 - MEDIUM
**Effort**: 2 days
**Strategy**:
- Services always raise exceptions on errors
- Commands catch and convert to CommandResult
- UI shows user-friendly error messages

### 3.2 Resource Leak Prevention
**Priority**: P2 - MEDIUM
**Effort**: 1 day
**Focus Areas**:
- Widget pooling cleanup
- Terminal session management
- File handle management
- Timer and signal cleanup

### 3.3 Enhanced Test Coverage
**Priority**: P2 - MEDIUM
**Effort**: 3 days
**Targets**:
- Increase coverage from ~30% to 50%
- Add integration tests for all commands
- Add performance benchmarks
- Add memory leak detection tests

## Phase 4: Prevention & Monitoring (Week 4)
**Goal**: Prevent future violations and establish quality gates

### 4.1 Linting Rules
**Priority**: P3 - LOW
**Effort**: 1 day
**Deliverables**:
- Custom pylint rules for architecture compliance
- Pre-commit hooks for validation
- IDE integration for real-time feedback

### 4.2 CI/CD Quality Gates
**Priority**: P3 - LOW
**Effort**: 1 day
**Gates**:
- Architecture compliance tests must pass
- No new ServiceLocator violations
- No bare exception handlers
- File size limits enforced
- Cyclomatic complexity limits

### 4.3 Documentation Updates
**Priority**: P3 - LOW
**Effort**: 1 day
**Updates**:
- Architecture guidelines in CLAUDE.md
- Command creation guide
- Service development guide
- Testing best practices

## Success Metrics

### Week 1 Targets
- [ ] ServiceLocator violations: 0 (from 26+)
- [ ] Bare exception handlers: 0 (from 20+)
- [ ] Architecture compliance tests: 100% passing

### Week 2 Targets
- [ ] Files >800 LOC: 0 (from 6)
- [ ] Command validation: 100% coverage
- [ ] Average file size: <400 LOC

### Week 3 Targets
- [ ] Test coverage: 50% (from 30%)
- [ ] Error handling consistency: 100%
- [ ] Resource leak tests: 100% passing

### Week 4 Targets
- [ ] CI/CD gates: All active
- [ ] Architecture compliance: 95% (from 65%)
- [ ] Technical debt ratio: <10% (from 15%)

## Implementation Order

### Day 1-2: Critical ServiceLocator Removal
1. Start with `ui/workspace.py` (most central)
2. Fix `ui/command_palette/palette_controller.py`
3. Fix `ui/widgets/shortcut_config_app_widget.py`
4. Create missing commands as needed

### Day 3: Exception Handling
1. Fix `services/state_service.py`
2. Fix `core/environment_detector.py`
3. Audit and fix remaining handlers

### Day 4: Architecture Tests
1. Create compliance test suite
2. Add to CI/CD pipeline
3. Run and fix any failures

### Day 5-8: File Refactoring
1. Split `split_pane_widget.py` first (most complex)
2. Split `theme_editor_widget.py`
3. Split `main_window.py`
4. Split `workspace_service.py`

### Day 9-10: Validation Framework
1. Create validation decorators
2. Apply to all commands
3. Test validation logic

### Day 11-15: Quality & Prevention
1. Error propagation patterns
2. Resource leak fixes
3. Test coverage increase
4. Linting and CI/CD setup

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**:
- Run full test suite after each change
- Use feature flags for gradual rollout
- Keep backup of working state

### Risk 2: Performance Regression
**Mitigation**:
- Benchmark before and after refactoring
- Profile critical paths
- Optimize only after correctness

### Risk 3: Scope Creep
**Mitigation**:
- Stick to defined phases
- Defer nice-to-have features
- Time-box each task

## Tools & Scripts Needed

### Architecture Validator Script
```bash
#!/bin/bash
# validate_architecture.sh
echo "Checking for ServiceLocator in UI..."
grep -r "ServiceLocator" ui/ --include="*.py" && exit 1
echo "✓ No ServiceLocator violations found"

echo "Checking for bare exceptions..."
grep -r "except:" . --include="*.py" && exit 1
echo "✓ No bare exception handlers found"

echo "Checking file sizes..."
find . -name "*.py" -exec wc -l {} \; | awk '$1 > 800 {print}' | grep . && exit 1
echo "✓ All files within size limits"
```

### Progress Tracker
```python
# track_progress.py
def check_progress():
    metrics = {
        'service_locator_violations': count_service_locator(),
        'bare_exceptions': count_bare_exceptions(),
        'oversized_files': count_oversized_files(),
        'test_coverage': get_test_coverage(),
        'architecture_compliance': calculate_compliance()
    }

    print(f"Progress Report:")
    print(f"ServiceLocator: {metrics['service_locator_violations']} violations")
    print(f"Exceptions: {metrics['bare_exceptions']} bare handlers")
    print(f"Large Files: {metrics['oversized_files']} files >800 LOC")
    print(f"Test Coverage: {metrics['test_coverage']}%")
    print(f"Compliance: {metrics['architecture_compliance']}%")
```

## Conclusion

This plan provides a systematic approach to addressing all code quality issues identified in the audit. By following this phased approach, we can improve the codebase from a C+ grade to an A- grade within 4 weeks, while maintaining application stability and preventing regressions.

The key to success is:
1. Fix critical architecture violations first
2. Refactor incrementally with tests
3. Establish prevention mechanisms
4. Monitor progress continuously

With disciplined execution of this plan, ViloxTerm will have a robust, maintainable, and architecturally sound codebase.