# Terminal Widget Integration Plan

## Architecture Overview
We'll integrate a terminal widget into viloapp by adapting the viloxtermjs implementation with significant improvements:

**Key Architecture Changes:**
1. **Single Flask Server**: Instead of one Flask server per terminal, we'll use a single shared server managing multiple terminal sessions
2. **Session Management**: Each terminal gets a unique session ID, managed by the central server
3. **Theme Integration**: Terminal styling will adapt to the VSCode light/dark theme system
4. **Widget Registry**: Terminal will be registered as a proper widget type in the existing system

## Implementation Structure

### 1. Terminal Server Module (`ui/terminal/terminal_server.py`)
- **TerminalServerManager** (Singleton)
  - Manages single Flask/SocketIO server instance
  - Handles multiple PTY sessions with unique IDs
  - Port management (find available port once, reuse)
  - Session lifecycle (create, destroy, cleanup)
  
- **Features:**
  - WebSocket rooms for session isolation
  - Session timeout and cleanup
  - Resource management (limit max terminals)
  - Graceful shutdown handling

### 2. Terminal Widget (`ui/terminal/terminal_widget.py`)
- **TerminalWidget** extends QWidget
  - QWebEngineView for xterm.js rendering
  - Session ID management
  - Theme-aware styling
  - State serialization support
  
- **Improvements:**
  - Better resize handling with debouncing
  - Font size configuration
  - Copy/paste with system clipboard
  - Terminal title management
  - Command history (optional)

### 3. Terminal Configuration (`ui/terminal/terminal_config.py`)
- **TerminalConfig** class
  - Shell selection (bash, zsh, powershell)
  - Font family and size
  - Color schemes (VSCode dark/light compatible)
  - Scrollback buffer size
  - Cursor style and blinking
  
- **Integration with QSettings** for persistence

### 4. HTML/JavaScript Template Improvements
- **Theme System:**
  - CSS variables for easy theming
  - VSCode color palette integration
  - Smooth theme transitions
  
- **Performance:**
  - Optimized resize algorithm
  - Canvas rendering optimizations
  - Better scrollbar styling
  
- **Features:**
  - Search functionality (Ctrl+F)
  - Link detection and clicking
  - Better touch/mobile support

## Integration Points

### 1. Widget Registry Integration
```python
# Register terminal widget type
WidgetType.TERMINAL = "terminal"  
TerminalConfig in WIDGET_CONFIGS with:
- Custom factory using TerminalWidget
- Serializer for session state
- Deserializer for session restoration
- VSCode-compatible styling
```

### 2. Workspace Integration
- Add terminal creation in split panes
- Terminal tabs in tab containers
- Keyboard shortcuts (Ctrl+` for new terminal)
- Context menu options

### 3. Activity Bar Integration
- Terminal icon in activity bar
- Terminal panel in sidebar (optional)
- Quick terminal toggle

## Implementation Steps

### Phase 1: Core Terminal Infrastructure
1. **Copy and adapt server.py → terminal_server.py**
   - Extract core PTY handling logic
   - Implement session-based architecture
   - Add room-based WebSocket isolation
   
2. **Implement TerminalServerManager singleton**
   - Server lifecycle management
   - Port allocation and reuse
   - Session registry and cleanup
   
3. **Add session management layer**
   - Unique session ID generation
   - Session state tracking
   - Timeout and cleanup mechanisms
   
4. **Create terminal configuration system**
   - Shell preferences
   - Visual settings
   - Keybinding configuration

### Phase 2: Terminal Widget Implementation
1. **Copy and adapt widget.py → terminal_widget.py**
   - Remove per-widget server creation
   - Add session ID handling
   - Connect to shared server
   
2. **Integrate with widget registry**
   - Create factory function
   - Define widget configuration
   - Set up proper minimum sizes
   
3. **Add theme support**
   - Listen for theme change signals
   - Update terminal colors dynamically
   - Persist theme preference
   
4. **Implement state serialization**
   - Save session ID and state
   - Restore on application restart
   - Handle orphaned sessions

### Phase 3: HTML/JS Template Enhancement
1. **Extract template to separate file**
   - Create terminal_template.html
   - Use Jinja2 templating for configuration
   - Support dynamic theme injection
   
2. **Add VSCode theme variables**
   - Map VSCode colors to xterm.js theme
   - Support both light and dark themes
   - Smooth transition animations
   
3. **Improve resize handling**
   - Implement debounced resize
   - Calculate exact cell dimensions
   - Prevent white space gaps
   
4. **Add configuration support**
   - Font size adjustment
   - Cursor customization
   - Scrollback configuration

### Phase 4: Integration with Main App
1. **Register terminal widget type**
   - Add to WidgetType enum
   - Configure in WIDGET_CONFIGS
   - Set up factory function
   
2. **Add menu items and shortcuts**
   - New Terminal (Ctrl+`)
   - Split Terminal
   - Clear Terminal
   
3. **Update workspace to handle terminals**
   - Terminal-specific tab icons
   - Proper focus handling
   - Terminal count tracking
   
4. **Add terminal-specific context menus**
   - Copy/Paste options
   - Clear buffer
   - Restart terminal

### Phase 5: Testing and Polish
1. **Unit tests for server manager**
   - Session creation/destruction
   - Multiple terminal handling
   - Error recovery
   
2. **Widget integration tests**
   - Theme switching
   - State persistence
   - Resize behavior
   
3. **Performance optimization**
   - Profiling with multiple terminals
   - Memory leak detection
   - CPU usage optimization
   
4. **User experience polish**
   - Smooth animations
   - Keyboard navigation
   - Error messages

## Key Improvements Over Reference Implementation

### 1. Resource Efficiency
- **Single server vs. multiple servers**: One Flask server handles all terminals
- **Shared resources**: Flask and SocketIO instances are reused
- **Better memory management**: Centralized session cleanup
- **Connection pooling**: WebSocket connections are managed efficiently

### 2. User Experience
- **Seamless theme integration**: Terminals match app theme automatically
- **Better keyboard shortcuts**: VSCode-compatible keybindings
- **Improved copy/paste**: System clipboard integration
- **Terminal tabs and splits**: Full integration with workspace system

### 3. Maintainability
- **Centralized configuration**: Single source of truth for settings
- **Clear separation of concerns**: Server, widget, and UI are decoupled
- **Comprehensive error handling**: Graceful degradation and recovery
- **Extensive logging**: Debug and audit trail support

### 4. Extensibility
- **Plugin support**: Hook system for terminal commands
- **Custom shell integrations**: Support for different shells
- **Terminal sharing**: Foundation for collaborative features
- **Remote terminal support**: Architecture supports future SSH integration

## Dependencies to Add

```txt
# Terminal emulation
flask>=2.0.0
flask-socketio>=5.0.0
python-socketio>=5.0.0
python-engineio>=4.0.0
simple-websocket>=1.0.0

# Web rendering (may already be installed with PySide6)
PySide6-WebEngine>=6.7.0
```

## Configuration Schema

```python
TERMINAL_CONFIG = {
    "shell": {
        "default": "bash",
        "available": ["bash", "zsh", "sh", "powershell"],
        "custom_path": None
    },
    "appearance": {
        "font_family": "Consolas, 'Courier New', monospace",
        "font_size": 14,
        "line_height": 1.2,
        "cursor_style": "block",  # block, underline, bar
        "cursor_blink": True,
        "scrollback": 1000
    },
    "colors": {
        "theme": "auto",  # auto, dark, light, custom
        "dark": {
            "background": "#1e1e1e",
            "foreground": "#d4d4d4",
            "cursor": "#ffffff",
            "selection": "#264f78",
            # ... ANSI colors
        },
        "light": {
            "background": "#ffffff",
            "foreground": "#333333",
            "cursor": "#000000",
            "selection": "#add6ff",
            # ... ANSI colors
        }
    },
    "behavior": {
        "copy_on_select": False,
        "right_click_paste": True,
        "confirm_on_exit": True,
        "bell_style": "visual",  # none, visual, sound
        "max_terminals": 10
    }
}
```

## Success Criteria

1. **Functionality**
   - [ ] Multiple terminals can run simultaneously
   - [ ] Each terminal maintains independent session
   - [ ] Commands execute properly with correct output
   - [ ] Copy/paste works with system clipboard

2. **Performance**
   - [ ] App remains responsive with 5+ terminals
   - [ ] Terminal output renders smoothly
   - [ ] Resize operations are fluid
   - [ ] Memory usage stays reasonable

3. **Integration**
   - [ ] Terminals work in split panes
   - [ ] Theme changes apply immediately
   - [ ] State persists across restarts
   - [ ] Keyboard shortcuts work globally

4. **Reliability**
   - [ ] Clean shutdown without orphaned processes
   - [ ] Graceful handling of server errors
   - [ ] Recovery from disconnections
   - [ ] No memory leaks over time

## Risk Mitigation

1. **Server Management Complexity**
   - Risk: Single server becomes bottleneck
   - Mitigation: Implement connection pooling and async handling

2. **Process Cleanup**
   - Risk: Orphaned PTY processes
   - Mitigation: Register signal handlers and cleanup hooks

3. **Security Concerns**
   - Risk: XSS through terminal output
   - Mitigation: Proper output sanitization and CSP headers

4. **Performance Issues**
   - Risk: Multiple terminals slow down app
   - Mitigation: Lazy loading and virtual scrolling

## Timeline Estimate

- Phase 1 (Core Infrastructure): 2-3 days
- Phase 2 (Widget Implementation): 2 days
- Phase 3 (Template Enhancement): 1-2 days
- Phase 4 (Integration): 2 days
- Phase 5 (Testing & Polish): 2-3 days

**Total: 9-13 days**

## Future Enhancements

1. **Terminal Multiplexing**: tmux-like functionality
2. **SSH Integration**: Remote terminal support
3. **Terminal Sharing**: Collaborative editing
4. **Shell Integration**: Enhanced shell prompts
5. **Search History**: Full-text search across sessions
6. **Terminal Replay**: Record and playback sessions
7. **Custom Renderers**: Support for images and rich content
8. **Terminal Profiles**: Saved configurations per project