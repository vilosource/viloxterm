# GUI Test Makefile Targets

## Overview

This document explains the Makefile targets available for running GUI tests in ViloApp. These targets provide convenient ways to run different categories of GUI tests with appropriate configurations.

## Basic GUI Test Targets

### `make test-gui` (alias: `make tg`)
Run all GUI tests with verbose output.
```bash
make test-gui
# or
make tg
```

### `make test-gui-clean`
Run GUI tests with minimal output for quick feedback.
```bash
make test-gui-clean
```

### `make test-gui-headless` (alias: `make tgh`)
Run GUI tests in headless mode using xvfb (Linux only).
```bash
make test-gui-headless
# or
make tgh
```

## Filtered GUI Test Targets

### Performance-Based Filtering

#### `make test-gui-fast`
Run GUI tests excluding slow tests (good for quick feedback during development).
```bash
make test-gui-fast
```

#### `make test-gui-slow`
Run only slow GUI tests (comprehensive animations, performance tests).
```bash
make test-gui-slow
```

### Category-Based Filtering

#### `make test-gui-animation`
Run tests related to animations and transitions.
```bash
make test-gui-animation
```

#### `make test-gui-keyboard`
Run tests for keyboard interactions and shortcuts.
```bash
make test-gui-keyboard
```

#### `make test-gui-mouse`
Run tests for mouse interactions (clicks, drags, hovers).
```bash
make test-gui-mouse
```

#### `make test-gui-theme`
Run tests related to theme switching and visual consistency.
```bash
make test-gui-theme
```

#### `make test-gui-integration`
Run integration tests between multiple GUI components.
```bash
make test-gui-integration
```

#### `make test-gui-performance`
Run performance-focused GUI tests.
```bash
make test-gui-performance
```

#### `make test-gui-accessibility`
Run accessibility and keyboard navigation tests.
```bash
make test-gui-accessibility
```

## Coverage and Reporting

### `make test-gui-coverage`
Run GUI tests with code coverage reporting.
```bash
make test-gui-coverage
```

This generates both terminal output and HTML coverage reports in `htmlcov/`.

## CI/CD Integration

### Updated CI Targets

#### `make validate`
Now includes fast GUI tests in the validation pipeline:
```bash
make validate  # Runs: check + test + test-gui-fast
```

#### `make ci`
Standard CI pipeline with headless GUI tests:
```bash
make ci  # Includes: clean + install + install-dev + check + test-coverage + test-gui-headless
```

#### `make ci-full`
Full CI pipeline including slow GUI tests:
```bash
make ci-full  # Includes: clean + install + install-dev + check + test-coverage + test-gui-coverage
```

## Usage Examples

### Development Workflow

```bash
# Quick development testing
make test-gui-fast

# Test specific interaction type you're working on
make test-gui-mouse

# Full testing before committing
make validate
```

### Debugging Failed Tests

```bash
# Run with verbose output to see details
make test-gui

# Run specific test category that's failing
make test-gui-animation

# Run with minimal output to focus on failures
make test-gui-clean
```

### CI/CD Setup

```bash
# Standard CI (faster, good for pull requests)
make ci

# Full CI (comprehensive, good for main branch)
make ci-full

# Headless testing for servers without display
make test-gui-headless
```

### Coverage Analysis

```bash
# Generate GUI test coverage report
make test-gui-coverage

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Prerequisites

### For Regular GUI Tests
- PySide6 installed
- Display available (X11/Wayland on Linux, native on macOS/Windows)

### For Headless Tests (Linux)
```bash
# Install xvfb for headless testing
sudo apt-get install xvfb
```

### For Coverage Reports
Coverage reports require the `pytest-cov` plugin (included in dev dependencies).

## Test Markers

The GUI tests use pytest markers for filtering:

- `@pytest.mark.gui` - Basic GUI tests
- `@pytest.mark.mouse` - Mouse interaction tests
- `@pytest.mark.keyboard` - Keyboard interaction tests
- `@pytest.mark.animation` - Animation and transition tests
- `@pytest.mark.theme` - Theme-related tests
- `@pytest.mark.integration` - Multi-component integration tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.accessibility` - Accessibility tests
- `@pytest.mark.slow` - Slow-running tests

## Environment Variables

### Display Configuration
For headless testing, you can configure the virtual display:

```bash
# Custom display size for headless tests
XVFB_WIDTH=1920 XVFB_HEIGHT=1080 make test-gui-headless
```

### Pytest Options
You can pass additional pytest options via environment:

```bash
# Run with specific test pattern
PYTEST_ARGS="-k test_sidebar" make test-gui

# Run with custom timeout
PYTEST_ARGS="--timeout=60" make test-gui
```

## Troubleshooting

### Common Issues

#### "QApplication instance already exists"
**Solution**: Tests are properly isolated using pytest-qt fixtures. This shouldn't occur with the provided test structure.

#### "No display available" on Linux
**Solution**: Use headless testing:
```bash
make test-gui-headless
```

#### Slow test execution
**Solution**: Use fast test subset during development:
```bash
make test-gui-fast
```

#### Tests hanging on animations
**Solution**: Check animation timeout values in test configuration. Run only non-animation tests:
```bash
make test-gui -k "not animation"
```

## Integration with IDEs

### VSCode
Add to `.vscode/tasks.json`:
```json
{
    "label": "Run GUI Tests",
    "type": "shell",
    "command": "make test-gui",
    "group": "test"
}
```

### PyCharm
Add as external tools:
- Program: `make`
- Arguments: `test-gui`
- Working directory: `$ProjectFileDir$`

## Best Practices

1. **Use `test-gui-fast` during development** for quick feedback
2. **Run `test-gui-headless` in CI/CD** to avoid display dependencies
3. **Use specific category targets** when working on particular features
4. **Always run `validate`** before committing to ensure all tests pass
5. **Use `test-gui-coverage`** periodically to ensure good test coverage

## See Also

- [GUI Testing Strategy](GUI_TESTING_STRATEGY.md) - Overall testing approach
- [GUI Test Patterns](GUI_TEST_PATTERNS.md) - Common testing patterns
- [GUI Fixtures Guide](GUI_FIXTURES_GUIDE.md) - Available test fixtures
- [GUI Test Examples](GUI_TEST_EXAMPLES.md) - Practical examples