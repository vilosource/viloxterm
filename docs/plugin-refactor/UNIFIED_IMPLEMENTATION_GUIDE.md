# Unified Plugin Refactoring Implementation Guide

## Executive Summary

This guide consolidates the complete plugin architecture refactoring plan for ViloxTerm, transforming it from a monolithic application into a plugin-based architecture. The refactoring will extract the terminal and editor widgets as standalone plugins while maintaining backward compatibility.

**Duration**: 8 weeks
**Goal**: Create a modular, extensible application with clean plugin interfaces
**Structure**: Monorepo with namespace packages

## Prerequisites

Before starting, ensure:
- [ ] All existing tests pass: `make test`
- [ ] Current branch is clean: `git status`
- [ ] Python 3.8+ installed
- [ ] Development dependencies installed: `pip install -e ".[dev]"`
- [ ] Create feature branch: `git checkout -b feature/plugin-architecture`

## Phase 1: Monorepo Structure Setup (Week 1, Day 1-2)

### Step 1.1: Create Directory Structure

```bash
# From project root (/home/kuja/GitHub/viloapp)
mkdir -p packages/{viloapp-sdk,viloxterm,viloedit,viloapp}/{src,tests}
mkdir -p scripts
mkdir -p docs/plugin-development
```

### Step 1.2: Create Root Configuration

Create `/home/kuja/GitHub/viloapp/pyproject.toml`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "viloapp-workspace"
version = "0.0.1"
description = "ViloxTerm monorepo workspace"

[tool.hatch.build]
packages = [
    "packages/viloapp-sdk",
    "packages/viloxterm",
    "packages/viloedit",
    "packages/viloapp"
]

[tool.pytest]
testpaths = ["packages/*/tests"]

[tool.ruff]
src = ["packages/*/src"]
```

### Step 1.3: Setup Development Environment Script

Create `/home/kuja/GitHub/viloapp/scripts/dev-setup.py`:
```python
#!/usr/bin/env python3
"""Setup development environment for monorepo."""
import subprocess
import sys
from pathlib import Path

PACKAGES = ["viloapp-sdk", "viloxterm", "viloedit", "viloapp"]

def main():
    root = Path(__file__).parent.parent
    packages_dir = root / "packages"

    for package in PACKAGES:
        package_path = packages_dir / package
        print(f"Installing {package} in editable mode...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", str(package_path)
        ], check=True)

    print("Development environment setup complete!")

if __name__ == "__main__":
    main()
```

## Phase 2: Plugin SDK Development (Week 1, Day 3-5)

### Step 2.1: Create SDK Package Structure

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "viloapp-sdk"
version = "1.0.0"
description = "ViloxTerm Plugin SDK"
requires-python = ">=3.8"
dependencies = [
    "PySide6>=6.5.0",
    "typing-extensions>=4.0.0",
]

[tool.setuptools]
package-dir = {"": "src"}
packages = ["viloapp_sdk"]
```

### Step 2.2: Define Core Interfaces

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/__init__.py`:
```python
"""ViloxTerm Plugin SDK."""
from .plugin import IPlugin, PluginMetadata
from .widget import IWidget, WidgetMetadata
from .service import IService, ServiceProxy
from .events import EventBus, PluginEvent, EventType
from .lifecycle import ILifecycle, LifecycleState

__version__ = "1.0.0"
__all__ = [
    "IPlugin", "PluginMetadata",
    "IWidget", "WidgetMetadata",
    "IService", "ServiceProxy",
    "EventBus", "PluginEvent", "EventType",
    "ILifecycle", "LifecycleState",
]
```

### Step 2.3: Create Plugin Interface

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/plugin.py`:
```python
"""Plugin interface definitions."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject

@dataclass
class PluginMetadata:
    """Plugin metadata."""
    id: str
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None
    activation_events: List[str] = None
    contributes: Dict[str, Any] = None

class IPlugin(ABC):
    """Base plugin interface."""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass

    @abstractmethod
    def activate(self, context: 'PluginContext') -> None:
        """Called when plugin is activated."""
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """Called when plugin is deactivated."""
        pass
```

### Step 2.4: Create Widget Interface

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/widget.py`:
```python
"""Widget interface definitions."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

@dataclass
class WidgetMetadata:
    """Widget metadata."""
    id: str
    title: str
    icon: Optional[str] = None
    closable: bool = True
    singleton: bool = False

class IWidget(ABC):
    """Base widget interface for plugins."""

    @abstractmethod
    def get_metadata(self) -> WidgetMetadata:
        """Get widget metadata."""
        pass

    @abstractmethod
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create the actual Qt widget."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get widget state for persistence."""
        pass

    @abstractmethod
    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        pass
```

### Step 2.5: Create Event System

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/events.py`:
```python
"""Event system for plugin communication."""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable
from enum import Enum
import time

class EventType(Enum):
    """Standard event types."""
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    WIDGET_CREATED = "widget.created"
    WIDGET_DESTROYED = "widget.destroyed"
    SETTINGS_CHANGED = "settings.changed"
    THEME_CHANGED = "theme.changed"
    COMMAND_EXECUTED = "command.executed"

@dataclass
class PluginEvent:
    """Event structure."""
    type: EventType
    source: str
    data: Dict[str, Any] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.data is None:
            self.data = {}

class EventBus:
    """Event bus for plugin communication."""

    def __init__(self):
        self._handlers = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to events."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def emit(self, event: PluginEvent):
        """Emit an event."""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                handler(event)
```

## Phase 3: Plugin Host Infrastructure (Week 2)

### Step 3.1: Create Plugin Manager

Create `/home/kuja/GitHub/viloapp/core/plugin_manager.py`:
```python
"""Plugin management system."""
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

from viloapp_sdk import IPlugin, PluginMetadata, EventBus, PluginEvent, EventType

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin lifecycle and loading."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.plugins: Dict[str, IPlugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}

    def discover_plugins(self) -> List[str]:
        """Discover available plugins."""
        discovered = []

        # Check for installed plugins via entry points
        try:
            import importlib.metadata
            for entry_point in importlib.metadata.entry_points(group='viloapp.plugins'):
                discovered.append(entry_point.name)
                logger.info(f"Discovered plugin: {entry_point.name}")
        except Exception as e:
            logger.error(f"Failed to discover plugins: {e}")

        return discovered

    def load_plugin(self, plugin_id: str) -> bool:
        """Load a plugin."""
        if plugin_id in self.plugins:
            logger.warning(f"Plugin {plugin_id} already loaded")
            return True

        try:
            # Import plugin module
            module = importlib.import_module(f"{plugin_id}.plugin")

            # Get plugin class (convention: <PluginName>Plugin)
            plugin_class_name = ''.join(word.capitalize() for word in plugin_id.split('_')) + 'Plugin'
            plugin_class = getattr(module, plugin_class_name)

            # Instantiate plugin
            plugin = plugin_class()
            metadata = plugin.get_metadata()

            # Store plugin
            self.plugins[plugin_id] = plugin
            self.metadata[plugin_id] = metadata

            # Emit loaded event
            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_LOADED,
                source="plugin_manager",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Loaded plugin: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin."""
        if plugin_id not in self.plugins:
            return False

        try:
            plugin = self.plugins[plugin_id]
            plugin.deactivate()

            del self.plugins[plugin_id]
            del self.metadata[plugin_id]

            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_UNLOADED,
                source="plugin_manager",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Unloaded plugin: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
```

### Step 3.2: Create Service Proxy Layer

Create `/home/kuja/GitHub/viloapp/core/service_proxy.py`:
```python
"""Service proxy for plugins."""
from typing import Dict, Any, Optional
from viloapp_sdk import IService

class ServiceProxy(IService):
    """Proxy for accessing host services from plugins."""

    def __init__(self, allowed_services: Dict[str, Any]):
        self._services = allowed_services

    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name."""
        return self._services.get(service_name)

    def call_command(self, command_id: str, **kwargs) -> Any:
        """Execute a command."""
        from core.commands.executor import execute_command
        return execute_command(command_id, **kwargs)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        settings_service = self._services.get('settings')
        if settings_service:
            return settings_service.get(key, default)
        return default

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value."""
        settings_service = self._services.get('settings')
        if settings_service:
            settings_service.set(key, value)
```

## Phase 4: Terminal Plugin Extraction (Week 3-4)

### Step 4.1: Create Terminal Plugin Package

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "viloxterm"
version = "1.0.0"
description = "Terminal Plugin for ViloxTerm"
requires-python = ">=3.8"
dependencies = [
    "viloapp-sdk>=1.0.0",
    "PySide6>=6.5.0",
    "flask>=2.0.0",
    "flask-socketio>=5.0.0",
    "pyte>=0.8.0",
]

[project.entry-points."viloapp.plugins"]
terminal = "viloxterm.plugin:TerminalPlugin"

[tool.setuptools]
package-dir = {"": "src"}
packages = ["viloxterm"]
```

### Step 4.2: Move Terminal Code

```bash
# Create terminal plugin structure
mkdir -p packages/viloxterm/src/viloxterm

# Move terminal files (DO NOT EXECUTE YET - this is the plan)
# mv ui/terminal/* packages/viloxterm/src/viloxterm/
# Update imports in moved files: ui.terminal -> viloxterm
```

### Step 4.3: Create Terminal Plugin Adapter

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/plugin.py`:
```python
"""Terminal plugin implementation."""
from typing import Optional
from viloapp_sdk import IPlugin, PluginMetadata, IWidget, WidgetMetadata
from PySide6.QtWidgets import QWidget

class TerminalPlugin(IPlugin):
    """Terminal plugin for ViloxTerm."""

    def __init__(self):
        self.context = None
        self.widgets = {}

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="viloxterm",
            name="ViloxTerm Terminal",
            version="1.0.0",
            description="Terminal emulator plugin",
            author="ViloxTerm Team",
            dependencies=["viloapp-sdk>=1.0.0"],
            activation_events=["onCommand:terminal.new"],
            contributes={
                "commands": [
                    {
                        "id": "terminal.new",
                        "title": "New Terminal",
                        "category": "Terminal"
                    }
                ],
                "widgets": [
                    {
                        "id": "terminal",
                        "factory": "viloxterm.widget:TerminalWidgetFactory"
                    }
                ]
            }
        )

    def activate(self, context):
        """Activate the plugin."""
        self.context = context
        # Register commands
        self._register_commands()

    def deactivate(self):
        """Deactivate the plugin."""
        # Cleanup terminals
        for widget in self.widgets.values():
            widget.cleanup()
        self.widgets.clear()

    def _register_commands(self):
        """Register terminal commands."""
        # Implementation will be added
        pass
```

### Step 4.4: Create Terminal Widget Factory

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/widget.py`:
```python
"""Terminal widget factory."""
from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget
from viloapp_sdk import IWidget, WidgetMetadata

# Import existing terminal widget (will be moved here)
# from .terminal_widget import TerminalWidget

class TerminalWidgetFactory(IWidget):
    """Factory for terminal widgets."""

    def get_metadata(self) -> WidgetMetadata:
        return WidgetMetadata(
            id="terminal",
            title="Terminal",
            icon="terminal",
            closable=True,
            singleton=False
        )

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create a new terminal widget instance."""
        # Will use the moved TerminalWidget class
        # return TerminalWidget(parent)
        pass

    def get_state(self) -> Dict[str, Any]:
        """Get terminal state."""
        return {}

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore terminal state."""
        pass
```

## Phase 5: Editor Plugin Extraction (Week 5)

### Step 5.1: Create Editor Plugin Package

Create `/home/kuja/GitHub/viloapp/packages/viloedit/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "viloedit"
version = "1.0.0"
description = "Code Editor Plugin for ViloxTerm"
requires-python = ">=3.8"
dependencies = [
    "viloapp-sdk>=1.0.0",
    "PySide6>=6.5.0",
    "Pygments>=2.0.0",
]

[project.entry-points."viloapp.plugins"]
editor = "viloedit.plugin:EditorPlugin"

[tool.setuptools]
package-dir = {"": "src"}
packages = ["viloedit"]
```

### Step 5.2: Create Editor Plugin

Create `/home/kuja/GitHub/viloapp/packages/viloedit/src/viloedit/plugin.py`:
```python
"""Editor plugin implementation."""
from viloapp_sdk import IPlugin, PluginMetadata

class EditorPlugin(IPlugin):
    """Code editor plugin."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="viloedit",
            name="ViloEdit",
            version="1.0.0",
            description="Code editor plugin",
            author="ViloxTerm Team",
            contributes={
                "commands": [
                    {
                        "id": "editor.open",
                        "title": "Open File",
                        "category": "Editor"
                    }
                ],
                "widgets": [
                    {
                        "id": "editor",
                        "factory": "viloedit.widget:EditorWidgetFactory"
                    }
                ]
            }
        )

    def activate(self, context):
        self.context = context

    def deactivate(self):
        pass
```

## Phase 6: Integration (Week 6-7)

### Step 6.1: Update Main Application

Modify `/home/kuja/GitHub/viloapp/main.py`:
```python
# Add plugin loading
from core.plugin_manager import PluginManager
from viloapp_sdk import EventBus

def initialize_plugins():
    """Initialize plugin system."""
    event_bus = EventBus()
    plugin_manager = PluginManager(event_bus)

    # Discover and load plugins
    plugins = plugin_manager.discover_plugins()
    for plugin_id in plugins:
        plugin_manager.load_plugin(plugin_id)

    return plugin_manager

# In main():
# plugin_manager = initialize_plugins()
```

### Step 6.2: Update Widget Registration

Modify workspace to use plugin widgets instead of hardcoded ones:
```python
# In WorkspaceService
def register_plugin_widget(self, widget_factory):
    """Register a widget from a plugin."""
    metadata = widget_factory.get_metadata()
    self.widget_factories[metadata.id] = widget_factory
```

## Phase 7: Testing (Week 7-8)

### Step 7.1: Create Plugin Tests

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/tests/test_plugin.py`:
```python
"""Test plugin SDK."""
import pytest
from viloapp_sdk import IPlugin, PluginMetadata

class TestPlugin(IPlugin):
    """Test plugin implementation."""

    def get_metadata(self):
        return PluginMetadata(
            id="test",
            name="Test Plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test"
        )

    def activate(self, context):
        self.activated = True

    def deactivate(self):
        self.activated = False

def test_plugin_lifecycle():
    """Test plugin lifecycle."""
    plugin = TestPlugin()
    assert not hasattr(plugin, 'activated')

    plugin.activate(None)
    assert plugin.activated

    plugin.deactivate()
    assert not plugin.activated
```

### Step 7.2: Integration Tests

Create `/home/kuja/GitHub/viloapp/tests/integration/test_plugin_system.py`:
```python
"""Test plugin system integration."""
import pytest
from core.plugin_manager import PluginManager
from viloapp_sdk import EventBus

def test_plugin_discovery():
    """Test plugin discovery."""
    event_bus = EventBus()
    manager = PluginManager(event_bus)
    plugins = manager.discover_plugins()

    # Should find terminal and editor plugins
    assert 'terminal' in plugins
    assert 'editor' in plugins
```

## Phase 8: Migration and Documentation (Week 8)

### Step 8.1: Migration Script

Create `/home/kuja/GitHub/viloapp/scripts/migrate.py`:
```python
#!/usr/bin/env python3
"""Migrate settings and state to plugin architecture."""
import json
from pathlib import Path

def migrate_settings():
    """Migrate user settings."""
    # Load old settings
    # Convert to new format
    # Save new settings
    pass

def migrate_state():
    """Migrate application state."""
    # Load old state
    # Convert to plugin-based state
    # Save new state
    pass

if __name__ == "__main__":
    migrate_settings()
    migrate_state()
    print("Migration complete!")
```

### Step 8.2: Update Documentation

Create `/home/kuja/GitHub/viloapp/docs/plugin-development/README.md`:
```markdown
# Plugin Development Guide

## Quick Start

1. Install the SDK:
   ```bash
   pip install viloapp-sdk
   ```

2. Create your plugin:
   ```python
   from viloapp_sdk import IPlugin, PluginMetadata

   class MyPlugin(IPlugin):
       def get_metadata(self):
           return PluginMetadata(...)
   ```

3. Register via entry point in pyproject.toml:
   ```toml
   [project.entry-points."viloapp.plugins"]
   my_plugin = "my_plugin.plugin:MyPlugin"
   ```
```

## Validation Checkpoints

### After Phase 1-2 (SDK Creation):
- [ ] SDK package installs without errors
- [ ] All interfaces are importable
- [ ] Basic plugin can be created
- [ ] Event system works

### After Phase 3-4 (Terminal Extraction):
- [ ] Terminal plugin loads successfully
- [ ] Terminal commands work
- [ ] No regression in terminal functionality
- [ ] Terminal can be opened/closed

### After Phase 5 (Editor Extraction):
- [ ] Editor plugin loads successfully
- [ ] Editor commands work
- [ ] Files can be opened/edited
- [ ] Syntax highlighting works

### After Phase 6-8 (Integration):
- [ ] All tests pass
- [ ] No performance regression
- [ ] Plugins can be disabled/enabled
- [ ] Settings migrate correctly
- [ ] Documentation is complete

## Common Commands

```bash
# Setup development environment
python scripts/dev-setup.py

# Run tests for specific package
pytest packages/viloapp-sdk/tests
pytest packages/viloxterm/tests
pytest packages/viloedit/tests

# Build all packages
python scripts/build.py

# Install package in editable mode
pip install -e packages/viloapp-sdk
pip install -e packages/viloxterm
pip install -e packages/viloedit
pip install -e packages/viloapp

# Run the application
python packages/viloapp/src/viloapp/main.py

# Run migration
python scripts/migrate.py
```

## Rollback Plan

If issues arise:

1. **Phase 1-2**: Simply remove new directories, no impact on existing code
2. **Phase 3-5**: Keep both old and new implementations, feature flag to switch
3. **Phase 6-8**: Maintain backward compatibility layer until stable

## Success Criteria

- [ ] All existing functionality preserved
- [ ] Plugins can be developed independently
- [ ] Performance within 5% of current
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Successfully load/unload plugins at runtime

## Next Steps

1. Begin with Phase 1: Create monorepo structure
2. Implement SDK with core interfaces
3. Test with a minimal "hello world" plugin
4. Proceed to terminal extraction once SDK is stable
5. Continue through phases systematically

---

This guide should be followed sequentially. Each phase builds on the previous one. Do not skip steps or phases. Validate each checkpoint before proceeding.