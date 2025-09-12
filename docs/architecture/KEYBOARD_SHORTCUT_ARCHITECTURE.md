# Keyboard Shortcut Architecture Guide

## Overview

This guide documents the sophisticated multi-layer architecture used to handle keyboard shortcuts in the Vilo application, with special focus on ensuring shortcuts work reliably across all widgets, including challenging contexts like WebEngine terminals where xterm.js would normally consume all keyboard input.

## Architecture Layers

The keyboard shortcut system consists of three primary layers that work together:

### 1. JavaScript Interception Layer (Terminal-specific)
- **Location**: `ui/terminal/terminal_assets.py`
- **Purpose**: Prevent xterm.js from consuming reserved shortcuts
- **Mechanism**: Custom key event handler attached to terminal instance

### 2. Qt Event Filter Layer
- **Component**: `WebShortcutGuard` class
- **Location**: `core/keyboard/web_shortcut_guard.py`
- **Purpose**: Intercept shortcuts before WebEngine processes them
- **Mechanism**: Event filter installed on QWebEngineView widgets

### 3. Qt Action Layer
- **Location**: `ui/main_window.py`
- **Purpose**: Global shortcut handling via Qt's action system
- **Mechanism**: QAction with ApplicationShortcut context

## Detailed Event Flow: Alt+P Example

Let's trace the complete flow when a user presses Alt+P while focused in a terminal:

### Step 1: JavaScript Layer Interception

```javascript
// In terminal_assets.py (embedded JavaScript)
term.attachCustomKeyEventHandler((e) => {
    if (e.type !== "keydown") return true;
    
    // CRITICAL: Intercept Alt+P for pane navigation
    if (e.altKey && !e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === "p") {
        console.log("Alt+P detected in terminal, notifying Qt");
        
        // Notify Qt bridge (optional)
        if (window.qtTerminal && window.qtTerminal.js_shortcut_pressed) {
            window.qtTerminal.js_shortcut_pressed("Alt+P");
        }
        
        // Prevent xterm.js from processing
        e.preventDefault();
        e.stopPropagation();
        return false;  // Critical: Don't let terminal process Alt+P
    }
    
    return true; // Let other keys pass through
});
```

**Key Points:**
- Returns `false` to prevent xterm.js from seeing the key
- Uses `preventDefault()` and `stopPropagation()` for extra safety
- Optionally notifies Qt bridge for additional handling

### Step 2: Qt Event Filter (WebShortcutGuard)

```python
# In web_shortcut_guard.py
def eventFilter(self, obj, event):
    """Filter events to intercept shortcuts before widgets process them."""
    
    # Handle both ShortcutOverride AND KeyPress events
    if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
        ke = event  # QKeyEvent
        key = ke.key()
        
        if key != Qt.Key_unknown:
            # Build QKeySequence from current key event
            ks = QKeySequence(int(ke.modifiers().value) | int(key))
            
            # Check if this matches any reserved shortcuts
            for reserved in self._reserved_shortcuts:
                if ks.matches(reserved) == QKeySequence.ExactMatch:
                    if event.type() == QEvent.Type.ShortcutOverride:
                        logger.info(f"WebShortcutGuard intercepted ShortcutOverride: {reserved.toString()}")
                        event.accept()   # Tell Qt this is a shortcut
                        return False     # Let Qt process the shortcut
                    else:  # KeyPress
                        logger.info(f"WebShortcutGuard blocked KeyPress: {reserved.toString()}")
                        return True      # Block event from reaching widget
    
    return False  # Not a reserved shortcut
```

**Critical Distinction:**
- **ShortcutOverride**: Accept event but return `False` to let Qt process
- **KeyPress**: Return `True` to block widget from seeing the key

### Step 3: Qt Action Triggering

```python
# In main_window.py, _create_application_shortcuts() method (line 443)
def _create_application_shortcuts(self):
    """
    Create QActions with ApplicationShortcut context for critical shortcuts.
    
    This ensures these shortcuts work even when QWebEngineView has focus,
    as Qt's action system takes precedence over widget key handling when
    combined with our WebShortcutGuard event filter.
    """
    
    # Alt+P - Toggle pane numbers
    toggle_panes_action = QAction("Toggle Pane Numbers", self)
    toggle_panes_action.setShortcut(QKeySequence("Alt+P"))
    toggle_panes_action.setShortcutContext(Qt.ApplicationShortcut)
    toggle_panes_action.triggered.connect(
        lambda: self.execute_command("workbench.action.togglePaneNumbers")
    )
    self.addAction(toggle_panes_action)
    toggle_panes_action.setEnabled(True)
```

**Key Configuration:**
- `Qt.ApplicationShortcut`: Works globally regardless of focus
- Action added to MainWindow for application-wide scope
- Lambda connects to command execution system

### Step 4: Command Execution

```python
# In workspace_commands.py
@command(
    id="workbench.action.togglePaneNumbers",
    title="Toggle Pane Numbers",
    category="View",
    description="Show or hide pane identification numbers",
    # shortcut="alt+p",  # COMMENTED OUT - handled by QAction instead
    icon="hash",
    when=None
)
def toggle_pane_numbers_command(context: CommandContext) -> CommandResult:
    """Enter command mode for pane navigation with visible numbers."""
    workspace_service = context.get_service(WorkspaceService)
    success = workspace_service.enter_pane_command_mode()
    # ... rest of implementation
```

**Important:** Shortcut is commented out in decorator to prevent duplicate registration.

## Reserved Shortcuts Configuration

```python
# In reserved_shortcuts.py
WEBENGINE_RESERVED_SHORTCUTS = [
    # View commands
    "Alt+P",           # Toggle pane numbers
    "Ctrl+B",          # Toggle sidebar
    "Ctrl+T",          # Toggle theme
    # ... more shortcuts
]
```

This list determines which shortcuts WebShortcutGuard will intercept.

## Installation and Setup

### Installing Event Filter on Terminal Widget

```python
# In terminal_app_widget.py
def __init__(self):
    self.web_view = QWebEngineView()
    
    # Install event filter to guard shortcuts
    self._shortcut_guard = WebShortcutGuard(self)
    self._shortcut_guard.set_reserved_shortcuts(get_reserved_shortcuts())
    self.web_view.installEventFilter(self._shortcut_guard)
    
    # Also install on focus proxy if it exists
    focus_proxy = self.web_view.focusProxy()
    if focus_proxy:
        focus_proxy.installEventFilter(self._shortcut_guard)
```

## Special Components

### FocusSink Widget

Used during command mode to capture subsequent input:

```python
# In focus_sink.py
class FocusSinkWidget(QWidget):
    """Invisible widget that captures keyboard input during command mode."""
    
    def enter_command_mode(self, original_focus_widget=None):
        self._in_command_mode = True
        self._original_focus_widget = original_focus_widget
        self.setVisible(True)
        self.setFocus()
        self.grabKeyboard()  # Ensure we get all keyboard events
```

## Why This Complex Architecture?

### Challenge 1: WebEngine/Terminal Consumption
- **Problem**: xterm.js naturally consumes all keyboard input
- **Solution**: JavaScript layer intercepts before xterm.js processes

### Challenge 2: Qt Shortcut System Requirements
- **Problem**: Qt needs ShortcutOverride event accepted to trigger QActions
- **Solution**: WebShortcutGuard handles both ShortcutOverride and KeyPress differently

### Challenge 3: Focus Independence
- **Problem**: Shortcuts must work regardless of which widget has focus
- **Solution**: ApplicationShortcut context on QActions

### Challenge 4: Command Pattern Integration
- **Problem**: Need decoupling between shortcuts and implementation
- **Solution**: Commands system with service layer

## Adding a New Global Shortcut

To add a new shortcut that works everywhere (including terminals), follow the same pattern as Alt+P. The process requires coordination across multiple layers:

### 1. Add to Reserved List
First, add your shortcut to the reserved list to prevent WebEngine from consuming it:

```python
# In core/keyboard/reserved_shortcuts.py
WEBENGINE_RESERVED_SHORTCUTS = [
    "Alt+P",           # Toggle pane numbers (existing)
    "Ctrl+B",          # Toggle sidebar (existing)
    # ... other existing shortcuts
    # Add your new shortcut here
]
```

### 2. Add JavaScript Handler (Required for Terminal Shortcuts)
If your shortcut needs to work when a terminal has focus, add interception in the JavaScript layer:

```javascript
// In ui/terminal/terminal_assets.py (embedded JavaScript)
// Look for the attachCustomKeyEventHandler section around line 258
// Add your handler similar to Alt+P:
if (e.altKey && !e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === "your_key") {
    console.log("Your shortcut detected in terminal");
    e.preventDefault();
    e.stopPropagation();
    return false;  // Prevent terminal from processing
}
```

### 3. Create QAction in MainWindow
For shortcuts requiring special WebEngine handling, add a QAction in `_create_application_shortcuts()`:

```python
# In ui/main_window.py, _create_application_shortcuts() method (line 443)
your_action = QAction("Your Action Name", self)
your_action.setShortcut(QKeySequence("Your+Shortcut"))
your_action.setShortcutContext(Qt.ApplicationShortcut)
your_action.triggered.connect(
    lambda: self.execute_command("workbench.action.yourCommand")
)
self.addAction(your_action)
your_action.setEnabled(True)  # Ensure it's enabled
```

### 4. Implement Command (Without Shortcut in Decorator)
**Critical:** When using QAction, do NOT define the shortcut in the command decorator:

```python
# In core/commands/builtin/workspace_commands.py or appropriate file
@command(
    id="workbench.action.yourCommand",
    title="Your Command Title",
    category="Workspace",
    # shortcut="your+shortcut",  # COMMENT OUT - handled by QAction
    description="What your command does"
)
def your_command(context: CommandContext) -> CommandResult:
    # Implementation
    pass
```

## Detailed Event Flow: Alt+Arrow Keys (Directional Navigation)

Alt+Arrow keys provide directional pane navigation. Unlike Alt+P which requires a QAction, these shortcuts work through the standard command system because they don't need special handling in command mode.

### Step 1: JavaScript Layer Prevention (Terminal Only)

When a terminal has focus, JavaScript intercepts Alt+Arrow to prevent xterm.js from consuming it:

```javascript
// In ui/terminal/terminal_assets.py (line 276-283)
// Intercept Alt+Arrow keys for directional pane navigation
if (e.altKey && !e.ctrlKey && !e.shiftKey) {
    const key = e.key.toLowerCase();
    if (key === "arrowleft" || key === "arrowright" || 
        key === "arrowup" || key === "arrowdown") {
        console.log("Alt+Arrow detected in terminal, bubbling to Qt");
        // Let Qt handle directional navigation
        return false;  // Don't let terminal consume Alt+Arrow
    }
}
```

**Note:** Unlike Alt+P, these keys simply return `false` without preventDefault() or stopPropagation(), allowing Qt to handle them naturally.

### Step 2: Reserved Shortcuts List

Alt+Arrow keys are in the reserved list to ensure WebShortcutGuard intercepts them:

```python
# In core/keyboard/reserved_shortcuts.py (lines 21-24)
WEBENGINE_RESERVED_SHORTCUTS = [
    "Alt+P",           # Toggle pane numbers
    # ... other shortcuts ...
    "Alt+Left",        # Navigate to pane on the left
    "Alt+Right",       # Navigate to pane on the right
    "Alt+Up",          # Navigate to pane above
    "Alt+Down",        # Navigate to pane below
]
```

### Step 3: Command Registration with Shortcuts

Unlike Alt+P, Alt+Arrow commands include shortcuts in their decorators:

```python
# In core/commands/builtin/navigation_commands.py (lines 154-241)

@command(
    id="workbench.action.focusLeftPane",
    title="Focus Left Pane",
    category="Navigation",
    description="Focus the pane to the left",
    shortcut="alt+left",  # Shortcut IS defined here
    when="workbench.pane.count > 1"
)
def focus_left_pane_command(context: CommandContext) -> CommandResult:
    """Focus the pane to the left."""
    workspace_service = context.get_service(WorkspaceService)
    success = workspace_service.navigate_in_direction("left")
    # ... return result

# Similar commands for alt+right, alt+up, alt+down
```

**Critical Difference:** These commands define shortcuts in decorators because they don't need QAction handling.

### Step 4: WorkspaceService Navigation

The commands call `navigate_in_direction()` in the service layer:

```python
# In services/workspace_service.py (line 513)
def navigate_in_direction(self, direction: str) -> bool:
    """
    Navigate to a pane in the specified direction.
    
    Uses tree structure and position overlap to find the most intuitive target.
    """
    widget = self._workspace.get_current_split_widget()
    if not widget or not widget.active_pane_id:
        logger.warning("No active pane to navigate from")
        return False
    
    # Delegate to the split widget's navigation logic
    # ... implementation details
```

### Event Flow Summary

1. **User presses Alt+Left in terminal**
2. **JavaScript layer** (terminal_assets.py):
   - Detects Alt+Arrow combination
   - Returns `false` to prevent terminal consumption
   - Key event bubbles up to Qt
3. **WebShortcutGuard** (event filter):
   - Sees Alt+Left in reserved list
   - For ShortcutOverride: Accepts event, returns False
   - For KeyPress: Returns True to block widget
4. **Qt Command System**:
   - Matches shortcut to registered command
   - Executes `focus_left_pane_command`
5. **Command Execution**:
   - Gets WorkspaceService
   - Calls `navigate_in_direction("left")`
6. **WorkspaceService**:
   - Finds pane to the left using tree structure
   - Focuses target pane
   - Returns success status

### Key Differences from Alt+P

| Aspect | Alt+P | Alt+Arrow |
|--------|-------|-----------|
| **QAction Required** | Yes - in `_create_application_shortcuts()` | No - standard command registration |
| **Shortcut in Decorator** | No - commented out | Yes - defined normally |
| **JavaScript Handling** | Calls Qt bridge, preventDefault() | Simple return false |
| **Purpose** | Enters command mode | Direct navigation |
| **Focus Handling** | Transfers to FocusSink | Stays with target pane |

## Detailed Event Flow: Ctrl+B (Toggle Sidebar)

Ctrl+B is a fundamental UI shortcut that toggles the sidebar visibility. Like Alt+Arrow keys, it uses standard command registration rather than QAction, demonstrating how most application shortcuts work.

### Step 1: JavaScript Layer Prevention (Terminal Only)

When a terminal has focus, JavaScript prevents xterm.js from consuming Ctrl+B:

```javascript
// In ui/terminal/terminal_assets.py (lines 287-302)
// Let Qt handle these global shortcuts - return false to prevent terminal from consuming them
if (e.ctrlKey && !e.shiftKey && !e.altKey) {
    const key = e.key.toLowerCase();
    // Global app shortcuts that should bubble up to Qt
    if (key === "b" ||     // Toggle sidebar
        key === "\\" ||    // Split horizontal
        key === "t" ||     // Toggle theme
        // ... other shortcuts
        ) {
        return false;  // Don't let terminal consume these
    }
}
```

**Note:** Ctrl+B is checked alongside other global Ctrl shortcuts, simply returning `false` to allow Qt handling.

### Step 2: Reserved Shortcuts List

Ctrl+B is in the reserved list to ensure WebShortcutGuard intercepts it:

```python
# In core/keyboard/reserved_shortcuts.py (line 15)
WEBENGINE_RESERVED_SHORTCUTS = [
    "Alt+P",           # Toggle pane numbers
    "Ctrl+B",          # Toggle sidebar
    "Ctrl+T",          # Toggle theme
    # ... other shortcuts
]
```

### Step 3: Command Registration with Shortcut

The toggle sidebar command defines its shortcut in the decorator:

```python
# In core/commands/builtin/view_commands.py (lines 40-63)

@command(
    id="view.toggleSidebar",
    title="Toggle Sidebar",
    category="View",
    description="Show or hide the sidebar",
    shortcut="ctrl+b",  # Shortcut IS defined here
    icon="sidebar"
)
def toggle_sidebar_command(context: CommandContext) -> CommandResult:
    """Toggle sidebar visibility using UIService."""
    ui_service = context.get_service(UIService)
    if not ui_service:
        return CommandResult(success=False, error="UIService not available")
    
    visible = ui_service.toggle_sidebar()
    
    return CommandResult(
        success=True,
        value={'visible': visible}
    )
```

### Step 4: UIService Layer

The command delegates to UIService for business logic:

```python
# In services/ui_service.py (lines 138-153)
def toggle_sidebar(self) -> bool:
    """
    Toggle sidebar visibility.
    
    Returns:
        New visibility state (True if visible)
    """
    self.validate_initialized()
    
    if not self._main_window:
        return False
    
    # Call main window's toggle method
    self._main_window.toggle_sidebar()
    self._sidebar_visible = not self._sidebar_visible
    
    return self._sidebar_visible
```

### Step 5: MainWindow UI Update

Finally, the main window handles the actual UI changes:

```python
# In ui/main_window.py (lines 565-580)
def toggle_sidebar(self):
    """Toggle sidebar visibility - now routes through command system for consistency."""
    # Still handle the UI updates directly for now to maintain compatibility
    self.sidebar.toggle()
    
    # Update splitter sizes when sidebar toggles
    if self.sidebar.is_collapsed:
        # Sidebar is now collapsed
        self.main_splitter.setSizes([0, self.main_splitter.width()])
        # Update activity bar to show current view as unchecked
        self.activity_bar.set_sidebar_visible(False)
    else:
        # Sidebar is now expanded
        self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
        # Update activity bar to show current view as checked
        self.activity_bar.set_sidebar_visible(True)
```

### Event Flow Summary

1. **User presses Ctrl+B in terminal**
2. **JavaScript layer** (terminal_assets.py):
   - Detects Ctrl+B in the list of global shortcuts
   - Returns `false` to prevent terminal consumption
   - Key event bubbles up to Qt
3. **WebShortcutGuard** (event filter):
   - Sees Ctrl+B in reserved list
   - For ShortcutOverride: Accepts event, returns False
   - For KeyPress: Returns True to block widget
4. **Qt Command System**:
   - Matches "ctrl+b" to registered command
   - Executes `toggle_sidebar_command`
5. **Command Execution**:
   - Gets UIService
   - Calls `toggle_sidebar()`
6. **UIService**:
   - Validates state
   - Calls `_main_window.toggle_sidebar()`
   - Updates internal visibility state
7. **MainWindow**:
   - Calls `sidebar.toggle()` for animation
   - Updates QSplitter sizes (0 for collapsed, 250px for expanded)
   - Updates activity bar visual state

### Architecture Insights

Ctrl+B demonstrates the standard shortcut flow that most commands follow:

1. **No QAction needed** - Standard command registration suffices
2. **Service layer pattern** - Command → Service → UI separation
3. **State management** - UIService tracks visibility state
4. **UI/Logic separation** - Business logic in service, UI updates in MainWindow

### Comparison with Other Shortcuts

| Aspect | Alt+P | Alt+Arrow | Ctrl+B |
|--------|-------|-----------|---------|
| **QAction Required** | Yes | No | No |
| **Shortcut in Decorator** | No | Yes | Yes |
| **Service Layer Used** | WorkspaceService | WorkspaceService | UIService |
| **UI Component** | FocusSink | Pane widgets | Sidebar widget |
| **State Change** | Command mode | Focus change | Visibility toggle |
| **Animation** | No | No | Yes (sidebar slide) |

## The FocusSink Pattern: A Focus Management Trick

The FocusSink is an architectural pattern that solves a fundamental problem in our multi-pane interface: how to capture keyboard input for command mode without disrupting the normal focus chain, especially when dealing with WebEngine terminals that aggressively consume keyboard events.

### The Problem

When Alt+P is pressed to enter pane navigation mode, we need to:
1. Show pane numbers as overlays
2. Wait for the user to press a digit (1-9) to select a pane
3. Navigate to that pane
4. OR cancel if Escape is pressed

The challenge is that after Alt+P, the currently focused widget (often a WebEngine terminal) would normally receive the subsequent keypress. WebEngine is particularly problematic because:
- It consumes most keyboard events before Qt can process them
- Event filters don't reliably intercept all keys once WebEngine has focus
- We can't modify the focus behavior of third-party widgets

### The Solution: An Invisible Focus Thief

The FocusSink is a 0x0 pixel invisible widget that temporarily "steals" focus and keyboard input during command mode. Here's how it works:

#### 1. Widget Setup (`ui/widgets/focus_sink.py`)

```python
class FocusSinkWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Make the widget invisible and minimal
        self.setFixedSize(0, 0)        # Zero size - completely invisible
        self.setVisible(False)          # Hidden by default
        
        # Strong focus policy to ensure it gets keyboard events
        self.setFocusPolicy(Qt.StrongFocus)
```

**Key Points:**
- **Zero Size**: The widget is 0x0 pixels, making it completely invisible to the user
- **Hidden by Default**: Only shown during command mode
- **Strong Focus Policy**: Ensures it can receive keyboard focus

#### 2. Entering Command Mode

When Alt+P triggers pane navigation mode:

```python
def enter_command_mode(self, original_focus_widget=None):
    self._in_command_mode = True
    self._original_focus_widget = original_focus_widget  # Remember who had focus
    
    # Make visible (though still 0x0 size) and grab focus
    self.setVisible(True)
    self.setFocus()
    self.grabKeyboard()  # Critical: Ensure we get ALL keyboard events
```

**The "Trick" Explained:**
1. **setVisible(True)**: Widget must be visible to receive focus (even at 0x0 size)
2. **setFocus()**: Takes focus away from current widget (e.g., terminal)
3. **grabKeyboard()**: The nuclear option - ensures ALL keyboard events come to us

The `grabKeyboard()` call is the key trick. It makes our invisible widget the exclusive recipient of keyboard events, bypassing normal event propagation entirely. This guarantees that WebEngine or any other widget cannot consume the digit keys.

#### 3. Processing Command Input

Once FocusSink has focus and keyboard grab:

```python
def keyPressEvent(self, event: QKeyEvent):
    if not self._in_command_mode:
        return
    
    key = event.key()
    
    # Handle digit keys (1-9)
    if Qt.Key_1 <= key <= Qt.Key_9:
        digit = key - Qt.Key_0
        self.digitPressed.emit(digit)
        self.exit_command_mode(restore_focus=False)  # Don't restore - pane will handle
        event.accept()
        
    # Handle Escape - cancel command mode
    elif key == Qt.Key_Escape:
        self.cancelled.emit()
        self.exit_command_mode(restore_focus=True)   # Restore to original widget
        event.accept()
        
    # Any other key exits command mode
    else:
        self.exit_command_mode(restore_focus=True)
        event.ignore()  # Let the key propagate
```

**Smart Focus Restoration:**
- **On digit press**: Don't restore focus - let the newly selected pane take focus
- **On Escape**: Restore focus to the original widget
- **On other keys**: Exit mode and restore focus

#### 4. Exiting Command Mode

```python
def exit_command_mode(self, restore_focus=True):
    self._in_command_mode = False
    
    # Release keyboard and hide
    self.releaseKeyboard()    # Critical: Release the exclusive grab
    self.setVisible(False)     # Hide again
    
    # Restore focus if requested
    if restore_focus and self._original_focus_widget:
        self._original_focus_widget.setFocus()
```

### Integration with WorkspaceService

The FocusSink is managed by the WorkspaceService (`services/workspace_service.py`):

```python
def enter_pane_command_mode(self) -> bool:
    """Enter command mode for pane navigation."""
    if not self._panes:
        return False
    
    # Store original focus widget
    original_focus = QApplication.focusWidget()
    
    # Show pane numbers
    self._show_pane_numbers()
    
    # Activate focus sink to capture input
    self._focus_sink.enter_command_mode(original_focus)
    
    return True
```

The FocusSink signals are connected to handle the actual navigation:

```python
# In WorkspaceService.__init__
self._focus_sink.digitPressed.connect(self._on_digit_pressed)
self._focus_sink.cancelled.connect(self._exit_command_mode)
self._focus_sink.commandModeExited.connect(self._exit_command_mode)
```

### Why This Pattern Works

1. **Complete Control**: `grabKeyboard()` gives absolute control over keyboard input
2. **Invisible Operation**: User never sees the focus sink widget
3. **Clean Restoration**: Focus returns to the appropriate widget after command mode
4. **WebEngine-Proof**: Even aggressive key consumers like WebEngine can't intercept events
5. **Safe Fallback**: Any unexpected input exits command mode gracefully

### Alternative Approaches (and why they don't work)

1. **Event Filters on WebEngine**: WebEngine often processes keys before filters see them
2. **Modal Dialogs**: Too heavy-weight and visually disruptive for quick navigation
3. **Global Event Filter**: Would affect the entire application, not just command mode
4. **JavaScript Key Handlers**: Only work within WebEngine, not for Qt widgets

The FocusSink pattern elegantly solves these issues by temporarily becoming the sole keyboard event recipient, ensuring reliable command mode operation regardless of what widget previously had focus.

## Debugging Shortcuts

### Enable Logging
```python
# Set logging level in main.py or config
logging.getLogger("core.keyboard.web_shortcut_guard").setLevel(logging.DEBUG)
```

### Common Issues and Solutions

1. **Shortcut not working in terminal**
   - Check JavaScript handler is intercepting
   - Verify shortcut is in reserved list
   - Check WebShortcutGuard is installed on widget

2. **Duplicate shortcut registration**
   - Ensure shortcut is ONLY in QAction, not command decorator
   - Check for conflicting shortcuts in different components

3. **Shortcut works intermittently**
   - Verify event filter is installed on both widget and focus proxy
   - Check no other widget is grabbing keyboard

## Testing Checklist

When implementing a new shortcut:

- [ ] Works when terminal has focus
- [ ] Works when editor has focus  
- [ ] Works when sidebar has focus
- [ ] Works during command mode
- [ ] Doesn't interfere with terminal input
- [ ] Logs show proper interception flow
- [ ] No duplicate registration warnings

## Performance Considerations

- Event filters are called frequently - keep logic minimal
- JavaScript handlers should return quickly
- Use logging judiciously in production

## References

- Qt Event System: https://doc.qt.io/qt-6/eventsandfilters.html
- xterm.js API: https://xtermjs.org/docs/api/terminal/
- PySide6 QAction: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QAction.html