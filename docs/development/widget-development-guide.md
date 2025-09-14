# Widget Development Guide

## Overview

This guide explains how to create new widgets for ViloxTerm using the AppWidgetManager system. The AppWidgetManager provides a centralized registry for all widgets with rich metadata support and plugin-ready architecture.

## Quick Start

### 1. Create Widget Class

Create your widget class extending `AppWidget`:

```python
from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType

class MyCustomWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        self.setup_ui()

    def setup_ui(self):
        # Initialize your widget UI
        pass

    def cleanup(self):
        # Clean up resources
        super().cleanup()
```

### 2. Register Widget

Add registration to `core/app_widget_registry.py`:

```python
from core.app_widget_metadata import AppWidgetMetadata, WidgetCategory

manager.register_widget(AppWidgetMetadata(
    widget_id="com.mycompany.mywidget",
    widget_type=WidgetType.CUSTOM,
    display_name="My Custom Widget",
    description="A custom widget for specific functionality",
    icon="custom-icon",
    category=WidgetCategory.TOOLS,
    widget_class=MyCustomWidget,
    open_command="mywidget.open",
    provides_capabilities=["custom_feature"]
))
```

### 3. Create Command

Add a command to open your widget:

```python
from core.commands.decorators import command
from core.commands.base import CommandContext, CommandResult

@command(
    id="mywidget.open",
    title="Open My Widget",
    category="Tools",
    description="Opens my custom widget in a new tab"
)
def open_my_widget_command(context: CommandContext) -> CommandResult:
    workspace_service = context.get_service(WorkspaceService)
    workspace_service.add_app_widget_tab(
        WidgetType.CUSTOM,
        tab_name="My Widget"
    )
    return CommandResult(success=True)
```

## Widget Architecture

### AppWidget Base Class

All widgets must extend the `AppWidget` base class:

```python
class AppWidget(QWidget):
    # Signals
    action_requested = Signal(str, dict)  # action_type, params
    state_changed = Signal(dict)          # state_data
    focus_requested = Signal()            # Request focus

    def __init__(self, widget_id: str, widget_type: WidgetType, parent=None):
        super().__init__(parent)
        self.widget_id = widget_id
        self.widget_type = widget_type
        self.leaf_node = None  # Set by the model

    def cleanup(self):
        """Override to clean up resources"""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Override to provide serializable state"""
        return {}

    def restore_state(self, state: Dict[str, Any]):
        """Override to restore from serialized state"""
        pass
```

### Key Principles

1. **Self-Contained**: Widgets manage their own UI and state
2. **Signal-Based Communication**: Use signals to communicate with parent components
3. **Stateless Model**: Don't store references to model/view components
4. **Resource Management**: Always clean up in the `cleanup()` method
5. **Serializable State**: Implement state save/restore for persistence

## Widget Metadata

### AppWidgetMetadata Fields

```python
@dataclass
class AppWidgetMetadata:
    # Required fields
    widget_id: str                      # Unique identifier
    widget_type: WidgetType            # Enum type for compatibility
    display_name: str                  # Human-readable name
    description: str                   # Widget description
    icon: str                         # Icon name
    category: WidgetCategory          # Category for organization
    widget_class: Type['AppWidget']   # Widget class

    # Optional fields
    factory: Optional[Callable] = None           # Custom factory function
    open_command: Optional[str] = None           # Command to open widget
    provides_capabilities: List[str] = []        # Capabilities provided
    requires_services: List[str] = []           # Required services
    supported_file_types: List[str] = []        # File types handled

    # Behavior flags
    singleton: bool = False                     # Only one instance
    show_in_menu: bool = True                  # Show in pane menus
    preserve_context_menu: bool = False        # Keep widget's context menu
    can_suspend: bool = True                   # Can be suspended when hidden

    # Layout hints
    min_width: int = 150                       # Minimum width
    min_height: int = 100                      # Minimum height

    # Plugin support
    source: str = "builtin"                    # Source identifier
    version: str = "1.0.0"                    # Version string
```

### Widget Categories

Choose the appropriate category:

```python
class WidgetCategory(Enum):
    EDITOR = "editor"       # Text/code editors
    TERMINAL = "terminal"   # Terminal emulators
    VIEWER = "viewer"       # File/content viewers
    TOOLS = "tools"         # Utility tools
    SYSTEM = "system"       # System widgets
```

## Advanced Features

### Custom Factory Functions

For complex widget creation, provide a factory function:

```python
def create_advanced_widget(widget_id: str) -> MyAdvancedWidget:
    # Complex initialization logic
    service = get_required_service()
    widget = MyAdvancedWidget(widget_id, service)
    widget.configure_advanced_features()
    return widget

# Register with factory
manager.register_widget(AppWidgetMetadata(
    widget_id="com.example.advanced",
    # ... other fields ...
    widget_class=MyAdvancedWidget,
    factory=create_advanced_widget
))
```

### Capability System

Declare capabilities your widget provides:

```python
manager.register_widget(AppWidgetMetadata(
    # ... other fields ...
    provides_capabilities=[
        "text_editing",
        "syntax_highlighting",
        "code_completion",
        "git_integration"
    ]
))
```

Other components can discover widgets by capability:

```python
editor_widgets = manager.get_widgets_with_capability("text_editing")
```

### Service Dependencies

Declare required services:

```python
manager.register_widget(AppWidgetMetadata(
    # ... other fields ...
    requires_services=[
        "file_system_service",
        "git_service",
        "theme_service"
    ]
))
```

### File Type Support

Declare supported file types:

```python
manager.register_widget(AppWidgetMetadata(
    # ... other fields ...
    supported_file_types=["py", "js", "ts", "json", "yml"]
))
```

Discover widgets for specific file types:

```python
python_editors = manager.get_widgets_for_file_type("py")
```

## Widget Lifecycle

### Creation Flow
1. User triggers command (menu, shortcut, etc.)
2. Command calls `workspace_service.add_app_widget_tab()`
3. `SplitPaneModel.create_app_widget()` called
4. `AppWidgetManager.create_widget_by_type()` creates instance
5. Widget added to UI hierarchy

### State Management
```python
class MyWidget(AppWidget):
    def get_state(self) -> Dict[str, Any]:
        return {
            "current_file": self.current_file,
            "scroll_position": self.get_scroll_position(),
            "settings": self.get_settings()
        }

    def restore_state(self, state: Dict[str, Any]):
        if "current_file" in state:
            self.load_file(state["current_file"])
        if "scroll_position" in state:
            self.set_scroll_position(state["scroll_position"])
        if "settings" in state:
            self.apply_settings(state["settings"])
```

### Cleanup
```python
class MyWidget(AppWidget):
    def cleanup(self):
        # Clean up timers
        if hasattr(self, 'timer'):
            self.timer.stop()

        # Close files
        if hasattr(self, 'file_handle'):
            self.file_handle.close()

        # Disconnect signals
        self.disconnect_all_signals()

        # Call parent cleanup
        super().cleanup()
```

## UI Integration

### Menu Integration

Widgets automatically appear in pane menus if `show_in_menu=True`:

```python
# Widgets are automatically grouped by category
# Menu structure:
# Editor
#   ├── Text Editor
#   └── Code Editor
# Tools
#   ├── Theme Editor
#   └── My Custom Tool
```

### Context Menus

Control context menu behavior:

```python
manager.register_widget(AppWidgetMetadata(
    # ... other fields ...
    preserve_context_menu=True  # Keep widget's context menu
))
```

### Header Configuration

Configure the pane header:

```python
class MyWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        # Header will be created automatically
        # Title comes from display_name in metadata
```

## Testing

### Unit Testing

Test your widget in isolation:

```python
import pytest
from PySide6.QtWidgets import QApplication
from mywidget import MyCustomWidget

@pytest.fixture
def qapp():
    return QApplication.instance() or QApplication([])

def test_widget_creation(qapp):
    widget = MyCustomWidget("test_widget_id")
    assert widget.widget_id == "test_widget_id"
    assert widget.widget_type == WidgetType.CUSTOM

def test_widget_cleanup(qapp):
    widget = MyCustomWidget("test_widget_id")
    # Setup some resources
    widget.setup_test_resources()

    # Cleanup should not raise exceptions
    widget.cleanup()
```

### GUI Integration Testing

Test UI integration:

```python
def test_widget_in_pane(qtbot, qapp):
    from ui.widgets.split_pane_model import SplitPaneModel
    from core.app_widget_manager import AppWidgetManager

    # Register test widget
    manager = AppWidgetManager.get_instance()
    # ... register widget ...

    # Create through model
    model = SplitPaneModel(WidgetType.PLACEHOLDER)
    widget = model.create_app_widget(WidgetType.CUSTOM, "test_id")

    assert widget is not None
    assert isinstance(widget, MyCustomWidget)
```

## Common Patterns

### Settings Widget Pattern

For configuration widgets:

```python
class SettingsWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.SETTINGS, parent)
        self.settings_service = ServiceLocator.get_service(SettingsService)
        self.setup_ui()

    def setup_ui(self):
        # Create settings form
        pass

    def apply_settings(self):
        # Apply changes to settings service
        pass
```

### File Viewer Pattern

For file content widgets:

```python
class FileViewerWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.TEXT_EDITOR, parent)
        self.current_file = None
        self.setup_ui()

    def load_file(self, file_path: str):
        # Load and display file
        self.current_file = file_path
        self.state_changed.emit({"current_file": file_path})
```

### Tool Widget Pattern

For utility tools:

```python
class ToolWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        self.setup_tool_ui()

    def execute_tool_action(self):
        # Perform tool function
        self.action_requested.emit("tool_completed", {"result": "success"})
```

## Best Practices

### Naming Conventions
- **Widget IDs**: Use reverse domain notation: `com.company.widget`
- **Widget Classes**: End with `Widget` or `AppWidget`
- **Commands**: Use namespace: `mywidget.open`, `mywidget.save`

### Performance
- **Lazy Loading**: Don't load heavy resources until needed
- **Efficient Updates**: Use signals to update UI efficiently
- **Memory Management**: Always clean up in `cleanup()`

### User Experience
- **Consistent UI**: Follow application UI patterns
- **Keyboard Shortcuts**: Support standard shortcuts
- **Context Menus**: Provide relevant actions
- **Status Updates**: Use signals to communicate status

### Error Handling
- **Graceful Degradation**: Handle missing services/resources
- **User Feedback**: Show meaningful error messages
- **Logging**: Use structured logging for debugging

## Examples

### Complete Example: Log Viewer Widget

```python
# log_viewer_widget.py
import logging
from PySide6.QtWidgets import QVBoxLayout, QTextEdit, QPushButton
from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType

logger = logging.getLogger(__name__)

class LogViewerWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        self.log_file = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Text area for log content
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        layout.addWidget(self.refresh_btn)

    def load_log_file(self, file_path: str):
        self.log_file = file_path
        self.refresh_logs()
        self.state_changed.emit({"log_file": file_path})

    def refresh_logs(self):
        if self.log_file:
            try:
                with open(self.log_file, 'r') as f:
                    content = f.read()
                self.text_edit.setPlainText(content)
            except Exception as e:
                logger.error(f"Failed to load log file: {e}")
                self.text_edit.setPlainText(f"Error: {e}")

    def get_state(self) -> dict:
        return {"log_file": self.log_file}

    def restore_state(self, state: dict):
        if "log_file" in state:
            self.load_log_file(state["log_file"])

    def cleanup(self):
        # Disconnect signals
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.clicked.disconnect()
        super().cleanup()

# Registration
from core.app_widget_manager import AppWidgetManager
from core.app_widget_metadata import AppWidgetMetadata, WidgetCategory

def register_log_viewer():
    manager = AppWidgetManager.get_instance()
    manager.register_widget(AppWidgetMetadata(
        widget_id="com.viloapp.logviewer",
        widget_type=WidgetType.CUSTOM,
        display_name="Log Viewer",
        description="View and monitor log files",
        icon="file-text",
        category=WidgetCategory.TOOLS,
        widget_class=LogViewerWidget,
        open_command="logviewer.open",
        provides_capabilities=["log_viewing", "file_monitoring"],
        supported_file_types=["log", "txt"],
        min_width=400,
        min_height=300
    ))

# Command
from core.commands.decorators import command
from core.commands.base import CommandContext, CommandResult

@command(
    id="logviewer.open",
    title="Open Log Viewer",
    category="Tools",
    description="Opens the log viewer widget"
)
def open_log_viewer_command(context: CommandContext) -> CommandResult:
    workspace_service = context.get_service(WorkspaceService)
    workspace_service.add_app_widget_tab(
        WidgetType.CUSTOM,
        tab_name="Log Viewer"
    )
    return CommandResult(success=True)
```

## Migration from Legacy System

### Old System
```python
# Old way - hardcoded in multiple places
def create_my_widget():
    return MyWidget()

# Hardcoded in pane_header.py
WIDGET_DISPLAY_NAMES = {
    WidgetType.CUSTOM: "My Widget"
}

# Manual factory registration
widget_registry.register_factory(WidgetType.CUSTOM, create_my_widget)
```

### New System
```python
# New way - centralized registration
manager.register_widget(AppWidgetMetadata(
    widget_id="com.company.mywidget",
    widget_type=WidgetType.CUSTOM,
    display_name="My Widget",
    # ... complete metadata
))
```

## Troubleshooting

### Common Issues

1. **Widget not appearing in menu**
   - Check `show_in_menu=True`
   - Verify registration is called at startup

2. **Widget creation fails**
   - Check constructor signature matches AppWidget
   - Verify all dependencies are available
   - Check error logs for exceptions

3. **State not persisting**
   - Implement `get_state()` and `restore_state()`
   - Ensure state is JSON-serializable

4. **Memory leaks**
   - Implement proper `cleanup()` method
   - Disconnect all signals
   - Close file handles and resources

### Debugging

Enable debug logging to see widget lifecycle:

```python
import logging
logging.getLogger('core.app_widget_manager').setLevel(logging.DEBUG)
logging.getLogger('ui.widgets.split_pane_model').setLevel(logging.DEBUG)
```

## Conclusion

The AppWidgetManager system provides a powerful and flexible foundation for widget development. By following this guide, you can create professional, well-integrated widgets that seamlessly fit into the ViloxTerm ecosystem while preparing for future plugin support.