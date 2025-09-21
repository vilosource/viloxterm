# ViloxTerm Application

The main ViloxTerm application - a VSCode-style desktop GUI application with plugin architecture.

## Overview

ViloxTerm is a powerful desktop application that provides:
- **VSCode-style Interface**: Activity bar, sidebar, workspace, and status bar
- **Plugin Architecture**: Extensible through plugins using the ViloxTerm SDK
- **Split Pane System**: Recursive splitting and tabbed interface
- **Command System**: Command palette and keyboard shortcuts
- **Cross-platform**: Runs on Windows, macOS, and Linux

## Installation

### From PyPI

```bash
pip install viloapp
```

### From Source

```bash
git clone https://github.com/viloapp/viloapp.git
cd viloapp/packages/viloapp
pip install -e .
```

## Quick Start

Launch ViloxTerm:

```bash
viloapp
```

Or run from Python:

```python
from viloapp.main import main
main()
```

## Features

- **Activity Bar**: Quick access to different tools (Explorer, Search, Git, Settings)
- **Sidebar**: Collapsible panel with multiple tool views
- **Workspace**: Tabbed interface with split pane support
- **Command Palette**: Access all commands with `Ctrl+Shift+P`
- **Chrome Mode**: Tabs in title bar mode with `Ctrl+Shift+C`
- **Theme Support**: Light and dark themes
- **State Persistence**: Remembers layout and settings

## Development

### Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint
ruff check src/
```

### Architecture

ViloxTerm uses a command-based architecture:
- **Commands**: All actions go through the command system
- **Services**: Business logic layer
- **UI Components**: PySide6-based interface
- **Plugin System**: Extensible through SDK

## Documentation

Full documentation available at: https://viloxterm.readthedocs.io

## License

MIT