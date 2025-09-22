#!/usr/bin/env python3
"""
Command system base classes and types.

This module defines the core Command class and related types that form
the foundation of the command system architecture.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Status of command execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class CommandContext:
    """Context for command execution - Model-View-Command architecture."""

    model: Optional[Any] = None  # Will be WorkspaceModel, using Any to avoid circular import
    active_tab_id: Optional[str] = None
    active_pane_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Legacy fields for compatibility during migration
    main_window: Optional[Any] = None
    workspace: Optional[Any] = None
    active_widget: Optional[Any] = None
    args: Dict[str, Any] = field(default_factory=dict)

    def get_active_tab(self) -> Optional[Any]:
        """Get the active tab from context or model."""
        if self.active_tab_id and hasattr(self.model, "tabs"):
            for tab in self.model.tabs:
                if tab.id == self.active_tab_id:
                    return tab
        if hasattr(self.model, "get_current_tab"):
            return self.model.get_current_tab()
        return None

    def get_active_pane(self) -> Optional[Any]:
        """Get the active pane from context or model."""
        tab = self.get_active_tab()
        if not tab:
            return None

        if self.active_pane_id and hasattr(tab, "root"):
            return tab.root.find_pane(self.active_pane_id)
        if hasattr(tab, "get_active_pane"):
            return tab.get_active_pane()
        return None

    def get_service(self, service_type: type) -> Any:
        """
        DEPRECATED: Get a service by type.

        This method is kept for backward compatibility during migration.
        Commands should use the model directly instead of services.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance or None if not found
        """
        logger.warning(
            f"get_service() is deprecated. Use model directly instead of {service_type.__name__}"
        )

        try:
            from viloapp.services.service_locator import ServiceLocator

            locator = ServiceLocator.get_instance()
            return locator.get(service_type)
        except ImportError:
            logger.error("ServiceLocator not available")
            return None

    def get_required_service(self, service_type: type) -> Any:
        """
        DEPRECATED: Get a required service by type.

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
        """Update command arguments (legacy support)."""
        self.args.update(kwargs)
        # Also update parameters for new system
        self.parameters.update(kwargs)


@dataclass
class CommandResult:
    """Result of command execution."""

    status: CommandStatus = CommandStatus.SUCCESS
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None

    # Legacy fields for compatibility
    value: Any = None

    @property
    def success(self) -> bool:
        """Check if command succeeded."""
        return self.status == CommandStatus.SUCCESS

    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.success

    def __repr__(self) -> str:
        if self.success:
            return f"CommandResult(status={self.status}, message={self.message!r})"
        return f"CommandResult(status={self.status}, error={self.error!r})"

    @classmethod
    def from_legacy(cls, success: bool, value: Any = None, error: Optional[str] = None):
        """Create from legacy format for backward compatibility."""
        if success:
            return cls(
                status=CommandStatus.SUCCESS,
                data={"value": value} if value is not None else {},
                value=value,
            )
        else:
            return cls(
                status=CommandStatus.FAILURE,
                message=error or "Command failed",
                error=Exception(error) if error else None,
            )


class Command(ABC):
    """Base class for all commands in Model-View-Command architecture."""

    def __init__(self, name: Optional[str] = None):
        """Initialize command with optional name."""
        self.name = name or self.__class__.__name__

    @abstractmethod
    def execute(self, context: CommandContext) -> CommandResult:
        """
        Execute the command.

        Args:
            context: Command execution context

        Returns:
            CommandResult with execution status
        """
        pass

    def can_execute(self, context: CommandContext) -> bool:
        """
        Check if command can be executed in current context.

        Args:
            context: Command execution context

        Returns:
            True if command can be executed
        """
        return True

    def undo(self, context: CommandContext) -> CommandResult:
        """
        Undo the command.

        Args:
            context: Command execution context

        Returns:
            CommandResult with undo status
        """
        return CommandResult(
            status=CommandStatus.NOT_APPLICABLE, message="Undo not supported for this command"
        )

    def redo(self, context: CommandContext) -> CommandResult:
        """
        Redo the command.

        Args:
            context: Command execution context

        Returns:
            CommandResult with redo status
        """
        return CommandResult(
            status=CommandStatus.NOT_APPLICABLE, message="Redo not supported for this command"
        )

    def __str__(self) -> str:
        """String representation of command."""
        return self.name


@dataclass
class FunctionCommand:
    """
    Wrapper for function-based commands.

    This wraps function handlers (from @command decorator or manual registration)
    into a command structure that can be registered and executed.
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

            # Convert old-style results to new format
            if not isinstance(result, CommandResult):
                # Assume success if we got a non-CommandResult
                result = CommandResult(
                    status=CommandStatus.SUCCESS,
                    data={"value": result} if result is not None else {},
                )

            return result

        except Exception as e:
            logger.error(f"Error executing command {self.id}: {e}", exc_info=True)
            return CommandResult(status=CommandStatus.FAILURE, message=str(e), error=e)

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
            try:
                from viloapp.core.context.evaluator import WhenClauseEvaluator

                return WhenClauseEvaluator.evaluate(self.when, context)
            except ImportError:
                # If evaluator not available, allow execution
                return True

        return True

    def __repr__(self) -> str:
        return f"LegacyCommand(id={self.id!r}, title={self.title!r}, shortcut={self.shortcut!r})"


class ICommandHandler(Protocol):
    """Protocol for command handler functions."""

    def __call__(self, context: CommandContext) -> CommandResult:
        """Execute the command."""
        ...


# Alias for backward compatibility during migration
LegacyCommand = FunctionCommand


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


# Command Patterns


class CompositeCommand(Command):
    """Command that executes multiple commands in sequence."""

    def __init__(self, commands: List[Command], name: str = "Composite"):
        """Initialize composite command."""
        super().__init__(name)
        self.commands = commands

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute all commands in sequence."""
        results = []

        for command in self.commands:
            result = command.execute(context)
            results.append(result)

            # Stop on failure
            if result.status != CommandStatus.SUCCESS:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Composite command failed at: {command.name}",
                    data={"results": results},
                )

        return CommandResult(
            status=CommandStatus.SUCCESS,
            message=f"Executed {len(self.commands)} commands",
            data={"results": results},
        )


class UndoableCommand(Command):
    """Base class for commands that support undo/redo."""

    @abstractmethod
    def undo(self, context: CommandContext) -> CommandResult:
        """Undo the command."""
        pass
