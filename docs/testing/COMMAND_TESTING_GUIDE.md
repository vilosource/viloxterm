# Command System Testing Guide

This guide explains how to use pytest-qt to comprehensively test the command implementations in the application, ensuring all commands work correctly with real Qt widgets and services.

## Overview

The command system testing strategy uses pytest-qt to verify that:
1. Commands execute successfully with real Qt widgets
2. UI state changes correctly in response to commands
3. Services are properly accessed and used
4. Error conditions are handled gracefully
5. Commands integrate properly with the entire application

## Test Infrastructure

### Key Dependencies

```python
# requirements-dev.txt
pytest>=7.0.0
pytest-qt>=4.2.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

### Test File Structure

```
tests/
├── conftest.py                        # Shared fixtures (qtbot, main_window, etc.)
├── test_command_system.py             # Basic command system tests
├── test_command_implementations.py    # Command implementation tests with Qt
├── unit/
│   └── test_*.py                      # Unit tests for individual components
└── integration/
    └── test_*.py                      # Integration tests
```

## pytest-qt Fixtures

### Core Fixtures (conftest.py)

```python
@pytest.fixture(scope="session")
def qapp():
    """QApplication instance for test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(qtbot):
    """Create main window with all components."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window

@pytest.fixture
def workspace(main_window):
    """Get workspace from main window."""
    return main_window.workspace
```

### qtbot Usage

The `qtbot` fixture provides essential testing utilities:

```python
# Wait for Qt events to process
qtbot.wait(100)  # Wait 100ms

# Wait for widget to be exposed
qtbot.waitExposed(widget)

# Wait for signal
with qtbot.waitSignal(widget.someSignal, timeout=1000):
    widget.doSomething()

# Simulate keyboard input
qtbot.keyClick(widget, Qt.Key_Enter)
qtbot.keyClicks(widget, "Hello")

# Simulate mouse actions
qtbot.mouseClick(widget, Qt.LeftButton)
```

## Testing Command Implementations

### 1. Pane Commands

Test pane splitting, closing, and maximizing:

```python
class TestPaneCommands:
    def test_split_pane_horizontal_command(self, qtbot, workspace):
        """Test horizontal pane splitting."""
        initial_count = len(workspace.get_all_panes())
        
        # Execute command
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert result.success
        
        # Wait for UI update
        qtbot.wait(100)
        
        # Verify pane was created
        final_count = len(workspace.get_all_panes())
        assert final_count == initial_count + 1
    
    def test_maximize_pane_toggle(self, qtbot, workspace):
        """Test pane maximize/restore toggle."""
        # Setup: Create multiple panes
        execute_command("workbench.action.splitPaneHorizontal")
        qtbot.wait(100)
        
        panes = workspace.get_all_panes()
        target_pane = panes[0]
        
        # Maximize
        result = execute_command("workbench.action.maximizePane", pane=target_pane)
        assert result.success
        qtbot.wait(100)
        
        # Verify only target pane is visible
        assert target_pane.isVisible()
        for pane in panes[1:]:
            assert not pane.isVisible()
        
        # Restore
        result = execute_command("workbench.action.maximizePane", pane=target_pane)
        assert result.success
        qtbot.wait(100)
        
        # Verify all panes visible again
        for pane in panes:
            assert pane.isVisible()
```

### 2. Tab Commands

Test tab management operations:

```python
class TestTabCommands:
    def test_duplicate_tab(self, qtbot, workspace):
        """Test tab duplication."""
        tab_widget = workspace.tab_widget
        original_count = tab_widget.count()
        original_text = tab_widget.tabText(0)
        
        result = execute_command("workbench.action.duplicateTab", tab_index=0)
        assert result.success
        
        qtbot.wait(100)
        
        # Verify tab was duplicated
        assert tab_widget.count() == original_count + 1
        new_tab_text = tab_widget.tabText(-1)
        assert original_text in new_tab_text or "Copy" in new_tab_text
    
    def test_rename_tab(self, qtbot, workspace):
        """Test tab renaming."""
        new_name = "My Custom Tab"
        
        result = execute_command(
            "workbench.action.renameTab",
            tab_index=0,
            new_name=new_name
        )
        assert result.success
        
        # Verify rename
        assert workspace.tab_widget.tabText(0) == new_name
```

### 3. Navigation Commands

Test focus navigation between panes:

```python
class TestNavigationCommands:
    def test_directional_navigation(self, qtbot, workspace):
        """Test navigating between panes directionally."""
        # Setup: Create pane grid
        execute_command("workbench.action.splitPaneHorizontal")
        execute_command("workbench.action.splitPaneVertical")
        qtbot.wait(100)
        
        # Test each direction
        for direction in ["Left", "Right", "Above", "Below"]:
            cmd = f"workbench.action.focus{direction}Pane"
            result = execute_command(cmd)
            # Should succeed or indicate no pane in that direction
            assert result.success or "No pane" in str(result.error)
```

## Testing with Mocks and Spies

### Mock Services

```python
def test_command_with_mock_service(qtbot, monkeypatch):
    """Test command with mocked service."""
    mock_service = Mock(spec=WorkspaceService)
    mock_service.get_workspace.return_value = Mock()
    
    # Inject mock service
    ServiceLocator.register(WorkspaceService, mock_service)
    
    # Execute command
    result = execute_command("workbench.action.splitPaneHorizontal")
    
    # Verify service was called
    mock_service.get_workspace.assert_called_once()
```

### Spy on Command Execution

```python
def test_keyboard_shortcut_triggers_command(qtbot, main_window):
    """Test that keyboard shortcuts trigger commands."""
    with patch('core.commands.executor.execute_command') as spy:
        spy.return_value = CommandResult(success=True)
        
        # Simulate Ctrl+N
        qtbot.keyClick(main_window, Qt.Key_N, Qt.ControlModifier)
        qtbot.wait(100)
        
        # Verify command was called
        spy.assert_called_with("file.newEditorTab")
```

## Testing Command Context

### Verify Context Propagation

```python
def test_command_receives_correct_context():
    """Test that commands receive proper context."""
    received_context = None
    
    @command(id="test.context", title="Test", category="Test")
    def test_command(context: CommandContext) -> CommandResult:
        nonlocal received_context
        received_context = context
        return CommandResult(success=True)
    
    execute_command("test.context")
    
    # Verify context contents
    assert received_context.main_window is not None
    assert received_context.workspace is not None
    assert received_context.get_service(WorkspaceService) is not None
```

## Testing Error Conditions

### Command Failures

```python
def test_command_error_handling():
    """Test graceful error handling."""
    # Non-existent command
    result = execute_command("non.existent.command")
    assert not result.success
    assert "not found" in result.error.lower()
    
    # Missing service
    ServiceLocator.reset()
    result = execute_command("workbench.action.splitPaneHorizontal")
    assert not result.success
    assert "service" in result.error.lower()
    
    # Invalid arguments
    result = execute_command("workbench.action.renameTab", tab_index=999)
    assert not result.success or result.value is None
```

## Performance Testing

### Rapid Command Execution

```python
def test_rapid_command_execution(qtbot, workspace):
    """Test executing many commands rapidly."""
    results = []
    
    for i in range(20):
        result = execute_command("workbench.action.splitPaneHorizontal")
        results.append(result)
    
    qtbot.wait(500)  # Let Qt catch up
    
    # Verify all succeeded
    assert all(r.success for r in results)
    assert len(workspace.get_all_panes()) > 20
```

### Concurrent Commands

```python
def test_concurrent_commands(qtbot):
    """Test thread-safe command execution."""
    import threading
    from queue import Queue
    
    results = Queue()
    
    def execute_in_thread():
        result = execute_command("workbench.action.splitPaneHorizontal")
        results.put(result)
    
    threads = [threading.Thread(target=execute_in_thread) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Check results
    success_count = sum(1 for _ in range(results.qsize()) 
                       if results.get().success)
    assert success_count > 0  # At least some should succeed
```

## Integration Testing

### Full Workflow Tests

```python
def test_complete_workflow(qtbot, main_window):
    """Test a complete user workflow."""
    workspace = main_window.workspace
    
    # 1. Create new tab
    execute_command("file.newEditorTab")
    qtbot.wait(100)
    
    # 2. Split pane
    execute_command("workbench.action.splitPaneHorizontal")
    qtbot.wait(100)
    
    # 3. Navigate to new pane
    execute_command("workbench.action.focusNextPane")
    qtbot.wait(100)
    
    # 4. Create another tab in new pane
    execute_command("file.newEditorTab")
    qtbot.wait(100)
    
    # Verify final state
    assert workspace.tab_widget.count() >= 2
    assert len(workspace.get_all_panes()) >= 2
```

## Running Tests

### Basic Test Execution

```bash
# Run all command tests
pytest tests/test_command_implementations.py -v

# Run specific test class
pytest tests/test_command_implementations.py::TestPaneCommands -v

# Run with coverage
pytest tests/test_command_implementations.py --cov=core.commands --cov-report=html

# Run in headless mode (CI/CD)
xvfb-run -a pytest tests/test_command_implementations.py
```

### Debugging Failed Tests

```bash
# Run with verbose output and capture disabled
pytest tests/test_command_implementations.py -vvs

# Run with Qt logging
QT_LOGGING_RULES="*.debug=true" pytest tests/test_command_implementations.py

# Run single test with debugging
pytest tests/test_command_implementations.py::TestPaneCommands::test_split_pane_horizontal_command -vvs --pdb
```

## Best Practices

### 1. Always Wait for Qt Events

```python
# After command execution, wait for Qt to update
result = execute_command("some.command")
qtbot.wait(100)  # Give Qt time to process
```

### 2. Setup and Teardown

```python
@pytest.fixture(autouse=True)
def setup_services(qtbot):
    """Ensure services are properly setup."""
    ServiceLocator.reset()
    # Register required services
    yield
    ServiceLocator.reset()  # Cleanup
```

### 3. Test Isolation

```python
def test_isolated_command():
    """Each test should be independent."""
    # Clear any previous state
    command_registry.clear()
    ServiceLocator.reset()
    
    # Run test
    # ...
    
    # No cleanup needed - next test handles its own setup
```

### 4. Verify UI State

```python
def test_ui_state_after_command(qtbot, workspace):
    """Always verify the actual UI state, not just return values."""
    result = execute_command("workbench.action.splitPaneHorizontal")
    assert result.success  # Check command succeeded
    
    qtbot.wait(100)
    
    # Also verify actual UI state
    panes = workspace.get_all_panes()
    assert len(panes) == 2
    assert all(pane.isVisible() for pane in panes)
```

### 5. Test Command Registration

```python
def test_all_commands_registered():
    """Verify all expected commands are registered."""
    expected_commands = [
        "workbench.action.splitPaneHorizontal",
        "workbench.action.splitPaneVertical",
        "workbench.action.closePane",
        # ... etc
    ]
    
    for cmd_id in expected_commands:
        cmd = command_registry.get_command(cmd_id)
        assert cmd is not None, f"Command {cmd_id} not registered"
        assert callable(cmd.handler), f"Command {cmd_id} has invalid handler"
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Test Commands

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install Qt dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y xvfb libxkbcommon-x11-0 libxcb-xinerama0
    
    - name: Install Python dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run Command Tests
      run: |
        xvfb-run -a pytest tests/test_command_implementations.py \
          --cov=core.commands \
          --cov-report=xml
    
    - name: Upload Coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

1. **"QApplication instance already exists"**
   - Use the session-scoped `qapp` fixture
   - Don't create QApplication in tests

2. **"Widget is not visible"**
   - Add `qtbot.waitExposed(widget)` after showing
   - Use `qtbot.wait()` after state changes

3. **"Signal timeout"**
   - Increase timeout: `qtbot.waitSignal(signal, timeout=5000)`
   - Verify signal is actually emitted

4. **"Command not found"**
   - Ensure command modules are imported
   - Check command registration in setup

5. **"Service not available"**
   - Register services in fixture or setup
   - Use ServiceLocator.register() before tests

## Summary

This testing approach ensures:
- **Correctness**: Commands work with real Qt widgets
- **Integration**: Commands properly integrate with services
- **Robustness**: Error conditions are handled gracefully
- **Performance**: Commands work under stress conditions
- **Maintainability**: Tests are clear and isolated

By following this guide, you can ensure that all command implementations are thoroughly tested and work correctly in the real application environment.