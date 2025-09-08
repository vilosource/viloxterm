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