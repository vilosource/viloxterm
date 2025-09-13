- This project uses direnv .envrc, when running code ensure that we are in the correct environment
- Use `.direnv/python-3.12.3/bin/python` and `.direnv/python-3.12.3/bin/pip` for Python commands

## Project Overview
Building a VSCode-style desktop GUI application using PySide6 based on the specification in `PROJECT.md`. Key features:
- Fixed Activity Bar (vertical toolbar with icons)
- Collapsible Sidebar with multiple tool panels (Explorer, Search, Git, Settings)
- Central Workspace with recursive split panes and tabs
- Status Bar
- State persistence using QSettings
- Chrome-style UI mode (tabs in title bar)

The full layout specification including state diagrams and interaction details is in `PROJECT.md`.

## 🚨 CRITICAL: Development Workflow - MUST READ

### Architecture is MANDATORY
This application uses a **Command Pattern Architecture**. Every user action MUST go through commands.

**Correct Flow:**
```
User Action → Command → Service → UI Update
```

**NEVER DO THIS:**
```
UI Component → Direct UI Manipulation ❌
Signal → Direct UI Component Update ❌
```

### Test-Driven Development (TDD) is REQUIRED
1. **Write failing tests FIRST**
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. **NEVER commit with failing tests**

### Before Implementing ANY Feature
- [ ] Study how similar features work in the codebase
- [ ] Identify which commands to create/extend
- [ ] Write integration tests first
- [ ] Ensure command palette integration
- [ ] Test cross-platform compatibility
- [ ] Follow existing patterns exactly

### Red Flags - Stop if you see these:
- No `@command` decorator in your implementation = architectural violation
- Direct signal connections between UI components = bypassing abstraction
- No tests written alongside code = not following TDD
- Using `widget.setSomething()` directly instead of commands = wrong approach
- Platform-specific hacks = need more research

## Core Architecture

### Command Pattern (MANDATORY)
Every user action goes through the command system:
- **Commands**: Decorated functions in `core/commands/builtin/`
- **Executor**: `execute_command()` handles all command execution
- **Services**: Business logic layer that commands interact with
- **UI**: Only displays state, never contains business logic

### Services Layer
- **UIService**: UI state, theme management, Chrome mode
- **WorkspaceService**: Tab and pane management
- **StateService**: Application state persistence
- **TerminalService**: Terminal integration
- **EditorService**: Editor functionality
- **KeyboardService**: Keyboard shortcut management

### UI Components
- **MainWindow**: QMainWindow subclass, application shell
- **ActivityBar**: Vertical toolbar with tool icons
- **Sidebar**: Collapsible panel with Explorer/Search/Git views
- **Workspace**: Split pane system with tabs
- **StatusBar**: Application status display

## Project Structure
```
viloxterm/
├── main.py                      # Application entry point
├── core/
│   ├── commands/               
│   │   ├── base.py             # Command base classes
│   │   ├── executor.py         # Command execution engine
│   │   ├── registry.py         # Command registration
│   │   └── builtin/            # Built-in commands
│   │       ├── workspace_commands.py
│   │       ├── ui_commands.py
│   │       └── ...
│   └── keyboard/               # Keyboard handling
├── services/
│   ├── base.py                 # Service base class
│   ├── ui_service.py           # UI state management
│   ├── workspace_service.py    # Workspace operations
│   └── ...
├── ui/
│   ├── main_window.py          # Main application window
│   ├── chrome_main_window.py   # Chrome-style variant
│   ├── activity_bar.py         # Tool sidebar
│   ├── sidebar.py              # Collapsible sidebar
│   ├── workspace_simple.py     # Tab/split management
│   └── widgets/
│       ├── split_pane_widget.py    # Split pane implementation
│       ├── chrome_title_bar*.py    # Chrome UI components
│       ├── window_controls.py      # Min/max/close buttons
│       └── ...
├── tests/
│   ├── unit/                   # Unit tests
│   ├── gui/                    # GUI integration tests
│   ├── integration/            # Command/service tests
│   └── e2e/                    # End-to-end tests
└── resources/                   # Icons, styles, etc.
```

## Testing Architecture

### Testing Stack
- **pytest**: Core test framework
- **pytest-qt**: Qt/PySide6 GUI testing with `qtbot` fixture
- **pytest-cov**: Coverage reporting
- **pytest-xvfb**: Headless GUI testing (Linux CI/CD)

### Test Organization
- `tests/unit/` - Unit tests for individual components
- `tests/gui/` - GUI integration tests using pytest-qt
- `tests/integration/` - Command and service integration tests
- `tests/e2e/` - End-to-end application tests

### Testing Commands
```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/gui/           # GUI tests only  
pytest tests/integration/   # Integration tests only

# Run with coverage
make test-coverage

# Run specific test file with verbose output
pytest tests/unit/test_chrome_mode.py -v

# Run headless (for CI/CD)
make test-headless
```

### Writing Tests

#### Example Unit Test
```python
def test_chrome_tab_sync(qtbot):
    """Test that Chrome tabs sync with workspace."""
    # Setup
    window = ChromeMainWindow()
    qtbot.addWidget(window)
    
    # Action
    execute_command("workbench.action.nextTab")
    
    # Assert - both should be synchronized
    assert window.workspace.current_tab() == 1
    assert window.chrome_title_bar.current_tab() == 1
```

#### Example Command Test
```python
def test_command_updates_ui(mock_context):
    """Test that commands properly update UI through services."""
    # Execute command
    result = next_tab_command(mock_context)
    
    # Verify service was called
    mock_context.workspace_service.switch_to_tab.assert_called_with(1)
    
    # Verify UI was updated through service
    mock_context.ui_service.update_chrome_tabs.assert_called()
```

## Command Pattern Implementation

### Creating New Commands
```python
from core.commands.decorators import command
from core.commands.base import CommandContext, CommandResult

@command(
    id="workbench.action.myFeature",
    title="My Feature",
    category="Workspace",
    description="Does something useful",
    shortcut="ctrl+shift+m"  # Optional
)
def my_feature_command(context: CommandContext) -> CommandResult:
    """Command implementation."""
    # Get services
    ui_service = context.get_service(UIService)
    workspace_service = context.get_service(WorkspaceService)
    
    # Perform business logic
    try:
        result = workspace_service.do_something()
        
        # Update UI through service (if needed)
        if ui_service:
            ui_service.update_display(result)
        
        return CommandResult(success=True, value=result)
    except Exception as e:
        return CommandResult(success=False, error=str(e))
```

### Extending Commands for UI Features
When adding UI features (like Chrome mode), extend existing commands:

```python
# In workspace_commands.py
@command(id="workbench.action.nextTab")
def next_tab_command(context: CommandContext) -> CommandResult:
    # ... existing logic ...
    
    # Check for Chrome mode and update
    ui_service = context.get_service(UIService)
    if ui_service:
        chrome_bar = ui_service.get_chrome_title_bar()
        if chrome_bar:
            chrome_bar.set_current_tab(new_index)
    
    return CommandResult(success=True, value={'tab_index': new_index})
```

### Executing Commands
```python
from core.commands.executor import execute_command

# From anywhere in the application
result = execute_command("workbench.action.nextTab")

# With arguments
result = execute_command("workbench.action.selectTab", tab_index=2)
```

## Service Architecture

### Available Services
| Service | Purpose | Key Methods |
|---------|---------|-------------|
| UIService | UI state management | `toggle_theme()`, `get_chrome_title_bar()`, `is_chrome_mode_enabled()` |
| WorkspaceService | Tab/pane management | `add_tab()`, `switch_to_tab()`, `split_pane()` |
| StateService | Persistence | `save_state()`, `restore_state()` |
| TerminalService | Terminal integration | `create_terminal()`, `execute_command()` |
| EditorService | Editor operations | `open_file()`, `save_file()` |
| KeyboardService | Shortcuts | `register_shortcut()`, `handle_key_event()` |

### Using Services in Commands
```python
def my_command(context: CommandContext) -> CommandResult:
    # Get service
    ui_service = context.get_service(UIService)
    if not ui_service:
        return CommandResult(success=False, error="UIService not available")
    
    # Check UI state
    if ui_service.is_chrome_mode_enabled():
        chrome_bar = ui_service.get_chrome_title_bar()
        # Update Chrome UI
    
    # Use service methods
    ui_service.show_notification("Task completed")
    return CommandResult(success=True)
```

## Common Commands
```bash
# Quick start
make setup      # Initial setup (install deps)
make run        # Run the application
make test       # Run tests
make check      # Run all code quality checks

# Development
make format     # Format code with black
make lint       # Lint with ruff
make typecheck  # Type check with mypy
make clean      # Clean up generated files

# Testing
make test-coverage  # Run tests with coverage
make test-unit      # Run unit tests only
make test-gui       # Run GUI tests only
make test-headless  # Run tests headless (Linux)

# Shortcuts
make r  # Run app
make t  # Run tests
make c  # Clean
make f  # Format
make l  # Lint
```

## UI Features
- **Chrome Mode**: `Ctrl+Shift+C` - Tabs in title bar like Chrome browser
- **Menu Bar Toggle**: `Ctrl+Shift+M` - Show/hide menu bar
- **Sidebar Toggle**: `Ctrl+B` - Show/hide sidebar
- **Theme Toggle**: `Ctrl+T` - Switch between light/dark themes
- **Command Palette**: `Ctrl+Shift+P` - Access all commands
- **Tab Navigation**: `Ctrl+PgUp/PgDown` - Navigate tabs

## Feature Development Checklist

### Before Starting
- [ ] Is there a design document or specification?
- [ ] Have you studied similar existing features?
- [ ] Do you understand the command pattern architecture?
- [ ] Have you identified which services to use?

### During Development
- [ ] Tests written FIRST (before implementation)?
- [ ] Using commands for all user actions?
- [ ] Following existing code patterns?
- [ ] No direct UI-to-UI connections?
- [ ] Cross-platform compatibility checked?
- [ ] Command palette integration working?

### Before Committing
- [ ] All tests passing?
- [ ] No architectural violations?
- [ ] Code follows project style (black, ruff)?
- [ ] Commands documented with descriptions?
- [ ] No platform-specific hacks?

## Lessons from Chrome Mode Implementation

### ❌ What NOT to Do
1. **Don't bypass the command pattern** - Every action through commands
2. **Don't add features without tests** - TDD is mandatory
3. **Don't create direct UI connections** - Use services and commands
4. **Don't implement without understanding** - Study existing code first
5. **Don't use platform-specific hacks** - Research proper solutions

### ✅ What TO Do
1. **Extend existing commands** for new features
2. **Write tests before code** (TDD)
3. **Use services** for state management
4. **Ensure command integration** for all features
5. **Follow existing patterns** exactly

### Common Mistakes to Avoid
- Importing UI components directly in other UI components
- Using signals/slots for business logic
- Creating new systems parallel to commands
- Forgetting to test command palette integration
- Not checking cross-platform compatibility

## Icon System
- **Icons**: Feather Icons-style SVG icons for activity bar
- **Themes**: Light and dark theme support with automatic icon switching
- **Resource System**: Qt .qrc files compiled to Python modules
- **Icon Manager**: Centralized icon loading and theme management
- **Commands**: `make resources` to compile icons

## References
- Implementation Guide: `IMPLEMENTATION_GUIDE.md`
- Project Specification: `PROJECT.md`
- Testing Strategy: `TESTING_STRATEGY.md`
- Command Documentation: `docs/commands.md`

## IMPORTANT: Agent Usage

### Code Monkey 🐵 - Safe Implementation Agent
**Use for**: New features, refactoring, bug fixes requiring multiple files

**Launch with**: `/code-monkey` or "Code monkey, implement [feature]"

**Protocol**:
1. Reads existing code before writing
2. Makes incremental changes (max 10 lines at a time)
3. Tests after EVERY change
4. Never breaks existing functionality
5. Follows patterns exactly

### Design Compliance Analyzer
**Use for**: Verifying implementation matches design, finding issues

**Launch with**: "Check design compliance" or "Review against spec"

**Capabilities**:
1. Exhaustive code searches
2. Architecture violation detection
3. Duplicate definition finding
4. Pattern compliance checking

## Quick Debugging Tips

### Command Not Working?
1. Check command is registered in `__init__.py`
2. Verify service dependencies are available
3. Check command ID matches everywhere
4. Test through command palette

### UI Not Updating?
1. Verify using commands, not direct manipulation
2. Check service is updating UI
3. Ensure Chrome mode awareness in commands
4. Check signal/slot connections

### Tests Failing?
1. Mock services properly
2. Use qtbot for GUI components
3. Check async operations
4. Verify command execution flow