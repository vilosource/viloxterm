# Keyboard Shortcut Configuration Guide

## Overview

This guide covers the keyboard shortcut configuration system that allows users to customize all keyboard shortcuts in the application through an intuitive interface.

## User Guide

### Opening the Configuration

You can open the keyboard shortcut configuration in three ways:

1. **File Menu**: File → Keyboard Shortcuts...
2. **Keyboard Shortcut**: Press `Ctrl+K`, then `Ctrl+S` (chord sequence)
3. **Command Palette**: Search for "Keyboard Shortcuts" and select "Keyboard Shortcuts..."

### Interface Overview

The configuration interface is organized into several sections:

```
┌─────────────────────────────────────────────┐
│ Search: [_______________] [×] │ Category ▼ │
├─────────────────────────────────────────────┤
│ Command          │ Current    │ New        │
│                  │ Shortcut   │ Shortcut   │
├──────────────────┼────────────┼────────────┤
│ File             │            │            │
│ ├ New Editor Tab │ Ctrl+N     │ [Ctrl+N]   │
│ ├ New Terminal   │ Ctrl+`     │ [Ctrl+`]   │
│ └ Open File      │ Ctrl+O     │ [Ctrl+O]   │
│ View             │            │            │
│ ├ Toggle Sidebar │ Ctrl+B     │ [Ctrl+B]   │
│ └ Toggle Theme   │ Ctrl+T     │ [Ctrl+T]   │
├─────────────────────────────────────────────┤
│ ⚠ Conflicts: None detected                  │
├─────────────────────────────────────────────┤
│ [Reset All] [Reset Selected] [Apply] [Cancel]│
└─────────────────────────────────────────────┘
```

### Recording Shortcuts

To change a keyboard shortcut:

1. **Click** on the shortcut field in the "New Shortcut" column
2. The field will highlight with an orange border and show "Press shortcut keys..."
3. **Press** the desired key combination (e.g., `Ctrl+Shift+N`)
4. The shortcut will be recorded automatically
5. Press **Escape** to cancel recording

#### Supported Key Combinations

- **Modifiers**: Ctrl, Alt, Shift, Meta (Windows/Cmd key)
- **Regular Keys**: A-Z, 0-9, F1-F12
- **Special Keys**: Escape, Tab, Space, Enter, Backspace, Delete, etc.
- **Arrow Keys**: Up, Down, Left, Right
- **Symbols**: Most punctuation and symbol keys

#### Examples of Valid Shortcuts

- `Ctrl+N` - Control + N
- `Alt+F4` - Alt + F4
- `Ctrl+Shift+P` - Control + Shift + P
- `F5` - Function key F5
- `Ctrl+K Ctrl+S` - Chord sequence (press Ctrl+K, release, then Ctrl+S)

### Managing Conflicts

When you assign a shortcut that's already in use:

1. **Conflict Detection**: The interface highlights conflicting commands in red
2. **Warning Panel**: Shows which commands are conflicting
3. **Resolution Options**:
   - Remove the shortcut from the other command
   - Choose a different shortcut
   - Force override (apply anyway with a warning)

### Search and Filtering

- **Search Box**: Type to filter commands by name or description
- **Category Filter**: Select a specific category to show only those commands
- **Real-time Filtering**: Results update as you type

### Reset Options

- **Reset All**: Restores all shortcuts to their default values
- **Reset Selected**: Restores only the selected shortcuts to defaults
- **Individual Reset**: Click on a shortcut and clear it to use the default

### Applying Changes

- **Apply**: Saves all changes and closes the configuration
- **Cancel**: Discards all changes and closes the configuration
- **Auto-save**: Changes are applied immediately when you click Apply

## Developer Guide

### Architecture

The shortcut configuration system consists of several key components:

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│ ShortcutConfigApp   │    │ SettingsService      │    │ KeyboardService     │
│ Widget              │◄──►│                      │◄──►│                     │
│                     │    │ - get_shortcuts()    │    │ - register()        │
│ - UI Management     │    │ - set_shortcut()     │    │ - unregister()      │
│ - Conflict Detection│    │ - reset_shortcuts()  │    │ - find_conflicts()  │
│ - Recording         │    │                      │    │                     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
           │                           │                           │
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│ Command Registry    │    │ QSettings            │    │ Event Handling      │
│                     │    │ (Persistent Storage) │    │ (Runtime Shortcuts) │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

### Key Classes

#### ShortcutConfigAppWidget

**Location**: `ui/widgets/shortcut_config_app_widget.py`

Main configuration interface that extends `AppWidget`:

```python
class ShortcutConfigAppWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.SETTINGS, parent)
        # Initialize UI and load shortcuts

    def load_shortcuts(self):
        # Load all commands and current shortcuts

    def on_shortcut_changed(self, command_id: str, new_shortcut: str):
        # Handle shortcut modifications

    def check_conflicts(self):
        # Detect and highlight conflicts

    def apply_changes(self):
        # Save changes to settings and keyboard service
```

#### ShortcutRecorder

**Location**: `ui/widgets/shortcut_config_app_widget.py`

Custom widget for recording keyboard shortcuts:

```python
class ShortcutRecorder(QLineEdit):
    shortcut_recorded = Signal(str)

    def start_recording(self):
        # Enter recording mode with visual feedback

    def keyPressEvent(self, event):
        # Capture and format key combinations

    def format_shortcut(self) -> str:
        # Normalize shortcut format
```

#### ShortcutItem

Data model for shortcut configuration:

```python
@dataclass
class ShortcutItem:
    command_id: str
    title: str
    category: str
    description: str
    default_shortcut: str
    current_shortcut: str
    new_shortcut: Optional[str] = None
    has_conflict: bool = False
    conflicting_commands: List[str] = None
```

### Integration Points

#### Command Registration

Add the configuration command to any command file:

```python
@command(
    id="settings.openKeyboardShortcuts",
    title="Keyboard Shortcuts...",
    category="Settings",
    description="Open keyboard shortcuts configuration",
    shortcut="ctrl+k ctrl+s",
    icon="keyboard"
)
def open_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    # Create and open shortcut configuration widget
```

#### Widget Factory Registration

Register the widget factory for the SETTINGS widget type:

```python
from ui.widgets.widget_registry import WidgetType, widget_registry
from ui.widgets.shortcut_config_app_widget import ShortcutConfigAppWidget

def create_shortcut_config_widget(widget_id: str) -> ShortcutConfigAppWidget:
    return ShortcutConfigAppWidget(widget_id)

widget_registry.register_factory(WidgetType.SETTINGS, create_shortcut_config_widget)
```

#### Settings Integration

The system uses the existing SettingsService methods:

```python
# Get all shortcuts
shortcuts = settings_service.get_keyboard_shortcuts()

# Set individual shortcut
settings_service.set_keyboard_shortcut(command_id, new_shortcut)

# Reset all shortcuts
settings_service.reset_keyboard_shortcuts()
```

#### Keyboard Service Integration

Updates are applied to the KeyboardService immediately:

```python
# Unregister old shortcut
keyboard_service.unregister_shortcut(f"command.{command_id}")

# Register new shortcut
keyboard_service.register_shortcut_from_string(
    shortcut_id=f"command.{command_id}",
    sequence_str=new_shortcut,
    command_id=command_id,
    description=description,
    source="user",
    priority=100  # User shortcuts have higher priority
)
```

### Extending the System

#### Adding New Shortcut Types

To support additional shortcut types (e.g., context-specific shortcuts):

1. **Extend ShortcutItem**: Add context fields
2. **Update UI**: Add context filters to the interface
3. **Modify Storage**: Update settings schema
4. **Enhance Service**: Add context-aware registration

#### Custom Validation

Add custom validation for specific shortcut patterns:

```python
def validate_shortcut(shortcut: str, command_id: str) -> bool:
    # Check for reserved shortcuts
    if shortcut in RESERVED_SHORTCUTS:
        return False

    # Check for system-specific restrictions
    if sys.platform == "darwin" and shortcut.startswith("cmd+"):
        # macOS-specific validation
        pass

    return True
```

#### Conflict Resolution Strategies

Implement different conflict resolution strategies:

```python
class ConflictResolver:
    def resolve_conflict(self, shortcut: str, conflicting_commands: List[str]) -> str:
        # Auto-suggest alternative shortcuts
        # Prioritize by command category
        # Allow user to choose resolution strategy
        pass
```

### Performance Considerations

#### Efficient Loading

- Load shortcuts on-demand rather than at startup
- Cache shortcut data to avoid repeated registry queries
- Use lazy loading for large command sets

#### Memory Management

- Clear unused shortcut data when configuration closes
- Avoid keeping references to large UI trees
- Use weak references for signal connections

#### Update Optimization

- Batch shortcut updates to reduce settings writes
- Only re-register changed shortcuts, not all shortcuts
- Defer UI updates during bulk operations

### Testing

#### Unit Tests

Test individual components:

```python
def test_shortcut_recorder():
    recorder = ShortcutRecorder()
    # Test recording functionality

def test_conflict_detection():
    widget = ShortcutConfigAppWidget("test")
    # Test conflict detection logic

def test_settings_integration():
    # Test settings persistence
```

#### Integration Tests

Test the complete workflow:

```python
def test_shortcut_configuration_workflow():
    # Open configuration
    # Change shortcuts
    # Apply changes
    # Verify shortcuts work
```

#### GUI Tests

Test user interactions:

```python
def test_shortcut_recording_ui(qtbot):
    widget = ShortcutConfigAppWidget("test")
    qtbot.addWidget(widget)

    # Test recording interaction
    recorder = widget.find_recorder_for_command("test.command")
    qtbot.mouseClick(recorder, Qt.LeftButton)
    qtbot.keyPress(recorder, Qt.Key_N, Qt.ControlModifier)

    assert recorder.text() == "ctrl+n"
```

## Best Practices

### For Users

1. **Test shortcuts**: Always test new shortcuts after applying them
2. **Avoid conflicts**: Check for conflicts before applying changes
3. **Use consistent patterns**: Follow existing shortcut conventions
4. **Document changes**: Keep track of custom shortcuts for team collaboration

### For Developers

1. **Follow patterns**: Use the established command pattern for new shortcuts
2. **Provide defaults**: Always define sensible default shortcuts
3. **Consider conflicts**: Check for potential conflicts when adding new commands
4. **Test thoroughly**: Verify shortcuts work in all contexts (terminal, editor, etc.)

## Troubleshooting

### Common Issues

#### Shortcut Not Working

1. Check if shortcut is registered in settings
2. Verify command exists in registry
3. Check for conflicts with other shortcuts
4. Ensure keyboard service is initialized

#### Recording Issues

1. Some key combinations may be reserved by the OS
2. Function keys might be captured by hardware
3. Certain modifiers may not work in all contexts

#### Persistence Problems

1. Check QSettings file permissions
2. Verify settings service initialization
3. Ensure proper cleanup on application exit

### Debug Tools

Enable logging to diagnose issues:

```python
logging.getLogger("core.keyboard").setLevel(logging.DEBUG)
logging.getLogger("core.settings").setLevel(logging.DEBUG)
```

Use the existing keyboard testing commands:

- `settings.showKeyboardShortcuts` - Display current shortcuts
- `settings.resetKeyboardShortcuts` - Reset to defaults

## Future Enhancements

### Planned Features

1. **Import/Export**: Share shortcut configurations between installations
2. **Presets**: Pre-defined shortcut schemes (VSCode, Vim, Emacs)
3. **Context-aware shortcuts**: Different shortcuts based on active widget
4. **Macro recording**: Record and replay key sequences
5. **Visual shortcut cheat sheet**: Generate printable reference cards

### Advanced Use Cases

1. **Team Synchronization**: Sync shortcuts across team members
2. **Accessibility**: Support for alternative input methods
3. **Gamification**: Achievement system for shortcut mastery
4. **Analytics**: Track shortcut usage patterns

---

This configuration system provides a foundation for powerful keyboard customization while maintaining the application's architectural principles and ensuring a smooth user experience.