# Testing Strategy for PySide6 VSCode-Style Application

## Overview
This document defines the comprehensive testing strategy for our PySide6 desktop application, covering unit testing, integration testing, E2E testing, and CI/CD integration.

## Testing Stack

### Core Testing Framework
- **pytest** - Primary testing framework
- **pytest-qt** (v4.4.0+) - Qt/PySide6 widget testing plugin
- **pytest-cov** - Coverage reporting
- **pytest-xvfb** - Virtual display for headless testing (Linux)

### E2E Testing Tools
- **PyAutoGUI** - Cross-platform GUI automation for E2E tests
- **PyWinAuto** - Windows-specific advanced automation (optional)

## Testing Layers

### 1. Unit Testing
Testing individual components in isolation.

#### Structure
```
tests/
├── unit/
│   ├── test_activity_bar.py
│   ├── test_sidebar.py
│   ├── test_split_tree.py
│   └── test_tab_container.py
```

#### Example Test
```python
import pytest
from pytestqt.qt_compat import qt_api
from ui.sidebar import CollapsibleSidebar

def test_sidebar_collapse(qtbot):
    """Test sidebar collapse animation."""
    sidebar = CollapsibleSidebar()
    qtbot.addWidget(sidebar)
    
    initial_width = sidebar.width()
    sidebar.toggle()
    
    # Wait for animation to complete
    qtbot.waitUntil(lambda: sidebar.width() == 0, timeout=1000)
    assert sidebar.is_collapsed == True
```

### 2. Integration Testing
Testing interactions between components.

#### Structure
```
tests/
├── integration/
│   ├── test_activity_sidebar_sync.py
│   ├── test_workspace_splits.py
│   └── test_state_persistence.py
```

#### Example Test
```python
def test_activity_bar_toggles_sidebar(qtbot, main_window):
    """Test activity bar buttons control sidebar visibility."""
    qtbot.mouseClick(
        main_window.activity_bar.explorer_button,
        qt_api.QtCore.Qt.MouseButton.LeftButton
    )
    assert main_window.sidebar.current_view == "explorer"
    assert main_window.sidebar.isVisible()
```

### 3. E2E Testing
Full application workflow testing using GUI automation.

#### Structure
```
tests/
├── e2e/
│   ├── test_complete_workflows.py
│   ├── test_split_pane_operations.py
│   └── test_persistence_across_restarts.py
```

#### Example E2E Test with PyAutoGUI
```python
import pyautogui
import pytest
from main import MainApplication

@pytest.fixture
def app_instance():
    """Launch application for E2E testing."""
    app = MainApplication()
    app.show()
    yield app
    app.close()

def test_split_pane_workflow(app_instance):
    """Test creating and managing split panes."""
    # Wait for app to be ready
    pyautogui.sleep(1)
    
    # Right-click in workspace to open context menu
    workspace_center = app_instance.workspace.geometry().center()
    pyautogui.rightClick(workspace_center.x(), workspace_center.y())
    
    # Select "Split Horizontal" from menu
    pyautogui.click("Split Horizontal")
    
    # Verify split was created
    assert len(app_instance.workspace.get_panes()) == 2
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
qt_api = pyside6
addopts = 
    --verbose
    --cov=ui
    --cov=models
    --cov-report=html
    --cov-report=term
```

### conftest.py
```python
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(qtbot):
    """Create main window fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install Linux dependencies
      if: runner.os == 'Linux'
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          xvfb \
          libxkbcommon-x11-0 \
          libxcb-icccm4 \
          libxcb-image0 \
          libxcb-keysyms1 \
          libxcb-randr0 \
          libxcb-render-util0 \
          libxcb-xinerama0 \
          libxcb-xinput0 \
          libxcb-xfixes0 \
          libxcb-cursor0
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-qt pytest-cov pytest-xvfb pyautogui
    
    - name: Run tests (Linux)
      if: runner.os == 'Linux'
      run: xvfb-run -a pytest tests/
      env:
        QT_QPA_PLATFORM: offscreen
    
    - name: Run tests (Windows/macOS)
      if: runner.os != 'Linux'
      run: pytest tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Testing Best Practices

### 1. Widget Testing Guidelines
- **Always use qtbot.addWidget()** to ensure proper cleanup
- **Prefer widget methods over qtbot methods** for reliability
- **Use qtbot.waitUntil()** for animations and async operations
- **Test both mouse and keyboard interactions**

### 2. Signal/Slot Testing
```python
def test_signal_emission(qtbot):
    with qtbot.waitSignal(widget.data_changed, timeout=1000) as blocker:
        widget.update_data("new_value")
    assert blocker.args == ["new_value"]
```

### 3. Exception Handling
```python
def test_error_handling(qtbot):
    with qtbot.capture_exceptions() as exceptions:
        widget.trigger_error()
    assert len(exceptions) == 1
    assert "Expected error" in str(exceptions[0][1])
```

### 4. Headless Testing
- Use `pytest-xvfb` on Linux for CI
- Set `QT_QPA_PLATFORM=offscreen` for true headless
- Alternative: `QT_QPA_PLATFORM=minimal` for basic tests

## Test Data Management

### Fixtures Directory
```
tests/
├── fixtures/
│   ├── sample_layouts.json
│   ├── test_settings.ini
│   └── mock_data.py
```

### Mock Data Example
```python
# tests/fixtures/mock_data.py
def get_mock_sidebar_items():
    return [
        {"type": "folder", "name": "src", "children": [...]},
        {"type": "file", "name": "main.py"}
    ]
```

## Performance Testing

### Benchmark Tests
```python
@pytest.mark.benchmark
def test_split_performance(benchmark, qtbot, main_window):
    """Benchmark split pane creation."""
    def create_split():
        main_window.workspace.split_horizontal()
    
    result = benchmark(create_split)
    assert result < 0.1  # Should complete in under 100ms
```

## Accessibility Testing

### Keyboard Navigation
```python
def test_keyboard_navigation(qtbot, main_window):
    """Ensure all features are keyboard accessible."""
    # Tab through interface elements
    for _ in range(10):
        qtbot.keyClick(main_window, qt_api.QtCore.Qt.Key_Tab)
    
    # Verify focus is on expected element
    assert main_window.focusWidget() is not None
```

## Test Execution Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_sidebar.py

# Run tests in parallel
pytest -n auto

# Run only E2E tests
pytest tests/e2e/

# Run with verbose output
pytest -v

# Run headless on Linux
xvfb-run -a pytest
```

## Coverage Goals
- **Unit Tests**: 80% minimum coverage
- **Integration Tests**: Cover all major workflows
- **E2E Tests**: Cover critical user paths

## Test Documentation
Each test should include:
1. Clear docstring explaining what is being tested
2. Arrange-Act-Assert structure
3. Meaningful assertions with error messages

## Continuous Improvement
- Review test failures weekly
- Add tests for all bug fixes
- Refactor tests alongside code changes
- Monitor test execution time

## Resources
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [PySide6 Testing Guide](https://doc.qt.io/qtforpython-6/PySide6/QtTest/)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)