# Application Defaults Architecture

## Overview

The Application Defaults system provides a centralized, validated configuration management system for ViloxTerm. It replaces scattered settings throughout the codebase with a unified approach that ensures type safety, validation, and fallback chains to prevent application crashes from invalid configurations.

## Core Components

### 1. AppDefaults Manager

The `AppDefaults` class (`core/settings/app_defaults.py`) is the central manager for all application settings:

```python
class AppDefaults:
    """Application defaults manager with validation and fallback support"""

    def get(self, key: str, fallback: Any = None) -> Any
    def set(self, key: str, value: Any) -> bool
    def reset(self, key: str) -> None
    def reset_all(self) -> None
    def export_settings(self) -> Dict[str, Any]
    def import_settings(self, settings: Dict[str, Any]) -> int
    def migrate_legacy_settings(self) -> int
```

### 2. Validation System

The `AppDefaultsValidator` provides type-safe validation for all settings:

```python
class AppDefaultsValidator:
    @staticmethod
    def validate_and_sanitize(key: str, value: Any) -> Tuple[bool, Any]:
        """Validates a setting value and returns sanitized version"""
```

### 3. Settings Categories

Settings are organized into logical categories:

- **Workspace Defaults**: Tab management, naming patterns, close behaviors
- **Pane Management**: Split directions, ratios, focus behavior
- **Widget Defaults**: Terminal, editor, theme editor specific settings
- **UI Behavior**: Window management, sidebar, status bar
- **User Experience**: Confirmations, notifications, animations

## Fallback Chain

Every setting access follows a robust fallback chain to ensure the application never crashes:

```
User Setting (QSettings)
    ↓ (if invalid or missing)
App Default (APP_DEFAULTS)
    ↓ (if missing)
Hard-coded Fallback (HARD_CODED_FALLBACKS)
    ↓ (last resort)
Safe Default Value
```

### Example Flow

```python
# User requests default widget type
get_app_default("workspace.default_new_tab_widget")
    ↓
1. Check QSettings: "app_defaults/workspace.default_new_tab_widget"
2. Validate value: is it in ["terminal", "editor", "theme_editor", ...]?
3. If invalid: log warning, use APP_DEFAULTS["workspace.default_new_tab_widget"]
4. If missing: use HARD_CODED_FALLBACKS["workspace.default_new_tab_widget"]
5. Return: "terminal" (guaranteed valid value)
```

## Key Settings

### Workspace Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `workspace.default_new_tab_widget` | string | "terminal" | Widget type for new tabs |
| `workspace.tab_auto_naming_pattern` | string | "{type} {index}" | Pattern for auto-generated tab names |
| `workspace.max_tabs` | int | 20 | Maximum number of tabs (0 = unlimited) |
| `workspace.close_last_tab_behavior` | string | "create_default" | Action when closing last tab |
| `workspace.restore_tabs_on_startup` | bool | true | Restore tabs from last session |

### Pane Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `pane.default_split_direction` | string | "horizontal" | Default split orientation |
| `pane.default_split_ratio` | float | 0.5 | Split ratio (0.1 to 0.9) |
| `pane.minimum_width` | int | 200 | Minimum pane width in pixels |
| `pane.focus_new_on_split` | bool | true | Focus new pane after split |

### UI Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ui.default_window_width` | int | 1200 | Default window width |
| `ui.default_window_height` | int | 800 | Default window height |
| `ui.sidebar_visible_on_start` | bool | true | Show sidebar on startup |
| `ui.show_status_bar` | bool | true | Show status bar |

## Settings Widget Integration

The Settings widget (`ui/widgets/settings_app_widget.py`) provides a comprehensive UI for managing all application defaults:

### Widget Structure

```
SettingsAppWidget
├── General Tab
│   ├── Workspace Defaults
│   ├── Pane Management
│   └── Startup Settings
├── Appearance Tab (Theme Editor)
├── Keyboard Tab (Shortcut Config)
├── Terminal Tab
└── Advanced Tab
    ├── Confirmations
    └── Import/Export/Reset
```

### Access Points

1. **File Menu**: File → Preferences → Settings (Ctrl+,)
2. **Command Palette**: "Open Settings"
3. **Keyboard Shortcut**: Ctrl+,
4. **Programmatic**: `execute_command("settings.openSettings")`

## Command Integration

### Unified New Tab Command

The system introduces a unified `workspace.newTab` command that respects user defaults:

```python
@command(id="workspace.newTab", shortcut="ctrl+t")
def new_tab_command(context: CommandContext) -> CommandResult:
    widget_type = get_default_widget_type()  # Uses app defaults
    return workspace_service.create_tab(widget_type)
```

This replaces the previous separate commands:
- ~~`file.newTerminalTab`~~ → `workspace.newTab` with default
- ~~`file.newEditorTab`~~ → `workspace.newTab` with default

## Migration System

The system includes automatic migration from legacy settings:

```python
def migrate_legacy_settings() -> int:
    """One-time migration from old QSettings keys to new system"""

    migration_map = {
        "UI/ShowSidebar": "ui.sidebar_visible_on_start",
        "Theme/Current": "appearance.theme",
        "Workspace/RestoreOnStartup": "workspace.restore_tabs_on_startup",
        # ... more mappings
    }
```

Migration runs automatically on first access to `AppDefaults`.

## Validation Examples

### Widget Type Validation

```python
def validate_widget_type(value: str) -> Tuple[bool, str]:
    valid_types = ["terminal", "editor", "theme_editor", "explorer"]
    if value in valid_types:
        return (True, value)
    logger.warning(f"Invalid widget type '{value}', falling back to 'terminal'")
    return (False, "terminal")
```

### Numeric Range Validation

```python
def validate_split_ratio(value: Any) -> Tuple[bool, float]:
    try:
        ratio = float(value)
        if 0.1 <= ratio <= 0.9:
            return (True, ratio)
        return (False, 0.5)  # Fallback to center
    except (TypeError, ValueError):
        return (False, 0.5)
```

## Service Integration

Services use app defaults for their operations:

```python
class WorkspaceService(Service):
    def split_active_pane(self, orientation: Optional[str] = None):
        # Use default if not specified
        if orientation is None:
            orientation = get_default_split_direction()

        # Get split ratio from settings
        split_ratio = get_default_split_ratio()
        # ... perform split
```

## Benefits

### For Users
- **Customizable Workflow**: Configure defaults to match preferences
- **Safe Settings**: Invalid settings never crash the application
- **Import/Export**: Share configurations across installations
- **Visual Configuration**: Settings widget for easy management

### For Developers
- **Type Safety**: All settings validated before use
- **Single Source**: Centralized configuration management
- **Easy Extension**: Add new settings with validation
- **Debugging**: Comprehensive logging of invalid settings

## Testing

The system includes comprehensive testing:

1. **Validation Tests**: Every validator function tested
2. **Fallback Tests**: Fallback chains verified
3. **Migration Tests**: Legacy setting migration
4. **Integration Tests**: Service integration verified

## Future Enhancements

Potential future improvements:

1. **Settings Profiles**: Multiple configuration profiles
2. **Cloud Sync**: Synchronize settings across devices
3. **Settings Search**: Find settings quickly
4. **Settings History**: Undo/redo for settings changes
5. **Context-aware Defaults**: Per-project settings overrides