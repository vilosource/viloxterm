#!/usr/bin/env python3
"""
Unit tests for the command validation framework.
"""

from unittest.mock import Mock, patch

import pytest

from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command
from core.commands.validation import (
    All,
    CommandValidationSpec,
    CompositeValidator,
    Custom,
    CustomValidator,
    List,
    ListValidator,
    OneOf,
    OneOfValidator,
    Optional,
    OptionalValidator,
    ParameterSpec,
    Range,
    RangeValidator,
    String,
    StringValidator,
    Type,
    TypeValidator,
    ValidationError,
    get_validation_spec,
    validate,
    validate_command_args,
)


class TestValidators:
    """Test individual validator classes."""

    def test_type_validator_success(self):
        """Test TypeValidator with valid type."""
        validator = TypeValidator(int)
        assert validator.validate(42) is True

    def test_type_validator_failure(self):
        """Test TypeValidator with invalid type."""
        validator = TypeValidator(int)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not an int")
        assert "Expected int, got str" in str(exc_info.value)

    def test_range_validator_success(self):
        """Test RangeValidator with valid values."""
        validator = RangeValidator(0, 10)
        assert validator.validate(5) is True
        assert validator.validate(0) is True
        assert validator.validate(10) is True

    def test_range_validator_failure(self):
        """Test RangeValidator with invalid values."""
        validator = RangeValidator(0, 10)

        with pytest.raises(ValidationError):
            validator.validate(-1)

        with pytest.raises(ValidationError):
            validator.validate(11)

    def test_range_validator_non_numeric(self):
        """Test RangeValidator with non-numeric value."""
        validator = RangeValidator(0, 10)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not a number")
        assert "Expected numeric value" in str(exc_info.value)

    def test_oneof_validator_success(self):
        """Test OneOfValidator with valid values."""
        validator = OneOfValidator(["red", "green", "blue"])
        assert validator.validate("red") is True
        assert validator.validate("green") is True

    def test_oneof_validator_failure(self):
        """Test OneOfValidator with invalid value."""
        validator = OneOfValidator(["red", "green", "blue"])
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("yellow")
        assert "not in allowed values" in str(exc_info.value)

    def test_string_validator_length(self):
        """Test StringValidator length constraints."""
        validator = StringValidator(min_length=3, max_length=10)

        assert validator.validate("hello") is True

        with pytest.raises(ValidationError):
            validator.validate("hi")  # too short

        with pytest.raises(ValidationError):
            validator.validate("this is too long")  # too long

    def test_string_validator_non_empty(self):
        """Test StringValidator non-empty constraint."""
        validator = StringValidator(non_empty=True)

        assert validator.validate("hello") is True

        with pytest.raises(ValidationError):
            validator.validate("")

        with pytest.raises(ValidationError):
            validator.validate("   ")  # whitespace only

    def test_string_validator_pattern(self):
        """Test StringValidator pattern matching."""
        validator = StringValidator(pattern=r"^[a-z]+$")

        assert validator.validate("hello") is True

        with pytest.raises(ValidationError):
            validator.validate("Hello")  # contains uppercase

        with pytest.raises(ValidationError):
            validator.validate("hello123")  # contains numbers

    def test_list_validator_length(self):
        """Test ListValidator length constraints."""
        validator = ListValidator(min_length=2, max_length=5)

        assert validator.validate([1, 2, 3]) is True

        with pytest.raises(ValidationError):
            validator.validate([1])  # too short

        with pytest.raises(ValidationError):
            validator.validate([1, 2, 3, 4, 5, 6])  # too long

    def test_list_validator_elements(self):
        """Test ListValidator element validation."""
        element_validator = TypeValidator(int)
        validator = ListValidator(element_validator=element_validator)

        assert validator.validate([1, 2, 3]) is True

        with pytest.raises(ValidationError) as exc_info:
            validator.validate([1, "two", 3])
        assert "Element 1" in str(exc_info.value)

    def test_custom_validator_success(self):
        """Test CustomValidator with valid value."""
        def even_number(value):
            return value % 2 == 0

        validator = CustomValidator(even_number, "Must be even")
        assert validator.validate(4) is True

    def test_custom_validator_failure(self):
        """Test CustomValidator with invalid value."""
        def even_number(value):
            return value % 2 == 0

        validator = CustomValidator(even_number, "Must be even")
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(3)
        assert "Must be even" in str(exc_info.value)

    def test_optional_validator(self):
        """Test OptionalValidator allows None."""
        base_validator = TypeValidator(int)
        validator = OptionalValidator(base_validator)

        assert validator.validate(None) is True
        assert validator.validate(42) is True

        with pytest.raises(ValidationError):
            validator.validate("not an int")

    def test_composite_validator(self):
        """Test CompositeValidator combines multiple validators."""
        validators = [
            TypeValidator(int),
            RangeValidator(0, 100)
        ]
        validator = CompositeValidator(validators)

        assert validator.validate(50) is True

        with pytest.raises(ValidationError):
            validator.validate("not an int")

        with pytest.raises(ValidationError):
            validator.validate(150)


class TestConvenienceFunctions:
    """Test convenience factory functions."""

    def test_string_factory(self):
        """Test String() factory function."""
        validator = String(min_length=3, max_length=10, non_empty=True)
        assert isinstance(validator, StringValidator)
        assert validator.validate("hello") is True

    def test_range_factory(self):
        """Test Range() factory function."""
        validator = Range(0, 10)
        assert isinstance(validator, RangeValidator)
        assert validator.validate(5) is True

    def test_oneof_factory(self):
        """Test OneOf() factory function."""
        validator = OneOf("red", "green", "blue")
        assert isinstance(validator, OneOfValidator)
        assert validator.validate("red") is True

    def test_optional_factory(self):
        """Test Optional() factory function."""
        validator = Optional(Type(int))
        assert isinstance(validator, OptionalValidator)
        assert validator.validate(None) is True
        assert validator.validate(42) is True

    def test_list_factory(self):
        """Test List() factory function."""
        validator = List(min_length=1, element_validator=Type(str))
        assert isinstance(validator, ListValidator)
        assert validator.validate(["hello", "world"]) is True

    def test_type_factory(self):
        """Test Type() factory function."""
        validator = Type(int)
        assert isinstance(validator, TypeValidator)
        assert validator.validate(42) is True

    def test_custom_factory(self):
        """Test Custom() factory function."""
        validator = Custom(lambda x: x > 0, "Must be positive")
        assert isinstance(validator, CustomValidator)
        assert validator.validate(5) is True

    def test_all_factory(self):
        """Test All() factory function."""
        validator = All(Type(int), Range(0, 100))
        assert isinstance(validator, CompositeValidator)
        assert validator.validate(50) is True


class TestParameterSpec:
    """Test ParameterSpec class."""

    def test_required_parameter(self):
        """Test required parameter validation."""
        spec = ParameterSpec("test", Type(int), required=True)

        assert spec.validate(42) == 42

        with pytest.raises(ValidationError) as exc_info:
            spec.validate(None)
        assert "Required parameter 'test' is missing" in str(exc_info.value)

    def test_optional_parameter_with_default(self):
        """Test optional parameter with default value."""
        spec = ParameterSpec("test", Type(int), default=10)

        assert spec.validate(42) == 42
        assert spec.validate(None) == 10

    def test_parameter_with_validator(self):
        """Test parameter with validator."""
        spec = ParameterSpec("test", Range(0, 10))

        assert spec.validate(5) == 5

        with pytest.raises(ValidationError):
            spec.validate(15)


class TestCommandValidationSpec:
    """Test CommandValidationSpec class."""

    def test_validate_context_success(self):
        """Test successful context validation."""
        specs = {
            "count": ParameterSpec("count", Type(int), required=True),
            "name": ParameterSpec("name", String(min_length=1), default="default")
        }
        validation_spec = CommandValidationSpec(specs)

        context = CommandContext(args={"count": 5})
        validated_context = validation_spec.validate_context(context)

        assert validated_context.args["count"] == 5
        assert validated_context.args["name"] == "default"

    def test_validate_context_failure(self):
        """Test context validation failure."""
        specs = {
            "count": ParameterSpec("count", Type(int), required=True)
        }
        validation_spec = CommandValidationSpec(specs)

        context = CommandContext(args={})

        with pytest.raises(ValidationError) as exc_info:
            validation_spec.validate_context(context)
        assert "Required parameter 'count' is missing" in str(exc_info.value)

    def test_argument_count_constraints(self):
        """Test argument count constraints."""
        validation_spec = CommandValidationSpec(min_args=2, max_args=5)

        # Too few arguments
        context = CommandContext(args={"a": 1})
        with pytest.raises(ValidationError) as exc_info:
            validation_spec.validate_context(context)
        assert "at least 2 arguments" in str(exc_info.value)

        # Too many arguments
        context = CommandContext(args={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6})
        with pytest.raises(ValidationError) as exc_info:
            validation_spec.validate_context(context)
        assert "at most 5 arguments" in str(exc_info.value)


class TestValidateDecorator:
    """Test the @validate decorator."""

    def test_validate_decorator_with_function(self):
        """Test @validate decorator applied to a function."""
        @validate(
            count=ParameterSpec("count", Type(int), required=True),
            name=ParameterSpec("name", String(min_length=1))
        )
        def test_function(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Test successful validation
        context = CommandContext(args={"count": 5, "name": "test"})
        result = test_function(context)
        assert result.success is True
        assert result.value["count"] == 5
        assert result.value["name"] == "test"

        # Test validation failure
        context = CommandContext(args={"name": "test"})  # missing required count
        result = test_function(context)
        assert result.success is False
        assert "Required parameter 'count' is missing" in result.error

    def test_validate_decorator_with_command(self):
        """Test @validate decorator applied to a command."""

        # Create the command first, then apply validation
        def test_func(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Apply command decorator first
        test_command = command(
            id="test.command",
            title="Test Command",
            category="Test",
            register=False
        )(test_func)

        # Then apply validation decorator
        test_command_with_validation = validate(
            tab_index=ParameterSpec("tab_index", Range(0, 10), required=True)
        )(test_command)

        # Test that command object has validation spec
        assert hasattr(test_command_with_validation, '_validation_spec')
        validation_spec = get_validation_spec(test_command_with_validation)
        assert validation_spec is not None
        assert "tab_index" in validation_spec.parameters

    def test_validate_decorator_with_simple_validators(self):
        """Test @validate decorator with simple validator objects."""
        @validate(
            count=Type(int),
            name=String(min_length=1)
        )
        def test_function(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Should convert validators to ParameterSpec
        validation_spec = get_validation_spec(test_function)
        assert validation_spec is not None
        assert isinstance(validation_spec.parameters["count"], ParameterSpec)
        assert isinstance(validation_spec.parameters["name"], ParameterSpec)


class TestIntegration:
    """Test integration between validation and other components."""

    def test_validate_command_args_function(self):
        """Test validate_command_args function."""
        # Create a mock command with validation
        test_command = Mock()
        test_command._validation_spec = CommandValidationSpec({
            "count": ParameterSpec("count", Type(int), required=True)
        })

        # Mock the registry
        with patch('core.commands.registry.command_registry') as mock_registry:
            mock_registry.get_command.return_value = test_command

            # Test successful validation
            validated_args = validate_command_args("test.command", {"count": 5})
            assert validated_args["count"] == 5

            # Test validation failure
            with pytest.raises(ValidationError):
                validate_command_args("test.command", {})  # missing required parameter

    def test_command_not_found(self):
        """Test validate_command_args with non-existent command."""
        with patch('core.commands.registry.command_registry') as mock_registry:
            mock_registry.get_command.return_value = None

            with pytest.raises(ValidationError) as exc_info:
                validate_command_args("nonexistent.command", {})
            assert "Command not found" in str(exc_info.value)

    def test_command_without_validation(self):
        """Test validate_command_args with command that has no validation."""
        test_command = Mock()
        test_command._validation_spec = None

        with patch('core.commands.registry.command_registry') as mock_registry:
            mock_registry.get_command.return_value = test_command

            # Should return args unchanged
            args = {"test": "value"}
            validated_args = validate_command_args("test.command", args)
            assert validated_args == args


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_validation_error_with_parameter_name(self):
        """Test ValidationError with parameter name."""
        error = ValidationError("Test error", parameter="test_param", value=42)
        assert "test_param" in str(error)
        assert "Test error" in str(error)

    def test_validation_error_without_parameter_name(self):
        """Test ValidationError without parameter name."""
        error = ValidationError("Test error")
        assert "Test error" in str(error)

    def test_validator_custom_error_message(self):
        """Test validator with custom error message."""
        validator = TypeValidator(int, error_message="Custom error message")

        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not an int")
        assert "Custom error message" in str(exc_info.value)

    def test_nested_validation_errors(self):
        """Test validation errors in nested structures."""
        element_validator = Type(int)
        list_validator = List(element_validator=element_validator)

        with pytest.raises(ValidationError) as exc_info:
            list_validator.validate([1, "not an int", 3], "test_list")

        error_msg = str(exc_info.value)
        assert "test_list" in error_msg
        assert "Element 1" in error_msg


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_workspace_command_validation(self):
        """Test validation for workspace-type commands."""
        @validate(
            widget_type=OneOf("terminal", "editor", "explorer"),
            tab_index=Optional(Range(0, 50)),
            name=Optional(String(max_length=100))
        )
        def workspace_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Test valid arguments
        context = CommandContext(args={
            "widget_type": "terminal",
            "tab_index": 2,
            "name": "My Terminal"
        })
        result = workspace_command(context)
        assert result.success is True

        # Test invalid widget type
        context = CommandContext(args={"widget_type": "invalid"})
        result = workspace_command(context)
        assert result.success is False
        assert "not in allowed values" in result.error

    def test_file_operation_validation(self):
        """Test validation for file operation commands."""
        @validate(
            file_path=String(min_length=1, pattern=r"^[^<>:\"\\|?*]+$"),
            encoding=Optional(OneOf("utf-8", "utf-16", "ascii")),
            backup=Optional(Type(bool))
        )
        def file_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Test valid file path
        context = CommandContext(args={
            "file_path": "test.txt",
            "encoding": "utf-8",
            "backup": True
        })
        result = file_command(context)
        assert result.success is True

        # Test invalid file path with special characters
        context = CommandContext(args={"file_path": "test<file>.txt"})
        result = file_command(context)
        assert result.success is False

    def test_numeric_range_validation(self):
        """Test validation for numeric ranges."""
        @validate(
            port=Range(1, 65535),
            timeout=Range(0.1, 300.0),
            retry_count=All(Type(int), Range(0, 10))
        )
        def network_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value=context.args)

        # Test valid values
        context = CommandContext(args={
            "port": 8080,
            "timeout": 30.5,
            "retry_count": 3
        })
        result = network_command(context)
        assert result.success is True

        # Test invalid port
        context = CommandContext(args={"port": 70000})
        result = network_command(context)
        assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__])
