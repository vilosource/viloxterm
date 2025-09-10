# Keyboard Shortcuts & Command Palette Design

## Vision

Transform ViloApp into a keyboard-first application that empowers users to navigate and control the entire interface without touching the mouse, while maintaining discoverability through a VSCode-style command palette.

## Design Principles

1. **Keyboard-First**: Every action accessible via keyboard
2. **Discoverable**: Command palette shows all available commands
3. **Customizable**: Users can remap any shortcut
4. **Contextual**: Different shortcuts in different contexts
5. **Consistent**: Follow established patterns (VSCode/browser)
6. **Accessible**: Support screen readers and accessibility tools

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     KeyboardService                          │
│                      (Singleton)                             │
├─────────────────────────┬────────────────────────────────────┤
│   ShortcutRegistry      │      CommandRegistry               │
│   - Global shortcuts    │      - Command definitions         │
│   - Context shortcuts   │      - Command metadata            │
│   - User overrides      │      - Command handlers            │
├─────────────────────────┼────────────────────────────────────┤
│                    ContextManager                            │
│   - Active contexts (editorFocus, terminalFocus, etc.)      │
│   - When clause evaluation                                   │
│   - Context inheritance                                      │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      CommandPalette                          │
├─────────────────────────┬────────────────────────────────────┤
│   Search & Filter       │      UI Components                 │
│   - Fuzzy matching      │      - Search input                │
│   - Category filter     │      - Results list                │
│   - Recent commands     │      - Preview pane                │
└─────────────────────────┴────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       FocusManager                           │
├─────────────────────────┬────────────────────────────────────┤
│   Navigation Control    │      Focus Indicators              │
│   - Focus groups        │      - Visual highlight            │
│   - Tab order           │      - Audio feedback              │
│   - Focus stack         │      - Status bar info             │
└─────────────────────────┴────────────────────────────────────┘
```

## Command System

### Command Structure

```python
@dataclass
class Command:
    """Represents an executable command"""
    id: str                          # "workbench.action.toggleSidebar"
    title: str                       # "Toggle Sidebar"
    category: str                    # "View"
    description: Optional[str]       # Detailed description
    icon: Optional[str]              # Icon identifier
    shortcut: Optional[str]          # Default keybinding
    when: Optional[str]              # Context expression
    group: Optional[str]             # Menu group
    
    # Execution
    handler: Callable[..., Any]      # Function to execute
    args: Optional[Dict[str, Any]]   # Default arguments
    
    # Metadata
    visible: bool = True             # Show in palette
    enabled: bool = True             # Can be executed
    checked: bool = False            # For toggle commands
```

### Command Categories

1. **File** - File operations
2. **Edit** - Text editing
3. **View** - UI visibility and layout
4. **Navigation** - Moving between elements
5. **Terminal** - Terminal operations
6. **Debug** - Debugging commands
7. **Window** - Window management
8. **Help** - Documentation and help

### Command Registry

```python
class CommandRegistry:
    def register(self, command: Command) -> None
    def unregister(self, command_id: str) -> None
    def get_command(self, command_id: str) -> Optional[Command]
    def get_all_commands(self) -> List[Command]
    def get_commands_for_category(self, category: str) -> List[Command]
    def execute_command(self, command_id: str, **kwargs) -> Any
```

## Keyboard Shortcut System

### Shortcut Definition

```python
@dataclass
class Shortcut:
    """Represents a keyboard shortcut"""
    key: str                    # "ctrl+shift+p"
    command: str                # Command ID
    when: Optional[str]         # Context expression
    args: Optional[Dict]        # Command arguments
    priority: int = 0           # For conflict resolution
```

### Context System

#### Context Keys

```python
# Focus contexts
"editorFocus"           # Editor has focus
"terminalFocus"         # Terminal has focus
"sidebarFocus"          # Sidebar has focus
"searchFocus"           # Search input has focus

# Visibility contexts
"sidebarVisible"        # Sidebar is visible
"terminalVisible"       # Terminal is visible
"menuBarVisible"        # Menu bar is visible

# State contexts
"hasOpenEditors"        # At least one editor open
"hasMultipleTabs"       # Multiple tabs open
"canSplit"             # Can split current pane
"isFullScreen"         # Window is fullscreen

# Mode contexts
"vimMode"              # Vim mode active
"vimInsertMode"        # Vim insert mode
"normalMode"           # Normal mode

# File contexts
"resourceExtension"    # File extension (.py, .js, etc.)
"resourceScheme"       # File scheme (file, untitled)
```

#### When Clause Expressions

```javascript
// Simple
"editorFocus"

// Negation
"!terminalFocus"

// AND
"editorFocus && !searchFocus"

// OR
"sidebarFocus || activityBarFocus"

// Complex
"editorFocus && hasMultipleTabs && !vimMode"
```

### Default Keyboard Shortcuts

#### Global Navigation
| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+Shift+P` | Show Command Palette | Open command palette |
| `Ctrl+P` | Quick Open | Quick file open |
| `Ctrl+,` | Open Settings | Open settings |
| `Ctrl+K Ctrl+S` | Open Keyboard Shortcuts | View/edit shortcuts |

#### Focus Navigation
| Shortcut | Command | Description |
|----------|---------|-------------|
| `F6` | Focus Next Part | Move focus to next major part |
| `Shift+F6` | Focus Previous Part | Move focus to previous part |
| `Ctrl+0` | Focus Sidebar | Focus on sidebar |
| `Ctrl+1` | Focus Editor | Focus on first editor |
| `Alt+F1` | Show Accessibility Help | Show navigation help |

#### Tab Management
| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+Tab` | Next Tab (MRU) | Switch to next tab (most recently used) |
| `Ctrl+Shift+Tab` | Previous Tab (MRU) | Switch to previous tab (MRU) |
| `Ctrl+PageDown` | Next Tab | Next tab in order |
| `Ctrl+PageUp` | Previous Tab | Previous tab in order |
| `Ctrl+W` | Close Tab | Close current tab |
| `Ctrl+K W` | Close All Tabs | Close all tabs |
| `Ctrl+Shift+T` | Reopen Closed Tab | Reopen recently closed |
| `Ctrl+1-9` | Go to Tab N | Jump to specific tab |

#### Split/Pane Management
| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+\` | Split Right | Split horizontally |
| `Ctrl+Shift+\` | Split Down | Split vertically |
| `Ctrl+K Arrow` | Focus Pane | Focus pane in direction |
| `Ctrl+K Ctrl+Arrow` | Move Pane | Move pane in direction |
| `Ctrl+K Shift+Arrow` | Resize Pane | Resize pane |
| `Ctrl+K Ctrl+Shift+Arrow` | Maximize Pane | Maximize in direction |

#### View Commands
| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+B` | Toggle Sidebar | Show/hide sidebar |
| `Ctrl+J` | Toggle Panel | Show/hide bottom panel |
| `Ctrl+` ` | Toggle Terminal | Show/hide terminal |
| `Ctrl+Shift+E` | Show Explorer | Focus file explorer |
| `Ctrl+Shift+F` | Show Search | Focus search |
| `Ctrl+Shift+G` | Show Git | Focus source control |
| `Ctrl+Shift+D` | Show Debug | Focus debug view |
| `F11` | Toggle Fullscreen | Enter/exit fullscreen |
| `Ctrl+K Z` | Zen Mode | Toggle zen mode |

#### Editor Commands
| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+N` | New File | Create new file |
| `Ctrl+O` | Open File | Open file dialog |
| `Ctrl+S` | Save | Save current file |
| `Ctrl+Shift+S` | Save As | Save with new name |
| `Ctrl+K S` | Save All | Save all files |
| `Ctrl+Z` | Undo | Undo last action |
| `Ctrl+Y` | Redo | Redo last action |
| `Ctrl+X` | Cut | Cut selection |
| `Ctrl+C` | Copy | Copy selection |
| `Ctrl+V` | Paste | Paste clipboard |
| `Ctrl+A` | Select All | Select all content |

#### Terminal Commands
| Shortcut | Command | Description |
|----------|---------|-------------|
| `Ctrl+Shift+` ` | New Terminal | Create new terminal |
| `Ctrl+Shift+C` | Copy (Terminal) | Copy in terminal |
| `Ctrl+Shift+V` | Paste (Terminal) | Paste in terminal |
| `Ctrl+PageDown` | Next Terminal | Switch to next terminal |
| `Ctrl+PageUp` | Previous Terminal | Switch to previous |
| `Ctrl+Shift+X` | Kill Terminal | Close current terminal |

## Command Palette

### Features

1. **Fuzzy Search**
   - Match anywhere in command name
   - Highlight matched characters
   - Score by relevance

2. **Categories**
   - Group commands by category
   - Filter by category
   - Show category in results

3. **Recent Commands**
   - Track frequently used commands
   - Show recent at top
   - Persistent across sessions

4. **Quick Actions**
   - `>` - Commands
   - `@` - Go to symbol
   - `:` - Go to line
   - `?` - Help

5. **Rich Display**
   - Command name
   - Keyboard shortcut
   - Description/preview
   - Category badge

### UI Design

```
┌─────────────────────────────────────────────┐
│ > Search commands...                    ESC │
├─────────────────────────────────────────────┤
│ RECENT                                      │
│ ⌘ Toggle Sidebar            Ctrl+B    View │
│ ⌘ New Terminal              Ctrl+`    Term │
├─────────────────────────────────────────────┤
│ ALL COMMANDS                                │
│ ⌘ Show All Commands         Ctrl+Shift+P   │
│ ⌘ Open File                 Ctrl+O    File │
│ ⌘ Save                      Ctrl+S    File │
│ ⌘ Toggle Terminal           Ctrl+`    View │
└─────────────────────────────────────────────┘
```

## Focus Management

### Focus Groups

```python
class FocusGroup(Enum):
    ACTIVITY_BAR = "activityBar"
    SIDEBAR = "sidebar"
    EDITOR = "editor"
    PANEL = "panel"
    STATUSBAR = "statusBar"
    MENU = "menu"
    DIALOG = "dialog"
```

### Focus Navigation

1. **Within Group**
   - Tab/Shift+Tab - Next/previous element
   - Arrow keys - Directional navigation

2. **Between Groups**
   - F6/Shift+F6 - Next/previous group
   - Ctrl+K F - Focus group by name
   - Alt+F1 - Focus menu

3. **Focus Stack**
   - Push focus for modals
   - Pop to restore previous
   - Escape to cancel and restore

### Focus Indicators

1. **Visual**
   - Border highlight
   - Background color
   - Outline style

2. **Audio** (Accessibility)
   - Focus change sound
   - Group change sound

3. **Status Bar**
   - Show current focus
   - Show available shortcuts

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

1. **Command System**
   ```python
   core/
   ├── commands/
   │   ├── __init__.py
   │   ├── command.py          # Command class
   │   ├── registry.py         # Command registry
   │   └── executor.py         # Command execution
   ```

2. **Keyboard Service**
   ```python
   core/
   ├── keyboard/
   │   ├── __init__.py
   │   ├── service.py          # Main service
   │   ├── shortcuts.py        # Shortcut management
   │   └── conflicts.py        # Conflict resolution
   ```

3. **Context System**
   ```python
   core/
   ├── context/
   │   ├── __init__.py
   │   ├── manager.py          # Context manager
   │   ├── evaluator.py        # When clause eval
   │   └── keys.py             # Context key definitions
   ```

### Phase 2: Command Palette (Week 2)

1. **UI Components**
   ```python
   ui/command_palette/
   ├── __init__.py
   ├── palette.py              # Main palette widget
   ├── search.py               # Search/filter logic
   ├── results.py              # Results display
   └── styles.py               # Styling
   ```

2. **Command Providers**
   ```python
   ui/command_palette/providers/
   ├── file_provider.py        # File commands
   ├── edit_provider.py        # Edit commands
   ├── view_provider.py        # View commands
   └── help_provider.py        # Help commands
   ```

### Phase 3: Focus Management (Week 3)

1. **Focus System**
   ```python
   core/focus/
   ├── __init__.py
   ├── manager.py              # Focus manager
   ├── groups.py               # Focus groups
   ├── navigation.py           # Navigation logic
   └── indicators.py           # Visual indicators
   ```

2. **Integration**
   - Update all widgets for focus support
   - Add keyboard navigation
   - Implement focus indicators

### Phase 4: Advanced Features (Week 4)

1. **Vim Mode**
   ```python
   extensions/vim/
   ├── __init__.py
   ├── mode.py                 # Mode management
   ├── commands.py             # Vim commands
   ├── motions.py              # Movement commands
   └── registers.py            # Register system
   ```

2. **Customization**
   - Settings UI for shortcuts
   - Import/export keymaps
   - Keymap schemes (VSCode, Sublime, Vim)

## Configuration

### User Settings

```json
{
  "keyboard.dispatch": "keyCode",
  "keyboard.layout": "us",
  "keyboard.shortcuts": [
    {
      "key": "ctrl+k ctrl+c",
      "command": "editor.action.commentLine",
      "when": "editorFocus"
    }
  ],
  "commandPalette.preserveInput": true,
  "commandPalette.showRecentCommands": true,
  "commandPalette.maxResults": 50,
  "focus.autoReveal": true,
  "focus.indicators": true,
  "vim.enable": false,
  "vim.startInInsertMode": false
}
```

### Keymap Schemes

```json
{
  "name": "VSCode",
  "parent": "default",
  "keybindings": [
    {
      "key": "ctrl+shift+p",
      "command": "workbench.action.showCommands"
    }
  ]
}
```

## Testing Strategy

### Unit Tests

1. **Command Tests**
   - Command registration
   - Command execution
   - Context evaluation

2. **Shortcut Tests**
   - Shortcut parsing
   - Conflict detection
   - Priority resolution

### Integration Tests

1. **End-to-End Flows**
   - Command palette interaction
   - Focus navigation
   - Keyboard shortcuts

2. **Performance Tests**
   - Command search speed
   - Large shortcut sets
   - Context evaluation

## Accessibility

### Screen Reader Support

1. **ARIA Labels**
   - All interactive elements
   - Focus announcements
   - Command descriptions

2. **Keyboard Navigation**
   - Full keyboard access
   - No keyboard traps
   - Escape to cancel

### High Contrast

1. **Focus Indicators**
   - High contrast borders
   - Sufficient color contrast
   - Non-color indicators

## Performance Considerations

### Optimizations

1. **Lazy Loading**
   - Load commands on demand
   - Defer palette creation
   - Virtual scrolling for results

2. **Caching**
   - Cache command search results
   - Cache context evaluations
   - Cache recent commands

3. **Debouncing**
   - Debounce search input
   - Throttle context updates
   - Batch command registration

## Migration Guide

### For Developers

1. **Converting Actions to Commands**
   ```python
   # Before
   action = QAction("Save", self)
   action.setShortcut("Ctrl+S")
   action.triggered.connect(self.save_file)
   
   # After
   registry.register(Command(
       id="file.save",
       title="Save",
       shortcut="ctrl+s",
       handler=self.save_file
   ))
   ```

2. **Adding Context**
   ```python
   # Set context
   context_manager.set("editorFocus", True)
   
   # Use in command
   Command(
       id="editor.copy",
       when="editorFocus && hasSelection"
   )
   ```

### For Users

1. **Learning Shortcuts**
   - Use command palette to discover
   - View keyboard shortcuts list
   - Customize to preference

2. **Migration from Other Editors**
   - Import VSCode keybindings
   - Use familiar keymap schemes
   - Gradual learning with palette

## Future Enhancements

### Version 2.0

1. **Macro Recording**
   - Record key sequences
   - Playback macros
   - Save/load macros

2. **Multi-cursor**
   - Multiple cursors
   - Column selection
   - Block editing

3. **Smart Keys**
   - Context-aware suggestions
   - Key chord completion
   - Learning from usage

### Version 3.0

1. **Voice Commands**
   - Voice input support
   - Command dictation
   - Accessibility enhancement

2. **Touch Gestures**
   - Touch bar support
   - Gesture shortcuts
   - Mobile compatibility

3. **AI Assistance**
   - Command suggestions
   - Shortcut optimization
   - Usage analytics

## Conclusion

This design provides a comprehensive foundation for transforming ViloApp into a keyboard-first application. The modular architecture ensures maintainability, the command system enables extensibility, and the focus on discoverability ensures usability for both beginners and power users.

The phased implementation approach allows for incremental development while maintaining system stability. Each phase delivers value independently while building toward the complete vision of a fully keyboard-navigable application with powerful command palette capabilities.