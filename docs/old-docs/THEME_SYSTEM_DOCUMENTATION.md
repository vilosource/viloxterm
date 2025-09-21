# Theme Management System Documentation

## Overview
This document provides a comprehensive analysis of how the theme management system works in ViloxTerm, from application startup through theme loading and application to the GUI.

## 1. Application Startup and Theme Initialization

### Entry Point (`main.py`)
The theme system initialization begins when the application starts:

1. Application starts and initializes services through `initialize_services()` (line 65)
2. Services are initialized in dependency order with ThemeService created early (line 49 in `services/__init__.py`)
3. ThemeProvider is created and linked to ThemeService (lines 71-74 in `services/__init__.py`)

### Service Initialization Chain
```
main.py
  → MainWindow.__init__()
    → initialize_services()
      → ThemeService creation
        → ThemeProvider creation
          → StylesheetGenerator creation
```

## 2. Theme Service Architecture

### Core Components

#### ThemeService (`services/theme_service.py`)
- Core business logic for theme management
- Handles loading, applying, and managing themes
- Manages both built-in and custom themes
- Emits signals when theme changes

#### ThemeProvider (`ui/themes/theme_provider.py`)
- Bridge between ThemeService and UI layer
- Manages stylesheet caching for performance
- Distributes theme updates to UI components
- Handles stylesheet generation requests

#### StylesheetGenerator (`ui/themes/stylesheet_generator.py`)
- Generates Qt stylesheets from theme colors
- Component-specific stylesheet generation
- Typography integration
- Dynamic stylesheet creation based on current theme

#### Theme Model (`core/themes/theme.py`)
- Data model representing a theme
- Contains colors, typography, and metadata
- Supports theme inheritance (extending base themes)
- Validation of required colors

## 3. Theme File Storage

### Theme Locations

#### Built-in Themes
Location: `resources/themes/builtin/` directory

Available themes:
- `vscode-dark.json` - VSCode Dark+ theme
- `vscode-light.json` - VSCode Light theme
- `monokai.json` - Monokai theme
- `solarized-dark.json` - Solarized Dark theme

#### User Custom Themes
Location: `~/.config/ViloxTerm/themes/` directory
- Custom themes are saved as JSON files
- Directory is automatically created on first run
- Themes can be imported/exported from this location

### Theme JSON Structure
```json
{
  "id": "vscode-dark",
  "name": "VSCode Dark+",
  "description": "Official Visual Studio Code Dark+ theme",
  "version": "1.0.0",
  "author": "ViloxTerm",
  "extends": null,  // Optional: ID of parent theme to inherit from
  "typography": {
    "fontFamily": "Fira Code, Consolas, Monaco, monospace",
    "fontSizeBase": 14,
    "lineHeight": 1.5,
    "fontWeightNormal": 400,
    "fontWeightMedium": 500,
    "fontWeightBold": 700,
    "sizeScale": {
      "xs": 0.75,
      "sm": 0.875,
      "base": 1.0,
      "lg": 1.125,
      "xl": 1.25,
      "2xl": 1.5,
      "3xl": 1.875
    }
  },
  "colors": {
    "editor.background": "#1e1e1e",
    "editor.foreground": "#d4d4d4",
    "editor.lineHighlightBackground": "#2a2d2e",
    "editor.selectionBackground": "#264f78",
    "activityBar.background": "#333333",
    "activityBar.foreground": "#ffffff",
    "sideBar.background": "#252526",
    "sideBar.foreground": "#cccccc",
    "statusBar.background": "#16825d",
    "statusBar.foreground": "#ffffff",
    "tab.activeBackground": "#1e1e1e",
    "tab.activeForeground": "#ffffff",
    // ... many more color definitions
  }
}
```

## 4. Theme Loading Process

### Initialization Sequence

The `ThemeService.initialize()` method performs the following steps:

1. **Load Built-in Themes** (`_load_builtin_themes()`)
   - In production mode: Load from Qt resources (compiled .qrc files)
   - In development mode: Load from filesystem (`resources/themes/builtin/`)

2. **Load User Custom Themes** (`_load_user_themes()`)
   - Scan `~/.config/ViloxTerm/themes/` directory
   - Load and validate each JSON theme file
   - Add valid themes to the theme registry

3. **Check for Theme Reset**
   - If `--reset-theme` command line flag is present, reset to default theme
   - Otherwise, load saved theme preference from QSettings

4. **Apply Initial Theme**
   - Load preference from QSettings key `theme/current`
   - If no preference exists, default to "vscode-dark"
   - Apply the selected theme

5. **Save Preference**
   - Save current theme ID to QSettings for persistence

## 5. Theme Application to GUI

### Application Flow

#### Step 1: Theme Selection
```python
ThemeService.apply_theme(theme_id: str)
  → Load theme from registry
  → Validate theme
  → Set as current theme
  → Save preference to QSettings
```

#### Step 2: Signal Emission
```python
ThemeService emits:
  → theme_changed signal with color dictionary
  → typography_changed signal with typography object
```

#### Step 3: ThemeProvider Response
```python
ThemeProvider receives signals:
  → _on_theme_changed(): Clear stylesheet cache
  → _on_typography_changed(): Clear stylesheet cache
  → Emit style_changed signal to UI components
```

#### Step 4: UI Component Updates
```python
MainWindow.apply_theme():
  → Request stylesheets from ThemeProvider
  → Apply stylesheets to components
  → Each child widget updates its appearance
```

### Stylesheet Generation Process

When a component requests a stylesheet:

```
Component.setStyleSheet(
  ThemeProvider.get_stylesheet("component_name")
    → Check cache for existing stylesheet
    → If not cached:
        StylesheetGenerator.generate("component_name")
          → Call component-specific generator method
          → Use current theme colors and typography
          → Return Qt stylesheet string
    → Cache and return stylesheet
)
```

## 6. Component-Specific Styling

### Available Component Stylesheets

| Component | Description | Key Elements |
|-----------|-------------|--------------|
| `main_window` | Main application window | Background, toolbars, general layout |
| `editor` | Text editor components | Font, colors, selection |
| `terminal` | Terminal widget | Monospace font, ANSI colors |
| `sidebar` | Left sidebar panel | Background, text, sections |
| `activity_bar` | Vertical activity toolbar | Icons, selection, hover states |
| `status_bar` | Bottom status bar | Background, text, sections |
| `tab_widget` | Tab containers | Tab styling, active/inactive states |
| `menu` | Menu bars and items | Menu styling, hover states |
| `splitter` | Pane splitters | Handle styling, hover effects |
| `settings_widget` | Settings dialog | Form elements, groups |
| `pane_header` | Pane header bars | Title, controls, background |
| `command_palette` | Command palette dialog | Input, list items, selection |

### Stylesheet Generator Methods

Each component has a dedicated generator method in `StylesheetGenerator`:

```python
def _component_name_style(self) -> str:
    # Get colors from theme
    bg_color = self._get_color("component.background")
    fg_color = self._get_color("component.foreground")

    # Get typography settings
    font_family = self._get_font_family()
    font_size = self._get_font_size("base")

    # Generate Qt stylesheet
    return f"""
        QWidget {{
            background-color: {bg_color};
            color: {fg_color};
            font-family: {font_family};
            font-size: {font_size}px;
        }}
    """
```

## 7. Theme Commands

### Available Commands

| Command ID | Title | Description |
|------------|-------|-------------|
| `theme.selectTheme` | Select Color Theme | Change the application color theme |
| `theme.getAvailableThemes` | Get Available Themes | List all available themes |
| `theme.getCurrentTheme` | Get Current Theme | Get current theme information |
| `theme.getTheme` | Get Theme | Get specific theme by ID |
| `theme.createCustomTheme` | Create Custom Theme | Create new custom theme |
| `theme.saveCustomTheme` | Save Custom Theme | Save theme to disk |
| `theme.deleteCustomTheme` | Delete Custom Theme | Delete a custom theme |
| `theme.getComponentStylesheet` | Get Component Stylesheet | Get stylesheet for specific component |
| `theme.applyThemeColors` | Apply Theme Colors | Apply color changes to current theme |
| `theme.applyTypography` | Apply Typography | Apply typography changes |

### Command Implementation Pattern

Commands follow a consistent pattern:

```python
@command(
    id="theme.commandName",
    title="Command Title",
    category="Preferences",
    description="Command description"
)
def theme_command(context: CommandContext, **kwargs) -> CommandResult:
    # Get theme service
    theme_service = context.get_service(ThemeService)

    # Perform operation
    result = theme_service.operation(**kwargs)

    # Return result
    return CommandResult(success=True, value=result)
```

## 8. Theme Persistence

### Settings Storage

#### Current Theme Preference
- Stored in QSettings with key: `theme/current`
- Platform-specific locations:
  - **Windows**: Registry `HKEY_CURRENT_USER\Software\ViloxTerm\ViloxTerm`
  - **Linux**: `~/.config/ViloxTerm/ViloxTerm.conf`
  - **macOS**: `~/Library/Preferences/com.ViloxTerm.ViloxTerm.plist`
  - **Portable mode**: Local `settings.ini` file

#### Custom Theme Files
- Saved as JSON files in: `~/.config/ViloxTerm/themes/{theme_id}.json`
- Automatically saved when modified through theme editor
- Can be exported/imported for sharing

### Save/Load Flow

#### Saving Theme Preference
```python
ThemeService._save_theme_preference(theme_id):
    → get_settings("ViloxTerm", "ViloxTerm")
    → settings.setValue("theme/current", theme_id)
    → settings.sync()
```

#### Loading Theme Preference
```python
ThemeService._load_theme_preference():
    → get_settings("ViloxTerm", "ViloxTerm")
    → settings.value("theme/current", "vscode-dark")
    → Return theme ID
```

## 9. Theme Editor Integration

### Theme Editor Widget (`ui/widgets/theme_editor_widget.py`)

The theme editor provides a GUI for theme customization:

#### Features
- **Real-time Preview**: Changes are applied instantly to preview widget
- **Color Editing**: Individual color pickers for each theme property
- **Typography Control**: Font family, size, and weight adjustments
- **Preview Mode**: Test changes without saving
- **Save/Apply/Reset**: Full control over theme modifications
- **Import/Export**: Support for VSCode theme format

#### Architecture
```
ThemeEditorAppWidget
  ├── ThemeControlsWidget (left panel)
  │   ├── Color categories
  │   ├── Color pickers
  │   └── Typography settings
  ├── ThemePreviewWidget (right panel)
  │   ├── Live preview
  │   └── Sample components
  └── ThemePersistenceManager
      ├── Save/Load operations
      ├── Import/Export
      └── Theme creation
```

## 10. Typography System

### Typography Configuration

The typography system provides comprehensive font control:

#### Configuration Structure
```python
ThemeTypography:
    fontFamily: str           # Font family names
    fontSizeBase: int        # Base font size in pixels
    lineHeight: float        # Line height multiplier
    fontWeightNormal: int    # Normal weight (400)
    fontWeightMedium: int    # Medium weight (500)
    fontWeightBold: int      # Bold weight (700)
    sizeScale: dict         # Size scaling factors
```

#### Size Scaling System
- `xs`: 0.75x base size (extra small)
- `sm`: 0.875x base size (small)
- `base`: 1.0x base size (normal)
- `lg`: 1.125x base size (large)
- `xl`: 1.25x base size (extra large)
- `2xl`: 1.5x base size (2x large)
- `3xl`: 1.875x base size (3x large)

#### Component-Specific Typography
Components can override typography settings:

```python
theme_service.get_component_typography("editor"):
    → Returns editor-specific font settings
    → Falls back to theme defaults if not specified
```

### Typography Presets

Pre-configured typography settings for common use cases:

- **Compact**: Smaller sizes, tighter spacing
- **Default**: Balanced for general use
- **Comfortable**: Larger sizes, more spacing
- **Presentation**: Extra large for demos

## 11. Theme Inheritance

### Extending Themes

Themes can inherit from parent themes:

```json
{
  "id": "my-custom-dark",
  "extends": "vscode-dark",
  "colors": {
    // Only override specific colors
    "editor.background": "#000000"
  }
}
```

### Inheritance Resolution
```python
Theme.merge_with_parent(parent_theme):
    → Start with parent colors
    → Override with child colors
    → Inherit typography if not specified
    → Result: Complete theme with inheritance
```

## 12. Performance Optimizations

### Stylesheet Caching
- Stylesheets are generated once and cached
- Cache is cleared when theme changes
- Reduces redundant generation overhead

### Signal Batching
- Multiple color changes are batched
- Single stylesheet regeneration per update
- Prevents UI flickering during editing

### Lazy Loading
- Themes are loaded on demand
- User themes loaded only when needed
- Reduces startup time

## Summary

The theme management system in ViloxTerm follows a clean, layered architecture:

1. **Data Layer**: Theme JSON files provide color and typography definitions
2. **Service Layer**: ThemeService manages business logic and theme operations
3. **Provider Layer**: ThemeProvider bridges the service and UI layers
4. **Generator Layer**: StylesheetGenerator creates Qt-specific stylesheets
5. **UI Layer**: Components apply generated stylesheets for theming

This architecture ensures:
- **Separation of Concerns**: Each layer has a specific responsibility
- **Performance**: Caching and lazy loading optimize runtime behavior
- **Extensibility**: New themes and components can be added easily
- **Customization**: Full support for user-created themes
- **Consistency**: Centralized theme management ensures uniform appearance
- **Reactivity**: Signal-based updates keep UI synchronized with theme changes

The system supports both built-in and custom themes, with comprehensive editing capabilities through the theme editor widget, making it a complete theming solution for the application.