#!/usr/bin/env python3
"""
Context manager for tracking application state.

The ContextManager maintains the current context of the application,
which is used to evaluate when clauses for commands and shortcuts.
"""

import builtins
import logging
from threading import Lock
from typing import Any, Callable, Optional

from viloapp.core.context.keys import ContextKey

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages application context for when clause evaluation.

    The context manager tracks the current state of the application
    (what has focus, what is visible, etc.) and provides this information
    for evaluating when clauses on commands and shortcuts.
    """

    _instance: Optional["ContextManager"] = None
    _lock = Lock()

    def __new__(cls) -> "ContextManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the manager (only once)."""
        if self._initialized:
            return

        self._context: dict[str, Any] = {}
        self._observers: list[Callable[[str, Any, Any], None]] = []
        self._providers: list[ContextProvider] = []
        self._initialized = True

        # Set default context values
        self._set_defaults()

        logger.info("ContextManager initialized")

    def _set_defaults(self):
        """Set default context values."""
        # Default focus states
        self._context[ContextKey.EDITOR_FOCUS] = False
        self._context[ContextKey.TERMINAL_FOCUS] = False
        self._context[ContextKey.SIDEBAR_FOCUS] = False
        self._context[ContextKey.ACTIVITY_BAR_FOCUS] = False
        self._context[ContextKey.COMMAND_PALETTE_FOCUS] = False

        # Default visibility states
        self._context[ContextKey.SIDEBAR_VISIBLE] = True
        self._context[ContextKey.MENU_BAR_VISIBLE] = True
        self._context[ContextKey.STATUS_BAR_VISIBLE] = True

        # Default editor states
        self._context[ContextKey.HAS_OPEN_EDITORS] = False
        self._context[ContextKey.HAS_SELECTION] = False
        self._context[ContextKey.IS_DIRTY] = False

        # Default counts
        self._context[ContextKey.PANE_COUNT] = 1
        self._context[ContextKey.TAB_COUNT] = 0

        # Platform detection
        import sys

        if sys.platform == "win32":
            self._context[ContextKey.PLATFORM] = "windows"
        elif sys.platform == "darwin":
            self._context[ContextKey.PLATFORM] = "darwin"
        else:
            self._context[ContextKey.PLATFORM] = "linux"

    def set(self, key: str, value: Any) -> None:
        """
        Set a context value.

        Args:
            key: Context key
            value: Value to set
        """
        old_value = self._context.get(key)

        # Only update and notify if value changed
        if old_value != value:
            self._context[key] = value
            logger.debug(f"Context updated: {key} = {value}")
            self._notify_observers(key, old_value, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a context value.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value or default
        """
        return self._context.get(key, default)

    def update(self, updates: dict[str, Any]) -> None:
        """
        Update multiple context values at once.

        Args:
            updates: Dictionary of key-value pairs to update
        """
        for key, value in updates.items():
            self.set(key, value)

    def get_all(self) -> dict[str, Any]:
        """
        Get all context values.

        Returns:
            Copy of the entire context dictionary
        """
        return self._context.copy()

    def clear_focus(self) -> None:
        """Clear all focus-related context keys."""
        focus_keys = [
            ContextKey.EDITOR_FOCUS,
            ContextKey.TERMINAL_FOCUS,
            ContextKey.SIDEBAR_FOCUS,
            ContextKey.ACTIVITY_BAR_FOCUS,
            ContextKey.COMMAND_PALETTE_FOCUS,
            ContextKey.MENU_FOCUS,
            ContextKey.DIALOG_FOCUS,
        ]

        for key in focus_keys:
            self.set(key, False)

    def update_from_widget(self, widget: Any) -> None:
        """
        Update context based on a widget gaining focus.

        Args:
            widget: Widget that gained focus
        """
        # Clear all focus first
        self.clear_focus()

        # Import here to avoid circular dependencies
        from viloapp.ui.activity_bar import ActivityBar
        from viloapp.ui.sidebar import Sidebar
        from viloapp.ui.widgets.app_widget import AppWidget

        # Determine widget type and set appropriate context
        widget_id = type(widget).__name__

        if isinstance(widget, AppWidget):
            from viloapp.ui.terminal.terminal_app_widget import TerminalAppWidget
            from viloapp.ui.widgets.editor_app_widget import EditorAppWidget

            if isinstance(widget, EditorAppWidget):
                self.set(ContextKey.EDITOR_FOCUS, True)
                self.set(ContextKey.ACTIVE_PANE_TYPE, "editor")
            elif isinstance(widget, TerminalAppWidget):
                self.set(ContextKey.TERMINAL_FOCUS, True)
                self.set(ContextKey.ACTIVE_PANE_TYPE, "terminal")
        elif isinstance(widget, Sidebar):
            self.set(ContextKey.SIDEBAR_FOCUS, True)
        elif isinstance(widget, ActivityBar):
            self.set(ContextKey.ACTIVITY_BAR_FOCUS, True)

        logger.debug(f"Context updated from widget: {widget_type}")

    def add_observer(self, observer: Callable[[str, Any, Any], None]) -> None:
        """
        Add an observer for context changes.

        Args:
            observer: Callback function(key, old_value, new_value)
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Callable[[str, Any, Any], None]) -> None:
        """
        Remove an observer.

        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def add_provider(self, provider: "ContextProvider") -> None:
        """
        Add a context provider.

        Context providers can dynamically contribute context values.

        Args:
            provider: Provider to add
        """
        if provider not in self._providers:
            self._providers.append(provider)
            provider.initialize(self)

    def remove_provider(self, provider: "ContextProvider") -> None:
        """
        Remove a context provider.

        Args:
            provider: Provider to remove
        """
        if provider in self._providers:
            self._providers.remove(provider)
            provider.dispose()

    def evaluate_context(self, keys: builtins.set[str]) -> dict[str, Any]:
        """
        Evaluate context for specific keys.

        This allows providers to contribute dynamic values.

        Args:
            keys: Set of keys to evaluate

        Returns:
            Context dictionary with requested keys
        """
        result = {}

        # Get static values
        for key in keys:
            if key in self._context:
                result[key] = self._context[key]

        # Let providers contribute
        for provider in self._providers:
            provider_values = provider.provide_context(keys)
            result.update(provider_values)

        return result

    def _notify_observers(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify all observers of a context change."""
        for observer in self._observers:
            try:
                observer(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}", exc_info=True)

    def reset(self) -> None:
        """Reset context to defaults (mainly for testing)."""
        self._context.clear()
        self._set_defaults()
        logger.info("Context reset to defaults")


class ContextProvider:
    """
    Base class for context providers.

    Context providers can dynamically contribute context values
    based on application state.
    """

    def initialize(self, manager: ContextManager) -> None:
        """
        Initialize the provider.

        Args:
            manager: The context manager
        """
        pass

    def provide_context(self, keys: set[str]) -> dict[str, Any]:
        """
        Provide context values for requested keys.

        Args:
            keys: Set of keys being evaluated

        Returns:
            Dictionary of provided values
        """
        return {}

    def dispose(self) -> None:
        """Clean up the provider."""
        pass


# Global singleton instance
context_manager = ContextManager()
