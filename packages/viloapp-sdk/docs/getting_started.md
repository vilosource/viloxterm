# Getting Started with ViloxTerm Plugin SDK

## Installation

```bash
pip install viloapp-sdk
```

## Creating Your First Plugin

### 1. Basic Plugin Structure

Create a new directory for your plugin:

```
my-plugin/
├── pyproject.toml
├── src/
│   └── my_plugin/
│       ├── __init__.py
│       └── plugin.py
└── tests/
```

### 2. Define Your Plugin

Create `src/my_plugin/plugin.py`:

```python
from viloapp_sdk import IPlugin, PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="my-plugin",
            name="My Plugin",
            version="1.0.0",
            description="My first ViloxTerm plugin",
            author="Your Name"
        )

    def activate(self, context):
        print(f"Plugin {self.get_metadata().name} activated!")
        self.context = context

    def deactivate(self):
        print(f"Plugin {self.get_metadata().name} deactivated!")
```

### 3. Configure Package

Create `pyproject.toml`:

```toml
[project]
name = "my-plugin"
version = "1.0.0"
dependencies = ["viloapp-sdk>=1.0.0"]

[project.entry-points."viloapp.plugins"]
my-plugin = "my_plugin.plugin:MyPlugin"
```

### 4. Adding a Widget

```python
from viloapp_sdk import IWidget, WidgetMetadata, WidgetPosition
from PySide6.QtWidgets import QWidget, QLabel

class MyWidget(IWidget):
    def get_metadata(self) -> WidgetMetadata:
        return WidgetMetadata(
            id="my-widget",
            title="My Widget",
            position=WidgetPosition.SIDEBAR
        )

    def create_widget(self, parent=None) -> QWidget:
        widget = QLabel("Hello from my plugin!", parent)
        return widget

    def get_state(self):
        return {}

    def restore_state(self, state):
        pass
```

### 5. Accessing Services

```python
def activate(self, context):
    # Get notification service
    notify_service = context.get_service("notification")
    if notify_service:
        notify_service.info("Plugin activated!")

    # Execute a command
    command_service = context.get_service("command")
    if command_service:
        command_service.execute_command("workbench.action.openSettings")
```

### 6. Using Events

```python
from viloapp_sdk.events import EventType

def activate(self, context):
    # Subscribe to theme changes
    def on_theme_changed(event):
        print(f"Theme changed: {event.data}")

    context.subscribe_event(EventType.THEME_CHANGED, on_theme_changed)

    # Emit custom event
    context.emit_event(EventType.CUSTOM, {
        "message": "Plugin initialized"
    })
```

## Testing Your Plugin

```python
import pytest
from my_plugin.plugin import MyPlugin

def test_plugin_metadata():
    plugin = MyPlugin()
    metadata = plugin.get_metadata()
    assert metadata.id == "my-plugin"
    assert metadata.version == "1.0.0"
```

## Installing Your Plugin

```bash
# Install in development mode
pip install -e .

# Or build and install
python -m build
pip install dist/*.whl
```

## Next Steps

- Read the [API Reference](api_reference.md)
- Check out [Example Plugins](examples/)
- Learn about [Advanced Features](advanced.md)