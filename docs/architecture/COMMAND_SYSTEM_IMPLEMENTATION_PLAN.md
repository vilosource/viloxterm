# Command System Implementation Plan

## Executive Summary

This document outlines the comprehensive plan to transform ViloApp's architecture from hardcoded QActions to a centralized command system that will serve as the foundation for all current and future features including keyboard shortcuts, command palette, pane navigation, and extensibility.

## Current State Analysis

### What Works Well (Keep)
- **AppWidget System**: Already has `action_requested` signals perfect for command integration
- **SplitPane Model-View Architecture**: Clean separation, works perfectly with commands
- **Tab-based Workspace**: Solid foundation for command targeting
- **Terminal Integration**: Complex but well-architected
- **Theme & State Management**: Just needs command integration

### What Needs Rebuilding (Burn Down)
- **Hardcoded QActions**: 15+ actions in `MainWindow.create_menu_bar()`
- **Direct Method Calls**: `self.workspace.add_editor_tab()` scattered throughout
- **Hardcoded Shortcuts**: `setShortcut("Ctrl+N")` with no central management
- **No Discoverability**: Actions hidden in menus with no command palette
- **No Context System**: Can't have context-sensitive shortcuts
- **Business Logic in UI**: Logic mixed with presentation layer

## Architecture Vision

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
├───────────────────┬───────────────────┬─────────────────────┤
│   Command Palette │    Menus/Toolbars │   Keyboard Input    │
└─────────┬─────────┴─────────┬─────────┴──────────┬──────────┘
          │                   │                     │
          ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Command System                          │
├─────────────────┬───────────────────┬───────────────────────┤
│ Command Registry│ Keyboard Service  │  Context Manager      │
├─────────────────┼───────────────────┼───────────────────────┤
│ Command Executor│ Shortcut Registry │  When Evaluator       │
└─────────────────┴───────────────────┴───────────────────────┘
          │                                         ▲
          ▼                                         │
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Workspace   │   Editor     │   Terminal   │     UI         │
│   Service    │   Service    │   Service    │   Service      │
└──────────────┴──────────────┴──────────────┴────────────────┘
          │                                         ▲
          ▼                                         │
┌─────────────────────────────────────────────────────────────┐
│                    Application Core                          │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  MainWindow  │  Workspace   │  SplitPane   │   AppWidget    │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## Implementation Phases

### Phase 1: Command System Foundation (Days 1-4)

#### Goal
Create the core command infrastructure that all features will build upon.

#### Directory Structure
```
core/
├── commands/
│   ├── __init__.py
│   ├── base.py              # Command base class
│   ├── registry.py          # CommandRegistry singleton
│   ├── executor.py          # CommandExecutor with undo/redo
│   ├── context.py           # CommandContext
│   ├── decorators.py        # @command decorator
│   └── builtin/            # Built-in commands
│       ├── __init__.py
│       ├── file_commands.py
│       ├── view_commands.py
│       ├── navigation_commands.py
│       └── debug_commands.py
├── keyboard/
│   ├── __init__.py
│   ├── service.py           # KeyboardService singleton
│   ├── shortcuts.py         # Shortcut management
│   ├── parser.py            # Key sequence parsing
│   ├── conflicts.py         # Conflict resolution
│   └── keymaps/
│       ├── default.json
│       ├── vscode.json
│       └── vim.json
└── context/
    ├── __init__.py
    ├── manager.py           # ContextManager singleton
    ├── keys.py              # Context key definitions
    ├── evaluator.py         # When clause evaluator
    └── providers.py         # Context providers
```

#### Command Class Design
```python
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any, List

@dataclass
class Command:
    """Represents an executable command in the system."""
    
    # Identity
    id: str                          # "workbench.action.toggleSidebar"
    title: str                       # "Toggle Sidebar"
    category: str                    # "View"
    
    # UI Metadata
    description: Optional[str] = None      # For command palette
    icon: Optional[str] = None            # Icon identifier
    keywords: List[str] = field(default_factory=list)  # Search terms
    
    # Execution
    handler: Callable[..., Any] = None    # Function to execute
    args: Optional[Dict[str, Any]] = None # Default arguments
    
    # Keyboard
    shortcut: Optional[str] = None         # Default keybinding
    when: Optional[str] = None            # Context expression
    
    # Undo/Redo
    undo_handler: Optional[Callable] = None
    redo_handler: Optional[Callable] = None
    supports_undo: bool = False
    
    # State
    visible: bool = True                  # Show in palette
    enabled: bool = True                  # Can execute
    checked: Optional[bool] = None        # For toggle commands
    
    # Grouping
    group: Optional[str] = None           # Menu group
    order: int = 0                        # Sort order
```

#### Context System
```python
class ContextKey:
    """Standard context keys for the application."""
    
    # Focus contexts
    EDITOR_FOCUS = "editorFocus"
    TERMINAL_FOCUS = "terminalFocus"
    SIDEBAR_FOCUS = "sidebarFocus"
    ACTIVITY_BAR_FOCUS = "activityBarFocus"
    COMMAND_PALETTE_FOCUS = "commandPaletteFocus"
    
    # Visibility contexts
    SIDEBAR_VISIBLE = "sidebarVisible"
    TERMINAL_VISIBLE = "terminalVisible"
    MENU_BAR_VISIBLE = "menuBarVisible"
    
    # State contexts
    HAS_OPEN_EDITORS = "hasOpenEditors"
    HAS_MULTIPLE_TABS = "hasMultipleTabs"
    HAS_SELECTION = "hasSelection"
    CAN_SPLIT = "canSplit"
    IS_FULL_SCREEN = "isFullScreen"
    
    # Content contexts
    ACTIVE_TAB_TYPE = "activeTabType"
    ACTIVE_PANE_TYPE = "activePaneType"
    PANE_COUNT = "paneCount"
    TAB_COUNT = "tabCount"
    
    # Mode contexts (future)
    VIM_MODE = "vimMode"
    VIM_INSERT_MODE = "vimInsertMode"
    SEARCH_MODE = "searchMode"
    DEBUG_MODE = "debugMode"
    
    # File contexts
    RESOURCE_EXTENSION = "resourceExtension"
    IS_UNTITLED = "isUntitled"
    IS_DIRTY = "isDirty"
```

#### Command Registry
```python
class CommandRegistry:
    """Central registry for all commands."""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[str, List[Command]] = {}
        self._shortcuts: Dict[str, str] = {}  # shortcut -> command_id
        self._observers: List[Callable] = []
        
    def register(self, command: Command) -> None:
        """Register a command."""
        if command.id in self._commands:
            logger.warning(f"Overwriting existing command: {command.id}")
            
        self._commands[command.id] = command
        self._index_command(command)
        self._notify_observers('registered', command)
        
    def get_command(self, command_id: str) -> Optional[Command]:
        """Get a command by ID."""
        return self._commands.get(command_id)
        
    def get_executable_commands(self, context: Dict[str, Any]) -> List[Command]:
        """Get all commands that can execute in the current context."""
        return [
            cmd for cmd in self._commands.values()
            if self._can_execute(cmd, context)
        ]
        
    def _can_execute(self, command: Command, context: Dict[str, Any]) -> bool:
        """Check if a command can execute in the given context."""
        if not command.enabled:
            return False
        if command.when:
            return WhenClauseEvaluator.evaluate(command.when, context)
        return True
```

### Phase 2: Service Layer Extraction (Days 5-6)

#### Goal
Extract business logic from UI components into testable services.

#### Service Architecture
```
services/
├── __init__.py
├── base.py                  # ServiceBase class
├── service_locator.py       # Service registry and DI
├── workspace_service.py     # Tab and pane operations
├── editor_service.py        # Editor operations
├── terminal_service.py      # Terminal management
├── ui_service.py           # UI state management
└── file_service.py         # File operations
```

#### Example Service Implementation
```python
class WorkspaceService(Service):
    """Manages workspace operations."""
    
    def __init__(self, workspace: Workspace):
        super().__init__()
        self._workspace = workspace
        
    def add_editor_tab(self, name: str = "Editor") -> int:
        """Add a new editor tab."""
        index = self._workspace.add_editor_tab(name)
        self.notify('tab_added', {'type': 'editor', 'name': name, 'index': index})
        return index
        
    def add_terminal_tab(self, name: str = "Terminal") -> int:
        """Add a new terminal tab."""
        index = self._workspace.add_terminal_tab(name)
        self.notify('tab_added', {'type': 'terminal', 'name': name, 'index': index})
        return index
        
    def split_active_pane(self, orientation: str = "horizontal") -> Optional[str]:
        """Split the active pane."""
        widget = self._workspace.get_current_split_widget()
        if widget and widget.active_pane_id:
            if orientation == "horizontal":
                new_id = widget.split_horizontal(widget.active_pane_id)
            else:
                new_id = widget.split_vertical(widget.active_pane_id)
            self.notify('pane_split', {'orientation': orientation, 'new_id': new_id})
            return new_id
        return None
        
    def close_active_pane(self) -> bool:
        """Close the active pane."""
        widget = self._workspace.get_current_split_widget()
        if widget and widget.active_pane_id:
            if widget.get_pane_count() > 1:
                widget.close_pane(widget.active_pane_id)
                self.notify('pane_closed', {'pane_id': widget.active_pane_id})
                return True
        return False
        
    def focus_pane(self, pane_id: str) -> bool:
        """Focus a specific pane."""
        widget = self._workspace.get_current_split_widget()
        if widget:
            widget.set_active_pane(pane_id)
            self.notify('pane_focused', {'pane_id': pane_id})
            return True
        return False
```

### Phase 3: Core Command Migration (Days 7-9)

#### Goal
Replace all existing QActions with commands.

#### Migration Strategy

##### Step 1: Create Command Definitions
```python
# core/commands/builtin/file_commands.py

@command(
    id="file.newEditorTab",
    title="New Editor Tab",
    category="File",
    description="Create a new editor tab",
    shortcut="ctrl+n",
    icon="file-plus"
)
def new_editor_tab_command(context: CommandContext) -> CommandResult:
    """Create a new editor tab."""
    workspace_service = context.get_service(WorkspaceService)
    name = context.args.get('name', 'New Editor')
    
    try:
        index = workspace_service.add_editor_tab(name)
        return CommandResult(success=True, value={'index': index})
    except Exception as e:
        return CommandResult(success=False, error=str(e))

@command(
    id="file.newTerminalTab",
    title="New Terminal Tab",
    category="File",
    description="Create a new terminal tab",
    shortcut="ctrl+`",
    icon="terminal"
)
def new_terminal_tab_command(context: CommandContext) -> CommandResult:
    """Create a new terminal tab."""
    workspace_service = context.get_service(WorkspaceService)
    name = context.args.get('name', 'Terminal')
    
    try:
        index = workspace_service.add_terminal_tab(name)
        return CommandResult(success=True, value={'index': index})
    except Exception as e:
        return CommandResult(success=False, error=str(e))
```

##### Step 2: Update MainWindow
```python
# ui/main_window.py

def create_menu_bar(self):
    """Create menu bar from registered commands."""
    menubar = self.menuBar()
    
    # Generate menus from command categories
    for category in ['File', 'Edit', 'View', 'Debug', 'Help']:
        menu = menubar.addMenu(category)
        self._populate_menu_from_commands(menu, category)
        
def _populate_menu_from_commands(self, menu: QMenu, category: str):
    """Populate a menu with commands from a category."""
    commands = command_registry.get_commands_by_category(category)
    
    groups = {}
    for command in commands:
        group = command.group or 'default'
        if group not in groups:
            groups[group] = []
        groups[group].append(command)
    
    for i, (group, commands) in enumerate(sorted(groups.items())):
        if i > 0:
            menu.addSeparator()
            
        for command in sorted(commands, key=lambda c: c.order):
            action = self._create_action_from_command(command)
            menu.addAction(action)
            
def _create_action_from_command(self, command: Command) -> QAction:
    """Create a QAction from a command."""
    action = QAction(command.title, self)
    
    if command.icon:
        action.setIcon(get_icon(command.icon))
    if command.shortcut:
        action.setShortcut(QKeySequence(command.shortcut))
    if command.description:
        action.setToolTip(command.description)
    if command.checked is not None:
        action.setCheckable(True)
        action.setChecked(command.checked)
        
    action.triggered.connect(
        lambda: self.execute_command(command.id)
    )
    
    return action
    
def execute_command(self, command_id: str, **kwargs):
    """Execute a command by ID."""
    context = self.create_command_context()
    context.args.update(kwargs)
    
    result = command_executor.execute(command_id, context)
    
    if not result.success:
        self.status_bar.set_message(f"Command failed: {result.error}", 3000)
    
    return result
```

#### Commands to Implement

##### File Commands (5)
- `file.newEditorTab` - Create new editor tab (Ctrl+N)
- `file.newTerminalTab` - Create new terminal tab (Ctrl+`)
- `file.newOutputTab` - Create new output tab
- `file.closeTab` - Close current tab (Ctrl+W)
- `file.closeAllTabs` - Close all tabs (Ctrl+K W)

##### View Commands (10)
- `view.toggleSidebar` - Toggle sidebar visibility (Ctrl+B)
- `view.toggleTheme` - Toggle light/dark theme (Ctrl+T)
- `view.toggleMenuBar` - Toggle menu bar (Ctrl+Shift+M)
- `view.showExplorer` - Show explorer in sidebar (Ctrl+Shift+E)
- `view.showSearch` - Show search in sidebar (Ctrl+Shift+F)
- `view.showGit` - Show git in sidebar (Ctrl+Shift+G)
- `view.showSettings` - Show settings in sidebar (Ctrl+,)
- `view.toggleFullScreen` - Toggle fullscreen (F11)
- `view.zoomIn` - Increase font size (Ctrl++)
- `view.zoomOut` - Decrease font size (Ctrl+-)

##### Workspace Commands (8)
- `workbench.action.splitRight` - Split pane horizontally (Ctrl+\)
- `workbench.action.splitDown` - Split pane vertically (Ctrl+Shift+\)
- `workbench.action.closeActivePane` - Close active pane (Ctrl+K W)
- `workbench.action.focusNextPane` - Focus next pane (Tab)
- `workbench.action.focusPreviousPane` - Focus previous pane (Shift+Tab)
- `workbench.action.maximizePane` - Maximize active pane (Ctrl+K Z)
- `workbench.action.evenPaneSizes` - Even all pane sizes
- `workbench.action.movePaneToNewTab` - Move pane to new tab

##### Navigation Commands (10)
- `workbench.action.nextTab` - Next tab (Ctrl+PageDown)
- `workbench.action.previousTab` - Previous tab (Ctrl+PageUp)
- `workbench.action.firstTab` - Go to first tab (Ctrl+1)
- `workbench.action.lastTab` - Go to last tab (Ctrl+9)
- `workbench.action.showPaneSelector` - Show pane overlay (Ctrl+W Q)
- `workbench.action.focusLeftPane` - Focus left pane (Ctrl+K Left)
- `workbench.action.focusRightPane` - Focus right pane (Ctrl+K Right)
- `workbench.action.focusAbovePane` - Focus above pane (Ctrl+K Up)
- `workbench.action.focusBelowPane` - Focus below pane (Ctrl+K Down)
- `workbench.action.focusSidebar` - Focus sidebar (Ctrl+0)

##### Debug Commands (3)
- `debug.resetAppState` - Reset application state (Ctrl+Shift+R)
- `debug.reloadWindow` - Reload window (Ctrl+R)
- `debug.toggleDevTools` - Toggle developer tools (F12)

### Phase 4: Keyboard Service Implementation (Days 10-11)

#### Goal
Centralized keyboard handling with conflict resolution.

#### Keyboard Service Architecture
```python
class KeyboardService:
    """Manages keyboard shortcuts and key events."""
    
    def __init__(self, command_registry: CommandRegistry):
        self._registry = command_registry
        self._shortcuts: Dict[str, List[Shortcut]] = {}
        self._keymap: str = "default"
        self._custom_shortcuts: Dict[str, str] = {}
        
    def register_shortcut(self, key: str, command_id: str, when: Optional[str] = None):
        """Register a keyboard shortcut."""
        shortcut = Shortcut(key=key, command_id=command_id, when=when)
        
        if key not in self._shortcuts:
            self._shortcuts[key] = []
        self._shortcuts[key].append(shortcut)
        
        # Sort by specificity (more specific when clauses first)
        self._shortcuts[key].sort(key=lambda s: self._get_specificity(s.when), reverse=True)
        
    def handle_key_event(self, event: QKeyEvent) -> bool:
        """Handle a key event, returning True if handled."""
        key = self._parse_key_event(event)
        
        if key in self._shortcuts:
            context = context_manager.get_current_context()
            
            for shortcut in self._shortcuts[key]:
                if self._matches_context(shortcut.when, context):
                    command_executor.execute(shortcut.command_id, context)
                    return True
                    
        return False
        
    def load_keymap(self, keymap_name: str):
        """Load a keymap from file."""
        path = f"core/keyboard/keymaps/{keymap_name}.json"
        with open(path) as f:
            keymap = json.load(f)
            
        for binding in keymap['bindings']:
            self.register_shortcut(
                binding['key'],
                binding['command'],
                binding.get('when')
            )
```

### Phase 5: Context System Implementation (Days 12-13)

#### Goal
Enable context-aware commands and shortcuts.

#### Context Manager Implementation
```python
class ContextManager:
    """Manages application context for when clauses."""
    
    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._providers: List[ContextProvider] = []
        self._observers: List[Callable] = []
        
    def set_context(self, key: str, value: Any):
        """Set a context value."""
        old_value = self._context.get(key)
        if old_value != value:
            self._context[key] = value
            self._notify_change(key, old_value, value)
            
    def update_from_focus(self, widget: QWidget):
        """Update context based on focused widget."""
        # Clear all focus contexts
        for key in [k for k in self._context if 'Focus' in k]:
            self.set_context(key, False)
            
        # Set new focus context
        if isinstance(widget, EditorAppWidget):
            self.set_context(ContextKey.EDITOR_FOCUS, True)
            self.set_context(ContextKey.ACTIVE_PANE_TYPE, 'editor')
        elif isinstance(widget, TerminalAppWidget):
            self.set_context(ContextKey.TERMINAL_FOCUS, True)
            self.set_context(ContextKey.ACTIVE_PANE_TYPE, 'terminal')
        elif isinstance(widget, Sidebar):
            self.set_context(ContextKey.SIDEBAR_FOCUS, True)
            
    def evaluate_when_clause(self, when: str) -> bool:
        """Evaluate a when clause expression."""
        if not when:
            return True
        return WhenClauseEvaluator.evaluate(when, self._context)
```

#### When Clause Evaluator
```python
class WhenClauseEvaluator:
    """Evaluates when clause expressions."""
    
    @staticmethod
    def evaluate(expression: str, context: Dict[str, Any]) -> bool:
        """Evaluate a when clause expression."""
        # Parse expression into AST
        ast = WhenClauseParser.parse(expression)
        
        # Evaluate AST
        return WhenClauseEvaluator._evaluate_node(ast, context)
        
    @staticmethod
    def _evaluate_node(node, context):
        if node.type == 'identifier':
            return context.get(node.value, False)
        elif node.type == 'not':
            return not WhenClauseEvaluator._evaluate_node(node.child, context)
        elif node.type == 'and':
            return all(WhenClauseEvaluator._evaluate_node(child, context) 
                      for child in node.children)
        elif node.type == 'or':
            return any(WhenClauseEvaluator._evaluate_node(child, context)
                      for child in node.children)
        elif node.type == 'equals':
            left = context.get(node.left, None)
            return left == node.right
```

### Phase 6: Command Palette Implementation (Days 14-16)

#### Goal
Create VSCode-style command palette for command discovery.

#### Command Palette Architecture
```
ui/command_palette/
├── __init__.py
├── palette.py               # Main palette widget
├── search.py               # Fuzzy search algorithm
├── results.py              # Results list widget
├── providers.py            # Command providers
└── styles.py               # Theming
```

#### Implementation
```python
class CommandPalette(QWidget):
    """VSCode-style command palette."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self._commands = []
        self._recent_commands = []
        
    def show_palette(self):
        """Show the command palette."""
        # Get executable commands for current context
        context = context_manager.get_current_context()
        self._commands = command_registry.get_executable_commands(context)
        
        # Show palette as overlay
        self.move_to_center()
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()
        
    def on_search_changed(self, text: str):
        """Handle search input changes."""
        if not text:
            # Show recent commands
            self.show_results(self._recent_commands[:10])
        else:
            # Fuzzy search
            results = self.fuzzy_search(text, self._commands)
            self.show_results(results[:50])
            
    def fuzzy_search(self, query: str, commands: List[Command]) -> List[Command]:
        """Perform fuzzy search on commands."""
        scores = []
        for command in commands:
            score = self.calculate_score(query, command)
            if score > 0:
                scores.append((score, command))
                
        scores.sort(reverse=True, key=lambda x: x[0])
        return [cmd for _, cmd in scores]
        
    def execute_selected_command(self):
        """Execute the currently selected command."""
        if command := self.get_selected_command():
            context = context_manager.get_current_context()
            command_executor.execute(command.id, context)
            
            # Add to recent commands
            if command not in self._recent_commands:
                self._recent_commands.insert(0, command)
                self._recent_commands = self._recent_commands[:20]
                
            self.hide()
```

### Phase 7: Focus Management Integration (Days 17-18)

#### Goal
Integrate focus management with command and context systems.

#### Focus Manager Enhancement
```python
class FocusManager:
    """Enhanced focus management with command integration."""
    
    def __init__(self):
        self._focus_stack: List[QWidget] = []
        self._focus_groups: Dict[str, FocusGroup] = {}
        
    def on_focus_changed(self, old: QWidget, new: QWidget):
        """Handle focus change events."""
        # Update context
        context_manager.update_from_focus(new)
        
        # Update focus stack
        if new and new not in self._focus_stack:
            self._focus_stack.append(new)
            self._focus_stack = self._focus_stack[-10:]  # Keep last 10
            
        # Enable/disable commands based on new context
        self._update_command_states()
        
    def focus_next_group(self):
        """Focus next major UI group (F6)."""
        groups = ['activityBar', 'sidebar', 'editor', 'panel', 'statusBar']
        current = self._get_current_group()
        
        idx = groups.index(current) if current in groups else -1
        next_idx = (idx + 1) % len(groups)
        
        self.focus_group(groups[next_idx])
        
    def focus_group(self, group_name: str):
        """Focus a specific UI group."""
        if group := self._focus_groups.get(group_name):
            if widget := group.get_first_focusable():
                widget.setFocus()
                context_manager.set_context(f'{group_name}Focus', True)
```

### Phase 8: Testing Infrastructure (Days 19-20)

#### Goal
Comprehensive testing for the command system.

#### Test Structure
```
tests/
├── unit/
│   ├── test_commands.py
│   ├── test_registry.py
│   ├── test_keyboard.py
│   ├── test_context.py
│   └── test_services.py
├── integration/
│   ├── test_command_execution.py
│   ├── test_keyboard_shortcuts.py
│   ├── test_command_palette.py
│   └── test_focus_navigation.py
└── e2e/
    ├── test_user_workflows.py
    └── test_keyboard_navigation.py
```

#### Example Tests
```python
# tests/unit/test_commands.py

def test_command_registration():
    """Test command registration and retrieval."""
    registry = CommandRegistry()
    
    command = Command(
        id="test.command",
        title="Test Command",
        category="Test",
        handler=lambda ctx: CommandResult(success=True)
    )
    
    registry.register(command)
    assert registry.get_command("test.command") == command
    
def test_command_execution():
    """Test command execution with context."""
    executed = False
    
    def handler(context):
        nonlocal executed
        executed = True
        return CommandResult(success=True)
        
    command = Command(id="test", title="Test", handler=handler)
    executor = CommandExecutor()
    
    context = CommandContext()
    result = executor.execute_command(command, context)
    
    assert executed
    assert result.success
    
def test_context_evaluation():
    """Test when clause evaluation."""
    command = Command(
        id="test",
        title="Test",
        when="editorFocus && !terminalFocus",
        handler=lambda ctx: None
    )
    
    context = {
        "editorFocus": True,
        "terminalFocus": False
    }
    
    assert WhenClauseEvaluator.evaluate(command.when, context)
```

## Migration Path

### Week 1: Foundation
- Days 1-4: Command system core
- Days 5-6: Service layer extraction

### Week 2: Migration
- Days 7-9: Core command migration
- Days 10-11: Keyboard service
- Days 12-13: Context system

### Week 3: Features
- Days 14-16: Command palette
- Days 17-18: Focus management
- Days 19-20: Testing

### Week 4: Polish
- Documentation
- Performance optimization
- User testing
- Bug fixes

## Success Metrics

### Technical Metrics
- ✅ 35+ commands migrated from QActions
- ✅ All existing shortcuts working
- ✅ <10ms command execution time
- ✅ 80%+ test coverage
- ✅ Zero breaking changes for users

### Feature Metrics
- ✅ Command palette with fuzzy search
- ✅ Context-sensitive shortcuts
- ✅ Customizable keybindings
- ✅ Undo/redo support for applicable commands
- ✅ Focus navigation between UI groups

### Architecture Metrics
- ✅ Complete separation of UI and business logic
- ✅ All actions go through command system
- ✅ Services handle all business operations
- ✅ Context system tracks application state
- ✅ Extensible for future features

## Risk Mitigation

### Risk: Breaking Existing Functionality
**Mitigation**:
- Parallel implementation (keep old code during migration)
- Comprehensive test suite before switching
- Feature flag to toggle between old/new system
- Gradual rollout with beta testing

### Risk: Performance Regression
**Mitigation**:
- Benchmark command execution times
- Profile keyboard event handling
- Lazy load command modules
- Cache context evaluations

### Risk: User Confusion
**Mitigation**:
- Keep all existing shortcuts unchanged
- Add tooltips showing new shortcuts
- Provide migration guide
- Show command palette hint on first launch

## Future Features Enabled

### Immediate Benefits
- Command palette for discoverability
- Customizable keyboard shortcuts
- Context-sensitive actions
- Better testability and maintainability

### Phase 2 Features (After Command System)
- Pane navigation with overlay identifiers
- Tab and pane naming with F2 rename
- Advanced search and replace
- File explorer integration

### Phase 3 Features
- Vim mode with modal editing
- Macro recording and playback
- Plugin system for extensions
- Command chaining and composition

### Long-term Vision
- AI-powered command suggestions
- Voice command support
- Mobile companion app control
- Cloud sync for settings and commands

## Conclusion

This command system implementation plan transforms ViloApp from a traditional menu-driven application into a modern, keyboard-first power tool. By building a solid foundation with commands, services, and context management, we enable all planned features while maintaining backward compatibility and improving code quality.

The phased approach ensures steady progress with minimal risk, and the architecture supports unlimited future expansion through the plugin system. This investment in infrastructure will pay dividends as the application grows and evolves.

## Appendices

### Appendix A: Command Naming Convention
```
category.subcategory.action

Examples:
- file.newEditorTab
- view.toggleSidebar
- workbench.action.splitRight
- editor.action.commentLine
- terminal.action.clear
```

### Appendix B: Keyboard Shortcut Syntax
```
modifier+modifier+key

Modifiers: ctrl, shift, alt, cmd (Mac)
Keys: a-z, 0-9, f1-f12, special keys

Examples:
- ctrl+n
- ctrl+shift+p
- alt+f4
- cmd+,
```

### Appendix C: When Clause Syntax
```
Simple: contextKey
Negation: !contextKey
AND: contextKey && otherKey
OR: contextKey || otherKey
Comparison: contextKey == value
Complex: (editorFocus || terminalFocus) && !searchMode
```

### Appendix D: Service Interface Pattern
```python
class IWorkspaceService(Protocol):
    """Interface for workspace operations."""
    
    def add_editor_tab(self, name: str) -> int: ...
    def add_terminal_tab(self, name: str) -> int: ...
    def split_active_pane(self, orientation: str) -> Optional[str]: ...
    def close_active_pane(self) -> bool: ...
    def focus_pane(self, pane_id: str) -> bool: ...
```