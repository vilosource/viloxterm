# ViloApp

A VSCode-style desktop application built with PySide6, featuring a collapsible sidebar, activity bar, and split-pane workspace.

## Features

- **Activity Bar**: Vertical toolbar with icon buttons for different views
- **Collapsible Sidebar**: Animated sidebar with multiple panels (Explorer, Search, Git, Settings)
- **Split Pane Workspace**: Support for recursive splitting with tabs
- **Status Bar**: Display status messages and cursor position
- **State Persistence**: Remember window layout and settings between sessions

## Project Structure

```
viloapp/
├── main.py                 # Application entry point
├── ui/                     # UI components
│   ├── main_window.py      # Main application window
│   ├── activity_bar.py     # Vertical activity bar
│   ├── sidebar.py          # Collapsible sidebar
│   ├── workspace.py        # Split pane workspace
│   ├── status_bar.py       # Status bar
│   └── widgets/            # Custom widgets
├── models/                 # Data models
├── resources/              # Resources (icons, styles)
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
└── docs/                   # Documentation
```

## Installation

### Requirements

- Python 3.9+
- PySide6

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/viloapp.git
cd viloapp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. For development, install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

## Usage

Run the application:
```bash
python main.py
```

### Command Line Options

ViloApp supports several command line options for configuring where settings are stored:

#### Settings Configuration
```bash
# Use custom settings directory
python main.py --settings-dir ~/.viloapp-dev

# Use specific settings file (INI format)
python main.py --settings-file /path/to/custom-settings.ini

# Use portable mode (settings in app directory)
python main.py --portable

# Use temporary settings (don't persist after app closes)
python main.py --temp-settings

# Reset all settings to defaults
python main.py --reset-settings
```

#### Development Scenarios
```bash
# Development with isolated settings
python main.py --settings-dir ~/.viloapp-dev

# Testing without affecting main settings
python main.py --temp-settings

# Clean start with defaults
python main.py --reset-settings --temp-settings

# Portable deployment
python main.py --portable
```

#### Environment Variables

You can also configure settings using environment variables (command line options take precedence):

```bash
# Set custom settings directory
export VILOAPP_SETTINGS_DIR=~/.viloapp-dev
python main.py

# Set specific settings file
export VILOAPP_SETTINGS_FILE=/path/to/settings.ini
python main.py

# Enable portable mode
export VILOAPP_PORTABLE=1
python main.py

# Enable temporary settings
export VILOAPP_TEMP_SETTINGS=1
python main.py
```

#### Settings Storage Locations
- **Default**: System-specific locations (Windows Registry, Linux ~/.config, macOS ~/Library)
- **Custom Directory**: Multiple INI files in specified directory
- **Custom File**: Single INI file at specified path  
- **Portable**: Settings stored in `./settings/` within app directory
- **Temporary**: Settings stored in system temp directory, deleted on exit

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run specific test categories:
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e          # E2E tests only
```

### Code Quality

Format code:
```bash
black .
```

Lint code:
```bash
ruff check .
```

Type checking:
```bash
mypy .
```

### Building Documentation

```bash
cd docs
make html
```

## Testing Strategy

The project uses a comprehensive testing approach:

- **Unit Tests**: Test individual components in isolation using `pytest-qt`
- **Integration Tests**: Test component interactions
- **E2E Tests**: Full workflow testing using `pyautogui`
- **CI/CD**: GitHub Actions with headless testing support

See [TESTING_STRATEGY.md](TESTING_STRATEGY.md) for detailed information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Documentation

- [Project Specification](PROJECT.md)
- [Implementation Guide](IMPLEMENTATION_GUIDE.md)
- [Testing Strategy](TESTING_STRATEGY.md)
- [Development Notes](CLAUDE.md)