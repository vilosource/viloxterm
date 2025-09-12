# Command and Navigation System Architecture

This document provides a comprehensive guide to the command system, keyboard navigation, and service layer patterns used in the application. It complements the `KEYBOARD_SHORTCUT_ARCHITECTURE.md` by focusing on the command pattern implementation and architectural decisions.

## Table of Contents

1. [Command System Architecture](#command-system-architecture)
2. [Multi-key Shortcuts (Chord Sequences)](#multi-key-shortcuts-chord-sequences)
3. [Service Layer Pattern](#service-layer-pattern)
4. [Command Palette Integration](#command-palette-integration)
5. [Context Evaluation System](#context-evaluation-system)
6. [Command Lifecycle](#command-lifecycle)

## Command System Architecture

The command system is the central abstraction for all user actions in the application. Every action - whether triggered by keyboard shortcut, menu item, or command palette - goes through the command system.

### Core Components

#### 1. Command Class (`core/commands/base.py`)

The `Command` dataclass represents an executable action:

```python
@dataclass
class Command:
    # Identity
    id: str                    # Unique identifier (e.g., "file.newEditorTab")
    title: str                 # Display name (e.g., "New Editor Tab")
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
    id="workbench.action.splitRight",
    title="Split Pane Right",
    category="Workspace",
    description="Split the active pane horizontally",
    shortcut="ctrl+\\",
    icon="split-horizontal",
    when="workbench.pane.canSplit"
)
def split_pane_right_command(context: CommandContext) -> CommandResult:
    """Split active pane horizontally using WorkspaceService."""
    workspace_service = context.get_service(WorkspaceService)
    new_pane_id = workspace_service.split_active_pane("horizontal")
    return CommandResult(success=True, value={'new_pane_id': new_pane_id})
```

**How the Decorator Works:**

1. **Function Wrapping**: The decorated function becomes the command handler
2. **Auto-Registration**: Command is automatically registered with CommandRegistry
3. **Error Handling**: Wrapped in try-catch to always return CommandResult
4. **Shortcut Registration**: If shortcut provided, attempts to register with KeyboardService

**Implementation Details (`core/commands/decorators.py`, lines 68-146):**
```python
def decorator(func: Callable) -> Command:
    @wraps(func)
    def handler(context: CommandContext) -> CommandResult:
        try:
            result = func(context)
            # Ensure we return a CommandResult
            if not isinstance(result, CommandResult):
                return CommandResult(success=True, value=result)
            return result
        except Exception as e:
            logger.error(f"Error in command {id}: {e}", exc_info=True)
            return CommandResult(success=False, error=str(e))
    
    # Create the command
    cmd = Command(id=id, title=title, handler=handler, ...)
    
    # Auto-register if requested
    if register:
        command_registry.register(cmd)
        
        # Auto-register shortcut if provided
        if shortcut:
            # ... shortcut registration logic
```

### CommandRegistry Singleton

The `CommandRegistry` (`core/commands/registry.py`) is a singleton managing all commands:

```python
class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[str, List[Command]] = {}
        self._shortcuts: Dict[str, List[str]] = {}  # shortcut -> [command_ids]
        self._keywords_index: Dict[str, Set[str]] = {}  # keyword -> {command_ids}
```

**Key Features:**
- **Singleton Pattern**: Ensures single source of truth for all commands
- **Multiple Indexes**: Commands indexed by ID, category, shortcut, and keywords
- **Conflict Detection**: Warns about duplicate shortcuts
- **Observer Pattern**: Notifies listeners when commands are registered/unregistered

### Command Categories

Standard categories (`core/commands/base.py`, lines 253-267):
- **FILE**: File operations
- **EDIT**: Editing operations
- **VIEW**: View/UI operations
- **NAVIGATION**: Navigation between panes/tabs
- **TERMINAL**: Terminal operations
- **WORKSPACE**: Workspace management
- **INTERNAL**: Hidden from UI
- **EXPERIMENTAL**: Experimental features

## Multi-key Shortcuts (Chord Sequences)

The system supports multi-key shortcuts like "Ctrl+K W" (close pane). This is implemented through the KeyboardService's chord detection mechanism.

### How Chord Detection Works

1. **First Key Detection**: When a potential chord starter (e.g., Ctrl+K) is pressed, the system enters "chord mode"
2. **Timeout Window**: A 2-second window opens for the next key
3. **Second Key**: If pressed within timeout, completes the chord
4. **Cancellation**: Any non-matching key or timeout cancels chord mode

### Implementation Example

The close pane command uses a chord:

```python
@command(
    id="workbench.action.closeActivePane",
    title="Close Active Pane",
    category="Workspace",
    shortcut="ctrl+k w",  # Note the space indicating a chord
    when="workbench.pane.count > 1"
)
def close_active_pane_command(context: CommandContext) -> CommandResult:
    # Implementation
```

### Chord Registration

When a shortcut contains a space, it's registered as a chord:
- "ctrl+k w" → First: Ctrl+K, Second: W
- "ctrl+k ctrl+w" → First: Ctrl+K, Second: Ctrl+W

## Service Layer Pattern

The service layer pattern separates business logic from UI components and commands.

### Architecture Overview

```
┌─────────────┐
│   Command   │  (User action)
└─────┬───────┘
      │ uses
      ▼
┌─────────────┐
│   Service   │  (Business logic)
└─────┬───────┘
      │ modifies
      ▼
┌─────────────┐
│  UI/Model   │  (State & presentation)
└─────────────┘
```

### Example: WorkspaceService

The `WorkspaceService` (`services/workspace_service.py`) manages workspace operations:

```python
class WorkspaceService:
    def __init__(self, workspace):
        self._workspace = workspace
        self._panes = {}
        self._focus_sink = FocusSinkWidget()
        # ... initialization
    
    def split_active_pane(self, orientation: str) -> Optional[str]:
        """Split the active pane in the specified orientation."""
        # Business logic for splitting panes
        widget = self._workspace.get_current_split_widget()
        if widget:
            new_pane_id = widget.split_active_pane(orientation)
            # Track new pane, update state
            return new_pane_id
        return None
```

### Service Discovery Pattern

Services are discovered through the CommandContext:

```python
def my_command(context: CommandContext) -> CommandResult:
    # Get service through context
    workspace_service = context.get_service(WorkspaceService)
    
    # Use service
    result = workspace_service.some_operation()
    
    return CommandResult(success=True, value=result)
```

**Benefits:**
1. **Decoupling**: Commands don't directly depend on service implementations
2. **Testability**: Services can be mocked in tests
3. **Reusability**: Services can be used by multiple commands
4. **Separation of Concerns**: UI logic separate from business logic

### ServiceLocator Integration

The modern approach uses ServiceLocator (`services/service_locator.py`):

```python
# In CommandContext.get_service() (lines 69-106)
def get_service(self, service_type: type) -> Any:
    # First try ServiceLocator if available
    if self._service_locator is None:
        from services.service_locator import ServiceLocator
        self._service_locator = ServiceLocator.get_instance()
    
    if self._service_locator:
        service = self._service_locator.get(service_type)
        if service:
            return service
    
    # Fall back to legacy services dict
    # ... fallback logic
```

## Command Palette Integration

The command palette provides a searchable interface for all commands.

### How Commands Appear in the Palette

Commands are shown if:
1. `visible` property is True
2. `when` clause evaluates to True (if present)
3. User has appropriate permissions

### Search and Filtering

The palette uses fuzzy search across:
- Command title
- Command description
- Keywords array
- Category name

### Execution from Palette

When a command is selected:
1. Palette closes
2. CommandContext is created with current state
3. Command handler is executed
4. Result is logged/displayed

## Context Evaluation System

The `when` clause enables conditional command availability based on application state.

### When Clause Examples

```python
# Only available when multiple panes exist
when="workbench.pane.count > 1"

# Only in editor context
when="editorFocus"

# Complex conditions
when="editorFocus && !editorReadonly && editorLangId == 'python'"
```

### Evaluation Process

The `WhenClauseEvaluator` (`core/context/evaluator.py`) parses and evaluates expressions:

```python
def can_execute(self, context: Dict[str, Any]) -> bool:
    if not self.enabled:
        return False
    
    if self.when:
        from core.context.evaluator import WhenClauseEvaluator
        return WhenClauseEvaluator.evaluate(self.when, context)
    
    return True
```

### Context Variables

Common context variables:
- `workbench.pane.count`: Number of open panes
- `workbench.pane.focused`: Whether a pane is focused
- `editorFocus`: Editor has focus
- `terminalFocus`: Terminal has focus
- `sidebarVisible`: Sidebar is visible

## Command Lifecycle

### 1. Registration Phase

```python
# Command defined with decorator
@command(id="my.command", ...)
def my_command(context): ...

# Decorator flow:
1. Create Command instance
2. Register with CommandRegistry
3. Register shortcut with KeyboardService
4. Index by category, keywords
```

### 2. Discovery Phase

Commands can be discovered through:
- CommandRegistry.get_command(id)
- CommandRegistry.get_commands_by_category(category)
- CommandRegistry.search(query)
- Command palette UI

### 3. Execution Phase

```python
# Execution flow:
1. Trigger (shortcut/palette/menu)
   ↓
2. Create CommandContext
   ↓
3. Check can_execute() with when clause
   ↓
4. Call command.execute(context)
   ↓
5. Handler function runs
   ↓
6. Return CommandResult
   ↓
7. Handle result (log/display/state update)
```

### 4. Error Handling

All command execution is wrapped in error handling:

```python
try:
    result = self.handler(context)
    if not isinstance(result, CommandResult):
        result = CommandResult(success=True, value=result)
    return result
except Exception as e:
    logger.error(f"Error executing command {self.id}: {e}", exc_info=True)
    return CommandResult(success=False, error=str(e))
```

## Best Practices

### 1. Command Design

- **Single Responsibility**: Each command should do one thing
- **Idempotent**: Commands should be safe to run multiple times
- **Context-Free**: Don't store state in command objects
- **Service Layer**: Use services for business logic

### 2. Naming Conventions

```python
# Command IDs: category.action.target
"file.new.editorTab"
"workspace.split.right"
"terminal.clear.buffer"

# Handler functions: action_target_command
def new_editor_tab_command(context): ...
def split_right_command(context): ...
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
    context.services['WorkspaceService'] = mock_service
    
    # Execute command
    result = split_pane_right_command(context)
    
    # Verify
    assert result.success
    mock_service.split_active_pane.assert_called_once_with("horizontal")
```

## Summary

The command system provides a robust, extensible architecture for handling user actions:

1. **Partially Centralized**: While the command system is the preferred architecture, not all actions go through it:
   - **Commands**: Primary keyboard shortcuts, command palette actions, some menu items
   - **Direct Connections**: UI button clicks, activity bar toggles, tab context menus, pane controls
2. **Discoverable**: Commands are searchable and browsable in the palette
3. **Context-Aware**: Commands can be conditionally available based on application state
4. **Service-Oriented**: Business logic separated from UI through service layer
5. **Error-Resilient**: Comprehensive error handling throughout the system
6. **Testable**: Clear separation of concerns enables easy unit and integration testing

### Exceptions to Command System

Several UI components bypass the command system for performance and simplicity:

#### Activity Bar (ui/activity_bar.py:80,87,94,104)
- View toggles use direct signal connections
- Example: `self.explorer_action.toggled.connect(lambda checked: self.on_action_toggled("explorer", checked))`
- Emits `view_changed` and `toggle_sidebar` signals directly

#### Tab Management (ui/workspace_simple.py:317-345)
- Context menu actions connect directly to methods
- Examples:
  - `duplicate_action.triggered.connect(lambda: self.duplicate_tab(index))`
  - `close_action.triggered.connect(lambda: self.close_tab(index))`
  - `rename_action.triggered.connect(lambda: self.start_tab_rename(...))`

#### Pane Controls (ui/widgets/pane_header.py:88-103)
- Header buttons emit signals directly
- Examples:
  - `self.split_h_button.clicked.connect(self.split_horizontal_requested.emit)`
  - `self.close_button.clicked.connect(self.close_requested.emit)`

#### Split Pane Context Menu (ui/widgets/split_pane_widget.py:172-194)
- Menu actions connect to local methods
- Example: `split_h.triggered.connect(lambda: self.request_split("horizontal"))`

### Design Rationale

This hybrid approach balances several concerns:

1. **Performance**: Direct connections avoid command system overhead for frequent UI operations
2. **Simplicity**: Simple UI interactions don't need command abstraction
3. **Discoverability**: Important actions are still exposed through commands
4. **Consistency**: Keyboard shortcuts uniformly use the command system
5. **Testability**: Both patterns are testable, just with different approaches

This architecture ensures consistency where it matters most (keyboard shortcuts and major actions) while maintaining simplicity for basic UI interactions.

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
}, true);  // Use capture phase
```

## Directional Pane Navigation (Alt+Arrow)

### Overview
The directional navigation system allows users to navigate between split panes using Alt+Arrow keys. The system uses the tree structure combined with position tracking to find the most intuitive target pane.

### Algorithm
The navigation algorithm (`SplitPaneModel.find_pane_in_direction()`) works by:

1. **Calculate Position Bounds**: Each pane has normalized bounds [x1, y1, x2, y2] in range [0.0, 1.0], calculated by accumulating split ratios while traversing the tree.

2. **Find Candidates**: Identify all panes in the target direction based on center positions:
   - **Left**: Target center X < source center X
   - **Right**: Target center X > source center X
   - **Up**: Target center Y < source center Y
   - **Down**: Target center Y > source center Y

3. **Score Candidates**: Rank candidates by:
   - **Primary**: Maximum overlap in perpendicular axis (Y-overlap for left/right, X-overlap for up/down)
   - **Secondary**: Minimum distance in movement direction
   - **Tiebreaker**: Prefer rightmost for left navigation, leftmost for right, etc.

### Example Navigation
```
Layout:
┌─────────┬─────────┐
│    A    │    B    │
├─────────┼─────────┤
│    C    │    D    │
└─────────┴─────────┘

From A: Alt+Right → B, Alt+Down → C
From B: Alt+Left → A, Alt+Down → D
From C: Alt+Right → D, Alt+Up → A
From D: Alt+Left → C, Alt+Up → B
```

### Implementation Files
- **Algorithm**: `ui/widgets/split_pane_model.py` - `calculate_pane_bounds()`, `find_pane_in_direction()`
- **Commands**: `core/commands/builtin/navigation_commands.py` - Alt+Arrow shortcuts
- **Service**: `services/workspace_service.py` - `navigate_in_direction()`
- **Documentation**: `docs/architecture/DIRECTIONAL_PANE_NAVIGATION.md` - Full algorithm details

## Available Commands and Shortcuts

### File Commands
- `file.newEditorTab` - **Ctrl+N** - New editor tab
- `file.newTerminalTab` - **Ctrl+`** - New terminal tab
- `file.closeTab` - **Ctrl+W** - Close current tab
- `file.saveState` - **Ctrl+S** - Save application state

### View Commands
- `view.toggleTheme` - **Ctrl+T** - Toggle light/dark theme
- `view.toggleSidebar` - **Ctrl+B** - Show/hide sidebar
- `view.toggleMenuBar` - **Ctrl+Shift+M** - Show/hide menu bar
- `view.toggleFullScreen` - **F11** - Toggle fullscreen mode

### Workspace Commands
- `workbench.action.splitRight` - **Ctrl+\\** - Split pane horizontally
- `workbench.action.splitDown` - **Ctrl+Shift+\\** - Split pane vertically
- `workbench.action.closeActivePane` - **Ctrl+K W** - Close active pane
- `workbench.action.togglePaneNumbers` - **Alt+P** - Toggle pane numbers

### Navigation Commands
- `workbench.action.focusNextPane` - **Tab** - Focus next pane
- `workbench.action.focusPreviousPane` - **Shift+Tab** - Focus previous pane
- `workbench.action.nextTab` - **Ctrl+PageDown** - Next tab
- `workbench.action.previousTab` - **Ctrl+PageUp** - Previous tab

### Directional Navigation
- `workbench.action.focusLeftPane` - **Alt+Left** - Focus pane to the left
- `workbench.action.focusRightPane` - **Alt+Right** - Focus pane to the right
- `workbench.action.focusAbovePane` - **Alt+Up** - Focus pane above
- `workbench.action.focusBelowPane` - **Alt+Down** - Focus pane below

### Editor Commands
- `editor.action.cut` - **Ctrl+X** - Cut text
- `editor.action.copy` - **Ctrl+C** - Copy text
- `editor.action.paste` - **Ctrl+V** - Paste text
- `editor.action.selectAll` - **Ctrl+A** - Select all text
- `editor.action.undo` - **Ctrl+Z** - Undo
- `editor.action.redo` - **Ctrl+Shift+Z** - Redo

### Command Palette
- `commandPalette.show` - **Ctrl+Shift+P** - Show command palette

## Implementation Details

### MVC Architecture in Split Panes

```
SplitPaneModel (Model)
├── Tree structure of nodes
├── Pane numbering logic
├── AppWidget lifecycle
└── State management

SplitPaneWidget (View)
├── Renders tree as Qt widgets
├── Handles visual updates
├── Manages PaneContent wrappers
└── Event delegation to model

Implicit Controller
├── Command handlers
├── Service layer
└── Event handlers
```

### Service Layer Architecture

```python
class WorkspaceService(Service):
    def toggle_pane_numbers(self) -> bool:
        widget = self._workspace.get_current_split_widget()
        visible = widget.toggle_pane_numbers()
        
        # Update context for conditional commands
        context_manager.set('workbench.panes.numbersVisible', visible)
        
        # Notify observers
        self.notify('pane_numbers_toggled', {'visible': visible})
        
        return visible
    
    def switch_to_pane_by_number(self, number: int) -> bool:
        # Find pane ID for number
        # Focus the pane
        # Return success status
```

### Focus Management

The system maintains proper keyboard focus through:

1. **AppWidget Base Class**
   - `request_focus()` - Request focus for this widget
   - `focus_widget()` - Actually set keyboard focus (overridden by subclasses)

2. **Terminal Focus**
   ```python
   def focus_widget(self):
       if self.web_view:
           self.web_view.setFocus()
           # Also focus terminal element in page
           if self.bridge:
               self.bridge.focus_terminal_element(self.web_view)
   ```

3. **Editor Focus**
   ```python
   def focus_widget(self):
       if self.editor:
           self.editor.setFocus()
   ```

## Design Patterns

### 1. Command Pattern
- Encapsulates actions as command objects
- Enables undo/redo, queuing, logging
- Decouples UI from business logic

### 2. Observer Pattern
- Services notify observers of state changes
- Loose coupling between components
- Used for theme changes, layout updates

### 3. Singleton Pattern
- CommandRegistry ensures single instance
- ServiceLocator provides global access
- IconManager maintains theme state

### 4. Decorator Pattern
- `@command` decorator for auto-registration
- Adds metadata to function handlers
- Simplifies command definition

### 5. Strategy Pattern
- Different focus strategies for widget types
- Keyboard handling varies by widget
- Pluggable shortcut providers (keymaps)

### 6. Model-View Pattern
- Split pane system separates data from presentation
- Model owns business logic and state
- View handles rendering and user interaction

## Testing Considerations

### Command System
- Test command registration and discovery
- Verify context validation
- Test keyboard shortcut mapping

### Pane Navigation
- Test number assignment algorithm
- Verify focus transfer
- Test command mode entry/exit

### Keyboard Handling
- Test shortcuts in different widget types
- Verify chord sequences work
- Test platform-specific modifiers

## Future Enhancements

1. **Vim Mode Support**
   - Modal editing shortcuts
   - Custom command mode
   - Motion commands

2. **Custom Keymaps**
   - User-defined shortcuts
   - Import/export keymaps
   - Conflict resolution UI

3. **Advanced Navigation**
   - Pane history (back/forward)
   - Named pane bookmarks
   - Pane groups/workspaces

4. **Command Macros**
   - Record command sequences
   - Playback with single shortcut
   - Parameterized macros