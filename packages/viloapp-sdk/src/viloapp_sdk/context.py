"""Plugin context for accessing host functionality."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from .service import ServiceProxy, IService
from .events import EventBus

class IPluginContext(ABC):
    """Interface for plugin context."""

    @abstractmethod
    def get_plugin_id(self) -> str:
        """Get the plugin ID."""
        pass

    @abstractmethod
    def get_plugin_path(self) -> Path:
        """Get plugin installation path."""
        pass

    @abstractmethod
    def get_data_path(self) -> Path:
        """Get plugin data storage path."""
        pass

    @abstractmethod
    def get_service_proxy(self) -> ServiceProxy:
        """Get service proxy for accessing host services."""
        pass

    @abstractmethod
    def get_event_bus(self) -> EventBus:
        """Get event bus for plugin communication."""
        pass

    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        pass

class PluginContext(IPluginContext):
    """Implementation of plugin context."""

    def __init__(
        self,
        plugin_id: str,
        plugin_path: Path,
        data_path: Path,
        service_proxy: ServiceProxy,
        event_bus: EventBus,
        configuration: Optional[Dict[str, Any]] = None
    ):
        self._plugin_id = plugin_id
        self._plugin_path = plugin_path
        self._data_path = data_path
        self._service_proxy = service_proxy
        self._event_bus = event_bus
        self._configuration = configuration or {}

    def get_plugin_id(self) -> str:
        return self._plugin_id

    def get_plugin_path(self) -> Path:
        return self._plugin_path

    def get_data_path(self) -> Path:
        """Get plugin data path, creating if necessary."""
        self._data_path.mkdir(parents=True, exist_ok=True)
        return self._data_path

    def get_service_proxy(self) -> ServiceProxy:
        return self._service_proxy

    def get_event_bus(self) -> EventBus:
        return self._event_bus

    def get_configuration(self) -> Dict[str, Any]:
        return self._configuration.copy()

    # Convenience methods

    def get_service(self, service_id: str) -> Optional[IService]:
        """Shortcut to get a service."""
        return self._service_proxy.get_service(service_id)

    def emit_event(self, event_type, data: Dict[str, Any] = None) -> None:
        """Shortcut to emit an event."""
        from .events import PluginEvent

        event = PluginEvent(
            type=event_type,
            source=self._plugin_id,
            data=data or {}
        )
        self._event_bus.emit(event)

    def subscribe_event(self, event_type, handler) -> None:
        """Shortcut to subscribe to an event."""
        self._event_bus.subscribe(
            event_type,
            handler,
            subscriber_id=self._plugin_id
        )