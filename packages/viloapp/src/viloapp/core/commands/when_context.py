#!/usr/bin/env python3
"""
When-clause context system for conditional command execution.

This module provides a context evaluation system that determines whether
commands should be available based on the current application state.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from viloapp.core.commands.base import CommandContext

logger = logging.getLogger(__name__)


class WhenContext:
    """Evaluates when-clause expressions for commands."""

    def __init__(self, context: CommandContext):
        """
        Initialize the when-context evaluator.

        Args:
            context: The command context to evaluate against
        """
        self.context = context
        self._variables = self._build_context_variables()

    def _build_context_variables(self) -> Dict[str, Any]:
        """Build context variables from the current application state."""
        variables = {}

        # Model-based variables
        if self.context.model:
            # Tab-related
            variables["workbench.tabs.count"] = len(self.context.model.state.tabs)
            variables["hasMultipleTabs"] = len(self.context.model.state.tabs) > 1

            # Active tab
            active_tab = self.context.model.state.get_active_tab()
            if active_tab:
                # Pane-related
                panes = active_tab.tree.root.get_all_panes()
                variables["workbench.pane.count"] = len(panes)
                variables["workbench.pane.canSplit"] = len(panes) > 0
                variables["hasMultiplePanes"] = len(panes) > 1

                # Active pane
                active_pane = active_tab.get_active_pane()
                if active_pane:
                    # Widget type checks
                    from viloapp.models.workspace_model import WidgetType

                    variables["editorFocus"] = active_pane.widget_type in [
                        WidgetType.EDITOR,
                        WidgetType.TEXT_EDITOR,
                    ]
                    variables["terminalFocus"] = active_pane.widget_type == WidgetType.TERMINAL
                    variables["explorerFocus"] = active_pane.widget_type in [
                        WidgetType.FILE_EXPLORER,
                        WidgetType.EXPLORER,
                    ]

                    # Widget state checks
                    widget_state = active_pane.widget_state or {}
                    variables["editorHasSelection"] = widget_state.get("has_selection", False)
                    variables["editorIsReadOnly"] = widget_state.get("is_readonly", False)
                    variables["editorIsDirty"] = widget_state.get("is_modified", False)

        # UI-related variables
        if self.context.main_window:
            variables["isFullScreen"] = (
                self.context.main_window.isFullScreen()
                if hasattr(self.context.main_window, "isFullScreen")
                else False
            )
            variables["sidebarVisible"] = (
                self.context.main_window.sidebar.isVisible()
                if hasattr(self.context.main_window, "sidebar")
                else False
            )
            variables["menuBarVisible"] = (
                self.context.main_window.menuBar().isVisible()
                if hasattr(self.context.main_window, "menuBar")
                else False
            )

        # Development mode
        from PySide6.QtCore import QSettings

        settings = QSettings("ViloxTerm", "ViloxTerm")
        variables["isDevelopment"] = settings.value("dev_mode", False, type=bool)

        return variables

    def evaluate(self, expression: Optional[str]) -> bool:
        """
        Evaluate a when-clause expression.

        Args:
            expression: The when-clause expression to evaluate

        Returns:
            True if the expression evaluates to True or is None/empty
        """
        if not expression:
            return True

        try:
            # Parse and evaluate the expression
            result = self._evaluate_expression(expression)
            logger.debug(f"When-clause '{expression}' evaluated to {result}")
            return result
        except Exception as e:
            logger.warning(f"Failed to evaluate when-clause '{expression}': {e}")
            # On error, default to allowing the command
            return True

    def _evaluate_expression(self, expression: str) -> bool:
        """
        Parse and evaluate a when-clause expression.

        Supports:
        - Variables: workbench.pane.count
        - Comparisons: >, <, >=, <=, ==, !=
        - Boolean operators: &&, ||, !
        - Grouping: ()
        """
        expression = expression.strip()

        # Handle negation
        if expression.startswith("!"):
            return not self._evaluate_expression(expression[1:].strip())

        # Handle parentheses
        if expression.startswith("(") and expression.endswith(")"):
            return self._evaluate_expression(expression[1:-1].strip())

        # Handle AND operator
        if "&&" in expression:
            parts = expression.split("&&", 1)
            return self._evaluate_expression(parts[0].strip()) and self._evaluate_expression(
                parts[1].strip()
            )

        # Handle OR operator
        if "||" in expression:
            parts = expression.split("||", 1)
            return self._evaluate_expression(parts[0].strip()) or self._evaluate_expression(
                parts[1].strip()
            )

        # Handle comparisons
        comparison_ops = [">=", "<=", "!=", "==", ">", "<"]
        for op in comparison_ops:
            if op in expression:
                parts = expression.split(op, 1)
                if len(parts) == 2:
                    left = self._evaluate_value(parts[0].strip())
                    right = self._evaluate_value(parts[1].strip())
                    return self._compare(left, op, right)

        # Handle simple variable or boolean
        value = self._evaluate_value(expression)
        return bool(value)

    def _evaluate_value(self, value_str: str) -> Any:
        """Evaluate a single value (variable, number, string, or boolean)."""
        value_str = value_str.strip()

        # Boolean literals
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Number literals
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # String literals
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]

        # Variable lookup
        return self._variables.get(value_str, False)

    def _compare(self, left: Any, op: str, right: Any) -> bool:
        """Compare two values using the specified operator."""
        try:
            if op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == ">":
                return left > right
            elif op == "<":
                return left < right
            elif op == ">=":
                return left >= right
            elif op == "<=":
                return left <= right
        except (TypeError, ValueError) as e:
            logger.debug(f"Comparison failed: {left} {op} {right} - {e}")
            return False
        return False


def can_execute_command(context: CommandContext, when_clause: Optional[str]) -> bool:
    """
    Check if a command can execute in the given context.

    Args:
        context: The command context
        when_clause: The when-clause expression

    Returns:
        True if the command can execute
    """
    if not when_clause:
        return True

    evaluator = WhenContext(context)
    return evaluator.evaluate(when_clause)
