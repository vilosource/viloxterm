#!/usr/bin/env python3
"""
Basic tests for the command system.

This module tests the core functionality of the command system including
registration, execution, context evaluation, and undo/redo.
"""

import pytest

from core import (
    Command,
    CommandContext,
    CommandResult,
    ContextKey,
    WhenClauseEvaluator,
    command,
    command_executor,
    command_registry,
    context_manager,
)


class TestCommandBasics:
    """Test basic command functionality."""

    def setup_method(self):
        """Clear registry before each test."""
        command_registry.clear()
        command_executor.clear_history()
        context_manager.reset()

    def test_command_creation(self):
        """Test creating a command."""
        def handler(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value="test")

        cmd = Command(
            id="test.command",
            title="Test Command",
            category="Test",
            handler=handler
        )

        assert cmd.id == "test.command"
        assert cmd.title == "Test Command"
        assert cmd.category == "Test"
        assert callable(cmd.handler)

    def test_command_registration(self):
        """Test registering a command."""
        @command(
            id="test.register",
            title="Test Register",
            category="Test"
        )
        def test_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        # Command should be auto-registered
        cmd = command_registry.get_command("test.register")
        assert cmd is not None
        assert cmd.title == "Test Register"

    def test_command_execution(self):
        """Test executing a command."""
        executed = False

        @command(
            id="test.execute",
            title="Test Execute",
            category="Test"
        )
        def test_command(context: CommandContext) -> CommandResult:
            nonlocal executed
            executed = True
            return CommandResult(success=True, value="executed")

        result = command_executor.execute("test.execute")

        assert executed
        assert result.success
        assert result.value == "executed"

    def test_command_with_args(self):
        """Test command with arguments."""
        @command(
            id="test.args",
            title="Test Args",
            category="Test"
        )
        def test_command(context: CommandContext) -> CommandResult:
            name = context.args.get('name', 'default')
            return CommandResult(success=True, value=f"Hello {name}")

        result = command_executor.execute("test.args", name="World")
        assert result.value == "Hello World"

        result = command_executor.execute("test.args")
        assert result.value == "Hello default"

    def test_command_search(self):
        """Test searching for commands."""
        @command(
            id="file.new",
            title="New File",
            category="File",
            keywords=["create", "add"]
        )
        def new_file(context):
            return CommandResult(success=True)

        @command(
            id="file.open",
            title="Open File",
            category="File",
            keywords=["load", "read"]
        )
        def open_file(context):
            return CommandResult(success=True)

        # Search by title
        results = command_registry.search_commands("new")
        assert len(results) == 1
        assert results[0].id == "file.new"

        # Search by keyword
        results = command_registry.search_commands("create")
        assert len(results) == 1
        assert results[0].id == "file.new"

        # Search by category
        results = command_registry.search_commands("file")
        assert len(results) == 2


class TestContextSystem:
    """Test context management and evaluation."""

    def setup_method(self):
        """Reset context before each test."""
        context_manager.reset()

    def test_context_set_get(self):
        """Test setting and getting context values."""
        context_manager.set(ContextKey.EDITOR_FOCUS, True)
        assert context_manager.get(ContextKey.EDITOR_FOCUS)

        context_manager.set(ContextKey.PANE_COUNT, 3)
        assert context_manager.get(ContextKey.PANE_COUNT) == 3

    def test_context_update(self):
        """Test updating multiple context values."""
        context_manager.update({
            ContextKey.EDITOR_FOCUS: True,
            ContextKey.TERMINAL_FOCUS: False,
            ContextKey.SIDEBAR_VISIBLE: True
        })

        assert context_manager.get(ContextKey.EDITOR_FOCUS)
        assert not context_manager.get(ContextKey.TERMINAL_FOCUS)
        assert context_manager.get(ContextKey.SIDEBAR_VISIBLE)

    def test_context_observer(self):
        """Test context change observers."""
        changes = []

        def observer(key, old_value, new_value):
            changes.append((key, old_value, new_value))

        context_manager.add_observer(observer)
        context_manager.set(ContextKey.EDITOR_FOCUS, True)

        assert len(changes) == 1
        assert changes[0] == (ContextKey.EDITOR_FOCUS, False, True)

        context_manager.remove_observer(observer)
        context_manager.set(ContextKey.EDITOR_FOCUS, False)

        # No new changes after removing observer
        assert len(changes) == 1


class TestWhenClauseEvaluation:
    """Test when clause expression evaluation."""

    def test_simple_identifier(self):
        """Test simple context key evaluation."""
        context = {"editorFocus": True, "terminalFocus": False}

        assert WhenClauseEvaluator.evaluate("editorFocus", context)
        assert not WhenClauseEvaluator.evaluate("terminalFocus", context)

    def test_negation(self):
        """Test NOT operator."""
        context = {"editorFocus": True, "terminalFocus": False}

        assert not WhenClauseEvaluator.evaluate("!editorFocus", context)
        assert WhenClauseEvaluator.evaluate("!terminalFocus", context)

    def test_logical_operators(self):
        """Test AND and OR operators."""
        context = {
            "editorFocus": True,
            "terminalFocus": False,
            "hasSelection": True
        }

        # AND
        assert WhenClauseEvaluator.evaluate("editorFocus && hasSelection", context)
        assert not WhenClauseEvaluator.evaluate("editorFocus && terminalFocus", context)

        # OR
        assert WhenClauseEvaluator.evaluate("editorFocus || terminalFocus", context)
        assert WhenClauseEvaluator.evaluate("terminalFocus || hasSelection", context)

    def test_comparisons(self):
        """Test comparison operators."""
        context = {
            "paneCount": 3,
            "platform": "linux"
        }

        assert WhenClauseEvaluator.evaluate("paneCount == 3", context)
        assert WhenClauseEvaluator.evaluate("paneCount != 2", context)
        assert WhenClauseEvaluator.evaluate("paneCount > 2", context)
        assert WhenClauseEvaluator.evaluate("paneCount >= 3", context)
        assert WhenClauseEvaluator.evaluate("paneCount < 4", context)
        assert WhenClauseEvaluator.evaluate("paneCount <= 3", context)

        assert WhenClauseEvaluator.evaluate("platform == 'linux'", context)
        assert WhenClauseEvaluator.evaluate("platform != 'windows'", context)

    def test_complex_expressions(self):
        """Test complex nested expressions."""
        context = {
            "editorFocus": True,
            "terminalFocus": False,
            "hasSelection": True,
            "paneCount": 3
        }

        # Parentheses
        assert WhenClauseEvaluator.evaluate(
            "(editorFocus || terminalFocus) && hasSelection",
            context
        )

        # Complex nested
        assert WhenClauseEvaluator.evaluate(
            "editorFocus && (paneCount > 2 || hasSelection)",
            context
        )

    def test_command_with_when_clause(self):
        """Test command with when clause."""
        command_registry.clear()

        @command(
            id="test.conditional",
            title="Conditional Command",
            category="Test",
            when="editorFocus && hasSelection"
        )
        def conditional_command(context):
            return CommandResult(success=True)

        cmd = command_registry.get_command("test.conditional")

        # Should not execute when conditions not met
        context = {"editorFocus": False, "hasSelection": True}
        assert not cmd.can_execute(context)

        # Should execute when conditions are met
        context = {"editorFocus": True, "hasSelection": True}
        assert cmd.can_execute(context)


class TestUndoRedo:
    """Test undo/redo functionality."""

    def setup_method(self):
        """Clear executor before each test."""
        command_executor.clear_history()
        command_registry.clear()

    def test_undo_redo(self):
        """Test basic undo/redo."""
        value = 0

        def increment(context):
            nonlocal value
            value += 1
            return CommandResult(success=True)

        def decrement(context):
            nonlocal value
            value -= 1
            return CommandResult(success=True)

        cmd = Command(
            id="test.increment",
            title="Increment",
            category="Test",
            handler=increment,
            undo_handler=decrement,
            redo_handler=increment,
            supports_undo=True
        )

        command_registry.register(cmd)

        # Execute command
        command_executor.execute("test.increment")
        assert value == 1

        # Undo
        result = command_executor.undo()
        assert result.success
        assert value == 0

        # Redo
        result = command_executor.redo()
        assert result.success
        assert value == 1

    def test_undo_stack(self):
        """Test undo stack management."""
        values = []

        @command(
            id="test.append",
            title="Append",
            category="Test"
        )
        def append_command(context):
            value = context.args.get('value')
            values.append(value)
            return CommandResult(success=True)

        # Add undo handler
        def undo_append(context):
            if values:
                values.pop()
            return CommandResult(success=True)

        cmd = command_registry.get_command("test.append")
        cmd.undo_handler = undo_append
        cmd.supports_undo = True

        # Execute multiple commands
        command_executor.execute("test.append", value=1)
        command_executor.execute("test.append", value=2)
        command_executor.execute("test.append", value=3)

        assert values == [1, 2, 3]

        # Undo twice
        command_executor.undo()
        command_executor.undo()

        assert values == [1]

        # Redo once
        command_executor.redo()

        assert values == [1, 2]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
