#!/usr/bin/env python3
"""
Command system for application actions.

This package provides the command infrastructure that centralizes
all application actions, enabling keyboard shortcuts, command palette,
and programmatic execution.
"""

from core.commands.base import Command, CommandContext, CommandResult, CommandCategory
from core.commands.registry import command_registry
from core.commands.executor import command_executor
from core.commands.decorators import command, command_handler, batch_register, create_command_group

__all__ = [
    'Command',
    'CommandContext',
    'CommandResult',
    'CommandCategory',
    'command_registry',
    'command_executor',
    'command',
    'command_handler',
    'batch_register',
    'create_command_group',
]