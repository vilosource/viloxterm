#!/usr/bin/env python3
"""
Integration tests for command validation framework.
"""

from unittest.mock import Mock

import pytest

from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command
from core.commands.executor import CommandExecutor
from core.commands.registry import CommandRegistry
from core.commands.validation import OneOf, ParameterSpec, Range, String, validate


class TestValidationIntegration:
    """Test validation framework integration with command execution."""

    def setup_method(self):
        """Set up test environment."""
        # Create a fresh registry for testing
        self.registry = CommandRegistry()
        self.executor = CommandExecutor()

    def test_validated_command_execution_success(self):
        """Test successful execution of a validated command."""

        @command(
            id="test.validated.success",
            title="Test Validated Success",
            category="Test",
            register=False
        )
        @validate(
            count=ParameterSpec("count", Range(1, 10), required=True),
            mode=ParameterSpec("mode", OneOf("fast", "slow"), default="fast")
        )
        def test_command(context: CommandContext) -> CommandResult:
            count = context.args.get("count")
            mode = context.args.get("mode")
            return CommandResult(
                success=True,
                value={"count": count, "mode": mode}
            )

        # Register the command
        self.registry.register(test_command)

        # Create context with valid parameters
        context = CommandContext(args={"count": 5})

        # Execute the command
        result = test_command.execute(context)

        # Verify success and parameter validation/defaulting
        assert result.success is True
        assert result.value["count"] == 5
        assert result.value["mode"] == "fast"  # Default value applied

    def test_validated_command_execution_failure(self):
        """Test failed execution of a validated command due to invalid parameters."""

        @command(
            id="test.validated.failure",
            title="Test Validated Failure",
            category="Test",
            register=False
        )
        @validate(
            count=ParameterSpec("count", Range(1, 10), required=True)
        )
        def test_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Register the command
        self.registry.register(test_command)

        # Test with missing required parameter
        context = CommandContext(args={})
        result = test_command.execute(context)
        assert result.success is False
        assert "Required parameter 'count' is missing" in result.error

        # Test with out-of-range parameter
        context = CommandContext(args={"count": 20})
        result = test_command.execute(context)
        assert result.success is False
        assert "greater than maximum 10" in result.error

    def test_validation_with_command_executor(self):
        """Test validation integration with CommandExecutor."""

        @command(
            id="test.executor.validation",
            title="Test Executor Validation",
            category="Test",
            register=False
        )
        @validate(
            name=ParameterSpec("name", String(min_length=3, max_length=20), required=True)
        )
        def test_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value={"name": context.args["name"]})

        # Test validation through direct command execution
        # Test successful validation
        context = CommandContext(args={"name": "TestName"})
        result = test_command.execute(context)
        assert result.success is True
        assert result.value["name"] == "TestName"

        # Test failed validation
        context = CommandContext(args={"name": "ab"})  # Too short
        result = test_command.execute(context)
        assert result.success is False
        assert "less than minimum 3" in result.error

    def test_workspace_command_validation_example(self):
        """Test the actual workspace commands with validation."""

        # This tests the commands we actually modified in workspace_commands.py
        from core.commands.builtin.workspace_commands import select_tab_command
        from core.commands.validation import get_validation_spec

        # Verify the command has validation
        validation_spec = get_validation_spec(select_tab_command)
        assert validation_spec is not None
        assert "tab_index" in validation_spec.parameters

        # Test valid execution
        context = CommandContext(args={"tab_index": 2})
        context.get_service = Mock(return_value=Mock())  # Mock workspace service

        # The command will fail because services aren't set up, but validation should pass
        result = select_tab_command.execute(context)
        # We expect it to fail on service issues, not validation
        assert "WorkspaceService not available" in result.error

        # Test invalid execution
        context = CommandContext(args={"tab_index": 100})  # Out of range
        result = select_tab_command.execute(context)
        # Should fail on validation before reaching service logic
        assert result.success is False
        assert "greater than maximum" in result.error

    def test_nested_validation_with_complex_types(self):
        """Test validation with complex nested parameters."""

        @command(
            id="test.complex.validation",
            title="Test Complex Validation",
            category="Test",
            register=False
        )
        @validate(
            file_paths=ParameterSpec(
                "file_paths",
                # This would test list validation if we need it
                String(min_length=1),
                required=True
            ),
            options=ParameterSpec(
                "options",
                OneOf("create", "update", "delete"),
                default="create"
            )
        )
        def complex_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Test successful execution
        context = CommandContext(args={
            "file_paths": "test.txt",
            "options": "update"
        })
        result = complex_command.execute(context)
        assert result.success is True
        assert result.value["file_paths"] == "test.txt"
        assert result.value["options"] == "update"

        # Test with invalid option
        context = CommandContext(args={
            "file_paths": "test.txt",
            "options": "invalid_option"
        })
        result = complex_command.execute(context)
        assert result.success is False
        assert "not in allowed values" in result.error


if __name__ == "__main__":
    pytest.main([__file__])
