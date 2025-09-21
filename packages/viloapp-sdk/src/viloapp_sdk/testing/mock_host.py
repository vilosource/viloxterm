"""Mock plugin host for testing plugins."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable
from unittest.mock import Mock, MagicMock
import tempfile
import shutil

from ..context import IPluginContext, PluginContext
from ..service import (
    IService, ServiceProxy, ServiceNotAvailableError,
    ICommandService, IConfigurationService, IWorkspaceService,
    IThemeService, INotificationService
)
from ..events import EventBus, PluginEvent, EventType, EventPriority

T = TypeVar('T', bound=IService)

class MockService(IService):
    """Base mock service implementation."""

    def __init__(self, service_id: str, version: str = "1.0.0"):
        self._service_id = service_id
        self._version = version
        self.mock = Mock()

    def get_service_id(self) -> str:
        return self._service_id

    def get_service_version(self) -> str:
        return self._version

class MockCommandService(MockService, ICommandService):
    """Mock implementation of command service."""

    def __init__(self):
        super().__init__("command", "1.0.0")
        self._commands: Dict[str, Callable] = {}

    def execute_command(self, command_id: str, **kwargs) -> Any:
        """Execute a command or return mock result."""
        if command_id in self._commands:
            return self._commands[command_id](**kwargs)
        return self.mock.execute_command(command_id, **kwargs)

    def register_command(self, command_id: str, handler: Callable) -> None:
        """Register a command handler."""
        self._commands[command_id] = handler
        self.mock.register_command(command_id, handler)

    def unregister_command(self, command_id: str) -> None:
        """Unregister a command."""
        if command_id in self._commands:
            del self._commands[command_id]
        self.mock.unregister_command(command_id)

class MockConfigurationService(MockService, IConfigurationService):
    """Mock implementation of configuration service."""

    def __init__(self):
        super().__init__("configuration", "1.0.0")
        self._config: Dict[str, Any] = {}
        self._listeners: Dict[str, List[Callable]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        value = self._config.get(key, default)
        self.mock.get(key, default)
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        old_value = self._config.get(key)
        self._config[key] = value
        self.mock.set(key, value)

        # Notify listeners
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, value, old_value)
                except Exception:
                    pass  # Ignore callback errors in tests

    def on_change(self, key: str, callback: Callable) -> None:
        """Register configuration change listener."""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
        self.mock.on_change(key, callback)

class MockWorkspaceService(MockService, IWorkspaceService):
    """Mock implementation of workspace service."""

    def __init__(self):
        super().__init__("workspace", "1.0.0")
        self._active_editor = None
        self._open_files: List[str] = []

    def open_file(self, path: str) -> None:
        """Open a file in the workspace."""
        if path not in self._open_files:
            self._open_files.append(path)
        self.mock.open_file(path)

    def get_active_editor(self) -> Optional[Any]:
        """Get the active editor."""
        self.mock.get_active_editor()
        return self._active_editor

    def create_pane(self, widget: Any, position: str) -> None:
        """Create a new pane with a widget."""
        self.mock.create_pane(widget, position)

class MockThemeService(MockService, IThemeService):
    """Mock implementation of theme service."""

    def __init__(self):
        super().__init__("theme", "1.0.0")
        self._theme = {
            "name": "test-theme",
            "colors": {
                "background": "#ffffff",
                "foreground": "#000000",
                "primary": "#007acc"
            }
        }
        self._listeners: List[Callable] = []

    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme."""
        self.mock.get_current_theme()
        return self._theme.copy()

    def get_color(self, key: str) -> str:
        """Get theme color."""
        color = self._theme.get("colors", {}).get(key, "#000000")
        self.mock.get_color(key)
        return color

    def on_theme_changed(self, callback: Callable) -> None:
        """Register theme change listener."""
        self._listeners.append(callback)
        self.mock.on_theme_changed(callback)

    def set_theme(self, theme: Dict[str, Any]) -> None:
        """Set theme for testing."""
        self._theme = theme
        for callback in self._listeners:
            try:
                callback(theme)
            except Exception:
                pass

class MockNotificationService(MockService, INotificationService):
    """Mock implementation of notification service."""

    def __init__(self):
        super().__init__("notification", "1.0.0")
        self.notifications: List[Dict[str, Any]] = []

    def info(self, message: str, title: Optional[str] = None) -> None:
        """Show info notification."""
        notification = {"type": "info", "message": message, "title": title}
        self.notifications.append(notification)
        self.mock.info(message, title)

    def warning(self, message: str, title: Optional[str] = None) -> None:
        """Show warning notification."""
        notification = {"type": "warning", "message": message, "title": title}
        self.notifications.append(notification)
        self.mock.warning(message, title)

    def error(self, message: str, title: Optional[str] = None) -> None:
        """Show error notification."""
        notification = {"type": "error", "message": message, "title": title}
        self.notifications.append(notification)
        self.mock.error(message, title)

class MockPluginHost:
    """Mock plugin host for testing plugins in isolation."""

    def __init__(self, plugin_id: str = "test-plugin"):
        self.plugin_id = plugin_id
        self._temp_dir = None
        self._services: Dict[str, IService] = {}
        self._event_bus = EventBus()

        # Create default mock services
        self.setup_default_services()

    def setup_default_services(self) -> None:
        """Set up default mock services."""
        self.command_service = MockCommandService()
        self.configuration_service = MockConfigurationService()
        self.workspace_service = MockWorkspaceService()
        self.theme_service = MockThemeService()
        self.notification_service = MockNotificationService()

        self._services.update({
            "command": self.command_service,
            "configuration": self.configuration_service,
            "workspace": self.workspace_service,
            "theme": self.theme_service,
            "notification": self.notification_service,
        })

    def add_service(self, service: IService) -> None:
        """Add a custom service."""
        self._services[service.get_service_id()] = service

    def remove_service(self, service_id: str) -> None:
        """Remove a service."""
        if service_id in self._services:
            del self._services[service_id]

    def get_service(self, service_id: str) -> Optional[IService]:
        """Get a service by ID."""
        return self._services.get(service_id)

    def get_service_typed(self, service_type: Type[T]) -> Optional[T]:
        """Get a service by type."""
        for service in self._services.values():
            if isinstance(service, service_type):
                return service
        return None

    def create_context(self,
                      plugin_path: Optional[Path] = None,
                      data_path: Optional[Path] = None,
                      configuration: Optional[Dict[str, Any]] = None) -> IPluginContext:
        """Create a plugin context for testing."""
        if plugin_path is None:
            plugin_path = self.get_temp_dir() / "plugin"
            plugin_path.mkdir(exist_ok=True)

        if data_path is None:
            data_path = self.get_temp_dir() / "data"
            data_path.mkdir(exist_ok=True)

        if configuration is None:
            configuration = {}

        service_proxy = ServiceProxy(self._services)

        return PluginContext(
            plugin_id=self.plugin_id,
            plugin_path=plugin_path,
            data_path=data_path,
            service_proxy=service_proxy,
            event_bus=self._event_bus,
            configuration=configuration
        )

    def get_temp_dir(self) -> Path:
        """Get temporary directory for testing."""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix=f"test_plugin_{self.plugin_id}_"))
        return self._temp_dir

    def cleanup(self) -> None:
        """Clean up test resources."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None

    def emit_event(self, event_type: EventType, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event for testing."""
        event = PluginEvent(
            type=event_type,
            source="test-host",
            data=data or {}
        )
        self._event_bus.emit(event)

    def get_event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._event_bus

    def assert_event_emitted(self, event_type: EventType,
                           source: Optional[str] = None,
                           timeout: float = 1.0) -> bool:
        """Assert that an event was emitted."""
        events = self._event_bus.get_history(event_type=event_type, source=source)
        return len(events) > 0

    def get_last_event(self, event_type: EventType,
                      source: Optional[str] = None) -> Optional[PluginEvent]:
        """Get the last event of a specific type."""
        events = self._event_bus.get_history(event_type=event_type, source=source, limit=1)
        return events[0] if events else None

    def reset_mocks(self) -> None:
        """Reset all mock call histories."""
        for service in self._services.values():
            if hasattr(service, 'mock'):
                service.mock.reset_mock()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()

# Helper functions for common test scenarios

def create_mock_plugin_context(plugin_id: str = "test-plugin",
                              services: Optional[Dict[str, IService]] = None,
                              configuration: Optional[Dict[str, Any]] = None) -> IPluginContext:
    """Create a mock plugin context with minimal setup."""
    host = MockPluginHost(plugin_id)

    if services:
        for service in services.values():
            host.add_service(service)

    return host.create_context(configuration=configuration)

def create_mock_service_proxy(services: Optional[Dict[str, IService]] = None) -> ServiceProxy:
    """Create a mock service proxy with specified services."""
    if services is None:
        host = MockPluginHost()
        services = host._services

    return ServiceProxy(services)