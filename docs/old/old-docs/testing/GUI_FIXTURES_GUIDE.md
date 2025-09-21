# GUI Test Fixtures Guide

## Overview

This guide explains all available GUI test fixtures in ViloApp's pytest-qt testing framework. These fixtures provide pre-configured components and utilities to make GUI testing efficient and reliable.

## Core GUI Fixtures

### Session-Level Fixtures

#### `qapp` (from main conftest.py)
**Scope**: Session  
**Purpose**: Provides a QApplication instance for the entire test session

```python
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()
```

**Usage**: Automatically available to all GUI tests. No need to request explicitly.

### Component Fixtures

#### `mock_icon_manager`
**Purpose**: Mocked icon manager to avoid loading actual icon resources during tests

```python
@pytest.fixture
def mock_icon_manager():
    """Mock icon manager for GUI tests to avoid resource loading issues."""
    with patch('ui.activity_bar.get_icon_manager') as mock_activity_bar, \
         patch('ui.main_window.get_icon_manager') as mock_main_window:
        
        mock_manager = Mock()
        mock_manager.theme = "light"
        mock_manager.get_icon.return_value = Mock()
        mock_manager.toggle_theme = Mock()
        mock_manager.detect_system_theme = Mock()
        
        mock_activity_bar.return_value = mock_manager
        mock_main_window.return_value = mock_manager
        
        yield mock_manager
```

**Usage**:
```python
def test_with_mocked_icons(self, mock_icon_manager, qtbot):
    # mock_icon_manager is automatically applied
    # No icon files will be loaded during test
    assert mock_icon_manager.theme == "light"
```

#### `gui_main_window`
**Purpose**: Fully initialized main window with all components ready for GUI testing

```python
@pytest.fixture
def gui_main_window(qtbot, mock_icon_manager):
    """Create a fully initialized main window for GUI testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    
    # Ensure the window is fully rendered
    QTest.qWait(100)
    
    return window
```

**Usage**:
```python
def test_main_window_functionality(self, gui_main_window, qtbot):
    # Window is fully initialized and visible
    assert gui_main_window.isVisible()
    assert gui_main_window.windowTitle() == "ViloApp"
    
    # All components are available
    assert gui_main_window.activity_bar is not None
    assert gui_main_window.sidebar is not None
    assert gui_main_window.workspace is not None
```

#### `gui_activity_bar`
**Purpose**: Activity bar component from the main window

```python
@pytest.fixture
def gui_activity_bar(gui_main_window):
    """Get activity bar from GUI main window."""
    return gui_main_window.activity_bar
```

**Usage**:
```python
def test_activity_bar_buttons(self, gui_activity_bar, qtbot):
    # Activity bar is ready for interaction
    assert gui_activity_bar.isVisible()
    
    # Test button clicking
    explorer_action = gui_activity_bar.explorer_action
    explorer_action.trigger()
```

#### `gui_sidebar`
**Purpose**: Sidebar component from the main window

```python
@pytest.fixture  
def gui_sidebar(gui_main_window):
    """Get sidebar from GUI main window."""
    return gui_main_window.sidebar
```

**Usage**:
```python
def test_sidebar_collapse(self, gui_sidebar, qtbot):
    # Sidebar is ready for testing
    assert gui_sidebar.isVisible()
    
    # Test collapse animation
    gui_sidebar.collapse()
    self.wait_for_sidebar_animation(qtbot, gui_sidebar)
    assert gui_sidebar.is_collapsed
```

#### `gui_workspace`
**Purpose**: Workspace component from the main window

```python
@pytest.fixture
def gui_workspace(gui_main_window):
    """Get workspace from GUI main window."""
    return gui_main_window.workspace
```

**Usage**:
```python
def test_workspace_tabs(self, gui_workspace, qtbot):
    # Workspace is ready with tabs
    tab_widget = gui_workspace.tab_widget
    assert tab_widget.count() >= 1
    
    # Test tab switching
    if tab_widget.count() > 1:
        tab_widget.setCurrentIndex(1)
```

#### `gui_status_bar`
**Purpose**: Status bar component from the main window

```python
@pytest.fixture
def gui_status_bar(gui_main_window):
    """Get status bar from GUI main window."""
    return gui_main_window.status_bar
```

**Usage**:
```python
def test_status_bar_display(self, gui_status_bar, qtbot):
    # Status bar is visible and functional
    assert gui_status_bar.isVisible()
    assert gui_status_bar.height() > 0
```

## Utility Fixtures and Functions

### Helper Functions (Available in tests/gui/conftest.py)

#### `wait_for_condition(qtbot, condition, timeout, interval)`
**Purpose**: Wait for arbitrary conditions with better error reporting

```python
def wait_for_condition(qtbot, condition, timeout=5000, interval=100):
    """
    Helper function to wait for a condition with better error reporting.
    
    Args:
        qtbot: pytest-qt bot
        condition: Callable that returns True when condition is met
        timeout: Maximum wait time in milliseconds
        interval: Check interval in milliseconds
    """
    def check_condition():
        try:
            return condition()
        except Exception as e:
            pytest.fail(f"Condition check failed: {e}")
    
    qtbot.waitUntil(check_condition, timeout=timeout)
```

**Usage**:
```python
def test_with_custom_condition(self, gui_sidebar, qtbot):
    gui_sidebar.collapse()
    
    # Wait for complex condition
    wait_for_condition(
        qtbot, 
        lambda: gui_sidebar.is_collapsed and gui_sidebar.width() < 10,
        timeout=3000
    )
```

#### `simulate_key_sequence(qtbot, widget, key_sequence)`
**Purpose**: Simulate keyboard shortcut sequences

```python
def simulate_key_sequence(qtbot, widget, key_sequence):
    """
    Simulate a keyboard shortcut sequence.
    
    Args:
        qtbot: pytest-qt bot
        widget: Target widget
        key_sequence: Key sequence string (e.g., "Ctrl+T")
    """
    from PySide6.QtGui import QKeySequence
    from PySide6.QtCore import Qt
    
    sequence = QKeySequence(key_sequence)
    if sequence.isEmpty():
        pytest.fail(f"Invalid key sequence: {key_sequence}")
    
    key = sequence[0].toCombined()
    qtbot.keyClick(widget, key)
```

**Usage**:
```python
def test_keyboard_shortcut(self, gui_main_window, qtbot):
    # Simulate Ctrl+T for theme toggle
    simulate_key_sequence(qtbot, gui_main_window, "Ctrl+T")
    
    # Verify expected action occurred
    # (would need to mock the command execution)
```

#### `get_widget_center(widget)`
**Purpose**: Get center point of a widget for precise clicking

```python
def get_widget_center(widget):
    """Get the center point of a widget for clicking."""
    from PySide6.QtCore import QPoint
    rect = widget.geometry()
    return QPoint(rect.width() // 2, rect.height() // 2)
```

**Usage**:
```python
def test_precise_clicking(self, gui_activity_bar, qtbot):
    # Click exactly in the center of the activity bar
    center = get_widget_center(gui_activity_bar)
    qtbot.mouseClick(gui_activity_bar, Qt.MouseButton.LeftButton, pos=center)
```

## Fixture Dependencies and Relationships

### Dependency Graph

```
qapp (session)
├── mock_icon_manager
│   └── gui_main_window
│       ├── gui_activity_bar  
│       ├── gui_sidebar
│       ├── gui_workspace
│       └── gui_status_bar
```

### Automatic Dependencies

When you request any GUI component fixture, all its dependencies are automatically resolved:

```python
# These fixtures are automatically included:
def test_activity_bar(self, gui_activity_bar, qtbot):
    # Automatically gets: qapp, mock_icon_manager, gui_main_window
    pass

def test_main_window(self, gui_main_window, qtbot):  
    # Automatically gets: qapp, mock_icon_manager
    pass
```

## Creating Custom Fixtures

### Component-Specific Fixtures

```python
@pytest.fixture
def configured_sidebar(gui_sidebar, qtbot):
    """Sidebar configured in a specific state for testing."""
    # Set to specific view
    gui_sidebar.set_current_view("search")
    
    # Ensure expanded
    if gui_sidebar.is_collapsed:
        gui_sidebar.expand()
        qtbot.waitUntil(lambda: not gui_sidebar.is_collapsed, timeout=2000)
    
    return gui_sidebar

@pytest.fixture  
def collapsed_sidebar(gui_sidebar, qtbot):
    """Sidebar in collapsed state."""
    gui_sidebar.collapse()
    qtbot.waitUntil(lambda: gui_sidebar.is_collapsed, timeout=2000)
    return gui_sidebar
```

### Mock Fixtures for Testing

```python
@pytest.fixture
def mock_command_executor():
    """Mock command executor for testing command integration."""
    with patch('core.commands.executor.execute_command') as mock:
        mock.return_value = {'success': True}
        yield mock

@pytest.fixture
def failing_command_executor():
    """Mock command executor that simulates failures."""
    with patch('core.commands.executor.execute_command') as mock:
        mock.return_value = {'success': False, 'error': 'Command failed'}
        yield mock
```

### Performance Testing Fixtures

```python
@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time
    import psutil
    
    start_time = time.time()
    process = psutil.Process()
    start_memory = process.memory_info().rss
    
    yield
    
    end_time = time.time()
    end_memory = process.memory_info().rss
    
    duration = end_time - start_time
    memory_delta = end_memory - start_memory
    
    print(f"Test duration: {duration:.2f}s")
    print(f"Memory delta: {memory_delta / 1024 / 1024:.2f}MB")
```

## Fixture Scopes and Lifecycle

### Available Scopes

- **function** (default): New instance for each test function
- **class**: Shared across all tests in a test class  
- **module**: Shared across all tests in a test module
- **session**: Shared across entire test session

### GUI Fixture Scopes in ViloApp

```python
# Session scope - expensive to create
@pytest.fixture(scope="session")
def qapp(): pass

# Function scope - fresh for each test
@pytest.fixture  # scope="function" is default
def gui_main_window(): pass

@pytest.fixture
def mock_icon_manager(): pass
```

### Choosing the Right Scope

**Use `function` scope when**:
- Widget state changes during tests
- Tests need isolated environments
- Resource usage is acceptable

**Use `class` scope when**:
- Multiple tests need same widget state
- Widget setup is expensive
- Tests don't modify widget state

**Use `session` scope when**:
- Fixture is expensive to create
- Fixture is truly stateless
- Shared across all tests safely

## Advanced Fixture Patterns

### Parameterized Fixtures

```python
@pytest.fixture(params=["light", "dark"])
def themed_main_window(request, qtbot, mock_icon_manager):
    """Main window with different theme configurations."""
    mock_icon_manager.theme = request.param
    
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    
    return window

# Usage: test runs twice, once for each theme
def test_across_themes(self, themed_main_window):
    assert themed_main_window.isVisible()
```

### Conditional Fixtures

```python
@pytest.fixture
def headless_main_window(qtbot, mock_icon_manager):
    """Main window for headless testing environments."""
    import os
    
    if os.environ.get('DISPLAY') is None:
        pytest.skip("No display available")
    
    window = MainWindow()
    qtbot.addWidget(window)
    # Don't call show() for headless
    
    return window
```

### Cleanup Fixtures

```python
@pytest.fixture
def temp_settings():
    """Temporary settings that are cleaned up after test."""
    from PySide6.QtCore import QSettings
    
    # Create temporary settings
    settings = QSettings("test_org", "test_app")
    
    yield settings
    
    # Cleanup
    settings.clear()
    settings.sync()
```

## Troubleshooting Fixtures

### Common Issues and Solutions

#### 1. QApplication Already Exists
**Problem**: `RuntimeError: QApplication instance already exists`  
**Solution**: Use the `qapp` fixture which handles existing instances

#### 2. Widget Not Visible
**Problem**: Widget tests fail because widget not visible  
**Solution**: Ensure `qtbot.addWidget()` and `widget.show()` are called

#### 3. Signal Timeout
**Problem**: `qtbot.waitSignal()` times out  
**Solution**: Check signal connections and increase timeout

#### 4. Mock Not Applied
**Problem**: Mock fixtures not affecting component behavior  
**Solution**: Ensure mock patches correct import paths

### Debug Fixture Issues

```python
@pytest.fixture
def debug_main_window(qtbot, mock_icon_manager):
    """Main window with debug information."""
    print(f"Creating main window with theme: {mock_icon_manager.theme}")
    
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    
    print(f"Main window created: visible={window.isVisible()}")
    print(f"Components: bar={window.activity_bar is not None}, "
          f"sidebar={window.sidebar is not None}")
    
    return window
```

## Best Practices

### 1. Use Appropriate Fixture Scope
```python
# Good - function scope for stateful widgets
@pytest.fixture
def fresh_sidebar(qtbot, mock_icon_manager):
    # New sidebar for each test

# Good - session scope for expensive resources  
@pytest.fixture(scope="session")
def icon_cache():
    # Shared cache across all tests
```

### 2. Clear Fixture Dependencies
```python
# Good - explicit dependencies
@pytest.fixture
def configured_workspace(gui_workspace, qtbot):
    # Dependencies clear from parameters

# Avoid - hidden dependencies
@pytest.fixture  
def configured_workspace():
    workspace = get_workspace_somehow()  # Where does this come from?
```

### 3. Proper Cleanup
```python
# Good - qtbot handles cleanup
@pytest.fixture
def test_widget(qtbot):
    widget = MyWidget()
    qtbot.addWidget(widget)  # Automatic cleanup
    return widget

# Avoid - manual cleanup required
@pytest.fixture
def test_widget():
    widget = MyWidget()  # No cleanup - memory leak risk
    return widget
```

### 4. Meaningful Fixture Names
```python
# Good - descriptive names
@pytest.fixture
def expanded_sidebar_with_search_view():
    pass

# Avoid - ambiguous names
@pytest.fixture 
def sidebar1():
    pass
```

## Conclusion

The fixture system in ViloApp's GUI tests provides a powerful foundation for creating reliable, maintainable tests. By understanding the available fixtures and following best practices, you can write comprehensive GUI tests that accurately reflect user interactions while being efficient and maintainable.