# Theme Management System Architecture

## Overview

The Theme Management System provides dynamic theme switching capabilities for ViloxTerm without requiring application restart. It follows a clean service-oriented architecture with proper separation of concerns between business logic, UI bridging, and presentation layers.

## Architecture Diagram

```
User Actions (Commands/UI)
    ↓
ThemeService (Business Logic)
    ↓
ThemeProvider (UI Bridge)
    ↓
StylesheetGenerator (CSS Generation)
    ↓
UI Components (Styled Widgets)
```

## Core Components

### 1. ThemeService (`services/theme_service.py`)

**Purpose**: Central business logic for theme management

**Responsibilities**:
- Load themes from built-in resources and user directories
- Theme validation using schema
- Theme inheritance and color resolution
- Apply themes with signal emission
- Import/export theme functionality
- Theme persistence via QSettings

**Key Methods**:
```python
def get_available_themes() -> List[ThemeInfo]
def get_current_theme() -> Optional[Theme]
def apply_theme(theme_id: str) -> bool
def get_colors() -> Dict[str, str]
def import_theme(file_path: Path) -> Optional[str]
def export_theme(theme_id: str, file_path: Path) -> bool
```

**Signals**:
- `theme_changed(dict)` - Emitted when theme changes with color dictionary

### 2. ThemeProvider (`ui/themes/theme_provider.py`)

**Purpose**: Bridge between ThemeService and UI components

**Responsibilities**:
- Stylesheet caching for performance
- Widget update orchestration
- Signal forwarding from ThemeService
- UI-specific theme operations

**Key Features**:
- Efficient stylesheet caching
- Automatic cache invalidation on theme changes
- Component-specific stylesheet generation
- Signal-based UI updates

### 3. StylesheetGenerator (`ui/themes/stylesheet_generator.py`)

**Purpose**: Dynamic CSS stylesheet generation

**Responsibilities**:
- Component-specific stylesheet templates
- Dynamic color injection into templates
- Efficient caching of generated stylesheets
- Support for theme inheritance

**Supported Components**:
- Main window and dialogs
- Activity bar and sidebar
- Workspace and tab widgets
- Terminal and editor widgets
- Status bar and headers
- Custom widgets

### 4. Theme Model (`core/themes/theme.py`)

**Purpose**: Data model for theme representation

**Structure**:
```python
@dataclass
class Theme:
    id: str                    # Unique theme identifier
    name: str                  # Display name
    description: str           # Theme description
    version: str              # Theme version
    author: str               # Theme author
    extends: Optional[str]     # Base theme inheritance
    colors: Dict[str, str]     # Color definitions
```

**Features**:
- Theme inheritance support
- Color validation
- JSON serialization/deserialization
- Version compatibility

### 5. Theme Schema (`core/themes/schema.py`)

**Purpose**: Theme validation and structure definition

**Responsibilities**:
- JSON schema validation
- Color format validation (hex, rgb, etc.)
- Required field validation
- Theme compatibility checking

## Data Flow

### Theme Loading Process

1. **Initialization**:
   ```
   ThemeService.__init__() → Load built-in themes → Load user themes
   ```

2. **Theme Resolution**:
   ```
   Theme JSON → Parse → Validate → Resolve inheritance → Cache
   ```

3. **Theme Application**:
   ```
   apply_theme() → Resolve colors → Emit signal → Update UI
   ```

### UI Update Process

1. **Signal Propagation**:
   ```
   ThemeService.theme_changed → ThemeProvider.style_changed → Widget.apply_theme()
   ```

2. **Stylesheet Generation**:
   ```
   Widget requests stylesheet → ThemeProvider → StylesheetGenerator → Cached result
   ```

## File Structure

```
/core/themes/
├── __init__.py              # Package initialization
├── theme.py                 # Theme data model and ThemeInfo
├── schema.py                # Theme validation schema
├── constants.py             # Theme color key constants
├── property_categories.py   # Theme property categorization
└── importers.py             # Theme import/export functionality

/services/
└── theme_service.py         # Theme business logic service

/ui/themes/
├── __init__.py              # Package initialization
├── theme_provider.py        # UI bridge for theme system
└── stylesheet_generator.py  # Dynamic stylesheet generation

/ui/widgets/
├── theme_editor_widget.py   # Visual theme editor widget
├── theme_preview_widget.py  # Live theme preview widget
└── color_picker_widget.py   # Color picker for theme editing

/resources/themes/builtin/
├── vscode-dark.json         # VSCode Dark+ theme
├── vscode-light.json        # VSCode Light theme
└── monokai.json             # Monokai theme

/core/commands/builtin/
└── theme_commands.py        # Theme-related commands
```

## Theme File Format

### JSON Structure
```json
{
  "id": "theme-identifier",
  "name": "Display Name",
  "description": "Theme description",
  "version": "1.0.0",
  "author": "Author Name",
  "extends": "base-theme-id",  // Optional inheritance
  "colors": {
    "editor.background": "#1e1e1e",
    "editor.foreground": "#d4d4d4",
    "activityBar.background": "#333333",
    "sideBar.background": "#252526",
    "statusBar.background": "#16825d"
  }
}
```

### Color Resolution

1. **Direct Colors**: Defined in current theme
2. **Inherited Colors**: From `extends` base theme
3. **Default Colors**: Fallback values from constants

## Service Integration

### Service Locator Pattern

```python
# Service registration (services/__init__.py)
theme_service = ThemeService()
locator.register(ThemeService, theme_service)

# Create ThemeProvider after service registration
theme_provider = ThemeProvider(theme_service)
theme_service.set_theme_provider(theme_provider)
```

### Widget Integration

```python
# Widget theme support pattern
def apply_theme(self):
    from services.service_locator import ServiceLocator
    from services.theme_service import ThemeService

    locator = ServiceLocator.get_instance()
    theme_service = locator.get(ThemeService)
    theme_provider = theme_service.get_theme_provider() if theme_service else None

    if theme_provider:
        stylesheet = theme_provider.get_stylesheet("component_name")
        self.setStyleSheet(stylesheet)
```

## Theme Editor

### Overview

The Theme Editor provides a visual interface for creating, modifying, and testing themes in real-time. It's implemented as an AppWidget that integrates with the workspace system.

### Components

#### ThemeEditorAppWidget (`ui/widgets/theme_editor_widget.py`)

**Purpose**: Main theme editor interface

**Features**:
- Visual color editing with live preview
- Theme selection and switching
- Import/export functionality
- Property categorization and search
- Save and apply changes
- Infinite loop prevention for recursive updates

**Key Methods**:
```python
def _load_theme(theme: Theme)  # Load theme with update protection
def _apply_theme() -> bool      # Apply changes to application
def _save_theme() -> bool        # Save theme to disk
def _import_vscode_theme()      # Import VSCode theme
```

#### ThemePreviewWidget (`ui/widgets/theme_preview_widget.py`)

**Purpose**: Live preview of theme changes

**Features**:
- Miniature IDE interface preview
- Real-time color updates
- Activity bar, sidebar, editor simulation
- Terminal and status bar preview

#### ColorPickerWidget (`ui/widgets/color_picker_widget.py`)

**Purpose**: Color selection interface

**Features**:
- Color button with preview
- Hex input validation
- Color dialog integration
- Live preview during selection
- Theme color suggestions

### Theme Property Categories

The `ThemePropertyCategories` class organizes theme properties into logical groups:

- **Editor**: Background, foreground, cursor, selection
- **Terminal**: Background, foreground, ANSI colors
- **Activity Bar**: Background, foreground, icons
- **Sidebar**: Background, foreground, sections
- **Status Bar**: Background, foreground, items
- **Title Bar**: Active/inactive states
- **Tabs**: Active/inactive, hover states
- **Input**: Background, foreground, border
- **Buttons**: Primary, secondary, hover states
- **Scrollbar**: Track, thumb, hover states

### Theme Importers

#### VSCodeThemeImporter (`core/themes/importers.py`)

**Purpose**: Import VSCode-compatible themes

**Features**:
- Color mapping from VSCode to ViloxTerm
- Automatic color derivation for missing values
- Brightness adjustment algorithms
- Theme validation and sanitization

**Mapping Strategy**:
```python
VSCODE_TO_VILOX_MAP = {
    "editor.background": "editor.background",
    "terminal.background": "terminal.background",
    # ... extensive mapping dictionary
}
```

## Command System Integration

### Available Commands

- `theme.selectTheme` - Cycle through available themes
- `theme.selectVSCodeDark` - Apply VSCode Dark+ theme
- `theme.selectVSCodeLight` - Apply VSCode Light theme
- `theme.selectMonokai` - Apply Monokai theme
- `theme.createCustomTheme` - Create custom theme from current
- `theme.exportTheme` - Export current theme to file
- `theme.importTheme` - Import theme from file
- `theme.resetToDefault` - Reset to default theme
- `theme.openEditor` - Open visual theme editor
- `theme.importVSCode` - Import VSCode theme file

### Command Pattern

```python
@command(
    id="theme.selectTheme",
    title="Select Color Theme",
    category="Preferences",
    description="Change the application color theme",
    shortcut="ctrl+k ctrl+t"
)
def select_theme_command(context: CommandContext) -> CommandResult:
    theme_service = context.get_service(ThemeService)
    # Implementation...
```

## Performance Considerations

### Caching Strategy

1. **Theme Loading**: Themes cached on first load
2. **Stylesheet Generation**: Generated stylesheets cached by component
3. **Color Resolution**: Resolved color palettes cached per theme

### Optimization Features

- **Lazy Loading**: Themes loaded on demand
- **Cache Invalidation**: Smart cache clearing on theme changes
- **Signal Efficiency**: Minimal UI updates via targeted signals
- **Memory Management**: Proper cleanup of cached resources

## Error Handling

### Theme Loading Errors
- Invalid JSON format
- Missing required fields
- Color format validation failures
- Theme inheritance cycles

### Recovery Strategies
- Fallback to default theme
- Graceful degradation with warning messages
- Theme validation before application
- User notification of theme errors

## Testing Strategy

### Unit Tests
- Theme loading and validation
- Color resolution and inheritance
- Service functionality
- Command execution
- Theme property categorization
- VSCode theme importing
- Color picker functionality
- Theme preview widget

### Integration Tests
- Service interaction
- Signal propagation
- Settings persistence
- Theme switching workflows
- Theme editor workspace integration
- Import/export functionality

### GUI Tests
- Widget theme updates
- Visual regression testing
- Theme persistence across sessions
- Command palette integration
- Theme editor opening and interaction
- Color picker dialog handling
- Live preview updates
- Infinite loop prevention

## Extension Points

### Custom Themes
- User theme directory support
- Theme import/export functionality
- Theme editor capabilities
- Community theme sharing

### Widget Support
- Standardized `apply_theme()` method
- Component-specific stylesheets
- Theme-aware custom widgets
- Dynamic style updates

## Migration and Compatibility

### Version Management
- Theme format versioning
- Backward compatibility checking
- Migration scripts for theme updates
- Graceful handling of unsupported versions

### Legacy Support
- Old theme format conversion
- Setting migration from previous versions
- Fallback theme support
- User notification of changes

This architecture provides a robust, extensible foundation for theme management while maintaining clean separation of concerns and supporting both built-in and user-created themes.