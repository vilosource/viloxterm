#!/usr/bin/env python3
"""
Context system for application state management.

This package provides context tracking and when clause evaluation
for determining when commands and shortcuts are available.
"""

from viloapp.core.context.evaluator import WhenClauseEvaluator
from viloapp.core.context.keys import ContextKey, ContextValue
from viloapp.core.context.manager import ContextProvider, context_manager

__all__ = [
    "context_manager",
    "ContextProvider",
    "ContextKey",
    "ContextValue",
    "WhenClauseEvaluator",
]
