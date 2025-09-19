# ViloxTerm Terminal Plugin

Professional terminal emulator plugin for ViloxTerm application.

## Features

- Full xterm compatibility
- Multiple concurrent sessions
- Cross-platform support (Linux, macOS, Windows)
- Web-based terminal using xterm.js
- Customizable shell and appearance
- Session management
- Command palette integration

## Installation

```bash
pip install viloxterm
```

Or install from source:

```bash
cd packages/viloxterm
pip install -e .
```

## Usage

The terminal plugin is automatically loaded by ViloxTerm when installed.

### Commands

- `terminal.new` - Create a new terminal
- `terminal.clear` - Clear the terminal screen
- `terminal.close` - Close the current terminal
- `terminal.split` - Split the terminal pane
- `terminal.focus` - Focus on the terminal

### Keyboard Shortcuts

- `Ctrl+Shift+`` ` - New terminal
- `Ctrl+Shift+K` - Clear terminal
- `Ctrl+Shift+W` - Close terminal

## Configuration

Configure the terminal through ViloxTerm settings:

```json
{
  "terminal.shell.linux": "/bin/bash",
  "terminal.shell.windows": "powershell.exe",
  "terminal.fontSize": 14,
  "terminal.fontFamily": "monospace",
  "terminal.cursorStyle": "block",
  "terminal.scrollback": 1000
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Building

```bash
python -m build
```

## License

MIT