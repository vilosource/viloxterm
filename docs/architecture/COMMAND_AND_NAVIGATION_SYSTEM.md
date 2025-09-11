# Command and Navigation System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Command System Architecture](#command-system-architecture)
3. [Keyboard Shortcut System](#keyboard-shortcut-system)
4. [Pane Navigation System](#pane-navigation-system)
5. [Available Commands and Shortcuts](#available-commands-and-shortcuts)
6. [Implementation Details](#implementation-details)
7. [Design Patterns](#design-patterns)

## Overview

The ViloApp command and navigation system provides a comprehensive framework for:
- Executing commands via keyboard shortcuts or command palette
- Managing split pane navigation with numbered pane selection
- Handling keyboard input across different widget types (terminals, editors)

## Command System Architecture

### Core Components

#### 1. Command Registry (`core/commands/registry.py`)
- Central repository for all registered commands
- Singleton pattern ensures single source of truth
- Tracks command metadata: ID, title, category, handler, shortcuts

#### 2. Command Decorator (`core/commands/decorators.py`)
```python
@command(
    id="workbench.action.splitRight",
    title="Split Editor Right",
    category="View",
    shortcut="ctrl+\\"
)
def split_right(context):
    # Implementation
```
- Auto-registers commands when modules are imported
- Supports optional keyboard shortcuts
- Queues shortcuts for later registration with keyboard service

#### 3. Command Executor (`core/commands/executor.py`)
- Validates context requirements before execution
- Provides "when" clause support for conditional commands
- Returns CommandResult with success/error status

### Command Flow
1. **Registration**: Commands decorated with `@command` are auto-registered
2. **Discovery**: Command palette queries registry for available commands
3. **Execution**: Executor validates context and runs command handler
4. **Result**: Returns success/error with optional return value

## Keyboard Shortcut System

### Architecture

#### 1. Shortcut Manager (`core/keyboard/shortcuts.py`)
- Maps key sequences to command IDs
- Handles QShortcut creation and signal connection
- Supports chord sequences (e.g., "Ctrl+K Ctrl+S")

#### 2. Keyboard Service (`core/keyboard/service.py`)
- Initializes shortcut system
- Loads shortcuts from commands and keymaps
- Manages shortcut lifecycle

#### 3. Shortcut Parsing (`core/keyboard/parser.py`)
- Converts string representations to QKeySequence
- Handles platform-specific modifiers
- Supports multi-key chord sequences

### Event Flow

#### For Native Qt Widgets (Editors)
1. User presses key combination
2. Qt's event system checks for matching QShortcut
3. QShortcut triggers, emitting activated signal
4. Signal handler executes associated command

#### For WebEngine Widgets (Terminals)
1. User presses key combination
2. JavaScript event handler intercepts before xterm.js
3. For reserved shortcuts (like Alt+P):
   - JavaScript prevents default and notifies Qt via QWebChannel
   - Qt executes the command
4. Other keys pass through to terminal

## Pane Navigation System

### Overview
The pane navigation system allows quick switching between split panes using keyboard shortcuts.

### Components

#### 1. Split Pane Model (`ui/widgets/split_pane_model.py`)
- Maintains tree structure of split panes
- Manages pane numbering (1-9)
- Handles pane lifecycle (create, split, close)

```python
class SplitPaneModel:
    def toggle_pane_numbers(self) -> bool:
        """Toggle visibility of pane numbers"""
        self.show_pane_numbers = not self.show_pane_numbers
        self.update_pane_indices()
        return self.show_pane_numbers
    
    def update_pane_indices(self):
        """Assign numbers 1-9 to panes in left-to-right, top-to-bottom order"""
        # Depth-first traversal of pane tree
```

#### 2. Pane Headers (`ui/widgets/pane_header.py`)
- Displays pane number when enabled
- Shows active/inactive state
- Provides close button

#### 3. Focus Sink Widget (`ui/widgets/focus_sink.py`)
- Invisible widget that captures keyboard focus during command mode
- Intercepts digit keys (1-9) for pane selection
- Handles Escape for cancellation

```python
class FocusSinkWidget(QWidget):
    digitPressed = Signal(int)  # Emits pane number
    cancelled = Signal()        # Emits on Escape
    
    def enter_command_mode(self, original_focus_widget=None):
        self.grabKeyboard()  # Exclusive keyboard capture
        self.setFocus()
```

### Navigation Flow

1. **Activation** (Alt+P)
   - For terminals: JavaScript intercepts Alt+P, notifies Qt via QWebChannel
   - For editors: Qt shortcut system handles directly
   - Command `workbench.action.togglePaneNumbers` executes

2. **Command Mode**
   - Pane numbers become visible in headers
   - FocusSink widget takes focus and grabs keyboard
   - System waits for user input

3. **Pane Selection** (1-9 keys)
   - FocusSink captures digit keypress
   - Emits signal with pane number
   - WorkspaceService finds pane by number and focuses it
   - Command mode exits, numbers hide

4. **Cancellation** (Escape)
   - FocusSink captures Escape
   - Command mode exits
   - Focus returns to original widget
   - Numbers hide

### Terminal-Specific Handling

Terminals require special handling because xterm.js consumes keyboard events:

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