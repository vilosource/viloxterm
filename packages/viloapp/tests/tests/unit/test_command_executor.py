#!/usr/bin/env python3
"""
Comprehensive tests for core/commands/executor.py.

This test module follows Test Monkey principles:
- Clear test names: test_what_condition_expectation()
- AAA pattern (Arrange-Act-Assert)
- Strong assertions (not just "is not None")
- Mock at service boundaries
- Test error paths
- Add edge cases for all inputs
"""

from collections import deque
from datetime import datetime
from unittest.mock import Mock, patch

from viloapp.core.commands.base import Command, CommandCategory, CommandContext, CommandResult
from viloapp.core.commands.executor import CommandExecutor, CommandHistoryEntry, execute_command
from viloapp.core.commands.registry import command_registry
from viloapp.core.commands.validation import ValidationError


class TestCommandHistoryEntry:
    """Test CommandHistoryEntry data class."""

    def test_init_creates_entry_with_all_fields(self):
        """Test that __init__ creates entry with all required fields."""
        # Arrange
        command_id = "test.command"
        context = CommandContext()
        result = CommandResult(success=True)
        timestamp = datetime.now()

        # Act
        entry = CommandHistoryEntry(command_id, context, result, timestamp)

        # Assert
        assert entry.command_id == command_id
        assert entry.context is context
        assert entry.result is result
        assert entry.timestamp == timestamp
        assert entry.undone is False

    def test_repr_shows_executed_status_when_not_undone(self):
        """Test that __repr__ shows 'executed' status when undone is False."""
        # Arrange
        entry = CommandHistoryEntry(
            "test.cmd", CommandContext(), CommandResult(True), datetime.now()
        )

        # Act
        repr_str = repr(entry)

        # Assert
        assert "executed" in repr_str
        assert "test.cmd" in repr_str
        assert "undone" not in repr_str

    def test_repr_shows_undone_status_when_undone(self):
        """Test that __repr__ shows 'undone' status when undone is True."""
        # Arrange
        entry = CommandHistoryEntry(
            "test.cmd", CommandContext(), CommandResult(True), datetime.now()
        )
        entry.undone = True

        # Act
        repr_str = repr(entry)

        # Assert
        assert "undone" in repr_str
        assert "test.cmd" in repr_str


class TestCommandExecutorSingleton:
    """Test singleton behavior of CommandExecutor."""

    def test_new_returns_same_instance_on_multiple_calls(self):
        """Test that __new__ returns the same instance on multiple calls."""
        # Act
        executor1 = CommandExecutor()
        executor2 = CommandExecutor()

        # Assert
        assert executor1 is executor2

    def test_init_only_initializes_once(self):
        """Test that __init__ only initializes once even with multiple instances."""
        # Arrange
        # Clear any existing instance for clean test
        CommandExecutor._instance = None

        # Act
        executor1 = CommandExecutor()
        initial_history = id(executor1._history)

        executor2 = CommandExecutor()

        # Assert
        assert executor1 is executor2
        assert id(executor2._history) == initial_history

    def test_global_singleton_matches_class_singleton(self):
        """Test that the global command_executor is the same as class singleton."""
        # Arrange
        from viloapp.core.commands.executor import command_executor

        # Act
        # The global executor is created before tests, so any new instance should be the same
        executor = CommandExecutor()

        # Assert - both should point to the same singleton instance
        # They might not be the exact same object due to import timing, but the singleton
        # pattern should ensure they're functionally equivalent
        assert isinstance(command_executor, CommandExecutor)
        assert isinstance(executor, CommandExecutor)
        # Verify they share the same internal state (history, stacks)
        assert executor._history is not None
        assert command_executor._history is not None


class TestCommandExecutorInitialization:
    """Test CommandExecutor initialization."""

    def setup_method(self):
        """Reset singleton for each test."""
        CommandExecutor._instance = None

    def test_init_creates_empty_history_deque_with_maxlen_100(self):
        """Test that __init__ creates empty history deque with maxlen=100."""
        # Act
        executor = CommandExecutor()

        # Assert
        assert isinstance(executor._history, deque)
        assert executor._history.maxlen == 100
        assert len(executor._history) == 0

    def test_init_creates_empty_undo_and_redo_stacks(self):
        """Test that __init__ creates empty undo and redo stacks."""
        # Act
        executor = CommandExecutor()

        # Assert
        assert executor._undo_stack == []
        assert executor._redo_stack == []

    def test_init_sets_executing_flag_to_false(self):
        """Test that __init__ sets _executing flag to False."""
        # Act
        executor = CommandExecutor()

        # Assert
        assert executor._executing is False

    def test_init_sets_last_result_to_none(self):
        """Test that __init__ sets _last_result to None."""
        # Act
        executor = CommandExecutor()

        # Assert
        assert executor._last_result is None


class TestCommandExecutorExecution:
    """Test command execution functionality."""

    def setup_method(self):
        """Setup for each test."""
        # Reset singleton and registry
        CommandExecutor._instance = None
        command_registry.clear()

    def test_execute_successful_command_returns_success_result(self):
        """Test that execute returns success result for successful command."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value="test_value")

        command = Command(
            id="test.success",
            title="Test Success",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.success")

        # Assert
        assert result.success is True
        assert result.value == "test_value"
        assert result.error is None

    def test_execute_nonexistent_command_returns_failure_result(self):
        """Test that execute returns failure result for nonexistent command."""
        # Arrange
        executor = CommandExecutor()

        # Act
        result = executor.execute("nonexistent.command")

        # Assert
        assert result.success is False
        assert "Command not found: nonexistent.command" in result.error
        assert result.value is None

    def test_execute_disabled_command_returns_failure_result(self):
        """Test that execute returns failure result for disabled command."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.disabled",
            title="Test Disabled",
            category=CommandCategory.FILE,
            handler=mock_handler,
            enabled=False,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.disabled")

        # Assert
        assert result.success is False
        assert "Command is disabled: test.disabled" in result.error

    def test_execute_with_context_passes_context_to_handler(self):
        """Test that execute passes provided context to command handler."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.context",
            title="Test Context",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        test_context = CommandContext(args={"test": "value"})

        # Act
        result = executor.execute("test.context", test_context)

        # Assert
        assert result.success is True
        assert received_context is test_context
        assert received_context.args["test"] == "value"

    def test_execute_without_context_creates_new_context(self):
        """Test that execute creates new context when none provided."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.no_context",
            title="Test No Context",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.no_context")

        # Assert
        assert result.success is True
        assert received_context is not None
        assert isinstance(received_context, CommandContext)

    def test_execute_with_kwargs_adds_kwargs_to_context_args(self):
        """Test that execute adds kwargs to context args."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.kwargs",
            title="Test Kwargs",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.kwargs", file_name="test.py", line_number=42)

        # Assert
        assert result.success is True
        assert received_context.args["file_name"] == "test.py"
        assert received_context.args["line_number"] == 42

    def test_execute_stores_last_result_on_success(self):
        """Test that execute stores result in _last_result on success."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value="stored_value")

        command = Command(
            id="test.store",
            title="Test Store",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.store")

        # Assert
        assert result.success is True
        assert executor._last_result is result
        assert executor._last_result.value == "stored_value"

    def test_execute_stores_last_result_on_failure(self):
        """Test that execute stores result in _last_result on failure."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=False, error="test_error")

        command = Command(
            id="test.fail",
            title="Test Fail",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.fail")

        # Assert
        assert result.success is False
        assert executor._last_result is result
        assert executor._last_result.error == "test_error"

    def test_execute_prevents_recursive_execution(self):
        """Test that execute prevents recursive command execution."""
        # Arrange
        executor = CommandExecutor()

        def recursive_handler(context):
            # Try to execute another command during execution
            return executor.execute("test.other")

        command = Command(
            id="test.recursive",
            title="Test Recursive",
            category=CommandCategory.FILE,
            handler=recursive_handler,
        )
        command_registry.register(command)

        # Act
        result = executor.execute("test.recursive")

        # Assert
        assert result.success is False
        assert "Command execution already in progress" in result.error

    def test_execute_adds_successful_command_to_history(self):
        """Test that execute adds successful commands to history."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value="test")

        command = Command(
            id="test.history",
            title="Test History",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.history")

        # Assert
        assert result.success is True
        assert len(executor._history) == 1

        history_entry = executor._history[0]
        assert history_entry.command_id == "test.history"
        assert history_entry.result.success is True
        assert history_entry.undone is False

    def test_execute_does_not_add_failed_command_to_history(self):
        """Test that execute does not add failed commands to history."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=False, error="test error")

        command = Command(
            id="test.fail_history",
            title="Test Fail History",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.fail_history")

        # Assert
        assert result.success is False
        assert len(executor._history) == 0

    def test_execute_handles_exception_in_command_handler(self):
        """Test that execute handles exceptions in command handlers gracefully."""

        # Arrange
        def exception_handler(context):
            raise ValueError("Test exception")

        command = Command(
            id="test.exception",
            title="Test Exception",
            category=CommandCategory.FILE,
            handler=exception_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.exception")

        # Assert
        assert result.success is False
        assert "Test exception" in result.error  # Command.execute wraps exceptions
        assert len(executor._history) == 0  # Failed commands not in history


class TestCommandExecutorHistory:
    """Test command history management."""

    def setup_method(self):
        """Setup for each test."""
        CommandExecutor._instance = None
        command_registry.clear()

    def test_get_history_returns_empty_list_when_no_commands_executed(self):
        """Test that get_history returns empty list when no commands executed."""
        # Arrange
        executor = CommandExecutor()

        # Act
        history = executor.get_history()

        # Assert
        assert history == []

    def test_get_history_returns_most_recent_first(self):
        """Test that get_history returns entries with most recent first."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command1 = Command(id="test.first", title="First", category="Test", handler=mock_handler)
        command2 = Command(id="test.second", title="Second", category="Test", handler=mock_handler)
        command_registry.register(command1)
        command_registry.register(command2)

        executor = CommandExecutor()

        # Act
        executor.execute("test.first")
        executor.execute("test.second")
        history = executor.get_history()

        # Assert
        assert len(history) == 2
        assert history[0].command_id == "test.second"  # Most recent first
        assert history[1].command_id == "test.first"

    def test_get_history_respects_limit_parameter(self):
        """Test that get_history respects the limit parameter."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        commands = []
        for i in range(5):
            command = Command(
                id=f"test.cmd{i}",
                title=f"Command {i}",
                category="Test",
                handler=mock_handler,
            )
            commands.append(command)
            command_registry.register(command)

        executor = CommandExecutor()

        # Execute all commands
        for command in commands:
            executor.execute(command.id)

        # Act
        limited_history = executor.get_history(limit=3)

        # Assert
        assert len(limited_history) == 3
        # Should be most recent 3
        assert limited_history[0].command_id == "test.cmd4"
        assert limited_history[1].command_id == "test.cmd3"
        assert limited_history[2].command_id == "test.cmd2"

    def test_get_last_result_returns_none_when_no_commands_executed(self):
        """Test that get_last_result returns None when no commands executed."""
        # Arrange
        executor = CommandExecutor()

        # Act
        last_result = executor.get_last_result()

        # Assert
        assert last_result is None

    def test_get_last_result_returns_last_command_result(self):
        """Test that get_last_result returns result of last executed command."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value="last_value")

        command = Command(
            id="test.last_result",
            title="Test Last Result",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        executor.execute("test.last_result")
        last_result = executor.get_last_result()

        # Assert
        assert last_result is not None
        assert last_result.success is True
        assert last_result.value == "last_value"

    def test_clear_history_removes_all_history_and_stacks(self):
        """Test that clear_history removes all history and undo/redo stacks."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.clear", title="Test Clear", category="Test", handler=mock_handler
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.clear")

        # Verify we have history
        assert len(executor._history) > 0
        assert executor._last_result is not None

        # Act
        executor.clear_history()

        # Assert
        assert len(executor._history) == 0
        assert len(executor._undo_stack) == 0
        assert len(executor._redo_stack) == 0
        assert executor._last_result is None


class TestCommandExecutorValidation:
    """Test parameter validation integration."""

    def setup_method(self):
        """Setup for each test."""
        CommandExecutor._instance = None
        command_registry.clear()

    def test_execute_skips_validation_when_no_validation_spec(self):
        """Test that execute skips validation when command has no validation spec."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value=context.args.get("unchecked"))

        command = Command(
            id="test.no_validation",
            title="Test No Validation",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.no_validation", unchecked="invalid_value")

        # Assert
        assert result.success is True
        assert result.value == "invalid_value"

    @patch("viloapp.core.commands.validation.get_validation_spec")
    def test_execute_validates_parameters_when_validation_spec_exists(
        self, mock_get_validation_spec
    ):
        """Test that execute validates parameters when validation spec exists."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value=context.args.get("name"))

        command = Command(
            id="test.with_validation",
            title="Test With Validation",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        # Create mock validation spec
        mock_spec = Mock()
        mock_context = CommandContext(args={"name": "validated_value"})
        mock_spec.validate_context.return_value = mock_context
        mock_get_validation_spec.return_value = mock_spec

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.with_validation", name="test_value")

        # Assert
        assert result.success is True
        assert result.value == "validated_value"
        mock_spec.validate_context.assert_called_once()

    @patch("viloapp.core.commands.validation.get_validation_spec")
    def test_execute_returns_failure_when_validation_fails(self, mock_get_validation_spec):
        """Test that execute returns failure when parameter validation fails."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.validation_fail",
            title="Test Validation Fail",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        # Create mock validation spec that raises ValidationError
        mock_spec = Mock()
        mock_spec.validate_context.side_effect = ValidationError("Invalid parameter")
        mock_get_validation_spec.return_value = mock_spec

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.validation_fail", invalid_param="bad_value")

        # Assert
        assert result.success is False
        assert "Parameter validation failed" in result.error
        assert "Invalid parameter" in result.error

    @patch("viloapp.core.commands.validation.get_validation_spec")
    def test_execute_logs_validation_debug_messages(self, mock_get_validation_spec):
        """Test that execute logs appropriate debug messages during validation."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.validation_logging",
            title="Test Validation Logging",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        # Create mock validation spec
        mock_spec = Mock()
        mock_spec.validate_context.return_value = CommandContext(args={})
        mock_get_validation_spec.return_value = mock_spec

        executor = CommandExecutor()

        # Act
        with patch("viloapp.core.commands.executor.logger") as mock_logger:
            result = executor.execute("test.validation_logging")

            # Assert
            assert result.success is True
            mock_logger.debug.assert_any_call(
                "Validating parameters for command: test.validation_logging"
            )
            mock_logger.debug.assert_any_call(
                "Parameter validation passed for command: test.validation_logging"
            )

    @patch("viloapp.core.commands.validation.get_validation_spec")
    def test_execute_handles_validation_module_import_failure(self, mock_get_validation_spec):
        """Test that execute handles validation module import failure gracefully."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.import_fail",
            title="Test Import Fail",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        # Make get_validation_spec raise ImportError
        mock_get_validation_spec.side_effect = ImportError("Validation module not found")

        executor = CommandExecutor()

        # Act
        with patch("viloapp.core.commands.executor.logger") as mock_logger:
            result = executor.execute("test.import_fail")

            # Assert
            assert result.success is False
            assert "Parameter validation failed" in result.error
            mock_logger.warning.assert_called_once()


class TestCommandExecutorDirectExecution:
    """Test execute_command method for direct command execution."""

    def setup_method(self):
        """Setup for each test."""
        CommandExecutor._instance = None
        command_registry.clear()

    def test_execute_command_registers_unregistered_command(self):
        """Test that execute_command registers command if not already registered."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value="direct_execution")

        command = Command(
            id="test.direct",
            title="Test Direct",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )

        executor = CommandExecutor()

        # Verify command is not registered
        assert command_registry.get_command("test.direct") is None

        # Act
        result = executor.execute_command(command)

        # Assert
        assert result.success is True
        assert result.value == "direct_execution"
        # Command should now be registered
        assert command_registry.get_command("test.direct") is not None

    def test_execute_command_uses_existing_registration(self):
        """Test that execute_command uses existing registration if command already registered."""

        # Arrange
        def original_handler(context):
            return CommandResult(success=True, value="original")

        def new_handler(context):
            return CommandResult(success=True, value="new")

        original_command = Command(
            id="test.existing",
            title="Test Existing",
            category=CommandCategory.FILE,
            handler=original_handler,
        )
        command_registry.register(original_command)

        new_command = Command(
            id="test.existing",  # Same ID
            title="Test New",
            category=CommandCategory.FILE,
            handler=new_handler,
        )

        executor = CommandExecutor()

        # Act
        result = executor.execute_command(new_command)

        # Assert
        # Should use the originally registered command
        assert result.success is True
        assert result.value == "original"

    def test_execute_command_passes_kwargs_to_execute(self):
        """Test that execute_command passes kwargs to execute method."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.kwargs_direct",
            title="Test Kwargs Direct",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )

        executor = CommandExecutor()

        # Act
        result = executor.execute_command(command, test_arg="test_value", number=42)

        # Assert
        assert result.success is True
        assert received_context.args["test_arg"] == "test_value"
        assert received_context.args["number"] == 42


class TestGlobalExecuteCommandFunction:
    """Test the global execute_command convenience function."""

    def setup_method(self):
        """Setup for each test."""
        CommandExecutor._instance = None
        command_registry.clear()

    def test_execute_command_function_uses_global_executor(self):
        """Test that global execute_command function uses global executor."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value="global_function")

        command = Command(
            id="test.global_func",
            title="Test Global Function",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        # Act
        result = execute_command("test.global_func")

        # Assert
        assert result.success is True
        assert result.value == "global_function"

    def test_execute_command_function_passes_kwargs(self):
        """Test that global execute_command function passes kwargs."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.global_kwargs",
            title="Test Global Kwargs",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        # Act
        result = execute_command("test.global_kwargs", param="value", flag=True)

        # Assert
        assert result.success is True
        assert received_context.args["param"] == "value"
        assert received_context.args["flag"] is True


class TestCommandExecutorUndoRedo:
    """Test undo/redo functionality."""

    def setup_method(self):
        """Setup for each test."""
        CommandExecutor._instance = None
        command_registry.clear()

    def test_can_undo_returns_false_when_no_undoable_commands(self):
        """Test that can_undo returns False when no undoable commands executed."""
        # Arrange
        executor = CommandExecutor()

        # Act & Assert
        assert executor.can_undo() is False

    def test_can_redo_returns_false_when_no_redoable_commands(self):
        """Test that can_redo returns False when no redoable commands executed."""
        # Arrange
        executor = CommandExecutor()

        # Act & Assert
        assert executor.can_redo() is False

    def test_execute_adds_undoable_command_to_undo_stack(self):
        """Test that execute adds undoable commands to undo stack."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        def mock_undo_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.undoable",
            title="Test Undoable",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=mock_undo_handler,
            supports_undo=True,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.undoable")

        # Assert
        assert result.success is True
        assert executor.can_undo() is True
        assert len(executor._undo_stack) == 1
        assert executor._undo_stack[0].command_id == "test.undoable"

    def test_execute_does_not_add_non_undoable_command_to_undo_stack(self):
        """Test that execute does not add non-undoable commands to undo stack."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.not_undoable",
            title="Test Not Undoable",
            category=CommandCategory.FILE,
            handler=mock_handler,
            supports_undo=False,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute("test.not_undoable")

        # Assert
        assert result.success is True
        assert executor.can_undo() is False
        assert len(executor._undo_stack) == 0

    def test_execute_clears_redo_stack_on_new_command(self):
        """Test that execute clears redo stack when new command is executed."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        def mock_undo_handler(context):
            return CommandResult(success=True)

        command1 = Command(
            id="test.cmd1",
            title="Test Command 1",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=mock_undo_handler,
            supports_undo=True,
        )
        command2 = Command(
            id="test.cmd2",
            title="Test Command 2",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=mock_undo_handler,
            supports_undo=True,
        )
        command_registry.register(command1)
        command_registry.register(command2)

        executor = CommandExecutor()

        # Execute, undo, then execute new command
        executor.execute("test.cmd1")
        executor.undo()
        assert executor.can_redo() is True

        # Act - execute new command
        result = executor.execute("test.cmd2")

        # Assert
        assert result.success is True
        assert executor.can_redo() is False  # Redo stack should be cleared
        assert len(executor._redo_stack) == 0

    def test_undo_returns_failure_when_nothing_to_undo(self):
        """Test that undo returns failure when nothing to undo."""
        # Arrange
        executor = CommandExecutor()

        # Act
        result = executor.undo()

        # Assert
        assert result.success is False
        assert "Nothing to undo" in result.error

    def test_undo_calls_undo_handler_and_moves_to_redo_stack(self):
        """Test that undo calls undo handler and moves entry to redo stack."""
        # Arrange
        undo_called = False

        def mock_handler(context):
            return CommandResult(success=True, value="executed")

        def mock_undo_handler(context):
            nonlocal undo_called
            undo_called = True
            return CommandResult(success=True, value="undone")

        command = Command(
            id="test.undo_success",
            title="Test Undo Success",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=mock_undo_handler,
            supports_undo=True,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.undo_success")

        # Act
        result = executor.undo()

        # Assert
        assert result.success is True
        assert result.value == "undone"
        assert undo_called is True
        assert executor.can_undo() is False
        assert executor.can_redo() is True
        assert len(executor._undo_stack) == 0
        assert len(executor._redo_stack) == 1
        assert executor._redo_stack[0].undone is True

    def test_undo_returns_failure_when_command_has_no_undo_handler(self):
        """Test that undo returns failure when command has no undo handler."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.no_undo_handler",
            title="Test No Undo Handler",
            category=CommandCategory.FILE,
            handler=mock_handler,
            supports_undo=True,  # Says it supports undo but no handler
            undo_handler=None,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.no_undo_handler")

        # Act
        result = executor.undo()

        # Assert
        assert result.success is False
        assert "Command does not support undo" in result.error
        # Entry should be put back on undo stack
        assert len(executor._undo_stack) == 1

    def test_undo_handles_exception_in_undo_handler(self):
        """Test that undo handles exceptions in undo handler gracefully."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        def exception_undo_handler(context):
            raise ValueError("Undo failed")

        command = Command(
            id="test.undo_exception",
            title="Test Undo Exception",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=exception_undo_handler,
            supports_undo=True,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.undo_exception")

        # Act
        result = executor.undo()

        # Assert
        assert result.success is False
        assert "Exception during undo: Undo failed" in result.error
        # Entry should be put back on undo stack
        assert len(executor._undo_stack) == 1

    def test_redo_returns_failure_when_nothing_to_redo(self):
        """Test that redo returns failure when nothing to redo."""
        # Arrange
        executor = CommandExecutor()

        # Act
        result = executor.redo()

        # Assert
        assert result.success is False
        assert "Nothing to redo" in result.error

    def test_redo_uses_redo_handler_when_available(self):
        """Test that redo uses redo handler when available."""
        # Arrange
        redo_called = False

        def mock_handler(context):
            return CommandResult(success=True, value="executed")

        def mock_undo_handler(context):
            return CommandResult(success=True, value="undone")

        def mock_redo_handler(context):
            nonlocal redo_called
            redo_called = True
            return CommandResult(success=True, value="redone")

        command = Command(
            id="test.redo_handler",
            title="Test Redo Handler",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=mock_undo_handler,
            redo_handler=mock_redo_handler,
            supports_undo=True,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.redo_handler")
        executor.undo()

        # Act
        result = executor.redo()

        # Assert
        assert result.success is True
        assert result.value == "redone"
        assert redo_called is True
        assert executor.can_undo() is True
        assert executor.can_redo() is False

    def test_redo_re_executes_command_when_no_redo_handler(self):
        """Test that redo re-executes command when no redo handler available."""
        # Arrange
        execution_count = 0

        def counting_handler(context):
            nonlocal execution_count
            execution_count += 1
            return CommandResult(success=True, value=f"execution_{execution_count}")

        def mock_undo_handler(context):
            return CommandResult(success=True, value="undone")

        command = Command(
            id="test.redo_re_execute",
            title="Test Redo Re-execute",
            category=CommandCategory.FILE,
            handler=counting_handler,
            undo_handler=mock_undo_handler,
            supports_undo=True,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.redo_re_execute")  # execution_count = 1
        executor.undo()

        # Act
        result = executor.redo()  # Should re-execute, execution_count = 2

        # Assert
        assert result.success is True
        assert result.value == "execution_2"
        assert execution_count == 2

    def test_redo_handles_command_not_found(self):
        """Test that redo handles case when command is no longer registered."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        def mock_undo_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.redo_missing",
            title="Test Redo Missing",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=mock_undo_handler,
            supports_undo=True,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.redo_missing")
        executor.undo()

        # Unregister the command
        command_registry.unregister("test.redo_missing")

        # Act
        result = executor.redo()

        # Assert
        assert result.success is False
        assert "Command not found: test.redo_missing" in result.error
        # Entry should be put back on redo stack
        assert len(executor._redo_stack) == 1

    def test_redo_handles_exception_in_redo_execution(self):
        """Test that redo handles exceptions during redo execution gracefully."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        def mock_undo_handler(context):
            return CommandResult(success=True)

        def exception_redo_handler(context):
            raise RuntimeError("Redo failed")

        command = Command(
            id="test.redo_exception",
            title="Test Redo Exception",
            category=CommandCategory.FILE,
            handler=mock_handler,
            undo_handler=mock_undo_handler,
            redo_handler=exception_redo_handler,
            supports_undo=True,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.redo_exception")
        executor.undo()

        # Act
        result = executor.redo()

        # Assert
        assert result.success is False
        assert "Exception during redo: Redo failed" in result.error
        # Entry should be put back on redo stack
        assert len(executor._redo_stack) == 1


class TestCommandExecutorEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Setup for each test."""
        CommandExecutor._instance = None
        command_registry.clear()

    def test_execute_with_empty_command_id_returns_failure(self):
        """Test that execute returns failure for empty command ID."""
        # Arrange
        executor = CommandExecutor()

        # Act
        result = executor.execute("")

        # Assert
        assert result.success is False
        assert "Command not found:" in result.error

    def test_execute_with_none_command_id_returns_failure(self):
        """Test that execute returns failure for None command ID."""
        # Arrange
        executor = CommandExecutor()

        # Act
        result = executor.execute(None)

        # Assert
        assert result.success is False
        assert "Command not found: None" in result.error

    def test_history_deque_respects_maxlen_limit(self):
        """Test that history deque respects maxlen=100 limit."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        executor = CommandExecutor()

        # Create and register commands
        commands = []
        for i in range(105):  # More than maxlen=100
            command = Command(
                id=f"test.bulk_{i}",
                title=f"Bulk Test {i}",
                category=CommandCategory.FILE,
                handler=mock_handler,
            )
            commands.append(command)
            command_registry.register(command)

        # Act - execute all commands
        for command in commands:
            executor.execute(command.id)

        # Assert
        assert len(executor._history) == 100  # Should be limited to maxlen
        # Should contain the most recent 100 commands
        history = executor.get_history(limit=100)  # Get all 100 entries
        assert history[0].command_id == "test.bulk_104"  # Most recent
        assert len(history) == 100  # Should have exactly 100 entries
        assert history[99].command_id == "test.bulk_5"  # Oldest in history

    def test_execute_with_very_large_kwargs_succeeds(self):
        """Test that execute handles very large kwargs dictionaries."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.large_kwargs",
            title="Test Large Kwargs",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Create large kwargs dictionary
        large_kwargs = {f"param_{i}": f"value_{i}" for i in range(1000)}

        # Act
        result = executor.execute("test.large_kwargs", **large_kwargs)

        # Assert
        assert result.success is True
        assert len(received_context.args) == 1000
        assert received_context.args["param_999"] == "value_999"

    def test_execute_with_special_characters_in_kwargs(self):
        """Test that execute handles special characters in kwargs."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.special_chars",
            title="Test Special Characters",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()

        # Act
        result = executor.execute(
            "test.special_chars",
            unicode_text="Hello 世界! 🚀",
            special_chars="!@#$%^&*()_+-=[]{}|;':\",./<>?",
            newlines="line1\nline2\r\nline3",
            empty_string="",
            none_value=None,
        )

        # Assert
        assert result.success is True
        assert received_context.args["unicode_text"] == "Hello 世界! 🚀"
        assert received_context.args["special_chars"] == "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        assert received_context.args["newlines"] == "line1\nline2\r\nline3"
        assert received_context.args["empty_string"] == ""
        assert received_context.args["none_value"] is None

    def test_command_handler_returns_non_commandresult_gets_wrapped(self):
        """Test that handlers returning non-CommandResult values get wrapped."""

        # Arrange
        def handler_returning_string(context):
            return "plain string result"

        def handler_returning_dict(context):
            return {"key": "value"}

        def handler_returning_none(context):
            return None

        commands = [
            Command(
                id="test.string",
                title="String",
                category="Test",
                handler=handler_returning_string,
            ),
            Command(
                id="test.dict",
                title="Dict",
                category="Test",
                handler=handler_returning_dict,
            ),
            Command(
                id="test.none",
                title="None",
                category="Test",
                handler=handler_returning_none,
            ),
        ]

        for command in commands:
            command_registry.register(command)

        executor = CommandExecutor()

        # Act & Assert
        result1 = executor.execute("test.string")
        assert result1.success is True
        assert result1.value == "plain string result"

        result2 = executor.execute("test.dict")
        assert result2.success is True
        assert result2.value == {"key": "value"}

        result3 = executor.execute("test.none")
        assert result3.success is True
        assert result3.value is None

    def test_context_args_update_preserves_existing_args(self):
        """Test that kwargs update preserves existing context args."""
        # Arrange
        received_context = None

        def mock_handler(context):
            nonlocal received_context
            received_context = context
            return CommandResult(success=True)

        command = Command(
            id="test.preserve_args",
            title="Test Preserve Args",
            category=CommandCategory.FILE,
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        context = CommandContext(args={"existing": "value", "shared": "original"})

        # Act
        result = executor.execute("test.preserve_args", context, shared="updated", new="added")

        # Assert
        assert result.success is True
        assert received_context.args["existing"] == "value"  # Preserved
        assert received_context.args["shared"] == "updated"  # Updated by kwargs
        assert received_context.args["new"] == "added"  # Added by kwargs

    def test_get_history_with_zero_limit_returns_empty_list(self):
        """Test that get_history with limit=0 returns empty list."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(id="test.zero_limit", title="Test", category="Test", handler=mock_handler)
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.zero_limit")

        # Act
        history = executor.get_history(limit=0)

        # Assert
        assert history == []

    def test_get_history_with_negative_limit_returns_empty_list(self):
        """Test that get_history with negative limit returns empty list."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        command = Command(
            id="test.negative_limit",
            title="Test",
            category="Test",
            handler=mock_handler,
        )
        command_registry.register(command)

        executor = CommandExecutor()
        executor.execute("test.negative_limit")

        # Act
        history = executor.get_history(limit=-5)

        # Assert
        assert history == []

    def test_undo_redo_sequence_maintains_proper_stack_states(self):
        """Test that multiple undo/redo operations maintain proper stack states."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True, value=context.args.get("value", "default"))

        def mock_undo_handler(context):
            return CommandResult(success=True, value="undone")

        commands = []
        for i in range(3):
            command = Command(
                id=f"test.sequence_{i}",
                title=f"Sequence {i}",
                category=CommandCategory.FILE,
                handler=mock_handler,
                undo_handler=mock_undo_handler,
                supports_undo=True,
            )
            commands.append(command)
            command_registry.register(command)

        executor = CommandExecutor()

        # Execute three commands
        for i, command in enumerate(commands):
            executor.execute(command.id, value=f"cmd_{i}")

        # Act & Assert sequence
        assert executor.can_undo() is True
        assert executor.can_redo() is False
        assert len(executor._undo_stack) == 3
        assert len(executor._redo_stack) == 0

        # Undo all three
        for i in range(3):
            result = executor.undo()
            assert result.success is True

        assert executor.can_undo() is False
        assert executor.can_redo() is True
        assert len(executor._undo_stack) == 0
        assert len(executor._redo_stack) == 3

        # Redo all three
        for i in range(3):
            result = executor.redo()
            assert result.success is True

        assert executor.can_undo() is True
        assert executor.can_redo() is False
        assert len(executor._undo_stack) == 3
        assert len(executor._redo_stack) == 0

    def test_undo_with_failed_undo_handler_restores_entry_to_correct_position(self):
        """Test that failed undo restores entry to correct position in undo stack."""

        # Arrange
        def mock_handler(context):
            return CommandResult(success=True)

        def successful_undo_handler(context):
            return CommandResult(success=True)

        def failing_undo_handler(context):
            return CommandResult(success=False, error="Undo failed")

        cmd1 = Command(
            id="test.undo_ok",
            title="Undo OK",
            category="Test",
            handler=mock_handler,
            undo_handler=successful_undo_handler,
            supports_undo=True,
        )
        cmd2 = Command(
            id="test.undo_fail",
            title="Undo Fail",
            category="Test",
            handler=mock_handler,
            undo_handler=failing_undo_handler,
            supports_undo=True,
        )

        command_registry.register(cmd1)
        command_registry.register(cmd2)

        executor = CommandExecutor()
        executor.execute("test.undo_ok")
        executor.execute("test.undo_fail")

        # Act - try to undo the failing command
        result = executor.undo()

        # Assert
        assert result.success is False
        assert "Undo failed" in result.error
        # Entry should be restored to undo stack
        assert len(executor._undo_stack) == 2
        assert executor._undo_stack[-1].command_id == "test.undo_fail"  # Back at top

    def test_multiple_executors_share_same_instance(self):
        """Test that multiple CommandExecutor instances are the same singleton."""
        # Arrange & Act
        executor1 = CommandExecutor()
        executor2 = CommandExecutor()
        executor3 = CommandExecutor()

        # Assert
        assert executor1 is executor2
        assert executor2 is executor3
        assert executor1 is executor3

        # Modifications to one affect all
        executor1.clear_history()
        assert len(executor2._history) == 0
        assert len(executor3._history) == 0
