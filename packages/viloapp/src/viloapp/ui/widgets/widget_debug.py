#!/usr/bin/env python3
"""
Widget lifecycle debugging utilities.

This module provides tools for inspecting and debugging widget lifecycle
state, signal connections, and performance metrics.
"""

import logging
import time
from datetime import datetime
from typing import Any

from PySide6.QtCore import QTimer

from viloapp.ui.widgets.app_widget import AppWidget
from viloapp.ui.widgets.widget_state import WidgetState

logger = logging.getLogger(__name__)


class WidgetDebugger:
    """
    Debugging utilities for widget lifecycle inspection.
    """

    def __init__(self):
        """Initialize the widget debugger."""
        self._tracked_widgets = {}  # widget_id -> widget
        self._state_history = {}  # widget_id -> list of (timestamp, state)
        self._performance_metrics = {}  # widget_id -> metrics dict
        self._callback_count = {}  # widget_id -> callback count
        self._debug_enabled = False

    def enable_debug(self):
        """Enable debug mode."""
        self._debug_enabled = True
        logger.info("Widget debugging enabled")

    def disable_debug(self):
        """Disable debug mode."""
        self._debug_enabled = False
        logger.info("Widget debugging disabled")

    def track_widget(self, widget: AppWidget):
        """
        Start tracking a widget for debugging.

        Args:
            widget: The widget to track
        """
        if not self._debug_enabled:
            return

        widget_id = widget.widget_id
        self._tracked_widgets[widget_id] = widget
        self._state_history[widget_id] = [(datetime.now(), widget.widget_state)]
        self._performance_metrics[widget_id] = {
            "init_start": None,
            "init_end": None,
            "init_duration": None,
            "error_count": 0,
            "retry_count": 0,
            "focus_requests": 0,
            "state_transitions": 0,
        }
        self._callback_count[widget_id] = 0

        # Register state transition callback for tracking
        widget.on_state_transition(callback=lambda w, f, t: self._on_state_change(w, f, t))

        logger.debug(f"Started tracking widget {widget_id}")

    def stop_tracking(self, widget: AppWidget):
        """
        Stop tracking a widget.

        Args:
            widget: The widget to stop tracking
        """
        widget_id = widget.widget_id
        if widget_id in self._tracked_widgets:
            del self._tracked_widgets[widget_id]
            logger.debug(f"Stopped tracking widget {widget_id}")

    def _on_state_change(self, widget: AppWidget, from_state: WidgetState, to_state: WidgetState):
        """Handle state change for tracked widgets."""
        if not self._debug_enabled:
            return

        widget_id = widget.widget_id
        if widget_id not in self._tracked_widgets:
            return

        # Record state history
        self._state_history[widget_id].append((datetime.now(), to_state))

        # Update metrics
        metrics = self._performance_metrics[widget_id]
        metrics["state_transitions"] += 1

        # Track initialization timing
        if from_state == WidgetState.CREATED and to_state == WidgetState.INITIALIZING:
            metrics["init_start"] = time.time()
        elif from_state == WidgetState.INITIALIZING and to_state == WidgetState.READY:
            if metrics["init_start"]:
                metrics["init_end"] = time.time()
                metrics["init_duration"] = metrics["init_end"] - metrics["init_start"]
                logger.info(
                    f"Widget {widget_id} initialization took {metrics['init_duration']:.3f}s"
                )

        # Track errors
        if to_state == WidgetState.ERROR:
            metrics["error_count"] += 1

        # Track retries
        if from_state == WidgetState.ERROR and to_state == WidgetState.INITIALIZING:
            metrics["retry_count"] += 1

    def get_widget_info(self, widget: AppWidget) -> dict[str, Any]:
        """
        Get comprehensive debug information for a widget.

        Args:
            widget: The widget to inspect

        Returns:
            Dictionary containing debug information
        """
        widget_id = widget.widget_id

        info = {
            "widget_id": widget_id,
            "widget_id": widget.widget_id.value,
            "current_state": widget.widget_state.value,
            "has_focus": widget.has_focus,
            "pending_focus": widget._pending_focus,
            "error_count": widget._error_count,
            "retry_config": {
                "max_retries": widget._max_retries,
                "base_delay": widget._retry_base_delay,
                "backoff_factor": widget._retry_backoff_factor,
            },
            "signal_connections": widget._signal_manager.get_connection_count(),
            "state_callbacks": len(widget._state_callbacks) + len(widget._any_state_callbacks),
        }

        # Add tracked metrics if available
        if widget_id in self._performance_metrics:
            info["metrics"] = self._performance_metrics[widget_id]

        # Add state history if available
        if widget_id in self._state_history:
            info["state_history"] = [
                {"timestamp": ts.isoformat(), "state": state.value}
                for ts, state in self._state_history[widget_id]
            ]

        return info

    def print_widget_state(self, widget: AppWidget):
        """
        Print formatted widget state information.

        Args:
            widget: The widget to inspect
        """
        info = self.get_widget_info(widget)

        print(f"\n{'=' * 60}")
        print(f"Widget Debug Info: {info['widget_id']}")
        print(f"{'=' * 60}")
        print(f"Type: {info['widget_id']}")
        print(f"Current State: {info['current_state']}")
        print(f"Has Focus: {info['has_focus']}")
        print(f"Pending Focus: {info['pending_focus']}")
        print(f"Error Count: {info['error_count']}")
        print(f"Signal Connections: {info['signal_connections']}")
        print(f"State Callbacks: {info['state_callbacks']}")

        if "metrics" in info:
            print("\nPerformance Metrics:")
            metrics = info["metrics"]
            if metrics["init_duration"]:
                print(f"  Init Duration: {metrics['init_duration']:.3f}s")
            print(f"  State Transitions: {metrics['state_transitions']}")
            print(f"  Error Count: {metrics['error_count']}")
            print(f"  Retry Count: {metrics['retry_count']}")

        if "state_history" in info and len(info["state_history"]) > 1:
            print("\nState History (last 5):")
            for entry in info["state_history"][-5:]:
                print(f"  {entry['timestamp']}: {entry['state']}")

        print(f"{'=' * 60}\n")

    def get_all_widgets_summary(self) -> list[dict[str, Any]]:
        """
        Get a summary of all tracked widgets.

        Returns:
            List of widget summaries
        """
        summaries = []
        for widget_id, widget in self._tracked_widgets.items():
            summaries.append(
                {
                    "widget_id": widget_id,
                    "type": widget.widget_id.value,
                    "state": widget.widget_state.value,
                    "has_focus": widget.has_focus,
                    "errors": widget._error_count,
                    "connections": widget._signal_manager.get_connection_count(),
                }
            )
        return summaries

    def print_all_widgets(self):
        """Print a summary table of all tracked widgets."""
        summaries = self.get_all_widgets_summary()

        if not summaries:
            print("No widgets being tracked")
            return

        print(f"\n{'=' * 80}")
        print(
            f"{'Widget ID':<20} {'Type':<15} {'State':<15} {'Focus':<8} {'Errors':<8} {'Conns':<8}"
        )
        print(f"{'-' * 80}")

        for summary in summaries:
            print(
                f"{summary['widget_id']:<20} "
                f"{summary['type']:<15} "
                f"{summary['state']:<15} "
                f"{'Yes' if summary['has_focus'] else 'No':<8} "
                f"{summary['errors']:<8} "
                f"{summary['connections']:<8}"
            )

        print(f"{'=' * 80}\n")

    def watch_widget(self, widget: AppWidget, interval_ms: int = 1000):
        """
        Watch a widget and print updates at regular intervals.

        Args:
            widget: The widget to watch
            interval_ms: Update interval in milliseconds
        """

        def update():
            self.print_widget_state(widget)

        timer = QTimer()
        timer.timeout.connect(update)
        timer.start(interval_ms)

        # Store timer to prevent garbage collection
        widget._debug_timer = timer

        logger.info(f"Started watching widget {widget.widget_id} with {interval_ms}ms interval")
        return timer

    def stop_watching(self, widget: AppWidget):
        """
        Stop watching a widget.

        Args:
            widget: The widget to stop watching
        """
        if hasattr(widget, "_debug_timer"):
            widget._debug_timer.stop()
            del widget._debug_timer
            logger.info(f"Stopped watching widget {widget.widget_id}")


class WidgetInspector:
    """
    Static methods for quick widget inspection.
    """

    @staticmethod
    def inspect(widget: AppWidget) -> dict[str, Any]:
        """
        Quick inspection of a widget's current state.

        Args:
            widget: The widget to inspect

        Returns:
            Dictionary with widget state information
        """
        return {
            "id": widget.widget_id,
            "type": widget.widget_id.value,
            "state": widget.widget_state.value,
            "ready": widget.widget_state == WidgetState.READY,
            "has_focus": widget.has_focus,
            "pending_focus": widget._pending_focus,
            "errors": widget._error_count,
            "connections": widget._signal_manager.get_connection_count(),
            "retry_config": {
                "max": widget._max_retries,
                "delay": widget._retry_base_delay,
                "factor": widget._retry_backoff_factor,
            },
        }

    @staticmethod
    def validate_state(widget: AppWidget) -> list[str]:
        """
        Validate widget state consistency.

        Args:
            widget: The widget to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check state consistency
        if widget.widget_state == WidgetState.READY and widget._pending_focus:
            issues.append("Widget is READY but has pending focus")

        if (
            widget.widget_state == WidgetState.DESTROYED
            and widget._signal_manager.has_connections()
        ):
            issues.append("Widget is DESTROYED but still has signal connections")

        if widget.widget_state == WidgetState.ERROR and widget._error_count == 0:
            issues.append("Widget is in ERROR state but error count is 0")

        if widget.has_focus and widget.widget_state not in [
            WidgetState.READY,
            WidgetState.SUSPENDED,
        ]:
            issues.append(f"Widget has focus but is in {widget.widget_state.value} state")

        return issues

    @staticmethod
    def compare_widgets(widget1: AppWidget, widget2: AppWidget) -> dict[str, Any]:
        """
        Compare two widgets for debugging.

        Args:
            widget1: First widget
            widget2: Second widget

        Returns:
            Comparison dictionary
        """
        return {
            "widget1_id": widget1.widget_id,
            "widget2_id": widget2.widget_id,
            "same_type": widget1.widget_id == widget2.widget_id,
            "same_state": widget1.widget_state == widget2.widget_state,
            "focus_diff": {"widget1": widget1.has_focus, "widget2": widget2.has_focus},
            "error_diff": {
                "widget1": widget1._error_count,
                "widget2": widget2._error_count,
            },
            "connection_diff": {
                "widget1": widget1._signal_manager.get_connection_count(),
                "widget2": widget2._signal_manager.get_connection_count(),
            },
        }


# Global debugger instance
_global_debugger = None


def get_widget_debugger() -> WidgetDebugger:
    """
    Get the global widget debugger instance.

    Returns:
        The global WidgetDebugger instance
    """
    global _global_debugger
    if _global_debugger is None:
        _global_debugger = WidgetDebugger()
    return _global_debugger


def enable_widget_debugging():
    """Enable global widget debugging."""
    debugger = get_widget_debugger()
    debugger.enable_debug()
    logging.getLogger("viloapp.ui.widgets").setLevel(logging.DEBUG)


def disable_widget_debugging():
    """Disable global widget debugging."""
    debugger = get_widget_debugger()
    debugger.disable_debug()


def debug_widget(widget: AppWidget):
    """
    Quick debug helper for a widget.

    Args:
        widget: The widget to debug
    """
    debugger = get_widget_debugger()
    if not debugger._debug_enabled:
        debugger.enable_debug()
    debugger.track_widget(widget)
    debugger.print_widget_state(widget)
