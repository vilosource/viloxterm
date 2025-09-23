# API Specifications for Capability-Based Architecture

**Date**: 2025-01-23
**Phase**: 1.3 - API Design Specifications
**Status**: COMPLETE

## Executive Summary

Complete API specifications for the capability-based architecture, defining interfaces and contracts for **Widget-to-Platform**, **Platform-to-Widget**, and **Service Discovery** interactions. These APIs enable clean separation of concerns and plugin extensibility.

## 🔧 Core API Contracts

### 1. Widget-to-Platform API

#### ICapabilityProvider Interface
```python
from abc import ABC, abstractmethod
from typing import Set, Optional, Dict, Any, Callable
from enum import Enum

class ICapabilityProvider(ABC):
    """Core interface for widgets that provide capabilities to the platform."""

    @abstractmethod
    def get_capabilities(self) -> Set[WidgetCapability]:
        """
        Return set of capabilities this widget provides.

        Returns:
            Set[WidgetCapability]: All capabilities supported by this widget

        Example:
            return {
                WidgetCapability.TEXT_EDITING,
                WidgetCapability.FILE_SAVING,
                WidgetCapability.SYNTAX_HIGHLIGHTING
            }
        """
        pass

    @abstractmethod
    def execute_capability(self, capability: WidgetCapability, **kwargs) -> Any:
        """
        Execute a specific capability with given parameters.

        Args:
            capability: The capability to execute
            **kwargs: Parameters for the capability execution

        Returns:
            Any: Result of capability execution

        Raises:
            CapabilityNotSupportedError: If capability is not supported
            CapabilityExecutionError: If execution fails
        """
        pass

    @abstractmethod
    def supports_capability(self, capability: WidgetCapability) -> bool:
        """
        Check if widget supports a specific capability.

        Args:
            capability: The capability to check

        Returns:
            bool: True if capability is supported
        """
        pass

    def get_capability_metadata(self, capability: WidgetCapability) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific capability.

        Args:
            capability: The capability to get metadata for

        Returns:
            Optional[Dict[str, Any]]: Metadata dict or None if not supported

        Example metadata:
            {
                "description": "Save current file to disk",
                "parameters": {
                    "file_path": {"type": "str", "required": False},
                    "encoding": {"type": "str", "default": "utf-8"}
                },
                "returns": {"type": "bool", "description": "True if save succeeded"}
            }
        """
        return None

    def get_capability_keybindings(self) -> Dict[WidgetCapability, List[str]]:
        """
        Get recommended keybindings for capabilities.

        Returns:
            Dict[WidgetCapability, List[str]]: Mapping of capabilities to key combinations

        Example:
            {
                WidgetCapability.FILE_SAVING: ["Ctrl+S"],
                WidgetCapability.CLIPBOARD_COPY: ["Ctrl+C", "Ctrl+Shift+C"],
            }
        """
        return {}
```

#### IWidgetLifecycle Interface
```python
class IWidgetLifecycle(ABC):
    """Interface for widget lifecycle management."""

    @abstractmethod
    def on_widget_created(self, widget_id: str, context: Dict[str, Any]):
        """Called when widget is created."""
        pass

    @abstractmethod
    def on_widget_activated(self, widget_id: str):
        """Called when widget becomes active."""
        pass

    @abstractmethod
    def on_widget_deactivated(self, widget_id: str):
        """Called when widget loses focus."""
        pass

    @abstractmethod
    def on_widget_destroyed(self, widget_id: str):
        """Called when widget is destroyed."""
        pass

    def on_widget_settings_changed(self, widget_id: str, settings: Dict[str, Any]):
        """Called when widget settings change."""
        pass
```

### 2. Platform-to-Widget API

#### IPlatformHost Interface
```python
class IPlatformHost(ABC):
    """Interface provided by platform to widgets."""

    @abstractmethod
    def get_service_registry(self) -> 'ServiceRegistry':
        """
        Get the platform service registry.

        Returns:
            ServiceRegistry: Platform service registry
        """
        pass

    @abstractmethod
    def get_configuration(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value from platform.

        Args:
            key: Configuration key (e.g., "editor.font.size")
            default: Default value if key not found

        Returns:
            Any: Configuration value
        """
        pass

    @abstractmethod
    def set_configuration(self, key: str, value: Any):
        """
        Set configuration value in platform.

        Args:
            key: Configuration key
            value: Value to set
        """
        pass

    @abstractmethod
    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """
        Emit event to platform event system.

        Args:
            event_type: Type of event (e.g., "widget.focus_changed")
            data: Event data
        """
        pass

    @abstractmethod
    def request_command_execution(self, command_id: str, **kwargs) -> Any:
        """
        Request platform to execute a command.

        Args:
            command_id: ID of command to execute
            **kwargs: Command parameters

        Returns:
            Any: Command execution result
        """
        pass

    @abstractmethod
    def register_widget_command(self, command_id: str, handler: Callable, metadata: Dict[str, Any]):
        """
        Register a widget-specific command with platform.

        Args:
            command_id: Unique command identifier
            handler: Command handler function
            metadata: Command metadata (title, description, etc.)
        """
        pass
```

#### IWidgetContext Interface
```python
class IWidgetContext(ABC):
    """Context provided to widgets during creation."""

    @abstractmethod
    def get_widget_id(self) -> str:
        """Get unique widget instance ID."""
        pass

    @abstractmethod
    def get_widget_type(self) -> str:
        """Get widget type identifier."""
        pass

    @abstractmethod
    def get_platform_host(self) -> IPlatformHost:
        """Get platform host interface."""
        pass

    @abstractmethod
    def get_initial_data(self) -> Dict[str, Any]:
        """Get initial data for widget creation."""
        pass

    @abstractmethod
    def get_parent_widget(self) -> Optional['ICapabilityProvider']:
        """Get parent widget if this is a child widget."""
        pass
```

### 3. Service Discovery API

#### IPlatformService Interface
```python
class IPlatformService(ABC):
    """Base interface for all platform services."""

    @abstractmethod
    def get_service_id(self) -> str:
        """
        Get unique service identifier.

        Returns:
            str: Unique service ID (e.g., "clipboard", "terminal_server")
        """
        pass

    @abstractmethod
    def get_service_version(self) -> str:
        """
        Get service version.

        Returns:
            str: Service version in semver format
        """
        pass

    @abstractmethod
    def get_service_interfaces(self) -> List[type]:
        """
        Get list of interfaces this service implements.

        Returns:
            List[type]: Interface classes this service implements
        """
        pass

    def is_service_available(self) -> bool:
        """
        Check if service is currently available.

        Returns:
            bool: True if service is operational
        """
        return True
```

#### Specific Service Interfaces

```python
# Clipboard Service
class IClipboardService(IPlatformService):
    """Platform clipboard service interface."""

    @abstractmethod
    def get_text(self) -> str:
        """Get text from clipboard."""
        pass

    @abstractmethod
    def set_text(self, text: str):
        """Set text to clipboard."""
        pass

    @abstractmethod
    def get_image(self) -> Optional[bytes]:
        """Get image from clipboard."""
        pass

    @abstractmethod
    def set_image(self, image_data: bytes, format: str = "PNG"):
        """Set image to clipboard."""
        pass

# File System Service
class IFileSystemService(IPlatformService):
    """Platform file system service interface."""

    @abstractmethod
    def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file content."""
        pass

    @abstractmethod
    def write_file(self, path: str, content: str, encoding: str = "utf-8"):
        """Write file content."""
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        pass

    @abstractmethod
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file metadata."""
        pass

    @abstractmethod
    def watch_file(self, path: str, callback: Callable[[str, str], None]):
        """Watch file for changes."""
        pass

# Terminal Server Service
class ITerminalServerService(IPlatformService):
    """Platform terminal server service interface."""

    @abstractmethod
    def create_terminal(self, config: Dict[str, Any]) -> str:
        """Create new terminal session."""
        pass

    @abstractmethod
    def destroy_terminal(self, terminal_id: str):
        """Destroy terminal session."""
        pass

    @abstractmethod
    def write_to_terminal(self, terminal_id: str, data: str):
        """Write data to terminal."""
        pass

    @abstractmethod
    def resize_terminal(self, terminal_id: str, rows: int, cols: int):
        """Resize terminal."""
        pass

    @abstractmethod
    def set_terminal_callback(self, terminal_id: str, callback: Callable[[str], None]):
        """Set callback for terminal output."""
        pass
```

#### ServiceRegistry Implementation
```python
class ServiceRegistry:
    """Registry for platform services with dependency injection."""

    def __init__(self):
        self._services: Dict[str, IPlatformService] = {}
        self._interface_map: Dict[type, List[str]] = {}
        self._service_dependencies: Dict[str, List[str]] = {}

    def register_service(self, service: IPlatformService, dependencies: List[str] = None):
        """
        Register a platform service.

        Args:
            service: Service instance to register
            dependencies: List of service IDs this service depends on
        """
        service_id = service.get_service_id()
        interfaces = service.get_service_interfaces()

        self._services[service_id] = service
        self._service_dependencies[service_id] = dependencies or []

        # Map interfaces to service IDs
        for interface in interfaces:
            if interface not in self._interface_map:
                self._interface_map[interface] = []
            self._interface_map[interface].append(service_id)

    def get_service(self, service_id: str) -> Optional[IPlatformService]:
        """Get service by ID."""
        return self._services.get(service_id)

    def get_service_by_interface(self, interface: type) -> Optional[IPlatformService]:
        """Get first service implementing interface."""
        service_ids = self._interface_map.get(interface, [])
        return self._services.get(service_ids[0]) if service_ids else None

    def get_services_by_interface(self, interface: type) -> List[IPlatformService]:
        """Get all services implementing interface."""
        service_ids = self._interface_map.get(interface, [])
        return [self._services[sid] for sid in service_ids if sid in self._services]

    def inject_services(self, widget: 'IServiceConsumer'):
        """
        Inject required services into widget.

        Args:
            widget: Widget that consumes services
        """
        widget.set_service_registry(self)

        # Auto-inject required services if widget implements injection interface
        if hasattr(widget, 'inject_service'):
            for interface in widget.get_required_services():
                service = self.get_service_by_interface(interface)
                if service:
                    widget.inject_service(interface, service)
```

### 4. Event System API

#### IEventBus Interface
```python
class IEventBus(ABC):
    """Platform event bus interface."""

    @abstractmethod
    def emit(self, event_type: str, data: Dict[str, Any], source: str = None):
        """Emit event to all subscribers."""
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Subscribe to event type."""
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Unsubscribe from event type."""
        pass

# Standard Event Types
class PlatformEvents:
    """Standard platform event types."""

    WIDGET_CREATED = "platform.widget.created"
    WIDGET_DESTROYED = "platform.widget.destroyed"
    WIDGET_ACTIVATED = "platform.widget.activated"
    WIDGET_DEACTIVATED = "platform.widget.deactivated"

    TAB_CREATED = "platform.tab.created"
    TAB_CLOSED = "platform.tab.closed"
    TAB_SWITCHED = "platform.tab.switched"

    COMMAND_EXECUTED = "platform.command.executed"
    COMMAND_FAILED = "platform.command.failed"

    SERVICE_REGISTERED = "platform.service.registered"
    SERVICE_UNREGISTERED = "platform.service.unregistered"
```

## 🔄 Usage Examples

### Widget Implementation Example
```python
class TerminalWidget(AppWidget, ICapabilityProvider, IServiceConsumer, IWidgetLifecycle):
    """Example terminal widget implementation."""

    def __init__(self, context: IWidgetContext):
        super().__init__()
        self.context = context
        self.platform_host = context.get_platform_host()
        self.service_registry = self.platform_host.get_service_registry()

        # Get required services
        self.clipboard_service = self.service_registry.get_service_by_interface(IClipboardService)
        self.terminal_server = self.service_registry.get_service_by_interface(ITerminalServerService)

        # Widget state
        self.terminal_id = None

    # === Capability Provider Implementation ===

    def get_capabilities(self) -> Set[WidgetCapability]:
        return {
            WidgetCapability.SHELL_EXECUTION,
            WidgetCapability.TEXT_INPUT,
            WidgetCapability.CLIPBOARD_COPY,
            WidgetCapability.CLIPBOARD_PASTE,
            WidgetCapability.CLEAR_DISPLAY,
        }

    def execute_capability(self, capability: WidgetCapability, **kwargs) -> Any:
        handlers = {
            WidgetCapability.CLEAR_DISPLAY: self._handle_clear_display,
            WidgetCapability.CLIPBOARD_COPY: self._handle_clipboard_copy,
            WidgetCapability.CLIPBOARD_PASTE: self._handle_clipboard_paste,
        }

        handler = handlers.get(capability)
        if not handler:
            raise CapabilityNotSupportedError(f"Capability {capability} not supported")

        return handler(**kwargs)

    def supports_capability(self, capability: WidgetCapability) -> bool:
        return capability in self.get_capabilities()

    # === Service Consumer Implementation ===

    def set_service_registry(self, registry: ServiceRegistry):
        self.service_registry = registry

    def get_required_services(self) -> List[type]:
        return [IClipboardService, ITerminalServerService]

    # === Lifecycle Implementation ===

    def on_widget_created(self, widget_id: str, context: Dict[str, Any]):
        # Create terminal session
        if self.terminal_server:
            self.terminal_id = self.terminal_server.create_terminal({
                "shell": context.get("shell", "/bin/bash"),
                "cwd": context.get("cwd", "~")
            })

    def on_widget_destroyed(self, widget_id: str):
        # Clean up terminal session
        if self.terminal_server and self.terminal_id:
            self.terminal_server.destroy_terminal(self.terminal_id)

    # === Capability Handlers ===

    def _handle_clear_display(self, **kwargs) -> bool:
        """Clear terminal display."""
        if self.terminal_server and self.terminal_id:
            self.terminal_server.write_to_terminal(self.terminal_id, "\033[2J\033[H")
            return True
        return False

    def _handle_clipboard_copy(self, **kwargs) -> bool:
        """Copy selected text to clipboard."""
        selected_text = self.get_selected_text()
        if selected_text and self.clipboard_service:
            self.clipboard_service.set_text(selected_text)
            return True
        return False

    def _handle_clipboard_paste(self, **kwargs) -> bool:
        """Paste clipboard text to terminal."""
        if self.clipboard_service and self.terminal_server and self.terminal_id:
            text = self.clipboard_service.get_text()
            if text:
                self.terminal_server.write_to_terminal(self.terminal_id, text)
                return True
        return False
```

### Command Registration Example
```python
def register_capability_commands(command_registry: CommandRegistry):
    """Register commands that use capability system."""

    # Clear command - works on any widget with CLEAR_DISPLAY capability
    command_registry.register_capability_command(CapabilityCommand(
        id="platform.clear",
        title="Clear Display",
        capability_required=WidgetCapability.CLEAR_DISPLAY,
        target_preference="active",
        keybinding="Ctrl+L"
    ))

    # Copy command - works on any widget with CLIPBOARD_COPY capability
    command_registry.register_capability_command(CapabilityCommand(
        id="platform.copy",
        title="Copy",
        capability_required=WidgetCapability.CLIPBOARD_COPY,
        target_preference="active",
        keybinding="Ctrl+C"
    ))

    # Save command - works on any widget with FILE_SAVING capability
    command_registry.register_capability_command(CapabilityCommand(
        id="platform.save",
        title="Save",
        capability_required=WidgetCapability.FILE_SAVING,
        target_preference="active",
        keybinding="Ctrl+S",
        fallback_behavior=lambda ctx: CommandResult(
            status=CommandStatus.NOT_APPLICABLE,
            message="No saveable content in active widget"
        )
    ))
```

## 📋 API Validation

### Interface Compliance Testing
```python
class CapabilityProviderTest:
    """Test widget capability provider implementation."""

    def test_capability_provider_compliance(self, widget: ICapabilityProvider):
        """Test widget implements capability provider correctly."""

        # Test capability enumeration
        capabilities = widget.get_capabilities()
        assert isinstance(capabilities, set)
        assert all(isinstance(cap, WidgetCapability) for cap in capabilities)

        # Test capability support checking
        for capability in capabilities:
            assert widget.supports_capability(capability)

        # Test capability execution for each declared capability
        for capability in capabilities:
            # This should not raise CapabilityNotSupportedError
            try:
                widget.execute_capability(capability)
            except CapabilityExecutionError:
                pass  # Execution errors are OK, support errors are not

    def test_service_consumer_compliance(self, widget: IServiceConsumer):
        """Test widget implements service consumer correctly."""

        # Test service registry injection
        registry = ServiceRegistry()
        widget.set_service_registry(registry)

        # Test required services declaration
        required_services = widget.get_required_services()
        assert isinstance(required_services, list)
        assert all(isinstance(svc, type) for svc in required_services)
```

---

**Status**: COMPLETE ✅
**Next**: Task 1.4 - Create Backward Compatibility Strategy
**Key Achievement**: Complete API specifications enable clean widget-platform separation with service discovery and capability-based interactions.