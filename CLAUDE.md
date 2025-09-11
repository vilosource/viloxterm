- This project uses direnv .envrc, when running code ensure that we are in the correct environment
- Use `.direnv/python-3.12.3/bin/python` and `.direnv/python-3.12.3/bin/pip` for Python commands

## Project Overview
Building a VSCode-style desktop GUI application using PySide6 based on the specification in `PROJECT.md`. Key features:
- Fixed Activity Bar (vertical toolbar with icons)
- Collapsible Sidebar with multiple tool panels (Explorer, Search, Git, Settings)
- Central Workspace with recursive split panes and tabs
- Status Bar
- State persistence using QSettings

The full layout specification including state diagrams and interaction details is in `PROJECT.md`.

## Key Technical Decisions

### Core Architecture
- **Base**: QMainWindow (provides built-in support for toolbars, docks, statusbar)
- **Activity Bar**: QToolBar (vertical, 44-56px width, non-movable)
- **Sidebar**: QDockWidget or QSplitter with animation (collapsible)
- **Workspace**: Nested QSplitters for recursive splitting, QTabWidget for tabs
- **Sidebar Views**: QStackedWidget to switch between Explorer/Search/Git panels

### Important Implementation Notes
1. **QSplitter**: Use `addWidget()` only, never `setLayout()`
2. **Animations**: Use QPropertyAnimation with `maximumWidth` property for smooth collapse
3. **State Persistence**: Use QSettings with `saveState()` and `restoreState()` methods
4. **Activity Bar**: Set property `"type": "activitybar"` for VSCode styling if using QtVSCodeStyle

### Project Structure
```
viloapp/
├── main.py                 # Application entry point
├── ui/
│   ├── main_window.py      # QMainWindow subclass
│   ├── activity_bar.py     # Vertical toolbar
│   ├── sidebar.py          # Collapsible sidebar
│   ├── workspace.py        # Split pane manager
│   └── widgets/
│       ├── split_tree.py   # Recursive splitter logic
│       └── tab_container.py # Tab management
├── models/
│   └── layout_state.py     # JSON serialization
└── resources/
    └── styles/              # QtVSCodeStyle integration
```

### Essential Libraries
- **PySide6**: Main GUI framework
- **QtVSCodeStyle**: VSCode theming (optional)
- **Qt-Advanced-Docking-System**: Advanced docking (optional)

## Commands to Run
```bash
# Quick start
make setup      # Initial setup (install deps)
make run        # Run the application
make test       # Run tests
make check      # Run all code quality checks

# Common commands
make help       # Show all available commands
make format     # Format code with black
make lint       # Lint with ruff
make typecheck  # Type check with mypy
make clean      # Clean up generated files

# Testing
make test-coverage  # Run tests with coverage
make test-unit      # Run unit tests only
make test-headless  # Run tests headless (Linux)

# Shortcuts
make r  # Run app
make t  # Run tests
make c  # Clean
make f  # Format
make l  # Lint
```

## Icon System
- **Icons**: Feather Icons-style SVG icons for activity bar
- **Themes**: Light and dark theme support with automatic icon switching
- **Resource System**: Qt .qrc files compiled to Python modules
- **Icon Manager**: Centralized icon loading and theme management
- **Commands**: `make resources` to compile icons, `Ctrl+T` to toggle theme

## UI Features
- **Menu Bar Toggle**: `Ctrl+Shift+M` to show/hide menu bar (works even when hidden)
- **Sidebar Toggle**: `Ctrl+B` to show/hide sidebar
- **Theme Toggle**: `Ctrl+T` to switch between light/dark themes
- **State Persistence**: Window layout, theme, menu bar visibility saved between sessions

## Testing Strategy
- **Unit Testing**: pytest + pytest-qt for widget testing
- **Integration Testing**: Test component interactions
- **E2E Testing**: PyAutoGUI for GUI automation
- **CI/CD**: GitHub Actions with xvfb for headless testing
- **Coverage Goal**: 80% minimum for unit tests
- Full testing strategy documented in `TESTING_STRATEGY.md`

## Next Implementation Steps
1. Create basic QMainWindow with layout structure
2. Implement Activity Bar as vertical QToolBar
3. Add collapsible Sidebar with QPropertyAnimation
4. Implement Workspace with nested QSplitters
5. Add QTabWidget to each pane
6. Implement state persistence with QSettings
7. Add smooth animations and transitions

## References
- Implementation Guide: `IMPLEMENTATION_GUIDE.md`
- Project Specification: `PROJECT.md`
- Testing Strategy: `TESTING_STRATEGY.md`

## Claude Code Agents

### Design Compliance Analyzer
When the user asks about:
- "design compliance" or "implementation vs design"
- "what's missing from the design" or "design verification"
- "find duplicates" or "duplicate definitions"
- "code smells" or "architectural issues"
- "code review against spec/design"

**Automatically use the design-compliance agent** which will:
1. Perform exhaustive three-pass searches before claiming anything is "not found"
2. Provide file:line evidence for every claim
3. Check for duplicate definitions
4. Document all searches performed
5. Never make assumptions - only report verified findings

Agent location: `.claude/agents/design-compliance.md`

Example: If user says "Check if our command system matches the design", invoke the design-compliance agent to perform systematic verification with evidence.