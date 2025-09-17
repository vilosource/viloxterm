#!/usr/bin/env python3
"""
Service locator pattern implementation for dependency injection.

The ServiceLocator provides a central registry for all services,
enabling loose coupling between components.
"""

import logging
from threading import Lock
from typing import Any, Optional, TypeVar

from services.base import Service

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Service)


class ServiceLocator:
    """
    Central registry for all application services.

    Implements the Service Locator pattern to provide dependency injection
    and service discovery throughout the application.
    """

    _instance: Optional["ServiceLocator"] = None
    _lock = Lock()

    def __new__(cls) -> "ServiceLocator":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the service locator (only once)."""
        if self._initialized:
            return

        self._services: dict[type[Service], Service] = {}
        self._service_instances: dict[str, Service] = {}
        self._initialization_order: list[type[Service]] = []
        self._initialized = True

        logger.info("ServiceLocator initialized")

    @classmethod
    def get_instance(cls) -> "ServiceLocator":
        """
        Get the singleton instance of ServiceLocator.

        Returns:
            The ServiceLocator instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, service_type: type[T], instance: T) -> None:
        """
        Register a service instance.

        Args:
            service_type: The service class type
            instance: The service instance

        Raises:
            ValueError: If a service of this type is already registered
        """
        if service_type in self._services:
            logger.warning(f"Overwriting existing service: {service_type.__name__}")

        self._services[service_type] = instance
        self._service_instances[instance.name] = instance

        # Track initialization order
        if service_type not in self._initialization_order:
            self._initialization_order.append(service_type)

        logger.debug(f"Registered service: {service_type.__name__} ({instance.name})")

    def unregister(self, service_type: type[Service]) -> bool:
        """
        Unregister a service.

        Args:
            service_type: The service class type to unregister

        Returns:
            True if service was unregistered, False if not found
        """
        if service_type not in self._services:
            return False

        instance = self._services[service_type]

        # Cleanup the service
        try:
            instance.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up service {instance.name}: {e}")

        # Remove from registries
        del self._services[service_type]
        if instance.name in self._service_instances:
            del self._service_instances[instance.name]

        # Remove from initialization order
        if service_type in self._initialization_order:
            self._initialization_order.remove(service_type)

        logger.info(f"Unregistered service: {service_type.__name__}")
        return True

    def get(self, service_type: type[T]) -> Optional[T]:
        """
        Get a service instance by type.

        Args:
            service_type: The service class type

        Returns:
            The service instance or None if not found
        """
        return self._services.get(service_type)

    def get_required(self, service_type: type[T]) -> T:
        """
        Get a required service instance by type.

        Args:
            service_type: The service class type

        Returns:
            The service instance

        Raises:
            RuntimeError: If service is not found
        """
        service = self.get(service_type)
        if service is None:
            raise RuntimeError(f"Required service not found: {service_type.__name__}")
        return service

    def get_by_name(self, name: str) -> Optional[Service]:
        """
        Get a service instance by name.

        Args:
            name: The service name

        Returns:
            The service instance or None if not found
        """
        return self._service_instances.get(name)

    def get_all(self) -> list[Service]:
        """
        Get all registered services in initialization order.

        Returns:
            List of all service instances
        """
        return [
            self._services[service_type]
            for service_type in self._initialization_order
            if service_type in self._services
        ]

    def get_all_of_type(self, base_type: type[T]) -> list[T]:
        """
        Get all services that are instances of a given type.

        Args:
            base_type: The base service type

        Returns:
            List of services that are instances of base_type
        """
        return [
            service
            for service in self._services.values()
            if isinstance(service, base_type)
        ]

    def has_service(self, service_type: type[Service]) -> bool:
        """
        Check if a service is registered.

        Args:
            service_type: The service class type

        Returns:
            True if service is registered
        """
        return service_type in self._services

    def initialize_all(self, context: dict[str, Any]) -> None:
        """
        Initialize all registered services.

        Args:
            context: Application context for initialization
        """
        for service in self.get_all():
            if not service.is_initialized:
                try:
                    service.initialize(context)
                    logger.info(f"Initialized service: {service.name}")
                except Exception as e:
                    logger.error(f"Failed to initialize service {service.name}: {e}")

    def cleanup_all(self) -> None:
        """Cleanup all registered services in reverse initialization order."""
        # Cleanup in reverse order
        for service_type in reversed(self._initialization_order):
            if service_type in self._services:
                service = self._services[service_type]
                try:
                    service.cleanup()
                    logger.info(f"Cleaned up service: {service.name}")
                except Exception as e:
                    logger.error(f"Error cleaning up service {service.name}: {e}")

    def clear(self) -> None:
        """
        Clear all registered services.

        This will cleanup and remove all services.
        """
        self.cleanup_all()
        self._services.clear()
        self._service_instances.clear()
        self._initialization_order.clear()
        logger.info("ServiceLocator cleared")

    def __repr__(self) -> str:
        """String representation of the service locator."""
        service_names = [s.name for s in self.get_all()]
        return f"<ServiceLocator(services={service_names})>"
