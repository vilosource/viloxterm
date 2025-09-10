#!/usr/bin/env python3
"""
Core application infrastructure.

This package contains the fundamental building blocks of the application:
- Command system for actions and keyboard shortcuts
- Context management for application state
- Keyboard service for shortcut handling
"""

# Import key components for easier access
from core.commands.base import Command, CommandContext, CommandResult
from core.commands.registry import command_registry
from core.commands.executor import command_executor
from core.commands.decorators import command

from core.context.manager import context_manager
from core.context.keys import ContextKey, ContextValue
from core.context.evaluator import WhenClauseEvaluator

__all__ = [
    # Commands
    'Command',
    'CommandContext', 
    'CommandResult',
    'command_registry',
    'command_executor',
    'command',
    
    # Context
    'context_manager',
    'ContextKey',
    'ContextValue',
    'WhenClauseEvaluator',
]