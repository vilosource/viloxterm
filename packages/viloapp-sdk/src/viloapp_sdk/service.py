"""Service interface and proxy for plugin-host communication."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from dataclasses import dataclass

T = TypeVar("T")


class ServiceNotAvailableError(Exception):
    """Raised when a requested service is not available."""

    pass


class IService(ABC):
    """Base interface for services exposed to plugins."""

    @abstractmethod
    def get_service_id(self) -> str:
        """Get unique service identifier."""
        pass

    @abstractmethod
    def get_service_version(self) -> str:
        """Get service version."""
        pass


@dataclass
class ServiceDescriptor:
    """Describes a service available to plugins."""

    id: str
    version: str
    interface: Type[IService]
    description: str
    optional: bool = False


class ServiceProxy:
    """Proxy for accessing host services from plugins."""

    def __init__(self, services: Dict[str, IService]):
        self._services = services
        self._service_cache = {}

    def get_service(self, service_id: str) -> Optional[IService]:
        """
        Get a service by ID.

        Args:
            service_id: Service identifier

        Returns:
            Service instance or None
        """
        if service_id in self._service_cache:
            return self._service_cache[service_id]

        service = self._services.get(service_id)
        if service:
            self._service_cache[service_id] = service

        return service

    def require_service(self, service_id: str) -> IService:
        """
        Get a required service by ID.

        Args:
            service_id: Service identifier

        Returns:
            Service instance

        Raises:
            ServiceNotAvailableError: If service is not available
        """
        service = self.get_service(service_id)
        if not service:
            raise ServiceNotAvailableError(f"Service '{service_id}' is not available")
        return service

    def get_service_typed(self, service_type: Type[T]) -> Optional[T]:
        """
        Get a service by type.

        Args:
            service_type: Service class type

        Returns:
            Service instance or None
        """
        for service in self._services.values():
            if isinstance(service, service_type):
                return service
        return None

    def has_service(self, service_id: str) -> bool:
        """
        Check if a service is available.

        Args:
            service_id: Service identifier

        Returns:
            True if service is available
        """
        return service_id in self._services

    def list_services(self) -> List[str]:
        """
        List all available service IDs.

        Returns:
            List of service IDs
        """
        return list(self._services.keys())


# Standard service interfaces


class ICommandService(IService):
    """Service for executing commands."""

    @abstractmethod
    def execute_command(self, command_id: str, **kwargs) -> Any:
        """Execute a command."""
        pass

    @abstractmethod
    def register_command(self, command_id: str, handler: callable) -> None:
        """Register a command handler."""
        pass

    @abstractmethod
    def unregister_command(self, command_id: str) -> None:
        """Unregister a command."""
        pass


class IConfigurationService(IService):
    """Service for accessing configuration."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass

    @abstractmethod
    def on_change(self, key: str, callback: callable) -> None:
        """Register configuration change listener."""
        pass


class IWorkspaceService(IService):
    """Service for workspace operations."""

    @abstractmethod
    def open_file(self, path: str) -> None:
        """Open a file in the workspace."""
        pass

    @abstractmethod
    def get_active_editor(self) -> Optional[Any]:
        """Get the active editor."""
        pass

    @abstractmethod
    def create_pane(self, widget: Any, position: str) -> None:
        """Create a new pane with a widget."""
        pass


class IThemeService(IService):
    """Service for theme operations."""

    @abstractmethod
    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme."""
        pass

    @abstractmethod
    def get_color(self, key: str) -> str:
        """Get theme color."""
        pass

    @abstractmethod
    def on_theme_changed(self, callback: callable) -> None:
        """Register theme change listener."""
        pass


class INotificationService(IService):
    """Service for showing notifications."""

    @abstractmethod
    def info(self, message: str, title: Optional[str] = None) -> None:
        """Show info notification."""
        pass

    @abstractmethod
    def warning(self, message: str, title: Optional[str] = None) -> None:
        """Show warning notification."""
        pass

    @abstractmethod
    def error(self, message: str, title: Optional[str] = None) -> None:
        """Show error notification."""
        pass
