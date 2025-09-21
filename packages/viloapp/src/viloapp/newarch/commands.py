"""
Pure command system for ViloxTerm.

All user actions go through commands. No direct model manipulation.
Commands are the ONLY way to change application state.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from .model import Pane, Tab, WidgetType, WorkspaceModel
except ImportError:
    # For direct script execution
    from model import Pane, Tab, WidgetType, WorkspaceModel


class CommandStatus(Enum):
    """Status of command execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class CommandContext:
    """Context for command execution."""

    model: WorkspaceModel
    active_tab_id: Optional[str] = None
    active_pane_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_active_tab(self) -> Optional[Tab]:
        """Get the active tab from context or model."""
        if self.active_tab_id:
            for tab in self.model.state.tabs:
                if tab.id == self.active_tab_id:
                    return tab
        return self.model.state.get_active_tab()

    def get_active_pane(self) -> Optional[Pane]:
        """Get the active pane from context or model."""
        tab = self.get_active_tab()
        if not tab:
            return None

        if self.active_pane_id:
            return tab.tree.root.find_pane(self.active_pane_id)
        return tab.get_active_pane()


@dataclass
class CommandResult:
    """Result of command execution."""

    status: CommandStatus = CommandStatus.SUCCESS
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None

    @property
    def success(self) -> bool:
        """Check if command succeeded."""
        return self.status == CommandStatus.SUCCESS


class Command(ABC):
    """Base class for all commands."""

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

    def __str__(self) -> str:
        """String representation of command."""
        return self.name


# Tab Commands
class CreateTabCommand(Command):
    """Command to create a new tab."""

    def __init__(self, name: str = "New Tab", widget_type: WidgetType = WidgetType.EDITOR):
        """Initialize create tab command."""
        super().__init__()
        self.tab_name = name
        self.widget_type = widget_type

    def execute(self, context: CommandContext) -> CommandResult:
        """Create a new tab."""
        try:
            tab_id = context.model.create_tab(self.tab_name, self.widget_type)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=f"Created tab '{self.tab_name}'",
                data={"tab_id": tab_id, "name": self.tab_name},
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Failed to create tab: {str(e)}",
                error=e,
            )


class CloseTabCommand(Command):
    """Command to close a tab."""

    def __init__(self, tab_id: Optional[str] = None):
        """Initialize close tab command."""
        super().__init__()
        self.tab_id = tab_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Close a tab."""
        try:
            tab_id = self.tab_id or context.active_tab_id or context.model.state.active_tab_id

            if not tab_id:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="No tab to close",
                )

            # Don't close last tab
            if len(context.model.state.tabs) == 1:
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE,
                    message="Cannot close last tab",
                )

            success = context.model.close_tab(tab_id)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Closed tab {tab_id}",
                    data={"tab_id": tab_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to close tab {tab_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error closing tab: {str(e)}",
                error=e,
            )


class RenameTabCommand(Command):
    """Command to rename a tab."""

    def __init__(self, new_name: str, tab_id: Optional[str] = None):
        """Initialize rename tab command."""
        super().__init__()
        self.new_name = new_name
        self.tab_id = tab_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Rename a tab."""
        try:
            tab_id = self.tab_id or context.active_tab_id or context.model.state.active_tab_id

            if not tab_id:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="No tab to rename",
                )

            success = context.model.rename_tab(tab_id, self.new_name)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Renamed tab to '{self.new_name}'",
                    data={"tab_id": tab_id, "name": self.new_name},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to rename tab {tab_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error renaming tab: {str(e)}",
                error=e,
            )


class SwitchTabCommand(Command):
    """Command to switch active tab."""

    def __init__(self, tab_id: str):
        """Initialize switch tab command."""
        super().__init__()
        self.tab_id = tab_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Switch to a different tab."""
        try:
            success = context.model.set_active_tab(self.tab_id)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Switched to tab {self.tab_id}",
                    data={"tab_id": self.tab_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to switch to tab {self.tab_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error switching tab: {str(e)}",
                error=e,
            )


# Pane Commands
class SplitPaneCommand(Command):
    """Command to split a pane."""

    def __init__(
        self,
        orientation: str = "horizontal",
        pane_id: Optional[str] = None,
        widget_type: Optional[WidgetType] = None,
    ):
        """Initialize split pane command."""
        super().__init__()
        self.orientation = orientation
        self.pane_id = pane_id
        self.widget_type = widget_type

    def execute(self, context: CommandContext) -> CommandResult:
        """Split a pane."""
        try:
            # Get pane to split
            if self.pane_id:
                pane_id = self.pane_id
            else:
                pane = context.get_active_pane()
                if not pane:
                    return CommandResult(
                        status=CommandStatus.FAILURE,
                        message="No active pane to split",
                    )
                pane_id = pane.id

            # Split the pane
            new_pane_id = context.model.split_pane(pane_id, self.orientation)

            if new_pane_id:
                # Set widget type if specified
                if self.widget_type:
                    context.model.change_pane_widget(new_pane_id, self.widget_type)

                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Split pane {self.orientation}ly",
                    data={
                        "parent_pane_id": pane_id,
                        "new_pane_id": new_pane_id,
                        "orientation": self.orientation,
                    },
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to split pane {pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error splitting pane: {str(e)}",
                error=e,
            )


class ClosePaneCommand(Command):
    """Command to close a pane."""

    def __init__(self, pane_id: Optional[str] = None):
        """Initialize close pane command."""
        super().__init__()
        self.pane_id = pane_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Close a pane."""
        try:
            # Get pane to close
            if self.pane_id:
                pane_id = self.pane_id
            else:
                pane = context.get_active_pane()
                if not pane:
                    return CommandResult(
                        status=CommandStatus.FAILURE,
                        message="No active pane to close",
                    )
                pane_id = pane.id

            # Check if it's the last pane
            tab = context.get_active_tab()
            if tab and len(tab.tree.root.get_all_panes()) == 1:
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE,
                    message="Cannot close last pane in tab",
                )

            # Close the pane
            success = context.model.close_pane(pane_id)

            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Closed pane {pane_id}",
                    data={"pane_id": pane_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to close pane {pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error closing pane: {str(e)}",
                error=e,
            )


class FocusPaneCommand(Command):
    """Command to focus a pane."""

    def __init__(self, pane_id: str):
        """Initialize focus pane command."""
        super().__init__()
        self.pane_id = pane_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Focus a pane."""
        try:
            success = context.model.focus_pane(self.pane_id)

            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Focused pane {self.pane_id}",
                    data={"pane_id": self.pane_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to focus pane {self.pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error focusing pane: {str(e)}",
                error=e,
            )


class ChangeWidgetTypeCommand(Command):
    """Command to change widget type of a pane."""

    def __init__(self, widget_type: WidgetType, pane_id: Optional[str] = None):
        """Initialize change widget type command."""
        super().__init__()
        self.widget_type = widget_type
        self.pane_id = pane_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Change widget type of a pane."""
        try:
            # Get pane to change
            if self.pane_id:
                pane_id = self.pane_id
            else:
                pane = context.get_active_pane()
                if not pane:
                    return CommandResult(
                        status=CommandStatus.FAILURE,
                        message="No active pane to change",
                    )
                pane_id = pane.id

            # Change widget type
            success = context.model.change_pane_widget(pane_id, self.widget_type)

            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Changed widget to {self.widget_type.value}",
                    data={"pane_id": pane_id, "widget_type": self.widget_type.value},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to change widget type for pane {pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error changing widget type: {str(e)}",
                error=e,
            )


# Navigation Commands
class NavigatePaneCommand(Command):
    """Command to navigate between panes."""

    def __init__(self, direction: str):
        """Initialize navigate pane command."""
        super().__init__()
        self.direction = direction  # up, down, left, right

    def execute(self, context: CommandContext) -> CommandResult:
        """Navigate to adjacent pane."""
        # TODO: Implement spatial navigation
        # This requires understanding the tree structure spatially
        return CommandResult(
            status=CommandStatus.NOT_APPLICABLE,
            message=f"Navigation in direction '{self.direction}' not yet implemented",
        )


# Command Registry
class CommandRegistry:
    """Registry for managing commands."""

    def __init__(self):
        """Initialize command registry."""
        self.commands: Dict[str, type[Command]] = {}
        self.aliases: Dict[str, str] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self):
        """Register all built-in commands."""
        # Tab commands
        self.register("tab.create", CreateTabCommand)
        self.register("tab.close", CloseTabCommand)
        self.register("tab.rename", RenameTabCommand)
        self.register("tab.switch", SwitchTabCommand)

        # Pane commands
        self.register("pane.split", SplitPaneCommand)
        self.register("pane.splitHorizontal", SplitPaneCommand)
        self.register("pane.splitVertical", SplitPaneCommand)
        self.register("pane.close", ClosePaneCommand)
        self.register("pane.focus", FocusPaneCommand)
        self.register("pane.changeWidget", ChangeWidgetTypeCommand)

        # Navigation
        self.register("navigate.up", NavigatePaneCommand)
        self.register("navigate.down", NavigatePaneCommand)
        self.register("navigate.left", NavigatePaneCommand)
        self.register("navigate.right", NavigatePaneCommand)

        # Aliases for common commands
        self.alias("workbench.action.splitPaneHorizontal", "pane.splitHorizontal")
        self.alias("workbench.action.splitPaneVertical", "pane.splitVertical")
        self.alias("workbench.action.closePane", "pane.close")
        self.alias("workbench.action.terminal.new", "tab.create")

    def register(self, name: str, command_class: type[Command]):
        """Register a command class."""
        self.commands[name] = command_class

    def alias(self, alias: str, command_name: str):
        """Create an alias for a command."""
        self.aliases[alias] = command_name

    def get_command_class(self, name: str) -> Optional[type[Command]]:
        """Get command class by name or alias."""
        # Check if it's an alias
        if name in self.aliases:
            name = self.aliases[name]

        return self.commands.get(name)

    def create_command(self, command_name: str, **kwargs) -> Optional[Command]:
        """Create a command instance."""
        command_class = self.get_command_class(command_name)
        if not command_class:
            return None

        # Special handling for split commands
        if command_name == "pane.splitHorizontal":
            kwargs["orientation"] = "horizontal"
        elif command_name == "pane.splitVertical":
            kwargs["orientation"] = "vertical"

        try:
            return command_class(**kwargs)
        except Exception as e:
            print(f"Error creating command {command_name}: {e}")
            return None

    def execute(
        self,
        command_name: str,
        context: CommandContext,
        **kwargs,
    ) -> CommandResult:
        """Execute a command by name."""
        command = self.create_command(command_name, **kwargs)
        if not command:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Unknown command: {command_name}",
            )

        # Check if command can execute
        if not command.can_execute(context):
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE,
                message=f"Command '{command_name}' cannot execute in current context",
            )

        # Execute command
        return command.execute(context)

    def list_commands(self) -> List[str]:
        """List all registered command names."""
        return list(self.commands.keys())

    def list_aliases(self) -> Dict[str, str]:
        """List all command aliases."""
        return self.aliases.copy()


# Composite Commands (Macros)
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
            if not result.success:
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


# Undo/Redo Support (Future)
class UndoableCommand(Command):
    """Base class for commands that support undo."""

    @abstractmethod
    def undo(self, context: CommandContext) -> CommandResult:
        """Undo the command."""
        pass

    @abstractmethod
    def redo(self, context: CommandContext) -> CommandResult:
        """Redo the command."""
        pass
