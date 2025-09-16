# Architecture Compliance Tests

This directory contains tests that enforce architectural principles and coding standards for the ViloxTerm project.

## Test Files

### `test_no_service_locator_in_ui.py`
**Purpose**: Ensures UI components follow the Command Pattern Architecture.

**Checks**:
- No direct ServiceLocator imports in UI components
- No ServiceLocator usage in UI files
- Overall architecture compliance

**Violations Found**: Currently PASSING ✅ (no violations)

### `test_no_bare_exceptions.py`
**Purpose**: Enforces proper exception handling practices.

**Checks**:
- No bare `except:` handlers
- Proper exception handling patterns
- Silent exception handling detection

**Violations Found**: 11 bare exception handlers across multiple files
- `ui/main_window.py:432`
- `core/themes/importers.py:355, 399`
- `ui/widgets/color_picker_widget.py:184, 196, 221`
- `ui/widgets/custom_title_bar.py:218`
- `ui/widgets/widget_pool.py:195`
- `ui/terminal/terminal_widget.py:291`
- `ui/terminal/terminal_app_widget.py:269`
- `core/commands/builtin/debug_commands.py:99`

### `test_file_size_limits.py`
**Purpose**: Prevents monolithic files that violate Single Responsibility Principle.

**Checks**:
- Files don't exceed critical size limits (1000 lines)
- Type-specific limits for widgets, services, commands, models
- Average codebase file size

**Violations Found**: 17 files exceed type-specific limits
- Commands should be ≤ 200 lines
- Widgets should be ≤ 400 lines
- Models should be ≤ 300 lines

### `test_command_pattern_compliance.py`
**Purpose**: Enforces Command Pattern Architecture compliance.

**Checks**:
- Commands have `@command` decorators
- Commands return `CommandResult` objects
- UI uses `execute_command()` instead of direct calls
- Command IDs follow namespacing convention
- Commands have proper `CommandContext` parameters

**Violations Found**: Multiple violations across the command system
- Many functions ending in `_command` missing decorators
- Non-standard command ID namespacing
- Missing type annotations

## Running the Tests

### Individual Test Files
```bash
# ServiceLocator compliance (currently passing)
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/test_no_service_locator_in_ui.py -v

# Exception handling compliance
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/test_no_bare_exceptions.py -v

# File size limits
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/test_file_size_limits.py -v

# Command pattern compliance
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/test_command_pattern_compliance.py -v
```

### All Architecture Tests
```bash
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/ -v
```

### CI/CD Integration
```bash
# Exit on first failure (recommended for CI)
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/ -x

# Generate JUnit XML report for CI systems
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/ --junitxml=architecture-report.xml

# Show only failures (quiet mode)
.direnv/python-3.12.3/bin/python -m pytest tests/architecture/ -q --tb=no
```

## Current Status Summary

| Test Category | Status | Violations | Priority |
|---------------|--------|------------|----------|
| ServiceLocator in UI | ✅ PASSING | 0 | ✅ Complete |
| Bare Exceptions | ❌ FAILING | 11 | 🔴 High |
| File Size Limits | ⚠️ WARNINGS | 17 | 🟡 Medium |
| Command Pattern | ❌ FAILING | 50+ | 🔴 High |

## Recommended Actions

### High Priority (Fix First)
1. **Fix bare exception handlers** - Replace `except:` with specific exception types
2. **Command pattern compliance** - Add missing `@command` decorators and proper return types

### Medium Priority
3. **File size refactoring** - Break down large command files and complex widgets
4. **Command ID standardization** - Use proper namespacing (workbench.*, editor.*, etc.)

### Integration with Development Workflow

Add to `make test` or CI pipeline:
```bash
# In Makefile or CI script
test-architecture:
	.direnv/python-3.12.3/bin/python -m pytest tests/architecture/ -v
```

These tests help maintain code quality and architectural integrity as the codebase grows.