# ViloxTerm - Advanced Terminal Plugin

A professional terminal emulator plugin for ViloxTerm with advanced features including profiles, session management, search functionality, and seamless integration.

## Features

### Core Terminal Features
- **xterm.js Integration**: Full xterm compatibility with modern terminal features
- **Cross-Platform**: Supports Windows (PowerShell, CMD, WSL), macOS, and Linux shells
- **Multiple Sessions**: Create and manage multiple terminal sessions
- **Tab Management**: Professional tab interface with close buttons and session info

### Advanced Features (Week 4)
- **Terminal Profiles**: Pre-configured shell profiles with custom settings
- **Session Management**: Named sessions with persistence and restoration
- **Search Functionality**: Full-text search in terminal output with navigation
- **Settings Integration**: Theme synchronization and customizable preferences
- **UI Enhancements**: Professional toolbar with profile selector and search

### Supported Shells
- **Windows**: PowerShell, Command Prompt, WSL
- **macOS/Linux**: Bash, Zsh, Fish, sh
- **Custom**: Add your own shell profiles

### Terminal Profiles
```python
# Default profiles are automatically detected
profiles = {
    "bash": TerminalProfile("Bash", "/bin/bash"),
    "zsh": TerminalProfile("Zsh", "/bin/zsh"),
    "powershell": TerminalProfile("PowerShell", "powershell.exe"),
}

# Add custom profiles
manager.add_profile("custom", TerminalProfile(
    name="Custom Shell",
    shell="/path/to/shell",
    args=["-l", "--interactive"],
    env={"CUSTOM_VAR": "value"},
    cwd="/custom/directory"
))
```

## Installation

The ViloxTerm plugin is part of the ViloxTerm plugin system:

```bash
cd packages/viloxterm
pip install -e .
```

## Commands

### Basic Commands
- `terminal.new` - Create new terminal (Ctrl+Shift+`)
- `terminal.clear` - Clear terminal (Ctrl+Shift+K)
- `terminal.close` - Close current terminal
- `terminal.focus` - Focus terminal

### Advanced Commands (Week 4)
- `terminal.newWithProfile` - Create terminal with specific profile
- `terminal.search` - Search in terminal output
- `terminal.renameSession` - Rename terminal session
- `terminal.listSessions` - List all terminal sessions

## Architecture

```
viloxterm/
├── src/viloxterm/
│   ├── plugin.py          # Main plugin class
│   ├── widget.py          # Terminal widget and factory
│   ├── server.py          # Terminal server backend
│   ├── features.py        # Advanced features (Week 4)
│   ├── ui_components.py   # UI enhancements (Week 4)
│   ├── settings.py        # Settings management (Week 4)
│   └── backends/          # Platform-specific backends
├── tests/                 # Test suite
└── assets/                # Terminal themes and assets
```

### Key Components

#### TerminalPlugin
Main plugin class handling lifecycle, commands, and integration.

#### TerminalWidget
Core terminal widget with:
- QWebEngineView for xterm.js
- Terminal server integration
- Session management
- Professional UI toolbar

#### TerminalServer
Backend server managing:
- PTY processes
- Session lifecycle
- Cross-platform shell execution

#### Advanced Features (Week 4)

**TerminalProfileManager**
- Platform-specific shell detection
- Custom profile management
- Default profile selection

**TerminalSessionManager**
- Session creation with profiles
- Session naming and tracking
- Session persistence

**TerminalSearch**
- xterm.js search addon integration
- Pattern search with case sensitivity
- Search history tracking

**TerminalSettingsManager**
- Theme synchronization
- Font and display settings
- Performance optimization

## Usage

### Basic Terminal Operations
```python
# Create new terminal
workspace.execute_command("terminal.new")

# Clear terminal
workspace.execute_command("terminal.clear")

# Close terminal
workspace.execute_command("terminal.close")
```

### Advanced Operations
```python
# Create terminal with specific profile
workspace.execute_command("terminal.newWithProfile", {
    "profile": "PowerShell"
})

# Search in terminal
workspace.execute_command("terminal.search", {
    "pattern": "error",
    "case_sensitive": True
})

# Rename session
workspace.execute_command("terminal.renameSession", {
    "session_id": "session_123",
    "name": "Development Shell"
})
```

### Profile Management
```python
from viloxterm.features import TerminalProfileManager, TerminalProfile

manager = TerminalProfileManager()

# List available profiles
profiles = manager.list_profiles()

# Add custom profile
custom_profile = TerminalProfile(
    name="Development Shell",
    shell="/bin/zsh",
    args=["-l"],
    env={"NODE_ENV": "development"},
    cwd="/workspace/project"
)
manager.add_profile("dev", custom_profile)
```

## Settings

Terminal settings are fully configurable:

```json
{
    "terminal.shell.linux": "/bin/bash",
    "terminal.shell.windows": "powershell.exe",
    "terminal.fontSize": 14,
    "terminal.fontFamily": "monospace",
    "terminal.cursorStyle": "block",
    "terminal.cursorBlink": true,
    "terminal.scrollback": 1000,
    "terminal.useThemeColors": true
}
```

## Integration

### With Editor Plugin
- Open files from terminal in editor
- Run code from editor in terminal
- Shared workspace and theming

### With Workspace
- Multiple terminal tabs
- Split pane support
- Session persistence

## Development

### Requirements
- Python >= 3.8
- PySide6 >= 6.5.0
- viloapp-sdk >= 1.0.0

### Testing
```bash
pytest tests/ -v
```

### Platform Support
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu, Fedora, Arch)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see LICENSE file for details.