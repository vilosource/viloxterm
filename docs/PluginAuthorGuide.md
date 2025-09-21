# ViloxTerm Plugin Author Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Plugin Structure](#plugin-structure)
3. [Implementing IPlugin](#implementing-iplugin)
4. [Creating Widgets](#creating-widgets)
5. [Commands and Keybindings](#commands-and-keybindings)
6. [Configuration](#configuration)
7. [Using Services](#using-services)
8. [Event Handling](#event-handling)
9. [Testing Plugins](#testing-plugins)
10. [Debugging](#debugging)
11. [Packaging and Distribution](#packaging-and-distribution)
12. [Complete Examples](#complete-examples)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

## Quick Start

### Minimal Plugin Example

```python
# myplugin/plugin.py
from viloapp_sdk import IPlugin, PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="myplugin",
            name="My Plugin",
            version="1.0.0",
            description="A simple ViloxTerm plugin",
            author="Your Name",
            license="MIT"
        )

    def activate(self, context):
        """Called when plugin is activated."""
        self.context = context
        print(f"Plugin {self.get_metadata().name} activated!")

        # Register a command
        command_service = context.get_service("command")
        if command_service:
            command_service.register_command(
                "myplugin.hello",
                lambda: print("Hello from plugin!")
            )

    def deactivate(self):
        """Called when plugin is deactivated."""
        print("Plugin deactivated")
```

### Minimal plugin.json

```json
{
  "id": "myplugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "main": "plugin.py",
  "entry_point": "myplugin.plugin:MyPlugin"
}
```

## Plugin Structure

### Standard Directory Layout

```
myplugin/
├── plugin.json                 # Plugin manifest
├── pyproject.toml              # Python package configuration
├── README.md                   # Documentation
├── LICENSE                     # License file
├── src/
│   └── myplugin/
│       ├── __init__.py
│       ├── plugin.py           # Main plugin class
│       ├── widget.py           # Widget implementations
│       ├── commands.py         # Command handlers
│       └── resources/          # Assets (icons, styles)
├── tests/                      # Plugin tests
│   ├── test_plugin.py
│   └── test_widget.py
└── docs/                       # Additional documentation
```

### Complete plugin.json Reference

```json
{
  "id": "myplugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "Detailed plugin description",
  "author": "Your Name",
  "license": "MIT",
  "homepage": "https://github.com/you/myplugin",
  "repository": {
    "type": "git",
    "url": "https://github.com/you/myplugin.git"
  },
  "engines": {
    "viloapp": ">=2.0.0",
    "viloapp-sdk": ">=1.0.0"
  },
  "categories": ["Development Tools", "Productivity"],
  "keywords": ["example", "plugin"],
  "icon": "icon.png",
  "main": "src/myplugin/plugin.py",
  "entry_point": "myplugin.plugin:MyPlugin",

  "activationEvents": [
    "onStartup",
    "onCommand:myplugin.activate",
    "onView:myview",
    "workspaceContains:**/*.myext"
  ],

  "contributes": {
    "commands": [
      {
        "id": "myplugin.doSomething",
        "title": "Do Something",
        "category": "My Plugin",
        "icon": "action-icon"
      }
    ],

    "widgets": [
      {
        "id": "mywidget",
        "factory": "myplugin.widget:MyWidgetFactory"
      }
    ],

    "keybindings": [
      {
        "command": "myplugin.doSomething",
        "key": "ctrl+shift+m",
        "mac": "cmd+shift+m",
        "when": "editorFocus"
      }
    ],

    "configuration": {
      "myplugin.setting1": {
        "type": "string",
        "default": "default value",
        "description": "Setting description"
      },
      "myplugin.enableFeature": {
        "type": "boolean",
        "default": true,
        "description": "Enable special feature"
      }
    },

    "menus": {
      "commandPalette": [
        {
          "command": "myplugin.doSomething",
          "when": "resourceExtname == .txt"
        }
      ],
      "view/title": [
        {
          "command": "myplugin.refresh",
          "when": "view == myview",
          "group": "navigation"
        }
      ]
    }
  },

  "permissions": [
    {
      "category": "filesystem",
      "scope": "read",
      "resource": "/home/*"
    },
    {
      "category": "ui",
      "scope": "write",
      "resource": "*"
    }
  ]
}
```

### pyproject.toml Configuration

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "myplugin"
version = "1.0.0"
description = "My ViloxTerm Plugin"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.8"
dependencies = [
    "viloapp-sdk>=1.0.0",
    "PySide6>=6.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-qt>=4.2.0",
    "black>=23.0",
    "ruff>=0.1.0",
]

[project.entry-points."viloapp.plugins"]
myplugin = "myplugin.plugin:MyPlugin"

[tool.setuptools.packages.find]
where = ["src"]
```

## Implementing IPlugin

### Complete Plugin Implementation

```python
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from viloapp_sdk import (
    IPlugin, PluginMetadata, PluginCapability,
    IPluginContext, EventType
)

logger = logging.getLogger(__name__)

class MyPlugin(IPlugin):
    """Main plugin class implementing IPlugin interface."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None
        self.commands_registered = False
        self.widgets_registered = False
        self.event_subscriptions = []

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            id="myplugin",
            name="My Plugin",
            version="1.0.0",
            description="Comprehensive plugin example",
            author="Your Name",
            homepage="https://github.com/you/myplugin",
            license="MIT",
            categories=["Development Tools"],
            keywords=["example", "tutorial"],
            capabilities=[
                PluginCapability.WIDGETS,
                PluginCapability.COMMANDS,
                PluginCapability.THEMES
            ],
            activation_events=[
                "onStartup",
                "onCommand:myplugin.activate"
            ]
        )

    def activate(self, context: IPluginContext) -> None:
        """Activate the plugin."""
        self.context = context
        logger.info(f"Activating {self.get_metadata().name}")

        # Get data directory (creates if needed)
        self.data_path = context.get_data_path()

        # Load saved state
        self._load_state()

        # Register components
        self._register_commands()
        self._register_widgets()
        self._subscribe_to_events()

        # Initialize features
        self._initialize_features()

        logger.info("Plugin activated successfully")

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        logger.info("Deactivating plugin")

        # Save state
        self._save_state()

        # Cleanup
        self._unregister_commands()
        self._unregister_widgets()
        self._unsubscribe_events()

        # Clear references
        self.context = None
        logger.info("Plugin deactivated")

    def on_configuration_changed(self, config: Dict[str, Any]) -> None:
        """Handle configuration changes."""
        logger.debug(f"Configuration changed: {config}")

        # Apply new settings
        if "myplugin.theme" in config:
            self._apply_theme(config["myplugin.theme"])

        if "myplugin.enableFeature" in config:
            self._toggle_feature(config["myplugin.enableFeature"])

    def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
        """Handle command execution."""
        if command_id == "myplugin.doSomething":
            return self._do_something(args)
        elif command_id == "myplugin.configure":
            return self._show_configuration()

        return None

    # Private methods for organization

    def _register_commands(self):
        """Register plugin commands."""
        command_service = self.context.get_service("command")
        if not command_service:
            logger.warning("Command service not available")
            return

        command_service.register_command(
            "myplugin.doSomething",
            self._do_something,
            description="Do something amazing"
        )

        command_service.register_command(
            "myplugin.configure",
            self._show_configuration,
            description="Configure plugin"
        )

        self.commands_registered = True

    def _unregister_commands(self):
        """Unregister plugin commands."""
        if not self.commands_registered:
            return

        command_service = self.context.get_service("command")
        if command_service:
            command_service.unregister_command("myplugin.doSomething")
            command_service.unregister_command("myplugin.configure")

        self.commands_registered = False

    def _do_something(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Command implementation."""
        ui_service = self.context.get_service("ui")
        if ui_service:
            ui_service.show_notification("Doing something!", "info")

        return {"success": True, "message": "Something done!"}

    def _load_state(self):
        """Load saved plugin state."""
        state_file = self.data_path / "state.json"
        if state_file.exists():
            import json
            with open(state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {}

    def _save_state(self):
        """Save plugin state."""
        state_file = self.data_path / "state.json"
        import json
        with open(state_file, 'w') as f:
            json.dump(self.state, f)
```

## Creating Widgets

### Implementing IWidget

```python
from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal
from viloapp_sdk import IWidget

class MyWidget(QWidget):
    """Custom widget implementation."""

    # Qt signals
    action_triggered = Signal(str)
    state_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup widget UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Add widgets
        self.label = QLabel("My Plugin Widget")
        layout.addWidget(self.label)

        self.button = QPushButton("Click Me")
        self.button.clicked.connect(self.on_button_clicked)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def on_button_clicked(self):
        """Handle button click."""
        self.action_triggered.emit("button_clicked")

    def update_content(self, content: str):
        """Update widget content."""
        self.label.setText(content)

    def get_state(self) -> Dict[str, Any]:
        """Get widget state for persistence."""
        return {
            "label_text": self.label.text(),
            "button_enabled": self.button.isEnabled()
        }

    def restore_state(self, state: Dict[str, Any]):
        """Restore widget state."""
        if "label_text" in state:
            self.label.setText(state["label_text"])
        if "button_enabled" in state:
            self.button.setEnabled(state["button_enabled"])


class MyWidgetFactory(IWidget):
    """Widget factory implementing IWidget interface."""

    def __init__(self):
        self._instances = {}

    def get_widget_id(self) -> str:
        """Return unique widget identifier."""
        return "mywidget"

    def get_title(self) -> str:
        """Return widget display title."""
        return "My Widget"

    def get_icon(self) -> Optional[str]:
        """Return widget icon identifier."""
        return "my-icon"

    def create_instance(self, instance_id: str) -> QWidget:
        """Create new widget instance."""
        widget = MyWidget()
        self._instances[instance_id] = widget

        # Connect signals for tracking
        widget.state_changed.connect(
            lambda state: self._on_state_changed(instance_id, state)
        )

        return widget

    def destroy_instance(self, instance_id: str) -> None:
        """Destroy widget instance and cleanup."""
        if instance_id in self._instances:
            widget = self._instances[instance_id]

            # Cleanup
            widget.deleteLater()
            del self._instances[instance_id]

    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        """Handle widget-specific commands."""
        if command == "update_all":
            # Update all widget instances
            for widget in self._instances.values():
                widget.update_content(args.get("content", ""))
            return {"success": True, "updated": len(self._instances)}

        elif command == "get_instance_count":
            return {"count": len(self._instances)}

        return None

    def get_state(self) -> Dict[str, Any]:
        """Get factory state."""
        return {
            "instance_states": {
                instance_id: widget.get_state()
                for instance_id, widget in self._instances.items()
            }
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore factory state."""
        instance_states = state.get("instance_states", {})
        for instance_id, widget_state in instance_states.items():
            if instance_id in self._instances:
                self._instances[instance_id].restore_state(widget_state)

    def _on_state_changed(self, instance_id: str, state: Dict[str, Any]):
        """Handle widget state changes."""
        logger.debug(f"Widget {instance_id} state changed: {state}")
```

### Registering Widgets

```python
def _register_widgets(self):
    """Register plugin widgets."""
    workspace_service = self.context.get_service("workspace")
    if not workspace_service:
        return

    # Create and register widget factory
    self.widget_factory = MyWidgetFactory()
    workspace_service.register_widget_factory(
        "mywidget",
        self.widget_factory
    )

    self.widgets_registered = True
```

## Commands and Keybindings

### Command Registration

```python
def _register_commands(self):
    """Register all plugin commands."""
    command_service = self.context.get_service("command")
    if not command_service:
        return

    # Simple command
    command_service.register_command(
        "myplugin.simple",
        lambda: print("Simple command executed")
    )

    # Command with arguments
    command_service.register_command(
        "myplugin.withArgs",
        self._command_with_args
    )

    # Async command
    command_service.register_command(
        "myplugin.async",
        self._async_command,
        is_async=True
    )

def _command_with_args(self, args: Dict[str, Any]) -> Any:
    """Command that accepts arguments."""
    name = args.get("name", "World")
    message = args.get("message", "Hello")

    result = f"{message}, {name}!"

    # Show notification
    ui_service = self.context.get_service("ui")
    if ui_service:
        ui_service.show_notification(result)

    return {"success": True, "result": result}

async def _async_command(self, args: Dict[str, Any]) -> Any:
    """Async command for long-running operations."""
    import asyncio

    # Simulate long operation
    await asyncio.sleep(2)

    return {"success": True, "message": "Async operation complete"}
```

### Keybinding Context

```python
# In plugin.json
"keybindings": [
  {
    "command": "myplugin.action",
    "key": "ctrl+shift+a",
    "mac": "cmd+shift+a",
    "when": "editorFocus && resourceExtname == .py"
  }
]
```

Context expressions:
- `editorFocus`: Editor has focus
- `terminalFocus`: Terminal has focus
- `resourceExtname == .py`: Current file is Python
- `view == myview`: Specific view is active
- `!inputFocus`: No input field has focus

## Configuration

### Define Configuration Schema

```json
// In plugin.json
"configuration": {
  "myplugin.apiEndpoint": {
    "type": "string",
    "default": "https://api.example.com",
    "description": "API endpoint URL"
  },
  "myplugin.maxRetries": {
    "type": "number",
    "default": 3,
    "minimum": 1,
    "maximum": 10,
    "description": "Maximum retry attempts"
  },
  "myplugin.features": {
    "type": "object",
    "properties": {
      "enableCache": {
        "type": "boolean",
        "default": true
      },
      "cacheSize": {
        "type": "number",
        "default": 100
      }
    }
  }
}
```

### Access Configuration

```python
def _load_configuration(self):
    """Load plugin configuration."""
    config = self.context.get_configuration()

    # Access with defaults
    self.api_endpoint = config.get("apiEndpoint", "https://api.example.com")
    self.max_retries = config.get("maxRetries", 3)

    # Nested configuration
    features = config.get("features", {})
    self.cache_enabled = features.get("enableCache", True)
    self.cache_size = features.get("cacheSize", 100)

def on_configuration_changed(self, config: Dict[str, Any]):
    """React to configuration changes."""
    if "apiEndpoint" in config:
        self.api_endpoint = config["apiEndpoint"]
        self._reconnect_api()

    if "features" in config:
        self._update_features(config["features"])
```

### Save User Preferences

```python
def _save_preferences(self, preferences: Dict[str, Any]):
    """Save user preferences."""
    settings_service = self.context.get_service("settings")
    if settings_service:
        for key, value in preferences.items():
            settings_service.set(f"plugins.myplugin.{key}", value)
        settings_service.save()
```

## Using Services

### Available Services Reference

```python
# Workspace Service
workspace_service = self.context.get_service("workspace")
workspace_service.add_widget(widget, "mywidget", "main")
workspace_service.remove_widget(widget)
active_widget = workspace_service.get_active_widget()

# UI Service
ui_service = self.context.get_service("ui")
ui_service.show_notification("Message", "info")  # info, warning, error
main_window = ui_service.get_main_window()
current_theme = ui_service.get_theme()

# Command Service
command_service = self.context.get_service("command")
command_service.register_command("id", handler)
command_service.execute_command("other.command", {"arg": "value"})
command_service.unregister_command("id")

# Terminal Service
terminal_service = self.context.get_service("terminal")
terminal_id = terminal_service.create_terminal("/bin/bash")
terminal_service.send_text(terminal_id, "ls -la\n")
terminal_service.close_terminal(terminal_id)

# Editor Service
editor_service = self.context.get_service("editor")
editor_service.open_file("/path/to/file.py")
content = editor_service.get_content()
editor_service.save_file("/path/to/file.py", content)

# Theme Service
theme_service = self.context.get_service("theme")
current_theme = theme_service.get_current_theme()
theme_service.apply_theme("dark")
available_themes = theme_service.get_available_themes()

# Settings Service
settings_service = self.context.get_service("settings")
value = settings_service.get("key", default_value)
settings_service.set("key", value)
settings_service.save()
```

### Service Error Handling

```python
def safe_service_call(self, service_name: str, method: str, *args, **kwargs):
    """Safely call a service method."""
    try:
        service = self.context.get_service(service_name)
        if service and hasattr(service, method):
            return getattr(service, method)(*args, **kwargs)
        else:
            logger.warning(f"Service {service_name}.{method} not available")
            return None
    except Exception as e:
        logger.error(f"Error calling {service_name}.{method}: {e}")
        return None
```

## Event Handling

### Subscribe to Events

```python
def _subscribe_to_events(self):
    """Subscribe to relevant events."""
    # Theme changes
    self.context.subscribe_event(
        EventType.THEME_CHANGED,
        self._on_theme_changed
    )

    # Settings changes
    self.context.subscribe_event(
        EventType.SETTINGS_CHANGED,
        self._on_settings_changed
    )

    # Custom events
    self.context.subscribe_event(
        "custom.event",
        self._on_custom_event
    )

    # Track subscriptions for cleanup
    self.event_subscriptions = [
        EventType.THEME_CHANGED,
        EventType.SETTINGS_CHANGED,
        "custom.event"
    ]

def _on_theme_changed(self, event):
    """Handle theme change."""
    logger.info(f"Theme changed to: {event.data.get('theme')}")
    # Update widget colors
    if hasattr(self, 'widget_factory'):
        self.widget_factory.apply_theme(event.data)

def _on_settings_changed(self, event):
    """Handle settings change."""
    if "plugins.myplugin" in event.data:
        self.on_configuration_changed(event.data["plugins.myplugin"])
```

### Emit Events

```python
def _emit_custom_event(self, data: Dict[str, Any]):
    """Emit a custom event."""
    self.context.emit_event(
        "myplugin.something_happened",
        {
            "timestamp": time.time(),
            "action": "user_action",
            **data
        }
    )
```

## Testing Plugins

### Unit Testing

```python
# tests/test_plugin.py
import pytest
from unittest.mock import Mock, MagicMock
from myplugin.plugin import MyPlugin

@pytest.fixture
def plugin():
    """Create plugin instance."""
    return MyPlugin()

@pytest.fixture
def mock_context():
    """Create mock plugin context."""
    context = Mock()
    context.get_data_path.return_value = Path("/tmp/test")
    context.get_configuration.return_value = {}

    # Mock services
    context.get_service.side_effect = lambda name: {
        "command": Mock(),
        "ui": Mock(),
        "workspace": Mock()
    }.get(name)

    return context

def test_plugin_metadata(plugin):
    """Test plugin metadata."""
    metadata = plugin.get_metadata()
    assert metadata.id == "myplugin"
    assert metadata.version == "1.0.0"

def test_plugin_activation(plugin, mock_context):
    """Test plugin activation."""
    plugin.activate(mock_context)

    assert plugin.context == mock_context
    assert plugin.commands_registered

    # Verify service calls
    mock_context.get_service.assert_called()

def test_command_execution(plugin, mock_context):
    """Test command execution."""
    plugin.activate(mock_context)

    result = plugin.on_command("myplugin.doSomething", {})
    assert result["success"] is True

def test_configuration_change(plugin, mock_context):
    """Test configuration handling."""
    plugin.activate(mock_context)

    config = {"myplugin.enableFeature": True}
    plugin.on_configuration_changed(config)

    # Verify configuration applied
    assert plugin.feature_enabled is True
```

### Integration Testing

```python
# tests/test_integration.py
from viloapp_sdk.testing import PluginTestHarness

def test_plugin_integration():
    """Test plugin in simulated environment."""
    harness = PluginTestHarness()

    # Load plugin
    plugin = harness.load_plugin("myplugin")

    # Simulate activation
    harness.activate_plugin(plugin)

    # Test command execution
    result = harness.execute_command("myplugin.doSomething")
    assert result["success"] is True

    # Test widget creation
    widget = harness.create_widget("mywidget")
    assert widget is not None

    # Cleanup
    harness.deactivate_plugin(plugin)
```

### Widget Testing

```python
# tests/test_widget.py
import pytest
from pytestqt import qtbot
from myplugin.widget import MyWidget, MyWidgetFactory

def test_widget_creation(qtbot):
    """Test widget creation."""
    widget = MyWidget()
    qtbot.addWidget(widget)

    assert widget.label.text() == "My Plugin Widget"
    assert widget.button.isEnabled()

def test_widget_interaction(qtbot):
    """Test widget interaction."""
    widget = MyWidget()
    qtbot.addWidget(widget)

    # Click button
    with qtbot.waitSignal(widget.action_triggered) as blocker:
        qtbot.mouseClick(widget.button, Qt.LeftButton)

    assert blocker.args[0] == "button_clicked"

def test_widget_factory():
    """Test widget factory."""
    factory = MyWidgetFactory()

    # Create instance
    widget1 = factory.create_instance("test1")
    assert widget1 is not None

    # Verify tracking
    assert "test1" in factory._instances

    # Destroy instance
    factory.destroy_instance("test1")
    assert "test1" not in factory._instances
```

## Debugging

### Enable Debug Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Debug Mode

```bash
# Set environment variable
export VILOAPP_DEBUG=1
export VILOAPP_LOG_LEVEL=DEBUG

# Run with verbose output
viloapp --debug --log-level DEBUG
```

### Common Debugging Techniques

```python
def debug_context(self):
    """Print context information for debugging."""
    print(f"Plugin ID: {self.context.get_plugin_id()}")
    print(f"Plugin Path: {self.context.get_plugin_path()}")
    print(f"Data Path: {self.context.get_data_path()}")

    # List available services
    for service_name in ["command", "ui", "workspace", "terminal", "editor"]:
        service = self.context.get_service(service_name)
        print(f"Service '{service_name}': {service is not None}")

def trace_execution(func):
    """Decorator for tracing function execution."""
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper
```

### Performance Profiling

```python
import time
from contextlib import contextmanager

@contextmanager
def profile_performance(operation_name: str):
    """Context manager for performance profiling."""
    start_time = time.time()
    logger.debug(f"Starting {operation_name}")

    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.info(f"{operation_name} took {elapsed:.3f} seconds")

        if elapsed > 1.0:
            logger.warning(f"{operation_name} is slow: {elapsed:.3f}s")

# Usage
def some_operation(self):
    with profile_performance("data_processing"):
        # Long running operation
        self.process_data()
```

## Packaging and Distribution

### Build Package

```bash
# Install build tools
pip install build

# Build distribution
python -m build

# Output in dist/
# - myplugin-1.0.0-py3-none-any.whl
# - myplugin-1.0.0.tar.gz
```

### Install Plugin

```bash
# Install from PyPI
pip install myplugin

# Install from local package
pip install ./dist/myplugin-1.0.0-py3-none-any.whl

# Install in development mode
pip install -e .
```

### Publish to PyPI

```bash
# Install twine
pip install twine

# Upload to PyPI
twine upload dist/*
```

### Plugin Discovery

Installed plugins are discovered via entry points:

```python
# Check if plugin is discoverable
import importlib.metadata

entry_points = importlib.metadata.entry_points()
plugins = entry_points.get("viloapp.plugins", [])

for plugin in plugins:
    print(f"Found plugin: {plugin.name}")
```

## Complete Examples

### Terminal Plugin Pattern

```python
# From viloxterm/plugin.py
class TerminalPlugin(IPlugin):
    def __init__(self):
        self.widget_factory = TerminalWidgetFactory()
        self.session_manager = TerminalSessionManager()

    def activate(self, context):
        self.context = context

        # Register widget factory
        workspace_service = context.get_service("workspace")
        workspace_service.register_widget_factory(
            "terminal",
            self.widget_factory
        )

        # Register commands
        command_service = context.get_service("command")
        command_service.register_command(
            "terminal.new",
            self._create_new_terminal
        )

    def _create_new_terminal(self, args=None):
        workspace_service = self.context.get_service("workspace")

        # Create widget
        widget = self.widget_factory.create_instance(f"terminal_{id(self)}")

        # Add to workspace
        workspace_service.add_widget(widget, "terminal", "main")

        return {"success": True, "widget_id": id(widget)}
```

### Editor Plugin Pattern

```python
# From viloedit/plugin.py
class EditorPlugin(IPlugin):
    def __init__(self):
        self.widget_factory = EditorWidgetFactory()
        self.syntax_highlighter = SyntaxHighlighter()

    def activate(self, context):
        self.context = context

        # Register file handlers
        self._register_file_handlers()

        # Register language support
        self._register_languages()

    def _register_file_handlers(self):
        editor_service = self.context.get_service("editor")

        # Register for Python files
        editor_service.register_handler(
            ".py",
            self._handle_python_file
        )

    def _handle_python_file(self, filepath):
        # Create editor widget
        widget = self.widget_factory.create_instance(filepath)

        # Apply syntax highlighting
        self.syntax_highlighter.apply(widget, "python")

        return widget
```

## Best Practices

### Resource Management

```python
class MyPlugin(IPlugin):
    def __init__(self):
        self.resources = []
        self.connections = []

    def activate(self, context):
        # Track resources for cleanup
        file_handle = open("data.txt")
        self.resources.append(file_handle)

        # Track signal connections
        connection = widget.signal.connect(handler)
        self.connections.append((widget.signal, handler))

    def deactivate(self):
        # Clean up resources
        for resource in self.resources:
            if hasattr(resource, 'close'):
                resource.close()

        # Disconnect signals
        for signal, handler in self.connections:
            signal.disconnect(handler)

        # Clear collections
        self.resources.clear()
        self.connections.clear()
```

### Error Handling

```python
def robust_command_handler(self, args):
    """Robust command handler with error handling."""
    try:
        # Validate arguments
        if not self._validate_args(args):
            return {"success": False, "error": "Invalid arguments"}

        # Execute command
        result = self._execute_command(args)

        return {"success": True, "result": result}

    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return {"success": False, "error": "Permission denied"}

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

        # Show user-friendly error
        ui_service = self.context.get_service("ui")
        if ui_service:
            ui_service.show_notification(
                "Command failed. Check logs for details.",
                "error"
            )

        return {"success": False, "error": str(e)}
```

### Thread Safety

```python
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker

class WorkerThread(QThread):
    """Worker thread for background operations."""

    progress = Signal(int)
    finished = Signal(dict)

    def __init__(self, plugin_context):
        super().__init__()
        self.context = plugin_context
        self.mutex = QMutex()
        self._cancelled = False

    def run(self):
        """Run background operation."""
        for i in range(100):
            # Check cancellation
            with QMutexLocker(self.mutex):
                if self._cancelled:
                    break

            # Do work
            time.sleep(0.1)

            # Report progress (thread-safe signal)
            self.progress.emit(i)

        # Report completion
        self.finished.emit({"completed": not self._cancelled})

    def cancel(self):
        """Cancel operation (thread-safe)."""
        with QMutexLocker(self.mutex):
            self._cancelled = True
```

### Memory Management

```python
def manage_widget_lifecycle(self):
    """Proper widget lifecycle management."""
    # Use parent-child relationships
    parent_widget = QWidget()
    child_widget = QWidget(parent_widget)  # Deleted with parent

    # Use deleteLater for deferred deletion
    widget = QWidget()
    widget.deleteLater()  # Deleted after event loop iteration

    # Clear references
    self.widget = None  # Allow garbage collection

    # Use weak references for callbacks
    import weakref

    class WidgetManager:
        def __init__(self, widget):
            self.widget_ref = weakref.ref(widget)

        def update(self):
            widget = self.widget_ref()
            if widget:
                widget.update()
```

## Troubleshooting

### Common Issues and Solutions

#### Plugin Not Found

**Problem**: Plugin doesn't appear in ViloxTerm

**Solutions**:
1. Check entry point registration in `pyproject.toml`
2. Verify plugin.json exists and is valid JSON
3. Ensure plugin is installed: `pip list | grep myplugin`
4. Check logs for discovery errors

#### Widget Not Displaying

**Problem**: Widget created but not visible

**Solutions**:
1. Verify widget factory registration
2. Check parent widget is set correctly
3. Ensure layout is applied
4. Verify widget is added to workspace

#### Commands Not Working

**Problem**: Commands don't execute

**Solutions**:
1. Verify command registration in activate()
2. Check command ID matches everywhere
3. Test via command palette
4. Check context conditions ("when" clause)

#### Permission Denied

**Problem**: Service calls fail with permission errors

**Solutions**:
1. Add required permissions to plugin.json
2. Check permission categories and scopes
3. Request minimum necessary permissions

#### Memory Leaks

**Problem**: Plugin causes memory growth

**Solutions**:
1. Ensure proper cleanup in deactivate()
2. Disconnect all signal connections
3. Clear widget references
4. Use deleteLater() for Qt objects

### Debug Checklist

- [ ] Enable debug logging
- [ ] Check plugin.json validity
- [ ] Verify entry points
- [ ] Test in development mode
- [ ] Check service availability
- [ ] Monitor resource usage
- [ ] Review error logs
- [ ] Test with minimal plugin
- [ ] Verify Qt parent-child relationships
- [ ] Check thread safety

## Summary

This guide provides comprehensive coverage of ViloxTerm plugin development. Following these patterns and best practices will help you create robust, performant plugins that integrate seamlessly with the ViloxTerm ecosystem. Remember to test thoroughly, handle errors gracefully, and clean up resources properly.

For additional examples, refer to the `viloxterm` and `viloedit` plugins in the packages directory.