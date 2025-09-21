# ViloxTerm Plugin Architecture

## Table of Contents
1. [Overview](#overview)
2. [Architecture Components](#architecture-components)
3. [Plugin Discovery](#plugin-discovery)
4. [Plugin Lifecycle](#plugin-lifecycle)
5. [Service Architecture](#service-architecture)
6. [Widget Integration](#widget-integration)
7. [Security Model](#security-model)
8. [Event System](#event-system)
9. [PySide6/Qt Integration](#pyside6qt-integration)
10. [Data Management](#data-management)
11. [Development Features](#development-features)

## Overview

The ViloxTerm plugin system provides a robust, secure, and extensible architecture for extending the application's functionality. Built on top of PySide6 and Python's dynamic loading capabilities, it enables developers to create plugins that seamlessly integrate with the core application.

### Design Principles

- **Isolation**: Plugins run in controlled environments with defined permissions
- **Extensibility**: Clear interfaces for adding new functionality
- **Hot Reload**: Development-friendly with live code updates
- **Type Safety**: Strong typing through SDK interfaces
- **Qt Integration**: Native PySide6 widget support

## Architecture Components

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                     ViloxTerm Core                       │
├─────────────────────────────────────────────────────────┤
│                    Plugin Manager                        │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │  Discovery  │ │    Loader    │ │    Registry     │  │
│  └─────────────┘ └──────────────┘ └─────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                  Service Layer                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ServiceProxy → Adapted Services → Core Services │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                  Widget Bridge                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  IWidget → PluginAppWidgetAdapter → AppWidget    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

- **PluginManager** (`plugin_manager.py`): Orchestrates all plugin operations
- **PluginDiscovery** (`plugin_discovery.py`): Finds plugins from various sources
- **PluginLoader** (`plugin_loader.py`): Loads and instantiates plugin modules
- **PluginRegistry** (`plugin_registry.py`): Maintains plugin metadata and state
- **DependencyResolver** (`dependency_resolver.py`): Resolves plugin dependencies
- **PluginWidgetBridge** (`widget_bridge.py`): Adapts plugin widgets to core UI

## Plugin Discovery

### Discovery Sources (Priority Order)

1. **Python Entry Points** (Highest Priority)
   ```python
   # pyproject.toml
   [project.entry-points."viloapp.plugins"]
   terminal = "viloxterm.plugin:TerminalPlugin"
   ```
   - Standard Python packaging mechanism
   - Discovered via `importlib.metadata.entry_points()`
   - Group name: `viloapp.plugins`

2. **Local Packages Directory** (Development)
   ```
   /home/kuja/GitHub/viloapp/packages/
   ├── viloxterm/
   │   ├── plugin.json
   │   └── src/viloxterm/plugin.py
   └── viloedit/
       ├── plugin.json
       └── src/viloedit/plugin.py
   ```
   - Auto-discovered relative to plugin system location
   - Fallback: `VILOAPP_ROOT` environment variable

3. **User Plugin Directory**
   ```
   ~/.local/share/ViloxTerm/plugins/
   ```
   - Platform-specific via `platformdirs.user_data_dir()`

4. **System Plugin Directory**
   ```
   /usr/share/ViloxTerm/plugins/  # Linux
   C:\ProgramData\ViloxTerm\plugins\  # Windows
   ```
   - Platform-specific via `platformdirs.site_data_dir()`

5. **Built-in Plugins** (Lowest Priority)
   - Hardcoded in `_load_builtin_plugin()`
   - Examples: `core-commands`, `core-themes`

### Discovery Methods

#### Manifest-based Discovery (`plugin.json`)
```json
{
  "id": "terminal",
  "name": "ViloxTerm Terminal",
  "version": "1.0.0",
  "main": "src/viloxterm/plugin.py",
  "entry_point": "viloxterm.plugin:TerminalPlugin",
  "activation_events": ["onCommand:terminal.new", "onStartup"],
  "contributes": {
    "widgets": [{"id": "terminal", "factory": "viloxterm.widget:TerminalWidgetFactory"}],
    "commands": [{"id": "terminal.new", "title": "New Terminal"}],
    "keybindings": [{"command": "terminal.new", "key": "ctrl+shift+`"}]
  }
}
```

#### Python Module Discovery
- Looks for `__plugin__.py` marker files
- Searches for classes ending with `Plugin`
- Must implement `IPlugin` interface

## Plugin Lifecycle

### Lifecycle States

```
DISCOVERED → LOADED → ACTIVATED → DEACTIVATED → UNLOADED
     ↓         ↓          ↓            ↓            ↓
   FAILED   FAILED     FAILED       FAILED       FAILED
```

### State Transitions

1. **DISCOVERED**: Plugin found but not loaded
   - Metadata available from manifest
   - No code executed yet

2. **LOADED**: Module imported, class instantiated
   ```python
   # PluginLoader._load_plugin_module()
   module = importlib.import_module(f"{package_name}.plugin")
   plugin_class = self._find_plugin_class(module)
   plugin_instance = plugin_class()
   ```

3. **ACTIVATED**: Plugin running and registered
   ```python
   # Plugin receives context and starts
   context = self._create_plugin_context(plugin_info)
   plugin_instance.activate(context)
   ```

4. **DEACTIVATED**: Plugin stopped but still loaded
   ```python
   plugin_instance.deactivate()
   # Cleanup resources, unregister handlers
   ```

5. **UNLOADED**: Module removed from memory
   ```python
   del sys.modules[module_name]
   ```

### Activation Events

Plugins can be activated by:
- `onStartup`: Application start
- `onCommand:*`: Command execution
- `onView:*`: View activation
- `onLanguage:*`: File type opened
- `workspaceContains:*`: File pattern in workspace

## Service Architecture

### Service Proxy System

The `ServiceProxyImpl` provides controlled access to core services:

```python
class ServiceProxyImpl(ServiceProxy):
    def __init__(self, services: Dict[str, Any]):
        self._services = services
        self._permission_manager = PermissionManager()

    def get_service(self, service_id: str) -> Optional[IService]:
        # Check permissions before returning service
        if self._has_permission(service_id):
            return ServiceAdapter(self._services[service_id])
        return None
```

### Available Services

| Service ID | Description | Methods |
|------------|-------------|---------|
| `workspace` | Widget management | `add_widget()`, `remove_widget()`, `get_active_widget()` |
| `command` | Command registration | `register_command()`, `execute_command()` |
| `ui` | UI state management | `show_notification()`, `get_theme()` |
| `terminal` | Terminal operations | `create_terminal()`, `send_text()` |
| `editor` | Editor operations | `open_file()`, `save_file()` |
| `settings` | Configuration | `get()`, `set()`, `save()` |
| `theme` | Theme management | `get_current_theme()`, `apply_theme()` |

### Service Adapters

Adapters wrap core services to enforce permissions:

```python
class WorkspaceServiceAdapter:
    def register_widget_factory(self, widget_id: str, factory):
        # Check UI write permission
        if self._check_permission(PermissionCategory.UI, PermissionScope.WRITE):
            self._workspace_service.register_widget_factory(widget_id, factory)
```

## Widget Integration

### Widget Bridge Architecture

```python
# Plugin provides IWidget implementation
class TerminalWidgetFactory(IWidget):
    def create_instance(self, instance_id: str) -> QWidget:
        return TerminalWidget()

# Bridge adapts to core AppWidget
class PluginAppWidgetAdapter(AppWidget):
    def __init__(self, plugin_widget, qt_widget, instance_id):
        super().__init__(instance_id, self._determine_widget_type())
        self.plugin_widget = plugin_widget
        self.qt_widget = qt_widget

        # Embed Qt widget
        layout = QVBoxLayout(self)
        layout.addWidget(self.qt_widget)
```

### Widget Registration Flow

1. Plugin declares widget in manifest
2. `PluginWidgetBridge.register_plugin_widget()` called
3. Factory registered with `WorkspaceService`
4. Core UI creates instances via factory
5. Adapter wraps plugin widget as `AppWidget`

### Widget Lifecycle Management

- **Creation**: Via factory pattern with unique instance IDs
- **State Management**: `get_state()` / `restore_state()`
- **Cleanup**: `destroy_instance()` called on removal
- **Parent-Child**: Qt parent hierarchy maintained

## Security Model

### Permission System

#### Permission Categories
- `FILESYSTEM`: File system access
- `NETWORK`: Network operations
- `SYSTEM`: System operations
- `UI`: User interface manipulation

#### Permission Scopes
- `READ`: Read access
- `WRITE`: Write/modify access
- `EXECUTE`: Execute operations

#### Permission Definition
```python
Permission(
    category=PermissionCategory.FILESYSTEM,
    scope=PermissionScope.READ,
    resource="/home/*"  # Wildcard support
)
```

### Permission Checking

```python
class PermissionManager:
    def can_access(self, plugin_id: str, category, scope, resource) -> bool:
        plugin_permissions = self._plugin_permissions.get(plugin_id, set())
        for permission in plugin_permissions:
            if (permission.category == category and
                permission.scope == scope and
                permission.matches_resource(resource)):
                return True
        return False
```

### Resource Monitoring

- CPU usage limits
- Memory allocation tracking
- File handle limits
- Network connection limits

## Event System

### Event Bus Architecture

```python
class EventBus:
    def emit(self, event: PluginEvent):
        for handler in self._handlers.get(event.type, []):
            handler(event)

    def subscribe(self, event_type: EventType, handler, subscriber_id: str):
        self._handlers[event_type].append(handler)
```

### Event Types

- `PLUGIN_ACTIVATED`: Plugin activated
- `PLUGIN_DEACTIVATED`: Plugin deactivated
- `THEME_CHANGED`: Theme changed
- `SETTINGS_CHANGED`: Settings modified
- `COMMAND_EXECUTED`: Command executed
- `WIDGET_CREATED`: Widget created
- `WIDGET_DESTROYED`: Widget destroyed

### Event Flow

1. Plugin subscribes to events via context
2. Core or other plugins emit events
3. Event bus dispatches to subscribers
4. Handlers execute in plugin context

## PySide6/Qt Integration

### Thread Safety

All plugin UI operations must occur on the Qt main thread:

```python
from PySide6.QtCore import QMetaObject, Qt

def thread_safe_operation(widget, method):
    QMetaObject.invokeMethod(
        widget, method,
        Qt.ConnectionType.QueuedConnection
    )
```

### Signal/Slot Connections

Plugins can use Qt signals across boundaries:

```python
class TerminalWidget(QWidget):
    session_started = Signal(str)

    def start_terminal(self):
        self.session_started.emit(self.session_id)
```

### Widget Parent Hierarchy

```python
# Proper parent-child relationship
class PluginAppWidgetAdapter(AppWidget):
    def __init__(self, plugin_widget, parent=None):
        super().__init__(parent)  # Set Qt parent
        self.qt_widget = plugin_widget.create_instance()
        self.qt_widget.setParent(self)  # Ensure proper hierarchy
```

### Event Filter Installation

Plugins can install event filters safely:

```python
def activate(self, context):
    main_window = context.get_service("ui").get_main_window()
    if main_window:
        main_window.installEventFilter(self.event_filter)
```

## Data Management

### Plugin Data Directory

Each plugin gets an isolated data directory:

```python
data_path = Path(platformdirs.user_data_dir("ViloxTerm")) / "plugins" / plugin_id
# ~/.local/share/ViloxTerm/plugins/terminal/
```

### Configuration Storage

```python
# Plugin configuration path
config_path = data_path / "config.json"

# Settings integration
config_service.get(f"plugins.{plugin_id}")
config_service.set(f"plugins.{plugin_id}.setting", value)
```

### State Persistence

```python
class PluginState:
    def save_state(self, state: Dict[str, Any]):
        state_file = self.data_path / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f)

    def load_state(self) -> Dict[str, Any]:
        state_file = self.data_path / "state.json"
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {}
```

## Development Features

### Hot Reload System

Located in `development/hot_reload.py`:

```python
class PluginReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if self._should_watch_file(event.src_path):
            self._trigger_reload(event.src_path)
```

Watched files:
- `*.py` Python sources
- `plugin.json` manifest
- `*.ui` Qt Designer files

### Debug Mode

Enable with environment variable:
```bash
VILOAPP_DEBUG=1 viloapp
```

Features:
- Verbose logging
- Stack traces for plugin errors
- Performance profiling
- Resource usage monitoring

### Development Paths

```python
# Check for development mode
if "VILOAPP_ROOT" in os.environ:
    packages_dir = Path(os.environ["VILOAPP_ROOT"]) / "packages"
else:
    # Use relative path from plugin system
    packages_dir = Path(__file__).parent.parent.parent / "packages"
```

## Performance Considerations

### Lazy Loading

Plugins are loaded only when needed:
- Activation events trigger loading
- Dependencies loaded on demand
- UI components created when displayed

### Resource Limits

```python
class ResourceMonitor:
    MAX_MEMORY = 100 * 1024 * 1024  # 100MB per plugin
    MAX_CPU_PERCENT = 25  # 25% CPU usage
    MAX_FILE_HANDLES = 50
```

### Cleanup Strategies

```python
def cleanup(self):
    # Close file handles
    for handle in self.file_handles:
        handle.close()

    # Clear caches
    self.cache.clear()

    # Disconnect signals
    for connection in self.connections:
        connection.disconnect()

    # Delete widgets
    for widget in self.widgets:
        widget.deleteLater()
```

## Error Handling

### Plugin Isolation

```python
try:
    plugin.activate(context)
except Exception as e:
    logger.error(f"Plugin {plugin_id} failed: {e}")
    registry.update_state(plugin_id, LifecycleState.FAILED)
    registry.set_error(plugin_id, str(e))
    # Plugin failure doesn't crash the app
```

### Recovery Mechanisms

1. **Automatic retry**: Failed plugins retry after delay
2. **Graceful degradation**: Missing dependencies handled
3. **Fallback options**: Default implementations available
4. **User notification**: Non-intrusive error messages

## Plugin Communication

### Direct Communication

Plugins can communicate via event bus:

```python
# Plugin A emits
context.emit_event(EventType.CUSTOM, {"data": "value"})

# Plugin B subscribes
context.subscribe_event(EventType.CUSTOM, self.handle_event)
```

### Service-mediated Communication

Through shared services:

```python
# Plugin A registers service
workspace_service.register_widget_factory("my_widget", factory)

# Plugin B uses service
workspace_service.create_widget("my_widget")
```

## Summary

The ViloxTerm plugin architecture provides a robust foundation for extending the application while maintaining stability, security, and performance. The combination of Python's dynamic capabilities with PySide6's powerful UI framework enables rich plugin development with proper isolation and resource management.