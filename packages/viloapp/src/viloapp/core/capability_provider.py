#!/usr/bin/env python3
"""
Capability provider interface for ViloxTerm widgets.

This module defines the interface that widgets implement to declare
and execute their capabilities. This enables the platform to interact
with widgets in a type-agnostic manner.

ARCHITECTURE COMPLIANCE:
- Interface-based design for extensibility
- No implementation details in the interface
- Platform uses this interface without knowing widget types
"""

from typing import Any, Dict, Optional, Set

from viloapp.core.capabilities import WidgetCapability


class ICapabilityProvider:
    """
    Interface for widgets that provide capabilities.

    Widgets implement this interface to declare what they can do
    and to execute capability-based actions.
    """

    def get_capabilities(self) -> Set[WidgetCapability]:
        """
        Get the set of capabilities this widget supports.

        This method is called by the platform to discover what
        operations the widget can perform.

        Returns:
            Set of supported capabilities
        """
        raise NotImplementedError("Subclasses must implement get_capabilities()")

    def execute_capability(
        self,
        capability: WidgetCapability,
        **kwargs: Any
    ) -> Any:
        """
        Execute a capability-based action.

        The platform calls this method to perform operations on the widget
        without knowing its specific type or implementation.

        Args:
            capability: The capability to execute
            **kwargs: Capability-specific arguments

        Returns:
            Capability-specific return value

        Raises:
            CapabilityNotSupportedError: If the widget doesn't support the capability
            CapabilityExecutionError: If execution fails
        """
        raise NotImplementedError("Subclasses must implement execute_capability()")

    def has_capability(self, capability: WidgetCapability) -> bool:
        """
        Check if this widget supports a specific capability.

        Default implementation checks the get_capabilities() set.
        Widgets can override for more complex logic.

        Args:
            capability: The capability to check

        Returns:
            True if the widget supports this capability
        """
        return capability in self.get_capabilities()

    def get_capability_metadata(
        self,
        capability: WidgetCapability
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a specific capability.

        Optional method for widgets to provide additional information
        about their capability implementations.

        Args:
            capability: The capability to get metadata for

        Returns:
            Metadata dictionary or None if not available
        """
        return None


class CapabilityNotSupportedError(Exception):
    """
    Raised when a widget doesn't support a requested capability.
    """

    def __init__(self, widget_id: str, capability: WidgetCapability):
        """
        Initialize the error.

        Args:
            widget_id: The widget that doesn't support the capability
            capability: The unsupported capability
        """
        self.widget_id = widget_id
        self.capability = capability
        super().__init__(
            f"Widget '{widget_id}' does not support capability '{capability.value}'"
        )


class CapabilityExecutionError(Exception):
    """
    Raised when capability execution fails.
    """

    def __init__(
        self,
        widget_id: str,
        capability: WidgetCapability,
        reason: str
    ):
        """
        Initialize the error.

        Args:
            widget_id: The widget where execution failed
            capability: The capability that failed
            reason: Reason for the failure
        """
        self.widget_id = widget_id
        self.capability = capability
        self.reason = reason
        super().__init__(
            f"Failed to execute capability '{capability.value}' "
            f"on widget '{widget_id}': {reason}"
        )


class CapabilityResult:
    """
    Standard result wrapper for capability execution.

    Provides a consistent way to return results from capability execution.
    """

    def __init__(
        self,
        success: bool,
        value: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the result.

        Args:
            success: Whether the capability execution succeeded
            value: The return value (if any)
            error: Error message (if failed)
            metadata: Additional metadata about the execution
        """
        self.success = success
        self.value = value
        self.error = error
        self.metadata = metadata or {}

    @classmethod
    def success_result(cls, value: Any = None, **metadata: Any) -> "CapabilityResult":
        """
        Create a successful result.

        Args:
            value: The return value
            **metadata: Additional metadata

        Returns:
            A successful CapabilityResult
        """
        return cls(success=True, value=value, metadata=metadata)

    @classmethod
    def failure_result(cls, error: str, **metadata: Any) -> "CapabilityResult":
        """
        Create a failure result.

        Args:
            error: The error message
            **metadata: Additional metadata

        Returns:
            A failed CapabilityResult
        """
        return cls(success=False, error=error, metadata=metadata)
