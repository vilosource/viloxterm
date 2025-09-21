#!/usr/bin/env python3
"""
Command system for application actions.

This package provides the command infrastructure that centralizes
all application actions, enabling keyboard shortcuts, command palette,
and programmatic execution.
"""

from viloapp.core.commands.base import Command, CommandCategory, CommandContext, CommandResult
from viloapp.core.commands.decorators import (
    batch_register,
    command,
    command_handler,
    create_command_group,
)
from viloapp.core.commands.executor import command_executor
from viloapp.core.commands.registry import command_registry

__all__ = [
    "Command",
    "CommandContext",
    "CommandResult",
    "CommandCategory",
    "command_registry",
    "command_executor",
    "command",
    "command_handler",
    "batch_register",
    "create_command_group",
]
