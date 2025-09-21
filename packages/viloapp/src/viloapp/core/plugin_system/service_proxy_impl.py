"""Service proxy implementation for plugins."""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from viloapp_sdk import IService, ServiceNotAvailableError, ServiceProxy

from .service_adapters import create_service_adapters

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceProxyImpl(ServiceProxy):
    """Implementation of service proxy for ViloxTerm."""

    def __init__(self, services: Dict[str, Any]):
        # Create service adapters that expose SDK interfaces
        adapters = create_service_adapters(services)

        # Combine original services with adapters
        all_services = {**services, **adapters}

        super().__init__(all_services)


class PermissionAwareServiceProxy:
    """Service proxy that enforces permissions for plugins."""

    def __init__(self, services: Dict[str, IService], permission_manager, plugin_id: str):
        """
        Initialize permission-aware service proxy.

        Args:
            services: Available services
            permission_manager: Permission manager instance
            plugin_id: ID of the plugin using this proxy
        """
        self._services = services
        self._permission_manager = permission_manager
        self.plugin_id = plugin_id
        self._service_cache = {}
        self._permission_cache = {}

    def _get_required_permission(self, service_id: str):
        """Get the permission required to access a service."""
        from .security import Permission, PermissionCategory, PermissionScope

        # Map service IDs to required permissions
        service_permission_map = {
            "configuration": Permission(
                PermissionCategory.SYSTEM, PermissionScope.READ, "configuration"
            ),
            "filesystem": Permission(PermissionCategory.FILESYSTEM, PermissionScope.READ, "*"),
            "network": Permission(PermissionCategory.NETWORK, PermissionScope.EXECUTE, "*"),
            "workspace": Permission(PermissionCategory.UI, PermissionScope.WRITE, "*"),
            "theme": Permission(PermissionCategory.UI, PermissionScope.READ, "*"),
            "notification": Permission(PermissionCategory.UI, PermissionScope.WRITE, "*"),
            "command": Permission(PermissionCategory.UI, PermissionScope.EXECUTE, "commands"),
        }

        return service_permission_map.get(
            service_id, Permission(PermissionCategory.SYSTEM, PermissionScope.READ, service_id)
        )

    def _check_service_permission(self, service_id: str) -> bool:
        """Check if plugin has permission to access a service."""
        # Check cache first
        if service_id in self._permission_cache:
            return self._permission_cache[service_id]

        # Get required permission for this service
        required_permission = self._get_required_permission(service_id)

        # Check if plugin has the required permission
        has_permission = self._permission_manager.has_permission(
            self.plugin_id, required_permission
        )

        # Cache the result
        self._permission_cache[service_id] = has_permission

        if not has_permission:
            logger.warning(
                f"Permission denied: Plugin '{self.plugin_id}' "
                f"attempted to access service '{service_id}' "
                f"without required permission: {required_permission}"
            )

        return has_permission

    def _wrap_service_methods(self, service: IService, service_id: str) -> IService:
        """Wrap service methods with permission checks for specific operations."""
        from .security import PermissionScope

        # Create a wrapper class that checks permissions for specific methods
        class PermissionWrappedService:
            def __init__(self, wrapped_service, proxy):
                self._wrapped_service = wrapped_service
                self._proxy = proxy

            def __getattr__(self, name):
                attr = getattr(self._wrapped_service, name)

                if not callable(attr):
                    return attr

                # Define method permission requirements
                method_permissions = {
                    "set": PermissionScope.WRITE,
                    "write": PermissionScope.WRITE,
                    "save": PermissionScope.WRITE,
                    "create": PermissionScope.WRITE,
                    "delete": PermissionScope.WRITE,
                    "execute": PermissionScope.EXECUTE,
                    "run": PermissionScope.EXECUTE,
                    "get": PermissionScope.READ,
                    "read": PermissionScope.READ,
                    "list": PermissionScope.READ,
                }

                required_scope = method_permissions.get(name)
                if required_scope:
                    # Check if plugin has the required scope for this operation
                    required_permission = self._proxy._get_required_permission(service_id)
                    if required_permission.scope != required_scope:
                        # Create permission with required scope
                        from .security import Permission

                        specific_permission = Permission(
                            required_permission.category,
                            required_scope,
                            required_permission.resource,
                        )

                        if not self._proxy._permission_manager.has_permission(
                            self._proxy.plugin_id, specific_permission
                        ):

                            def permission_denied(*args, **kwargs):
                                raise PermissionError(
                                    f"Plugin '{self._proxy.plugin_id}' lacks {required_scope.value} "
                                    f"permission for service '{service_id}'"
                                )

                            return permission_denied

                return attr

        return PermissionWrappedService(service, self)

    def get_service(self, service_id: str) -> Optional[IService]:
        """
        Get a service by ID with permission checking.

        Args:
            service_id: Service identifier

        Returns:
            Service instance or None if not available or no permission
        """
        # Check if service exists
        if service_id not in self._services:
            return None

        # Check permission
        if not self._check_service_permission(service_id):
            return None

        # Check cache
        if service_id in self._service_cache:
            return self._service_cache[service_id]

        # Get and wrap service
        service = self._services[service_id]
        wrapped_service = self._wrap_service_methods(service, service_id)
        self._service_cache[service_id] = wrapped_service

        return wrapped_service

    def require_service(self, service_id: str) -> IService:
        """
        Get a required service by ID with permission checking.

        Args:
            service_id: Service identifier

        Returns:
            Service instance

        Raises:
            ServiceNotAvailableError: If service is not available or no permission
        """
        service = self.get_service(service_id)
        if not service:
            if service_id not in self._services:
                raise ServiceNotAvailableError(f"Service '{service_id}' is not available")
            else:
                raise ServiceNotAvailableError(
                    f"Service '{service_id}' is not available due to insufficient permissions"
                )
        return service

    def get_service_typed(self, service_type: Type[T]) -> Optional[T]:
        """
        Get a service by type with permission checking.

        Args:
            service_type: Service class type

        Returns:
            Service instance or None
        """
        for service_id, service in self._services.items():
            if isinstance(service, service_type):
                # Check permission before returning
                if self._check_service_permission(service_id):
                    return self.get_service(service_id)
        return None

    def has_service(self, service_id: str) -> bool:
        """
        Check if a service is available with permission checking.

        Args:
            service_id: Service identifier

        Returns:
            True if service is available and plugin has permission
        """
        return service_id in self._services and self._check_service_permission(service_id)

    def list_services(self) -> List[str]:
        """
        List all available service IDs that the plugin has permission to access.

        Returns:
            List of service IDs
        """
        available_services = []
        for service_id in self._services.keys():
            if self._check_service_permission(service_id):
                available_services.append(service_id)
        return available_services
