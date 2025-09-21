# Theme Development Guide

## Overview

This guide covers how to create, modify, and manage themes in ViloxTerm. The application includes a visual theme editor and supports importing VSCode-compatible themes.

## Quick Start

### Opening the Theme Editor

1. **Via Command Palette** (Ctrl+Shift+P):
   - Type "theme editor"
   - Select "Open Theme Editor"

2. **Via Command**:
   - Execute command: `theme.openEditor`

3. **Via Code**:
   ```python
   from core.commands.executor import execute_command
   execute_command("theme.openEditor")
   ```

## Using the Theme Editor

### Main Features

The theme editor provides a comprehensive interface for theme customization:

- **Theme Selector**: Choose from existing themes or create new ones
- **Property Editor**: Organized color properties by category
- **Live Preview**: See changes in real-time
- **Import/Export**: Share themes or import VSCode themes
- **Search**: Find specific properties quickly

### Creating a New Theme

1. Click the **"New"** button in the theme editor
2. Enter a unique theme ID (e.g., "my-awesome-theme")
3. Provide a display name (e.g., "My Awesome Theme")
4. Start customizing colors

### Modifying Colors

1. **Browse Categories**: Properties are organized into logical groups:
   - Editor (background, foreground, selection)
   - Terminal (colors, ANSI palette)
   - Activity Bar (icons, background)
   - Sidebar (panels, headers)
   - Status Bar (items, background)

2. **Change Colors**:
   - Click the color button to open color picker
   - Enter hex values directly (#RRGGBB format)
   - Use suggested colors from current theme

3. **Preview Changes**:
   - Changes appear in the preview widget immediately
   - Apply to see changes in the full application

### Importing VSCode Themes

1. Click **"Import VSCode"** button
2. Select a `.json` theme file
3. The importer will:
   - Map VSCode color keys to ViloxTerm equivalents
   - Derive missing colors automatically
   - Validate the imported theme

## Theme File Format

### JSON Structure

```json
{
  "id": "my-theme",
  "name": "My Theme",
  "description": "A beautiful custom theme",
  "version": "1.0.0",
  "author": "Your Name",
  "extends": "vscode-dark",  // Optional: inherit from base theme
  "colors": {
    "editor.background": "#1e1e1e",
    "editor.foreground": "#d4d4d4",
    "editor.selectionBackground": "#264f78",
    "terminal.background": "#000000",
    "terminal.foreground": "#ffffff",
    "activityBar.background": "#333333",
    "sideBar.background": "#252526",
    "statusBar.background": "#007acc"
  }
}
```

### Color Properties Reference

#### Editor Colors
- `editor.background` - Main editor background
- `editor.foreground` - Default text color
- `editor.selectionBackground` - Selected text background
- `editor.lineHighlightBackground` - Current line highlight
- `editorCursor.foreground` - Cursor color

#### Terminal Colors
- `terminal.background` - Terminal background
- `terminal.foreground` - Terminal text
- `terminal.ansiBlack` through `terminal.ansiWhite` - ANSI colors
- `terminal.ansiBrightBlack` through `terminal.ansiBrightWhite` - Bright ANSI colors

#### UI Components
- `activityBar.background` - Left icon bar background
- `activityBar.foreground` - Icon colors
- `sideBar.background` - Sidebar panel background
- `statusBar.background` - Bottom status bar
- `titleBar.activeBackground` - Window title bar

### Theme Inheritance

Themes can extend other themes to inherit their colors:

```json
{
  "id": "my-dark-variant",
  "extends": "vscode-dark",
  "colors": {
    // Only override specific colors
    "editor.background": "#0a0a0a",
    "statusBar.background": "#ff0000"
  }
}
```

## Programmatic Theme Creation

### Using ThemeService

```python
from services.service_locator import ServiceLocator
from services.theme_service import ThemeService
from core.themes.theme import Theme

# Get theme service
locator = ServiceLocator.get_instance()
theme_service = locator.get(ThemeService)

# Create new theme
theme = Theme(
    id="custom-theme",
    name="Custom Theme",
    description="My custom theme",
    version="1.0.0",
    author="Developer",
    colors={
        "editor.background": "#1a1a1a",
        "editor.foreground": "#e0e0e0",
        # ... more colors
    }
)

# Save and apply
theme_service.save_custom_theme(theme)
theme_service.apply_theme("custom-theme")
```

### Creating Theme Commands

```python
from core.commands.decorators import command
from core.commands.base import CommandContext, CommandResult

@command(
    id="theme.applyMyTheme",
    title="Apply My Custom Theme",
    category="Theme"
)
def apply_my_theme_command(context: CommandContext) -> CommandResult:
    theme_service = context.get_service(ThemeService)
    if theme_service:
        theme_service.apply_theme("my-custom-theme")
        return CommandResult(success=True)
    return CommandResult(success=False, error="Theme service not available")
```

## VSCode Theme Compatibility

### Supported Properties

The VSCode theme importer maps over 100 color properties. Key mappings include:

- All editor colors (background, foreground, selection, etc.)
- Terminal colors including full ANSI palette
- UI components (activity bar, sidebar, status bar)
- Widget colors (buttons, inputs, dropdowns)
- Diff editor colors
- Debug console colors

### Color Derivation

When importing VSCode themes, missing colors are automatically derived:

1. **Terminal colors** from editor colors
2. **Hover states** from base colors with brightness adjustment
3. **Border colors** from background colors
4. **Selection colors** from accent colors

## Testing Themes

### Unit Tests

```python
def test_theme_colors():
    theme = Theme(
        id="test-theme",
        name="Test Theme",
        colors={"editor.background": "#1e1e1e"}
    )
    assert theme.get_color("editor.background") == "#1e1e1e"
    assert theme.get_color("missing.color", "#default") == "#default"
```

### GUI Tests

```python
def test_theme_editor_color_change(qtbot):
    from ui.widgets.theme_editor_widget import ThemeEditorAppWidget

    widget = ThemeEditorAppWidget(widget_id="test")
    qtbot.addWidget(widget)

    # Change a color
    widget._color_fields["editor.background"].set_color("#ff0000")

    # Verify change
    colors = widget._get_current_colors()
    assert colors["editor.background"] == "#ff0000"
```

## Best Practices

### 1. Color Consistency
- Use a consistent color palette throughout
- Maintain good contrast ratios for accessibility
- Test with different content types

### 2. Theme Naming
- Use descriptive IDs (e.g., "monokai-pro", "dracula-soft")
- Include version numbers for updates
- Add meaningful descriptions

### 3. Property Coverage
- Define all essential properties
- Use inheritance for variants
- Test missing property fallbacks

### 4. Performance
- Avoid extremely frequent theme switches
- Cache compiled stylesheets when possible
- Use the `_updating` flag pattern to prevent loops

## Troubleshooting

### Common Issues

#### Theme Not Applying
- Check theme ID is unique
- Verify JSON syntax is valid
- Ensure required properties are defined

#### Infinite Update Loop
- Use `_updating` flag in custom widgets
- Disconnect signals during updates
- Batch color changes

#### Colors Not Showing
- Verify hex color format (#RRGGBB)
- Check property key spelling
- Test inheritance chain

### Debug Commands

```python
# List all available themes
themes = theme_service.get_available_themes()
for theme_info in themes:
    print(f"{theme_info.id}: {theme_info.name}")

# Get current theme colors
theme = theme_service.get_current_theme()
for key, color in theme.colors.items():
    print(f"{key}: {color}")

# Validate theme file
from core.themes.schema import validate_theme
is_valid = validate_theme(theme_dict)
```

## Distribution

### Sharing Themes

1. **Export from Editor**:
   - Click "Export" button
   - Choose location to save `.json` file

2. **Manual Export**:
   ```python
   theme_service.export_theme("theme-id", Path("my-theme.json"))
   ```

3. **Package with Application**:
   - Place in `resources/themes/builtin/`
   - Theme loads automatically on startup

### Theme Locations

- **Built-in**: `resources/themes/builtin/`
- **User Themes**: `~/.config/viloxterm/themes/` (Linux/Mac)
- **User Themes**: `%APPDATA%/viloxterm/themes/` (Windows)

## Advanced Topics

### Dynamic Theme Generation

```python
def generate_theme_from_image(image_path: Path) -> Theme:
    """Generate theme colors from an image."""
    # Extract dominant colors
    colors = extract_colors(image_path)

    return Theme(
        id=f"generated-{uuid.uuid4().hex[:8]}",
        name="Generated Theme",
        colors={
            "editor.background": colors.darkest,
            "editor.foreground": colors.lightest,
            "activityBar.background": colors.accent1,
            "statusBar.background": colors.accent2,
            # ... map other colors
        }
    )
```

### Theme Variants

```python
def create_theme_variant(base_theme: Theme, adjustments: dict) -> Theme:
    """Create a variant of an existing theme."""
    variant = Theme(
        id=f"{base_theme.id}-variant",
        name=f"{base_theme.name} (Variant)",
        extends=base_theme.id,
        colors={}
    )

    # Apply adjustments
    for key, adjustment in adjustments.items():
        base_color = base_theme.get_color(key)
        variant.colors[key] = apply_adjustment(base_color, adjustment)

    return variant
```

## Contributing Themes

To contribute a theme to ViloxTerm:

1. Create your theme using the editor
2. Test thoroughly with different file types
3. Export to JSON file
4. Submit pull request with:
   - Theme file in `resources/themes/builtin/`
   - Screenshot in PR description
   - Update to theme list in documentation

## Resources

- [VSCode Theme Color Reference](https://code.visualstudio.com/api/references/theme-color)
- [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design Color System](https://material.io/design/color/)
- [Qt Stylesheet Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)