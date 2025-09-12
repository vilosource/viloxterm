# GUI Test Patterns for ViloApp

## Overview

This document provides detailed patterns and examples for writing effective GUI tests using pytest-qt in ViloApp. These patterns are proven approaches that ensure reliable, maintainable GUI tests.

## Core Testing Patterns

### 1. Signal-Driven Testing Pattern

**Use Case**: Testing component communication and event handling

**Pattern Structure**:
```python
with qtbot.waitSignal(component.signal_name, timeout=1000) as blocker:
    # Trigger action that should emit signal
    trigger_action()

# Verify signal was emitted with expected arguments
assert blocker.args == expected_values
```

**Example**:
```python
def test_activity_bar_view_change_signal(self, gui_activity_bar, qtbot):
    """Test activity bar emits view_changed signal when button is clicked."""
    with qtbot.waitSignal(gui_activity_bar.view_changed, timeout=1000) as blocker:
        self.click_activity_button(qtbot, gui_activity_bar, "search")
    
    # Verify signal emitted with correct view name
    assert blocker.args == ["search"]
    assert gui_activity_bar.current_view == "search"
```

**Benefits**:
- Tests actual signal/slot communication
- Ensures loose coupling between components
- Verifies event-driven architecture

### 2. State Verification Pattern

**Use Case**: Testing UI state changes after interactions

**Pattern Structure**:
```python
# Record initial state
initial_state = get_widget_state(widget)

# Perform action
perform_user_action()

# Verify state change
final_state = get_widget_state(widget)
assert final_state != initial_state
assert final_state == expected_state
```

**Example**:
```python
def test_sidebar_toggle_state_change(self, gui_sidebar, qtbot):
    """Test sidebar toggle changes visual and internal state."""
    # Record initial state
    initial_collapsed = gui_sidebar.is_collapsed
    initial_width = gui_sidebar.width()
    
    # Trigger toggle
    gui_sidebar.toggle()
    self.wait_for_sidebar_animation(qtbot, gui_sidebar)
    
    # Verify state changed
    assert gui_sidebar.is_collapsed != initial_collapsed
    if gui_sidebar.is_collapsed:
        assert gui_sidebar.width() < initial_width
    else:
        assert gui_sidebar.width() >= initial_width
```

### 3. Animation Testing Pattern

**Use Case**: Testing smooth transitions and animations

**Pattern Structure**:
```python
# Setup initial state
setup_animation_start_state()

# Trigger animation
start_animation()

# Wait for animation completion
wait_for_animation_complete()

# Verify final state
assert_animation_end_state()
```

**Example**:
```python
def test_sidebar_collapse_animation_smooth(self, gui_sidebar, qtbot):
    """Test sidebar collapse animation completes smoothly."""
    # Ensure expanded state
    if gui_sidebar.is_collapsed:
        gui_sidebar.expand()
        self.wait_for_sidebar_animation(qtbot, gui_sidebar)
    
    # Record initial state
    initial_width = gui_sidebar.width()
    assert initial_width > 0
    
    # Start animation
    gui_sidebar.collapse()
    
    # Verify animation started
    assert gui_sidebar.animation.state() == gui_sidebar.animation.State.Running
    
    # Wait for completion
    self.wait_for_sidebar_animation(qtbot, gui_sidebar, timeout=2000)
    
    # Verify final state
    assert gui_sidebar.is_collapsed
    assert gui_sidebar.animation.state() == gui_sidebar.animation.State.Stopped
```

### 4. Command Integration Pattern

**Use Case**: Testing GUI components integrate with command system

**Pattern Structure**:
```python
with patch('module.execute_command') as mock_execute:
    mock_execute.return_value = {'success': True}
    
    # Trigger GUI action
    perform_gui_action()
    
    # Verify command was executed
    mock_execute.assert_called_with("expected.command.id")
```

**Example**:
```python
@patch('ui.activity_bar.execute_command')
def test_activity_button_executes_command(self, mock_execute, gui_activity_bar, qtbot):
    """Test activity button click executes corresponding command."""
    mock_execute.return_value = {'success': True}
    
    # Click git button
    self.click_activity_button(qtbot, gui_activity_bar, "git")
    
    # Verify command execution
    mock_execute.assert_called_with("workbench.view.git")
    
    # Verify UI state updated
    assert gui_activity_bar.current_view == "git"
```

### 5. Multi-Component Integration Pattern

**Use Case**: Testing interactions between multiple UI components

**Pattern Structure**:
```python
# Setup multiple components
component_a = get_component_a()
component_b = get_component_b()

# Trigger action in component A
perform_action_on_component_a()

# Verify effect in component B
assert component_b.state == expected_state
```

**Example**:
```python
def test_activity_bar_sidebar_integration(self, gui_main_window, qtbot):
    """Test activity bar changes affect sidebar view."""
    activity_bar = gui_main_window.activity_bar
    sidebar = gui_main_window.sidebar
    
    # Record initial sidebar state
    initial_view_index = sidebar.stack.currentIndex()
    
    # Change activity view
    with qtbot.waitSignal(activity_bar.view_changed, timeout=1000):
        self.click_activity_button(qtbot, activity_bar, "search")
    
    # Verify sidebar was notified through main window connection
    # (The actual integration test would depend on the connection implementation)
    assert activity_bar.current_view == "search"
```

### 6. Keyboard Shortcut Testing Pattern

**Use Case**: Testing keyboard shortcuts and accessibility

**Pattern Structure**:
```python
# Focus target widget
widget.setFocus()
qtbot.waitUntil(lambda: widget.hasFocus(), timeout=1000)

# Send key combination
qtbot.keyClick(widget, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)

# Verify expected action occurred
assert expected_result()
```

**Example**:
```python
def test_ctrl_b_toggles_sidebar(self, gui_main_window, qtbot):
    """Test Ctrl+B keyboard shortcut toggles sidebar."""
    with patch('ui.main_window.execute_command') as mock_execute:
        mock_execute.return_value = {'success': True}
        
        # Focus main window
        gui_main_window.setFocus()
        
        # Send Ctrl+B
        qtbot.keyClick(gui_main_window, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(100)
        
        # Verify command was executed
        mock_execute.assert_called_with("workbench.action.toggleSidebar")
```

### 7. Theme Testing Pattern

**Use Case**: Testing visual consistency across theme changes

**Pattern Structure**:
```python
# Setup theme test with mocked dependencies
setup_theme_mocks()

# Record initial theme state
initial_theme_state = get_theme_state()

# Trigger theme change
trigger_theme_toggle()

# Verify theme propagation to all components
verify_theme_applied_to_all_components()
```

**Example**:
```python
def test_theme_toggle_updates_all_icons(self, gui_main_window, qtbot, mock_icon_manager):
    """Test theme toggle updates icons in all components."""
    # Setup initial theme
    mock_icon_manager.theme = "light"
    
    # Trigger theme toggle
    with patch('ui.main_window.execute_command') as mock_execute:
        mock_execute.return_value = {'success': True}
        
        self.trigger_theme_toggle(qtbot, gui_main_window)
        
        # Verify theme command executed
        mock_execute.assert_called_with("view.toggleTheme")
    
    # Verify icon manager was called for theme change
    mock_icon_manager.toggle_theme.assert_called()
```

### 8. Error Handling Pattern

**Use Case**: Testing GUI behavior during error conditions

**Pattern Structure**:
```python
# Setup error condition
setup_error_scenario()

# Trigger action that should handle error
perform_action_that_may_fail()

# Verify graceful error handling
assert_error_handled_gracefully()
assert_ui_remains_functional()
```

**Example**:
```python
def test_command_execution_error_handling(self, gui_activity_bar, qtbot):
    """Test activity bar handles command execution errors gracefully."""
    with patch('ui.activity_bar.execute_command') as mock_execute:
        # Simulate command execution error
        mock_execute.return_value = {'success': False, 'error': 'Command failed'}
        
        # Click button that executes command
        initial_view = gui_activity_bar.current_view
        self.click_activity_button(qtbot, gui_activity_bar, "git")
        
        # Verify error didn't break UI
        assert gui_activity_bar.isVisible()
        assert gui_activity_bar.isEnabled()
        
        # Verify UI state is consistent (behavior may vary based on implementation)
        current_view = gui_activity_bar.current_view
        assert current_view is not None
```

### 9. Performance Testing Pattern

**Use Case**: Testing GUI performance under load or rapid interactions

**Pattern Structure**:
```python
# Setup performance test
start_time = time.time()

# Perform rapid/heavy operations
for i in range(many_iterations):
    perform_operation()
    if i % check_interval == 0:
        assert_still_responsive()

# Verify performance within acceptable limits
end_time = time.time()
assert (end_time - start_time) < acceptable_time_limit
```

**Example**:
```python
def test_rapid_tab_switching_performance(self, gui_workspace, qtbot):
    """Test workspace handles rapid tab switching without performance issues."""
    tab_widget = gui_workspace.tab_widget
    
    if tab_widget.count() > 1:
        # Rapid switching test
        start_time = time.time()
        
        for cycle in range(20):  # 20 rapid cycles
            for tab_index in range(tab_widget.count()):
                tab_widget.setCurrentIndex(tab_index)
                QTest.qWait(5)  # Very brief wait
                
                # Check responsiveness every 10 operations
                if (cycle * tab_widget.count() + tab_index) % 10 == 0:
                    current_widget = tab_widget.currentWidget()
                    assert current_widget is not None
                    assert current_widget.isVisible()
        
        end_time = time.time()
        
        # Should complete within reasonable time (adjust based on needs)
        assert (end_time - start_time) < 10.0  # 10 seconds max
        
        # Final state should be consistent
        assert tab_widget.currentIndex() >= 0
        assert tab_widget.currentWidget() is not None
```

### 10. Accessibility Testing Pattern

**Use Case**: Testing keyboard navigation and screen reader compatibility

**Pattern Structure**:
```python
# Test keyboard navigation
widget.setFocus()
qtbot.waitUntil(lambda: widget.hasFocus())

# Test tab navigation
qtbot.keyClick(widget, Qt.Key.Key_Tab)
verify_focus_moved_correctly()

# Test accessibility attributes
assert_accessibility_attributes_present()
```

**Example**:
```python
def test_activity_bar_keyboard_accessibility(self, gui_activity_bar, qtbot):
    """Test activity bar is accessible via keyboard navigation."""
    # Focus activity bar
    gui_activity_bar.setFocus()
    qtbot.waitUntil(lambda: gui_activity_bar.hasFocus() or gui_activity_bar.isActiveWindow())
    
    # Test Tab navigation through buttons
    initial_focus = QApplication.focusWidget()
    
    qtbot.keyClick(gui_activity_bar, Qt.Key.Key_Tab)
    QTest.qWait(50)
    
    # Verify tab navigation works (focus may move to toolbar buttons)
    # Exact behavior depends on QToolBar implementation
    current_focus = QApplication.focusWidget()
    
    # Test that buttons have accessible text
    buttons = self.get_activity_buttons(gui_activity_bar)
    for view_name, button in buttons.items():
        assert button.text(), f"Button {view_name} should have accessible text"
```

## Advanced Patterns

### 1. Custom Wait Conditions

```python
def wait_for_custom_condition(self, qtbot, condition_func, timeout=5000):
    """Wait for custom condition with detailed error reporting."""
    def check_condition():
        try:
            result = condition_func()
            if not result:
                # Add debug information
                logger.debug(f"Condition not met: {condition_func}")
            return result
        except Exception as e:
            logger.error(f"Condition check failed: {e}")
            return False
    
    qtbot.waitUntil(check_condition, timeout=timeout)

# Usage
self.wait_for_custom_condition(
    qtbot,
    lambda: sidebar.width() == 0 and sidebar.is_collapsed,
    timeout=2000
)
```

### 2. Visual State Comparison

```python
def compare_widget_states(self, widget, expected_state):
    """Compare widget visual state with expected state."""
    actual_state = {
        'visible': widget.isVisible(),
        'enabled': widget.isEnabled(),
        'width': widget.width(),
        'height': widget.height(),
        'position': (widget.x(), widget.y())
    }
    
    for key, expected_value in expected_state.items():
        actual_value = actual_state.get(key)
        assert actual_value == expected_value, \
            f"Widget {key}: expected {expected_value}, got {actual_value}"
```

### 3. Signal Chain Testing

```python
def test_signal_chain(self, gui_main_window, qtbot):
    """Test signals propagate through component chain correctly."""
    activity_bar = gui_main_window.activity_bar
    
    # Setup signal monitoring
    signals_received = []
    
    def track_view_changed(view_name):
        signals_received.append(('view_changed', view_name))
    
    def track_toggle_sidebar():
        signals_received.append(('toggle_sidebar',))
    
    activity_bar.view_changed.connect(track_view_changed)
    activity_bar.toggle_sidebar.connect(track_toggle_sidebar)
    
    # Trigger action that should emit multiple signals
    self.click_activity_button(qtbot, activity_bar, "search")
    QTest.qWait(100)
    
    # Verify correct signals in correct order
    expected_signals = [('view_changed', 'search')]
    assert signals_received == expected_signals
```

## Anti-Patterns to Avoid

### 1. ❌ Direct Method Calls Instead of User Interactions

```python
# Bad - bypasses user interaction
button.click()

# Good - simulates real user action
qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
```

### 2. ❌ Fixed Sleep Instead of Proper Waiting

```python
# Bad - unreliable timing
time.sleep(0.5)
assert widget.isVisible()

# Good - wait for actual condition
qtbot.waitUntil(lambda: widget.isVisible(), timeout=1000)
```

### 3. ❌ Testing Internal Implementation Details

```python
# Bad - tests implementation
assert widget._internal_state == "collapsed"

# Good - tests user-visible behavior
assert not widget.isVisible() or widget.width() == 0
```

### 4. ❌ Ignoring Asynchronous Operations

```python
# Bad - doesn't wait for async operation
trigger_async_action()
assert result_is_ready()

# Good - waits for async completion
with qtbot.waitSignal(widget.operation_complete, timeout=5000):
    trigger_async_action()
assert result_is_ready()
```

### 5. ❌ Not Cleaning Up Resources

```python
# Bad - leaves widgets around
def test_creates_widget():
    widget = MyWidget()
    # widget not added to qtbot, may cause cleanup issues

# Good - proper cleanup
def test_creates_widget(qtbot):
    widget = MyWidget()
    qtbot.addWidget(widget)  # qtbot handles cleanup
```

## Debugging GUI Tests

### 1. Visual Debugging

```python
def debug_widget_state(self, widget, label="Widget"):
    """Print widget state for debugging."""
    print(f"\n{label} Debug Info:")
    print(f"  Visible: {widget.isVisible()}")
    print(f"  Enabled: {widget.isEnabled()}")
    print(f"  Size: {widget.width()}x{widget.height()}")
    print(f"  Position: ({widget.x()}, {widget.y()})")
    print(f"  Focus: {widget.hasFocus()}")
```

### 2. Screenshot on Failure

```python
def take_failure_screenshot(self, widget, test_name):
    """Take screenshot when test fails."""
    if hasattr(widget, 'grab'):
        pixmap = widget.grab()
        filename = f"/tmp/test_failure_{test_name}.png"
        pixmap.save(filename)
        print(f"Screenshot saved: {filename}")
```

## Conclusion

These patterns provide a solid foundation for writing reliable, maintainable GUI tests. By following these patterns and avoiding anti-patterns, you can create a comprehensive GUI test suite that accurately reflects user interactions and catches regressions early.