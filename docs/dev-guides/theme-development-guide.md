# Theme Development Guide

## Overview

This guide provides comprehensive instructions for developers working with ViloxTerm's theme system. Whether you're adding theme support to a new widget, creating custom themes, or extending the theme system itself, this guide covers all the essential patterns and best practices.

## Quick Start

### Adding Theme Support to a Widget

1. **Import the required services**:
```python
from services.service_locator import ServiceLocator
from services.theme_service import ThemeService
```

2. **Implement the `apply_theme()` method**:
```python
def apply_theme(self):
    """Apply current theme to this widget."""
    locator = ServiceLocator.get_instance()
    theme_service = locator.get(ThemeService)
    theme_provider = theme_service.get_theme_provider() if theme_service else None

    if theme_provider:
        stylesheet = theme_provider.get_stylesheet("your_component_name")
        self.setStyleSheet(stylesheet)
```

3. **Connect to theme changes**:
```python
def __init__(self):
    super().__init__()
    self.setup_ui()
    self.apply_theme()  # Apply initial theme

    # Connect to theme change signals
    locator = ServiceLocator.get_instance()
    theme_service = locator.get(ThemeService)
    if theme_service:
        theme_provider = theme_service.get_theme_provider()
        if theme_provider:
            theme_provider.style_changed.connect(self.apply_theme)
```

## Creating Custom Themes

### Theme File Structure

Create a JSON file with the following structure:

```json
{
  "id": "my-custom-theme",
  "name": "My Custom Theme",
  "description": "A beautiful custom theme",
  "version": "1.0.0",
  "author": "Your Name",
  "extends": "vscode-dark",  // Optional: inherit from existing theme
  "colors": {
    "editor.background": "#1a1a1a",
    "editor.foreground": "#ffffff",
    "activityBar.background": "#2d2d2d",
    "sideBar.background": "#1e1e1e",
    "statusBar.background": "#007acc",
    "terminal.ansiBlack": "#000000",
    "terminal.ansiRed": "#ff6b6b",
    "terminal.ansiGreen": "#51cf66",
    "terminal.ansiYellow": "#ffd43b",
    "terminal.ansiBlue": "#74c0fc",
    "terminal.ansiMagenta": "#d0bfff",
    "terminal.ansiCyan": "#99e9f2",
    "terminal.ansiWhite": "#f8f9fa"
  }
}
```

### Available Color Keys

#### Core UI Colors
```json
{
  // Editor
  "editor.background": "#1e1e1e",
  "editor.foreground": "#d4d4d4",
  "editor.lineHighlightBackground": "#1e1e1e",
  "editor.selectionBackground": "#264f78",

  // Activity Bar
  "activityBar.background": "#333333",
  "activityBar.foreground": "#ffffff",
  "activityBar.activeBorder": "#007acc",

  // Sidebar
  "sideBar.background": "#252526",
  "sideBar.foreground": "#cccccc",
  "sideBar.border": "#444444",

  // Status Bar
  "statusBar.background": "#16825d",
  "statusBar.foreground": "#ffffff",

  // Tabs
  "tab.activeBackground": "#1e1e1e",
  "tab.activeForeground": "#ffffff",
  "tab.inactiveBackground": "#2d2d2d",
  "tab.inactiveForeground": "#ffffff80",

  // Borders and Panels
  "panel.background": "#1e1e1e",
  "panel.border": "#444444",
  "border": "#444444",

  // Input and Buttons
  "input.background": "#3c3c3c",
  "input.foreground": "#cccccc",
  "input.border": "#444444",
  "button.background": "#0e639c",
  "button.foreground": "#ffffff"
}
```

#### Terminal Colors
```json
{
  // Standard ANSI colors
  "terminal.ansiBlack": "#000000",
  "terminal.ansiRed": "#cd3131",
  "terminal.ansiGreen": "#0dbc79",
  "terminal.ansiYellow": "#e5e510",
  "terminal.ansiBlue": "#2472c8",
  "terminal.ansiMagenta": "#bc3fbc",
  "terminal.ansiCyan": "#11a8cd",
  "terminal.ansiWhite": "#e5e5e5",

  // Bright ANSI colors
  "terminal.ansiBrightBlack": "#666666",
  "terminal.ansiBrightRed": "#f14c4c",
  "terminal.ansiBrightGreen": "#23d18b",
  "terminal.ansiBrightYellow": "#f5f543",
  "terminal.ansiBrightBlue": "#3b8eea",
  "terminal.ansiBrightMagenta": "#d670d6",
  "terminal.ansiBrightCyan": "#29b8db",
  "terminal.ansiBrightWhite": "#e5e5e5",

  // Terminal UI
  "terminal.background": "#1e1e1e",
  "terminal.foreground": "#d4d4d4",
  "terminal.cursor": "#ffffff",
  "terminal.selection": "#264f78"
}
```

### Theme Inheritance

Use the `extends` field to inherit from existing themes:

```json
{
  "id": "my-dark-variant",
  "name": "My Dark Variant",
  "extends": "vscode-dark",
  "colors": {
    // Only specify colors you want to override
    "editor.background": "#0d1117",
    "sideBar.background": "#161b22"
  }
}
```

Color resolution order:
1. Direct colors in current theme
2. Inherited colors from `extends` theme
3. Default fallback colors

### Installing Custom Themes

1. **Via Command**: Use `theme.importTheme` command with file path
2. **Manual Installation**: Place JSON file in `~/.config/ViloxTerm/themes/`
3. **Programmatic**: Use `ThemeService.import_theme()` method

## Widget Development Patterns

### Standard Widget Pattern

```python
class MyCustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_theme_signals()
        self.apply_theme()  # Apply initial theme

    def setup_ui(self):
        """Set up the widget UI."""
        # Widget setup code here
        pass

    def connect_theme_signals(self):
        """Connect to theme change signals."""
        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        if theme_service:
            theme_provider = theme_service.get_theme_provider()
            if theme_provider:
                theme_provider.style_changed.connect(self.apply_theme)

    def apply_theme(self):
        """Apply current theme to this widget."""
        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        theme_provider = theme_service.get_theme_provider() if theme_service else None

        if theme_provider:
            # Get component-specific stylesheet
            stylesheet = theme_provider.get_stylesheet("my_component")
            self.setStyleSheet(stylesheet)

    def cleanup(self):
        """Clean up theme connections."""
        # Disconnect signals if needed
        pass
```

### AppWidget Pattern

For AppWidgets (widgets in the split pane system):

```python
from ui.widgets.app_widget import AppWidget

class MyAppWidget(AppWidget):
    def __init__(self, pane_id: str):
        super().__init__(pane_id)
        self.setup_ui()
        self.apply_theme()

    def apply_theme(self):
        """Apply theme with AppWidget-specific considerations."""
        super().apply_theme()  # Call base implementation

        # Add custom theme handling
        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        theme_provider = theme_service.get_theme_provider() if theme_service else None

        if theme_provider:
            colors = theme_provider._theme_service.get_colors()

            # Example: Update specific elements based on colors
            self.special_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors.get('editor.foreground', '#cccccc')};
                    background-color: {colors.get('editor.background', '#1e1e1e')};
                }}
            """)
```

### Dialog Pattern

For dialogs and popup windows:

```python
class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_theme()

        # Connect to theme changes
        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        if theme_service:
            theme_provider = theme_service.get_theme_provider()
            if theme_provider:
                theme_provider.style_changed.connect(self.apply_theme)

    def apply_theme(self):
        """Apply theme to dialog."""
        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        theme_provider = theme_service.get_theme_provider() if theme_service else None

        if theme_provider:
            colors = theme_provider._theme_service.get_colors()

            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors.get('panel.background', '#1e1e1e')};
                    color: {colors.get('editor.foreground', '#cccccc')};
                    border: 1px solid {colors.get('border', '#444444')};
                }}
                QPushButton {{
                    background-color: {colors.get('button.background', '#0e639c')};
                    color: {colors.get('button.foreground', '#ffffff')};
                    border: none;
                    padding: 6px 12px;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: {colors.get('button.hoverBackground', '#1177bb')};
                }}
            """)
```

## Stylesheet Generation

### Adding Custom Component Stylesheets

To add support for a new component in `StylesheetGenerator`:

```python
def get_stylesheet(self, component: str) -> str:
    """Get stylesheet for a component."""
    generators = {
        'my_component': self._generate_my_component_stylesheet,
        # ... existing generators
    }

    generator = generators.get(component)
    if generator:
        return generator()
    return ""

def _generate_my_component_stylesheet(self) -> str:
    """Generate stylesheet for my custom component."""
    colors = self.theme_service.get_colors()

    return f"""
        MyComponent {{
            background-color: {colors.get('editor.background', '#1e1e1e')};
            color: {colors.get('editor.foreground', '#cccccc')};
            border: 1px solid {colors.get('border', '#444444')};
        }}

        MyComponent::item {{
            padding: 4px;
            border-radius: 2px;
        }}

        MyComponent::item:selected {{
            background-color: {colors.get('editor.selectionBackground', '#264f78')};
        }}

        MyComponent::item:hover {{
            background-color: {colors.get('editor.lineHighlightBackground', '#2d2d2d')};
        }}
    """
```

### Dynamic Styling Patterns

For complex styling that depends on theme colors:

```python
def apply_theme(self):
    """Apply theme with dynamic calculations."""
    locator = ServiceLocator.get_instance()
    theme_service = locator.get(ThemeService)
    theme_provider = theme_service.get_theme_provider() if theme_service else None

    if theme_provider:
        colors = theme_provider._theme_service.get_colors()

        # Get base colors
        bg_color = colors.get('editor.background', '#1e1e1e')
        fg_color = colors.get('editor.foreground', '#cccccc')

        # Calculate derived colors (example: lighter/darker variants)
        from PySide6.QtGui import QColor
        bg_qcolor = QColor(bg_color)
        lighter_bg = bg_qcolor.lighter(120).name()
        darker_bg = bg_qcolor.darker(120).name()

        # Apply dynamic stylesheet
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {fg_color};
            }}
            QWidget:hover {{
                background-color: {lighter_bg};
            }}
            QWidget:pressed {{
                background-color: {darker_bg};
            }}
        """)
```

## Testing Theme Support

### Unit Testing Widget Themes

```python
import pytest
from PySide6.QtWidgets import QApplication
from services.theme_service import ThemeService
from ui.themes.theme_provider import ThemeProvider

def test_widget_theme_application(qtbot):
    """Test that widget applies theme correctly."""
    # Create services
    theme_service = ThemeService()
    theme_provider = ThemeProvider(theme_service)
    theme_service.set_theme_provider(theme_provider)

    # Initialize with test themes
    theme_service.load_builtin_themes()

    # Create widget
    widget = MyCustomWidget()
    qtbot.addWidget(widget)

    # Apply theme
    widget.apply_theme()

    # Verify stylesheet was applied
    assert widget.styleSheet() != ""

    # Test theme switching
    theme_service.apply_theme("vscode-light")
    widget.apply_theme()

    # Verify stylesheet changed
    light_stylesheet = widget.styleSheet()

    theme_service.apply_theme("vscode-dark")
    widget.apply_theme()

    dark_stylesheet = widget.styleSheet()
    assert light_stylesheet != dark_stylesheet
```

### Integration Testing

```python
def test_theme_system_integration(qtbot):
    """Test full theme system integration."""
    from services.service_locator import ServiceLocator

    # Set up service locator
    locator = ServiceLocator.get_instance()

    # Initialize theme service
    theme_service = ThemeService()
    locator.register(ThemeService, theme_service)

    # Create theme provider
    theme_provider = ThemeProvider(theme_service)
    theme_service.set_theme_provider(theme_provider)

    # Test widget creation and theme application
    widget = MyCustomWidget()
    qtbot.addWidget(widget)

    # Widget should automatically apply current theme
    assert widget.styleSheet() != ""

    # Test theme change propagation
    with qtbot.waitSignal(theme_provider.style_changed):
        theme_service.apply_theme("monokai")

    # Widget should have updated automatically
    assert "monokai" in widget.styleSheet().lower() or len(widget.styleSheet()) > 100
```

## Debugging Theme Issues

### Common Issues and Solutions

#### 1. Widget Not Updating on Theme Change
**Problem**: Widget doesn't update when theme changes
**Solution**: Ensure signal connection in widget initialization:

```python
def __init__(self):
    super().__init__()
    self.setup_ui()
    self.connect_theme_signals()  # Make sure this is called
    self.apply_theme()
```

#### 2. Stylesheet Not Applied
**Problem**: `apply_theme()` called but no visual change
**Solution**: Check service availability and add debugging:

```python
def apply_theme(self):
    locator = ServiceLocator.get_instance()
    theme_service = locator.get(ThemeService)
    print(f"ThemeService available: {theme_service is not None}")

    if theme_service:
        theme_provider = theme_service.get_theme_provider()
        print(f"ThemeProvider available: {theme_provider is not None}")

        if theme_provider:
            stylesheet = theme_provider.get_stylesheet("component_name")
            print(f"Generated stylesheet length: {len(stylesheet)}")
            self.setStyleSheet(stylesheet)
```

#### 3. Colors Not Resolving
**Problem**: Colors showing as defaults instead of theme colors
**Solution**: Verify color key names and inheritance:

```python
def apply_theme(self):
    # ... get theme_provider ...
    if theme_provider:
        colors = theme_provider._theme_service.get_colors()
        print(f"Available colors: {list(colors.keys())}")

        # Use exact color keys from theme
        bg_color = colors.get('editor.background', '#1e1e1e')
        print(f"Background color: {bg_color}")
```

### Theme Development Tools

#### Theme Validation

```python
def validate_theme_file(file_path: str) -> bool:
    """Validate a theme file before import."""
    try:
        with open(file_path, 'r') as f:
            theme_data = json.load(f)

        # Check required fields
        required_fields = ['id', 'name', 'description', 'version', 'author', 'colors']
        for field in required_fields:
            if field not in theme_data:
                print(f"Missing required field: {field}")
                return False

        # Validate color format
        for key, value in theme_data['colors'].items():
            if not is_valid_color(value):
                print(f"Invalid color format for {key}: {value}")
                return False

        return True
    except Exception as e:
        print(f"Theme validation error: {e}")
        return False

def is_valid_color(color: str) -> bool:
    """Check if color is in valid format."""
    from PySide6.QtGui import QColor
    return QColor(color).isValid()
```

#### Live Theme Preview

```python
class ThemePreviewWidget(QWidget):
    """Widget for live theme preview during development."""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_preview_timer()

    def setup_preview_timer(self):
        """Set up timer for live preview updates."""
        from PySide6.QtCore import QTimer
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(1000)  # Update every second

    def update_preview(self):
        """Update preview if theme file changed."""
        # Check file modification time and reload if changed
        pass
```

## Best Practices

### Performance
- Cache stylesheets when possible
- Avoid frequent theme switching in tight loops
- Use signals efficiently - connect once, disconnect on cleanup
- Minimize stylesheet complexity

### Maintainability
- Use consistent color key naming
- Document custom color keys
- Provide fallback colors for all theme properties
- Keep widget theme code separate from business logic

### User Experience
- Provide immediate visual feedback on theme changes
- Support both light and dark theme variants
- Test themes with different content types
- Ensure sufficient color contrast for accessibility

### Code Quality
- Follow the established widget patterns
- Write tests for theme functionality
- Use type hints for theme-related methods
- Document custom stylesheet generators

This guide should help you effectively work with ViloxTerm's theme system, whether you're adding theme support to widgets or creating beautiful custom themes!