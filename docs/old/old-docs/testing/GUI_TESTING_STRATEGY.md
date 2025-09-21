# GUI Testing Strategy for ViloApp

## Overview

This document outlines the comprehensive GUI testing strategy for ViloApp, built using pytest-qt to test PySide6 components with real user interactions.

## Testing Philosophy

Our GUI testing approach focuses on:

1. **Real User Interactions**: Testing actual mouse clicks, keyboard input, and visual feedback
2. **Component Integration**: Ensuring UI components work together seamlessly
3. **Visual State Verification**: Confirming UI state changes are visually correct
4. **Performance Under Interaction**: Ensuring smooth performance during user interactions
5. **Accessibility**: Verifying keyboard navigation and screen reader compatibility

## Architecture

### Test Structure

```
tests/gui/
├── __init__.py                 # GUI test package
├── conftest.py                 # GUI-specific fixtures and utilities
├── base.py                     # Base classes for GUI tests
├── test_main_window_gui.py     # Main window GUI tests
├── test_activity_bar_gui.py    # Activity bar interaction tests
├── test_sidebar_gui.py         # Sidebar GUI tests
└── test_workspace_gui.py       # Workspace GUI tests
```

### Base Classes Hierarchy

```
GUITestBase                     # Core GUI testing utilities
├── MainWindowGUITestBase      # Main window specific helpers
├── ActivityBarGUITestBase     # Activity bar specific helpers
├── SidebarGUITestBase         # Sidebar specific helpers
├── WorkspaceGUITestBase       # Workspace specific helpers
├── KeyboardGUITestBase        # Keyboard interaction helpers
├── MouseGUITestBase           # Mouse interaction helpers
├── ThemeGUITestBase           # Theme testing helpers
└── AnimationGUITestBase       # Animation testing helpers
```

## Test Categories

### 1. Component Display Tests (`@pytest.mark.gui`)

Test basic component rendering and initial states:

- Component visibility and dimensions
- Initial property values
- Layout correctness
- Visual hierarchy

**Example:**
```python
@pytest.mark.gui
def test_activity_bar_displays_correctly(self, gui_activity_bar, qtbot):
    """Test activity bar displays with all buttons visible."""
    assert gui_activity_bar.isVisible()
    assert gui_activity_bar.orientation() == Qt.Orientation.Vertical
    
    buttons = self.get_activity_buttons(gui_activity_bar)
    for view_name, button in buttons.items():
        assert button is not None
        assert button.isEnabled()
```

### 2. Mouse Interaction Tests (`@pytest.mark.mouse`)

Test mouse-based user interactions:

- Button clicking
- Context menus
- Drag and drop
- Hover effects
- Double-click actions

**Example:**
```python
@pytest.mark.gui
@pytest.mark.mouse
def test_click_search_button(self, mock_execute, gui_activity_bar, qtbot):
    """Test clicking search button changes view and triggers signal."""
    with qtbot.waitSignal(gui_activity_bar.view_changed, timeout=1000) as blocker:
        self.click_activity_button(qtbot, gui_activity_bar, "search")
    
    assert blocker.args == ["search"]
    assert gui_activity_bar.current_view == "search"
```

### 3. Keyboard Interaction Tests (`@pytest.mark.keyboard`)

Test keyboard navigation and shortcuts:

- Shortcut key combinations
- Tab navigation
- Focus management
- Accessibility keys

**Example:**
```python
@pytest.mark.gui
@pytest.mark.keyboard
def test_keyboard_shortcut_toggle_sidebar(self, mock_execute, gui_main_window, qtbot):
    """Test Ctrl+B keyboard shortcut toggles sidebar."""
    qtbot.keyClick(gui_main_window, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
    mock_execute.assert_called_with("workbench.action.toggleSidebar")
```

### 4. Animation Tests (`@pytest.mark.animation`)

Test UI animations and transitions:

- Sidebar collapse/expand
- Theme transitions
- Loading animations
- Smooth state changes

**Example:**
```python
@pytest.mark.gui
@pytest.mark.animation
def test_sidebar_collapse_animation(self, gui_sidebar, qtbot):
    """Test sidebar collapse animation works correctly."""
    gui_sidebar.collapse()
    self.wait_for_sidebar_animation(qtbot, gui_sidebar)
    self.verify_sidebar_collapsed(gui_sidebar)
```

### 5. Theme Tests (`@pytest.mark.theme`)

Test theme switching and visual consistency:

- Theme toggle functionality
- Icon updates across themes
- Visual consistency
- Theme persistence

**Example:**
```python
@pytest.mark.gui
@pytest.mark.theme
def test_activity_bar_icon_updates_on_theme_change(self, gui_activity_bar, qtbot, mock_icon_manager):
    """Test activity bar icons update when theme changes."""
    gui_activity_bar.update_icons()
    
    expected_icons = ["explorer", "search", "git", "settings"]
    actual_calls = [call[0][0] for call in mock_icon_manager.get_icon.call_args_list]
    
    for expected_icon in expected_icons:
        assert expected_icon in actual_calls
```

### 6. Integration Tests (`@pytest.mark.integration`)

Test component interactions:

- Activity bar ↔ Sidebar synchronization
- Command system integration
- Focus management between components
- Signal/slot connections

### 7. Performance Tests (`@pytest.mark.performance`)

Test GUI performance under various conditions:

- Rapid user interactions
- Multiple component updates
- Animation performance
- Resource usage

### 8. Accessibility Tests (`@pytest.mark.accessibility`)

Test accessibility features:

- Keyboard navigation
- Screen reader compatibility
- Focus indicators
- ARIA attributes

## Key Testing Patterns

### 1. Signal Testing with pytest-qt

```python
with qtbot.waitSignal(widget.signal_name, timeout=1000) as blocker:
    # Trigger action that should emit signal
    widget.trigger_action()

# Verify signal was emitted with correct arguments
assert blocker.args == expected_args
```

### 2. Animation Testing

```python
def test_animation(self, widget, qtbot):
    # Record initial state
    initial_value = widget.property_value
    
    # Trigger animation
    widget.start_animation()
    
    # Wait for animation to complete
    self.wait_for_animation(qtbot, timeout=2000)
    
    # Verify final state
    assert widget.property_value != initial_value
```

### 3. Theme Testing

```python
def test_theme_change(self, widget, qtbot, mock_icon_manager):
    # Setup initial theme state
    self.setup_theme_test(qtbot, widget)
    
    # Trigger theme change
    self.trigger_theme_toggle(qtbot, widget)
    
    # Verify theme propagation
    self.verify_theme_change_propagated(widget, mock_icon_manager)
```

### 4. Integration Testing

```python
def test_component_integration(self, gui_main_window, qtbot):
    activity_bar = gui_main_window.activity_bar
    sidebar = gui_main_window.sidebar
    
    # Test interaction between components
    with qtbot.waitSignal(activity_bar.view_changed):
        self.click_activity_button(qtbot, activity_bar, "search")
    
    # Verify integration effect
    assert sidebar.current_view == "search"  # If integrated correctly
```

## Fixtures and Utilities

### Core Fixtures

- `gui_main_window`: Fully initialized main window with mocked dependencies
- `gui_activity_bar`: Activity bar from main window
- `gui_sidebar`: Sidebar from main window
- `gui_workspace`: Workspace from main window
- `mock_icon_manager`: Mocked icon manager to avoid resource loading

### Utility Functions

- `wait_for_condition()`: Wait for arbitrary conditions with good error reporting
- `simulate_key_sequence()`: Simulate keyboard shortcuts
- `get_widget_center()`: Get center point of widget for clicking
- `wait_for_animation()`: Wait for animations to complete

## Running GUI Tests

### Basic Test Execution

```bash
# Run all GUI tests
pytest tests/gui/ -v

# Run specific test categories
pytest tests/gui/ -m gui -v
pytest tests/gui/ -m "gui and mouse" -v
pytest tests/gui/ -m "gui and keyboard" -v
pytest tests/gui/ -m "gui and animation" -v

# Run with coverage
pytest tests/gui/ --cov=ui --cov-report=html -v

# Run headless (on Linux with xvfb)
pytest tests/gui/ --xvfb-width=1280 --xvfb-height=720 -v
```

### Test Environment Setup

```bash
# Install GUI test dependencies
pip install pytest pytest-qt pytest-xvfb

# For headless testing on Linux
sudo apt-get install xvfb

# Run with virtual display
xvfb-run -a pytest tests/gui/ -v
```

## Best Practices

### 1. Use Real User Interactions

```python
# ✅ Good - Real user interaction
qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

# ❌ Avoid - Direct method calls
button.click()
```

### 2. Wait for UI Updates

```python
# ✅ Good - Wait for signals
with qtbot.waitSignal(widget.signal, timeout=1000):
    widget.trigger_action()

# ✅ Good - Wait for conditions
qtbot.waitUntil(lambda: widget.isVisible(), timeout=5000)
```

### 3. Test Visual States

```python
# ✅ Good - Verify actual visual state
assert widget.isVisible()
assert widget.width() > 0

# ❌ Insufficient - Only test internal state
assert widget._is_visible
```

### 4. Mock External Dependencies

```python
# ✅ Good - Mock heavy resources
@patch('ui.activity_bar.get_icon_manager')
def test_with_mocked_icons(self, mock_icon_manager, gui_activity_bar, qtbot):
    # Test without loading actual icon files
```

### 5. Use Appropriate Timeouts

```python
# ✅ Good - Reasonable timeouts
qtbot.waitSignal(widget.signal, timeout=1000)  # 1 second for signals
qtbot.waitUntil(condition, timeout=5000)       # 5 seconds for conditions
self.wait_for_animation(qtbot, timeout=2000)   # 2 seconds for animations
```

## Troubleshooting Common Issues

### 1. Timing Issues

**Problem**: Tests fail intermittently due to timing
**Solution**: Use `qtbot.waitSignal()` and `qtbot.waitUntil()` instead of `QTest.qWait()`

### 2. Widget Not Found

**Problem**: Cannot find widget to interact with
**Solution**: Ensure widget is visible and added to qtbot: `qtbot.addWidget(widget)`

### 3. Animation Tests Flaky

**Problem**: Animation tests fail due to timing
**Solution**: Use longer timeouts and verify end state rather than intermediate states

### 4. Focus Issues

**Problem**: Keyboard shortcuts don't work
**Solution**: Ensure widget has focus: `widget.setFocus()` then `qtbot.waitUntil(lambda: widget.hasFocus())`

### 5. Signal Not Emitted

**Problem**: `waitSignal` times out
**Solution**: Verify signal connection and that the action actually triggers the signal

## Future Enhancements

1. **Visual Regression Testing**: Add screenshot comparison for visual changes
2. **Cross-Platform Testing**: Ensure tests work on Windows, macOS, and Linux
3. **Mobile/Touch Testing**: Add touch interaction testing for tablet interfaces
4. **Performance Profiling**: Add automated performance regression detection
5. **Accessibility Automation**: Integrate with accessibility testing tools

## Conclusion

This GUI testing strategy provides comprehensive coverage of user interactions in ViloApp. By focusing on real user interactions, visual state verification, and component integration, we ensure that the GUI behaves correctly from the user's perspective while maintaining good performance and accessibility.