#!/usr/bin/env python3
"""
Base service class for all application services.

Services provide business logic separated from UI components,
enabling better testability and maintainability.
"""

from abc import ABCMeta, abstractmethod
from typing import List, Callable, Any, Dict, Optional
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServiceEvent:
    """Event emitted by services."""
    name: str
    data: Dict[str, Any]
    source: str  # Service name that emitted the event


# Create a metaclass that works with both QObject and ABC
class ServiceMeta(type(QObject), ABCMeta):
    """Metaclass that combines QObject and ABC metaclasses."""
    pass


class Service(QObject, metaclass=ServiceMeta):
    """
    Base class for all services.
    
    Services encapsulate business logic and provide a clean interface
    for commands and UI components to interact with application functionality.
    """
    
    # Signal for service events
    service_event = Signal(ServiceEvent)
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the service.
        
        Args:
            name: Optional service name, defaults to class name
        """
        super().__init__()
        self._name = name or self.__class__.__name__
        self._observers: List[Callable[[ServiceEvent], None]] = []
        self._initialized = False
        self._context: Dict[str, Any] = {}
        
    @property
    def name(self) -> str:
        """Get the service name."""
        return self._name
        
    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> None:
        """
        Initialize the service with application context.
        
        Args:
            context: Dictionary containing application components like
                    main_window, workspace, sidebar, etc.
        """
        self._context = context
        self._initialized = True
        logger.info(f"Service {self.name} initialized")
        
    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup service resources.
        
        This is called when the service is being destroyed or the
        application is shutting down.
        """
        self._initialized = False
        self._observers.clear()
        logger.info(f"Service {self.name} cleaned up")
        
    def notify(self, event_name: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Notify observers of a service event.
        
        Args:
            event_name: Name of the event
            data: Optional event data
        """
        event = ServiceEvent(
            name=event_name,
            data=data or {},
            source=self.name
        )
        
        # Emit Qt signal
        self.service_event.emit(event)
        
        # Call observer callbacks
        for observer in self._observers:
            try:
                observer(event)
            except Exception as e:
                logger.error(f"Error in observer for {event_name}: {e}")
    
    def add_observer(self, observer: Callable[[ServiceEvent], None]) -> None:
        """
        Add an observer for service events.
        
        Args:
            observer: Callback function that receives ServiceEvent
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[ServiceEvent], None]) -> None:
        """
        Remove an observer.
        
        Args:
            observer: Callback function to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def get_context_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the initialization context.
        
        Args:
            key: Context key
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        return self._context.get(key, default)
    
    def validate_initialized(self) -> None:
        """
        Validate that the service is initialized.
        
        Raises:
            RuntimeError: If service is not initialized
        """
        if not self._initialized:
            raise RuntimeError(f"Service {self.name} is not initialized")
    
    def __repr__(self) -> str:
        """String representation of the service."""
        return f"<{self.__class__.__name__}(name={self.name}, initialized={self._initialized})>"