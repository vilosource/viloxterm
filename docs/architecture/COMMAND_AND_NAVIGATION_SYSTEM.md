# Command and Navigation System Architecture

This document provides a comprehensive guide to the command system, keyboard navigation, and service layer patterns used in the application. It complements the `KEYBOARD_SHORTCUT_ARCHITECTURE.md` by focusing on the command pattern implementation and architectural decisions.

## Table of Contents

1. [Command System Architecture](#command-system-architecture)
2. [Multi-key Shortcuts (Chord Sequences)](#multi-key-shortcuts-chord-sequences)
3. [Service Layer Pattern](#service-layer-pattern)
4. [Command Palette Integration](#command-palette-integration)
5. [Context Evaluation System](#context-evaluation-system)
6. [Command Lifecycle](#command-lifecycle)
7. [Available Commands and Shortcuts](#available-commands-and-shortcuts)

## Command System Architecture

The command system is the central abstraction for all user actions in the application. Every action - whether triggered by keyboard shortcut, menu item, or command palette - goes through the command system.

### Core Components

#### 1. Command Class (`core/commands/base.py`)

The `Command` dataclass represents an executable action:

```python
@dataclass
class Command:
    # Identity
    id: str                    # Unique identifier (e.g., "workspace.newTab")
    title: str                 # Display name (e.g., "New Tab")
    category: str              # Category for grouping (e.g., "File")
    
    # Execution
    handler: Callable[[CommandContext], CommandResult]  # Function to execute
    
    # UI Metadata
    description: Optional[str] = None     # Detailed description
    icon: Optional[str] = None           # Icon identifier
    keywords: List[str] = field(default_factory=list)  # Search keywords
    
    # Keyboard
    shortcut: Optional[str] = None       # Default keyboard shortcut
    when: Optional[str] = None           # Context expression for availability
    
    # State
    visible: bool = True                 # Show in command palette
    enabled: bool = True                 # Can be executed
```

**Key Design Decisions:**
- **Dataclass Pattern**: Using dataclasses provides automatic initialization, repr, and validation
- **Handler Function**: Commands are just data with a handler function, making them serializable
- **Context-Aware**: The `when` clause enables conditional availability
- **Metadata-Rich**: Extensive metadata supports UI features like icons and tooltips

#### 2. CommandContext (`core/commands/base.py`)

Context passed to command handlers during execution:

```python
class CommandContext:
    def __init__(self, 
                 main_window=None,
                 workspace=None,
                 active_widget=None,
                 services: Optional[Dict[str, Any]] = None,
                 args: Optional[Dict[str, Any]] = None):
        # ... initialization
    
    def get_service(self, service_type: type) -> Any:
        """Get a service by type using ServiceLocator pattern."""
        # First tries ServiceLocator, then falls back to legacy services dict
```

**Key Features:**
- **Service Discovery**: Integrates with ServiceLocator for dependency injection
- **Contextual Information**: Provides access to main window, workspace, active widget
- **Arguments**: Supports command arguments for parameterized commands

#### 3. CommandResult (`core/commands/base.py`)

Standardized result from command execution:

```python
class CommandResult:
    def __init__(self, success: bool, value: Any = None, error: Optional[str] = None):
        self.success = success
        self.value = value
        self.error = error
    
    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.success
```

### The @command Decorator Pattern

The decorator pattern (`core/commands/decorators.py`) simplifies command creation:

```python
@command(
    id="workbench.action.splitPaneHorizontal",
    title="Split Pane Horizontally",
    category="Pane",
    description="Split the current pane horizontally"
)
def split_pane_horizontal_command(context: CommandContext) -> CommandResult:
    """Split the current or specified pane horizontally."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        # Get pane from context or use active
        pane = context.args.get('pane')
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # Split the pane
        workspace.split_pane(pane, "horizontal")
        return CommandResult(success=True)
        
    except Exception as e:
        logger.error(f"Error splitting pane: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))
```

**Benefits:**
- **Auto-Registration**: Commands are automatically registered when the module loads
- **Clear Metadata**: Command metadata is visible at the definition site
- **Type Safety**: The decorator ensures correct function signature

### Command Registry

The `CommandRegistry` (`core/commands/registry.py`) is a singleton that manages all commands:

```python
class CommandRegistry:
    def register(self, command: Command) -> None:
        """Register a command."""
        
    def get_command(self, command_id: str) -> Optional[Command]:
        """Get a command by ID."""
        
    def search_commands(self, query: str) -> List[Command]:
        """Search for commands by title, description, or keywords."""
```

**Features:**
- **Singleton Pattern**: Ensures a single source of truth for commands
- **Search Capabilities**: Supports fuzzy searching across command metadata
- **Category Management**: Groups commands by category for organization

### Command Execution

The `execute_command` function (`core/commands/executor.py`) is the primary interface:

```python
def execute_command(command_id: str, **kwargs) -> CommandResult:
    """
    Execute a command by ID with optional arguments.
    
    Args:
        command_id: The command identifier
        **kwargs: Arguments to pass to the command
        
    Returns:
        CommandResult with success status and optional value/error
    """
```

**Execution Flow:**
1. Look up command in registry
2. Create CommandContext with current state
3. Merge provided kwargs into context.args
4. Call command handler
5. Return standardized CommandResult

## Multi-key Shortcuts (Chord Sequences)

The system supports VSCode-style chord sequences:

### Implementation

```python
class ChordTracker:
    """Tracks multi-key chord sequences."""
    
    def __init__(self):
        self.pending_chord = None
        self.chord_timer = QTimer()
        self.chord_timer.timeout.connect(self.clear_chord)
        
    def process_shortcut(self, shortcut: str) -> Optional[str]:
        """Process a shortcut, potentially as part of a chord."""
        if self.pending_chord:
            # Complete the chord
            full_chord = f"{self.pending_chord} {shortcut}"
            self.clear_chord()
            return full_chord
        elif self.is_chord_prefix(shortcut):
            # Start a chord sequence
            self.pending_chord = shortcut
            self.chord_timer.start(2000)  # 2 second timeout
            return None
        else:
            # Single shortcut
            return shortcut
```

### Common Chord Sequences

- **Ctrl+K Ctrl+C**: Comment selection
- **Ctrl+K Ctrl+U**: Uncomment selection
- **Ctrl+K W**: Close all editors
- **Ctrl+K Ctrl+S**: Save all

## Service Layer Pattern

Services provide business logic separated from UI components:

### Service Access Pattern

The correct pattern for accessing services in commands:

```python
@command(
    id="workbench.action.splitPaneHorizontal",
    title="Split Pane Horizontally",
    category="Pane"
)
def split_pane_horizontal_command(context: CommandContext) -> CommandResult:
    # CORRECT: Use context.get_service() with the service class
    workspace_service = context.get_service(WorkspaceService)
    if not workspace_service:
        return CommandResult(success=False, error="WorkspaceService not available")
    
    # Use the service
    workspace = workspace_service.get_workspace()
    # ...
```

**Important:** Always use `context.get_service(ServiceClass)` not string names.

### Common Services

#### WorkspaceService
```python
class WorkspaceService:
    def get_workspace(self) -> Optional[WorkspaceSimple]:
        """Get the current workspace."""
        
    def split_active_pane(self, direction: str) -> bool:
        """Split the currently active pane."""
        
    def close_active_pane(self) -> bool:
        """Close the currently active pane."""
```

#### TerminalService
```python
class TerminalService:
    def get_active_terminal(self) -> Optional[TerminalWidget]:
        """Get the currently active terminal."""
        
    def create_terminal(self) -> TerminalWidget:
        """Create a new terminal instance."""
```

## Command Palette Integration

The command palette provides a searchable interface for all commands:

### Implementation

```python
class CommandPalette(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_input = QLineEdit()
        self.results_list = QListWidget()
        
        # Get all commands from registry
        self.commands = command_registry.get_all_commands()
        
        # Connect search
        self.search_input.textChanged.connect(self.update_results)
        
    def update_results(self, query: str):
        """Update results based on search query."""
        matching_commands = command_registry.search_commands(query)
        self.display_commands(matching_commands)
```

### Features

- **Fuzzy Search**: Searches across command titles, descriptions, and keywords
- **Category Grouping**: Commands grouped by category for better organization
- **Keyboard Navigation**: Full keyboard support for navigation and execution
- **Recent Commands**: Shows frequently used commands at the top

## Context Evaluation System

The context system determines when commands are available:

### When Clauses

Commands can specify conditions for availability:

```python
@command(
    id="editor.action.commentLine",
    title="Comment Line",
    when="editorTextFocus && !editorReadonly"
)
```

### Context Keys

Common context keys:
- `editorTextFocus`: Editor has focus
- `terminalFocus`: Terminal has focus
- `sidebarVisible`: Sidebar is visible
- `panelFocus`: A panel has focus
- `multipleEditors`: Multiple editors are open

### Evaluation

```python
class WhenClauseEvaluator:
    @staticmethod
    def evaluate(when_clause: str, context: Dict[str, Any]) -> bool:
        """Evaluate a when clause against the current context."""
        # Parse and evaluate the expression
        # Supports &&, ||, !, and parentheses
```

## Command Lifecycle

### Registration Phase

1. **Module Import**: Command modules are imported at startup
2. **Decorator Execution**: @command decorators register commands
3. **Registry Storage**: Commands stored in CommandRegistry

### Execution Phase

1. **Trigger**: User action (keyboard, menu, palette)
2. **Lookup**: Find command in registry
3. **Context Creation**: Build CommandContext with current state
4. **Handler Execution**: Call command handler function
5. **Result Processing**: Handle success/failure

### Example Flow

```python
# 1. User presses Ctrl+T
# 2. Keyboard manager maps to "workspace.newTab"
# 3. execute_command("workspace.newTab") called
# 4. Registry returns Command object
# 5. CommandContext created with main_window, workspace, etc.
# 6. Command handler executed
# 7. New tab created, CommandResult returned
```

## Implementation Best Practices

### 1. Command Design

```python
@command(
    id="category.action.verbNoun",  # Consistent naming
    title="Human Readable Title",
    category="Category",
    description="Detailed description for tooltips"
)
def command_name(context: CommandContext) -> CommandResult:
    """Docstring explains the implementation."""
    pass
```

### 2. Service Access

Always use the type-based service access:
```python
# CORRECT
service = context.get_service(WorkspaceService)

# INCORRECT - Don't use string names
service = context.get_service('WorkspaceService')
```

### 3. Error Handling

Always return CommandResult:
```python
def my_command(context: CommandContext) -> CommandResult:
    try:
        # Command logic
        return CommandResult(success=True, value=result)
    except SpecificError as e:
        # Handle specific errors
        return CommandResult(success=False, error=f"Failed: {e}")
```

### 4. Testing Commands

```python
def test_split_pane_command():
    # Create mock context
    context = CommandContext()
    mock_service = Mock(spec=WorkspaceService)
    
    # Mock ServiceLocator if using new pattern
    with patch('services.service_locator.ServiceLocator.get_instance') as mock_locator:
        mock_locator.return_value.get.return_value = mock_service
        
        # Execute command
        result = split_pane_horizontal_command(context)
        
        # Verify
        assert result.success
        mock_service.get_workspace.assert_called_once()
```

## Summary

The command system provides a robust, extensible architecture for handling user actions:

1. **Mostly Centralized**: The command system is the primary architecture for almost all user actions:
   - **Commands**: All keyboard shortcuts, command palette actions, menu items
   - **Direct Connections**: Only Activity Bar toggles remain non-centralized
2. **Discoverable**: Commands are searchable and browsable in the palette
3. **Context-Aware**: Commands can be conditionally available based on application state
4. **Service-Oriented**: Business logic separated from UI through service layer
5. **Error-Resilient**: Comprehensive error handling throughout the system
6. **Testable**: Clear separation of concerns enables easy unit and integration testing

### Current Architecture Status

As of the Phase 2 implementation, the command system has been successfully centralized for:

#### Fully Centralized Components
- **Tab Management** (`ui/workspace_simple.py:317-345`)
  - All tab context menu actions use `execute_command()`
  - Examples: duplicate, close, rename, close others, close to right
  
- **Pane Controls** (`ui/widgets/pane_header.py:88-103`)
  - Header buttons use `execute_command()` for all actions
  - Split horizontal/vertical, close, maximize
  
- **Split Pane Context Menu** (`ui/widgets/split_pane_widget.py:172-221`)
  - All menu actions use `execute_command()`
  - Split, close, change type operations
  
- **Main Window Menus** (`ui/main_window.py:459-544`)
  - All menu items use `execute_command()`

#### Exception: Activity Bar

The Activity Bar (`ui/activity_bar.py:80-105`) remains the only component using direct signal connections:

```python
# Activity Bar still uses direct connections for performance/complexity reasons
self.explorer_action.toggled.connect(lambda checked: self.on_action_toggled("explorer", checked))
```

This executes `execute_command()` internally but manages complex toggle state directly.

### Design Rationale

This mostly-centralized approach balances several concerns:

1. **Consistency**: All major user actions go through the command system
2. **Performance**: Activity Bar's complex toggle logic remains optimized
3. **Discoverability**: All important actions exposed through commands
4. **Maintainability**: Single pattern for 99% of actions
5. **Testability**: Both command execution and Activity Bar behavior are testable

## Available Commands and Shortcuts

The application currently implements 80+ commands across 11 categories:

### File Commands
- `workspace.newTab` - **Ctrl+T** - New tab (uses default widget type from settings)
- `workspace.newTabWithType` - **Ctrl+Shift+T** - New tab with type selection
- `file.closeTab` - **Ctrl+W** - Close current tab
- `file.saveState` - **Ctrl+S** - Save application state
- `file.restoreState` - Restore application state

### View Commands
- `view.toggleTheme` - **Ctrl+T** - Toggle light/dark theme
- `view.toggleSidebar` - **Ctrl+B** - Show/hide sidebar
- `view.toggleMenuBar` - **Ctrl+Shift+M** - Show/hide menu bar
- `view.toggleFullScreen` - **F11** - Toggle fullscreen mode
- `view.showExplorer` - Show Explorer in sidebar
- `view.showSearch` - Show Search in sidebar
- `view.showGit` - Show Git in sidebar
- `view.showSettings` - Show Settings in sidebar
- `view.resetLayout` - Reset window layout to default

### Workspace Commands
- `workbench.action.splitRight` - **Ctrl+\\** - Split pane horizontally
- `workbench.action.splitDown` - **Ctrl+Shift+\\** - Split pane vertically
- `workbench.action.closeActivePane` - **Ctrl+K W** - Close active pane
- `workbench.action.togglePaneNumbers` - **Alt+P** - Toggle pane numbers
- `workbench.action.nextTab` - **Ctrl+PageDown** - Next tab
- `workbench.action.previousTab` - **Ctrl+PageUp** - Previous tab
- `workbench.action.saveLayout` - Save current layout
- `workbench.action.restoreLayout` - Restore saved layout
- `workbench.action.renamePane` - Rename current pane

### Navigation Commands
- `workbench.action.focusNextPane` - **Tab** - Focus next pane
- `workbench.action.focusPreviousPane` - **Shift+Tab** - Focus previous pane
- `workbench.action.focusLeftPane` - **Alt+Left** - Focus pane to the left
- `workbench.action.focusRightPane` - **Alt+Right** - Focus pane to the right
- `workbench.action.focusAbovePane` - **Alt+Up** - Focus pane above
- `workbench.action.focusBelowPane` - **Alt+Down** - Focus pane below
- `workbench.action.focusSidebar` - Focus sidebar
- `workbench.action.focusActivePane` - Focus active editor pane
- `workbench.action.firstTab` - Go to first tab
- `workbench.action.lastTab` - Go to last tab
- `workbench.action.closeAllTabs` - Close all tabs
- `workbench.action.maximizePane` - Maximize current pane
- `workbench.action.evenPaneSizes` - Make all panes equal size
- `workbench.action.movePaneToNewTab` - Move pane to new tab
- `workbench.action.focusNextGroup` - Focus next pane group
- `workbench.action.focusPreviousGroup` - Focus previous pane group

### Tab Commands
- `workbench.action.duplicateTab` - Duplicate current tab
- `workbench.action.closeTabsToRight` - Close tabs to the right
- `workbench.action.renameTab` - Rename current tab
- `workbench.action.closeOtherTabs` - Close all other tabs

### Pane Commands
- `workbench.action.splitPaneHorizontal` - Split pane horizontally
- `workbench.action.splitPaneVertical` - Split pane vertically
- `workbench.action.closePane` - Close current pane
- `workbench.action.maximizePane` - Maximize/restore pane
- `workbench.action.changePaneType` - Change pane type

### Sidebar Commands
- `workbench.view.explorer` - Show Explorer view
- `workbench.view.search` - Show Search view
- `workbench.view.git` - Show Git/Source Control view
- `workbench.view.settings` - Show Settings view
- `workbench.action.toggleSidebar` - Toggle sidebar visibility

### Editor Commands
- `editor.action.cut` - **Ctrl+X** - Cut text
- `editor.action.copy` - **Ctrl+C** - Copy text
- `editor.action.paste` - **Ctrl+V** - Paste text
- `editor.action.selectAll` - **Ctrl+A** - Select all text
- `editor.action.undo` - **Ctrl+Z** - Undo
- `editor.action.redo` - **Ctrl+Shift+Z** - Redo
- `editor.action.find` - **Ctrl+F** - Find in editor
- `editor.action.replace` - **Ctrl+H** - Find and replace

### Terminal Commands
- `terminal.clear` - Clear terminal output
- `terminal.new` - Create new terminal
- `terminal.copy` - Copy selected text
- `terminal.paste` - Paste text
- `terminal.kill` - Kill terminal process
- `terminal.restart` - Restart terminal

### Command Palette Commands
- `commandPalette.show` - **Ctrl+Shift+P** - Show command palette
- `commandPalette.hide` - Hide command palette
- `commandPalette.refresh` - Refresh command list

### Settings Commands
- `settings.openSettings` - **Ctrl+,** - Open comprehensive settings widget
- `settings.resetSettings` - Reset all settings to defaults
- `settings.showSettingsInfo` - Show settings information
- `settings.toggleTheme` - Toggle application theme
- `settings.changeFontSize` - Change editor font size
- `settings.resetKeyboardShortcuts` - Reset keyboard shortcuts
- `settings.showKeyboardShortcuts` - Show keyboard shortcuts

### Debug Commands (Development)
- `debug.resetAppState` - Reset application state
- `debug.showServiceInfo` - Show service information
- `debug.showCommandInfo` - Show command registry info
- `debug.showWorkspaceInfo` - Show workspace information
- `debug.testCommand` - Test command for development
- `debug.reloadWindow` - Reload application window
- `debug.toggleDevMode` - Toggle developer mode

## Keyboard Shortcut Implementation

### Terminal Shortcuts

For terminal widgets that use WebEngine, special handling is required:

```javascript
// In terminal HTML/JavaScript
document.addEventListener('keydown', function(e) {
    // Alt+P for pane numbers
    if (e.altKey && !e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === "p") {
        // Notify Qt via QWebChannel
        if (window.qtTerminal && window.qtTerminal.js_shortcut_pressed) {
            window.qtTerminal.js_shortcut_pressed("Alt+P");
        }
        e.preventDefault();
        return false;  // Don't let xterm.js process it
    }
    
    // Alt+Arrow keys for directional navigation
    if (e.altKey && !e.ctrlKey && !e.shiftKey) {
        const key = e.key.toLowerCase();
        if (key === "arrowleft" || key === "arrowright" || 
            key === "arrowup" || key === "arrowdown") {
            return false;  // Let Qt handle directional navigation
        }
    }
});
```

This architecture ensures consistency across the application while maintaining flexibility for component-specific optimizations.