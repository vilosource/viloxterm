# Plugin Architecture Boundary Fix Plan - UPDATED

## Problem Summary

The ViloxTerm application crashes on startup with an AttributeError because the PluginManager doesn't have a `name` attribute that the ServiceLocator expects. Deep audit reveals that while the plugin SDK was implemented, the critical integration layer between plugins and core application was never built, leaving the plugin system completely non-functional.

## Critical Issues Identified (Updated from Audit)

### 1. Immediate Runtime Errors
- **ServiceLocator Registration**: `AttributeError: 'PluginManager' object has no attribute 'name'`
- **Command Class Missing @dataclass**: Command objects can't be instantiated
- **Service Registration Type Mismatch**: Using string instead of class type

### 2. Integration Layer Completely Missing

#### Service Adapters Are Empty Stubs
```python
# Current implementation - doesn't work!
def register_command(self, command_id: str, handler: callable) -> None:
    # This would need implementation in command registry
    pass  # ← Never implemented!
```

#### Widget Registration Method Missing
- Plugin calls `workspace_service.register_widget_factory()`
- WorkspaceService doesn't have this method
- Plugin widgets can't be registered

#### No Widget Bridge
- Plugins implement IWidget interface
- Core expects AppWidget class
- No translation layer exists

### 3. Architectural Violations

#### Widget Duplication
- **Core widgets**: `ui/terminal/terminal_app_widget.py`, `ui/widgets/editor_app_widget.py`
- **Plugin widgets**: `packages/viloxterm/`, `packages/viloedit/`
- Core directly instantiates its own widgets, ignoring plugins

#### Tight Coupling
- Plugin system embedded as a service
- Direct widget creation in split_pane_model.py
- No abstraction between core and plugins

#### Missing Components
- AppWidgetManager doesn't exist (referenced in docs)
- No command bridge for plugin commands
- No event routing between plugins and core

## Implementation Plan - Phase-Based Approach

## Phase 1: Critical Fixes (Stop Crashes) - 2 Hours

### Task 1.1: Fix Command Class Structure
**Location**: `core/commands/base.py`
**Priority**: CRITICAL
```python
# Add missing import
from dataclasses import dataclass, field

# Add decorator to Command class
@dataclass
class Command:
    """Represents an executable command in the system."""
    # Existing field definitions remain
```

### Task 1.2: Create PluginService Wrapper
**Location**: `services/plugin_service.py` (new file)
**Priority**: CRITICAL
```python
from services.base import Service
from core.plugin_system import PluginManager
from typing import Optional, Dict, Any

class PluginService(Service):
    """Service wrapper for plugin management."""

    def __init__(self):
        super().__init__(name="PluginService")
        self._plugin_manager: Optional[PluginManager] = None
        self._widget_bridge = None

    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize plugin service with context."""
        super().initialize(context)
        # Plugin manager will be set externally

    def set_plugin_manager(self, plugin_manager: PluginManager) -> None:
        """Set the plugin manager instance."""
        self._plugin_manager = plugin_manager

    def cleanup(self) -> None:
        """Cleanup plugin system."""
        if self._plugin_manager:
            self._plugin_manager.shutdown()

    def get_plugin_manager(self) -> Optional[PluginManager]:
        """Get the underlying plugin manager."""
        return self._plugin_manager

    def register_widget(self, widget_factory) -> None:
        """Register a plugin widget factory."""
        if self._widget_bridge:
            self._widget_bridge.register_plugin_widget(widget_factory)
```

### Task 1.3: Fix Service Registration
**Location**: `services/__init__.py` lines 122-124
**Priority**: CRITICAL
```python
# Change from:
if plugin_manager:
    locator.register('plugin_manager', plugin_manager)

# To:
if plugin_manager:
    from services.plugin_service import PluginService
    plugin_service = PluginService()
    plugin_service.set_plugin_manager(plugin_manager)
    locator.register(PluginService, plugin_service)
```

## Phase 2: Enable Basic Functionality - 4 Hours

### Task 2.1: Implement CommandServiceAdapter
**Location**: `core/plugin_system/service_adapters.py`
**Priority**: HIGH
```python
def register_command(self, command_id: str, handler: callable) -> None:
    """Register a command with the command registry."""
    from core.commands.registry import command_registry
    from core.commands.base import Command, CommandContext, CommandResult

    # Create wrapper that converts plugin handler to command handler
    def command_wrapper(context: CommandContext) -> CommandResult:
        try:
            # Convert CommandContext to plugin args
            plugin_args = {
                'workspace': context.workspace,
                'active_widget': context.active_widget,
                **context.args
            }
            result = handler(plugin_args)
            return CommandResult(success=True, value=result)
        except Exception as e:
            return CommandResult(success=False, error=str(e))

    # Create Command instance
    command = Command(
        id=command_id,
        title=command_id.replace('.', ' ').title(),
        category="Plugin",
        handler=command_wrapper
    )

    # Register with command registry
    command_registry.register(command)

def unregister_command(self, command_id: str) -> None:
    """Unregister a command from the command registry."""
    from core.commands.registry import command_registry
    command_registry.unregister(command_id)
```

### Task 2.2: Add Widget Registration to WorkspaceService
**Location**: `services/workspace_service.py`
**Priority**: HIGH

Add new methods:
```python
def __init__(self):
    super().__init__(name="WorkspaceService")
    self._widget_factories = {}  # Add this
    # ... existing init code ...

def register_widget_factory(self, widget_id: str, factory: Any) -> None:
    """Register a widget factory (for plugins)."""
    self._widget_factories[widget_id] = factory
    logger.info(f"Registered widget factory: {widget_id}")

def create_widget(self, widget_id: str, instance_id: str) -> Optional[QWidget]:
    """Create a widget using registered factory."""
    if widget_id in self._widget_factories:
        factory = self._widget_factories[widget_id]
        # Handle both IWidget and direct factory functions
        if hasattr(factory, 'create_instance'):
            return factory.create_instance(instance_id)
        elif callable(factory):
            return factory(instance_id)
    return None

def get_widget_factories(self) -> Dict[str, Any]:
    """Get all registered widget factories."""
    return self._widget_factories.copy()
```

### Task 2.3: Create Plugin-Widget Bridge
**Location**: `core/plugin_system/widget_bridge.py` (new file)
**Priority**: HIGH
```python
"""Bridge between plugin widgets and core UI system."""

from typing import Dict, Any, Optional
from viloapp_sdk import IWidget
from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
import uuid

class PluginWidgetBridge:
    """Bridges plugin widgets to core UI system."""

    def __init__(self, workspace_service):
        self.workspace_service = workspace_service
        self._plugin_widgets: Dict[str, IWidget] = {}

    def register_plugin_widget(self, plugin_widget: IWidget) -> None:
        """Register a plugin widget with core UI."""
        widget_id = plugin_widget.get_widget_id()
        self._plugin_widgets[widget_id] = plugin_widget

        # Register factory with workspace service
        self.workspace_service.register_widget_factory(
            widget_id,
            lambda instance_id: self._create_widget_adapter(widget_id, instance_id)
        )

    def _create_widget_adapter(self, widget_id: str, instance_id: str) -> AppWidget:
        """Create AppWidget adapter for plugin widget."""
        plugin_widget = self._plugin_widgets[widget_id]
        qt_widget = plugin_widget.create_instance(instance_id)
        return PluginAppWidgetAdapter(plugin_widget, qt_widget, instance_id)


class PluginAppWidgetAdapter(AppWidget):
    """Adapts plugin widgets to core AppWidget interface."""

    def __init__(self, plugin_widget: IWidget, qt_widget, instance_id: str):
        widget_type = self._determine_widget_type(plugin_widget.get_widget_id())
        super().__init__(
            widget_id=instance_id,
            widget_type=widget_type
        )
        self.plugin_widget = plugin_widget
        self.qt_widget = qt_widget

        # Add the Qt widget as a child
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.qt_widget)

    def _determine_widget_type(self, widget_id: str) -> WidgetType:
        """Determine WidgetType from plugin widget ID."""
        if 'terminal' in widget_id.lower():
            return WidgetType.TERMINAL
        elif 'editor' in widget_id.lower():
            return WidgetType.EDITOR
        else:
            return WidgetType.CUSTOM

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        return self.plugin_widget.get_state()

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        self.plugin_widget.restore_state(state)

    def cleanup(self) -> None:
        """Cleanup widget resources."""
        if hasattr(self.plugin_widget, 'destroy_instance'):
            self.plugin_widget.destroy_instance(self.widget_id)
        super().cleanup()
```

## Phase 3: Remove Duplication - 3 Hours

### Task 3.1: Update Split Pane Model
**Location**: `ui/widgets/split_pane_model.py`
**Priority**: MEDIUM

Replace direct widget creation with factory pattern:
```python
def _create_widget_for_tab(self, widget_type: str, widget_id: str) -> AppWidget:
    """Create widget using registered factories or fallback."""
    # Try plugin widget first
    workspace_service = self.get_service(WorkspaceService)
    if workspace_service:
        widget = workspace_service.create_widget(widget_type, widget_id)
        if widget:
            return widget

    # Fallback to legacy widgets (temporary)
    if widget_type == "terminal":
        # Import locally to avoid circular dependency
        from ui.terminal.terminal_app_widget import TerminalAppWidget
        return TerminalAppWidget(widget_id)
    elif widget_type == "editor":
        from ui.widgets.editor_app_widget import EditorAppWidget
        return EditorAppWidget(widget_id)
    else:
        return self._create_placeholder_widget(widget_id)
```

### Task 3.2: Implement AppWidgetManager
**Location**: `ui/widgets/app_widget_manager.py` (new file)
**Priority**: MEDIUM
```python
"""Central widget management system."""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

class WidgetSource(Enum):
    """Source of widget registration."""
    CORE = "core"
    PLUGIN = "plugin"
    LEGACY = "legacy"

@dataclass
class WidgetMetadata:
    """Metadata for registered widgets."""
    id: str
    title: str
    icon: Optional[str]
    factory: Callable
    source: WidgetSource
    category: str = "General"
    keywords: List[str] = None
    singleton: bool = False

class AppWidgetManager:
    """Central registry for all application widgets."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._widgets: Dict[str, WidgetMetadata] = {}
        self._instances: Dict[str, Any] = {}  # For singleton widgets
        self._initialized = True

    def register_widget(self, metadata: WidgetMetadata) -> None:
        """Register a widget."""
        self._widgets[metadata.id] = metadata

    def create_widget(self, widget_id: str, instance_id: Optional[str] = None) -> Optional[Any]:
        """Create a widget instance."""
        if widget_id not in self._widgets:
            return None

        metadata = self._widgets[widget_id]

        # Handle singleton widgets
        if metadata.singleton:
            if widget_id not in self._instances:
                self._instances[widget_id] = metadata.factory(widget_id)
            return self._instances[widget_id]

        # Create new instance
        return metadata.factory(instance_id or self._generate_instance_id())

    def get_available_widgets(self, source: Optional[WidgetSource] = None) -> List[WidgetMetadata]:
        """Get list of available widgets."""
        widgets = list(self._widgets.values())
        if source:
            widgets = [w for w in widgets if w.source == source]
        return widgets

    def _generate_instance_id(self) -> str:
        """Generate unique instance ID."""
        import uuid
        return str(uuid.uuid4())
```

### Task 3.3: Connect Plugin Widgets on Activation
**Location**: `core/plugin_system/plugin_loader.py`
**Priority**: MEDIUM

Update activate_plugin method:
```python
def activate_plugin(self, plugin_id: str) -> bool:
    """Activate a plugin."""
    # ... existing code ...

    # After plugin.activate(context)

    # Register plugin widgets if it has any
    if hasattr(plugin_info.instance, 'get_widgets'):
        plugin_service = self.services.get('plugin_service')
        if plugin_service:
            for widget in plugin_info.instance.get_widgets():
                plugin_service.register_widget(widget)

    # ... rest of existing code ...
```

## Phase 4: Complete Integration - 2 Hours

### Task 4.1: Initialize Plugin System Properly
**Location**: `main.py`
**Priority**: LOW

Add after window creation:
```python
def initialize_plugins(window):
    """Initialize plugin system after main window is ready."""
    try:
        # Get services from window
        service_locator = window.service_locator

        # Get plugin service
        plugin_service = service_locator.get(PluginService)
        if plugin_service:
            plugin_manager = plugin_service.get_plugin_manager()
            if plugin_manager:
                # Create widget bridge
                from core.plugin_system.widget_bridge import PluginWidgetBridge
                workspace_service = service_locator.get(WorkspaceService)
                widget_bridge = PluginWidgetBridge(workspace_service)

                # Connect to plugin service
                plugin_service._widget_bridge = widget_bridge

                # Activate plugins
                for plugin_id in plugin_manager.get_loaded_plugins():
                    plugin_manager.activate_plugin(plugin_id)

                logger.info("Plugin system fully initialized")
    except Exception as e:
        logger.error(f"Failed to initialize plugins: {e}")
```

### Task 4.2: Complete Service Adapter Implementation
**Location**: `core/plugin_system/service_adapters.py`
**Priority**: LOW

Complete remaining stub methods:
```python
# ConfigurationServiceAdapter
def on_change(self, key: str, callback: callable) -> None:
    """Subscribe to configuration changes."""
    # Connect to settings service signal
    self.settings_service.setting_changed.connect(
        lambda k, v: callback(v) if k == key else None
    )

# WorkspaceServiceAdapter
def create_pane(self, widget: Any, position: str) -> None:
    """Create new pane with widget."""
    if self.workspace_service and hasattr(self.workspace_service, 'workspace'):
        workspace = self.workspace_service.workspace
        # Implementation depends on workspace structure
        if hasattr(workspace, 'split_pane'):
            workspace.split_pane(widget, position)

def get_active_editor(self) -> Optional[Any]:
    """Return active editor widget."""
    if self.workspace_service and hasattr(self.workspace_service, 'get_active_widget'):
        widget = self.workspace_service.get_active_widget()
        if widget and hasattr(widget, 'widget_type'):
            if widget.widget_type == WidgetType.EDITOR:
                return widget
    return None
```

## Phase 5: Testing and Validation - 2 Hours

### Task 5.1: Create Integration Tests
**Location**: `tests/integration/test_plugin_integration.py`
**Priority**: MEDIUM

```python
def test_plugin_widget_registration():
    """Test that plugin widgets can be registered and created."""
    # Create services
    workspace_service = WorkspaceService()
    plugin_service = PluginService()

    # Create mock plugin widget
    mock_widget = Mock(spec=IWidget)
    mock_widget.get_widget_id.return_value = "test_widget"

    # Register widget
    plugin_service.register_widget(mock_widget)

    # Verify registration
    assert "test_widget" in workspace_service.get_widget_factories()

def test_plugin_command_registration():
    """Test that plugin commands are registered in command registry."""
    from core.commands.registry import command_registry

    # Register plugin command
    adapter = CommandServiceAdapter(None)
    adapter.register_command("plugin.test", lambda x: "result")

    # Verify registration
    command = command_registry.get_command("plugin.test")
    assert command is not None
    assert command.id == "plugin.test"
```

### Task 5.2: Architecture Validation Tests
**Location**: `tests/architecture/test_boundaries.py`
**Priority**: LOW

```python
import ast
import glob

def test_no_plugin_imports_in_core():
    """Ensure core doesn't import from plugins."""
    core_files = glob.glob('ui/**/*.py', recursive=True)
    core_files += glob.glob('services/**/*.py', recursive=True)

    for file_path in core_files:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        assert not name.name.startswith('packages.')
                        assert not name.name.startswith('viloxterm')
                        assert not name.name.startswith('viloedit')

def test_plugins_use_sdk_only():
    """Ensure plugins only use SDK interfaces."""
    plugin_files = glob.glob('packages/*/src/**/*.py', recursive=True)

    for file_path in plugin_files:
        with open(file_path, 'r') as f:
            content = f.read()
            # Plugins should only import from viloapp_sdk
            assert 'from ui.' not in content
            assert 'from services.' not in content
            assert 'from core.' not in content or 'from core.plugin_system' in content
```

## Implementation Timeline

### Day 1: Critical Fixes (2 hours)
- [ ] Task 1.1: Fix Command class @dataclass
- [ ] Task 1.2: Create PluginService wrapper
- [ ] Task 1.3: Fix service registration

### Day 2: Basic Functionality (4 hours)
- [ ] Task 2.1: Implement CommandServiceAdapter
- [ ] Task 2.2: Add widget registration to WorkspaceService
- [ ] Task 2.3: Create Plugin-Widget Bridge

### Day 3: Architecture Cleanup (3 hours)
- [ ] Task 3.1: Update Split Pane Model
- [ ] Task 3.2: Implement AppWidgetManager
- [ ] Task 3.3: Connect plugin widgets on activation

### Day 4: Integration (2 hours)
- [ ] Task 4.1: Initialize plugin system properly
- [ ] Task 4.2: Complete service adapter implementation

### Day 5: Testing (2 hours)
- [ ] Task 5.1: Create integration tests
- [ ] Task 5.2: Architecture validation tests

## Success Criteria

### Functional Requirements
- ✅ Application starts without crashes
- ✅ Plugin commands appear in command palette
- ✅ Plugin widgets can be created
- ✅ Plugin configuration works
- ✅ Plugin events are handled

### Architecture Requirements
- ✅ Clear separation between core and plugins
- ✅ No direct imports between core and plugins
- ✅ All interaction through SDK interfaces
- ✅ Plugin system is not a service
- ✅ Widgets use factory pattern

### Quality Requirements
- ✅ All tests passing
- ✅ No duplicate widget implementations
- ✅ Service adapters fully implemented
- ✅ Documentation updated
- ✅ Code follows project conventions

## Risk Mitigation

### High Risk Items
1. **Breaking existing functionality**
   - Keep legacy widgets as fallback
   - Test thoroughly before removing old code
   - Use feature flags if needed

2. **Command registration conflicts**
   - Namespace plugin commands properly
   - Check for duplicates before registering
   - Log all registrations for debugging

3. **Widget adapter complexity**
   - Start with simple pass-through adapter
   - Add features incrementally
   - Test each widget type separately

## Conclusion

This updated plan addresses all issues found in the audit:
1. **Immediate crashes** will be fixed first
2. **Missing implementations** will be completed
3. **Architectural violations** will be corrected
4. **Integration gaps** will be bridged
5. **Testing** will validate everything works

Total estimated time: **13 hours** of focused development to have a fully functional plugin system.