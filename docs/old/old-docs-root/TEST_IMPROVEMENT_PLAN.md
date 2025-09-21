# Test Coverage Improvement Plan

## Current State (Grade: D+)
- **Test Coverage**: 25.5% of changed files have tests
- **Qt Compliance**: 62 hardcoded delay violations
- **Critical Issues**: Core components completely untested
- **Quality Issues**: Weak assertions, missing edge cases

## Target State (Grade: B+)
- **Test Coverage**: 80%+ for all changed files
- **Qt Compliance**: 100% proper patterns
- **Complete Coverage**: All critical components tested
- **Quality**: Strong assertions, comprehensive edge cases

## Implementation Phases

### Phase 1: Critical Infrastructure Fixes (Days 1-3)
**Goal**: Fix broken tests and create tests for core components

#### Day 1: Fix Immediate Issues
1. **Fix broken imports** (2 files) - Quick wins
   - `tests/unit/test_workspace.py` - Update import from `ui.workspace_simple` to correct module
   - `tests/gui/test_keyboard_shortcuts_gui.py` - Fix ShortcutManager import

2. **Create CommandExecutor tests** - Critical component
   ```python
   # tests/unit/test_command_executor.py
   - Test command registration
   - Test command execution with context
   - Test parameter validation integration
   - Test error handling and rollback
   - Test command not found scenarios
   ```

#### Day 2: Service Layer Testing
3. **Create WorkspaceService tests** - Core service
   ```python
   # tests/unit/test_workspace_service.py
   - Test tab management (add, remove, switch)
   - Test pane operations (split, close, navigate)
   - Test widget registry operations
   - Test state persistence
   - Test error conditions
   ```

4. **Create Terminal Widget tests** - Critical UI component
   ```python
   # tests/gui/test_terminal_widget.py
   - Test session lifecycle (create, ready, close)
   - Test input/output operations
   - Test signal emissions
   - Test cleanup and resource management
   - Test error handling
   ```

#### Day 3: Refactored Components
5. **Test split_pane_widget.py** - Recently refactored
   ```python
   # tests/gui/test_split_pane_widget.py
   - Test splitting operations (horizontal/vertical)
   - Test ratio management
   - Test focus navigation
   - Test signal emissions on split/close
   - Test recursive operations
   ```

6. **Test theme_editor_widget.py** - Recently refactored
   ```python
   # tests/gui/test_theme_editor_widget.py
   - Test theme loading and saving
   - Test color picker integration
   - Test preview updates
   - Test import/export functionality
   - Test validation
   ```

### Phase 2: Qt/PySide6 Compliance (Days 4-6)
**Goal**: Fix all Qt anti-patterns and add proper signal testing

#### Day 4: Replace Hardcoded Delays
7. **Fix 62 QTest.qWait violations**
   ```python
   # BEFORE:
   QTest.qWait(50)

   # AFTER:
   qtbot.waitUntil(lambda: widget.is_ready(), timeout=1000)
   # OR
   qtbot.wait(50)  # For unavoidable waits
   ```

   Files to fix:
   - All files in `tests/gui/`
   - Terminal tests
   - Animation tests

#### Day 5: Add Signal Testing
8. **Add comprehensive signal testing**
   ```python
   # Pattern to implement:
   def test_widget_signals(qtbot):
       widget = MyWidget()
       qtbot.addWidget(widget)

       with qtbot.wait_signal(widget.dataChanged, timeout=1000) as blocker:
           widget.update_data("test")
       assert blocker.args == ["test"]
   ```

   Components needing signal tests:
   - SplitPaneWidget (pane_split, pane_closed signals)
   - Workspace (tab_changed, tab_closed signals)
   - TerminalWidget (session_started, session_ended signals)
   - CommandPalette (command_selected signal)

#### Day 6: Modal Dialog Mocking
9. **Add proper modal dialog mocking**
   ```python
   # Pattern to implement:
   def test_dialog_interaction(qtbot, monkeypatch):
       # Mock the exec method
       monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Yes)

       result = widget.show_confirmation()
       assert result is True
   ```

### Phase 3: Quality Improvements (Days 7-9)
**Goal**: Improve assertion quality and add edge cases

#### Day 7: Replace Weak Assertions
10. **Fix weak assertions in 15+ files**
    ```python
    # BEFORE:
    assert widget is not None
    assert widget

    # AFTER:
    assert widget.isVisible() is True
    assert widget.width() == 640
    assert widget.get_tab_count() == 3
    assert isinstance(widget.current_widget(), TerminalWidget)
    ```

#### Day 8: Add Edge Case Testing
11. **Implement comprehensive edge case testing**
    ```python
    @pytest.mark.parametrize("input,expected_error", [
        ("", ValueError),           # Empty input
        (None, TypeError),          # Null input
        ("x" * 1001, ValueError),   # Too long
        (-1, ValueError),           # Negative
        (sys.maxsize, ValueError),  # Max value
        ("../../etc/passwd", SecurityError),  # Path traversal
    ])
    def test_validation_edge_cases(input, expected_error):
        with pytest.raises(expected_error):
            validate_input(input)
    ```

#### Day 9: Error Path Coverage
12. **Add error path testing**
    ```python
    def test_error_conditions():
        # Test service unavailable
        mock_context.get_service.return_value = None
        result = command(mock_context)
        assert result.success is False
        assert "service unavailable" in result.error

        # Test invalid parameters
        result = command(mock_context, invalid_param=999)
        assert result.success is False

        # Test resource exhaustion
        with pytest.raises(ResourceError):
            for _ in range(1000):
                create_resource()
    ```

### Phase 4: Integration and Coverage (Days 10-12)
**Goal**: Create integration tests and achieve coverage targets

#### Day 10: Service Integration Tests
13. **Create service integration tests**
    ```python
    # tests/integration/test_service_integration.py
    - Test WorkspaceService + UIService interaction
    - Test StateService persistence across services
    - Test ThemeService + UIService updates
    - Test command execution through full stack
    ```

#### Day 11: Command Validation Framework Tests
14. **Test the validation framework**
    ```python
    # tests/unit/test_command_validation_framework.py
    - Test all validator types
    - Test validation decorator
    - Test integration with executor
    - Test error messages
    - Test custom validators
    ```

#### Day 12: Coverage Gap Analysis
15. **Fill remaining coverage gaps**
    - Run coverage report
    - Identify untested code paths
    - Add targeted tests for gaps
    - Ensure 80%+ coverage for critical components

## Success Metrics

### Week 1 Targets
- [ ] All broken tests fixed
- [ ] CommandExecutor fully tested
- [ ] WorkspaceService fully tested
- [ ] 30 hardcoded delays replaced

### Week 2 Targets
- [ ] All 62 hardcoded delays replaced
- [ ] Signal testing added to 5+ components
- [ ] All weak assertions replaced
- [ ] Edge cases covered for validation

### Final Targets
- [ ] Test coverage: 80%+ for changed files
- [ ] Qt compliance: 100%
- [ ] Zero weak assertions
- [ ] All critical paths tested
- [ ] Grade improved from D+ to B+

## Testing Commands

### Daily Testing Workflow
```bash
# 1. Check current state
python scripts/test_review.py --since HEAD~1

# 2. Run tests for changed files
pytest tests/ -k "test_name" -v

# 3. Check Qt compliance
pytest tests/gui/ --qt-api=pyside6 -v

# 4. Generate coverage report
pytest --cov=core --cov=services --cov=ui --cov-report=html

# 5. Validate improvements
@agent-test-guardian review
```

## Priority Order

### Critical (Must Fix First)
1. Broken test imports - Blocks other testing
2. CommandExecutor tests - Core functionality
3. WorkspaceService tests - Critical service

### High Priority
4. Replace hardcoded delays - Improves reliability
5. Terminal widget tests - User-facing critical component
6. Signal testing - Qt best practice

### Medium Priority
7. Weak assertion replacement - Code quality
8. Edge case testing - Robustness
9. Error path coverage - Reliability

### Lower Priority
10. Integration tests - Nice to have
11. Full coverage gaps - Diminishing returns

## Resource Requirements

### Time Estimate
- **Phase 1**: 3 days (Critical infrastructure)
- **Phase 2**: 3 days (Qt compliance)
- **Phase 3**: 3 days (Quality improvements)
- **Phase 4**: 3 days (Integration and coverage)
- **Total**: 12 days to achieve B+ grade

### Tools Needed
- pytest-qt for GUI testing
- pytest-cov for coverage
- pytest-mock for mocking
- Test Guardian for validation

## Risk Mitigation

### Risk: Breaking existing functionality
**Mitigation**: Run full test suite after each change

### Risk: Time overrun
**Mitigation**: Focus on critical paths first, defer nice-to-haves

### Risk: Complex Qt testing
**Mitigation**: Use established patterns from qt_testing_patterns.py

## Monitoring Progress

### Daily Checks
```bash
# Check test count
pytest --collect-only | grep "test session starts"

# Check coverage trend
pytest --cov --cov-report=term-missing | grep TOTAL

# Check Qt compliance
grep -r "QTest.qWait" tests/ | wc -l  # Should decrease daily
```

### Weekly Review
```bash
# Run Test Guardian
@agent-test-guardian review --comprehensive

# Generate progress report
python scripts/test_review.py --since HEAD~7 --json > week_report.json
```

## Conclusion

This plan provides a systematic approach to improving test coverage from the current D+ grade to B+ within 12 days. By focusing on critical components first and following Qt best practices, we can ensure the ViloxTerm codebase has robust test coverage that matches its excellent architecture.

The key to success:
1. Fix broken tests immediately (quick wins)
2. Test critical components first
3. Follow Qt/PySide6 best practices
4. Use strong assertions
5. Cover edge cases and error paths

With disciplined execution, we can achieve 80%+ test coverage and ensure code reliability.