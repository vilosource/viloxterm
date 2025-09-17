#!/usr/bin/env python3
"""
Command system base classes and types.

This module defines the core Command class and related types that form
the foundation of the command system architecture.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

logger = logging.getLogger(__name__)


class CommandResult:
    """Result of a command execution."""

    def __init__(self, success: bool, value: Any = None, error: Optional[str] = None):
        """
        Initialize a command result.

        Args:
            success: Whether the command executed successfully
            value: Return value from the command (if any)
            error: Error message if the command failed
        """
        self.success = success
        self.value = value
        self.error = error

    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.success

    def __repr__(self) -> str:
        if self.success:
            return f"CommandResult(success=True, value={self.value!r})"
        return f"CommandResult(success=False, error={self.error!r})"


class CommandContext:
    """Context passed to command handlers during execution."""

    def __init__(
        self,
        main_window=None,
        workspace=None,
        active_widget=None,
        services: Optional[dict[str, Any]] = None,
        args: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize command context.

        Args:
            main_window: Main application window
            workspace: Current workspace
            active_widget: Currently focused widget
            services: Available services (deprecated - use ServiceLocator)
            args: Command arguments
        """
        self.main_window = main_window
        self.workspace = workspace
        self.active_widget = active_widget
        self.services = services or {}  # Kept for backward compatibility
        self.args = args or {}
        self._service_locator = None

    def get_service(self, service_type: type) -> Any:
        """
        Get a service by type.

        This method now integrates with ServiceLocator for better service management.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance or None if not found
        """
        # First try ServiceLocator if available
        if self._service_locator is None:
            try:
                from services.service_locator import ServiceLocator

                self._service_locator = ServiceLocator.get_instance()
            except ImportError:
                logger.debug(
                    "ServiceLocator not available, falling back to legacy services"
                )
                self._service_locator = False  # Mark as tried but not available

        if self._service_locator:
            service = self._service_locator.get(service_type)
            if service:
                return service

        # Fall back to legacy services dict
        # Try by type name first
        service_name = service_type.__name__
        if service_name in self.services:
            return self.services[service_name]

        # Try by type
        for service in self.services.values():
            if isinstance(service, service_type):
                return service

        return None

    def get_required_service(self, service_type: type) -> Any:
        """
        Get a required service by type.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance

        Raises:
            RuntimeError: If service is not found
        """
        service = self.get_service(service_type)
        if service is None:
            raise RuntimeError(f"Required service not found: {service_type.__name__}")
        return service

    def update_args(self, **kwargs):
        """Update command arguments."""
        self.args.update(kwargs)


@dataclass
class Command:
    """
    Represents an executable command in the system.

    Commands are the central abstraction for all user actions in the application.
    They can be triggered by keyboard shortcuts, menu items, the command palette,
    or programmatically.
    """

    # Identity
    id: str  # Unique identifier (e.g., "file.newEditorTab")
    title: str  # Display name (e.g., "New Editor Tab")
    category: str  # Category for grouping (e.g., "File")

    # Execution
    handler: Callable[[CommandContext], CommandResult]  # Function to execute

    # UI Metadata
    description: Optional[str] = None  # Detailed description for tooltips
    icon: Optional[str] = None  # Icon identifier
    keywords: list[str] = field(default_factory=list)  # Search keywords

    # Keyboard
    shortcut: Optional[str] = None  # Default keyboard shortcut
    when: Optional[str] = None  # Context expression for availability

    # Undo/Redo Support
    undo_handler: Optional[Callable[[CommandContext], CommandResult]] = None
    redo_handler: Optional[Callable[[CommandContext], CommandResult]] = None
    supports_undo: bool = False

    # Default Arguments
    args: Optional[dict[str, Any]] = None  # Default arguments

    # State
    visible: bool = True  # Show in command palette
    enabled: bool = True  # Can be executed
    checked: Optional[bool] = None  # For toggle commands

    # Grouping and Ordering
    group: Optional[str] = None  # Menu group
    order: int = 0  # Sort order within group

    def __post_init__(self):
        """Validate command after initialization."""
        if not self.id:
            raise ValueError("Command must have an id")
        if not self.title:
            raise ValueError("Command must have a title")
        if not self.category:
            raise ValueError("Command must have a category")
        if not callable(self.handler):
            raise ValueError(f"Command {self.id} handler must be callable")

        # Set undo support flag if handlers are provided
        if self.undo_handler or self.redo_handler:
            self.supports_undo = True

    def execute(self, context: CommandContext) -> CommandResult:
        """
        Execute the command with the given context.

        Args:
            context: Command execution context

        Returns:
            CommandResult indicating success or failure
        """
        try:
            # Merge default args with context args
            if self.args:
                for key, value in self.args.items():
                    if key not in context.args:
                        context.args[key] = value

            # Execute the handler
            result = self.handler(context)

            # Ensure we always return a CommandResult
            if not isinstance(result, CommandResult):
                result = CommandResult(success=True, value=result)

            return result

        except Exception as e:
            logger.error(f"Error executing command {self.id}: {e}", exc_info=True)
            return CommandResult(success=False, error=str(e))

    def __call__(self, context: CommandContext) -> CommandResult:
        """Execute the command - makes Command objects callable."""
        return self.execute(context)

    def can_execute(self, context: dict[str, Any]) -> bool:
        """
        Check if the command can execute in the given context.

        Args:
            context: Current application context

        Returns:
            True if the command can execute
        """
        if not self.enabled:
            return False

        if self.when:
            # This will be implemented by the context evaluator
            # For now, just return True if there's no when clause
            from core.context.evaluator import WhenClauseEvaluator

            return WhenClauseEvaluator.evaluate(self.when, context)

        return True

    def __repr__(self) -> str:
        return (
            f"Command(id={self.id!r}, title={self.title!r}, shortcut={self.shortcut!r})"
        )


class ICommandHandler(Protocol):
    """Protocol for command handler functions."""

    def __call__(self, context: CommandContext) -> CommandResult:
        """Execute the command."""
        ...


class CommandCategory:
    """Standard command categories."""

    FILE = "File"
    EDIT = "Edit"
    VIEW = "View"
    NAVIGATION = "Navigation"
    TERMINAL = "Terminal"
    DEBUG = "Debug"
    WINDOW = "Window"
    HELP = "Help"

    # Special categories
    INTERNAL = "_Internal"  # Hidden from UI
    EXPERIMENTAL = "_Experimental"  # Experimental features
