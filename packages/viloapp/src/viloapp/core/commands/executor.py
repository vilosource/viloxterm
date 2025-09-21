#!/usr/bin/env python3
"""
Command executor with undo/redo support.

The CommandExecutor handles command execution, manages the undo/redo stack,
and provides command history tracking.
"""

import logging
from collections import deque
from datetime import datetime
from typing import Optional

from viloapp.core.commands.base import Command, CommandContext, CommandResult
from viloapp.core.commands.registry import command_registry

logger = logging.getLogger(__name__)


class CommandHistoryEntry:
    """Entry in the command history."""

    def __init__(
        self,
        command_id: str,
        context: CommandContext,
        result: CommandResult,
        timestamp: datetime,
    ):
        """
        Initialize a history entry.

        Args:
            command_id: ID of executed command
            context: Context used for execution
            result: Result of execution
            timestamp: When the command was executed
        """
        self.command_id = command_id
        self.context = context
        self.result = result
        self.timestamp = timestamp
        self.undone = False

    def __repr__(self) -> str:
        status = "undone" if self.undone else "executed"
        return f"HistoryEntry({self.command_id}, {status}, {self.timestamp})"


class CommandExecutor:
    """
    Executes commands and manages undo/redo operations.

    The executor maintains a history of executed commands and provides
    undo/redo functionality for commands that support it.
    """

    _instance: Optional["CommandExecutor"] = None

    def __new__(cls) -> "CommandExecutor":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the executor (only once)."""
        if self._initialized:
            return

        self._history: deque[CommandHistoryEntry] = deque(maxlen=100)
        self._undo_stack: list[CommandHistoryEntry] = []
        self._redo_stack: list[CommandHistoryEntry] = []
        self._executing = False  # Prevent recursive execution
        self._last_result: Optional[CommandResult] = None
        self._initialized = True

        logger.info("CommandExecutor initialized")

    def execute(
        self, command_id: str, context: Optional[CommandContext] = None, **kwargs
    ) -> CommandResult:
        """
        Execute a command by ID.

        Args:
            command_id: ID of command to execute
            context: Execution context (created if not provided)
            **kwargs: Additional arguments to pass to the command

        Returns:
            CommandResult from the execution
        """
        # Prevent recursive execution
        if self._executing:
            logger.warning(f"Recursive execution prevented for command: {command_id}")
            return CommandResult(
                success=False, error="Command execution already in progress"
            )

        # Get the command
        command = command_registry.get_command(command_id)
        if not command:
            logger.error(f"Command not found: {command_id}")
            return CommandResult(
                success=False, error=f"Command not found: {command_id}"
            )

        # Create context if not provided
        if context is None:
            context = CommandContext()

        # Add kwargs to context args
        context.args.update(kwargs)

        # Check if command can execute in current context
        if not command.enabled:
            logger.warning(f"Command is disabled: {command_id}")
            return CommandResult(
                success=False, error=f"Command is disabled: {command_id}"
            )

        # TODO: Check when clause once context system is implemented
        # if command.when and not command.can_execute(context_dict):
        #     return CommandResult(success=False, error="Command not available in current context")

        try:
            self._executing = True

            # Log execution
            logger.info(f"Executing command: {command_id}")

            # Validate command parameters if validation is configured
            try:
                from viloapp.core.commands.validation import get_validation_spec

                validation_spec = get_validation_spec(command)
                if validation_spec:
                    logger.debug(f"Validating parameters for command: {command_id}")
                    context = validation_spec.validate_context(context)
                    logger.debug(
                        f"Parameter validation passed for command: {command_id}"
                    )
            except Exception as validation_error:
                logger.warning(
                    f"Parameter validation failed for command {command_id}: {validation_error}"
                )
                return CommandResult(
                    success=False,
                    error=f"Parameter validation failed: {str(validation_error)}",
                )

            # Execute the command
            result = command.execute(context)

            # Store result
            self._last_result = result

            # Add to history if successful
            if result.success:
                entry = CommandHistoryEntry(
                    command_id=command_id,
                    context=context,
                    result=result,
                    timestamp=datetime.now(),
                )
                self._history.append(entry)

                # Add to undo stack if command supports undo
                if command.supports_undo:
                    self._undo_stack.append(entry)
                    # Clear redo stack on new command
                    self._redo_stack.clear()

                logger.info(f"Command executed successfully: {command_id}")
            else:
                logger.warning(f"Command failed: {command_id} - {result.error}")

            return result

        except Exception as e:
            logger.error(
                f"Exception executing command {command_id}: {e}", exc_info=True
            )
            return CommandResult(
                success=False, error=f"Exception during execution: {str(e)}"
            )
        finally:
            self._executing = False

    def execute_command(
        self, command: Command, context: Optional[CommandContext] = None, **kwargs
    ) -> CommandResult:
        """
        Execute a command directly.

        Args:
            command: Command to execute
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            CommandResult from the execution
        """
        # Register command if not already registered
        if not command_registry.get_command(command.id):
            command_registry.register(command)

        return self.execute(command.id, context, **kwargs)

    def undo(self) -> CommandResult:
        """
        Undo the last undoable command.

        Returns:
            CommandResult indicating success or failure
        """
        if not self._undo_stack:
            logger.info("Nothing to undo")
            return CommandResult(success=False, error="Nothing to undo")

        entry = self._undo_stack.pop()
        command = command_registry.get_command(entry.command_id)

        if not command or not command.undo_handler:
            logger.error(f"Cannot undo command: {entry.command_id}")
            self._undo_stack.append(entry)  # Put it back
            return CommandResult(
                success=False,
                error=f"Command does not support undo: {entry.command_id}",
            )

        try:
            logger.info(f"Undoing command: {entry.command_id}")

            # Execute undo handler
            result = command.undo_handler(entry.context)

            if result.success:
                entry.undone = True
                self._redo_stack.append(entry)
                logger.info(f"Command undone: {entry.command_id}")
            else:
                self._undo_stack.append(entry)  # Put it back
                logger.warning(f"Undo failed: {entry.command_id}")

            return result

        except Exception as e:
            logger.error(f"Exception during undo: {e}", exc_info=True)
            self._undo_stack.append(entry)  # Put it back
            return CommandResult(
                success=False, error=f"Exception during undo: {str(e)}"
            )

    def redo(self) -> CommandResult:
        """
        Redo the last undone command.

        Returns:
            CommandResult indicating success or failure
        """
        if not self._redo_stack:
            logger.info("Nothing to redo")
            return CommandResult(success=False, error="Nothing to redo")

        entry = self._redo_stack.pop()
        command = command_registry.get_command(entry.command_id)

        if not command:
            logger.error(f"Cannot redo command: {entry.command_id}")
            self._redo_stack.append(entry)  # Put it back
            return CommandResult(
                success=False, error=f"Command not found: {entry.command_id}"
            )

        try:
            logger.info(f"Redoing command: {entry.command_id}")

            # Use redo handler if available, otherwise re-execute
            if command.redo_handler:
                result = command.redo_handler(entry.context)
            else:
                result = command.execute(entry.context)

            if result.success:
                entry.undone = False
                self._undo_stack.append(entry)
                logger.info(f"Command redone: {entry.command_id}")
            else:
                self._redo_stack.append(entry)  # Put it back
                logger.warning(f"Redo failed: {entry.command_id}")

            return result

        except Exception as e:
            logger.error(f"Exception during redo: {e}", exc_info=True)
            self._redo_stack.append(entry)  # Put it back
            return CommandResult(
                success=False, error=f"Exception during redo: {str(e)}"
            )

    def get_history(self, limit: int = 50) -> list[CommandHistoryEntry]:
        """
        Get command execution history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries (most recent first)
        """
        entries = list(self._history)
        entries.reverse()
        return entries[:limit]

    def get_last_result(self) -> Optional[CommandResult]:
        """
        Get the result of the last executed command.

        Returns:
            Last CommandResult or None
        """
        return self._last_result

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return bool(self._redo_stack)

    def clear_history(self) -> None:
        """Clear all history and undo/redo stacks."""
        self._history.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._last_result = None
        logger.info("Command history cleared")


# Global singleton instance
command_executor = CommandExecutor()


def execute_command(command_id: str, **kwargs) -> CommandResult:
    """
    Execute a command through the global executor.

    This is a convenience function that allows any widget to execute
    commands without needing to import or reference the executor.

    Args:
        command_id: The ID of the command to execute
        **kwargs: Additional arguments for the command

    Returns:
        CommandResult from the executed command

    Example:
        from viloapp.core.commands.executor import execute_command
        result = execute_command("file.newEditorTab", name="untitled.py")
    """
    return command_executor.execute(command_id, **kwargs)
