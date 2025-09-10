#!/usr/bin/env python3
"""
Context system for application state management.

This package provides context tracking and when clause evaluation
for determining when commands and shortcuts are available.
"""

from core.context.manager import context_manager, ContextProvider
from core.context.keys import ContextKey, ContextValue
from core.context.evaluator import WhenClauseEvaluator

__all__ = [
    'context_manager',
    'ContextProvider',
    'ContextKey',
    'ContextValue',
    'WhenClauseEvaluator',
]