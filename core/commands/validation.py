#!/usr/bin/env python3
"""
Command parameter validation framework.

This module provides a comprehensive framework for validating command parameters
before execution, ensuring type safety and business logic constraints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Callable, Set, Type, get_type_hints
from abc import ABC, abstractmethod
from functools import wraps
from enum import Enum
import logging
import re

from core.commands.base import CommandContext, CommandResult

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when command parameter validation fails."""

    def __init__(self, message: str, parameter: str = None, value: Any = None):
        super().__init__(message)
        self.parameter = parameter
        self.value = value
        self.message = message

    def __str__(self) -> str:
        if self.parameter:
            return f"Validation error for parameter '{self.parameter}': {self.message}"
        return f"Validation error: {self.message}"


class Validator(ABC):
    """Base class for all parameter validators."""

    def __init__(self, error_message: str = None):
        self.error_message = error_message

    @abstractmethod
    def validate(self, value: Any, parameter_name: str = None) -> bool:
        """
        Validate a value.

        Args:
            value: The value to validate
            parameter_name: Name of the parameter being validated

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        pass

    def _raise_error(self, message: str, parameter_name: str = None, value: Any = None):
        """Helper to raise a validation error."""
        raise ValidationError(
            message=self.error_message or message,
            parameter=parameter_name,
            value=value
        )


class TypeValidator(Validator):
    """Validates that a value matches a specific type."""

    def __init__(self, expected_type: Type, error_message: str = None):
        self.expected_type = expected_type
        super().__init__(error_message)

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        if not isinstance(value, self.expected_type):
            self._raise_error(
                f"Expected {self.expected_type.__name__}, got {type(value).__name__}",
                parameter_name,
                value
            )
        return True


class RangeValidator(Validator):
    """Validates that a numeric value is within a specified range."""

    def __init__(self, min_value: Union[int, float] = None, max_value: Union[int, float] = None,
                 inclusive: bool = True, error_message: str = None):
        self.min_value = min_value
        self.max_value = max_value
        self.inclusive = inclusive
        super().__init__(error_message)

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        if not isinstance(value, (int, float)):
            self._raise_error(
                f"Expected numeric value, got {type(value).__name__}",
                parameter_name,
                value
            )

        if self.min_value is not None:
            if self.inclusive and value < self.min_value:
                self._raise_error(
                    f"Value {value} is less than minimum {self.min_value}",
                    parameter_name,
                    value
                )
            elif not self.inclusive and value <= self.min_value:
                self._raise_error(
                    f"Value {value} must be greater than {self.min_value}",
                    parameter_name,
                    value
                )

        if self.max_value is not None:
            if self.inclusive and value > self.max_value:
                self._raise_error(
                    f"Value {value} is greater than maximum {self.max_value}",
                    parameter_name,
                    value
                )
            elif not self.inclusive and value >= self.max_value:
                self._raise_error(
                    f"Value {value} must be less than {self.max_value}",
                    parameter_name,
                    value
                )

        return True


class OneOfValidator(Validator):
    """Validates that a value is one of a set of allowed values."""

    def __init__(self, allowed_values: Union[List, Set, tuple], error_message: str = None):
        self.allowed_values = set(allowed_values)
        super().__init__(error_message)

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        if value not in self.allowed_values:
            allowed_str = ", ".join(repr(v) for v in sorted(self.allowed_values, key=str))
            self._raise_error(
                f"Value {value!r} not in allowed values: {allowed_str}",
                parameter_name,
                value
            )
        return True


class StringValidator(Validator):
    """Validates string properties like length, pattern, etc."""

    def __init__(self, min_length: int = None, max_length: int = None,
                 pattern: str = None, non_empty: bool = False, error_message: str = None):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.non_empty = non_empty
        super().__init__(error_message)

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        if not isinstance(value, str):
            self._raise_error(
                f"Expected string, got {type(value).__name__}",
                parameter_name,
                value
            )

        if self.non_empty and not value.strip():
            self._raise_error(
                "String cannot be empty",
                parameter_name,
                value
            )

        if self.min_length is not None and len(value) < self.min_length:
            self._raise_error(
                f"String length {len(value)} is less than minimum {self.min_length}",
                parameter_name,
                value
            )

        if self.max_length is not None and len(value) > self.max_length:
            self._raise_error(
                f"String length {len(value)} is greater than maximum {self.max_length}",
                parameter_name,
                value
            )

        if self.pattern and not self.pattern.match(value):
            self._raise_error(
                f"String does not match required pattern",
                parameter_name,
                value
            )

        return True


class ListValidator(Validator):
    """Validates list properties like length and element validation."""

    def __init__(self, min_length: int = None, max_length: int = None,
                 element_validator: Validator = None, error_message: str = None):
        self.min_length = min_length
        self.max_length = max_length
        self.element_validator = element_validator
        super().__init__(error_message)

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        if not isinstance(value, (list, tuple)):
            self._raise_error(
                f"Expected list or tuple, got {type(value).__name__}",
                parameter_name,
                value
            )

        if self.min_length is not None and len(value) < self.min_length:
            self._raise_error(
                f"List length {len(value)} is less than minimum {self.min_length}",
                parameter_name,
                value
            )

        if self.max_length is not None and len(value) > self.max_length:
            self._raise_error(
                f"List length {len(value)} is greater than maximum {self.max_length}",
                parameter_name,
                value
            )

        if self.element_validator:
            for i, element in enumerate(value):
                try:
                    self.element_validator.validate(element, f"{parameter_name}[{i}]")
                except ValidationError as e:
                    # Re-raise with context
                    raise ValidationError(
                        f"Element {i}: {e.message}",
                        parameter_name,
                        value
                    )

        return True


class CustomValidator(Validator):
    """Allows custom validation logic through a callable."""

    def __init__(self, validator_func: Callable[[Any], bool], error_message: str):
        self.validator_func = validator_func
        super().__init__(error_message)

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        try:
            if not self.validator_func(value):
                self._raise_error(
                    self.error_message or "Custom validation failed",
                    parameter_name,
                    value
                )
        except Exception as e:
            self._raise_error(
                f"Custom validation error: {e}",
                parameter_name,
                value
            )
        return True


class OptionalValidator(Validator):
    """Wraps another validator to make it optional (allows None)."""

    def __init__(self, wrapped_validator: Validator):
        self.wrapped_validator = wrapped_validator
        super().__init__()

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        if value is None:
            return True
        return self.wrapped_validator.validate(value, parameter_name)


class CompositeValidator(Validator):
    """Combines multiple validators with AND logic."""

    def __init__(self, validators: List[Validator], error_message: str = None):
        self.validators = validators
        super().__init__(error_message)

    def validate(self, value: Any, parameter_name: str = None) -> bool:
        for validator in self.validators:
            validator.validate(value, parameter_name)
        return True


# Convenience factory functions
def String(min_length: int = None, max_length: int = None, pattern: str = None,
           non_empty: bool = False) -> StringValidator:
    """Create a string validator."""
    return StringValidator(min_length, max_length, pattern, non_empty)


def Range(min_value: Union[int, float] = None, max_value: Union[int, float] = None,
          inclusive: bool = True) -> RangeValidator:
    """Create a range validator."""
    return RangeValidator(min_value, max_value, inclusive)


def OneOf(*values) -> OneOfValidator:
    """Create a choice validator."""
    return OneOfValidator(values)


def Optional(validator: Validator) -> OptionalValidator:
    """Make a validator optional."""
    return OptionalValidator(validator)


def List(min_length: int = None, max_length: int = None,
         element_validator: Validator = None) -> ListValidator:
    """Create a list validator."""
    return ListValidator(min_length, max_length, element_validator)


def Type(expected_type: Type) -> TypeValidator:
    """Create a type validator."""
    return TypeValidator(expected_type)


def Custom(validator_func: Callable[[Any], bool], error_message: str) -> CustomValidator:
    """Create a custom validator."""
    return CustomValidator(validator_func, error_message)


def All(*validators: Validator) -> CompositeValidator:
    """Combine multiple validators with AND logic."""
    return CompositeValidator(list(validators))


class ParameterSpec:
    """Specification for a command parameter."""

    def __init__(self, name: str, validator: Validator = None,
                 required: bool = False, default: Any = None,
                 description: str = None):
        self.name = name
        self.validator = validator
        self.required = required
        self.default = default
        self.description = description

    def validate(self, value: Any) -> Any:
        """Validate and possibly transform a parameter value."""
        if value is None and self.required:
            raise ValidationError(f"Required parameter '{self.name}' is missing")

        if value is None and self.default is not None:
            value = self.default

        if value is not None and self.validator:
            self.validator.validate(value, self.name)

        return value


class CommandValidationSpec:
    """Complete validation specification for a command."""

    def __init__(self, parameters: Dict[str, ParameterSpec] = None,
                 min_args: int = None, max_args: int = None):
        self.parameters = parameters or {}
        self.min_args = min_args
        self.max_args = max_args

    def validate_context(self, context: CommandContext) -> CommandContext:
        """
        Validate command context and return a new context with validated parameters.

        Args:
            context: Original command context

        Returns:
            New CommandContext with validated parameters

        Raises:
            ValidationError: If validation fails
        """
        validated_args = {}

        # Check argument count constraints
        if self.min_args is not None and len(context.args) < self.min_args:
            raise ValidationError(f"Command requires at least {self.min_args} arguments, got {len(context.args)}")

        if self.max_args is not None and len(context.args) > self.max_args:
            raise ValidationError(f"Command accepts at most {self.max_args} arguments, got {len(context.args)}")

        # Validate each parameter
        for param_name, param_spec in self.parameters.items():
            value = context.args.get(param_name)
            validated_value = param_spec.validate(value)
            validated_args[param_name] = validated_value

        # Check for unexpected parameters (only warn, don't fail)
        unexpected = set(context.args.keys()) - set(self.parameters.keys())
        if unexpected:
            logger.warning(f"Unexpected parameters: {unexpected}")
            # Include unexpected parameters in validated args
            for param in unexpected:
                validated_args[param] = context.args[param]

        # Create new context with validated args
        new_context = CommandContext(
            main_window=context.main_window,
            workspace=context.workspace,
            active_widget=context.active_widget,
            services=context.services,
            args=validated_args
        )
        new_context._service_locator = context._service_locator

        return new_context


def validate(**parameter_specs) -> Callable:
    """
    Decorator to add parameter validation to commands.

    This decorator can be used with the @command decorator to add automatic
    parameter validation before command execution.

    Args:
        **parameter_specs: Keyword arguments where keys are parameter names
                          and values are Validator instances or ParameterSpec instances

    Returns:
        Decorator function

    Example:
        @command(id="test.command", title="Test", category="Test")
        @validate(
            tab_index=ParameterSpec("tab_index", Range(0, 10), required=True),
            name=ParameterSpec("name", String(min_length=1, max_length=50))
        )
        def test_command(context: CommandContext) -> CommandResult:
            # Parameters are guaranteed to be valid here
            return CommandResult(success=True)
    """
    def decorator(func_or_command):
        # Convert simple validators to ParameterSpec
        specs = {}
        for name, spec in parameter_specs.items():
            if isinstance(spec, Validator):
                specs[name] = ParameterSpec(name, spec)
            elif isinstance(spec, ParameterSpec):
                specs[name] = spec
            else:
                raise ValueError(f"Parameter spec for '{name}' must be a Validator or ParameterSpec")

        validation_spec = CommandValidationSpec(specs)

        # Check if this is already a Command object (from @command decorator)
        if hasattr(func_or_command, 'handler') and hasattr(func_or_command, 'id'):
            # This is a Command object, wrap its handler
            command = func_or_command
            original_handler = command.handler

            @wraps(original_handler)
            def validated_handler(context: CommandContext) -> CommandResult:
                try:
                    # Validate parameters
                    validated_context = validation_spec.validate_context(context)
                    # Execute original handler with validated context
                    return original_handler(validated_context)
                except ValidationError as e:
                    logger.warning(f"Validation failed for command {command.id}: {e}")
                    return CommandResult(success=False, error=str(e))

            command.handler = validated_handler
            # Store validation spec for introspection
            command._validation_spec = validation_spec
            return command
        else:
            # This is a function, wrap it directly and store validation spec
            @wraps(func_or_command)
            def validated_func(context: CommandContext) -> CommandResult:
                try:
                    # Validate parameters
                    validated_context = validation_spec.validate_context(context)
                    # Execute original function with validated context
                    return func_or_command(validated_context)
                except ValidationError as e:
                    logger.warning(f"Validation failed: {e}")
                    return CommandResult(success=False, error=str(e))

            # Store validation spec for introspection
            # The @command decorator will check for this and transfer it to the Command object
            validated_func._validation_spec = validation_spec
            return validated_func

    return decorator


def get_validation_spec(command_or_func) -> Optional[CommandValidationSpec]:
    """
    Get the validation specification for a command or function.

    Args:
        command_or_func: Command object or function with validation

    Returns:
        CommandValidationSpec if validation is configured, None otherwise
    """
    if hasattr(command_or_func, '_validation_spec'):
        return command_or_func._validation_spec
    return None


def validate_command_args(command_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate command arguments against a command's validation specification.

    This function can be used to validate arguments before executing a command.

    Args:
        command_id: ID of the command
        args: Arguments to validate

    Returns:
        Dictionary of validated arguments

    Raises:
        ValidationError: If validation fails
    """
    from core.commands.registry import command_registry

    command = command_registry.get_command(command_id)
    if not command:
        raise ValidationError(f"Command not found: {command_id}")

    validation_spec = get_validation_spec(command)
    if not validation_spec:
        # No validation configured, return args as-is
        return args

    # Create a temporary context for validation
    temp_context = CommandContext(args=args)
    validated_context = validation_spec.validate_context(temp_context)

    return validated_context.args