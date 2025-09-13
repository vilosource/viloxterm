# AppWidget Development Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Step-by-Step Implementation](#step-by-step-implementation)
4. [Theme Integration](#theme-integration)
5. [Widget Registry System](#widget-registry-system)
6. [Common Patterns](#common-patterns)
7. [Pitfalls to Avoid](#pitfalls-to-avoid)
8. [Complete Example](#complete-example)
9. [Testing Your AppWidget](#testing-your-appwidget)
10. [Troubleshooting](#troubleshooting)

## Introduction

AppWidgets are the fundamental content components in ViloxTerm's split-pane architecture. They represent the actual content that users interact with - terminals, editors, configuration panels, and more. This guide provides comprehensive instructions for implementing new AppWidgets with proper theming and integration.

> **Prerequisites**: Before diving into AppWidget development, it's recommended to understand the overall architecture:
> - [Command and Navigation System](../architecture/COMMAND_AND_NAVIGATION_SYSTEM.md) - Command pattern implementation
> - [Theming and Styling Architecture](../architecture/THEMING_AND_STYLING.md) - VSCode theme system
> - [Keyboard Shortcut Architecture](../architecture/KEYBOARD_SHORTCUT_ARCHITECTURE.md) - Shortcut management system
> - [Widget Registry Architecture](../pending/UNIFIED_TAB_REGISTRY_ARCHITECTURE.md) - Widget registration patterns

### What is an AppWidget?

An AppWidget is a specialized QWidget that:
- Extends the `AppWidget` base class
- Lives within the split-pane tree structure
- Communicates through signals and the command pattern
- Manages its own state and resources
- Integrates with the application's theme system

### Architecture Overview

```
┌─────────────────────────────────────────┐
│           Split Pane Model              │
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │  LeafNode    │───►│  AppWidget   │  │
│  │  (Model)     │    │  (Content)   │  │
│  └──────────────┘    └──────────────┘  │
│         │                    │          │
│         ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐  │
│  │  PaneContent │───►│  PaneHeader  │  │
│  │  (View)      │    │  (Controls)  │  │
│  └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────┘
```

## Core Concepts

### Base Class: AppWidget

Every AppWidget must extend the `AppWidget` base class from `ui/widgets/app_widget.py`:

```python
from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType

class MyCustomWidget(AppWidget):
    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        # Your initialization code here
```

### Key Methods to Implement

| Method | Purpose | Required |
|--------|---------|----------|
| `cleanup()` | Clean up resources when widget is destroyed | Yes |
| `get_state()` | Return serializable state for persistence | Yes |
| `set_state(state)` | Restore widget from persisted state | Yes |
| `can_close()` | Check if widget can be safely closed | Yes |
| `get_title()` | Return display title for the widget | Optional |
| `get_icon_name()` | Return icon name for the widget | Optional |
| `focus_widget()` | Set keyboard focus to appropriate element | Optional |

### Widget Types

Define your widget type in `ui/widgets/widget_registry.py`:

```python
class WidgetType(Enum):
    TEXT_EDITOR = "text_editor"
    TERMINAL = "terminal"
    SETTINGS = "settings"  # Add your new type
    CUSTOM = "custom"
```

## Step-by-Step Implementation

### Step 1: Create Your AppWidget Class

```python
#!/usr/bin/env python3
"""
My custom widget implementation.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.vscode_theme import get_settings_widget_stylesheet


class MyCustomWidget(AppWidget):
    """
    Custom widget for specific functionality.
    """

    def __init__(self, widget_id: str, parent=None):
        """Initialize the custom widget."""
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Apply theme stylesheet
        self.setStyleSheet(get_settings_widget_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add your UI components here

    def cleanup(self):
        """Clean up resources."""
        # Clean up any resources (connections, timers, etc.)
        pass

    def get_state(self) -> Dict[str, Any]:
        """Get widget state for persistence."""
        state = super().get_state()
        # Add your widget-specific state
        state["custom_data"] = "value"
        return state

    def set_state(self, state: Dict[str, Any]):
        """Restore widget state."""
        super().set_state(state)
        # Restore your widget-specific state
        if "custom_data" in state:
            # Restore the data
            pass

    def can_close(self) -> bool:
        """Check if widget can be closed."""
        # Check for unsaved changes, etc.
        return True
```

### Step 2: Create a Factory Function

The factory function creates instances of your widget:

```python
def create_my_custom_widget(widget_id: str) -> MyCustomWidget:
    """Factory function for creating custom widget instances."""
    return MyCustomWidget(widget_id)
```

### Step 3: Register the Factory

Register your factory at module load time (not inside a command):

```python
# At the top of your command file or in the widget file itself
def _register_custom_widget():
    """Register the custom widget factory."""
    try:
        from ui.widgets.my_custom_widget import MyCustomWidget
        from ui.widgets.widget_registry import widget_registry, WidgetType

        def create_custom_widget(widget_id: str) -> MyCustomWidget:
            return MyCustomWidget(widget_id)

        widget_registry.register_factory(WidgetType.CUSTOM, create_custom_widget)
        logger.debug("Registered custom widget factory")
    except ImportError as e:
        logger.error(f"Failed to register custom widget: {e}")

# Register when module is imported
_register_custom_widget()
```

### Step 4: Create a Command to Open Your Widget

```python
from core.commands.decorators import command
from core.commands.base import CommandContext, CommandResult

@command(
    id="app.openCustomWidget",
    title="Open Custom Widget",
    category="Application",
    description="Open a new custom widget tab",
    shortcut="ctrl+shift+w"
)
def open_custom_widget_command(context: CommandContext) -> CommandResult:
    """Open a custom widget in a new tab."""
    try:
        from services.workspace_service import WorkspaceService
        from ui.widgets.widget_registry import WidgetType
        import uuid

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        widget_id = f"custom_{uuid.uuid4().hex[:8]}"
        success = workspace_service.add_app_widget(
            WidgetType.CUSTOM,
            widget_id,
            "Custom Widget"
        )

        if success:
            return CommandResult(
                success=True,
                value={'widget_id': widget_id}
            )
        else:
            return CommandResult(success=False, error="Failed to create widget")

    except Exception as e:
        logger.error(f"Failed to open custom widget: {e}")
        return CommandResult(success=False, error=str(e))
```

## Theme Integration

### Using the VSCode Theme System

**NEVER hardcode colors or styles!** Always use the theme system from `ui/vscode_theme.py`.

#### Import Theme Components

```python
from ui.vscode_theme import (
    get_settings_widget_stylesheet,  # For settings/config widgets
    get_editor_stylesheet,           # For editor-like widgets
    EDITOR_BACKGROUND,               # Individual color constants
    EDITOR_FOREGROUND,
    WARNING_COLOR,
    FOCUS_BORDER
)
```

#### Apply Theme Stylesheets

Apply the appropriate stylesheet in your `setup_ui` method:

```python
def setup_ui(self):
    """Set up the user interface."""
    # Apply theme stylesheet to entire widget
    self.setStyleSheet(get_settings_widget_stylesheet())

    # Your UI setup code...
```

#### Theme-Aware Dynamic Styling

For dynamic styling (e.g., recording states, warnings):

```python
# Good - Uses theme colors
self.setStyleSheet(f"""
    QLineEdit {{
        background-color: {EDITOR_BACKGROUND};
        border: 2px solid {FOCUS_BORDER};
    }}
""")

# Bad - Hardcoded colors
self.setStyleSheet("QLineEdit { background-color: #ffeecc; }")
```

### Common Theme Functions

| Function | Use Case |
|----------|----------|
| `get_settings_widget_stylesheet()` | Configuration and settings widgets |
| `get_editor_stylesheet()` | Text editors and code viewers |
| `get_terminal_stylesheet()` | Terminal and console widgets |
| `get_sidebar_stylesheet()` | Sidebar panels and explorers |
| `get_tab_stylesheet()` | Tab containers |

### Handling Special UI States

```python
# Warning/Error states
warning_style = f"""
    QLabel {{
        background-color: rgba(244, 135, 113, 0.1);
        color: {WARNING_COLOR};
        border: 1px solid {WARNING_COLOR};
        border-radius: 4px;
        padding: 8px;
    }}
"""

# Active/Focus states
active_style = f"""
    QWidget {{
        border: 2px solid {FOCUS_BORDER};
        background-color: {EDITOR_BACKGROUND};
    }}
"""
```

## Widget Registry System

### Understanding the Registry

The widget registry (`ui/widgets/widget_registry.py`) manages:
- Widget type definitions
- Factory functions for creating widgets
- Configuration for each widget type
- State serialization/deserialization

### Widget Configuration

```python
from ui.widgets.widget_registry import WidgetConfig

config = WidgetConfig(
    widget_class=MyCustomWidget,
    factory=create_custom_widget,  # Optional custom factory
    preserve_context_menu=True,    # Keep native context menu
    show_header=True,              # Show pane header
    allow_type_change=True,        # Can change to other types
    can_be_closed=True,            # Can be closed
    can_be_split=True,             # Can split pane
    min_width=150,                 # Minimum dimensions
    min_height=100,
    default_content="",            # Default content
    stylesheet="",                 # Custom stylesheet (use theme!)
)
```

### Registration Timing

**Critical:** Register factories at module import time, NOT inside commands!

```python
# Good - Registration at module level
def _register_widget():
    widget_registry.register_factory(WidgetType.CUSTOM, factory)

_register_widget()  # Called when module imports

# Bad - Registration inside command
def command(context):
    # DON'T register here - too late!
    widget_registry.register_factory(...)
```

## Common Patterns

### Signal Communication

AppWidgets communicate through signals:

```python
class MyWidget(AppWidget):
    def request_split(self):
        """Request to split this pane."""
        self.request_action("split", {"direction": "horizontal"})

    def request_close(self):
        """Request to close this widget."""
        self.request_action("close", {"widget_id": self.widget_id})

    def notify_modified(self):
        """Notify that content was modified."""
        self.notify_state_change({"modified": True})
```

### State Persistence

Implement proper state management:

```python
def get_state(self) -> Dict[str, Any]:
    """Get complete widget state."""
    state = super().get_state()

    # Add all necessary state
    state.update({
        "content": self.get_content(),
        "cursor_position": self.get_cursor_position(),
        "scroll_position": self.get_scroll_position(),
        "custom_settings": self.settings
    })

    return state

def set_state(self, state: Dict[str, Any]):
    """Restore complete widget state."""
    super().set_state(state)

    # Restore all state
    if "content" in state:
        self.set_content(state["content"])
    if "cursor_position" in state:
        self.set_cursor_position(state["cursor_position"])
    # ... etc
```

### Focus Management

Handle focus properly:

```python
def focus_widget(self):
    """Set keyboard focus to the main input element."""
    if self.main_input:
        self.main_input.setFocus()

def mousePressEvent(self, event):
    """Request focus when clicked."""
    self.request_focus()
    super().mousePressEvent(event)
```

## Pitfalls to Avoid

### 1. Hardcoded Styles

**Problem:** Hardcoding colors breaks theme consistency
```python
# BAD
self.setStyleSheet("background-color: #ffeecc; color: #000000;")
```

**Solution:** Always use theme system
```python
# GOOD
from ui.vscode_theme import EDITOR_BACKGROUND, EDITOR_FOREGROUND
self.setStyleSheet(f"background-color: {EDITOR_BACKGROUND}; color: {EDITOR_FOREGROUND};")
```

### 2. Alternating Row Colors

**Problem:** Qt's alternating row colors can show white rows
```python
# BAD
self.tree_widget.setAlternatingRowColors(True)
```

**Solution:** Disable alternating colors for dark themes
```python
# GOOD
self.tree_widget.setAlternatingRowColors(False)
```

### 3. Factory Registration Timing

**Problem:** Registering factory inside command is too late
```python
# BAD - Inside command
def open_widget_command(context):
    register_factory(...)  # Too late!
    workspace_service.add_app_widget(...)
```

**Solution:** Register at module import
```python
# GOOD - Module level
_register_factory()  # At import time

def open_widget_command(context):
    workspace_service.add_app_widget(...)  # Factory already registered
```

### 4. Missing Theme Constants

**Problem:** Using undefined theme constants causes errors

**Solution:** Check constants exist or add them to `vscode_theme.py`:
```python
# In vscode_theme.py
FOCUS_BORDER = "#007acc"
PANEL_FOREGROUND = "#d4d4d4"
BUTTON_BORDER = "#0e639c"
```

### 5. CommandResult Parameters

**Problem:** CommandResult only accepts specific parameters
```python
# BAD
return CommandResult(success=True, message="Done")  # 'message' not accepted!
```

**Solution:** Use correct parameters
```python
# GOOD
return CommandResult(
    success=True,
    value={"message": "Done"},  # Put extra data in 'value'
    error=None  # Only for failures
)
```

## Complete Example

Here's the complete implementation of a settings widget (ShortcutConfigAppWidget):

### Widget Implementation
```python
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel
)
from PySide6.QtCore import Qt, Signal

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.vscode_theme import (
    get_settings_widget_stylesheet,
    WARNING_COLOR,
    FOCUS_BORDER,
    EDITOR_BACKGROUND
)

class ShortcutConfigAppWidget(AppWidget):
    """Keyboard shortcut configuration widget."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.SETTINGS, parent)
        self.modified_shortcuts = {}
        self.setup_ui()
        self.load_shortcuts()

    def setup_ui(self):
        """Set up the user interface."""
        # Apply theme - CRITICAL!
        self.setStyleSheet(get_settings_widget_stylesheet())

        layout = QVBoxLayout(self)

        # Create tree widget for shortcuts
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Command", "Shortcut"])
        self.tree_widget.setAlternatingRowColors(False)  # Important!

        layout.addWidget(self.tree_widget)

        # Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_changes)
        layout.addWidget(self.apply_button)

    def load_shortcuts(self):
        """Load shortcuts from registry."""
        # Implementation here
        pass

    def apply_changes(self):
        """Apply shortcut changes."""
        # Save changes
        # ...

        # Request close
        self.request_action("close", {"widget_id": self.widget_id})

    def cleanup(self):
        """Clean up resources."""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        state = super().get_state()
        state["modified"] = self.modified_shortcuts
        return state

    def set_state(self, state: Dict[str, Any]):
        """Restore widget state."""
        super().set_state(state)
        if "modified" in state:
            self.modified_shortcuts = state["modified"]

    def can_close(self) -> bool:
        """Check if can close."""
        if self.modified_shortcuts:
            # Could show dialog here
            return True
        return True
```

### Factory Registration
```python
# In settings_commands.py
def _register_shortcut_config_widget():
    """Register the shortcut configuration widget factory."""
    try:
        from ui.widgets.shortcut_config_app_widget import ShortcutConfigAppWidget
        from ui.widgets.widget_registry import widget_registry, WidgetType

        def create_shortcut_config_widget(widget_id: str) -> ShortcutConfigAppWidget:
            return ShortcutConfigAppWidget(widget_id)

        widget_registry.register_factory(WidgetType.SETTINGS, create_shortcut_config_widget)
        logger.debug("Registered shortcut configuration widget factory")
    except ImportError as e:
        logger.error(f"Failed to register shortcut config widget: {e}")

# Register at module import
_register_shortcut_config_widget()
```

### Command Integration
```python
@command(
    id="settings.openKeyboardShortcuts",
    title="Keyboard Shortcuts...",
    category="Settings",
    description="Open keyboard shortcuts configuration",
    shortcut="ctrl+k ctrl+s"
)
def open_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Open keyboard shortcuts configuration widget."""
    try:
        from services.workspace_service import WorkspaceService
        from ui.widgets.widget_registry import WidgetType
        import uuid

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        widget_id = f"shortcuts_config_{uuid.uuid4().hex[:8]}"
        success = workspace_service.add_app_widget(
            WidgetType.SETTINGS,
            widget_id,
            "Keyboard Shortcuts"
        )

        if success:
            return CommandResult(
                success=True,
                value={'widget_id': widget_id}
            )
        else:
            return CommandResult(success=False, error="Failed to create widget")

    except Exception as e:
        logger.error(f"Failed to open keyboard shortcuts: {e}")
        return CommandResult(success=False, error=str(e))
```

## Testing Your AppWidget

### Manual Testing Checklist

- [ ] Widget creates and displays correctly
- [ ] Theme is properly applied (no white backgrounds in dark mode)
- [ ] State persistence works (save/restore)
- [ ] Widget can be closed safely
- [ ] Focus management works correctly
- [ ] Signals are properly connected
- [ ] No hardcoded colors or styles
- [ ] Works in split panes
- [ ] Tab title displays correctly

### Unit Testing

```python
def test_widget_creation(qtbot):
    """Test widget can be created."""
    widget = MyCustomWidget("test_id")
    qtbot.addWidget(widget)
    assert widget.widget_id == "test_id"
    assert widget.widget_type == WidgetType.CUSTOM

def test_state_persistence(qtbot):
    """Test state save/restore."""
    widget = MyCustomWidget("test_id")
    qtbot.addWidget(widget)

    # Set some state
    widget.set_content("test content")

    # Save state
    state = widget.get_state()
    assert "content" in state

    # Create new widget and restore
    widget2 = MyCustomWidget("test_id2")
    widget2.set_state(state)
    assert widget2.get_content() == "test content"
```

## Troubleshooting

### Widget Not Appearing

1. Check factory is registered at module import
2. Verify WidgetType is defined in enum
3. Check WorkspaceService.add_app_widget() is called correctly
4. Look for errors in logs about factory registration

### Theme Not Applied

1. Ensure `setStyleSheet()` is called in `setup_ui()`
2. Check you're using a theme function, not hardcoded styles
3. Verify theme constants are defined in `vscode_theme.py`
4. Check for style conflicts with child widgets

### State Not Persisting

1. Implement both `get_state()` and `set_state()`
2. Call `super().get_state()` and `super().set_state()`
3. Ensure state dictionary is serializable (no Qt objects)
4. Check state is actually being saved by the framework

### Signals Not Working

1. Connect signals after widget creation
2. Use `self.request_action()` for system actions
3. Check signal/slot signatures match
4. Verify parent widgets are connecting to signals

## Conclusion

Creating AppWidgets is straightforward when you follow the patterns:
1. Extend AppWidget base class
2. Use the theme system (never hardcode styles)
3. Register factory at module import time
4. Implement required methods
5. Integrate with command system
6. Test thoroughly

Remember: The theme system is your friend. Use it consistently for a professional, cohesive application appearance.

## Related Documentation

- [Theme System Architecture](../architecture/THEMING_AND_STYLING.md)
- [Command Pattern](../architecture/COMMAND_AND_NAVIGATION_SYSTEM.md)
- [Widget Registry Architecture](../pending/UNIFIED_TAB_REGISTRY_ARCHITECTURE.md)
- [Keyboard Shortcuts Architecture](../architecture/KEYBOARD_SHORTCUT_ARCHITECTURE.md)