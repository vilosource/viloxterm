# Application Defaults System - Implementation Plan

## Overview

Implement a comprehensive application defaults system that allows users to configure default behaviors throughout the application, similar to VSCode's settings system.

## Core Requirements

- **Global Settings Only** - No workspace-specific overrides, single source of truth
- **Invalid Settings Handling** - Automatic validation and fallback to safe defaults
- **Big Bang Migration** - Replace existing commands in one shot, no gradual migration
- **Import Existing Preferences** - One-time migration from current QSettings

## Architecture

### Settings Hierarchy
```
User Settings (QSettings) → App Defaults → Hard-coded Fallbacks
```

Every setting access goes through validation to ensure the application never crashes due to invalid configuration.

## Components

### 1. Core Defaults Module (`core/settings/app_defaults.py`)

**Categories:**
- **Workspace Defaults**
  - `default_new_tab_widget`: Widget type for new tabs (terminal, editor, etc.)
  - `tab_auto_naming_pattern`: Pattern for auto-generated tab names
  - `max_tabs`: Maximum number of tabs (0 = unlimited)
  - `close_last_tab_behavior`: Action when closing last tab
  - `restore_tabs_on_startup`: Restore tabs from last session

- **Pane Management**
  - `default_split_direction`: horizontal or vertical
  - `default_split_ratio`: Split ratio (0.1 to 0.9)
  - `minimum_pane_width/height`: Minimum dimensions
  - `focus_new_pane_on_split`: Focus behavior after split
  - `default_pane_widget`: Widget type for new panes

- **Widget Defaults**
  - Terminal: shell, starting directory, environment
  - Editor: file type, encoding, content template
  - Theme Editor: preview settings
  - Explorer: view options, sorting

- **UI Behavior**
  - Window: default size, position, startup state
  - Sidebar: visibility, width, position
  - Status bar: visibility, content

- **User Experience**
  - Confirmations: exit, close, reload behaviors
  - Notifications: position, duration, sound
  - Performance: animation speed, hardware acceleration

### 2. Validation System

```python
class AppDefaultsValidator:
    @staticmethod
    def validate_and_sanitize(key: str, value: Any) -> Tuple[bool, Any]:
        """
        Validates a setting value and returns sanitized version.
        Returns: (is_valid, safe_value)
        """
        # Specific validators for each setting
        # Always returns a safe, usable value
```

**Fallback Chain:**
1. Try to get user setting
2. Validate the value
3. If invalid, log warning and use app default
4. If app default missing, use hard-coded fallback
5. Never crash, always return something usable

### 3. Settings AppWidget (`ui/widgets/settings_app_widget.py`)

**Structure:**
```
Settings AppWidget
├── General Tab
│   ├── Workspace Defaults
│   │   ├── Default new tab widget: [Dropdown]
│   │   ├── Tab naming pattern: [Text field]
│   │   ├── Max tabs: [SpinBox]
│   │   └── When closing last tab: [Radio buttons]
│   ├── Pane Management
│   │   ├── Default split: [H/V toggle]
│   │   ├── Split ratio: [Slider]
│   │   └── Focus new pane: [Checkbox]
│   └── Startup
│       ├── Restore tabs: [Checkbox]
│       └── Window state: [Radio buttons]
├── Appearance Tab (incorporates Theme Editor)
├── Keyboard Tab (incorporates Shortcuts widget)
├── Terminal Tab
│   ├── Default shell: [Dropdown]
│   └── Starting directory: [Dropdown]
└── Advanced Tab
    ├── Show confirmations: [Checkbox]
    └── [Reset] [Export] [Import] buttons
```

**Registration:**
- Widget ID: `com.viloapp.settings`
- Widget Type: `SETTINGS`
- Access: Activity Bar, Command Palette, Ctrl+,

### 4. Command Updates

**Remove Old Commands:**
- `file.newTerminalTab` (Ctrl+N)
- `file.newEditorTab` (Ctrl+Shift+N)

**Add New Unified Commands:**
```python
@command(
    id="workspace.newTab",
    title="New Tab",
    category="Workspace",
    shortcut="ctrl+t"
)
def new_tab_command(context: CommandContext) -> CommandResult:
    widget_type = get_app_default("workspace.default_new_tab_widget", "terminal")
    return workspace_service.create_tab(widget_type)

@command(
    id="workspace.newTabWithType",
    title="New Tab (Choose Type)...",
    category="Workspace",
    shortcut="ctrl+shift+t"
)
def new_tab_with_type_command(context: CommandContext) -> CommandResult:
    # Shows quick pick to choose widget type
```

### 5. Migration System

```python
def import_existing_preferences():
    """One-time import of existing user preferences to new system."""

    migration_map = {
        # UI settings
        "UI/ShowSidebar": "ui_behavior.sidebar_visible_on_start",
        "UI/ShowActivityBar": "ui_behavior.show_activity_bar",
        "UI/SidebarWidth": "ui_behavior.default_sidebar_width",
        "UI/FramelessMode": "ui_behavior.frameless_mode",

        # Theme settings
        "Theme/Current": "appearance.theme",
        "Theme/FontFamily": "appearance.font_family",
        "Theme/FontSize": "appearance.font_size",

        # Workspace settings
        "Workspace/RestoreOnStartup": "workspace.restore_tabs_on_startup",
    }

    # Validate and migrate each setting
    # Mark migration complete
```

## Implementation Steps

1. **Create app_defaults module**
   - Define all default values
   - Implement validation system
   - Create getter functions with fallbacks

2. **Create SettingsAppWidget**
   - Build tabbed interface
   - Connect to settings service
   - Implement live preview where applicable

3. **Update Command System**
   - Remove old specific commands
   - Add new unified commands
   - Update keyboard shortcuts

4. **Implement Migration**
   - Read existing QSettings
   - Map to new structure
   - Run on first launch after update

5. **Update Services**
   - WorkspaceService to use defaults
   - TerminalService to use defaults
   - EditorService to use defaults

6. **Testing**
   - Unit tests for validation
   - Integration tests for settings UI
   - Migration tests with various configs

## Usage Examples

### Creating a New Tab
```python
# User presses Ctrl+T
# System checks default_new_tab_widget setting
# If set to "terminal", creates terminal tab
# If set to "editor", creates editor tab
# If invalid/missing, falls back to "terminal"
```

### Accessing Settings
```python
from core.settings.app_defaults import get_app_default

widget_type = get_app_default(
    "workspace.default_new_tab_widget",
    fallback="terminal",
    validator=lambda x: x in valid_widget_types
)
```

### Settings UI Access
- Command Palette: "Open Settings" (Ctrl+,)
- Activity Bar: Settings icon
- Menu: File → Preferences → Settings

## Benefits

1. **User Control** - Full customization of application behavior
2. **Safety** - Robust validation prevents crashes
3. **Consistency** - Single source of truth for configuration
4. **Discoverability** - Visual settings UI with search
5. **Power Users** - Command palette integration
6. **Clean Migration** - Automatic import of existing preferences

## Success Criteria

- [ ] All settings accessible through UI
- [ ] Invalid settings never crash application
- [ ] Existing user preferences preserved
- [ ] New tab command respects user preference
- [ ] Settings changes apply immediately
- [ ] Export/import settings working
- [ ] Documentation updated

## Future Enhancements

- Settings sync across devices
- Settings profiles (work, personal, etc.)
- Settings search/filter
- Settings history/undo
- Context-aware defaults